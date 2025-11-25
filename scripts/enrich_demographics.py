"""
Carga datos auxiliares para enriquecer fact_demografia y elimina valores nulos.

Este script utiliza las funciones de `src.data_processing` para recalcular
hogares_totales, edad_media, porc_inmigracion y densidad_hab_km2 usando
los datasets del Portal de Dades, aplicando los cambios directamente en
la tabla fact_demografia dentro de SQLite.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from src.database_setup import create_connection, ensure_database_path
from src.data_processing import enrich_fact_demografia

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_PROCESSED_DIR = Path("data/processed")
DEFAULT_RAW_DIR = Path("data/raw")


def create_backup(db_path: Path) -> Path:
    """
    Genera un backup con timestamp de la base de datos.

    Args:
        db_path: Ruta al archivo SQLite original.

    Returns:
        Ruta al archivo de backup generado.

    Raises:
        FileNotFoundError: Si la base de datos no existe.
    """

    if not db_path.exists():
        raise FileNotFoundError(f"No se encontró la base de datos: {db_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    logger.info("Backup creado en %s", backup_path)
    return backup_path


def load_fact_demografia(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Recupera fact_demografia como DataFrame.

    Args:
        conn: Conexión SQLite abierta.

    Returns:
        DataFrame con fact_demografia ordenada por barrio y año.
    """

    query = """
        SELECT id, barrio_id, anio, poblacion_total, poblacion_hombres,
               poblacion_mujeres, hogares_totales, edad_media,
               porc_inmigracion, densidad_hab_km2, dataset_id, source,
               etl_loaded_at
        FROM fact_demografia
        ORDER BY barrio_id, anio
    """
    return pd.read_sql_query(query, conn)


def load_dim_barrios(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Recupera dim_barrios para soportar el mapeo de barrios.

    Args:
        conn: Conexión SQLite abierta.

    Returns:
        DataFrame con la dimensión de barrios.
    """

    query = """
        SELECT barrio_id, barrio_nombre, barrio_nombre_normalizado,
               distrito_id, distrito_nombre, municipio, ambito,
               codi_districte, codi_barri, geometry_json
        FROM dim_barrios
    """
    return pd.read_sql_query(query, conn)


def _series_diff(original: pd.Series, enriched: pd.Series) -> pd.Series:
    """
    Devuelve True donde los valores difieren considerando NaN.
    """

    return ~(
        original.eq(enriched)
        | (original.isna() & enriched.isna())
    )


def detect_changes(
    original: pd.DataFrame,
    enriched: pd.DataFrame,
    columns: Iterable[str],
) -> pd.Series:
    """
    Calcula una máscara booleana indicando filas con cambios.

    Args:
        original: DataFrame original (mismo orden que enriched).
        enriched: DataFrame enriquecido.
        columns: Columnas a comparar.

    Returns:
        Serie booleana con True cuando existe cambio en alguna columna.
    """

    diffs: Optional[pd.Series] = None
    for col in columns:
        col_diff = _series_diff(original[col], enriched[col])
        diffs = col_diff if diffs is None else (diffs | col_diff)
    return diffs if diffs is not None else pd.Series(False, index=original.index)


def apply_updates(
    conn: sqlite3.Connection,
    updated_rows: pd.DataFrame,
    columns: List[str],
) -> int:
    """
    Aplica los cambios detectados a fact_demografia.

    Args:
        conn: Conexión SQLite abierta.
        updated_rows: DataFrame con filas a actualizar (incluye columna id).
        columns: Columnas que serán actualizadas.

    Returns:
        Número de filas actualizadas efectivamente.
    """

    if updated_rows.empty:
        return 0

    placeholders = ", ".join(f"{col} = ?" for col in columns)
    query = f"UPDATE fact_demografia SET {placeholders} WHERE id = ?"
    cursor = conn.cursor()
    updated_count = 0

    with conn:
        for _, row in updated_rows.iterrows():
            values = [row[col] if not pd.isna(row[col]) else None for col in columns]
            values.append(int(row["id"]))
            cursor.execute(query, values)
            updated_count += cursor.rowcount

    return updated_count


def enrich_demographics(
    db_path: Optional[Path],
    processed_dir: Optional[Path],
    raw_base_dir: Optional[Path],
    create_backup_flag: bool,
    dry_run: bool,
) -> bool:
    """
    Ejecuta el proceso de enriquecimiento de fact_demografia.
    """

    processed_dir = processed_dir or DEFAULT_PROCESSED_DIR
    db_path = ensure_database_path(db_path, processed_dir)
    raw_dir = (raw_base_dir or DEFAULT_RAW_DIR).resolve()

    logger.info("Base de datos: %s", db_path)
    logger.info("Directorio raw: %s", raw_dir)
    logger.info("Dry-run: %s", dry_run)

    if not db_path.exists():
        logger.error("La base de datos no existe: %s", db_path)
        return False
    if not raw_dir.exists():
        logger.error("No existe el directorio de datos raw: %s", raw_dir)
        return False

    backup_path = None
    if create_backup_flag and not dry_run:
        try:
            backup_path = create_backup(db_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("No se pudo crear el backup: %s", exc)
            return False

    conn = create_connection(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        fact_original = load_fact_demografia(conn)
        dim_barrios = load_dim_barrios(conn)

        if fact_original.empty:
            logger.error("fact_demografia está vacío; no hay nada que enriquecer")
            return False

        logger.info("Filas originales en fact_demografia: %s", len(fact_original))

        enriched = enrich_fact_demografia(
            fact=fact_original,
            dim_barrios=dim_barrios,
            raw_base_dir=raw_dir,
            reference_time=datetime.now(timezone.utc),
        )

        fact_original = fact_original.sort_values("id").reset_index(drop=True)
        enriched = enriched.sort_values("id").reset_index(drop=True)

        if len(fact_original) != len(enriched):
            logger.error(
                "El DataFrame enriquecido tiene un número distinto de filas (%s vs %s)",
                len(enriched),
                len(fact_original),
            )
            return False

        compare_columns = [
            "hogares_totales",
            "edad_media",
            "porc_inmigracion",
            "densidad_hab_km2",
            "dataset_id",
            "source",
        ]

        change_mask = detect_changes(fact_original, enriched, compare_columns)
        updates = enriched.loc[change_mask].copy()

        logger.info(
            "Filas con cambios detectados: %s (%.2f%%)",
            len(updates),
            (len(updates) / len(fact_original)) * 100.0,
        )

        if updates.empty:
            logger.info("No se detectaron cambios; fact_demografia ya estaba completa")
            return True

        if dry_run:
            logger.info("DRY-RUN: No se aplicarán actualizaciones a la base de datos")
            logger.info(
                "Primeras filas con cambios:\n%s",
                updates[["id", "barrio_id", "anio"] + compare_columns].head(10),
            )
            return True

        updated_count = apply_updates(conn, updates, compare_columns)
        logger.info("Filas actualizadas en SQLite: %s", updated_count)

        if backup_path:
            logger.info("Backup disponible en: %s", backup_path)

        return True

    except Exception as exc:  # noqa: BLE001
        logger.error("Error durante el enriquecimiento: %s", exc, exc_info=True)
        if backup_path:
            logger.info("Puede restaurar la base de datos desde: %s", backup_path)
        return False

    finally:
        conn.close()
        logger.info("Conexión a la base de datos cerrada")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enriquece fact_demografia usando datasets del Portal de Dades",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Ruta al archivo SQLite (por defecto data/processed/database.db)",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Directorio base para datos procesados (default data/processed)",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="Directorio base con datos raw (default data/raw)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="No generar backup antes de actualizar",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar cambios detectados sin escribir en la base",
    )

    args = parser.parse_args()
    success = enrich_demographics(
        db_path=args.db_path,
        processed_dir=args.processed_dir,
        raw_base_dir=args.raw_dir,
        create_backup_flag=not args.no_backup,
        dry_run=args.dry_run,
    )
    exit(0 if success else 1)


if __name__ == "__main__":
    main()

