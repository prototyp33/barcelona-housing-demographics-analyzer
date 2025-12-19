#!/usr/bin/env python3
"""
Entrena y evalúa un baseline MACRO para Gràcia usando datos agregados (Fase 1).

Contexto:
- En Fase 1, los precios de Portal Dades están agregados por barrio/periodo/indicador.
- Los atributos estructurales (Catastro) están imputados o agregados por barrio.
- Por tanto, un hedónico micro (edificio-a-edificio) NO es coherente con este `y`.

Este script entrena un modelo lineal (OLS) sobre:
- `spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv`

Evaluación:
- Split aleatorio (80/20)
- Split temporal (train 2020–2024, test 2025)

Outputs:
- JSON métricas: `spike-data-validation/data/logs/macro_baseline_model_203.json`
- CSV predicciones (split temporal): `spike-data-validation/data/processed/macro_baseline_predictions_203.csv`
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

DEFAULT_INPUT = PROCESSED_DIR / "gracia_merged_agg_barrio_anio_dataset.csv"
DEFAULT_REPORT = LOG_DIR / "macro_baseline_model_203.json"
DEFAULT_PRED = PROCESSED_DIR / "macro_baseline_predictions_203.csv"

PROJECT_DB_PATH = Path("data/processed/database.db")
SPIKE_GEOJSON_DIR = Path("spike-data-validation/data/raw/geojson")


@dataclass(frozen=True)
class TrainConfig:
    """Configuración del baseline macro."""

    seed: int = 42
    test_size: float = 0.2
    temporal_test_year: int = 2025


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _load_barrio_name_map_from_sqlite(db_path: Path) -> Dict[int, str]:
    """
    Carga un mapa barrio_id -> nombre desde SQLite (tabla dim_barrios).

    Args:
        db_path: Ruta a la base de datos SQLite principal del proyecto.

    Returns:
        Diccionario {barrio_id: nombre}.

    Raises:
        FileNotFoundError: Si la base de datos no existe.
        ValueError: Si no se puede construir el mapa por falta de columnas.
        sqlite3.Error: Si hay error consultando SQLite.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"No se encontró la base de datos en {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        df_dim = pd.read_sql_query("SELECT * FROM dim_barrios", conn)
    finally:
        conn.close()

    if df_dim.empty:
        raise ValueError("dim_barrios está vacía")

    # Intentar columnas comunes en el proyecto
    candidate_id_cols = ["barrio_id", "codi_barri", "CODI_BARRI"]
    candidate_name_cols = ["nombre", "nom_barri", "NOM_BARRI", "barrio_nombre"]

    id_col = next((c for c in candidate_id_cols if c in df_dim.columns), None)
    name_col = next((c for c in candidate_name_cols if c in df_dim.columns), None)
    if id_col is None or name_col is None:
        raise ValueError(
            f"No se encontraron columnas esperadas para id/nombre en dim_barrios. "
            f"Cols={df_dim.columns.tolist()}",
        )

    df_dim = df_dim[[id_col, name_col]].dropna().copy()
    df_dim[id_col] = pd.to_numeric(df_dim[id_col], errors="coerce").astype("Int64")
    df_dim[name_col] = df_dim[name_col].astype(str)
    df_dim = df_dim.dropna(subset=[id_col]).copy()

    return {int(k): str(v) for k, v in zip(df_dim[id_col].to_list(), df_dim[name_col].to_list())}


def _load_barrio_name_map_from_geojson(geojson_dir: Path) -> Dict[int, str]:
    """
    Carga un mapa barrio_id -> nombre desde el GeoJSON oficial de barrios usado en el spike.

    Args:
        geojson_dir: Directorio que contiene `barrios_geojson_*.json`.

    Returns:
        Diccionario {barrio_id: nombre}.

    Raises:
        FileNotFoundError: Si no se encuentra ningún GeoJSON.
        ValueError: Si el GeoJSON no tiene la estructura esperada.
    """
    if not geojson_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de GeoJSON: {geojson_dir}")

    candidates = sorted(geojson_dir.glob("barrios_geojson_*.json"))
    if not candidates:
        raise FileNotFoundError(f"No se encontró ningún barrios_geojson_*.json en {geojson_dir}")

    # Usar el más reciente (orden lexicográfico con timestamp suele funcionar)
    geojson_path = candidates[-1]
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    feats = data.get("features")
    if not isinstance(feats, list):
        raise ValueError("GeoJSON sin lista 'features'")

    out: Dict[int, str] = {}
    for f in feats:
        props = f.get("properties") or {}
        barrio_id = props.get("codi_barri")
        barrio_nombre = props.get("nom_barri")
        if barrio_id is None or barrio_nombre is None:
            continue
        try:
            out[int(barrio_id)] = str(barrio_nombre)
        except (TypeError, ValueError):
            continue
    return out


def load_barrio_name_map() -> Dict[int, str]:
    """
    Carga un mapa barrio_id -> nombre, intentando primero SQLite y luego GeoJSON del spike.

    Returns:
        Diccionario {barrio_id: nombre}. Puede estar vacío si no se pudo cargar.
    """
    try:
        m = _load_barrio_name_map_from_sqlite(PROJECT_DB_PATH)
        logger.info("Mapa barrio_id->nombre cargado desde SQLite (%s entradas)", len(m))
        return m
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        logger.warning("No se pudo cargar mapa desde SQLite (%s). Probando GeoJSON...", exc)

    try:
        m = _load_barrio_name_map_from_geojson(SPIKE_GEOJSON_DIR)
        logger.info("Mapa barrio_id->nombre cargado desde GeoJSON (%s entradas)", len(m))
        return m
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("No se pudo cargar mapa desde GeoJSON (%s).", exc)

    return {}


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--report", type=str, default=str(DEFAULT_REPORT))
    parser.add_argument("--pred-out", type=str, default=str(DEFAULT_PRED))
    parser.add_argument("--seed", type=int, default=TrainConfig.seed)
    parser.add_argument("--test-size", type=float, default=TrainConfig.test_size)
    parser.add_argument("--temporal-test-year", type=int, default=TrainConfig.temporal_test_year)
    return parser.parse_args()


def _ols_fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Ajusta OLS por mínimos cuadrados."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def ols_coefficients_table(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: List[str],
    barrio_name_map: Optional[Dict[int, str]] = None,
    baseline_info: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Calcula tabla de coeficientes (OLS) con errores estándar y t-stats.

    Nota:
    - Usamos pseudo-inversa para robustez (colinealidad por dummies).
    - No calculamos p-values para evitar dependencia extra (scipy).

    Args:
        X_train: Matriz de diseño de entrenamiento (incluye intercept).
        y_train: Target de entrenamiento.
        feature_names: Nombres de columnas de X (mismo orden).

    Returns:
        DataFrame con coeficiente, error estándar y t-stat por feature.

    Raises:
        ValueError: Si las dimensiones de X/y no son consistentes.
    """
    if X_train.ndim != 2:
        raise ValueError("X_train debe ser una matriz 2D.")
    if y_train.ndim != 1:
        raise ValueError("y_train debe ser un vector 1D.")
    if X_train.shape[0] != y_train.shape[0]:
        raise ValueError("X_train e y_train deben tener el mismo número de filas.")
    if X_train.shape[1] != len(feature_names):
        raise ValueError("feature_names debe tener longitud igual a X_train.shape[1].")

    beta = _ols_fit(X_train, y_train)
    y_hat = X_train @ beta
    resid = y_train - y_hat

    n, p = X_train.shape
    dof = max(n - p, 1)
    sse = float((resid**2).sum())
    sigma2 = sse / float(dof)

    # (X'X)^-1 con pseudo-inversa para casos singulares (dummies / colinealidad)
    xtx_inv = np.linalg.pinv(X_train.T @ X_train)
    var_beta = np.diag(xtx_inv) * sigma2
    se = np.sqrt(np.clip(var_beta, 0.0, np.inf))

    with np.errstate(divide="ignore", invalid="ignore"):
        t_stat = np.where(se > 0, beta / se, np.nan)

    df = pd.DataFrame(
        {
            "feature": feature_names,
            "coeficiente": beta.astype(float),
            "std_error": se.astype(float),
            "t_stat": t_stat.astype(float),
        },
    )
    df["feature_type"] = "other"
    df.loc[df["feature"] == "intercept", "feature_type"] = "intercept"
    df.loc[df["feature"].isin({"superficie_m2_barrio_mean", "ano_construccion_barrio_mean", "plantas_barrio_mean", "anio_num"}), "feature_type"] = "numeric"
    df.loc[df["feature"].str.startswith("barrio_"), "feature_type"] = "barrio"
    df.loc[df["feature"].str.startswith("ds_"), "feature_type"] = "dataset"
    df.loc[df["feature"].str.startswith("year_"), "feature_type"] = "year"

    # Anotar barrio_id y nombre cuando aplique
    df["barrio_id"] = pd.NA
    df["barrio_nombre"] = pd.NA
    if barrio_name_map:
        barrio_rows = df["feature_type"] == "barrio"
        if barrio_rows.any():
            barrio_ids = (
                df.loc[barrio_rows, "feature"]
                .str.replace("barrio_", "", regex=False)
                .apply(lambda x: int(x) if str(x).isdigit() else None)
            )
            df.loc[barrio_rows, "barrio_id"] = barrio_ids
            df.loc[barrio_rows, "barrio_nombre"] = barrio_ids.apply(
                lambda bid: barrio_name_map.get(int(bid), None) if bid is not None else None,
            )

    # Incluir baseline info (categorías omitidas por drop_first) como metadatos repetidos
    if baseline_info:
        for k, v in baseline_info.items():
            df[k] = v

    df["abs_coef"] = df["coeficiente"].abs()
    df = df.sort_values("abs_coef", ascending=False).reset_index(drop=True)
    return df


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calcula métricas de regresión."""
    resid = y_true - y_pred
    sse = float((resid**2).sum())
    sst = float(((y_true - y_true.mean()) ** 2).sum())
    r2 = 1.0 - sse / sst if sst > 0 else float("nan")
    rmse = float(np.sqrt(sse / len(y_true))) if len(y_true) > 0 else float("nan")
    mae = float(np.mean(np.abs(resid))) if len(y_true) > 0 else float("nan")
    return {"r2": r2, "rmse": rmse, "mae": mae}


def build_design_matrix(
    df: pd.DataFrame,
    use_dummies_year: bool,
    use_dummies_dataset: bool,
    use_dummies_barrio: bool,
    year_as_numeric: bool = False,
    include_structural: bool = True,
) -> Tuple[np.ndarray, List[str], pd.DataFrame]:
    """
    Construye X con intercept + features numéricas + dummies.

    Args:
        df: DataFrame agregado.
        use_dummies_year: Si True, añade dummies de `anio`.
        use_dummies_dataset: Si True, añade dummies de `dataset_id`.
        use_dummies_barrio: Si True, añade dummies de `barrio_id` (fixed effects de barrio).

    Returns:
        (X, feature_names, base_df)
    """
    X_cols = [
        "superficie_m2_barrio_mean",
        "ano_construccion_barrio_mean",
        "plantas_barrio_mean",
    ]
    required_cols: List[str] = ["precio_m2_mean"]
    if include_structural:
        required_cols.extend(X_cols)
    if year_as_numeric or use_dummies_year:
        required_cols.append("anio")
    if use_dummies_dataset:
        required_cols.append("dataset_id")
    if use_dummies_barrio:
        required_cols.append("barrio_id")

    missing_cols = sorted(set(required_cols) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Faltan columnas requeridas en el dataset macro: {missing_cols}")

    base = df.dropna(subset=required_cols).copy()

    X_parts: List[np.ndarray] = [np.ones(len(base))]
    names: List[str] = ["intercept"]

    if include_structural:
        for c in X_cols:
            X_parts.append(pd.to_numeric(base[c], errors="coerce").to_numpy(dtype=float))
            names.append(c)

    if year_as_numeric and "anio" in base.columns:
        # Año como variable numérica (permite extrapolar a un año no visto en train)
        year_num = pd.to_numeric(base["anio"], errors="coerce").to_numpy(dtype=float)
        X_parts.append(year_num)
        names.append("anio_num")
    elif use_dummies_year and "anio" in base.columns:
        d_year = pd.get_dummies(pd.to_numeric(base["anio"], errors="coerce").astype(int), prefix="year", drop_first=True)
        X_parts.append(d_year.to_numpy(dtype=float))
        names.extend(d_year.columns.tolist())

    if use_dummies_dataset and "dataset_id" in base.columns:
        d_ds = pd.get_dummies(base["dataset_id"].astype(str), prefix="ds", drop_first=True)
        X_parts.append(d_ds.to_numpy(dtype=float))
        names.extend(d_ds.columns.tolist())

    if use_dummies_barrio and "barrio_id" in base.columns:
        d_b = pd.get_dummies(pd.to_numeric(base["barrio_id"], errors="coerce").astype(int), prefix="barrio", drop_first=True)
        X_parts.append(d_b.to_numpy(dtype=float))
        names.extend(d_b.columns.tolist())

    X = np.column_stack(X_parts)
    return X, names, base


def train_eval_random_split(
    df: pd.DataFrame,
    config: TrainConfig,
    use_dummies_year: bool,
    use_dummies_dataset: bool,
    use_dummies_barrio: bool,
    year_as_numeric: bool = False,
    include_structural: bool = True,
) -> Dict[str, Any]:
    """Entrena/evalúa con split aleatorio."""
    rng = np.random.default_rng(config.seed)

    # Filtrar filas válidas
    X_all, names, base = build_design_matrix(
        df,
        use_dummies_year=use_dummies_year,
        use_dummies_dataset=use_dummies_dataset,
        use_dummies_barrio=use_dummies_barrio,
        year_as_numeric=year_as_numeric,
        include_structural=include_structural,
    )
    y_all = pd.to_numeric(base["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)

    n = len(y_all)
    idx = np.arange(n)
    rng.shuffle(idx)
    cut = int(round((1.0 - config.test_size) * n))
    train_idx, test_idx = idx[:cut], idx[cut:]

    X_train, y_train = X_all[train_idx], y_all[train_idx]
    X_test, y_test = X_all[test_idx], y_all[test_idx]

    beta = _ols_fit(X_train, y_train)
    pred_test = X_test @ beta

    return {
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "metrics_test": _metrics(y_test, pred_test),
        "feature_names": names,
        "beta": beta.astype(float).tolist(),
    }


def train_eval_temporal_split(
    df: pd.DataFrame,
    config: TrainConfig,
    use_dummies_year: bool,
    use_dummies_dataset: bool,
    use_dummies_barrio: bool,
    year_as_numeric: bool = False,
    include_structural: bool = True,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Entrena/evalúa con split temporal (train <= year-1, test == year)."""
    if "anio" not in df.columns:
        raise ValueError("El dataset macro no contiene columna 'anio' para split temporal.")

    required_cols: List[str] = ["precio_m2_mean", "anio"]
    if include_structural:
        required_cols.extend(
            [
                "superficie_m2_barrio_mean",
                "ano_construccion_barrio_mean",
                "plantas_barrio_mean",
            ],
        )
    if use_dummies_dataset:
        required_cols.append("dataset_id")
    if use_dummies_barrio:
        required_cols.append("barrio_id")

    base = df.dropna(subset=required_cols).copy()
    base["anio"] = pd.to_numeric(base["anio"], errors="coerce").astype(int)

    train_df = base[base["anio"] < config.temporal_test_year].copy()
    test_df = base[base["anio"] == config.temporal_test_year].copy()

    if train_df.empty or test_df.empty:
        raise ValueError(
            f"Split temporal inválido: train={len(train_df)} test={len(test_df)} para year={config.temporal_test_year}",
        )

    X_train, names, train_base = build_design_matrix(
        train_df,
        use_dummies_year=use_dummies_year,
        use_dummies_dataset=use_dummies_dataset,
        use_dummies_barrio=use_dummies_barrio,
        year_as_numeric=year_as_numeric,
        include_structural=include_structural,
    )
    y_train = pd.to_numeric(train_base["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)

    # Construir X_test usando las mismas columnas: para simplificar, construimos dummies en conjunto
    combo = pd.concat([train_df, test_df], ignore_index=True)
    X_combo, combo_names, combo_base = build_design_matrix(
        combo,
        use_dummies_year=use_dummies_year,
        use_dummies_dataset=use_dummies_dataset,
        use_dummies_barrio=use_dummies_barrio,
        year_as_numeric=year_as_numeric,
        include_structural=include_structural,
    )
    if combo_names != names:
        # Fallback robusto: asegurar que el diseño se basa en combo_names y entrenar también ahí
        names = combo_names

        # Re-split indices
        n_train = len(train_df)
        X_train = X_combo[:n_train]
        y_train = pd.to_numeric(combo_base.iloc[:n_train]["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)
        X_test = X_combo[n_train:]
        y_test = pd.to_numeric(combo_base.iloc[n_train:]["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)
        test_rows = combo_base.iloc[n_train:].copy()
    else:
        n_train = len(train_df)
        X_test = X_combo[n_train:]
        y_test = pd.to_numeric(combo_base.iloc[n_train:]["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)
        test_rows = combo_base.iloc[n_train:].copy()

    beta = _ols_fit(X_train, y_train)
    pred_test = X_test @ beta

    pred_df = test_rows.copy()
    pred_df["y_true"] = y_test
    pred_df["y_pred"] = pred_test
    pred_df["residual"] = pred_df["y_true"] - pred_df["y_pred"]

    return (
        {
            "temporal_test_year": int(config.temporal_test_year),
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "metrics_test": _metrics(y_test, pred_test),
            "feature_names": names,
            "beta": beta.astype(float).tolist(),
        },
        pred_df,
    )


def main() -> int:
    setup_logging()
    args = parse_args()
    cfg = TrainConfig(seed=int(args.seed), test_size=float(args.test_size), temporal_test_year=int(args.temporal_test_year))

    input_path = Path(args.input)
    report_path = Path(args.report)
    pred_out = Path(args.pred_out)

    if not input_path.exists():
        logger.error("Input no encontrado: %s", input_path)
        return 1

    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Input vacío: %s", input_path)
        return 1

    barrio_name_map = load_barrio_name_map()

    # Modelo 1 (in-sample fuerte): estructurales + dummies de año + dummies de dataset + dummies de barrio
    # Nota: NO extrapola bien a años no vistos en train (la dummy del año nuevo no se puede aprender).
    settings_dummies = {
        "use_dummies_year": True,
        "use_dummies_dataset": True,
        "use_dummies_barrio": True,
        "year_as_numeric": False,
        "include_structural": True,
    }

    # Modelo 2 (generalización temporal): estructurales + año numérico + dummies dataset + dummies barrio
    settings_year_trend = {
        "use_dummies_year": False,
        "use_dummies_dataset": True,
        "use_dummies_barrio": True,
        "year_as_numeric": True,
        "include_structural": True,
    }

    # Modelo 3 (coeficientes interpretables FE): anio_num + dummies dataset + dummies barrio (SIN estructurales)
    settings_fe_only = {
        "use_dummies_year": False,
        "use_dummies_dataset": True,
        "use_dummies_barrio": True,
        "year_as_numeric": True,
        "include_structural": False,
    }

    # Modelo 4 (interpretabilidad estructural): estructurales + anio_num + dummies dataset (SIN dummies barrio)
    settings_structural_only = {
        "use_dummies_year": False,
        "use_dummies_dataset": True,
        "use_dummies_barrio": False,
        "year_as_numeric": True,
        "include_structural": True,
    }

    logger.info("=== Macro baseline (Gràcia) ===")
    logger.info("Input: %s | filas=%s", input_path, len(df))
    logger.info("Config: %s", cfg)
    logger.info("Modelo dummies (año/dataset/barrio): %s", settings_dummies)
    logger.info("Modelo year-trend (anio_num + dataset/barrio): %s", settings_year_trend)
    logger.info("Modelo FE-only (anio_num + dataset/barrio; sin estructurales): %s", settings_fe_only)
    logger.info("Modelo Structural-only (estructurales + anio_num + dataset; sin barrio FE): %s", settings_structural_only)

    # Entrenar ambos y reportar
    random_eval_dummies = train_eval_random_split(df, cfg, **settings_dummies)
    temporal_eval_dummies, pred_df_dummies = train_eval_temporal_split(df, cfg, **settings_dummies)

    random_eval_trend = train_eval_random_split(df, cfg, **settings_year_trend)
    temporal_eval_trend, pred_df_trend = train_eval_temporal_split(df, cfg, **settings_year_trend)

    random_eval_fe = train_eval_random_split(df, cfg, **settings_fe_only)
    temporal_eval_fe, pred_df_fe = train_eval_temporal_split(df, cfg, **settings_fe_only)

    random_eval_struct = train_eval_random_split(df, cfg, **settings_structural_only)
    temporal_eval_struct, pred_df_struct = train_eval_temporal_split(df, cfg, **settings_structural_only)

    # Export coeficientes (validación adicional recomendada)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _export_coefs(
        *,
        model_key: str,
        split_key: str,
        df_source: pd.DataFrame,
        eval_obj: Dict[str, Any],
        settings: Dict[str, Any],
        cfg_local: TrainConfig,
    ) -> Path:
        baseline_info: Dict[str, Any] = {}
        if split_key == "temporal":
            subset_cols = ["precio_m2_mean", "anio"]
            if settings.get("include_structural", True):
                subset_cols.extend(
                    [
                        "superficie_m2_barrio_mean",
                        "ano_construccion_barrio_mean",
                        "plantas_barrio_mean",
                    ],
                )
            if settings.get("use_dummies_dataset"):
                subset_cols.append("dataset_id")
            if settings.get("use_dummies_barrio"):
                subset_cols.append("barrio_id")

            base = df_source.dropna(subset=subset_cols).copy()
            base["anio"] = pd.to_numeric(base["anio"], errors="coerce").astype(int)
            train_df_local = base[base["anio"] < cfg_local.temporal_test_year].copy()

            # Baseline categories (drop_first=True)
            if "barrio_id" in train_df_local.columns:
                bvals = sorted(pd.to_numeric(train_df_local["barrio_id"], errors="coerce").dropna().astype(int).unique().tolist())
                if bvals:
                    baseline_info["baseline_barrio_id"] = int(bvals[0])
                    baseline_info["baseline_barrio_nombre"] = barrio_name_map.get(int(bvals[0]), None)
            if "dataset_id" in train_df_local.columns:
                dsvals = sorted(train_df_local["dataset_id"].astype(str).dropna().unique().tolist())
                if dsvals:
                    baseline_info["baseline_dataset_id"] = str(dsvals[0])
            if settings.get("use_dummies_year") and "anio" in train_df_local.columns:
                yvals = sorted(pd.to_numeric(train_df_local["anio"], errors="coerce").dropna().astype(int).unique().tolist())
                if yvals:
                    baseline_info["baseline_year"] = int(yvals[0])

            X_train_local, names_local, train_base_local = build_design_matrix(train_df_local, **settings)
            y_train_local = pd.to_numeric(
                train_base_local["precio_m2_mean"],
                errors="coerce",
            ).to_numpy(dtype=float)
        else:
            # Para random split, re-generamos el mismo split con la misma semilla
            rng_local = np.random.default_rng(cfg_local.seed)
            subset_cols = ["precio_m2_mean"]
            if settings.get("include_structural", True):
                subset_cols.extend(
                    [
                        "superficie_m2_barrio_mean",
                        "ano_construccion_barrio_mean",
                        "plantas_barrio_mean",
                    ],
                )
            if settings.get("year_as_numeric") or settings.get("use_dummies_year"):
                subset_cols.append("anio")
            if settings.get("use_dummies_dataset"):
                subset_cols.append("dataset_id")
            if settings.get("use_dummies_barrio"):
                subset_cols.append("barrio_id")

            base = df_source.dropna(subset=subset_cols).copy()

            # Baseline categories (drop_first=True) sobre el universo usado en el split
            if "barrio_id" in base.columns:
                bvals = sorted(pd.to_numeric(base["barrio_id"], errors="coerce").dropna().astype(int).unique().tolist())
                if bvals:
                    baseline_info["baseline_barrio_id"] = int(bvals[0])
                    baseline_info["baseline_barrio_nombre"] = barrio_name_map.get(int(bvals[0]), None)
            if "dataset_id" in base.columns:
                dsvals = sorted(base["dataset_id"].astype(str).dropna().unique().tolist())
                if dsvals:
                    baseline_info["baseline_dataset_id"] = str(dsvals[0])
            if settings.get("use_dummies_year") and "anio" in base.columns:
                yvals = sorted(pd.to_numeric(base["anio"], errors="coerce").dropna().astype(int).unique().tolist())
                if yvals:
                    baseline_info["baseline_year"] = int(yvals[0])

            X_all_local, names_local, base_local = build_design_matrix(base, **settings)
            y_all_local = pd.to_numeric(base_local["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)

            n_local = len(y_all_local)
            idx_local = np.arange(n_local)
            rng_local.shuffle(idx_local)
            cut_local = int(round((1.0 - cfg_local.test_size) * n_local))
            train_idx_local = idx_local[:cut_local]

            X_train_local = X_all_local[train_idx_local]
            y_train_local = y_all_local[train_idx_local]

        coefs_df = ols_coefficients_table(
            X_train_local,
            y_train_local,
            names_local,
            barrio_name_map=barrio_name_map,
            baseline_info=baseline_info,
        )
        out_path = LOG_DIR / f"macro_baseline_coefficients_203_{model_key}_{split_key}.csv"
        coefs_df.to_csv(out_path, index=False, encoding="utf-8")

        # Guardar top features “interpretables” en el reporte (sin inflar demasiado el JSON)
        top = coefs_df[coefs_df["feature"] != "intercept"].head(15)
        eval_obj["top_coefficients"] = top[
            ["feature", "feature_type", "coeficiente", "std_error", "t_stat", "barrio_id", "barrio_nombre"]
        ].to_dict(orient="records")
        eval_obj["coefficients_path"] = str(out_path)
        eval_obj["baseline"] = baseline_info
        return out_path

    _export_coefs(
        model_key="dummies",
        split_key="random",
        df_source=df,
        eval_obj=random_eval_dummies,
        settings=settings_dummies,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="dummies",
        split_key="temporal",
        df_source=df,
        eval_obj=temporal_eval_dummies,
        settings=settings_dummies,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="year_trend",
        split_key="random",
        df_source=df,
        eval_obj=random_eval_trend,
        settings=settings_year_trend,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="year_trend",
        split_key="temporal",
        df_source=df,
        eval_obj=temporal_eval_trend,
        settings=settings_year_trend,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="fe_only",
        split_key="random",
        df_source=df,
        eval_obj=random_eval_fe,
        settings=settings_fe_only,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="fe_only",
        split_key="temporal",
        df_source=df,
        eval_obj=temporal_eval_fe,
        settings=settings_fe_only,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="structural_only",
        split_key="random",
        df_source=df,
        eval_obj=random_eval_struct,
        settings=settings_structural_only,
        cfg_local=cfg,
    )
    _export_coefs(
        model_key="structural_only",
        split_key="temporal",
        df_source=df,
        eval_obj=temporal_eval_struct,
        settings=settings_structural_only,
        cfg_local=cfg,
    )

    pred_out.parent.mkdir(parents=True, exist_ok=True)
    pred_out_dummies = pred_out.with_name("macro_baseline_predictions_203_temporal_dummies.csv")
    pred_out_trend = pred_out.with_name("macro_baseline_predictions_203_temporal_year_trend.csv")
    pred_out_fe = pred_out.with_name("macro_baseline_predictions_203_temporal_fe_only.csv")
    pred_out_struct = pred_out.with_name("macro_baseline_predictions_203_temporal_structural_only.csv")

    pred_df_dummies.to_csv(pred_out_dummies, index=False, encoding="utf-8")
    pred_df_trend.to_csv(pred_out_trend, index=False, encoding="utf-8")
    pred_df_fe.to_csv(pred_out_fe, index=False, encoding="utf-8")
    pred_df_struct.to_csv(pred_out_struct, index=False, encoding="utf-8")
    logger.info("Predicciones temporal (dummies) guardadas: %s", pred_out_dummies)
    logger.info("Predicciones temporal (year-trend) guardadas: %s", pred_out_trend)
    logger.info("Predicciones temporal (fe-only) guardadas: %s", pred_out_fe)
    logger.info("Predicciones temporal (structural-only) guardadas: %s", pred_out_struct)

    report: Dict[str, Any] = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "macro_dataset_shape": [int(df.shape[0]), int(df.shape[1])],
        "models": {
            "dummies": {
                "settings": settings_dummies,
                "random_split": random_eval_dummies,
                "temporal_split": temporal_eval_dummies,
                "pred_path_temporal": str(pred_out_dummies),
            },
            "year_trend": {
                "settings": settings_year_trend,
                "random_split": random_eval_trend,
                "temporal_split": temporal_eval_trend,
                "pred_path_temporal": str(pred_out_trend),
            },
            "fe_only": {
                "settings": settings_fe_only,
                "random_split": random_eval_fe,
                "temporal_split": temporal_eval_fe,
                "pred_path_temporal": str(pred_out_fe),
            },
            "structural_only": {
                "settings": settings_structural_only,
                "random_split": random_eval_struct,
                "temporal_split": temporal_eval_struct,
                "pred_path_temporal": str(pred_out_struct),
            },
        },
        "notes": {
            "scope": "Baseline macro v0.1 (no micro-hedonic).",
            "why": "Portal Dades precio_m2 es agregado; Catastro Fase 1 no aporta X micro real para ese y.",
            "tip": "Para evaluación realista, preferir split temporal y modelo con `anio_num` (year_trend).",
        },
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Reporte guardado: %s", report_path)

    # Print compacto: top coeficientes del modelo recomendado (YEAR_TREND temporal)
    try:
        top_year_trend = temporal_eval_trend.get("top_coefficients", [])[:10]
        if top_year_trend:
            logger.info("Top coeficientes (YEAR_TREND temporal) por |coef|:")
            for row in top_year_trend:
                logger.info(
                    "  %s: coef=%.3f se=%.3f t=%.2f",
                    row["feature"],
                    float(row["coeficiente"]),
                    float(row["std_error"]),
                    float(row["t_stat"]) if row["t_stat"] == row["t_stat"] else float("nan"),
                )
    except Exception as exc:
        logger.warning("No se pudieron imprimir coeficientes top: %s", exc)

    logger.info(
        "DUMMIES random R2=%.3f RMSE=%.2f | temporal(%s) R2=%.3f RMSE=%.2f",
        random_eval_dummies["metrics_test"]["r2"],
        random_eval_dummies["metrics_test"]["rmse"],
        temporal_eval_dummies["temporal_test_year"],
        temporal_eval_dummies["metrics_test"]["r2"],
        temporal_eval_dummies["metrics_test"]["rmse"],
    )
    logger.info(
        "YEAR_TREND random R2=%.3f RMSE=%.2f | temporal(%s) R2=%.3f RMSE=%.2f",
        random_eval_trend["metrics_test"]["r2"],
        random_eval_trend["metrics_test"]["rmse"],
        temporal_eval_trend["temporal_test_year"],
        temporal_eval_trend["metrics_test"]["r2"],
        temporal_eval_trend["metrics_test"]["rmse"],
    )
    logger.info(
        "FE_ONLY random R2=%.3f RMSE=%.2f | temporal(%s) R2=%.3f RMSE=%.2f",
        random_eval_fe["metrics_test"]["r2"],
        random_eval_fe["metrics_test"]["rmse"],
        temporal_eval_fe["temporal_test_year"],
        temporal_eval_fe["metrics_test"]["r2"],
        temporal_eval_fe["metrics_test"]["rmse"],
    )
    logger.info(
        "STRUCT_ONLY random R2=%.3f RMSE=%.2f | temporal(%s) R2=%.3f RMSE=%.2f",
        random_eval_struct["metrics_test"]["r2"],
        random_eval_struct["metrics_test"]["rmse"],
        temporal_eval_struct["temporal_test_year"],
        temporal_eval_struct["metrics_test"]["r2"],
        temporal_eval_struct["metrics_test"]["rmse"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


