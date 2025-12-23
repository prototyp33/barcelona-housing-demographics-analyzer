"""
Extractor para datos de criminalidad del ICGC (Institut Català de Gestió Criminal).

Fuentes posibles:
1. ICGC Mapa Delincuencial (scraping de visor web)
2. Open Data BCN (si hay datasets de seguridad)
3. Datos manuales (CSV preparados externamente)

URL: http://www.icgc.cat/es/Herramientas-y-visores/Visores/Mapa-delincuencial
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class ICGCExtractor(BaseExtractor):
    """
    Extractor para datos de criminalidad del ICGC.
    
    El ICGC no proporciona una API pública directa, por lo que este extractor
    implementa múltiples estrategias de obtención de datos:
    
    1. Scraping del visor web del Mapa Delincuencial
    2. Búsqueda en Open Data BCN por datasets de seguridad
    3. Carga de archivos CSV manuales preparados externamente
    """
    
    BASE_URL = "http://www.icgc.cat"
    MAPA_DELINCUENCIAL_URL = f"{BASE_URL}/es/Herramientas-y-visores/Visores/Mapa-delincuencial"
    
    # URLs alternativas de Open Data BCN para datos de seguridad
    OPENDATA_BCN_BASE = "https://opendata-ajuntament.barcelona.cat"
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de ICGC.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 2.0).
            output_dir: Directorio donde guardar los datos descargados.
        """
        super().__init__("ICGC", rate_limit_delay, output_dir)
    
    def extract_criminalidad_barrio(
        self,
        anio_inicio: int,
        anio_fin: int
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Extrae datos de criminalidad por barrio para el rango de años especificado.
        
        Args:
            anio_inicio: Año inicial del rango.
            anio_fin: Año final del rango.
        
        Returns:
            Tupla con (DataFrame con datos de criminalidad, metadata).
        """
        logger.info(
            "=== Extrayendo datos de criminalidad ICGC para Barcelona ==="
        )
        logger.info("Rango de años: %s-%s", anio_inicio, anio_fin)
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "icgc",
            "anio_inicio": anio_inicio,
            "anio_fin": anio_fin,
            "method_used": None,
            "files_downloaded": [],
            "files_failed": [],
        }
        
        # Estrategia 1: Buscar datos en Open Data BCN
        logger.info("Intentando extraer desde Open Data BCN...")
        df_opendata, meta_opendata = self._try_opendata_bcn(anio_inicio, anio_fin)
        
        if df_opendata is not None and not df_opendata.empty:
            logger.info("✓ Datos obtenidos desde Open Data BCN")
            metadata.update(meta_opendata)
            metadata["success"] = True
            metadata["method_used"] = "opendata_bcn"
            return df_opendata, metadata
        
        # Estrategia 2: Intentar scraping del visor ICGC
        logger.info("Intentando scraping del visor ICGC...")
        df_scraping, meta_scraping = self._try_scraping_icgc(anio_inicio, anio_fin)
        
        if df_scraping is not None and not df_scraping.empty:
            logger.info("✓ Datos obtenidos mediante scraping del visor ICGC")
            metadata.update(meta_scraping)
            metadata["success"] = True
            metadata["method_used"] = "scraping_icgc"
            return df_scraping, metadata
        
        # Estrategia 3: Buscar archivos CSV manuales
        logger.info("Buscando archivos CSV manuales...")
        df_manual, meta_manual = self._try_load_manual_csv(anio_inicio, anio_fin)
        
        if df_manual is not None and not df_manual.empty:
            logger.info("✓ Datos obtenidos desde archivos CSV manuales")
            metadata.update(meta_manual)
            metadata["success"] = True
            metadata["method_used"] = "manual_csv"
            return df_manual, metadata
        
        # Si ninguna estrategia funcionó
        logger.warning(
            "No se pudieron obtener datos de criminalidad. "
            "Considera preparar archivos CSV manuales en data/raw/icgc/"
        )
        metadata["error"] = "No se encontraron datos de criminalidad por ningún método"
        return None, metadata
    
    def _try_opendata_bcn(
        self,
        anio_inicio: int,
        anio_fin: int
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Intenta obtener datos de criminalidad desde Open Data BCN.
        
        Returns:
            Tupla con (DataFrame, metadata).
        """
        metadata = {"method": "opendata_bcn", "error": None}
        
        try:
            from .opendata import OpenDataBCNExtractor
            
            opendata_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
            
            # Buscar datasets relacionados con seguridad/criminalidad
            # Nota: Estos IDs deben verificarse en Open Data BCN
            potential_datasets = [
                "seguretat-ciutadana",
                "delictes",
                "criminalitat",
                "seguretat",
            ]
            
            for dataset_id in potential_datasets:
                try:
                    df, meta = opendata_extractor.extract_dataset(
                        dataset_id=dataset_id,
                        year_start=anio_inicio,
                        year_end=anio_fin,
                    )
                    
                    if df is not None and not df.empty:
                        # Verificar que tiene columnas relevantes
                        if any(
                            col.lower() in ["delito", "delictes", "barrio", "barri", "codi_barri"]
                            for col in df.columns
                        ):
                            logger.info("Dataset encontrado: %s", dataset_id)
                            metadata["dataset_id"] = dataset_id
                            return df, metadata
                except Exception as e:
                    logger.debug("Error intentando dataset %s: %s", dataset_id, e)
                    continue
            
            metadata["error"] = "No se encontraron datasets de seguridad en Open Data BCN"
            return None, metadata
            
        except Exception as e:
            logger.warning("Error en extracción desde Open Data BCN: %s", e)
            metadata["error"] = str(e)
            return None, metadata
    
    def _try_scraping_icgc(
        self,
        anio_inicio: int,
        anio_fin: int
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Intenta hacer scraping del visor web del ICGC.
        
        Nota: Esta implementación es un placeholder. El scraping real requeriría
        analizar la estructura HTML/JavaScript del visor y puede requerir Selenium
        o Playwright para interactuar con elementos dinámicos.
        
        Returns:
            Tupla con (DataFrame, metadata).
        """
        metadata = {"method": "scraping_icgc", "error": None}
        
        try:
            self._rate_limit()
            response = self.session.get(self.MAPA_DELINCUENCIAL_URL, timeout=30)
            
            if not self._validate_response(response):
                metadata["error"] = f"HTTP {response.status_code}"
                return None, metadata
            
            # Por ahora, retornamos None ya que el scraping requiere análisis
            # detallado del visor web y posiblemente herramientas como Selenium
            logger.info(
                "Scraping del visor ICGC no implementado completamente. "
                "Requiere análisis de la estructura del visor web."
            )
            metadata["error"] = "Scraping no implementado (requiere análisis del visor)"
            return None, metadata
            
        except Exception as e:
            logger.warning("Error en scraping del visor ICGC: %s", e)
            metadata["error"] = str(e)
            return None, metadata
    
    def _try_load_manual_csv(
        self,
        anio_inicio: int,
        anio_fin: int
        ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Busca y carga archivos CSV manuales preparados externamente.
        
        Busca archivos en data/raw/icgc/ con patrones como:
        - icgc_criminalidad_*.csv
        - icgc_delitos_*.csv
        - seguridad_*.csv
        
        Returns:
            Tupla con (DataFrame, metadata).
        """
        metadata = {"method": "manual_csv", "files_found": []}
        
        # Buscar en varios directorios posibles
        search_paths = [
            self.output_dir / "icgc",
            self.output_dir.parent / "icgc",
            Path("data/raw/icgc"),
        ]
        
        frames = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # Buscar archivos CSV relacionados con criminalidad
            csv_files = list(search_path.glob("*criminalidad*.csv"))
            csv_files.extend(list(search_path.glob("*delitos*.csv")))
            csv_files.extend(list(search_path.glob("*seguridad*.csv")))
            csv_files.extend(list(search_path.glob("icgc_*.csv")))
            
            for csv_file in csv_files:
                try:
                    logger.info("Cargando archivo CSV manual: %s", csv_file)
                    df = pd.read_csv(csv_file, low_memory=False)
                    
                    # Verificar que tiene columnas relevantes
                    required_cols = ["barrio", "barrio_id", "codi_barri", "anio", "any"]
                    has_relevant_cols = any(
                        col.lower() in [c.lower() for c in df.columns]
                        for col in required_cols
                    )
                    
                    if has_relevant_cols:
                        frames.append(df)
                        metadata["files_found"].append(str(csv_file))
                        logger.info("✓ Archivo CSV cargado: %s (%s registros)", csv_file, len(df))
                    
                except Exception as e:
                    logger.warning("Error leyendo CSV %s: %s", csv_file, e)
                    continue
        
        if frames:
            df_combined = pd.concat(frames, ignore_index=True)
            logger.info("Total registros cargados desde CSVs manuales: %s", len(df_combined))
            return df_combined, metadata
        
        metadata["error"] = "No se encontraron archivos CSV manuales"
        return None, metadata

