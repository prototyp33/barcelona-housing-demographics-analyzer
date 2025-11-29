from __future__ import annotations

import json
import logging
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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


def _load_manifest(raw_dir: Path) -> List[Dict[str, object]]:
    """
    Carga el manifest.json que contiene el registro de todos los archivos extraídos.
    
    Args:
        raw_dir: Directorio base de datos raw
        
    Returns:
        Lista de entradas del manifest (vacía si no existe)
    """
    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        logger.debug("No se encontró manifest.json en %s", raw_dir)
        return []
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        logger.info("Manifest cargado: %d entradas", len(manifest))
        return manifest
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Error cargando manifest.json: %s", e)
        return []


def _get_latest_file_from_manifest(
    manifest: List[Dict[str, object]],
    raw_dir: Path,
    data_type: str,
    source: Optional[str] = None,
) -> Optional[Path]:
    """
    Obtiene el archivo más reciente de un tipo específico desde el manifest.
    
    Args:
        manifest: Lista de entradas del manifest
        raw_dir: Directorio base de datos raw
        data_type: Tipo de datos a buscar (ej. 'demographics', 'prices_venta')
        source: Filtrar por fuente específica (opcional)
        
    Returns:
        Path al archivo más reciente o None si no se encuentra
    """
    # Filtrar entradas por tipo (y opcionalmente por fuente)
    candidates = [
        entry for entry in manifest
        if entry.get("type") == data_type
        and (source is None or entry.get("source") == source)
    ]
    
    if not candidates:
        logger.debug("No se encontró archivo de tipo '%s' en manifest", data_type)
        return None
    
    # Ordenar por timestamp (más reciente primero)
    candidates.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    
    # Construir path completo
    latest = candidates[0]
    file_path = raw_dir / latest["file_path"]
    
    if file_path.exists():
        logger.info("Manifest: usando %s para tipo '%s'", file_path.name, data_type)
        return file_path
    else:
        logger.warning("Archivo del manifest no existe: %s", file_path)
        return None


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
        geojson_dir = raw_base_dir / "geojson"
        idealista_dir = raw_base_dir / "idealista"
        
        # Cargar manifest para descubrimiento de archivos
        manifest = _load_manifest(raw_base_dir)
        use_manifest = len(manifest) > 0
        
        if use_manifest:
            logger.info("=== Usando manifest.json para descubrimiento de archivos ===")
        else:
            logger.info("=== Manifest no disponible, usando patrones de nombre (legacy) ===")
        
        # Buscar archivos de datos
        # Prioridad: manifest > patrones de nombre (fallback para compatibilidad)
        
        # 1. Demographics
        demographics_path = None
        is_demographics_ampliada = False
        
        if use_manifest:
            # Primero intentar demografía ampliada
            demographics_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "demographics_ampliada", source="opendatabcn"
            )
            if demographics_path:
                is_demographics_ampliada = True
            else:
                # Fallback a demografía estándar
                demographics_path = _get_latest_file_from_manifest(
                    manifest, raw_base_dir, "demographics", source="opendatabcn"
                )
        
        # Fallback a patrones de nombre (legacy)
        if demographics_path is None:
            demographics_path = _find_latest_file(opendata_dir, "opendatabcn_pad_mdb_*.csv")
            if demographics_path and "lloc-naix" in demographics_path.name.lower():
                is_demographics_ampliada = True
        if demographics_path is None:
            demographics_path = _find_latest_file(opendata_dir, "opendatabcn_demographics_*.csv")
        
        # 2. Renta
        renta_path = None
        if use_manifest:
            renta_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "renta", source="opendatabcn"
            )
        if renta_path is None:
            renta_path = _find_latest_file(opendata_dir, "opendatabcn_renda-*.csv")
        
        # 3. Precios (venta y alquiler)
        venta_path = None
        alquiler_path = None
        
        if use_manifest:
            venta_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "prices_venta", source="opendatabcn"
            )
            alquiler_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "prices_alquiler", source="opendatabcn"
            )
        
        if venta_path is None:
            venta_path = _find_latest_file(opendata_dir, "opendatabcn_venta_*.csv")
        if alquiler_path is None:
            alquiler_path = _find_latest_file(opendata_dir, "opendatabcn_alquiler_*.csv")
        
        # 4. GeoJSON
        geojson_path = None
        if use_manifest:
            geojson_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "geojson"
            )
        if geojson_path is None:
            geojson_path = _find_latest_file(geojson_dir, "barrios_geojson_*.json")
        
        # 5. Idealista
        idealista_venta_path = None
        idealista_rent_path = None
        
        if use_manifest:
            idealista_venta_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "idealista_sale"
            )
            idealista_rent_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "idealista_rent"
            )
        
        if idealista_venta_path is None:
            idealista_venta_path = _find_latest_file(idealista_dir, "idealista_oferta_sale_*.csv")
        if idealista_rent_path is None:
            idealista_rent_path = _find_latest_file(idealista_dir, "idealista_oferta_rent_*.csv")

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
        
        # Cargar datos de renta si están disponibles
        renta_df = None
        if renta_path:
            try:
                renta_df = _safe_read_csv(renta_path)
                logger.info("✓ Datos de renta cargados: %s", renta_path.name)
            except Exception as e:
                logger.warning("Error cargando datos de renta: %s", e)

        # Determinar dataset IDs
        dataset_dem = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_demographics", {}
        ).get("datasets_processed", ["pad_mdbas_sexe"])
        dataset_dem_id = dataset_dem[0] if dataset_dem else "pad_mdbas_sexe"
        
        # Usar ID correcto si es demografía ampliada (determinado por manifest o patrón)
        if is_demographics_ampliada:
            dataset_dem_id = "pad_mdb_lloc-naix-continent_edat-q_sexe"

        dataset_venta_id = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_venta", {}
        ).get("dataset_id", "habitatges-2na-ma")

        dataset_alquiler_id = metadata.get("coverage_by_source", {}).get(
            "opendatabcn_alquiler", {}
        ).get("dataset_id")
        
        # Determinar dataset ID de renta
        dataset_renta_id = "renda-disponible-llars-bcn"
        if renta_path and "atles-renda" in renta_path.name.lower():
            if "per-llar" in renta_path.name.lower():
                dataset_renta_id = "atles-renda-bruta-per-llar"
            elif "per-persona" in renta_path.name.lower():
                dataset_renta_id = "atles-renda-bruta-per-persona"

        reference_time = datetime.utcnow()

        # Preparar dim_barrios con GeoJSON si está disponible
        logger.info("Preparando dimensión de barrios...")
        if geojson_path:
            logger.info("  Usando GeoJSON: %s", geojson_path.name)
        dim_barrios = data_processing.prepare_dim_barrios(
            dem_df, 
            dataset_id=dataset_dem_id, 
            reference_time=reference_time,
            geojson_path=geojson_path
        )

        # Procesar demografía: usar función ampliada si el dataset lo soporta
        fact_demografia = None
        fact_demografia_ampliada = None
        
        if is_demographics_ampliada:
            # Usar procesamiento ampliado para datos con edad quinquenal y nacionalidad
            logger.info("Procesando demografía ampliada (edad quinquenal y nacionalidad)...")
            try:
                fact_demografia_ampliada = data_processing.prepare_demografia_ampliada(
                    dem_df,
                    dim_barrios,
                    dataset_id=dataset_dem_id,
                    reference_time=reference_time,
                    source="opendatabcn",
                )
                logger.info("✓ Demografía ampliada procesada: %s registros", len(fact_demografia_ampliada))
            except Exception as e:
                logger.warning("Error procesando demografía ampliada, usando procesamiento estándar: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia_ampliada = None
        
        # Si no se procesó ampliada o falló, usar procesamiento estándar
        if fact_demografia_ampliada is None:
            logger.info("Procesando demografía estándar...")
            fact_demografia = data_processing.prepare_fact_demografia(
                dem_df,
                dim_barrios,
                dataset_id=dataset_dem_id,
                reference_time=reference_time,
                source="opendatabcn",
            )

            fact_demografia = data_processing.enrich_fact_demografia(
                fact_demografia,
                dim_barrios,
                raw_base_dir=raw_base_dir,
                reference_time=reference_time,
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
        
        # Procesar renta si está disponible
        fact_renta = None
        if renta_df is not None and not renta_df.empty:
            logger.info("Procesando datos de renta...")
            try:
                fact_renta = data_processing.prepare_renta_barrio(
                    renta_df,
                    dim_barrios,
                    dataset_id=dataset_renta_id,
                    reference_time=reference_time,
                    source="opendatabcn",
                    metric="mean",
                )
                logger.info("✓ Renta procesada: %s registros", len(fact_renta))
            except Exception as e:
                logger.warning("Error procesando renta: %s", e)
                logger.debug(traceback.format_exc())
                fact_renta = None
        
        # Procesar datos de Idealista si están disponibles
        fact_oferta_idealista = None
        idealista_data_combined = []
        
        if idealista_venta_path and idealista_venta_path.exists():
            try:
                logger.info("Cargando datos de oferta de venta de Idealista...")
                idealista_venta_df = _safe_read_csv(idealista_venta_path)
                if not idealista_venta_df.empty:
                    idealista_data_combined.append(idealista_venta_df)
                    logger.info("✓ Datos de venta Idealista cargados: %s", idealista_venta_path.name)
            except Exception as e:
                logger.warning("Error cargando datos de venta de Idealista: %s", e)
                logger.debug(traceback.format_exc())
        
        if idealista_rent_path and idealista_rent_path.exists():
            try:
                logger.info("Cargando datos de oferta de alquiler de Idealista...")
                idealista_rent_df = _safe_read_csv(idealista_rent_path)
                if not idealista_rent_df.empty:
                    idealista_data_combined.append(idealista_rent_df)
                    logger.info("✓ Datos de alquiler Idealista cargados: %s", idealista_rent_path.name)
            except Exception as e:
                logger.warning("Error cargando datos de alquiler de Idealista: %s", e)
                logger.debug(traceback.format_exc())
        
        if idealista_data_combined:
            logger.info("Procesando datos de oferta de Idealista...")
            try:
                idealista_df = pd.concat(idealista_data_combined, ignore_index=True)
                
                fact_oferta_idealista = data_processing.prepare_idealista_oferta(
                    idealista_df,
                    dim_barrios,
                    dataset_id="idealista_api",
                    reference_time=reference_time,
                    source="idealista_api",
                )
                logger.info("✓ Oferta Idealista procesada: %s registros", len(fact_oferta_idealista))
            except Exception as e:
                logger.warning("Error procesando oferta de Idealista: %s", e)
                logger.debug(traceback.format_exc())
                fact_oferta_idealista = None
        else:
            logger.debug("No se encontraron datos de Idealista (opcional, requiere API credentials)")

        params.update(
            {
                "demographics_file": demographics_path.name,
                "venta_file": venta_path.name if venta_path else None,
                "alquiler_file": alquiler_path.name if alquiler_path else None,
                "renta_file": renta_path.name if renta_path else None,
                "geojson_file": geojson_path.name if geojson_path else None,
                "idealista_venta_file": idealista_venta_path.name if idealista_venta_path and idealista_venta_path.exists() else None,
                "idealista_rent_file": idealista_rent_path.name if idealista_rent_path and idealista_rent_path.exists() else None,
                "dim_barrios_rows": len(dim_barrios),
                "fact_demografia_rows": len(fact_demografia) if fact_demografia is not None else 0,
                "fact_demografia_ampliada_rows": len(fact_demografia_ampliada) if fact_demografia_ampliada is not None else 0,
                "fact_precios_rows": len(fact_precios),
                "fact_renta_rows": len(fact_renta) if fact_renta is not None else 0,
                "fact_oferta_idealista_rows": len(fact_oferta_idealista) if fact_oferta_idealista is not None else 0,
            }
        )

        database_path = ensure_database_path(db_path, processed_dir)
        params["database_path"] = str(database_path.resolve())

        conn = create_connection(database_path)
        
        # Truncate tables BEFORE creating schema to avoid unique constraint errors
        # on existing duplicate data
        tables_to_truncate = []
        if fact_demografia_ampliada is not None:
            tables_to_truncate.append("fact_demografia_ampliada")
        if fact_demografia is not None:
            tables_to_truncate.append("fact_demografia")
        if fact_renta is not None:
            tables_to_truncate.append("fact_renta")
        if fact_oferta_idealista is not None:
            tables_to_truncate.append("fact_oferta_idealista")
        tables_to_truncate.append("fact_precios")
        # dim_barrios se trunca al final porque otras tablas tienen foreign keys hacia ella
        tables_to_truncate.append("dim_barrios")
        
        truncate_tables(conn, tables_to_truncate)
        
        # Create schema AFTER truncating to ensure no duplicate data exists
        create_database_schema(conn)

        logger.info("Cargando dimensión de barrios en SQLite")
        dim_barrios.to_sql("dim_barrios", conn, if_exists="append", index=False)

        # Cargar demografía (estándar o ampliada)
        if fact_demografia_ampliada is not None:
            logger.info("Cargando tabla de hechos demográficos ampliados")
            fact_demografia_ampliada.to_sql(
                "fact_demografia_ampliada", conn, if_exists="append", index=False
            )
        elif fact_demografia is not None:
            logger.info("Cargando tabla de hechos demográficos")
            fact_demografia.to_sql(
                "fact_demografia", conn, if_exists="append", index=False
            )
        else:
            logger.warning("No se cargaron datos demográficos")

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
        
        if fact_renta is not None and not fact_renta.empty:
            logger.info("Cargando tabla de hechos de renta")
            fact_renta.to_sql(
                "fact_renta",
                conn,
                if_exists="append",
                index=False,
            )
        else:
            logger.debug("No se cargaron datos en fact_renta (no disponible o vacío)")
        
        if fact_oferta_idealista is not None and not fact_oferta_idealista.empty:
            logger.info("Cargando tabla de hechos de oferta Idealista")
            fact_oferta_idealista.to_sql(
                "fact_oferta_idealista",
                conn,
                if_exists="append",
                index=False,
            )
        else:
            logger.debug("No se cargaron datos en fact_oferta_idealista (no disponible o vacío)")

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
