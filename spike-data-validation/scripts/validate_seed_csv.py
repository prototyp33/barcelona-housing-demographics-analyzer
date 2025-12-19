"""
Script para validar el seed CSV de referencias catastrales de Gràcia.

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Configurar logging
LOG_DIR = Path("spike-data-validation/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "seed_validation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def validate_seed_csv(seed_path: Path) -> Dict[str, Any]:
    """
    Valida el seed CSV de referencias catastrales.

    Args:
        seed_path: Ruta al archivo CSV seed

    Returns:
        Diccionario con resultados de validación
    """
    logger.info(f"Validando seed CSV: {seed_path}")

    if not seed_path.exists():
        return {
            "valido": False,
            "error": f"Archivo no encontrado: {seed_path}",
            "total_referencias": 0,
        }

    try:
        # Cargar CSV
        df = pd.read_csv(seed_path, encoding="utf-8")
        if df.empty:
            return {
                "valido": False,
                "error": "El seed CSV está vacío",
                "total_referencias": 0,
            }

        # Validar columnas requeridas
        required_cols = {"referencia_catastral"}
        missing_cols = required_cols - set(df.columns)

        if missing_cols:
            return {
                "valido": False,
                "error": f"Columnas faltantes: {missing_cols}",
                "total_referencias": 0,
            }

        # Normalizar y validar formato de referencias catastrales
        # - Por coordenadas (Consulta_RCCOOR): PC1+PC2 (14 caracteres)
        # - Por referencia (Consulta_DNPRC): RC completa (20 caracteres) -> actualmente no funciona (Issue #200)
        refs_series = df["referencia_catastral"].dropna().astype(str).str.strip()
        refs = refs_series.unique()
        total_refs = len(refs)

        lens = refs_series.str.len()
        counts_by_len = lens.value_counts().to_dict()
        count_len_14 = int(counts_by_len.get(14, 0))
        count_len_20 = int(counts_by_len.get(20, 0))

        # Validar alfanumérico (sin espacios)
        refs_alnum = refs_series[refs_series.str.isalnum()]
        refs_non_alnum = int(total_refs - refs_alnum.nunique())

        # Validar formato aceptable para el spike (≥14 caracteres o 20 exactos)
        refs_validas = refs_series[refs_series.str.len().between(14, 20)].unique()
        refs_invalidas = int(total_refs - len(refs_validas))

        # Validar unicidad
        duplicados = int(df["referencia_catastral"].duplicated().sum())

        # Validar completitud
        nulos = int(df["referencia_catastral"].isna().sum())

        # Validar si el seed incluye coordenadas (modo recomendado mientras DNPRC está caído)
        tiene_coords = {"lat", "lon"}.issubset(set(df.columns))
        coords_invalidas = 0
        if tiene_coords:
            lat_ok = pd.to_numeric(df["lat"], errors="coerce").notna()
            lon_ok = pd.to_numeric(df["lon"], errors="coerce").notna()
            coords_invalidas = int((~(lat_ok & lon_ok)).sum())

        # Validar cobertura por barrio (si existe)
        tiene_barrio_id = "barrio_id" in df.columns
        barrios_counts: Dict[int, int] = {}
        if tiene_barrio_id:
            barrio_series = pd.to_numeric(df["barrio_id"], errors="coerce").dropna().astype(int)
            barrios_counts = barrio_series.value_counts().sort_index().to_dict()

        gracia_ids = {28, 29, 30, 31, 32}
        cubre_gracia_5 = False
        if tiene_barrio_id:
            cubre_gracia_5 = gracia_ids.issubset(set(barrios_counts.keys()))

        resultado = {
            "valido": True,
            "total_referencias": total_refs,
            "referencias_unicas": total_refs - duplicados,
            "referencias_validas_formato": len(refs_validas),
            "referencias_invalidas_formato": refs_invalidas,
            "referencias_no_alfanumericas": refs_non_alnum,
            "longitudes_referencias": counts_by_len,
            "refs_len_14": count_len_14,
            "refs_len_20": count_len_20,
            "duplicados": duplicados,
            "nulos": nulos,
            "cumple_objetivo_50": total_refs >= 50,
            "tiene_direccion": "direccion" in df.columns,
            "tiene_coords": tiene_coords,
            "coords_invalidas": coords_invalidas,
            "tiene_barrio_id": tiene_barrio_id,
            "conteo_por_barrio_id": barrios_counts,
            "cubre_5_barrios_gracia": cubre_gracia_5,
        }

        logger.info(f"✓ Validación completada: {total_refs} referencias")
        logger.info(f"  - Únicas: {resultado['referencias_unicas']}")
        logger.info(f"  - Formato válido: {resultado['referencias_validas_formato']}")
        logger.info(f"  - Longitudes (14/20): {count_len_14}/{count_len_20}")
        logger.info(f"  - Tiene coords (lat/lon): {tiene_coords} (inválidas: {coords_invalidas})")
        logger.info(f"  - Cumple objetivo (≥50): {resultado['cumple_objetivo_50']}")
        if tiene_barrio_id:
            logger.info(f"  - Cobertura barrios Gràcia (28-32): {cubre_gracia_5} | conteo={barrios_counts}")

        if refs_invalidas > 0:
            logger.warning(f"⚠️ {refs_invalidas} referencias con formato sospechoso")

        if duplicados > 0:
            logger.warning(f"⚠️ {duplicados} referencias duplicadas")

        if refs_non_alnum > 0:
            logger.warning(f"⚠️ {refs_non_alnum} referencias no alfanuméricas (contienen símbolos/espacios)")

        if tiene_coords and coords_invalidas > 0:
            logger.warning(f"⚠️ {coords_invalidas} filas con coordenadas inválidas")

        if tiene_barrio_id and not cubre_gracia_5:
            logger.warning("⚠️ Seed no cubre los 5 barrios de Gràcia (28-32)")

        return resultado

    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logger.error(f"Error validando CSV: {exc}", exc_info=True)
        return {
            "valido": False,
            "error": str(exc),
            "total_referencias": 0,
        }


def main() -> int:
    """Función principal de validación."""
    seed_path = Path("spike-data-validation/data/raw/gracia_refs_seed.csv")

    resultado = validate_seed_csv(seed_path)

    if resultado["valido"]:
        logger.info("=" * 60)
        logger.info("VALIDACIÓN SEED CSV - RESULTADO")
        logger.info("=" * 60)
        for key, value in resultado.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)

        if resultado["cumple_objetivo_50"]:
            logger.info("✅ Seed CSV válido y listo para Issue #200")
            return 0
        else:
            logger.warning(
                f"⚠️ Seed CSV tiene solo {resultado['total_referencias']} referencias "
                f"(objetivo: ≥50). Considerar generar más referencias."
            )
            return 0  # No fallar, solo advertir
    else:
        logger.error(f"❌ Seed CSV inválido: {resultado.get('error', 'Error desconocido')}")
        return 1


if __name__ == "__main__":
    exit(main())
