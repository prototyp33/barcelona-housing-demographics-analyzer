"""
Extractor para datos de contaminación acústica (ruido) de Open Data BCN.

Fuentes:
- Mapas Estratégicos de Ruido (MER): Rásteres con niveles Ld, Ln, Lden
- Red de monitorización: Datos de sensores de ruido ambiental
- Datasets CSV agregados por barrio (si están disponibles)

URLs:
- Mapa de ruido: https://opendata-ajuntament.barcelona.cat/data/es/dataset/mapa-ruido
- Red monitorización: https://opendata-ajuntament.barcelona.cat/data/es/dataset/xarxasoroll-equipsmonitor-dades
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class RuidoExtractor(BaseExtractor):
    """
    Extractor para datos de contaminación acústica de Open Data BCN.
    
    Implementa múltiples estrategias:
    1. Búsqueda de datasets CSV agregados por barrio
    2. Descarga de rásteres del Mapa Estratégico de Ruido (requiere procesamiento GIS)
    3. Datos de sensores de la red de monitorización
    """
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    
    # IDs potenciales de datasets de ruido en Open Data BCN
    POTENTIAL_DATASET_IDS = [
        "mapa-ruido",
        "mapa-ruido-barcelona",
        "mapa-estrategic-soroll",
        "rasters-mapa-estrategic-soroll",
        "xarxasoroll-equipsmonitor-dades",
        "ruido",
        "soroll",
        "noise",
        "contaminacion-acustica",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de ruido.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 1.5).
            output_dir: Directorio donde guardar los datos descargados.
        """
        super().__init__("Ruido", rate_limit_delay, output_dir)
    
    def extract_mapas_ruido(self, anio: int) -> Tuple[Optional[Path], Dict]:
        """
        Extrae mapas ráster del Mapa Estratégico de Ruido para un año.
        
        Args:
            anio: Año del mapa estratégico (típicamente 2022 para el último disponible).
        
        Returns:
            Tupla con (ruta al archivo ráster descargado, metadata).
        """
        logger.info("=== Extrayendo Mapa Estratégico de Ruido ===")
        logger.info("Año: %s", anio)
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "opendata_bcn",
            "anio": anio,
            "file_path": None,
            "error": None,
        }
        
        try:
            from .opendata import OpenDataBCNExtractor
            
            opendata_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
            
            # Buscar datasets de mapas de ruido
            for dataset_id in self.POTENTIAL_DATASET_IDS:
                try:
                    logger.info("Intentando dataset: %s", dataset_id)
                    df, meta = opendata_extractor.extract_dataset(
                        dataset_id=dataset_id,
                        year_start=anio,
                        year_end=anio,
                    )
                    
                    if df is not None and not df.empty:
                        logger.info("✓ Dataset encontrado: %s", dataset_id)
                        metadata["dataset_id"] = dataset_id
                        metadata["success"] = True
                        # Guardar como CSV si es DataFrame
                        output_file = self.output_dir / f"ruido_mapa_{anio}.csv"
                        df.to_csv(output_file, index=False)
                        metadata["file_path"] = str(output_file)
                        return output_file, metadata
                    
                    # Si no es DataFrame, podría ser un recurso ráster
                    # Intentar descargar recursos del dataset
                    resources = opendata_extractor.get_dataset_resources_ckan(dataset_id)
                    if resources:
                        for resource in resources:
                            resource_format = resource.get("format", "").lower()
                            if resource_format in ["tif", "tiff", "geotiff", "raster"]:
                                logger.info("Encontrado recurso ráster: %s", resource.get("name"))
                                # Descargar ráster
                                resource_url = resource.get("url")
                                if resource_url:
                                    output_file = self.output_dir / f"ruido_mapa_{anio}.{resource_format}"
                                    self._download_file(resource_url, output_file)
                                    metadata["file_path"] = str(output_file)
                                    metadata["success"] = True
                                    metadata["resource_name"] = resource.get("name")
                                    return output_file, metadata
                
                except Exception as e:
                    logger.debug("Error intentando dataset %s: %s", dataset_id, e)
                    continue
            
            metadata["error"] = "No se encontraron mapas de ruido en Open Data BCN"
            return None, metadata
            
        except Exception as e:
            logger.warning("Error en extracción de mapas de ruido: %s", e)
            metadata["error"] = str(e)
            return None, metadata
    
    def extract_red_monitorizacion(
        self,
        anio: int,
        mes: Optional[int] = None
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Extrae datos de la red de monitorización de ruido ambiental.
        
        Args:
            anio: Año de los datos.
            mes: Mes opcional (si None, extrae todo el año).
        
        Returns:
            Tupla con (DataFrame con datos de sensores, metadata).
        """
        logger.info("=== Extrayendo datos de red de monitorización de ruido ===")
        logger.info("Año: %s, Mes: %s", anio, mes if mes else "todos")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "opendata_bcn",
            "anio": anio,
            "mes": mes,
            "error": None,
        }
        
        try:
            from .opendata import OpenDataBCNExtractor
            
            opendata_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
            
            # Buscar datasets de red de monitorización
            monitorizacion_datasets = [
                "xarxasoroll-equipsmonitor-dades",
                "red-monitorizacion-ruido",
                "sensors-ruido",
            ]
            
            for dataset_id in monitorizacion_datasets:
                try:
                    df, meta = opendata_extractor.extract_dataset(
                        dataset_id=dataset_id,
                        year_start=anio,
                        year_end=anio,
                    )
                    
                    if df is not None and not df.empty:
                        logger.info("✓ Dataset de monitorización encontrado: %s", dataset_id)
                        metadata["dataset_id"] = dataset_id
                        metadata["success"] = True
                        return df, metadata
                
                except Exception as e:
                    logger.debug("Error intentando dataset %s: %s", dataset_id, e)
                    continue
            
            metadata["error"] = "No se encontraron datos de red de monitorización"
            return None, metadata
            
        except Exception as e:
            logger.warning("Error en extracción de red de monitorización: %s", e)
            metadata["error"] = str(e)
            return None, metadata
    
    def extract_ruido_barrio(
        self,
        anio: int
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Extrae datos de ruido agregados por barrio para un año.
        
        Intenta múltiples métodos:
        1. Datasets CSV agregados por barrio
        2. Procesamiento de mapas ráster (si está disponible)
        3. Agregación de datos de sensores
        
        Args:
            anio: Año de los datos.
        
        Returns:
            Tupla con (DataFrame con datos por barrio, metadata).
        """
        logger.info("=== Extrayendo datos de ruido por barrio ===")
        logger.info("Año: %s", anio)
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "opendata_bcn",
            "anio": anio,
            "method_used": None,
            "error": None,
        }
        
        # Estrategia 1: Buscar datasets CSV agregados por barrio
        try:
            from .opendata import OpenDataBCNExtractor
            
            opendata_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
            
            # Buscar datasets que puedan tener datos agregados por barrio
            for dataset_id in self.POTENTIAL_DATASET_IDS:
                try:
                    df, meta = opendata_extractor.extract_dataset(
                        dataset_id=dataset_id,
                        year_start=anio,
                        year_end=anio,
                    )
                    
                    if df is not None and not df.empty:
                        # Verificar que tiene columnas de barrio
                        barrio_cols = ["barrio", "barri", "barrio_nombre", "codi_barri", "barrio_id"]
                        has_barrio = any(col.lower() in [c.lower() for c in df.columns] for col in barrio_cols)
                        
                        if has_barrio:
                            logger.info("✓ Dataset agregado por barrio encontrado: %s", dataset_id)
                            metadata["dataset_id"] = dataset_id
                            metadata["success"] = True
                            metadata["method_used"] = "csv_aggregated"
                            return df, metadata
                
                except Exception as e:
                    logger.debug("Error intentando dataset %s: %s", dataset_id, e)
                    continue
        
        except Exception as e:
            logger.warning("Error en búsqueda de datasets CSV: %s", e)
        
        # Estrategia 2: Buscar archivos CSV manuales
        logger.info("Buscando archivos CSV manuales...")
        df_manual, meta_manual = self._try_load_manual_csv(anio)
        
        if df_manual is not None and not df_manual.empty:
            logger.info("✓ Datos obtenidos desde archivos CSV manuales")
            metadata.update(meta_manual)
            metadata["success"] = True
            metadata["method_used"] = "manual_csv"
            return df_manual, metadata
        
        metadata["error"] = "No se encontraron datos de ruido por ningún método"
        return None, metadata
    
    def _try_load_manual_csv(self, anio: int) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Busca y carga archivos CSV manuales preparados externamente.
        
        Args:
            anio: Año de los datos.
        
        Returns:
            Tupla con (DataFrame, metadata).
        """
        metadata = {"method": "manual_csv", "files_found": []}
        
        # Buscar en varios directorios posibles
        search_paths = [
            self.output_dir / "ruido",
            self.output_dir.parent / "ruido",
            Path("data/raw/ruido"),
        ]
        
        frames = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # Buscar archivos CSV relacionados con ruido
            csv_files = list(search_path.glob(f"*ruido*{anio}*.csv"))
            csv_files.extend(list(search_path.glob(f"*soroll*{anio}*.csv")))
            csv_files.extend(list(search_path.glob(f"*noise*{anio}*.csv")))
            csv_files.extend(list(search_path.glob("ruido_*.csv")))
            
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
    
    def _download_file(self, url: str, output_path: Path) -> None:
        """
        Descarga un archivo desde una URL.
        
        Args:
            url: URL del archivo a descargar.
            output_path: Ruta donde guardar el archivo.
        """
        self._rate_limit()
        response = self.session.get(url, stream=True, timeout=60)
        
        if self._validate_response(response):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("✓ Archivo descargado: %s", output_path)

