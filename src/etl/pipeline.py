from __future__ import annotations

import gc
import json
import logging
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .batch_processor import insert_dataframe_in_batches, optimize_dataframe_memory
from ..database_setup import (
    create_connection,
    create_database_schema,
    ensure_database_path,
    register_etl_run,
    truncate_tables,
)
from ..database_views import create_analytical_views
from .migrations import migrate_dim_barrios_if_needed
from .transformations.demographics import (
    enrich_fact_demografia,
    populate_fact_demografia_from_ampliada,
    prepare_demografia_ampliada,
    prepare_fact_demografia,
)
from .transformations.dimensions import prepare_dim_barrios
from .transformations.enrichment import (
    prepare_idealista_oferta,
    prepare_portaldades_precios,
)
from .transformations.market import (
    prepare_fact_precios, 
    prepare_renta_barrio,
    prepare_fact_renta_hist
)
from .transformations.advanced_analysis import (
    prepare_fact_renta_avanzada,
    prepare_fact_catastro_avanzado,
    prepare_fact_hogares_avanzado,
    prepare_fact_turismo_intensidad,
)
from .transformations.social_infrastructure import (
    prepare_fact_educacion,
    prepare_fact_vivienda_publica,
)
from .transformations.affordability import calculate_affordability_metrics
from .validators import (
    FKValidationStrategy,
    handle_source_error,
    validate_all_fact_tables,
)
from ..extraction.opendata import OpenDataBCNExtractor
from ..extraction.idescat import IDESCATExtractor

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
        # ESTRATEGIA: Detectar y procesar AMBOS tipos de demografía si están disponibles
        # - Demografía ampliada: para datos recientes con edad quinquenal (solo 2025)
        # - Demografía estándar: para datos históricos (2015-2024)
        demographics_path = None
        demographics_standard_path = None
        is_demographics_ampliada = False
        fact_renta_hist = None
        
        if use_manifest:
            # Primero intentar demografía ampliada
            demographics_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "demographics_ampliada", source="opendatabcn"
            )
            if demographics_path:
                is_demographics_ampliada = True
            
            # También buscar demografía estándar (puede tener datos históricos)
            demographics_standard_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "demographics", source="opendatabcn"
            )
        
        # Fallback a patrones de nombre (legacy)
        if demographics_path is None:
            # Buscar demografía ampliada
            demographics_path = _find_latest_file(opendata_dir, "opendatabcn_pad_mdb_lloc-naix*.csv")
            if demographics_path and "lloc-naix" in demographics_path.name.lower():
                is_demographics_ampliada = True
        
        # Buscar demografía estándar (puede tener datos históricos)
        if demographics_standard_path is None:
            # Buscar archivos de demografía estándar con datos históricos
            demographics_standard_path = _find_latest_file(opendata_dir, "opendatabcn_demographics_*.csv")
            if demographics_standard_path is None:
                demographics_standard_path = _find_latest_file(opendata_dir, "opendatabcn_pad_mdbas_sexe_*.csv")
        
        # Si no hay archivo principal, usar el estándar como fallback
        if demographics_path is None and demographics_standard_path:
            demographics_path = demographics_standard_path
            demographics_standard_path = None  # Evitar procesar dos veces
        
        renta_path = None
        if use_manifest:
            renta_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "renta", source="opendatabcn"
            )
        if renta_path is None:
            renta_path = _find_latest_file(opendata_dir, "opendatabcn_renda-*.csv")
        
        renta_hist_path = None
        if use_manifest:
            renta_hist_path = _get_latest_file_from_manifest(
                manifest, raw_base_dir, "renta_historica"
            )
        if renta_hist_path is None:
            renta_hist_path = _find_latest_file(raw_base_dir / "idescat", "idescat_renta_*.csv")
        
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

        # Descubrimiento de archivos avanzados
        renta_avanzada_files = {}
        catastro_avanzado_files = {}
        hogares_avanzado_files = {}
        turismo_intensidad_files = {}
        
        # Mapeo de grupos a sus keys
        advanced_groups = {
            "renta": ["income_gross_household", "income_gini", "income_p80_p20"],
            "catastro": ["cadastre_year_const", "cadastre_owner_type", "cadastre_avg_surface", "cadastre_owner_nationality", "cadastre_floors", "cadastre_built_surface", "cadastre_soil_surface"],
            "hogares": ["household_crowding", "household_nationality", "household_minors", "household_women"],
            "turismo": ["tourism_intensity", "tourism_hut"]
        }
        
        group_to_target = {
            "renta": renta_avanzada_files,
            "catastro": catastro_avanzado_files,
            "hogares": hogares_avanzado_files,
            "turismo": turismo_intensidad_files
        }
        
        datasets_mapping = OpenDataBCNExtractor.DATASETS
        
        for group_name, keys in advanced_groups.items():
            target_dict = group_to_target[group_name]
            for key in keys:
                dataset_id = datasets_mapping.get(key)
                if not dataset_id:
                    continue
                    
                path = None
                if use_manifest:
                    path = _get_latest_file_from_manifest(manifest, raw_base_dir, key, source="opendatabcn")
                
                if path is None:
                    # Fallback: buscar por ID del dataset en el nombre del archivo
                    path = _find_latest_file(RAW_OPENDATABCN_DIR, f"*{dataset_id}*.csv")
                    # También buscar en portaldades si no se encuentra en opendatabcn
                    if path is None and portaldades_dir.exists():
                        path = _find_latest_file(portaldades_dir, f"*{dataset_id}*.csv")
                
                if path:
                    logger.info(f"Cargando dataset avanzado '{key}' desde: {path.name}")
                    target_dict[key] = _safe_read_csv(path)
                else:
                    logger.debug(f"No se encontró archivo para dataset avanzado '{key}' (ID: {dataset_id})")
        
        # Descubrimiento de archivos de infraestructura social
        educacion_path = None
        vivienda_publica_files = {}
        
        if use_manifest:
            educacion_path = _get_latest_file_from_manifest(manifest, raw_base_dir, "education")
            vivienda_publica_files['tutelats'] = _get_latest_file_from_manifest(manifest, raw_base_dir, "housing_tut")
        
        if educacion_path is None:
            educacion_path = _find_latest_file(raw_base_dir / "educacion", "equipament_educacio_*.csv")
        
        if not vivienda_publica_files.get('tutelats'):
            vivienda_publica_files['tutelats'] = _find_latest_file(raw_base_dir / "viviendapublica", "opendatabcn_serveissocials_habitatgestutelats_*.csv")

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
        
        # Verificar si el archivo estándar tiene datos históricos (múltiples años)
        # Esto se hace después de cargar el archivo principal para evitar cargar dos veces
        has_historical_data = False
        if demographics_standard_path and demographics_standard_path.exists() and demographics_standard_path != demographics_path:
            try:
                # Leer una muestra más representativa: primeras, medias y últimas filas
                # para detectar múltiples años incluso si el archivo está ordenado
                total_lines = sum(1 for _ in open(demographics_standard_path)) - 1  # -1 para header
                sample_size = min(5000, total_lines)
                
                # Leer muestra más grande para mejor detección de años
                sample_df = pd.read_csv(demographics_standard_path, nrows=sample_size)
                if "Data_Referencia" in sample_df.columns:
                    years = pd.to_datetime(sample_df["Data_Referencia"], errors="coerce").dt.year.dropna().unique()
                    has_historical_data = len(years) > 1 or (len(years) == 1 and years[0] < 2025)
                    if has_historical_data:
                        logger.info(
                            "✓ Detectado archivo de demografía estándar con datos históricos: %s (años detectados: %s)",
                            demographics_standard_path.name,
                            sorted(years)
                        )
                # También verificar si el nombre del archivo sugiere datos históricos
                elif "2015" in demographics_standard_path.name and "2024" in demographics_standard_path.name:
                    has_historical_data = True
                    logger.info(
                        "✓ Archivo de demografía estándar con nombre histórico detectado: %s",
                        demographics_standard_path.name
                    )
            except Exception as e:
                logger.debug("Error verificando datos históricos: %s", e)
                # Fallback: si el nombre del archivo sugiere datos históricos, asumir que los tiene
                if "2015" in demographics_standard_path.name and "2024" in demographics_standard_path.name:
                    has_historical_data = True
                    logger.info(
                        "✓ Asumiendo datos históricos basado en nombre de archivo: %s",
                        demographics_standard_path.name
                    )
        venta_df = _safe_read_csv(venta_path) if venta_path else pd.DataFrame()
        if renta_hist_path:
            try:
                renta_hist_raw = _safe_read_csv(renta_hist_path)
                logger.info("✓ Datos de renta histórica cargados: %s", renta_hist_path.name)
            except Exception as e:
                handle_source_error("renta_historica", e, context="carga renta_hist")
        alquiler_df = _safe_read_csv(alquiler_path) if alquiler_path else pd.DataFrame()
        
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
        dim_barrios = prepare_dim_barrios(
            dem_df, 
            dataset_id=dataset_dem_id, 
            reference_time=reference_time,
            geojson_path=geojson_path
        )

        # Procesar renta histórica ahora que tenemos dim_barrios
        if renta_hist_path and 'renta_hist_raw' in locals():
            try:
                fact_renta_hist = prepare_fact_renta_hist(
                    renta_hist_raw,
                    dim_barrios,
                    reference_time
                )
            except Exception as e:
                handle_source_error("renta_historica", e, context="procesamiento renta_hist")

        # Procesar demografía: ESTRATEGIA HÍBRIDA
        # - Si hay demografía ampliada (2025): procesarla para fact_demografia_ampliada
        # - Si hay demografía estándar con datos históricos (2015-2024): procesarla para fact_demografia
        # - Si hay ambos: procesar ambos y combinar en fact_demografia
        fact_demografia = None
        fact_demografia_ampliada = None
        fact_demografia_standard = None
        fact_alquiler_mensual = None
        
        # 1. Procesar demografía ampliada si está disponible (solo 2025)
        if is_demographics_ampliada:
            logger.info("Procesando demografía ampliada (edad quinquenal y nacionalidad)...")
            try:
                fact_demografia_ampliada = prepare_demografia_ampliada(
                    dem_df,
                    dim_barrios,
                    dataset_id=dataset_dem_id,
                    reference_time=reference_time,
                    source="opendatabcn",
                )
                logger.info("✓ Demografía ampliada procesada: %s registros (años %s-%s)",
                    len(fact_demografia_ampliada),
                    fact_demografia_ampliada["anio"].min() if not fact_demografia_ampliada.empty else None,
                    fact_demografia_ampliada["anio"].max() if not fact_demografia_ampliada.empty else None,
                )
            except Exception as e:
                logger.warning("Error procesando demografía ampliada: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia_ampliada = None
        
        # 2. Procesar demografía estándar con datos históricos si está disponible
        if demographics_standard_path and demographics_standard_path.exists() and has_historical_data:
            logger.info("Procesando demografía estándar con datos históricos (2015-2024)...")
            try:
                dem_standard_df = _safe_read_csv(demographics_standard_path)
                dataset_standard_id = "pad_mdbas_sexe"
                
                fact_demografia_standard = prepare_fact_demografia(
                    dem_standard_df,
                    dim_barrios,
                    dataset_id=dataset_standard_id,
                    reference_time=reference_time,
                    source="opendatabcn",
                )
                
                fact_demografia_standard = enrich_fact_demografia(
                    fact_demografia_standard,
                    dim_barrios,
                    raw_base_dir=raw_base_dir,
                    reference_time=reference_time,
                )
                
                logger.info("✓ Demografía estándar procesada: %s registros (años %s-%s)",
                    len(fact_demografia_standard),
                    fact_demografia_standard["anio"].min() if not fact_demografia_standard.empty else None,
                    fact_demografia_standard["anio"].max() if not fact_demografia_standard.empty else None,
                )
            except Exception as e:
                logger.warning("Error procesando demografía estándar histórica: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia_standard = None
        
        # 3. Si no hay datos históricos pero hay demografía estándar del archivo principal, procesarla
        elif not is_demographics_ampliada:
            logger.info("Procesando demografía estándar...")
            try:
                fact_demografia = prepare_fact_demografia(
                    dem_df,
                    dim_barrios,
                    dataset_id=dataset_dem_id,
                    reference_time=reference_time,
                    source="opendatabcn",
                )

                fact_demografia = enrich_fact_demografia(
                    fact_demografia,
                    dim_barrios,
                    raw_base_dir=raw_base_dir,
                    reference_time=reference_time,
                )
            except Exception as e:
                logger.warning("Error procesando demografía estándar: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia = None
        
        # 4. Si tenemos ambos tipos, poblar fact_demografia desde fact_demografia_ampliada para 2025
        #    y usar fact_demografia_standard para años históricos
        if fact_demografia_ampliada is not None and not fact_demografia_ampliada.empty and fact_demografia_standard is not None and not fact_demografia_standard.empty:
            logger.info("Combinando demografía ampliada (2025) y estándar (histórica)...")
            try:
                # Poblar fact_demografia desde ampliada para 2025
                fact_demografia_2025 = populate_fact_demografia_from_ampliada(
                    fact_demografia_ampliada,
                    dim_barrios,
                    reference_time
                )
                
                # Combinar con datos históricos
                if fact_demografia_2025 is not None and not fact_demografia_2025.empty:
                    # Filtrar fact_demografia_standard for excluir 2025 si existe
                    fact_standard_filtered = fact_demografia_standard[
                        fact_demografia_standard["anio"] != 2025
                    ] if 2025 in fact_demografia_standard["anio"].values else fact_demografia_standard
                    
                    # Combinar ambos DataFrames
                    fact_demografia = pd.concat(
                        [fact_standard_filtered, fact_demografia_2025],
                        ignore_index=True
                    ).sort_values(["anio", "barrio_id"]).reset_index(drop=True)

                    # Re-enriquecer el total para asegurar consistencia (especialmente para 2025)
                    fact_demografia = enrich_fact_demografia(
                        fact_demografia,
                        dim_barrios,
                        raw_base_dir=raw_base_dir,
                        reference_time=reference_time,
                    )
                    
                    logger.info("✓ Demografía combinada: %s registros (años %s-%s)",
                        len(fact_demografia),
                        fact_demografia["anio"].min(),
                        fact_demografia["anio"].max(),
                    )
                else:
                    # Si no se pudo poblar desde ampliada, usar solo estándar
                    fact_demografia = fact_demografia_standard
                    logger.info("✓ Usando solo demografía estándar: %s registros", len(fact_demografia))
            except Exception as e:
                logger.warning("Error combinando demografías, usando solo estándar: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia = fact_demografia_standard
        elif fact_demografia_standard is not None and not fact_demografia_standard.empty:
            # Solo tenemos datos históricos estándar
            fact_demografia = fact_demografia_standard
        elif fact_demografia_ampliada is not None and not fact_demografia_ampliada.empty:
            # Solo tenemos datos ampliados (2025), poblar fact_demografia desde ampliada
            logger.info("Poblando fact_demografia desde demografía ampliada (2025)...")
            try:
                fact_demografia = populate_fact_demografia_from_ampliada(
                    fact_demografia_ampliada,
                    dim_barrios,
                    reference_time
                )
                
                # Enriquecer métricas adicionales
                if fact_demografia is not None and not fact_demografia.empty:
                    fact_demografia = enrich_fact_demografia(
                        fact_demografia,
                        dim_barrios,
                        raw_base_dir=raw_base_dir,
                        reference_time=reference_time,
                    )
                if fact_demografia is not None and not fact_demografia.empty:
                    logger.info("✓ fact_demografia poblada desde ampliada: %s registros", len(fact_demografia))
            except Exception as e:
                logger.warning("Error poblando fact_demografia desde ampliada: %s", e)
                logger.debug(traceback.format_exc())
                fact_demografia = None

        # Procesar datos del Portal de Dades
        portaldades_dir = raw_base_dir / "portaldades"
        portaldades_venta_df = pd.DataFrame()
        portaldades_alquiler_df = pd.DataFrame()
        portaldades_alquiler_mensual_df = pd.DataFrame()
        
        if portaldades_dir.exists():
            logger.info("=== Procesando datos del Portal de Dades ===")
            metadata_file = portaldades_dir / "indicadores_habitatge.csv"
            try:
                portaldades_venta_df, portaldades_alquiler_df, portaldades_alquiler_mensual_df = (
                    prepare_portaldades_precios(
                        portaldades_dir,
                        dim_barrios,
                        reference_time,
                        metadata_file=metadata_file if metadata_file.exists() else None,
                    )
                )
                params["portaldades_venta_rows"] = int(len(portaldades_venta_df))
                params["portaldades_alquiler_rows"] = int(len(portaldades_alquiler_df))
                params["portaldades_alquiler_mensual_rows"] = int(len(portaldades_alquiler_mensual_df))
                
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
            portaldades_alquiler_mensual_df = pd.DataFrame()

        fact_precios = prepare_fact_precios(
            venta_df,
            dim_barrios,
            dataset_id_venta=dataset_venta_id,
            reference_time=reference_time,
            alquiler=alquiler_df,
            dataset_id_alquiler=dataset_alquiler_id,
            portaldades_venta=portaldades_venta_df,
            portaldades_alquiler=portaldades_alquiler_df,
        )

        # Procesar alquiler mensual desde Portal de Dades si está disponible
        if portaldades_alquiler_mensual_df is not None and not portaldades_alquiler_mensual_df.empty:
            logger.info("✓ Alquiler mensual (Portal de Dades) disponible: %s registros", len(portaldades_alquiler_mensual_df))
            fact_alquiler_mensual = portaldades_alquiler_mensual_df

        # Procesar datos de renta histórica
        # (Ya procesado arriba en la sección de carga inicial para asegurar que dim_barrios esté listo)

        # Procesar datos de regulación (Portal de Dades + Open Data BCN)
        from ..processing.prepare_regulacion import prepare_regulacion  # noqa: WPS433
        from ..processing.prepare_presion_turistica import prepare_presion_turistica  # noqa: WPS433
        from ..processing.prepare_seguridad import prepare_seguridad  # noqa: WPS433
        from ..processing.prepare_ruido import prepare_ruido  # noqa: WPS433
        from ..processing.prepare_movilidad import prepare_movilidad  # noqa: WPS433
        from ..processing.prepare_calidad_aire import prepare_calidad_aire  # noqa: WPS433
 
        fact_regulacion = None
        fact_presion_turistica = None
        fact_seguridad = None
        fact_ruido = None
        fact_educacion = None
        fact_movilidad = None
        fact_vivienda_publica = None
        fact_calidad_aire = None
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
        
        # Procesar datos de calidad del aire
        try:
            logger.info("=== Procesando datos de calidad del aire ===")
            fact_calidad_aire = prepare_calidad_aire(
                raw_data_path=raw_base_dir,
                barrios_df=dim_barrios,
                reference_time=reference_time,
            )
            
            if fact_calidad_aire is not None and not fact_calidad_aire.empty:
                logger.info(
                    "✓ Calidad del aire procesada: %s registros (años %s-%s)",
                    len(fact_calidad_aire),
                    fact_calidad_aire["anio"].min() if not fact_calidad_aire.empty else None,
                    fact_calidad_aire["anio"].max() if not fact_calidad_aire.empty else None,
                )
                params["calidad_aire_rows"] = int(len(fact_calidad_aire))
                params["calidad_aire_barrios"] = int(fact_calidad_aire["barrio_id"].nunique())
            else:
                logger.warning(
                    "No se encontraron datos de calidad del aire procesables. "
                    "Verifica que existan archivos CSV de mapas de inmisión."
                )
        except Exception as e:
            handle_source_error("calidad_aire", e, context="procesamiento")
            fact_calidad_aire = None
        
        # Procesar movilidad y accesibilidad (TMB/OSM)
        try:
            logger.info("=== Procesando movilidad y accesibilidad ===")
            fact_movilidad = prepare_movilidad(
                raw_data_dir=raw_base_dir,
                barrios_df=dim_barrios,
                reference_time=reference_time
            )
            if fact_movilidad is not None and not fact_movilidad.empty:
                logger.info("✓ Movilidad procesada: %s registros", len(fact_movilidad))
                params["movilidad_rows"] = int(len(fact_movilidad))
        except Exception as e:
            handle_source_error("movilidad", e, context="procesamiento")
            fact_movilidad = None

        # Procesar Educación (Nuevo en 3B)
        if educacion_path:
            logger.info("=== Procesando datos de Educación ===")
            try:
                educacion_df_raw = _safe_read_csv(educacion_path)
                fact_educacion = prepare_fact_educacion(educacion_df_raw, dim_barrios, reference_time)
                if fact_educacion is not None and not fact_educacion.empty:
                    logger.info("✓ Educación procesada: %s registros", len(fact_educacion))
                    params["educacion_rows"] = int(len(fact_educacion))
            except Exception as e:
                handle_source_error("educacion", e, context="procesamiento")
                fact_educacion = None

        # Procesar Vivienda Pública (Nuevo en 3B)
        if vivienda_publica_files:
            logger.info("=== Procesando datos de Vivienda Pública ===")
            try:
                vp_data = {}
                for k, v in vivienda_publica_files.items():
                    if v: vp_data[k] = _safe_read_csv(v)
                fact_vivienda_publica = prepare_fact_vivienda_publica(vp_data, dim_barrios, reference_time)
                if fact_vivienda_publica is not None and not fact_vivienda_publica.empty:
                    logger.info("✓ Vivienda Pública procesada: %s registros", len(fact_vivienda_publica))
                    params["vivienda_publica_rows"] = int(len(fact_vivienda_publica))
            except Exception as e:
                handle_source_error("vivienda_publica", e, context="procesamiento")
                fact_vivienda_publica = None

        # Procesar renta si está disponible
        fact_renta = None
        if renta_df is not None and not renta_df.empty:
            logger.info("Procesando datos de renta...")
            try:
                fact_renta = prepare_renta_barrio(
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
                
                fact_oferta_idealista = prepare_idealista_oferta(
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

        # Procesar datasets avanzados
        logger.info("Procesando datasets avanzados...")
        fact_renta_avanzada = prepare_fact_renta_avanzada(renta_avanzada_files, dim_barrios, reference_time) if renta_avanzada_files else None
        fact_catastro_avanzado = prepare_fact_catastro_avanzado(catastro_avanzado_files, dim_barrios, reference_time) if catastro_avanzado_files else None
        fact_hogares_avanzado = prepare_fact_hogares_avanzado(hogares_avanzado_files, dim_barrios, reference_time) if hogares_avanzado_files else None
        fact_turismo_intensidad = prepare_fact_turismo_intensidad(turismo_intensidad_files, dim_barrios, reference_time) if turismo_intensidad_files else None

        # 14. Calcular esfuerzo de alquiler (Affordability)
        if fact_precios is not None and not fact_precios.empty and \
           fact_renta_hist is not None and not fact_renta_hist.empty:
            logger.info("Calculando métricas de esfuerzo de alquiler (series históricas)...")
            try:
                fact_esfuerzo_alquiler = calculate_affordability_metrics(
                    fact_precios,
                    fact_renta_hist,
                    reference_time
                )
            except Exception as e:
                logger.warning("Error calculando esfuerzo de alquiler: %s", e)
                logger.debug(traceback.format_exc())

        # === VALIDACIÓN DE INTEGRIDAD REFERENCIAL ===
        # Validar todas las fact tables antes de insertar en SQLite
        logger.info("=== Validando integridad referencial ===")
        (
            fact_precios,
            fact_demografia,
            fact_demografia_ampliada,
            # Nota: fact_alquiler_mensual aún no está integrado en validate_all_fact_tables
            fact_renta,
            fact_oferta_idealista,
            fact_regulacion,
            fact_presion_turistica,
            fact_seguridad,
            fact_ruido,
            fact_educacion,
            fact_movilidad,
            fact_vivienda_publica,
            fact_renta_avanzada,
            fact_catastro_avanzado,
            fact_hogares_avanzado,
            fact_turismo_intensidad,
            fact_renta_hist,
            fact_esfuerzo_alquiler,
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
            fact_educacion=fact_educacion,
            fact_movilidad=fact_movilidad,
            fact_vivienda_publica=fact_vivienda_publica,
            fact_renta_avanzada=fact_renta_avanzada,
            fact_catastro_avanzado=fact_catastro_avanzado,
            fact_hogares_avanzado=fact_hogares_avanzado,
            fact_turismo_intensidad=fact_turismo_intensidad,
            fact_renta_hist=fact_renta_hist,
            fact_esfuerzo_alquiler=fact_esfuerzo_alquiler,
            strategy=FKValidationStrategy.FILTER,
        )
        
        # Note: fact_calidad_aire validation skipped (not in validator signature yet)
        # It will be validated by foreign key constraints at insert time
        
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
                "fact_alquiler_mensual_rows": int(len(fact_alquiler_mensual)) if fact_alquiler_mensual is not None else 0,
                "fact_oferta_idealista_rows": int(len(fact_oferta_idealista)) if fact_oferta_idealista is not None else 0,
                "fact_regulacion_rows": int(len(fact_regulacion)) if fact_regulacion is not None else 0,
                "fact_renta_hist_rows": int(len(fact_renta_hist)) if fact_renta_hist is not None else 0,
                "fact_esfuerzo_alquiler_rows": int(len(fact_esfuerzo_alquiler)) if fact_esfuerzo_alquiler is not None else 0,
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
        if fact_alquiler_mensual is not None:
            tables_to_truncate.append("fact_alquiler_mensual")
        if fact_renta is not None:
            tables_to_truncate.append("fact_renta")
        if fact_oferta_idealista is not None:
            tables_to_truncate.append("fact_oferta_idealista")
        if fact_regulacion is not None:
            tables_to_truncate.append("fact_regulacion")
        tables_to_truncate.append("fact_precios")
        if fact_renta_hist is not None:
            tables_to_truncate.append("fact_renta_hist")
        if fact_esfuerzo_alquiler is not None:
            tables_to_truncate.append("fact_esfuerzo_alquiler")
        if fact_renta_avanzada is not None:
            tables_to_truncate.append("fact_renta_avanzada")
        if fact_catastro_avanzado is not None:
            tables_to_truncate.append("fact_catastro_avanzado")
        if fact_hogares_avanzado is not None:
            tables_to_truncate.append("fact_hogares_avanzado")
        if fact_turismo_intensidad is not None:
            tables_to_truncate.append("fact_turismo_intensidad")
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

        # Cargar demografía (estándar o ampliada) con batch processing
        # ESTRATEGIA: Cargar ambos tipos si están disponibles
        if fact_demografia_ampliada is not None and not fact_demografia_ampliada.empty:
            logger.info("Cargando tabla de hechos demográficos ampliados")
            fact_demografia_ampliada = optimize_dataframe_memory(fact_demografia_ampliada)
            insert_dataframe_in_batches(
                fact_demografia_ampliada, "fact_demografia_ampliada", conn,
                batch_size=10000, if_exists="append"
            )
            del fact_demografia_ampliada
            gc.collect()
        
        if fact_demografia is not None and not fact_demografia.empty:
            logger.info("Cargando tabla de hechos demográficos")
            fact_demografia = optimize_dataframe_memory(fact_demografia)
            insert_dataframe_in_batches(
                fact_demografia, "fact_demografia", conn,
                batch_size=10000, if_exists="append"
            )
            del fact_demografia
            gc.collect()
        elif fact_demografia_ampliada is None or fact_demografia_ampliada.empty:
            logger.warning("No se cargaron datos demográficos")

        if not fact_precios.empty:
            logger.info("Cargando tabla de hechos de precios")
            fact_precios = optimize_dataframe_memory(fact_precios)
            insert_dataframe_in_batches(
                fact_precios, "fact_precios", conn,
                batch_size=10000, if_exists="append"
            )
            del fact_precios
            gc.collect()
        else:
            logger.warning(
                "No se cargaron datos en fact_precios (dataframe vacío)"
            )

        if fact_alquiler_mensual is not None and not fact_alquiler_mensual.empty:
            logger.info("Cargando tabla de hechos de alquiler mensual")
            fact_alquiler_mensual = optimize_dataframe_memory(fact_alquiler_mensual)
            insert_dataframe_in_batches(
                fact_alquiler_mensual,
                "fact_alquiler_mensual",
                conn,
                batch_size=10000,
                if_exists="append",
            )
            del fact_alquiler_mensual
            gc.collect()
        
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

        if fact_calidad_aire is not None and not fact_calidad_aire.empty:
            logger.info("Cargando tabla de hechos de calidad del aire")
            fact_calidad_aire.to_sql(
                "fact_calidad_aire",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug(
                "No se cargaron datos en fact_calidad_aire (no disponible o vacío)"
            )

        if fact_renta_hist is not None and not fact_renta_hist.empty:
            logger.info("Cargando tabla de hechos de renta histórica")
            fact_renta_hist.to_sql(
                "fact_renta_hist",
                conn,
                if_exists="append",
                index=False,
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
 
        if fact_movilidad is not None and not fact_movilidad.empty:
            logger.info("Cargando tabla de hechos de movilidad")
            fact_movilidad.to_sql(
                "fact_movilidad",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            logger.debug("No se cargaron datos en fact_movilidad (no disponible o vacío)")

        if fact_educacion is not None and not fact_educacion.empty:
            logger.info("Cargando tabla de hechos de educación")
            fact_educacion.to_sql("fact_educacion", conn, if_exists="replace", index=False)
        
        if fact_vivienda_publica is not None and not fact_vivienda_publica.empty:
            logger.info("Cargando tabla de hechos de vivienda pública")
            fact_vivienda_publica.to_sql("fact_vivienda_publica", conn, if_exists="replace", index=False)

        if fact_esfuerzo_alquiler is not None and not fact_esfuerzo_alquiler.empty:
            logger.info("Cargando tabla de hechos de esfuerzo de alquiler")
            fact_esfuerzo_alquiler.to_sql(
                "fact_esfuerzo_alquiler",
                conn,
                if_exists="append",
                index=False,
            )

         # Cargar datasets avanzados usando batch processing
        logger.info("=== Cargando datasets avanzados con procesamiento por lotes ===")
        
        # Optimize memory before insertion
        if fact_renta_avanzada is not None:
            fact_renta_avanzada = optimize_dataframe_memory(fact_renta_avanzada)
        if fact_catastro_avanzado is not None:
            fact_catastro_avanzado = optimize_dataframe_memory(fact_catastro_avanzado)
        if fact_hogares_avanzado is not None:
            fact_hogares_avanzado = optimize_dataframe_memory(fact_hogares_avanzado)
        if fact_turismo_intensidad is not None:
            fact_turismo_intensidad = optimize_dataframe_memory(fact_turismo_intensidad)
        
        # Insert using batch processing
        insert_dataframe_in_batches(
            fact_renta_avanzada, "fact_renta_avanzada", conn, 
            batch_size=5000, clear_first=True
        )
        gc.collect()  # Force garbage collection between tables
        
        insert_dataframe_in_batches(
            fact_catastro_avanzado, "fact_catastro_avanzado", conn,
            batch_size=5000, clear_first=True
        )
        gc.collect()
        
        insert_dataframe_in_batches(
            fact_hogares_avanzado, "fact_hogares_avanzado", conn,
            batch_size=5000, clear_first=True
        )
        gc.collect()
        
        insert_dataframe_in_batches(
            fact_turismo_intensidad, "fact_turismo_intensidad", conn,
            batch_size=5000, clear_first=True
        )
        gc.collect()

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
