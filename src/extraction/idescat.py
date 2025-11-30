"""
IDESCAT Extractor Module - Extracción de datos del Institut d'Estadística de Catalunya.

Este módulo proporciona funcionalidades para extraer datos de renta histórica
por barrio desde IDESCAT (2015-2023).
"""

import io
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger


class IDESCATExtractor(BaseExtractor):
    """
    Extractor para datos del Institut d'Estadística de Catalunya (IDESCAT).
    
    Este extractor está diseñado para obtener datos de renta disponible por barrio
    de Barcelona para el período 2015-2023. Utiliza la API v1 de IDESCAT y, si
    es necesario, busca alternativas en el sitio web o datos públicos.
    """
    
    BASE_URL = "https://www.idescat.cat"
    API_BASE_URL = "https://api.idescat.cat"
    
    # Servicios disponibles en la API
    SERVICE_INDICADORS = "indicadors"
    SERVICE_POB = "pob"  # Población
    
    def __init__(self, rate_limit_delay: float = 1.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de IDESCAT.
        
        Args:
            rate_limit_delay: Tiempo de espera entre peticiones (segundos)
            output_dir: Directorio donde guardar los datos (None = usar default)
        """
        super().__init__("IDESCAT", rate_limit_delay, output_dir)
    
    def get_renta_by_barrio(
        self,
        year_start: int = 2015,
        year_end: int = 2023
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Obtiene datos de renta disponible por barrio para el período especificado.
        
        Este método intenta múltiples estrategias:
        1. Open Data BCN (fuente principal - tiene datos por barrio confirmados)
        2. API de indicadores IDESCAT (fallback - solo datos agregados)
        3. Búsqueda en el sitio web de IDESCAT
        
        Args:
            year_start: Año inicial del período
            year_end: Año final del período
            
        Returns:
            Tupla con (DataFrame con datos de renta, metadata de cobertura)
        """
        logger.info(f"Extrayendo datos de renta ({year_start}-{year_end})")
        
        coverage_metadata = {
            "requested_range": {"start": year_start, "end": year_end},
            "strategy_used": None,
            "years_extracted": [],
            "years_failed": [],
            "success": False
        }
        
        # Estrategia 1: Open Data BCN (fuente principal - tiene datos por barrio)
        logger.info("Estrategia 1: Intentando Open Data BCN (fuente principal)...")
        df, metadata = self._try_opendata_bcn(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "opendata_bcn"
            coverage_metadata["success"] = True
            # Guardar datos
            self._save_renta_data(df, year_start, year_end)
            return df, coverage_metadata
        
        # Estrategia 2: Intentar API de indicadores IDESCAT (fallback - solo agregados)
        logger.info("Estrategia 2: Intentando API de indicadores IDESCAT (fallback)...")
        df, metadata = self._try_api_indicators(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "api_indicators"
            coverage_metadata["success"] = True
            # Guardar datos
            self._save_renta_data(df, year_start, year_end)
            return df, coverage_metadata
        
        # Estrategia 3: Buscar en el sitio web
        logger.info("Estrategia 3: Buscando datos en el sitio web...")
        df, metadata = self._try_web_scraping(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "web_scraping"
            coverage_metadata["success"] = True
            # Guardar datos
            self._save_renta_data(df, year_start, year_end)
            return df, coverage_metadata
        
        # Si todas las estrategias fallan
        logger.warning("No se pudieron extraer datos de renta")
        coverage_metadata["error"] = "Todas las estrategias de extracción fallaron"
        return pd.DataFrame(), coverage_metadata
    
    def _try_api_indicators(
        self,
        year_start: int,
        year_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intenta obtener datos de renta usando la API de indicadores IDESCAT.
        
        NOTA: La API de IDESCAT solo proporciona datos agregados a nivel de Cataluña,
        no por barrio. Este método se mantiene como fallback para datos agregados.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata)
        """
        metadata = {
            "strategy": "api_indicators",
            "success": False,
            "note": "API IDESCAT solo proporciona datos agregados (no por barrio)"
        }
        
        # Indicador identificado: m10409 - "Renta anual" - "Renta media neta por persona"
        indicator_id = "m10409"
        
        logger.info(f"Consultando API IDESCAT - Indicador {indicator_id}...")
        logger.warning("⚠️ API IDESCAT solo tiene datos agregados a nivel de Cataluña, no por barrio")
        
        try:
            url = f"{self.API_BASE_URL}/{self.SERVICE_INDICADORS}/v1/dades.json"
            params = {
                "i": indicator_id,
                "lang": "es"
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if not self._validate_response(response):
                logger.warning("No se pudo acceder a la API de indicadores")
                return pd.DataFrame(), metadata
            
            data = response.json()
            
            # Extraer datos del indicador
            if 'indicadors' in data and 'i' in data['indicadors']:
                indicator = data['indicadors']['i']
                
                # Manejar caso donde 'i' puede ser lista
                if isinstance(indicator, list):
                    if len(indicator) > 0:
                        indicator = indicator[0]
                    else:
                        logger.warning("Respuesta de API vacía")
                        return pd.DataFrame(), metadata
                
                # Extraer serie temporal
                ts_values = indicator.get('ts', '')
                if isinstance(ts_values, str):
                    values = [float(v) for v in ts_values.split(',') if v.strip()]
                    
                    if values:
                        # Crear DataFrame con datos agregados
                        # Nota: Estos son datos a nivel de Cataluña, no por barrio
                        df = pd.DataFrame({
                            'territorio': ['Cataluña'] * len(values),
                            'renta_media_neta_persona': values,
                            'anio': [year_end - len(values) + i + 1 for i in range(len(values))],
                            'source': 'idescat_api',
                            'indicator_id': indicator_id
                        })
                        
                        # Filtrar por años solicitados
                        df = df[(df['anio'] >= year_start) & (df['anio'] <= year_end)]
                        
                        if not df.empty:
                            logger.info(f"✓ Datos agregados obtenidos: {len(df)} registros (nivel: Cataluña)")
                            metadata["success"] = True
                            metadata["records"] = len(df)
                            metadata["level"] = "aggregated_catalunya"
                            metadata["warning"] = "Datos solo a nivel de Cataluña, no por barrio"
                            return df, metadata
                        else:
                            logger.warning("No hay datos en el rango temporal solicitado")
                    else:
                        logger.warning("No se encontraron valores en la serie temporal")
                else:
                    logger.warning("Formato de serie temporal no reconocido")
            else:
                logger.warning("Estructura de respuesta de API no reconocida")
            
        except Exception as e:
            logger.error(f"Error accediendo a la API de indicadores: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
        
        return pd.DataFrame(), metadata
    
    def _try_web_scraping(
        self,
        year_start: int,
        year_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intenta obtener datos mediante scraping del sitio web de IDESCAT.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata)
        """
        metadata = {
            "strategy": "web_scraping",
            "success": False
        }
        
        logger.info("Buscando datos de renta en el sitio web de IDESCAT...")
        
        # Por ahora, esta estrategia requiere investigación adicional
        # sobre la estructura del sitio web de IDESCAT
        
        try:
            # Buscar página de datos de renta
            search_url = f"{self.BASE_URL}/dades/?lang=es"
            
            self._rate_limit()
            response = self.session.get(search_url, timeout=30)
            
            if not self._validate_response(response):
                logger.warning("No se pudo acceder al sitio web de IDESCAT")
                return pd.DataFrame(), metadata
            
            # Aquí se implementaría el scraping específico
            # Por ahora, retornamos DataFrame vacío
            logger.info("Sitio web accesible, pero se requiere implementación de scraping específico")
            metadata["note"] = "Sitio web accesible pero requiere implementación de scraping"
            
        except Exception as e:
            logger.error(f"Error en web scraping: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
        
        return pd.DataFrame(), metadata
    
    def _try_opendata_bcn(
        self,
        year_start: int,
        year_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intenta obtener datos de renta desde Open Data BCN.
        
        Open Data BCN tiene datasets confirmados con datos de renta por barrio:
        - renda-disponible-llars-bcn: Renda disponible per càpita (€)
        - atles-renda-bruta-per-llar: Renda bruta mitjana per llar (€)
        - atles-renda-bruta-per-persona: Renda bruta mitjana per persona (€)
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata)
        """
        metadata = {
            "strategy": "opendata_bcn",
            "success": False,
            "datasets_tried": []
        }
        
        logger.info("Extrayendo datos de renta desde Open Data BCN...")
        
        try:
            from .opendata import OpenDataBCNExtractor
            
            # Crear extractor de Open Data BCN
            bcn_extractor = OpenDataBCNExtractor(
                rate_limit_delay=self.rate_limit_delay,
                output_dir=self.output_dir
            )
            
            # IDs de datasets conocidos y confirmados con datos por barrio
            known_datasets = [
                "renda-disponible-llars-bcn",  # Renda disponible per càpita (€)
                "atles-renda-bruta-per-llar",  # Renda bruta mitjana per llar (€)
                "atles-renda-bruta-per-persona",  # Renda bruta mitjana per persona (€)
            ]
            
            all_data = []
            
            for dataset_id in known_datasets:
                logger.info(f"  Probando dataset: {dataset_id}")
                metadata["datasets_tried"].append(dataset_id)
                
                try:
                    # Intentar descargar sin filtro de año primero (los datasets pueden no tener columna de año)
                    df, cov_meta = bcn_extractor.download_dataset(
                        dataset_id,
                        resource_format='csv',
                        year_start=None,  # Sin filtro inicial
                        year_end=None
                    )
                    
                    # Si hay datos, intentar filtrar por año si existe columna de año
                    if df is not None and not df.empty:
                        year_cols = [col for col in df.columns 
                                    if any(kw in col.lower() for kw in ['any', 'año', 'year', 'anio'])]
                        if year_cols:
                            year_col = year_cols[0]
                            # Convertir a numérico y filtrar
                            try:
                                df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
                                df = df[(df[year_col] >= year_start) & (df[year_col] <= year_end)]
                            except Exception:
                                pass  # Si falla el filtro, usar todos los datos
                    
                    if df is not None and not df.empty:
                        # Validar que tiene columnas de barrio
                        barrio_cols = ['Codi_Barri', 'Nom_Barri', 'barrio', 'barri', 'Barris']
                        has_barrio = any(col in df.columns for col in barrio_cols)
                        
                        if has_barrio:
                            logger.info(f"  ✓ Dataset {dataset_id}: {len(df)} registros")
                            # Agregar información del dataset
                            df['dataset_id'] = dataset_id
                            df['source'] = 'opendatabcn'
                            all_data.append(df)
                        else:
                            logger.warning(f"  ⚠️ Dataset {dataset_id} no tiene columnas de barrio")
                    else:
                        logger.debug(f"  Dataset {dataset_id} vacío o no disponible")
                        
                except Exception as e:
                    logger.debug(f"  Error con dataset {dataset_id}: {e}")
                    continue
            
            if not all_data:
                logger.warning("No se obtuvieron datos de Open Data BCN")
                metadata["error"] = "Ningún dataset de Open Data BCN disponible"
                return pd.DataFrame(), metadata
            
            # Combinar todos los datasets
            df_combined = pd.concat(all_data, ignore_index=True)
            
            # Si hay datos por sección censal, agregar por barrio
            if 'Seccio_Censal' in df_combined.columns and 'Codi_Barri' in df_combined.columns:
                logger.info("Agregando datos por barrio (de sección censal)...")
                # Identificar columnas de renta
                renta_cols = [col for col in df_combined.columns 
                             if any(kw in col.lower() for kw in ['renta', 'renda', 'import', 'euros', '€'])]
                
                if renta_cols:
                    # Agrupar por barrio y calcular media
                    group_cols = ['Codi_Barri', 'Nom_Barri'] if 'Nom_Barri' in df_combined.columns else ['Codi_Barri']
                    df_combined = df_combined.groupby(group_cols)[renta_cols].mean().reset_index()
                    logger.info(f"  Datos agregados: {len(df_combined)} barrios")
            
            metadata["success"] = True
            metadata["records"] = len(df_combined)
            metadata["columns"] = list(df_combined.columns)
            metadata["datasets_used"] = [ds for ds in known_datasets if ds in metadata["datasets_tried"]]
            
            logger.info(f"✅ Total registros de renta desde Open Data BCN: {len(df_combined)}")
            return df_combined, metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de Open Data BCN: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
            return pd.DataFrame(), metadata
    
    def _save_renta_data(
        self,
        df: pd.DataFrame,
        year_start: int,
        year_end: int
    ) -> Path:
        """
        Guarda los datos de renta extraídos en formato CSV.
        
        Args:
            df: DataFrame con datos de renta
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Path del archivo guardado
        """
        return self._save_raw_data(
            df,
            "idescat_renta",
            'csv',
            year_start=year_start,
            year_end=year_end,
            data_type="renta_historica"
        )
    
    def _normalize_barrio_name(self, name: str) -> str:
        """
        Normaliza el nombre de un barrio para mapearlo a codi_barri.
        
        Args:
            name: Nombre del barrio desde IDESCAT
            
        Returns:
            Nombre normalizado
        """
        # Importar el cleaner para usar la normalización estándar
        from ..transform.cleaners import HousingCleaner
        
        cleaner = HousingCleaner()
        return cleaner.normalize_neighborhoods(name)
    
    def _map_barrio_to_id(
        self,
        barrio_name: str,
        dim_barrios: Optional[pd.DataFrame] = None
    ) -> Optional[int]:
        """
        Mapea un nombre de barrio a su barrio_id.
        
        Args:
            barrio_name: Nombre del barrio
            dim_barrios: DataFrame con la dimensión de barrios (opcional)
            
        Returns:
            barrio_id si se encuentra, None si no
        """
        # Si no se proporciona dim_barrios, intentar cargarlo desde la BD
        if dim_barrios is None:
            try:
                import sqlite3
                from ..database_setup import DEFAULT_DB_NAME
                from pathlib import Path
                
                db_path = Path(__file__).parent.parent.parent / "data" / "processed" / DEFAULT_DB_NAME
                if db_path.exists():
                    conn = sqlite3.connect(db_path)
                    dim_barrios = pd.read_sql_query(
                        "SELECT barrio_id, barrio_nombre, barrio_nombre_normalizado FROM dim_barrios",
                        conn
                    )
                    conn.close()
                else:
                    logger.warning("Base de datos no encontrada, no se puede mapear barrio")
                    return None
            except Exception as e:
                logger.error(f"Error cargando dim_barrios: {e}")
                return None
        
        if dim_barrios is None or dim_barrios.empty:
            logger.warning("dim_barrios vacío, no se puede mapear barrio")
            return None
        
        # Normalizar nombre
        barrio_normalizado = self._normalize_barrio_name(barrio_name)
        
        # Buscar coincidencia exacta normalizada
        match = dim_barrios[
            dim_barrios["barrio_nombre_normalizado"] == barrio_normalizado
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])
        
        # Buscar coincidencia parcial
        match = dim_barrios[
            dim_barrios["barrio_nombre"].str.contains(
                barrio_name, case=False, na=False, regex=False
            )
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])
        
        logger.warning(f"No se pudo mapear el barrio '{barrio_name}' (normalizado: '{barrio_normalizado}')")
        return None

