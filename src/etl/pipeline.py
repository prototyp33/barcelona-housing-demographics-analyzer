from __future__ import annotations

import json
import logging
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .. import data_processing
from ..database_setup import (
    create_connection,
    create_database_schema,
    ensure_database_path,
    register_etl_run,
    truncate_tables,
)

logger = logging.getLogger(__name__)

RAW_OPENDATABCN_DIR = Path("data/raw/opendatabcn")
RAW_METADATA_GLOB = "extraction_metadata_*.json"
PROCESSED_DIR = Path("data/processed")


def _find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _load_metadata(raw_dir: Path) -> Dict[str, object]:
    metadata_file = _find_latest_file(raw_dir, RAW_METADATA_GLOB)
    if not metadata_file:
        logger.warning(
            "No se encontró archivo de metadata de extracción en %s", raw_dir
        )
        return {}
    logger.info("Usando metadata de extracción: %s", metadata_file.name)
    return json.loads(metadata_file.read_text(encoding="utf-8"))


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path or not path.exists():
        raise FileNotFoundError(f"El archivo requerido no existe: {path}")
    logger.info("Leyendo archivo %s", path.name)
    return pd.read_csv(path)


def run_etl(
    raw_base_dir: Path = Path("data/raw"),
    processed_dir: Path = PROCESSED_DIR,
    db_path: Optional[Path] = None,
) -> Path:
    """Execute the transformation (T) and load (L) stages into SQLite."""

    raw_base_dir = Path(raw_base_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.utcnow()
    run_id = f"etl_{started_at.strftime('%Y%m%d_%H%M%S_%f')}"
    status = "SUCCESS"
    params: Dict[str, object] = {
        "raw_base_dir": str(raw_base_dir.resolve()),
        "processed_dir": str(processed_dir.resolve()),
    }
    error_message: Optional[str] = None
    conn: Optional[sqlite3.Connection] = None

    try:
        opendata_dir = raw_base_dir / "opendatabcn"
        demographics_path = _find_latest_file(opendata_dir, "opendatabcn_demographics_*.csv")
        venta_path = _find_latest_file(opendata_dir, "opendatabcn_venta_*.csv")
        alquiler_path = _find_latest_file(opendata_dir, "opendatabcn_alquiler_*.csv")

        if demographics_path is None:
            raise FileNotFoundError(
                "No se encontró un archivo de demografía en data/raw/opendatabcn"
            )
        if venta_path is None:
            logger.warning(
                "No se encontró archivo de venta. La tabla fact_precios se cargará vacía."
            )

        metadata = _load_metadata(raw_base_dir)
        params["metadata_file"] = _find_latest_file(raw_base_dir, RAW_METADATA_GLOB).name if _find_latest_file(raw_base_dir, RAW_METADATA_GLOB) else None

        dem_df = _safe_read_csv(demographics_path)
        venta_df = _safe_read_csv(venta_path) if venta_path else pd.DataFrame()
        alquiler_df = _safe_read_csv(alquiler_path) if alquiler_path else pd.DataFrame()

        dataset_dem = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_demographics", {}
        ).get("datasets_processed", ["pad_mdbas_sexe"])
        dataset_dem_id = dataset_dem[0] if dataset_dem else "pad_mdbas_sexe"

        dataset_venta_id = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_venta", {}
        ).get("dataset_id", "habitatges-2na-ma")

        dataset_alquiler_id = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_alquiler", {}
        ).get("dataset_id")

        reference_time = datetime.utcnow()

        dim_barrios = data_processing.prepare_dim_barrios(
            dem_df, dataset_id=dataset_dem_id, reference_time=reference_time
        )

        fact_demografia = data_processing.prepare_fact_demografia(
            dem_df,
            dim_barrios,
            dataset_id=dataset_dem_id,
            reference_time=reference_time,
            source="opendatabcn",
        )

        # Procesar datos del Portal de Dades
        portaldades_dir = raw_base_dir / "portaldades"
        portaldades_venta_df = pd.DataFrame()
        portaldades_alquiler_df = pd.DataFrame()
        
        if portaldades_dir.exists():
            logger.info("=== Procesando datos del Portal de Dades ===")
            metadata_file = portaldades_dir / "indicadores_habitatge.csv"
            try:
                portaldades_venta_df, portaldades_alquiler_df = (
                    data_processing.prepare_portaldades_precios(
                        portaldades_dir,
                        dim_barrios,
                        reference_time,
                        metadata_file=metadata_file if metadata_file.exists() else None,
                    )
                )
                params["portaldades_venta_rows"] = len(portaldades_venta_df)
                params["portaldades_alquiler_rows"] = len(portaldades_alquiler_df)
                
                if not portaldades_venta_df.empty:
                    logger.info(
                        f"✓ Portal de Dades - Venta: {len(portaldades_venta_df):,} registros "
                        f"(años {portaldades_venta_df['anio'].min()}-{portaldades_venta_df['anio'].max()})"
                    )
                if not portaldades_alquiler_df.empty:
                    logger.info(
                        f"✓ Portal de Dades - Alquiler: {len(portaldades_alquiler_df):,} registros "
                        f"(años {portaldades_alquiler_df['anio'].min()}-{portaldades_alquiler_df['anio'].max()})"
                    )
            except Exception as e:
                logger.warning(f"Error procesando datos del Portal de Dades: {e}")
                logger.debug(traceback.format_exc())
        else:
            logger.info("Directorio del Portal de Dades no encontrado, omitiendo")

        fact_precios = data_processing.prepare_fact_precios(
            venta_df,
            dim_barrios,
            dataset_id_venta=dataset_venta_id,
            reference_time=reference_time,
            alquiler=alquiler_df,
            dataset_id_alquiler=dataset_alquiler_id,
            portaldades_venta=portaldades_venta_df,
            portaldades_alquiler=portaldades_alquiler_df,
        )

        params.update(
            {
                "demographics_file": demographics_path.name,
                "venta_file": venta_path.name if venta_path else None,
                "alquiler_file": alquiler_path.name if alquiler_path else None,
                "dim_barrios_rows": len(dim_barrios),
                "fact_demografia_rows": len(fact_demografia),
                "fact_precios_rows": len(fact_precios),
            }
        )

        database_path = ensure_database_path(db_path, processed_dir)
        params["database_path"] = str(database_path.resolve())

        conn = create_connection(database_path)
        create_database_schema(conn)

        truncate_tables(conn, ["fact_precios", "fact_demografia", "dim_barrios"])

        logger.info("Cargando dimensión de barrios en SQLite")
        dim_barrios.to_sql("dim_barrios", conn, if_exists="append", index=False)

        logger.info("Cargando tabla de hechos demográficos")
        fact_demografia.to_sql(
            "fact_demografia", conn, if_exists="append", index=False
        )

        if not fact_precios.empty:
            logger.info("Cargando tabla de hechos de precios")
            fact_precios.to_sql(
                "fact_precios",
                conn,
                if_exists="append",
                index=False,
            )
        else:
            logger.warning(
                "No se cargaron datos en fact_precios (dataframe vacío)"
            )

    except Exception as exc:  # noqa: BLE001
        status = "FAILED"
        error_message = str(exc)
        logger.exception("Error durante la ejecución del ETL: %s", exc)
        raise
    finally:
        finished_at = datetime.utcnow()
        params["finished_at"] = finished_at.isoformat()
        if error_message:
            params["error"] = error_message
        if conn is None:
            database_path = ensure_database_path(db_path, processed_dir)
            conn = create_connection(database_path)
            create_database_schema(conn)
        register_etl_run(
            conn,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            parameters=params,
        )
        conn.close()

    logger.info("ETL completado correctamente. Base de datos disponible en %s", database_path)
    return database_path
