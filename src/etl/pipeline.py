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
from ..database_views import create_analytical_views
from .migrations import migrate_dim_barrios_if_needed
from .validators import (
    FKValidationStrategy,
    handle_source_error,
    validate_all_fact_tables,
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


def _convert_to_json_serializable(obj):
    """
    Convierte recursivamente valores numéricos de pandas/numpy a tipos nativos de Python.
    
    Args:
        obj: Objeto a convertir (dict, list, o valor primitivo)
    
    Returns:
        Objeto con valores convertidos a tipos nativos de Python
    """
    import numpy as np
    
    if isinstance(obj, dict):
        return {k: _convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Intentar convertir a int o float si es posible
        try:
            if isinstance(obj, (int, float)):
                return int(obj) if isinstance(obj, (int, np.integer)) else float(obj)
        except (ValueError, TypeError):
            pass
        return obj


def run_etl(
    raw_base_dir: Path = Path("data/raw"),
    processed_dir: Path = PROCESSED_DIR,
    db_path: Optional[Path] = None,
) -> Path:
    """Execute the transformation (T) and load (L) stages into SQLite."""

    # #region agent log
    import json
    import time as time_module
    from pathlib import Path as PathLib
    debug_log_path = PathLib(__file__).parent.parent.parent / ".cursor" / "debug.log"
    try:
        debug_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "pipeline.py:run_etl",
                "message": "run_etl function entry",
                "data": {
                    "raw_base_dir": str(raw_base_dir),
                    "processed_dir": str(processed_dir),
                },
                "timestamp": int(time_module.time() * 1000)
            }) + "\n")
    except Exception as log_err:
        logger.debug("Debug log write failed: %s", log_err)
    # #endregion

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
        
        # Descubrimiento de archivos de entrada: priorizamos manifest y usamos patrones legacy como respaldo.
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
        
        renta_path = None
        if use_manifest:
            renta_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "renta", source="opendatabcn"
            )
        if renta_path is None:
            renta_path = _find_latest_file(opendata_dir, "opendatabcn_renda-*.csv")
        
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
        
        geojson_path = None
        if use_manifest:
            geojson_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "geojson"
            )
        if geojson_path is None:
            geojson_path = _find_latest_file(geojson_dir, "barrios_geojson_*.json")
        
        idealista_venta_path = None
        idealista_rent_path = None
        regulacion_dir = raw_base_dir / "regulacion"
        portaldades_dir = raw_base_dir / "portaldades"
        regulacion_path = None

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
            idealista_rent_path = _find_latest_file(
                idealista_dir, "idealista_oferta_rent_*.csv"
            )

        # Buscar datos de regulación: primero en regulacion/, luego en portaldades/
        if use_manifest:
            regulacion_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "regulacion", source="portaldades"
            )
        if regulacion_path is None and regulacion_dir.exists():
            # Buscar CSV del Portal de Dades con ID b37xv8wcjh
            regulacion_path = _find_latest_file(
                regulacion_dir, "*b37xv8wcjh*.csv"
            )
        if regulacion_path is None and portaldades_dir.exists():
            # Fallback: buscar en directorio portaldades
            regulacion_path = _find_latest_file(
                portaldades_dir, "*b37xv8wcjh*.csv"
            )

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
        alquiler_df = (
            _safe_read_csv(alquiler_path) if alquiler_path else pd.DataFrame()
        )
        
        # Cargar datos de renta si están disponibles (fuente opcional)
        renta_df = None
        if renta_path:
            try:
                renta_df = _safe_read_csv(renta_path)
                logger.info("✓ Datos de renta cargados: %s", renta_path.name)
            except Exception as e:
                handle_source_error("renta", e, context="carga CSV")

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
                params["portaldades_venta_rows"] = int(len(portaldades_venta_df))
                params["portaldades_alquiler_rows"] = int(len(portaldades_alquiler_df))
                
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
                handle_source_error("portaldades", e, context="procesamiento precios")
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

        # Procesar datos de regulación (Portal de Dades + Open Data BCN)
        from ..processing.prepare_regulacion import prepare_regulacion  # noqa: WPS433
        from ..processing.prepare_presion_turistica import prepare_presion_turistica  # noqa: WPS433
        from ..processing.prepare_seguridad import prepare_seguridad  # noqa: WPS433
        from ..processing.prepare_ruido import prepare_ruido  # noqa: WPS433

        fact_regulacion = None
        fact_presion_turistica = None
        fact_seguridad = None
        fact_ruido = None
        # Intentar primero regulacion_dir, luego portaldades_dir, luego raw_base_dir
        regulacion_data_dir = None
        
        # #region agent log
        import json
        import time as time_module
        from pathlib import Path as PathLib
        debug_log_path = PathLib(__file__).parent.parent.parent / ".cursor" / "debug.log"
        try:
            debug_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "pipeline.py:412",
                    "message": "Checking regulacion directories",
                    "data": {
                        "regulacion_dir": str(regulacion_dir),
                        "regulacion_dir_exists": regulacion_dir.exists(),
                        "portaldades_dir": str(portaldades_dir),
                        "portaldades_dir_exists": portaldades_dir.exists(),
                        "raw_base_dir": str(raw_base_dir),
                        "debug_log_path": str(debug_log_path),
                    },
                    "timestamp": int(time_module.time() * 1000)
                }) + "\n")
        except Exception as log_err:
            logger.debug("Debug log write failed: %s", log_err)
        # #endregion
        
        if regulacion_dir.exists():
            regulacion_data_dir = regulacion_dir
        elif portaldades_dir.exists():
            regulacion_data_dir = portaldades_dir
        else:
            # Fallback: usar raw_base_dir directamente (prepare_regulacion buscará recursivamente)
            regulacion_data_dir = raw_base_dir
        
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "pipeline.py:420",
                    "message": "Selected regulacion_data_dir",
                    "data": {
                        "regulacion_data_dir": str(regulacion_data_dir),
                        "regulacion_data_dir_exists": regulacion_data_dir.exists() if regulacion_data_dir else False,
                    },
                    "timestamp": int(time_module.time() * 1000)
                }) + "\n")
        except Exception as log_err:
            logger.debug("Debug log write failed: %s", log_err)
        # #endregion
        
        logger.info("Buscando datos de regulación en: %s", regulacion_data_dir)
        try:
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "pipeline.py:424",
                        "message": "Calling prepare_regulacion",
                        "data": {
                            "raw_data_path": str(regulacion_data_dir),
                            "barrios_df_rows": len(dim_barrios),
                        },
                        "timestamp": int(time_module.time() * 1000)
                    }) + "\n")
            except Exception as log_err:
                logger.debug("Debug log write failed: %s", log_err)
            # #endregion
            
            fact_regulacion = prepare_regulacion(
                raw_data_path=regulacion_data_dir,
                barrios_df=dim_barrios,
            )
            
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "D",
                        "location": "pipeline.py:428",
                        "message": "prepare_regulacion returned",
                        "data": {
                            "fact_regulacion_is_none": fact_regulacion is None,
                            "fact_regulacion_empty": fact_regulacion.empty if fact_regulacion is not None else None,
                            "fact_regulacion_rows": len(fact_regulacion) if fact_regulacion is not None else 0,
                        },
                        "timestamp": int(time_module.time() * 1000)
                    }) + "\n")
            except Exception as log_err:
                logger.debug("Debug log write failed: %s", log_err)
            # #endregion
            
            if fact_regulacion is not None and not fact_regulacion.empty:
                logger.info(
                    "✓ Regulación procesada: %s registros (años %s-%s)",
                    len(fact_regulacion),
                    fact_regulacion["anio"].min() if not fact_regulacion.empty else None,
                    fact_regulacion["anio"].max() if not fact_regulacion.empty else None,
                )
            else:
                logger.warning(
                    "No se encontraron datos de regulación procesables en %s. "
                    "Verifica que existan archivos CSV con 'b37xv8wcjh' en el nombre.",
                    regulacion_data_dir
                )
        except Exception as e:
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "C",
                        "location": "pipeline.py:441",
                        "message": "Exception in prepare_regulacion",
                        "data": {
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                        "timestamp": int(time_module.time() * 1000)
                    }) + "\n")
            except Exception as log_err:
                logger.debug("Debug log write failed: %s", log_err)
            # #endregion
            handle_source_error("regulacion", e, context="procesamiento")
            fact_regulacion = None
        
        # Procesar datos de presión turística (Inside Airbnb)
        airbnb_data_dir = raw_base_dir / "airbnb"
        if not airbnb_data_dir.exists():
            airbnb_data_dir = raw_base_dir / "insideairbnb"
        
        if airbnb_data_dir.exists():
            logger.info("=== Procesando datos de presión turística (Inside Airbnb) ===")
            try:
                fact_presion_turistica = prepare_presion_turistica(
                    raw_data_path=airbnb_data_dir,
                    barrios_df=dim_barrios,
                )
                
                if fact_presion_turistica is not None and not fact_presion_turistica.empty:
                    logger.info(
                        "✓ Presión turística procesada: %s registros (años %s-%s)",
                        len(fact_presion_turistica),
                        fact_presion_turistica["anio"].min() if not fact_presion_turistica.empty else None,
                        fact_presion_turistica["anio"].max() if not fact_presion_turistica.empty else None,
                    )
                    params["presion_turistica_rows"] = int(len(fact_presion_turistica))
                    params["presion_turistica_barrios"] = int(fact_presion_turistica["barrio_id"].nunique())
                else:
                    logger.warning(
                        "No se encontraron datos de presión turística procesables en %s. "
                        "Verifica que existan archivos CSV de listings, calendar y reviews.",
                        airbnb_data_dir
                    )
            except Exception as e:
                handle_source_error("presion_turistica", e, context="procesamiento")
                fact_presion_turistica = None
        else:
            logger.info("Directorio de datos de Airbnb no encontrado, omitiendo presión turística")
            fact_presion_turistica = None
        
        # Procesar datos de seguridad y criminalidad (ICGC)
        icgc_data_dir = raw_base_dir / "icgc"
        if not icgc_data_dir.exists():
            icgc_data_dir = raw_base_dir / "seguridad"
        
        if icgc_data_dir.exists():
            logger.info("=== Procesando datos de seguridad y criminalidad (ICGC) ===")
            try:
                # Cargar datos de población para calcular tasas
                poblacion_df = None
                if fact_demografia is not None and not fact_demografia.empty:
                    poblacion_df = fact_demografia[["barrio_id", "anio", "poblacion_total"]].copy()
                    logger.info("Datos de población cargados para cálculo de tasas: %s registros", len(poblacion_df))
                
                fact_seguridad = prepare_seguridad(
                    raw_data_path=icgc_data_dir,
                    barrios_df=dim_barrios,
                    poblacion_df=poblacion_df,
                )
                
                if fact_seguridad is not None and not fact_seguridad.empty:
                    logger.info(
                        "✓ Seguridad procesada: %s registros (años %s-%s)",
                        len(fact_seguridad),
                        fact_seguridad["anio"].min() if not fact_seguridad.empty else None,
                        fact_seguridad["anio"].max() if not fact_seguridad.empty else None,
                    )
                    params["seguridad_rows"] = int(len(fact_seguridad))
                    params["seguridad_barrios"] = int(fact_seguridad["barrio_id"].nunique())
                else:
                    logger.warning(
                        "No se encontraron datos de seguridad procesables en %s. "
                        "Verifica que existan archivos CSV de criminalidad.",
                        icgc_data_dir
                    )
            except Exception as e:
                handle_source_error("seguridad", e, context="procesamiento")
                fact_seguridad = None
        else:
            logger.info("Directorio de datos de ICGC no encontrado, omitiendo seguridad")
            fact_seguridad = None
        
        # Procesar datos de contaminación acústica (ruido)
        ruido_data_dir = raw_base_dir / "ruido"
        if not ruido_data_dir.exists():
            ruido_data_dir = raw_base_dir / "opendatabcn" / "ruido"
        
        if ruido_data_dir.exists() or (raw_base_dir / "ruido").exists():
            logger.info("=== Procesando datos de contaminación acústica (ruido) ===")
            try:
                # Cargar datos de población para calcular porcentaje expuesto
                poblacion_df = None
                if fact_demografia is not None and not fact_demografia.empty:
                    poblacion_df = fact_demografia[["barrio_id", "anio", "poblacion_total"]].copy()
                    logger.info("Datos de población cargados para cálculo de exposición: %s registros", len(poblacion_df))
                
                fact_ruido = prepare_ruido(
                    raw_data_path=ruido_data_dir if ruido_data_dir.exists() else raw_base_dir,
                    barrios_df=dim_barrios,
                    poblacion_df=poblacion_df,
                )
                
                if fact_ruido is not None and not fact_ruido.empty:
                    logger.info(
                        "✓ Ruido procesado: %s registros (años %s-%s)",
                        len(fact_ruido),
                        fact_ruido["anio"].min() if not fact_ruido.empty else None,
                        fact_ruido["anio"].max() if not fact_ruido.empty else None,
                    )
                    params["ruido_rows"] = int(len(fact_ruido))
                    params["ruido_barrios"] = int(fact_ruido["barrio_id"].nunique())
                else:
                    logger.warning(
                        "No se encontraron datos de ruido procesables. "
                        "Verifica que existan archivos CSV de ruido o mapas ráster."
                    )
            except Exception as e:
                handle_source_error("ruido", e, context="procesamiento")
                fact_ruido = None
        else:
            logger.info("Directorio de datos de ruido no encontrado, omitiendo contaminación acústica")
            fact_ruido = None
        
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
                handle_source_error("renta", e, context="procesamiento")
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
                handle_source_error("idealista", e, context="carga venta CSV")
        
        if idealista_rent_path and idealista_rent_path.exists():
            try:
                logger.info("Cargando datos de oferta de alquiler de Idealista...")
                idealista_rent_df = _safe_read_csv(idealista_rent_path)
                if not idealista_rent_df.empty:
                    idealista_data_combined.append(idealista_rent_df)
                    logger.info("✓ Datos de alquiler Idealista cargados: %s", idealista_rent_path.name)
            except Exception as e:
                handle_source_error("idealista", e, context="carga alquiler CSV")
        
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
                handle_source_error("idealista", e, context="procesamiento oferta")
                fact_oferta_idealista = None
        else:
            logger.debug("No se encontraron datos de Idealista (opcional, requiere API credentials)")

        # === VALIDACIÓN DE INTEGRIDAD REFERENCIAL ===
        # Validar todas las fact tables antes de insertar en SQLite
        logger.info("=== Validando integridad referencial ===")
        (
            fact_precios,
            fact_demografia,
            fact_demografia_ampliada,
            fact_renta,
            fact_oferta_idealista,
            fact_regulacion,
            fact_presion_turistica,
            fact_seguridad,
            fact_ruido,
            fk_validation_results,
        ) = validate_all_fact_tables(
            dim_barrios=dim_barrios,
            fact_precios=fact_precios,
            fact_demografia=fact_demografia,
            fact_demografia_ampliada=fact_demografia_ampliada,
            fact_renta=fact_renta,
            fact_oferta_idealista=fact_oferta_idealista,
            fact_regulacion=fact_regulacion,
            fact_presion_turistica=fact_presion_turistica,
            fact_seguridad=fact_seguridad,
            fact_ruido=fact_ruido,
            strategy=FKValidationStrategy.FILTER,  # Filtra registros con FK inválidos
        )
        
        # Registrar estadísticas de validación
        # Convertir valores numéricos a tipos nativos de Python para serialización JSON
        def to_native_type(v):
            """Convierte valores numéricos de pandas/numpy a tipos nativos de Python."""
            import numpy as np
            if v is None:
                return None
            try:
                if pd.isna(v):
                    return None
            except (TypeError, ValueError):
                pass
            # Convertir tipos numpy/pandas a tipos nativos de Python
            if isinstance(v, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                return int(v)
            if isinstance(v, (np.floating, np.float64, np.float32)):
                return float(v)
            if isinstance(v, (int, float)):
                return int(v) if isinstance(v, int) else float(v)
            return v
        
        fk_stats = {
            result.table_name: {
                "total": to_native_type(result.total_records),
                "valid": to_native_type(result.valid_records),
                "invalid": to_native_type(result.invalid_records),
                "pct_invalid": to_native_type(round(result.pct_invalid, 2)),
            }
            for result in fk_validation_results
        }
        params["fk_validation"] = fk_stats

        params.update(
            {
                "demographics_file": demographics_path.name,
                "venta_file": venta_path.name if venta_path else None,
                "alquiler_file": alquiler_path.name if alquiler_path else None,
                "renta_file": renta_path.name if renta_path else None,
                "geojson_file": geojson_path.name if geojson_path else None,
                "idealista_venta_file": idealista_venta_path.name if idealista_venta_path and idealista_venta_path.exists() else None,
                "idealista_rent_file": idealista_rent_path.name if idealista_rent_path and idealista_rent_path.exists() else None,
                "dim_barrios_rows": int(len(dim_barrios)),
                "fact_demografia_rows": int(len(fact_demografia)) if fact_demografia is not None else 0,
                "fact_demografia_ampliada_rows": int(len(fact_demografia_ampliada)) if fact_demografia_ampliada is not None else 0,
                "fact_precios_rows": int(len(fact_precios)),
                "fact_renta_rows": int(len(fact_renta)) if fact_renta is not None else 0,
                "fact_oferta_idealista_rows": int(len(fact_oferta_idealista)) if fact_oferta_idealista is not None else 0,
                "fact_regulacion_rows": int(len(fact_regulacion)) if fact_regulacion is not None else 0,
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
        if fact_regulacion is not None:
            tables_to_truncate.append("fact_regulacion")
        tables_to_truncate.append("fact_precios")
        # dim_barrios se trunca al final porque otras tablas tienen foreign keys hacia ella
        tables_to_truncate.append("dim_barrios")
        
        truncate_tables(conn, tables_to_truncate)
        
        # Create schema AFTER truncating to ensure no duplicate data exists
        create_database_schema(conn)

        logger.info("Cargando dimensión de barrios en SQLite")
        dim_barrios.to_sql("dim_barrios", conn, if_exists="append", index=False)

        # Migración de dim_barrios (centroides, áreas, códigos INE) una vez cargados los datos
        try:
            migrate_dim_barrios_if_needed(conn)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Error durante migración de dim_barrios (se continúa con el ETL): %s",
                exc,
            )

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

        if fact_regulacion is not None and not fact_regulacion.empty:
            logger.info("Cargando tabla de hechos de regulación")
            # Usar replace para evitar errores de UNIQUE constraint si hay datos previos
            fact_regulacion.to_sql(
                "fact_regulacion",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug(
                "No se cargaron datos en fact_regulacion (no disponible o vacío)"
            )

        if fact_presion_turistica is not None and not fact_presion_turistica.empty:
            logger.info("Cargando tabla de hechos de presión turística")
            fact_presion_turistica.to_sql(
                "fact_presion_turistica",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug(
                "No se cargaron datos en fact_presion_turistica (no disponible o vacío)"
            )

        if fact_seguridad is not None and not fact_seguridad.empty:
            logger.info("Cargando tabla de hechos de seguridad")
            fact_seguridad.to_sql(
                "fact_seguridad",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug(
                "No se cargaron datos en fact_seguridad (no disponible o vacío)"
            )

        if fact_ruido is not None and not fact_ruido.empty:
            logger.info("Cargando tabla de hechos de ruido")
            fact_ruido.to_sql(
                "fact_ruido",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug(
                "No se cargaron datos en fact_ruido (no disponible o vacío)"
            )

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

        # Crear vistas analíticas después de cargar los datos
        try:
            create_analytical_views(conn)
            logger.info("Vistas analíticas creadas/actualizadas tras la carga de datos")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Error creando vistas analíticas (no bloqueante para el ETL): %s",
                exc,
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
        
        # Convertir params a tipos serializables antes de registrar
        params_serializable = _convert_to_json_serializable(params)
        
        register_etl_run(
            conn,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            parameters=params_serializable,
        )
        conn.close()

    logger.info("ETL completado correctamente. Base de datos disponible en %s", database_path)
    return database_path


if __name__ == "__main__":
    """Punto de entrada cuando se ejecuta como módulo: python -m src.etl.pipeline"""
    import sys
    
    # Ejecutar ETL con parámetros por defecto
    try:
        db_path = run_etl()
        print(f"✅ ETL completado. Base de datos: {db_path}")
        sys.exit(0)
    except Exception as exc:
        logger.exception("Error durante ejecución del ETL: %s", exc)
        print(f"❌ Error durante el ETL: {exc}")
        sys.exit(1)
