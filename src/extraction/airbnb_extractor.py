"""
Extractor para datos de Inside Airbnb.

Fuente: http://insideairbnb.com/get-the-data/
URLs públicas en S3: http://data.insideairbnb.com/spain/catalonia/barcelona/YYYY-MM-DD/data/
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class AirbnbExtractor(BaseExtractor):
    """
    Extractor para datos de Inside Airbnb.
    
    Descarga datos públicos de Inside Airbnb desde su repositorio S3.
    Los datos están disponibles en formato CSV comprimido (.csv.gz).
    
    URL base: http://data.insideairbnb.com/spain/catalonia/barcelona/YYYY-MM-DD/data/
    """
    
    BASE_URL = "http://data.insideairbnb.com"
    BARCELONA_PATH = "/spain/catalonia/barcelona"
    
    # Tipos de archivos disponibles
    FILE_TYPES = {
        "listings": "listings.csv.gz",
        "calendar": "calendar.csv.gz",
        "reviews": "reviews.csv.gz",
    }
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de Inside Airbnb.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 2.0).
            output_dir: Directorio donde guardar los archivos descargados.
        """
        super().__init__("InsideAirbnb", rate_limit_delay, output_dir)
    
    def find_latest_data_date(self) -> Optional[str]:
        """
        Busca la fecha más reciente de datos disponibles para Barcelona.
        
        Returns:
            Fecha en formato 'YYYY-MM-DD' o None si no se encuentra.
        """
        # Por ahora, retornamos una fecha conocida
        # En producción, esto podría hacer scraping de la página de Inside Airbnb
        # o usar una API si está disponible
        return "2025-09-14"  # Última fecha conocida (actualizar según necesidad)
    
    def extract_barcelona_data(
        self,
        fecha: Optional[str] = None,
        file_types: Optional[list] = None
    ) -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict]:
        """
        Extrae datos de Inside Airbnb para Barcelona.
        
        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'. Si None, usa la más reciente disponible.
            file_types: Lista de tipos de archivo a descargar.
                      Opciones: 'listings', 'calendar', 'reviews'.
                      Si None, descarga todos.
        
        Returns:
            Tupla con (dict de DataFrames, metadata).
        """
        logger.info("=== Extrayendo datos de Inside Airbnb para Barcelona ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "insideairbnb",
            "files_downloaded": [],
            "files_failed": [],
        }
        
        if fecha is None:
            fecha = self.find_latest_data_date()
            if fecha is None:
                metadata["error"] = "No se pudo determinar la fecha de datos más reciente"
                return {}, metadata
        
        if file_types is None:
            file_types = list(self.FILE_TYPES.keys())
        
        results = {}
        base_url = f"{self.BASE_URL}{self.BARCELONA_PATH}/{fecha}/data"
        
        # Crear directorio de destino
        source_dir = self.output_dir / self.source_name.lower().replace(" ", "_")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Descargar cada tipo de archivo
        for file_type in file_types:
            if file_type not in self.FILE_TYPES:
                logger.warning(f"Tipo de archivo desconocido: {file_type}")
                results[file_type] = None
                metadata["files_failed"].append(file_type)
                continue
            
            filename = self.FILE_TYPES[file_type]
            url = f"{base_url}/{filename}"
            
            logger.info(f"\n--- Descargando {file_type} ---")
            logger.info(f"URL: {url}")
            
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=120, stream=True)
                
                if not self._validate_response(response):
                    logger.error(f"Error descargando {file_type}: HTTP {response.status_code}")
                    results[file_type] = None
                    metadata["files_failed"].append(file_type)
                    continue
                
                # Guardar archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = source_dir / f"insideairbnb_{file_type}_{timestamp}.csv.gz"
                
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Descomprimir y leer CSV
                import gzip
                import io
                with gzip.open(filepath, "rb") as f:
                    df = pd.read_csv(io.BytesIO(f.read()), low_memory=False)
                
                logger.info(f"Datos guardados en: {filepath}")
                logger.info(f"✓ {file_type} descargado: {len(df)} registros, {len(df.columns)} columnas")
                
                results[file_type] = df
                metadata["files_downloaded"].append(file_type)
                metadata[f"{file_type}_records"] = len(df)
                metadata[f"{file_type}_columns"] = list(df.columns)
                
            except Exception as e:
                logger.error(f"Error descargando {file_type}: {e}")
                results[file_type] = None
                metadata["files_failed"].append(file_type)
                metadata[f"{file_type}_error"] = str(e)
        
        metadata["success"] = len(metadata["files_downloaded"]) > 0
        
        return results, metadata

