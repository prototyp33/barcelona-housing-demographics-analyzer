"""
Base Extractor Module - Funcionalidades comunes para todos los extractores.

Este módulo proporciona:
- BaseExtractor: Clase base con métodos comunes (rate limiting, sesiones HTTP, guardado)
- Configuración de logging
- Constantes de directorio
"""

import json
import logging
import logging.handlers
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de directorios
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
LOGS_DIR = BASE_DIR / "logs"
EXTRACTION_LOGS_DIR = BASE_DIR / "data" / "logs"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTION_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de validación
MIN_RECORDS_WARNING = 10  # Número mínimo de registros para considerar datos válidos


def setup_logging(log_to_file: bool = True, log_level: int = logging.INFO):
    """
    Configura el sistema de logging con handlers para consola y archivo.
    
    Args:
        log_to_file: Si True, guarda logs en archivo
        log_level: Nivel de logging (logging.INFO, logging.DEBUG, etc.)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    # Evitar duplicar handlers si ya están configurados
    if logger.handlers:
        return logger
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (rotación diaria)
    if log_to_file:
        log_file = LOGS_DIR / f"data_extraction_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30,  # Mantener 30 días de logs
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Inicializar logging
logger = setup_logging()


class BaseExtractor:
    """Clase base para extractores de datos con funcionalidades comunes."""
    
    def __init__(
        self,
        source_name: str,
        rate_limit_delay: float = 1.0,
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor base.
        
        Args:
            source_name: Nombre de la fuente de datos
            rate_limit_delay: Tiempo de espera entre peticiones (segundos)
            output_dir: Directorio donde guardar los datos (None = usar default)
        """
        self.source_name = source_name
        self.rate_limit_delay = rate_limit_delay
        self.output_dir = output_dir or DATA_RAW_DIR
        self.session = self._create_session()
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """Crea una sesión HTTP con retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _rate_limit(self):
        """Implementa rate limiting entre peticiones."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _save_raw_data(
        self,
        data: Any,
        filename: str,
        format: str = 'json',
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        data_type: Optional[str] = None
    ) -> Path:
        """
        Guarda datos raw en el directorio correspondiente con timestamp único.
        
        También registra el archivo en manifest.json para facilitar el descubrimiento
        de archivos durante el ETL (evita depender de patrones de nombre de archivo).
        
        Args:
            data: Datos a guardar
            filename: Nombre del archivo (sin extensión)
            format: Formato de guardado ('json', 'csv', 'xlsx')
            year_start: Año inicial (para incluir en nombre de archivo)
            year_end: Año final (para incluir en nombre de archivo)
            data_type: Tipo de datos (ej. 'demographics', 'prices_venta', 'geojson')
                       para clasificación en el manifest
            
        Returns:
            Path del archivo guardado
        """
        source_dir = self.output_dir / self.source_name.lower().replace(' ', '_')
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp único: fecha, hora y microsegundos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Construir nombre de archivo con años si están disponibles
        if year_start and year_end:
            year_range = f"{year_start}_{year_end}"
            filepath = source_dir / f"{filename}_{year_range}_{timestamp}.{format}"
        else:
            filepath = source_dir / f"{filename}_{timestamp}.{format}"
        
        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            elif format == 'csv':
                if isinstance(data, pd.DataFrame):
                    data.to_csv(filepath, index=False, encoding='utf-8')
                else:
                    raise ValueError("Para formato CSV, data debe ser un DataFrame")
            elif format == 'xlsx':
                if isinstance(data, pd.DataFrame):
                    data.to_excel(filepath, index=False)
                else:
                    raise ValueError("Para formato XLSX, data debe ser un DataFrame")
            
            logger.info(f"Datos guardados en: {filepath}")
            
            # Registrar en manifest.json
            self._append_to_manifest(
                file_path=filepath,
                source=self.source_name.lower().replace(' ', '_'),
                data_type=data_type or self._infer_data_type(filename),
                year_start=year_start,
                year_end=year_end,
            )
            
            return filepath
        except Exception as e:
            logger.error(f"Error guardando datos en {filepath}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _append_to_manifest(
        self,
        file_path: Path,
        source: str,
        data_type: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
    ) -> None:
        """
        Registra un archivo en el manifest.json centralizado.
        
        Args:
            file_path: Ruta completa del archivo guardado
            source: Nombre de la fuente (ej. 'opendatabcn', 'portaldades')
            data_type: Tipo de datos (ej. 'demographics', 'prices_venta')
            year_start: Año inicial de los datos
            year_end: Año final de los datos
        """
        manifest_path = self.output_dir / "manifest.json"
        
        # Cargar manifest existente o crear nuevo
        manifest: List[Dict[str, Any]] = []
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error leyendo manifest existente, creando nuevo: {e}")
                manifest = []
        
        # Crear entrada para el nuevo archivo
        entry = {
            "file_path": str(file_path.relative_to(self.output_dir)),
            "source": source,
            "type": data_type,
            "timestamp": datetime.now().isoformat(),
            "year_start": year_start,
            "year_end": year_end,
        }
        
        manifest.append(entry)
        
        # Guardar manifest actualizado
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            logger.debug(f"Manifest actualizado: {entry['file_path']}")
        except Exception as e:
            logger.warning(f"Error actualizando manifest: {e}")
    
    @staticmethod
    def _infer_data_type(filename: str) -> str:
        """
        Infiere el tipo de datos basándose en el nombre del archivo.
        
        Args:
            filename: Nombre del archivo (sin extensión)
            
        Returns:
            Tipo de datos inferido
        """
        filename_lower = filename.lower()
        
        # Mapeo de patrones a tipos
        type_patterns = {
            "demographics": ["demographic", "poblacion", "pad_mdb", "pad_mdbas"],
            "demographics_ampliada": ["lloc-naix", "edat-q", "nacionalitat"],
            "prices_venta": ["venta", "compravenda", "habitatges"],
            "prices_alquiler": ["alquiler", "lloguer", "rent"],
            "renta": ["renta", "renda", "income"],
            "geojson": ["geojson", "geometry", "barrios_geojson"],
            "idealista_sale": ["idealista", "sale"],
            "idealista_rent": ["idealista", "rent"],
        }
        
        for data_type, patterns in type_patterns.items():
            if any(pattern in filename_lower for pattern in patterns):
                return data_type
        
        return "unknown"
    
    def _validate_response(self, response: requests.Response) -> bool:
        """Valida la respuesta HTTP."""
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            logger.warning("Rate limit alcanzado. Esperando...")
            time.sleep(60)
            return False
        else:
            logger.error(f"Error HTTP {response.status_code}: {response.text}")
            return False

