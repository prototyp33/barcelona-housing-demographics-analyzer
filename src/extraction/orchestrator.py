"""
Extraction Orchestrator Module - Coordina la extracción de múltiples fuentes.
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import DATA_RAW_DIR, EXTRACTION_LOGS_DIR, MIN_RECORDS_WARNING, logger
from .generalitat_extractor import GeneralitatExtractor
from .idealista import IdealistaExtractor
from .ine import INEExtractor
from .opendata import OpenDataBCNExtractor
from .portaldades import PortalDadesExtractor


def validate_data_size(
    df: pd.DataFrame,
    source_name: str,
    min_records: int = MIN_RECORDS_WARNING
) -> bool:
    """
    Valida el tamaño de los datos extraídos.
    
    Args:
        df: DataFrame a validar
        source_name: Nombre de la fuente
        min_records: Número mínimo de registros esperados
        
    Returns:
        True si los datos son válidos, False si están vacíos o sospechosamente pequeños
    """
    if df is None or df.empty:
        logger.warning(f"⚠️  {source_name}: DataFrame vacío - No se obtuvieron datos")
        return False
    
    record_count = len(df)
    if record_count < min_records:
        logger.warning(
            f"⚠️  {source_name}: Solo {record_count} registros obtenidos "
            f"(mínimo esperado: {min_records}). Los datos pueden estar incompletos."
        )
        return False
    
    logger.info(f"✓ {source_name}: {record_count:,} registros válidos")
    return True


def write_extraction_summary(
    results: Dict[str, pd.DataFrame],
    metadata: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Escribe un resumen de la extracción en formato texto plano.
    
    Args:
        results: Diccionario con DataFrames por fuente
        metadata: Metadata de cobertura y errores
        output_dir: Directorio donde guardar el resumen (None = data/logs/)
        
    Returns:
        Path del archivo de resumen creado
    """
    if output_dir is None:
        output_dir = EXTRACTION_LOGS_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_dir / f"extraction_{timestamp}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RESUMEN DE EXTRACCIÓN DE DATOS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Fecha de extracción: {metadata.get('extraction_date', 'N/A')}\n")
        f.write(f"Rango solicitado: {metadata.get('requested_range', {}).get('start', 'N/A')} - "
                f"{metadata.get('requested_range', {}).get('end', 'N/A')}\n")
        f.write(f"Fuentes solicitadas: {', '.join(metadata.get('sources_requested', []))}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("RESUMEN POR FUENTE\n")
        f.write("-" * 80 + "\n\n")
        
        total_records = 0
        for source, df in results.items():
            records = len(df) if df is not None and not df.empty else 0
            total_records += records
            status = "✓" if records > 0 else "✗"
            
            # Validar sin logging (ya se hizo durante la extracción)
            if records == 0:
                validation_status = "VACÍO"
            elif records < MIN_RECORDS_WARNING:
                validation_status = "SOSPECHOSO"
            else:
                validation_status = "VÁLIDO"
            
            f.write(f"{status} {source:35s} {records:>10,} registros [{validation_status}]\n")
        
        f.write(f"\nTotal de registros extraídos: {total_records:,}\n\n")
        
        # Cobertura temporal
        if metadata.get("coverage_by_source"):
            f.write("-" * 80 + "\n")
            f.write("COBERTURA TEMPORAL\n")
            f.write("-" * 80 + "\n\n")
            
            for source, cov_meta in metadata["coverage_by_source"].items():
                if isinstance(cov_meta, dict):
                    if "coverage_percentage" in cov_meta:
                        coverage = cov_meta["coverage_percentage"]
                        missing = cov_meta.get("missing_years", [])
                        if coverage < 100:
                            f.write(f"⚠️  {source:35s} {coverage:>5.1f}% - Años faltantes: {missing}\n")
                        else:
                            f.write(f"✓   {source:35s} {coverage:>5.1f}% - Completo\n")
                    elif "error" in cov_meta:
                        f.write(f"✗   {source:35s} Error: {cov_meta['error']}\n")
        
        # Estado de fuentes
        if metadata.get("sources_success") or metadata.get("sources_failed"):
            f.write("\n" + "-" * 80 + "\n")
            f.write("ESTADO DE FUENTES\n")
            f.write("-" * 80 + "\n\n")
            
            if metadata.get("sources_success"):
                f.write(f"✓ Fuentes exitosas: {', '.join(metadata['sources_success'])}\n")
            if metadata.get("sources_failed"):
                f.write(f"✗ Fuentes fallidas: {', '.join(metadata['sources_failed'])}\n")
        
        # Advertencias sobre datos sospechosos
        f.write("\n" + "-" * 80 + "\n")
        f.write("VALIDACIÓN DE DATOS\n")
        f.write("-" * 80 + "\n\n")
        
        suspicious_sources = []
        for source, df in results.items():
            if df is not None and not df.empty:
                if len(df) < MIN_RECORDS_WARNING:
                    suspicious_sources.append(f"{source} ({len(df)} registros)")
        
        if suspicious_sources:
            f.write("⚠️  ADVERTENCIA: Las siguientes fuentes tienen pocos registros:\n")
            for source in suspicious_sources:
                f.write(f"   - {source}\n")
        else:
            f.write("✓ Todas las fuentes tienen un número adecuado de registros\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Resumen guardado: {summary_file}\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Resumen de extracción guardado en: {summary_file}")
    return summary_file


def extract_all_sources(
    year_start: int = 2015,
    year_end: int = 2025,
    sources: Optional[List[str]] = None,
    continue_on_error: bool = True,
    parallel: bool = False,  # Futuro: habilitar paralelización
    output_dir: Optional[Path] = None
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Extrae datos de todas las fuentes configuradas.
    
    Args:
        year_start: Año inicial
        year_end: Año final
        sources: Lista de fuentes a extraer (None = todas)
        continue_on_error: Si True, continúa con otras fuentes si una falla
        parallel: Si True, ejecuta extracciones en paralelo (futuro)
        output_dir: Directorio donde guardar los datos
        
    Returns:
        Tupla con (diccionario de DataFrames por fuente, metadata de cobertura)
    """
    if sources is None:
        sources = ["ine", "opendatabcn", "idealista", "portaldades", "generalitat"]
    
    # Configurar directorio de salida
    if output_dir is None:
        output_dir = DATA_RAW_DIR
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    coverage_metadata = {
        "extraction_date": datetime.now().isoformat(),
        "requested_range": {"start": year_start, "end": year_end},
        "sources_requested": sources,
        "sources_success": [],
        "sources_failed": [],
        "coverage_by_source": {},
        "output_dir": str(output_dir)
    }
    
    # INE
    if "ine" in sources:
        try:
            logger.info("=== Extrayendo datos del INE ===")
            ine_extractor = INEExtractor(output_dir=output_dir)
            df, metadata = ine_extractor.get_demographic_data(year_start, year_end)
            results["ine"] = df
            coverage_metadata["coverage_by_source"]["ine"] = metadata
            
            # Validar tamaño de datos
            is_valid = validate_data_size(df, "INE")
            
            if not df.empty and is_valid:
                coverage_metadata["sources_success"].append("ine")
            else:
                coverage_metadata["sources_failed"].append("ine")
        except Exception as e:
            error_msg = f"Error en extracción INE: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            results["ine"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("ine")
            coverage_metadata["coverage_by_source"]["ine"] = {
                "error": str(e),
                "success": False
            }
            if not continue_on_error:
                raise
    
    # Open Data BCN
    if "opendatabcn" in sources:
        try:
            logger.info("=== Extrayendo datos de Open Data BCN ===")
            bcn_extractor = OpenDataBCNExtractor(output_dir=output_dir)
            
            # Demographics (usando nuevo método con IDs correctos)
            try:
                df_demo, metadata_demo = bcn_extractor.extract_demographics_ckan(
                    year_start, year_end
                )
                results["opendatabcn_demographics"] = df_demo if df_demo is not None else pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_demographics"] = metadata_demo
                
                # Validar tamaño de datos
                is_valid = validate_data_size(results["opendatabcn_demographics"], "OpenDataBCN Demographics")
                
                if df_demo is not None and not df_demo.empty and is_valid:
                    coverage_metadata["sources_success"].append("opendatabcn_demographics")
                else:
                    coverage_metadata["sources_failed"].append("opendatabcn_demographics")
            except Exception as e:
                logger.error(f"Error extrayendo demographics de Open Data BCN: {e}")
                logger.debug(traceback.format_exc())
                results["opendatabcn_demographics"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_demographics"] = {"error": str(e)}
                coverage_metadata["sources_failed"].append("opendatabcn_demographics")
            
            # Housing - Venta (usando nuevo método con IDs correctos)
            try:
                df_venta, metadata_venta = bcn_extractor.extract_housing_venta(
                    year_start, year_end
                )
                results["opendatabcn_venta"] = df_venta if df_venta is not None else pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_venta"] = metadata_venta
                
                # Validar tamaño de datos
                is_valid = validate_data_size(results["opendatabcn_venta"], "OpenDataBCN Venta")
                
                if df_venta is not None and not df_venta.empty and is_valid:
                    coverage_metadata["sources_success"].append("opendatabcn_venta")
                else:
                    coverage_metadata["sources_failed"].append("opendatabcn_venta")
            except Exception as e:
                logger.error(f"Error extrayendo venta de Open Data BCN: {e}")
                logger.debug(traceback.format_exc())
                results["opendatabcn_venta"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_venta"] = {"error": str(e)}
                coverage_metadata["sources_failed"].append("opendatabcn_venta")
            
            # Housing - Alquiler (usando nuevo método con IDs correctos)
            try:
                df_alquiler, metadata_alquiler = bcn_extractor.extract_housing_alquiler(
                    year_start, year_end
                )
                results["opendatabcn_alquiler"] = df_alquiler if df_alquiler is not None else pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_alquiler"] = metadata_alquiler
                
                # Validar tamaño de datos
                is_valid = validate_data_size(results["opendatabcn_alquiler"], "OpenDataBCN Alquiler")
                
                if df_alquiler is not None and not df_alquiler.empty and is_valid:
                    coverage_metadata["sources_success"].append("opendatabcn_alquiler")
                else:
                    coverage_metadata["sources_failed"].append("opendatabcn_alquiler")
            except Exception as e:
                logger.error(f"Error extrayendo alquiler de Open Data BCN: {e}")
                logger.debug(traceback.format_exc())
                results["opendatabcn_alquiler"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_alquiler"] = {"error": str(e)}
                coverage_metadata["sources_failed"].append("opendatabcn_alquiler")
            
            # Housing (método legacy para compatibilidad)
            try:
                df_housing, metadata_housing = bcn_extractor.get_housing_data_by_neighborhood(
                    year_start, year_end
                )
                if df_housing is not None and not df_housing.empty:
                    results["opendatabcn_housing"] = df_housing
                    coverage_metadata["coverage_by_source"]["opendatabcn_housing"] = metadata_housing
            except Exception as e:
                logger.debug(f"Método legacy de housing falló (esperado): {e}")
                
        except Exception as e:
            error_msg = f"Error en extracción Open Data BCN: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            if "opendatabcn_demographics" not in results:
                results["opendatabcn_demographics"] = pd.DataFrame()
            if "opendatabcn_housing" not in results:
                results["opendatabcn_housing"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("opendatabcn")
            if not continue_on_error:
                raise
    
    # Idealista
    if "idealista" in sources:
        try:
            logger.info("=== Extrayendo datos de Idealista ===")
            idealista_extractor = IdealistaExtractor(output_dir=output_dir)
            
            # Extraer oferta de venta y alquiler
            idealista_data = []
            idealista_metadata = {}
            
            # Oferta de venta
            df_venta, metadata_venta = idealista_extractor.extract_offer_by_barrio(
                barrio_names=None,  # Buscar en toda Barcelona
                operation="sale",
                max_items_per_barrio=50
            )
            if df_venta is not None and not df_venta.empty:
                idealista_data.append(df_venta)
                idealista_metadata["venta"] = metadata_venta
            
            # Oferta de alquiler
            df_alquiler, metadata_alquiler = idealista_extractor.extract_offer_by_barrio(
                barrio_names=None,  # Buscar en toda Barcelona
                operation="rent",
                max_items_per_barrio=50
            )
            if df_alquiler is not None and not df_alquiler.empty:
                idealista_data.append(df_alquiler)
                idealista_metadata["alquiler"] = metadata_alquiler
            
            # Combinar datos
            if idealista_data:
                results["idealista"] = pd.concat(idealista_data, ignore_index=True)
                coverage_metadata["coverage_by_source"]["idealista"] = {
                    "success": True,
                    "venta": idealista_metadata.get("venta", {}),
                    "alquiler": idealista_metadata.get("alquiler", {}),
                    "total_rows": len(results["idealista"])
                }
                validate_data_size(results["idealista"], "Idealista")
            else:
                logger.warning("No se obtuvieron datos de Idealista (puede requerir API credentials)")
                results["idealista"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["idealista"] = {
                    "success": False,
                    "note": "No se obtuvieron datos. Verifica IDEALISTA_API_KEY y IDEALISTA_API_SECRET."
                }
                coverage_metadata["sources_failed"].append("idealista")
                
        except Exception as e:
            error_msg = f"Error en extracción Idealista: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            results["idealista"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("idealista")
            coverage_metadata["coverage_by_source"]["idealista"] = {"error": str(e)}
            if not continue_on_error:
                raise
    
    # Portal de Dades (nuevo extractor con Playwright y Client ID)
    if "portaldades" in sources:
        try:
            logger.info("=== Extrayendo datos del Portal de Dades (Habitatge) ===")
            portal_extractor = PortalDadesExtractor(output_dir=output_dir)

            # Extraer IDs y descargar indicadores
            try:
                indicadores, archivos = portal_extractor.extraer_y_descargar_habitatge(
                    descargar=True,
                    formato="CSV",
                    max_pages=None,  # Recorrer todas las páginas
                )

                # Crear un DataFrame con la lista de indicadores
                if indicadores:
                    df_indicadores = pd.DataFrame(indicadores)
                    df_indicadores["source"] = "portaldades"
                    df_indicadores["fecha_extraccion"] = datetime.now().isoformat()
                    results["portaldades_indicadores"] = df_indicadores

                    # Metadata
                    coverage_metadata["coverage_by_source"]["portaldades"] = {
                        "success": True,
                        "indicadores_encontrados": len(indicadores),
                        "archivos_descargados": len(
                            [p for p in archivos.values() if p is not None]
                        ),
                        "archivos_fallidos": len(
                            [p for p in archivos.values() if p is None]
                        ),
                    }

                    is_valid = validate_data_size(
                        df_indicadores, "PortalDades Indicadores"
                    )
                    if is_valid:
                        coverage_metadata["sources_success"].append("portaldades")
                    else:
                        coverage_metadata["sources_failed"].append("portaldades")
                else:
                    results["portaldades_indicadores"] = pd.DataFrame()
                    coverage_metadata["coverage_by_source"]["portaldades"] = {
                        "success": False,
                        "error": "No se encontraron indicadores",
                    }
                    coverage_metadata["sources_failed"].append("portaldades")

            except Exception as e:  # noqa: BLE001
                logger.error("Error extrayendo datos del Portal de Dades: %s", e)
                logger.debug(traceback.format_exc())
                results["portaldades_indicadores"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["portaldades"] = {
                    "error": str(e)
                }
                coverage_metadata["sources_failed"].append("portaldades")
                if not continue_on_error:
                    raise

        except Exception as e:  # noqa: BLE001
            error_msg = f"Error en extracción Portal de Dades: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            results["portaldades_indicadores"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("portaldades")
            coverage_metadata["coverage_by_source"]["portaldades"] = {"error": str(e)}
            if not continue_on_error:
                raise

    # Generalitat - índice de referencia de alquileres
    if "generalitat" in sources:
        try:
            logger.info("=== Extrayendo índice de referencia de la Generalitat ===")
            gen_extractor = GeneralitatExtractor(output_dir=output_dir)
            gen_df, gen_meta = gen_extractor.extract_indice_referencia(
                year_start, year_end
            )
            results["generalitat_regulacion"] = gen_df
            coverage_metadata["coverage_by_source"]["generalitat_regulacion"] = gen_meta

            is_valid_generalitat = validate_data_size(
                gen_df, "Generalitat Índice Referencia"
            )
            if gen_meta.get("success") and is_valid_generalitat:
                coverage_metadata["sources_success"].append("generalitat_regulacion")
            else:
                coverage_metadata["sources_failed"].append("generalitat_regulacion")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error en extracción Generalitat (índice referencia): {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            results["generalitat_regulacion"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("generalitat_regulacion")
            coverage_metadata["coverage_by_source"]["generalitat_regulacion"] = {
                "error": str(e),
                "success": False,
            }
            if not continue_on_error:
                raise

    # Validación de cobertura temporal y resumen
    logger.info("=== Resumen de extracción ===")
    for source, df in results.items():
        records = len(df)
        status = "✓" if records > 0 else "✗"
        logger.info(f"{status} {source:30s} {records:>10,} registros")
    
    # Validar cobertura temporal
    logger.info("\n=== Validación de Cobertura Temporal ===")
    for source, metadata in coverage_metadata["coverage_by_source"].items():
        if isinstance(metadata, dict) and "coverage_percentage" in metadata:
            coverage = metadata["coverage_percentage"]
            if coverage < 100:
                missing = metadata.get("missing_years", [])
                logger.warning(
                    f"{source}: Cobertura {coverage:.1f}% - Años faltantes: {missing}"
                )
            else:
                logger.info(f"{source}: Cobertura completa (100%)")
        elif isinstance(metadata, dict) and "error" in metadata:
            logger.error(f"{source}: Error - {metadata['error']}")
    
    # Guardar metadata de cobertura
    metadata_file = output_dir / f"extraction_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(coverage_metadata, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Metadata de cobertura guardada en: {metadata_file}")
    
    # Escribir resumen en texto plano
    summary_file = write_extraction_summary(results, coverage_metadata, output_dir=None)
    coverage_metadata["summary_file"] = str(summary_file)
    
    return results, coverage_metadata

