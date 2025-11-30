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
        1. API de indicadores (si hay datos de renta disponibles)
        2. Búsqueda en el sitio web de IDESCAT
        3. Descarga de CSV/Excel públicos
        
        Args:
            year_start: Año inicial del período
            year_end: Año final del período
            
        Returns:
            Tupla con (DataFrame con datos de renta, metadata de cobertura)
        """
        logger.info(f"Extrayendo datos de renta IDESCAT ({year_start}-{year_end})")
        
        coverage_metadata = {
            "requested_range": {"start": year_start, "end": year_end},
            "strategy_used": None,
            "years_extracted": [],
            "years_failed": [],
            "success": False
        }
        
        # Estrategia 1: Intentar API de indicadores
        logger.info("Estrategia 1: Intentando API de indicadores...")
        df, metadata = self._try_api_indicators(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "api_indicators"
            coverage_metadata["success"] = True
            return df, coverage_metadata
        
        # Estrategia 2: Buscar en el sitio web
        logger.info("Estrategia 2: Buscando datos en el sitio web...")
        df, metadata = self._try_web_scraping(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "web_scraping"
            coverage_metadata["success"] = True
            return df, coverage_metadata
        
        # Estrategia 3: Buscar CSV/Excel públicos
        logger.info("Estrategia 3: Buscando archivos CSV/Excel públicos...")
        df, metadata = self._try_public_files(year_start, year_end)
        if not df.empty:
            coverage_metadata.update(metadata)
            coverage_metadata["strategy_used"] = "public_files"
            coverage_metadata["success"] = True
            return df, coverage_metadata
        
        # Si todas las estrategias fallan
        logger.warning("No se pudieron extraer datos de renta de IDESCAT")
        coverage_metadata["error"] = "Todas las estrategias de extracción fallaron"
        return pd.DataFrame(), coverage_metadata
    
    def _try_api_indicators(
        self,
        year_start: int,
        year_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intenta obtener datos de renta usando la API de indicadores.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata)
        """
        metadata = {
            "strategy": "api_indicators",
            "success": False
        }
        
        # La API de indicadores requiere conocer el ID del indicador específico
        # Por ahora, intentamos buscar indicadores relacionados con renta
        # Nota: Esto requerirá investigación adicional para encontrar el ID correcto
        
        logger.info("Buscando indicadores de renta en la API...")
        
        # Intentar operación 'nodes' para buscar indicadores
        try:
            url = f"{self.API_BASE_URL}/{self.SERVICE_INDICADORS}/v1/nodes.json"
            params = {"lang": "es"}
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if not self._validate_response(response):
                logger.warning("No se pudo acceder a la API de indicadores")
                return pd.DataFrame(), metadata
            
            data = response.json()
            
            # Buscar indicadores relacionados con renta
            # La estructura exacta dependerá de la respuesta de la API
            logger.debug(f"Respuesta API: {str(data)[:500]}")
            
            # Por ahora, retornamos DataFrame vacío ya que necesitamos
            # investigar más sobre la estructura de la API
            logger.info("API de indicadores accesible, pero se requiere investigación adicional para identificar el indicador de renta")
            metadata["note"] = "API accesible pero requiere ID de indicador específico"
            
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
    
    def _try_public_files(
        self,
        year_start: int,
        year_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intenta descargar archivos CSV/Excel públicos de IDESCAT.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata)
        """
        metadata = {
            "strategy": "public_files",
            "success": False
        }
        
        logger.info("Buscando archivos CSV/Excel públicos...")
        
        # Por ahora, esta estrategia requiere conocer las URLs específicas
        # de los archivos públicos de IDESCAT
        
        # Nota: Los datos de renta pueden estar en:
        # - Anuari Estadístic de Barcelona
        # - Datos abiertos del Ayuntamiento de Barcelona
        # - Portal de datos de IDESCAT
        
        metadata["note"] = "Requiere URLs específicas de archivos públicos"
        
        return pd.DataFrame(), metadata
    
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

