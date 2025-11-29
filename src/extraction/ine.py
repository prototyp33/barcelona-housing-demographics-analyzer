"""
INE Extractor Module - Extracción de datos del Instituto Nacional de Estadística.
"""

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, DATA_RAW_DIR, logger


class INEExtractor(BaseExtractor):
    """Extractor para datos del Instituto Nacional de Estadística (INE)."""
    
    BASE_URL = "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA"
    API_URL = "https://www.ine.es/jaxiT3/Tabla.htm"
    
    # Códigos INE para Barcelona
    BARCELONA_CODE = "08019"  # Código INE de Barcelona
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """Inicializa el extractor de INE."""
        super().__init__("INE", rate_limit_delay, output_dir)
    
    def get_demographic_data(
        self,
        year_start: int = 2015,
        year_end: int = 2025,
        variables: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrae datos demográficos de Barcelona del INE.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            variables: Lista de variables a extraer (None = todas disponibles)
            
        Returns:
            Tupla con (DataFrame con datos demográficos, metadata de cobertura)
        """
        logger.info(f"Extrayendo datos demográficos INE para Barcelona ({year_start}-{year_end})")
        
        # Variables demográficas comunes del INE
        if variables is None:
            variables = [
                "Población total",
                "Población por sexo",
                "Población por edad",
                "Nacimientos",
                "Defunciones",
                "Migraciones"
            ]
        
        all_data = []
        years_extracted = []
        years_failed = []
        
        for year in range(year_start, min(year_end + 1, datetime.now().year + 1)):
            try:
                # Nota: El INE requiere códigos específicos de tablas
                # Este es un ejemplo genérico - ajustar según tablas específicas necesarias
                data = self._fetch_ine_table(
                    table_code="2852",  # Ejemplo: Población por municipios
                    territory_code=self.BARCELONA_CODE,
                    year=year
                )
                if data is not None and not data.empty:
                    data['year'] = year
                    all_data.append(data)
                    years_extracted.append(year)
                else:
                    years_failed.append(year)
                
                self._rate_limit()
            except Exception as e:
                logger.error(f"Error extrayendo datos INE para año {year}: {e}")
                logger.debug(traceback.format_exc())
                years_failed.append(year)
                continue
        
        # Metadata de cobertura
        coverage_metadata = {
            "requested_range": {"start": year_start, "end": year_end},
            "years_extracted": sorted(years_extracted),
            "years_failed": sorted(years_failed),
            "coverage_percentage": len(years_extracted) / (year_end - year_start + 1) * 100 if year_end >= year_start else 0
        }
        
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
            self._save_raw_data(
                df,
                "ine_demographics",
                'csv',
                year_start=year_start,
                year_end=year_end,
                data_type="demographics"
            )
            return df, coverage_metadata
        else:
            logger.warning("No se obtuvieron datos del INE")
            return pd.DataFrame(), coverage_metadata
    
    def _fetch_ine_table(
        self,
        table_code: str,
        territory_code: str,
        year: int
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene una tabla específica del INE.
        
        Args:
            table_code: Código de la tabla INE
            territory_code: Código del territorio
            year: Año de los datos
            
        Returns:
            DataFrame con los datos o None si hay error
        """
        self._rate_limit()
        
        # URL para descarga directa de datos del INE
        # Nota: Ajustar según la estructura real de la API del INE
        url = f"{self.API_URL}?t={table_code}&p={year}&c={territory_code}"
        
        try:
            response = self.session.get(url, timeout=30)
            if not self._validate_response(response):
                return None
            
            # El INE puede devolver datos en diferentes formatos
            # Aquí se asume formato HTML que requiere parsing
            # En producción, usar la API REST del INE cuando esté disponible
            logger.info(f"Datos INE obtenidos para año {year}")
            
            # Placeholder: En producción, parsear la respuesta real
            # Por ahora, retornar estructura vacía
            return pd.DataFrame({
                'territory_code': [territory_code],
                'year': [year],
                'population': [None],  # Se completará con datos reales
            })
            
        except Exception as e:
            logger.error(f"Error en petición INE: {e}")
            return None
    
    def download_ine_file(self, url: str, filename: str) -> Optional[Path]:
        """
        Descarga un archivo directamente del INE.
        
        Args:
            url: URL del archivo a descargar
            filename: Nombre del archivo de destino
            
        Returns:
            Path del archivo descargado o None
        """
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            if not self._validate_response(response):
                return None
            
            filepath = DATA_RAW_DIR / "ine" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Archivo INE descargado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error descargando archivo INE: {e}")
            return None

