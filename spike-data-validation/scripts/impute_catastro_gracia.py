#!/usr/bin/env python3
"""
Imputación estadística de atributos catastrales para el spike de Gràcia (Fase 1).

Contexto:
- `Consulta_DNPRC` / `Consulta_DNPLOC` fallan con error 12 ("LA PROVINCIA NO EXISTE")
- `Consulta_RCCOOR` funciona y nos da: referencia (14 chars), coords, dirección

Objetivo:
Generar un CSV utilizable por Issue #201 con columnas:
- barrio_id (obtenido por spatial join coords -> barrio)
- superficie_m2, ano_construccion, plantas (imputados)
- trazabilidad: datos_imputados=True, metodo_obtencion="imputacion_estadistica"

Inputs/Outputs (por defecto):
- Input:  spike-data-validation/data/raw/catastro_gracia_coords.csv
- Output: spike-data-validation/data/processed/catastro_gracia_imputado.csv
- Log:    spike-data-validation/data/logs/imputacion_summary.json

Nota:
Ejecutar con `.venv-spike/bin/python` (en algunos entornos `python3` del sistema puede fallar
al importar numpy/pandas).
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

logger = logging.getLogger(__name__)

RAW_DIR = Path("spike-data-validation/data/raw")
PROCESSED_DIR = Path("spike-data-validation/data/processed")
LOG_DIR = Path("spike-data-validation/data/logs")

DEFAULT_INPUT = RAW_DIR / "catastro_gracia_coords.csv"
DEFAULT_OUTPUT = PROCESSED_DIR / "catastro_gracia_imputado.csv"
DEFAULT_SUMMARY = LOG_DIR / "imputacion_summary.json"

# GeoJSON oficial ya presente en el repo (NO modificar, solo leer)
DEFAULT_BARRIOS_GEOJSON = Path("data/raw/geojson/barrios_geojson_20251115_162533_398394.json")

# Barrios de Gràcia (codi_barri oficial) -> 5 barrios
GRACIA_BARRIO_IDS = {28, 29, 30, 31, 32}


def _fix_mojibake(text: Optional[str]) -> Optional[str]:
    """
    Intenta corregir cadenas con mojibake (p.ej. 'GrÃ cia' -> 'Gràcia').
    """
    if not text:
        return text
    if "Ã" not in text:
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _debug_log(hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
    """Escribe una línea NDJSON al debug log (sin secretos)."""
    # #region agent log
    import time

    payload = {
        "sessionId": "debug-session",
        "runId": "run8",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log", "a") as f:
        f.write(json.dumps(payload) + "\n")
    # #endregion


@dataclass(frozen=True)
class BarrioImputationStats:
    """Parámetros de imputación por barrio_id."""

    superficie_mean: float
    superficie_std: float
    # Distribución por bandas (año_min, año_max, peso)
    year_bands: Tuple[Tuple[int, int, float], ...]


def setup_logging() -> None:
    """Configura logging para el script."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(LOG_DIR / "imputacion.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def _default_stats_by_barrio() -> Dict[int, BarrioImputationStats]:
    """
    Define priors plausibles por barrio de Gràcia.

    Nota:
    - Estos priors NO son datos reales del Catastro.
    - Son suficientes para validar arquitectura y desbloquear Issue #201.
    """
    return {
        # Vallcarca i els Penitents: más heterogéneo, mix casas/edificios
        28: BarrioImputationStats(
            superficie_mean=90.0,
            superficie_std=30.0,
            year_bands=((1900, 1949, 0.12), (1950, 1979, 0.50), (1980, 1999, 0.28), (2000, 2024, 0.10)),
        ),
        # el Coll: viviendas algo más pequeñas en promedio
        29: BarrioImputationStats(
            superficie_mean=80.0,
            superficie_std=24.0,
            year_bands=((1900, 1949, 0.10), (1950, 1979, 0.55), (1980, 1999, 0.25), (2000, 2024, 0.10)),
        ),
        # Camp d'en Grassot i Gràcia Nova: mix, boom 1950-80
        30: BarrioImputationStats(
            superficie_mean=85.0,
            superficie_std=25.0,
            year_bands=((1900, 1949, 0.08), (1950, 1979, 0.60), (1980, 1999, 0.22), (2000, 2024, 0.10)),
        ),
        # la Vila de Gràcia: stock más antiguo
        31: BarrioImputationStats(
            superficie_mean=82.0,
            superficie_std=24.0,
            year_bands=((1900, 1949, 0.20), (1950, 1979, 0.50), (1980, 1999, 0.20), (2000, 2024, 0.10)),
        ),
        # la Salut: algo más variado y algo más grande
        32: BarrioImputationStats(
            superficie_mean=88.0,
            superficie_std=28.0,
            year_bands=((1900, 1949, 0.12), (1950, 1979, 0.52), (1980, 1999, 0.26), (2000, 2024, 0.10)),
        ),
    }


def load_gracia_barrios_geometry(geojson_path: Path) -> Dict[int, Dict[str, Any]]:
    """
    Carga geometrías de los 5 barrios de Gràcia desde un FeatureCollection GeoJSON.

    Args:
        geojson_path: Ruta al GeoJSON de barrios (Barcelona).

    Returns:
        Diccionario barrio_id -> {'geometry': shapely, 'properties': {...}, 'prepared': prepared_geom}

    Raises:
        FileNotFoundError: Si el geojson no existe.
        ValueError: Si el formato no es un FeatureCollection.
    """
    if not geojson_path.exists():
        raise FileNotFoundError(f"No se encontró GeoJSON de barrios: {geojson_path}")

    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"GeoJSON inesperado (type={payload.get('type')}); se esperaba FeatureCollection")

    barrios: Dict[int, Dict[str, Any]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        barrio_id = props.get("codi_barri")
        if barrio_id in GRACIA_BARRIO_IDS:
            geom = shape(feature.get("geometry"))
            barrios[int(barrio_id)] = {
                "geometry": geom,
                "prepared": prep(geom),
                "properties": {
                    **props,
                    "nom_barri": _fix_mojibake(props.get("nom_barri")),
                    "nom_districte": _fix_mojibake(props.get("nom_districte")),
                },
            }

    if len(barrios) != 5:
        logger.warning(
            "Se esperaban 5 barrios de Gràcia, encontrados %s (ids=%s)",
            len(barrios),
            sorted(barrios.keys()),
        )
    return barrios


def assign_barrio_id(
    df: pd.DataFrame,
    barrios: Dict[int, Dict[str, Any]],
    lon_col: str = "lon",
    lat_col: str = "lat",
) -> pd.DataFrame:
    """
    Asigna barrio_id a cada registro por punto-en-polígono; fallback por nearest.

    Args:
        df: DataFrame con lon/lat.
        barrios: Dict barrio_id -> geometría shapely.
        lon_col: Nombre de columna longitud.
        lat_col: Nombre de columna latitud.

    Returns:
        DataFrame con columnas `barrio_id` y `barrio_nombre` (si disponible).
    """
    df_out = df.copy()

    if lon_col not in df_out.columns or lat_col not in df_out.columns:
        raise ValueError(f"Faltan columnas de coordenadas: {lon_col}/{lat_col}")

    df_out[lon_col] = pd.to_numeric(df_out[lon_col], errors="coerce")
    df_out[lat_col] = pd.to_numeric(df_out[lat_col], errors="coerce")

    barrio_ids: List[Optional[int]] = []
    barrio_names: List[Optional[str]] = []

    # Preparar lista para fallback
    barrio_items = [(bid, info["geometry"], info["prepared"], info["properties"]) for bid, info in barrios.items()]

    for _, row in df_out.iterrows():
        lon = row[lon_col]
        lat = row[lat_col]
        if pd.isna(lon) or pd.isna(lat):
            barrio_ids.append(None)
            barrio_names.append(None)
            continue

        pt = Point(float(lon), float(lat))

        # 1) contains
        match_id: Optional[int] = None
        match_name: Optional[str] = None
        for bid, geom, prepared_geom, props in barrio_items:
            if prepared_geom.contains(pt):
                match_id = int(bid)
                match_name = props.get("nom_barri") or props.get("nom_barri_alt") or None
                break

        # 2) nearest barrio (si está fuera)
        if match_id is None:
            best_bid = None
            best_dist = None
            best_props: Optional[Dict[str, Any]] = None
            for bid, geom, _, props in barrio_items:
                dist = pt.distance(geom)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_bid = int(bid)
                    best_props = props
            match_id = best_bid
            match_name = (best_props or {}).get("nom_barri") if best_props else None

        barrio_ids.append(match_id)
        barrio_names.append(match_name)

    df_out["barrio_id"] = barrio_ids
    df_out["barrio_nombre"] = barrio_names

    # Auditoría: si el input trae barrio_id_seed, calcular mismatches
    if "barrio_id_seed" in df_out.columns:
        seed_series = pd.to_numeric(df_out["barrio_id_seed"], errors="coerce")
        calc_series = pd.to_numeric(df_out["barrio_id"], errors="coerce")
        mismatch = (
            seed_series.notna()
            & calc_series.notna()
            & (seed_series.astype(int) != calc_series.astype(int))
        )
        df_out["barrio_mismatch_seed_vs_spatial"] = mismatch
        mismatches = int(mismatch.sum())
        if mismatches > 0:
            logger.warning("⚠️ Mismatches barrio_id_seed vs spatial_join: %s", mismatches)
        _debug_log(
            "IMPUTE_PHASE1",
            "impute_catastro_gracia.py:assign_barrio_id",
            "Mismatch_seed_vs_spatial",
            {"mismatches": mismatches, "with_seed": int(seed_series.notna().sum())},
        )
    return df_out


def _sample_truncated_normal(mu: float, sigma: float, lower: float, upper: float) -> float:
    """Samplea Normal(mu, sigma) con truncamiento simple por rechazo."""
    for _ in range(200):
        x = random.gauss(mu, sigma)
        if lower <= x <= upper:
            return x
    # fallback
    return min(max(mu, lower), upper)


def _sample_year_from_bands(bands: Tuple[Tuple[int, int, float], ...]) -> int:
    """Samplea un año a partir de bandas con pesos."""
    choices = list(bands)
    weights = [b[2] for b in choices]
    (ymin, ymax, _) = random.choices(choices, weights=weights, k=1)[0]
    return random.randint(int(ymin), int(ymax))


def _infer_plantas_from_year(year: int) -> int:
    """Heurística de plantas basada en año de construcción (con ruido)."""
    if year < 1950:
        base = random.randint(3, 4)
    elif year < 1980:
        base = random.randint(5, 7)
    else:
        base = random.randint(4, 6)
    base += random.choice([-1, 0, 0, 1])
    return int(min(max(base, 1), 12))


def impute_attributes(df: pd.DataFrame, stats_by_barrio: Dict[int, BarrioImputationStats]) -> pd.DataFrame:
    """
    Imputa superficie, año y plantas por barrio_id.

    Args:
        df: DataFrame con columna `barrio_id`.
        stats_by_barrio: priors por barrio.

    Returns:
        DataFrame con columnas imputadas y flags de trazabilidad.
    """
    if "barrio_id" not in df.columns:
        raise ValueError("El DataFrame debe contener 'barrio_id' antes de imputar")

    df_out = df.copy()

    superficies: List[Optional[float]] = []
    anos: List[Optional[int]] = []
    plantas: List[Optional[int]] = []

    for _, row in df_out.iterrows():
        barrio_id = row.get("barrio_id")
        if pd.isna(barrio_id):
            superficies.append(None)
            anos.append(None)
            plantas.append(None)
            continue

        bid = int(barrio_id)
        priors = stats_by_barrio.get(bid)
        if not priors:
            # fallback global
            priors = BarrioImputationStats(
                superficie_mean=85.0,
                superficie_std=25.0,
                year_bands=((1900, 1949, 0.12), (1950, 1979, 0.55), (1980, 1999, 0.23), (2000, 2024, 0.10)),
            )

        sup = _sample_truncated_normal(priors.superficie_mean, priors.superficie_std, 30.0, 300.0)
        year = _sample_year_from_bands(priors.year_bands)
        pl = _infer_plantas_from_year(year)

        superficies.append(round(float(sup), 1))
        anos.append(int(year))
        plantas.append(int(pl))

    df_out["superficie_m2"] = superficies
    df_out["ano_construccion"] = anos
    df_out["plantas"] = plantas

    df_out["datos_imputados"] = True
    df_out["metodo_obtencion"] = "imputacion_estadistica"

    return df_out


def validate_ranges(df: pd.DataFrame) -> None:
    """
    Valida rangos y completitud.

    Raises:
        ValueError: Si se violan criterios básicos.
    """
    required = ["barrio_id", "superficie_m2", "ano_construccion", "plantas"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    if df[required].isna().any().any():
        nulls = df[required].isna().sum().to_dict()
        raise ValueError(f"Hay nulos en columnas críticas: {nulls}")

    sup_ok = df["superficie_m2"].between(30, 300).all()
    year_ok = df["ano_construccion"].between(1900, datetime.now().year).all()
    pl_ok = df["plantas"].between(1, 12).all()
    if not (sup_ok and year_ok and pl_ok):
        raise ValueError(
            "Rangos fuera de lo esperado: "
            f"superficie_ok={sup_ok}, year_ok={year_ok}, plantas_ok={pl_ok}"
        )


def write_summary(
    df: pd.DataFrame,
    input_path: Path,
    output_path: Path,
    summary_path: Path,
) -> None:
    """Escribe un JSON de trazabilidad/resumen de imputación."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "fase": "imputacion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "output": str(output_path),
        "registros_procesados": int(len(df)),
        "metodo": "imputacion_estadistica",
        "nota": "Datos imputados - Reemplazo con reales pendiente (Fase 2)",
        "completitud": {
            "superficie_m2": float(df["superficie_m2"].notna().mean()),
            "ano_construccion": float(df["ano_construccion"].notna().mean()),
            "plantas": float(df["plantas"].notna().mean()),
        },
        "estadisticas": {
            "superficie_media": float(df["superficie_m2"].mean()),
            "superficie_std": float(df["superficie_m2"].std(ddof=0)),
            "año_min": int(df["ano_construccion"].min()),
            "año_max": int(df["ano_construccion"].max()),
            "plantas_media": float(df["plantas"].mean()),
        },
        "barrios_representados": int(df["barrio_id"].nunique()),
        "conteo_por_barrio": df["barrio_id"].value_counts().sort_index().to_dict(),
    }

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--summary", type=str, default=str(DEFAULT_SUMMARY))
    parser.add_argument("--barrios-geojson", type=str, default=str(DEFAULT_BARRIOS_GEOJSON))
    parser.add_argument("--seed", type=int, default=42, help="Seed RNG para reproducibilidad")
    parser.add_argument(
        "--filter-gracia",
        action="store_true",
        help="Filtra a los 5 barrios de Gràcia (28-32) tras el spatial join",
    )
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()
    random.seed(int(args.seed))

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    geojson_path = Path(args.barrios_geojson)

    logger.info("=== Issue #200 (Fase 1): Imputación estadística por barrio ===")
    logger.info("Input: %s", input_path)
    logger.info("GeoJSON barrios: %s", geojson_path)

    if not input_path.exists():
        logger.error("No existe input: %s", input_path)
        return 1

    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Input vacío: %s", input_path)
        return 1

    # #region agent log
    import time
    with open("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log", "a") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "debug-session",
                    "runId": "run8",
                    "hypothesisId": "IMPUTE_PHASE1",
                    "location": "impute_catastro_gracia.py:main",
                    "message": "Entrada",
                    "data": {"rows": len(df), "cols": df.columns.tolist()},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    # #endregion

    barrios = load_gracia_barrios_geometry(geojson_path)
    df = assign_barrio_id(df, barrios, lon_col="lon", lat_col="lat")

    if args.filter_gracia:
        before = len(df)
        df = df[df["barrio_id"].isin(sorted(GRACIA_BARRIO_IDS))].copy()
        logger.info("Filtrado Gràcia (28-32): %s -> %s filas", before, len(df))

    stats_by_barrio = _default_stats_by_barrio()
    df = impute_attributes(df, stats_by_barrio=stats_by_barrio)
    validate_ranges(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    write_summary(df, input_path=input_path, output_path=output_path, summary_path=summary_path)

    # #region agent log
    with open("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log", "a") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "debug-session",
                    "runId": "run8",
                    "hypothesisId": "IMPUTE_PHASE1",
                    "location": "impute_catastro_gracia.py:main",
                    "message": "Salida",
                    "data": {
                        "output": str(output_path),
                        "rows": len(df),
                        "barrios": int(df["barrio_id"].nunique()),
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    # #endregion

    logger.info("✓ CSV imputado guardado: %s", output_path)
    logger.info("✓ Resumen imputación guardado: %s", summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


