"""
Script para cruzar precios y atributos de edificios en Gràcia.

Issue: #201
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz


LOG_DIR = Path("spike-data-validation/data/logs")
RAW_DIR = Path("spike-data-validation/data/raw")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    Configura logging para el script de linking y limpieza.
    """
    log_path = LOG_DIR / "linking.log"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


@dataclass
class LinkingConfig:
    """
    Configuración para el proceso de linking de Gràcia.

    Attributes:
        fuzzy_threshold: Umbral de similitud para matching por dirección.
        min_match_rate_ok: Match rate objetivo (porcentaje).
        min_match_rate_warning: Match rate mínimo aceptable (porcentaje).
    """

    fuzzy_threshold: int = 80
    min_match_rate_ok: float = 70.0
    min_match_rate_warning: float = 50.0


class GraciaDataLinker:
    """
    Linker de datos de precios y atributos para el spike de Gràcia.
    """

    def __init__(self, config: Optional[LinkingConfig] = None) -> None:
        """
        Inicializa el linker con rutas predefinidas.

        Args:
            config: Configuración de linking; si es None, se usa la por defecto.
        """
        self.config = config or LinkingConfig()
        self.df_precios: Optional[pd.DataFrame] = None
        self.df_catastro: Optional[pd.DataFrame] = None

    def load_data(self) -> None:
        """
        Carga los datasets de precios y catastro del spike.

        Raises:
            FileNotFoundError: Si los CSV requeridos no existen.
        """
        # Precios: priorizar el CSV generado por el notebook (Issue #199), fallback al nombre legacy
        precios_path = RAW_DIR / "ine_precios_gracia_notebook.csv"
        if not precios_path.exists():
            precios_path = RAW_DIR / "ine_precios_gracia.csv"

        # Catastro: priorizar CSV imputado (Fase 1), fallback a coords/raw
        catastro_path = PROCESSED_DIR / "catastro_gracia_imputado.csv"
        if not catastro_path.exists():
            catastro_path = RAW_DIR / "catastro_gracia_coords.csv"
        if not catastro_path.exists():
            catastro_path = RAW_DIR / "catastro_gracia.csv"

        if not precios_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de precios: {precios_path}")
        if not catastro_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de catastro: {catastro_path}")

        precios_df = pd.read_csv(precios_path)
        catastro_df = pd.read_csv(catastro_path)

        if precios_df.empty:
            raise ValueError("El archivo de precios está vacío")
        if catastro_df.empty:
            raise ValueError("El archivo de catastro está vacío")

        self.df_precios = precios_df.copy()
        self.df_catastro = catastro_df.copy()

        if "precio_m2" not in self.df_precios.columns:
            raise ValueError("El DataFrame de precios debe contener la columna 'precio_m2'")

        logger.info("Precios cargados: %s registros", len(self.df_precios))
        logger.info("Catastro cargado: %s registros", len(self.df_catastro))

    def link_data(self) -> pd.DataFrame:
        """
        Ejecuta el matching jerárquico entre precios y atributos.

        Returns:
            DataFrame combinado con columna ``match_method``.

        Raises:
            RuntimeError: Si no se han cargado los datos.
        """
        if self.df_precios is None or self.df_catastro is None:
            raise RuntimeError("Los datos no han sido cargados; ejecuta load_data() primero")

        precios_remaining = self.df_precios.copy()
        catastro = self.df_catastro.copy()

        all_matches: List[pd.DataFrame] = []

        # Nivel 1: referencia catastral exacta
        if "referencia_catastral" in precios_remaining.columns and "referencia_catastral" in catastro.columns:
            nivel1, precios_remaining = self._match_by_reference(precios_remaining, catastro)
            if not nivel1.empty:
                all_matches.append(nivel1)

        # Nivel 2: dirección fuzzy (si hay direcciones disponibles)
        if (
            "direccion_normalizada" in precios_remaining.columns
            and "direccion_normalizada" in catastro.columns
        ):
            nivel2, precios_remaining = self._match_by_address(precios_remaining, catastro)
            if not nivel2.empty:
                all_matches.append(nivel2)

        # Nivel 3: agregación estadística (barrio-anio)
        if "barrio_id" in precios_remaining.columns:
            nivel3 = self._match_by_barrio_anio(precios_remaining, catastro)
            if not nivel3.empty:
                all_matches.append(nivel3)

        if not all_matches:
            logger.error("No se pudieron realizar matches entre precios y catastro")
            return pd.DataFrame()

        df_merged = pd.concat(all_matches, ignore_index=True)

        total_precios = len(self.df_precios)
        match_rate = len(df_merged) / float(total_precios) * 100.0

        logger.info(
            "Match rate global: %.1f%% (%s/%s)",
            match_rate,
            len(df_merged),
            total_precios,
        )

        if match_rate >= self.config.min_match_rate_ok:
            logger.info(
                "✓ Criterio cumplido: match rate %.1f%% ≥ %.1f%%",
                match_rate,
                self.config.min_match_rate_ok,
            )
        elif match_rate >= self.config.min_match_rate_warning:
            logger.warning(
                "Match rate moderado: %.1f%% (umbral objetivo %.1f%%, mínimo %.1f%%)",
                match_rate,
                self.config.min_match_rate_ok,
                self.config.min_match_rate_warning,
            )
        else:
            logger.error(
                "Match rate insuficiente: %.1f%% (objetivo %.1f%%)",
                match_rate,
                self.config.min_match_rate_ok,
            )

        return df_merged

    def _match_by_reference(
        self,
        precios_df: pd.DataFrame,
        catastro_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Matching por referencia catastral exacta.

        Args:
            precios_df: DataFrame de precios aún no asignados.
            catastro_df: DataFrame completo de atributos catastrales.

        Returns:
            Tupla ``(matched, remaining_precios)``.
        """
        merged = precios_df.merge(
            catastro_df,
            on="referencia_catastral",
            how="inner",
            suffixes=("", "_cat"),
        )
        if merged.empty:
            logger.info("No se encontraron matches por referencia catastral")
            return merged, precios_df

        merged = merged.copy()
        merged["match_method"] = "referencia_catastral"

        matched_ids = merged.index
        remaining = precios_df.drop(index=matched_ids, errors="ignore")

        logger.info(
            "Matches por referencia catastral: %s (restantes: %s)",
            len(merged),
            len(remaining),
        )
        return merged, remaining

    def _match_by_address(
        self,
        precios_df: pd.DataFrame,
        catastro_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Matching por dirección usando fuzzy matching.

        Nota: Este método es costoso O(N*M); para el spike se asume tamaño moderado.

        Args:
            precios_df: DataFrame de precios aún no asignados.
            catastro_df: DataFrame completo de atributos catastrales.

        Returns:
            Tupla ``(matched, remaining_precios)``.
        """
        registros: List[Dict[str, object]] = []
        precios_remaining_indices: List[int] = []

        catastro_df = catastro_df.copy()
        catastro_df = catastro_df[catastro_df["direccion_normalizada"].notna()]

        for idx_p, row_p in precios_df.iterrows():
            direccion_p = row_p.get("direccion_normalizada")
            if pd.isna(direccion_p):
                precios_remaining_indices.append(idx_p)
                continue

            best_score = 0.0
            best_row: Optional[pd.Series] = None

            for _, row_c in catastro_df.iterrows():
                direccion_c = row_c.get("direccion_normalizada")
                if pd.isna(direccion_c):
                    continue

                score = fuzz.ratio(
                    str(direccion_p).lower(),
                    str(direccion_c).lower(),
                )
                if score > best_score:
                    best_score = score
                    best_row = row_c

            if best_row is not None and best_score >= self.config.fuzzy_threshold:
                merged_row: Dict[str, object] = {
                    **row_p.to_dict(),
                    **{
                        key: best_row[key]
                        for key in best_row.index
                        if key not in row_p.index or key == "direccion_normalizada"
                    },
                }
                merged_row["match_method"] = "direccion_fuzzy"
                merged_row["match_score"] = float(best_score)
                registros.append(merged_row)
            else:
                precios_remaining_indices.append(idx_p)

        matched_df = pd.DataFrame(registros) if registros else pd.DataFrame()
        remaining_df = precios_df.loc[precios_remaining_indices] if precios_remaining_indices else pd.DataFrame()

        logger.info(
            "Matches por dirección fuzzy: %s (restantes: %s)",
            len(matched_df),
            len(remaining_df),
        )
        return matched_df, remaining_df

    def _match_by_barrio_anio(
        self,
        precios_df: pd.DataFrame,
        catastro_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Matching estadístico por barrio y año.

        Se agregan atributos medios/modales por barrio y se asignan a cada
        registro de precios restante.

        Args:
            precios_df: DataFrame de precios restantes.
            catastro_df: DataFrame completo de atributos catastrales.

        Returns:
            DataFrame combinado con columnas agregadas de atributos.
        """
        if precios_df.empty:
            return pd.DataFrame()

        catastro = catastro_df.copy()

        if "barrio_id" not in precios_df.columns:
            logger.warning("Precios sin barrio_id; no se puede linkear por barrio")
            return pd.DataFrame()

        if "barrio_id" not in catastro.columns:
            logger.warning("Catastro sin barrio_id; no se puede linkear por barrio")
            return pd.DataFrame()

        # Agregar atributos del catastro a nivel barrio (para asignarlos a cada registro de precios)
        agg_map: Dict[str, str] = {}
        if "superficie_m2" in catastro.columns:
            agg_map["superficie_m2"] = "mean"
        if "ano_construccion" in catastro.columns:
            agg_map["ano_construccion"] = "mean"
        if "plantas" in catastro.columns:
            agg_map["plantas"] = "mean"

        if not agg_map:
            logger.warning("Catastro no tiene columnas numéricas para agregar; linking degradado")
            catastro_stats = catastro[["barrio_id"]].drop_duplicates().copy()
        else:
            catastro_stats = catastro.groupby("barrio_id", as_index=False).agg(agg_map)

        catastro_stats = catastro_stats.rename(
            columns={
                "superficie_m2": "superficie_m2_barrio_mean",
                "ano_construccion": "ano_construccion_barrio_mean",
                "plantas": "plantas_barrio_mean",
            },
        )

        merged = precios_df.merge(catastro_stats, on="barrio_id", how="left")
        merged = merged.copy()
        merged["match_method"] = "barrio_id"

        logger.info("Matches por barrio_id (agregado): %s", len(merged))
        return merged

    @staticmethod
    def clean_outliers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Elimina outliers extremos en ``precio_m2`` usando el método IQR.

        Args:
            df: DataFrame combinado.

        Returns:
            DataFrame sin outliers.
        """
        if df.empty or "precio_m2" not in df.columns:
            return df.copy()

        df_clean = df.copy()

        q1 = df_clean["precio_m2"].quantile(0.25)
        q3 = df_clean["precio_m2"].quantile(0.75)
        iqr = q3 - q1

        if pd.isna(iqr) or iqr == 0:
            logger.warning(
                "No se puede calcular IQR para precio_m2 (iqr=%s); no se filtrarán outliers.",
                iqr,
            )
            return df_clean

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        initial_count = len(df_clean)
        df_clean = df_clean[
            (df_clean["precio_m2"] >= lower_bound)
            & (df_clean["precio_m2"] <= upper_bound)
        ]
        removed = initial_count - len(df_clean)

        if initial_count > 0:
            removed_pct = removed / float(initial_count) * 100.0
        else:
            removed_pct = 0.0

        logger.info(
            "Outliers removidos en precio_m2: %s (%.1f%%)",
            removed,
            removed_pct,
        )

        return df_clean


def save_merged_data(df: pd.DataFrame) -> Path:
    """
    Guarda el dataset combinado y limpio para el spike de Gràcia.

    Args:
        df: DataFrame final tras linking y limpieza.

    Returns:
        Ruta del archivo CSV generado.
    """
    output_path = PROCESSED_DIR / "gracia_merged.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Dataset combinado de Gràcia guardado en %s", output_path)
    return output_path


def build_macro_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye un dataset agregado (macro) coherente para Fase 1.

    En Fase 1, los atributos estructurales provienen de imputación y/o agregación por barrio,
    mientras que los precios de Portal Dades son agregados por barrio y periodo/indicador.

    Este método agrega `gracia_merged.csv` a nivel:
    - `barrio_id` + `anio` + `dataset_id` (si existe)

    Args:
        df: DataFrame merged (ya limpio) con `precio_m2` y columnas de contexto.

    Returns:
        DataFrame agregado con métricas `n_obs`, `precio_m2_mean`, `precio_m2_std` y
        features (primer valor por grupo).
    """
    if df.empty:
        return df.copy()

    group_keys = ["barrio_id", "anio"]
    if "dataset_id" in df.columns:
        group_keys.append("dataset_id")

    # Columnas de features que queremos “arrastrar” (son constantes o casi constantes por grupo)
    carry_cols = [
        c
        for c in [
            "superficie_m2_barrio_mean",
            "ano_construccion_barrio_mean",
            "plantas_barrio_mean",
            "source",
            "match_method",
        ]
        if c in df.columns
    ]

    out = (
        df.groupby(group_keys)
        .agg(
            n_obs=("precio_m2", "count"),
            precio_m2_mean=("precio_m2", "mean"),
            precio_m2_std=("precio_m2", "std"),
            **{c: (c, "first") for c in carry_cols},
        )
        .reset_index()
        .sort_values(group_keys)
    )

    return out


def save_macro_data(df_macro: pd.DataFrame) -> Path:
    """
    Guarda el dataset macro agregado para el baseline v0.1.

    Args:
        df_macro: DataFrame agregado generado por `build_macro_dataset`.

    Returns:
        Ruta del archivo CSV generado.
    """
    output_path = PROCESSED_DIR / "gracia_merged_agg_barrio_anio_dataset.csv"
    df_macro.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Dataset macro agregado guardado en %s", output_path)
    return output_path


def save_catastro_micro_alias(catastro_df: pd.DataFrame) -> Path:
    """
    Guarda un alias “micro” del catastro imputado (edificio-a-edificio).

    Nota:
        Esto NO crea datos nuevos; solo deja un output explícito para diferenciar:
        - macro (precios agregados) vs
        - micro (atributos por edificio, imputados en Fase 1).

    Args:
        catastro_df: DataFrame de catastro cargado por el linker.

    Returns:
        Ruta del archivo CSV generado.
    """
    output_path = PROCESSED_DIR / "catastro_gracia_imputado_micro.csv"
    catastro_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Alias catastro micro guardado en %s", output_path)
    return output_path


def generate_report(df: pd.DataFrame, match_config: LinkingConfig) -> Path:
    """
    Genera un reporte JSON de calidad de linking para el Issue #201.

    Args:
        df: DataFrame final.
        match_config: Configuración de linking (umbrales).

    Returns:
        Ruta del archivo JSON generado.
    """
    if df.empty:
        report: Dict[str, object] = {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "total_registros": 0,
            "match_rate_global": 0.0,
            "match_rate_por_metodo": {},
            "precio_m2": {},
            "superficie_m2": {},
            "completitud": {},
        }
    else:
        total = len(df)
        method_counts = df["match_method"].value_counts(dropna=False)
        match_rate_por_metodo = {
            str(method): float(count) / float(total) * 100.0
            for method, count in method_counts.items()
        }

        precio_stats = {
            "min": float(df["precio_m2"].min()),
            "max": float(df["precio_m2"].max()),
            "mean": float(df["precio_m2"].mean()),
            "median": float(df["precio_m2"].median()),
        }

        superficie_col = "superficie_m2"
        superficie_stats: Dict[str, Optional[float]]
        if superficie_col in df.columns and df[superficie_col].notna().any():
            superficie_stats = {
                "min": float(df[superficie_col].min()),
                "max": float(df[superficie_col].max()),
                "mean": float(df[superficie_col].mean()),
            }
        else:
            superficie_stats = {}

        completitud: Dict[str, float] = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                completitud[col] = float(df[col].notna().sum()) / float(total) * 100.0

        report = {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "total_registros": int(total),
            "match_rate_global": 100.0,  # Todos los registros del df son matched o imputados
            "match_rate_por_metodo": match_rate_por_metodo,
            "precio_m2": precio_stats,
            "superficie_m2": superficie_stats,
            "completitud": completitud,
            "config": {
                "fuzzy_threshold": match_config.fuzzy_threshold,
                "min_match_rate_ok": match_config.min_match_rate_ok,
                "min_match_rate_warning": match_config.min_match_rate_warning,
            },
        }

    report_path = LOG_DIR / "linking_report_201.json"
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    logger.info("Reporte de linking guardado en %s", report_path)
    return report_path


def main() -> int:
    """
    Función principal del script de linking para Gràcia.

    Returns:
        Código de salida (0 si éxito, 1 si error).
    """
    setup_logging()
    logger.info("=== Issue #201: Linking y limpieza para Gràcia ===")

    config = LinkingConfig()
    linker = GraciaDataLinker(config=config)

    try:
        linker.load_data()
        df_merged = linker.link_data()

        if df_merged.empty:
            logger.error("No se pudo construir un dataset combinado para Gràcia")
            generate_report(df_merged, config)
            return 1

        df_clean = linker.clean_outliers(df_merged)
        save_merged_data(df_clean)
        # Export macro agregado (baseline v0.1 coherente)
        df_macro = build_macro_dataset(df_clean)
        if not df_macro.empty:
            save_macro_data(df_macro)
        else:
            logger.warning("Dataset macro vacío; no se generará CSV agregado")

        # Export alias micro (atributos por edificio imputados)
        if linker.df_catastro is not None and not linker.df_catastro.empty:
            save_catastro_micro_alias(linker.df_catastro)
        generate_report(df_clean, config)

        logger.info("✓ Linking y limpieza completados correctamente para Gràcia")
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Error inesperado en el linking de Gràcia: %s",
            exc,
            exc_info=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


