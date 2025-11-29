"""
Data Extraction Module (INE, BCN, Idealista)

Este módulo proporciona funciones para extraer datos de múltiples fuentes públicas:
- INE (Instituto Nacional de Estadística): Datos demográficos oficiales
- Open Data BCN: Datos abiertos del Ayuntamiento de Barcelona
- Idealista: Precios de vivienda (con prácticas éticas)
"""

import os
import io
import json
import logging
import logging.handlers
import re
import time
import traceback
import unicodedata
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse

import chardet
import pandas as pd
import requests
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Playwright import (opcional, solo si está disponible)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Logger aún no está inicializado aquí, así que usamos print
    import sys
    if sys.stderr:
        print("WARNING: Playwright no está instalado. El extractor PortalDades requerirá: pip install playwright && playwright install", file=sys.stderr)

# Configuración de directorios
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
LOGS_DIR = BASE_DIR / "logs"
EXTRACTION_LOGS_DIR = BASE_DIR / "data" / "logs"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTION_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de validación
MIN_RECORDS_WARNING = 10  # Número mínimo de registros para considerar datos válidos

# Configuración de logging con archivo
def setup_logging(log_to_file: bool = True, log_level: int = logging.INFO):
    """
    Configura el sistema de logging con handlers para consola y archivo.
    
    Args:
        log_to_file: Si True, guarda logs en archivo
        log_level: Nivel de logging (logging.INFO, logging.DEBUG, etc.)
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
    
    def __init__(self, source_name: str, rate_limit_delay: float = 1.0, output_dir: Optional[Path] = None):
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
        year_end: Optional[int] = None
    ) -> Path:
        """
        Guarda datos raw en el directorio correspondiente con timestamp único.
        
        Args:
            data: Datos a guardar
            filename: Nombre del archivo (sin extensión)
            format: Formato de guardado ('json', 'csv', 'xlsx')
            year_start: Año inicial (para incluir en nombre de archivo)
            year_end: Año final (para incluir en nombre de archivo)
            
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
            return filepath
        except Exception as e:
            logger.error(f"Error guardando datos en {filepath}: {e}")
            logger.error(traceback.format_exc())
            raise
    
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
                year_end=year_end
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


class OpenDataBCNExtractor(BaseExtractor):
    """Extractor para datos de Open Data Barcelona."""
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    API_URL = f"{BASE_URL}/data/api/3/action"
    
    # IDs de datasets CKAN identificados y confirmados
    DATASETS = {
        "demographics": "pad_mdbas_sexe",  # Población por sexo y barrio
        "demographics_age": "est-padro-edat-any-a-any",  # Población por edad
        "housing_venta": "habitatges-2na-ma",  # Precios de venta (confirmado)
        "housing_alquiler": "est-mercat-immobiliari-lloguer-mitja-mensual",  # Precios de alquiler
        # Mantener IDs antiguos para compatibilidad
        "demographics_old": "demografia-per-barris",
        "housing_old": "habitatge-per-barris",
        "population": "poblacio-per-barris",
        "prices": "preus-habitatge"
    }
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """Inicializa el extractor de Open Data BCN."""
        super().__init__("OpenDataBCN", rate_limit_delay, output_dir)
    
    def get_dataset_list(self) -> List[Dict]:
        """Obtiene la lista de datasets disponibles."""
        self._rate_limit()
        
        url = f"{self.API_URL}/package_list"
        try:
            response = self.session.get(url, timeout=30)
            if self._validate_response(response):
                data = response.json()
                return data.get('result', [])
        except Exception as e:
            logger.error(f"Error obteniendo lista de datasets: {e}")
        return []
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict]:
        """
        Obtiene información de un dataset específico.
        
        Args:
            dataset_id: ID del dataset
            
        Returns:
            Diccionario con información del dataset o None
        """
        self._rate_limit()
        
        url = f"{self.API_URL}/package_show"
        params = {"id": dataset_id}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if self._validate_response(response):
                data = response.json()
                return data.get('result')
        except Exception as e:
            logger.error(f"Error obteniendo info del dataset {dataset_id}: {e}")
        return None
    
    def download_dataset(
        self,
        dataset_id: str,
        resource_format: str = 'csv',
        year_start: Optional[int] = None,
        year_end: Optional[int] = None
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Descarga un dataset de Open Data BCN.
        
        Args:
            dataset_id: ID del dataset
            resource_format: Formato preferido ('csv', 'json', 'xlsx')
            year_start: Año inicial para filtrar (opcional)
            year_end: Año final para filtrar (opcional)
            
        Returns:
            Tupla con (DataFrame con los datos o None, metadata de cobertura)
        """
        logger.info(f"Descargando dataset Open Data BCN: {dataset_id}")
        
        coverage_metadata = {
            "dataset_id": dataset_id,
            "requested_range": {"start": year_start, "end": year_end},
            "success": False
        }
        
        try:
            dataset_info = self.get_dataset_info(dataset_id)
            if not dataset_info:
                logger.error(f"Dataset {dataset_id} no encontrado")
                coverage_metadata["error"] = "Dataset no encontrado"
                return None, coverage_metadata
            
            resources = dataset_info.get('resources', [])
            
            # Buscar recurso en el formato preferido
            resource = None
            for r in resources:
                if resource_format.lower() in r.get('format', '').lower():
                    resource = r
                    break
            
            if not resource and resources:
                resource = resources[0]  # Usar el primer recurso disponible
            
            if not resource:
                logger.error(f"No se encontraron recursos para {dataset_id}")
                coverage_metadata["error"] = "No se encontraron recursos"
                return None, coverage_metadata
            
            download_url = resource.get('url')
            if not download_url:
                logger.error(f"URL de descarga no disponible para {dataset_id}")
                coverage_metadata["error"] = "URL no disponible"
                return None, coverage_metadata
            
            self._rate_limit()
            
            # Descargar datos
            response = self.session.get(download_url, timeout=60)
            if not self._validate_response(response):
                coverage_metadata["error"] = "Error en respuesta HTTP"
                return None, coverage_metadata
            
            # Parsear según formato
            format_type = resource.get('format', '').lower()
            
            if 'csv' in format_type:
                df = pd.read_csv(io.StringIO(response.text), encoding='utf-8')
            elif 'json' in format_type:
                df = pd.json_normalize(response.json())
            elif 'xlsx' in format_type or 'excel' in format_type:
                df = pd.read_excel(io.BytesIO(response.content))
            else:
                logger.warning(f"Formato {format_type} no soportado, intentando CSV")
                df = pd.read_csv(io.StringIO(response.text), encoding='utf-8')
            
            # Filtrar por años si se especifica
            original_count = len(df)
            if year_start or year_end:
                df = self._filter_by_year(df, year_start, year_end)
            
            # Analizar cobertura temporal
            year_cols = [col for col in df.columns if 'any' in col.lower() or 'year' in col.lower() or 'año' in col.lower()]
            if year_cols:
                year_col = year_cols[0]
                available_years = sorted(df[year_col].dropna().unique().astype(int).tolist())
                coverage_metadata["available_years"] = available_years
                if year_start and year_end:
                    requested_years = set(range(year_start, year_end + 1))
                    available_years_set = set(available_years)
                    missing_years = sorted(list(requested_years - available_years_set))
                    coverage_metadata["missing_years"] = missing_years
                    coverage_metadata["coverage_percentage"] = len(available_years_set & requested_years) / len(requested_years) * 100
            
            # Guardar datos raw
            self._save_raw_data(
                df,
                f"opendatabcn_{dataset_id}",
                'csv',
                year_start=year_start,
                year_end=year_end
            )
            
            coverage_metadata["success"] = True
            coverage_metadata["records_before_filter"] = original_count
            coverage_metadata["records_after_filter"] = len(df)
            
            logger.info(f"Dataset {dataset_id} descargado: {len(df)} registros")
            return df, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error descargando dataset {dataset_id}: {e}")
            logger.debug(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def _filter_by_year(
        self,
        df: pd.DataFrame,
        year_start: Optional[int],
        year_end: Optional[int]
    ) -> pd.DataFrame:
        """Filtra DataFrame por rango de años."""
        # Intentar identificar columna de año
        year_cols = [col for col in df.columns if 'any' in col.lower() or 'year' in col.lower() or 'año' in col.lower()]
        
        if not year_cols:
            logger.warning("No se encontró columna de año para filtrar")
            return df
        
        year_col = year_cols[0]
        
        if year_start:
            df = df[df[year_col] >= year_start]
        if year_end:
            df = df[df[year_col] <= year_end]
        
        return df
    
    def get_demographics_by_neighborhood(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Obtiene datos demográficos por barrio usando API CKAN con IDs correctos.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata de cobertura)
        """
        # Usar el nuevo método con IDs correctos
        return self.extract_demographics_ckan(year_start, year_end)
    
    def get_housing_data_by_neighborhood(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Obtiene datos de vivienda por barrio (método legacy)."""
        return self.download_dataset(
            self.DATASETS.get("housing_old", "habitatge-per-barris"),
            year_start=year_start,
            year_end=year_end
        )
    
    def get_dataset_resources_ckan(self, dataset_id: str) -> Dict[str, str]:
        """
        Obtiene todos los recursos (archivos) de un dataset usando API CKAN.
        
        Args:
            dataset_id: ID del dataset en CKAN
        
        Returns:
            Diccionario con {año: url_descarga} o {nombre: url}
        """
        logger.info(f"Obteniendo recursos del dataset: {dataset_id}")
        
        self._rate_limit()
        
        url = f"{self.API_URL}/package_show"
        params = {"id": dataset_id}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # Manejar error 404 específicamente
            if response.status_code == 404:
                logger.warning(f"Dataset '{dataset_id}' no encontrado (404). Puede que el ID haya cambiado o el dataset no exista.")
                return {}
            
            if not self._validate_response(response):
                return {}
            
            data = response.json()
            
            if not data.get('success'):
                error_msg = data.get('error', {}).get('message', 'Error desconocido')
                logger.error(f"API CKAN devolvió error para {dataset_id}: {error_msg}")
                return {}
            
            resources = {}
            for resource in data['result'].get('resources', []):
                # Solo archivos CSV
                if resource.get('format', '').lower() in ['csv', 'text/csv']:
                    name = resource.get('name', '')
                    url_resource = resource.get('url', '')
                    
                    if not url_resource:
                        continue
                    
                    # Intentar extraer año del nombre
                    year_match = re.search(r'(\d{4})', name)
                    
                    if year_match:
                        year = int(year_match.group(1))
                        resources[year] = url_resource
                    else:
                        # Si no hay año, usar nombre completo
                        resources[name] = url_resource
            
            logger.info(f"✓ {len(resources)} recursos CSV encontrados para {dataset_id}")
            return resources
            
        except Exception as e:
            logger.error(f"Error obteniendo recursos de {dataset_id}: {e}")
            logger.debug(traceback.format_exc())
            return {}
    
    def search_datasets_by_keyword(self, keyword: str) -> List[str]:
        """
        Busca datasets en Open Data BCN por palabra clave.
        
        Args:
            keyword: Palabra clave para buscar (ej: "alquiler", "lloguer", "vivienda")
            
        Returns:
            Lista de IDs de datasets encontrados
        """
        logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
        
        all_datasets = self.get_dataset_list()
        matching_datasets = []
        
        for dataset_id in all_datasets:
            try:
                info = self.get_dataset_info(dataset_id)
                if info:
                    title = info.get('title', '').lower()
                    description = info.get('notes', '').lower()
                    tags = [tag.get('name', '').lower() for tag in info.get('tags', [])]
                    
                    if (keyword.lower() in title or 
                        keyword.lower() in description or 
                        keyword.lower() in ' '.join(tags)):
                        matching_datasets.append(dataset_id)
                        logger.info(f"  Encontrado: {dataset_id} - {info.get('title', 'Sin título')}")
            except Exception as e:
                logger.debug(f"Error obteniendo info de {dataset_id}: {e}")
                continue
        
        return matching_datasets
    
    def download_and_parse_csv(
        self,
        url: str,
        encoding: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Descarga y parsea un archivo CSV detectando encoding automáticamente.
        
        Args:
            url: URL del CSV
            encoding: Encoding inicial (se detectará automáticamente si es None)
        
        Returns:
            DataFrame con los datos
        """
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=60)
            if not self._validate_response(response):
                return pd.DataFrame()
            
            raw_data = response.content
            
            # Detectar encoding si no se especifica
            if encoding is None:
                detected = chardet.detect(raw_data)
                encoding = detected.get('encoding', 'utf-8')
                logger.debug(f"Encoding detectado: {encoding} (confianza: {detected.get('confidence', 0):.2f})")
            
            # Intentar leer CSV
            try:
                df = pd.read_csv(io.BytesIO(raw_data), encoding=encoding)
            except UnicodeDecodeError:
                # Si falla, intentar con otros encodings comunes
                for enc in ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']:
                    try:
                        df = pd.read_csv(io.BytesIO(raw_data), encoding=enc)
                        logger.info(f"CSV leído con encoding: {enc}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise
            
            return df
            
        except Exception as e:
            logger.error(f"Error descargando/parseando CSV desde {url}: {e}")
            logger.debug(traceback.format_exc())
            return pd.DataFrame()
    
    def extract_housing_venta(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrae datos de PRECIO DE VENTA usando API CKAN.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata de cobertura)
        """
        logger.info(f"Extrayendo precios de VENTA ({year_start}-{year_end})")
        
        dataset_id = self.DATASETS["housing_venta"]
        resources = self.get_dataset_resources_ckan(dataset_id)
        
        coverage_metadata = {
            "dataset_id": dataset_id,
            "requested_range": {"start": year_start, "end": year_end},
            "years_extracted": [],
            "years_failed": [],
            "success": False
        }
        
        if not resources:
            logger.warning("No se encontraron recursos de venta")
            coverage_metadata["error"] = "No se encontraron recursos"
            return pd.DataFrame(), coverage_metadata
        
        all_data = []
        
        for identifier, url in resources.items():
            # Si identifier es un año (int)
            if isinstance(identifier, int):
                year = identifier
                if year_start <= year <= year_end:
                    logger.info(f"Descargando año {year}...")
                    
                    df = self.download_and_parse_csv(url)
                    
                    if not df.empty:
                        logger.info(f"✓ Año {year}: {len(df)} registros")
                        logger.debug(f"  Columnas: {list(df.columns)}")
                        
                        df['año'] = year
                        df['tipo_operacion'] = 'venta'
                        df['source'] = 'opendatabcn_idealista'
                        
                        all_data.append(df)
                        coverage_metadata["years_extracted"].append(year)
                    else:
                        logger.warning(f"✗ Año {year}: DataFrame vacío")
                        coverage_metadata["years_failed"].append(year)
            else:
                # Si es un nombre, intentar descargar y filtrar por años
                logger.info(f"Descargando recurso: {identifier}...")
                df = self.download_and_parse_csv(url)
                
                if not df.empty:
                    # Buscar columna de año
                    year_cols = [col for col in df.columns if any(x in col.lower() for x in ['any', 'año', 'year'])]
                    if year_cols:
                        year_col = year_cols[0]
                        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
                        df = df[(df[year_col] >= year_start) & (df[year_col] <= year_end)]
                        
                        if not df.empty:
                            df['tipo_operacion'] = 'venta'
                            df['source'] = 'opendatabcn_idealista'
                            all_data.append(df)
                            logger.info(f"✓ {identifier}: {len(df)} registros")
        
        if not all_data:
            coverage_metadata["error"] = "No se obtuvieron datos"
            return pd.DataFrame(), coverage_metadata
        
        df_combined = pd.concat(all_data, ignore_index=True)
        coverage_metadata["success"] = True
        coverage_metadata["records"] = len(df_combined)
        coverage_metadata["coverage_percentage"] = (
            len(coverage_metadata["years_extracted"]) / (year_end - year_start + 1) * 100
            if year_end >= year_start else 0
        )
        
        logger.info(f"✅ Total registros venta: {len(df_combined)}")
        
        # Guardar datos
        self._save_raw_data(
            df_combined,
            "opendatabcn_venta",
            'csv',
            year_start=year_start,
            year_end=year_end
        )
        
        return df_combined, coverage_metadata
    
    def extract_housing_alquiler(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrae datos de PRECIO DE ALQUILER usando API CKAN.
        
        Intenta múltiples IDs posibles y usa búsqueda automática como fallback.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata de cobertura)
        """
        logger.info(f"Extrayendo precios de ALQUILER ({year_start}-{year_end})")
        
        coverage_metadata = {
            "requested_range": {"start": year_start, "end": year_end},
            "success": False,
            "alternative_datasets_searched": False,
            "ids_tried": []
        }
        
        # Intentar primero con múltiples IDs posibles
        possible_ids = [
            self.DATASETS["housing_alquiler"],  # ID principal
            "lloguer-mitja-mensual",
            "est-lloguer-mitja",
            "mercat-immobiliari-lloguer",
        ]
        
        resources = {}
        found_dataset = None
        
        for dataset_id in possible_ids:
            logger.debug(f"Probando dataset ID: {dataset_id}")
            coverage_metadata["ids_tried"].append(dataset_id)
            
            temp_resources = self.get_dataset_resources_ckan(dataset_id)
            if temp_resources:
                logger.info(f"✓ Dataset alquiler encontrado: {dataset_id}")
                resources = temp_resources
                found_dataset = dataset_id
                coverage_metadata["dataset_id"] = dataset_id
                break
        
        # Si la API CKAN falló con todos los IDs, buscar alternativas automáticamente
        if not resources:
            logger.warning("Ningún ID conocido funcionó. Buscando datasets alternativos...")
            
            # Buscar datasets alternativos
            alternative_keywords = ["lloguer", "alquiler", "rent", "renta"]
            alternative_datasets = []
            
            for keyword in alternative_keywords:
                found = self.search_datasets_by_keyword(keyword)
                alternative_datasets.extend(found)
                if found:
                    break  # Si encontramos alguno, usar ese
            
            if alternative_datasets:
                logger.info(f"Encontrados {len(alternative_datasets)} datasets alternativos. Intentando con el primero...")
                coverage_metadata["alternative_datasets_searched"] = True
                coverage_metadata["alternative_datasets_found"] = alternative_datasets
                
                # Intentar con el primer dataset alternativo
                found_dataset = alternative_datasets[0]
                coverage_metadata["dataset_id"] = found_dataset
                resources = self.get_dataset_resources_ckan(found_dataset)
            else:
                logger.warning("No se encontraron datasets alternativos de alquiler")
                coverage_metadata["error"] = f"Ningún dataset de alquiler encontrado. IDs probados: {possible_ids}"
                return pd.DataFrame(), coverage_metadata
        
        if not resources:
            coverage_metadata["error"] = "No se encontraron recursos de alquiler"
            return pd.DataFrame(), coverage_metadata
        
        all_data = []
        
        for identifier, url in resources.items():
            # Si identifier es un año (int), filtrar antes de descargar
            if isinstance(identifier, int):
                year = identifier
                if not (year_start <= year <= year_end):
                    logger.debug(f"Omitiendo año {year} (fuera del rango {year_start}-{year_end})")
                    continue
                logger.info(f"Descargando año {year}...")
            else:
                logger.info(f"Descargando recurso: {identifier}...")
            
            df = self.download_and_parse_csv(url)
            
            if not df.empty:
                logger.info(f"✓ {identifier}: {len(df)} registros")
                logger.debug(f"  Columnas: {list(df.columns)}")
                
                df['tipo_operacion'] = 'alquiler'
                df['source'] = 'opendatabcn_incasol'
                
                # Si identifier es un año, agregarlo directamente
                if isinstance(identifier, int):
                    df['año'] = identifier
                else:
                    # Filtrar por años si existe columna de año
                    year_cols = [col for col in df.columns if any(x in col.lower() for x in ['any', 'año', 'year'])]
                    if year_cols:
                        year_col = year_cols[0]
                        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
                        original_count = len(df)
                        df = df[(df[year_col] >= year_start) & (df[year_col] <= year_end)]
                        if len(df) < original_count:
                            logger.info(f"  Filtrado: {len(df)} registros (de {original_count})")
                
                all_data.append(df)
        
        if not all_data:
            coverage_metadata["error"] = "No se obtuvieron datos"
            return pd.DataFrame(), coverage_metadata
        
        df_combined = pd.concat(all_data, ignore_index=True)
        coverage_metadata["success"] = True
        coverage_metadata["records"] = len(df_combined)
        
        logger.info(f"✅ Total registros alquiler: {len(df_combined)}")
        
        # Guardar datos
        self._save_raw_data(
            df_combined,
            "opendatabcn_alquiler",
            'csv',
            year_start=year_start,
            year_end=year_end
        )
        
        return df_combined, coverage_metadata
    
    def extract_demographics_ckan(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrae datos DEMOGRÁFICOS (población) usando API CKAN con IDs correctos.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            Tupla con (DataFrame con datos, metadata de cobertura)
        """
        logger.info(f"Extrayendo datos demográficos ({year_start}-{year_end})")
        
        # Probar múltiples datasets de población
        # Nota: est-padro-edat-any-a-any devuelve 404, usar solo pad_mdbas_sexe por ahora
        dataset_ids = [
            self.DATASETS["demographics"],  # Población por sexo y barrio
            # self.DATASETS["demographics_age"]  # Población por edad - ID no encontrado (404)
        ]
        
        coverage_metadata = {
            "requested_range": {"start": year_start, "end": year_end},
            "datasets_processed": [],
            "datasets_failed": [],
            "success": False
        }
        
        all_data = []
        
        for dataset_id in dataset_ids:
            logger.info(f"Consultando dataset: {dataset_id}")
            resources = self.get_dataset_resources_ckan(dataset_id)
            
            if not resources:
                coverage_metadata["datasets_failed"].append(dataset_id)
                continue
            
            for identifier, url in resources.items():
                # Si identifier es un año (int), filtrar antes de descargar
                if isinstance(identifier, int):
                    year = identifier
                    if not (year_start <= year <= year_end):
                        logger.debug(f"  Omitiendo año {year} (fuera del rango {year_start}-{year_end})")
                        continue
                    logger.info(f"  Descargando año {year}...")
                else:
                    logger.info(f"  Descargando: {identifier}...")
                
                df = self.download_and_parse_csv(url)
                
                if not df.empty:
                    logger.info(f"  ✓ {identifier}: {len(df)} registros")
                    logger.debug(f"    Columnas: {list(df.columns)}")
                    
                    df['dataset_origen'] = dataset_id
                    df['source'] = 'opendatabcn'
                    
                    # Si identifier es un año, agregarlo directamente
                    if isinstance(identifier, int):
                        df['año'] = identifier
                    else:
                        # Filtrar por años si existe columna de año
                        year_cols = [col for col in df.columns if any(x in col.lower() for x in ['any', 'año', 'year'])]
                        if year_cols:
                            year_col = year_cols[0]
                            df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
                            original_count = len(df)
                            df = df[(df[year_col] >= year_start) & (df[year_col] <= year_end)]
                            if len(df) < original_count:
                                logger.info(f"    Filtrado: {len(df)} registros (de {original_count})")
                    
                    all_data.append(df)
                    if dataset_id not in coverage_metadata["datasets_processed"]:
                        coverage_metadata["datasets_processed"].append(dataset_id)
        
        if not all_data:
            logger.warning("No se pudieron extraer datos demográficos")
            coverage_metadata["error"] = "No se obtuvieron datos"
            return pd.DataFrame(), coverage_metadata
        
        df_combined = pd.concat(all_data, ignore_index=True)
        coverage_metadata["success"] = True
        coverage_metadata["records"] = len(df_combined)
        
        logger.info(f"✅ Total registros demografía: {len(df_combined)}")
        
        # Guardar datos
        self._save_raw_data(
            df_combined,
            "opendatabcn_demographics",
            'csv',
            year_start=year_start,
            year_end=year_end
        )
        
        return df_combined, coverage_metadata


class IdealistaExtractor(BaseExtractor):
    """Extractor para datos de Idealista (con prácticas éticas)."""
    
    BASE_URL = "https://www.idealista.com"
    API_URL = "https://api.idealista.com/3.5"
    OAUTH_URL = "https://api.idealista.com/oauth/token"
    
    # Código de Barcelona en Idealista API
    BARCELONA_LOCATION_ID = "8"  # Barcelona city code
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        rate_limit_delay: float = 3.0, 
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor de Idealista.
        
        Args:
            api_key: API key de Idealista (opcional, desde env var IDEALISTA_API_KEY)
            api_secret: API secret de Idealista (opcional, desde env var IDEALISTA_API_SECRET)
            rate_limit_delay: Delay entre peticiones (más largo por ética)
            output_dir: Directorio donde guardar los datos
        """
        super().__init__("Idealista", rate_limit_delay, output_dir)
        self.api_key = api_key or os.getenv("IDEALISTA_API_KEY")
        self.api_secret = api_secret or os.getenv("IDEALISTA_API_SECRET")
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        # Headers para API requests
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BarcelonaHousingAnalyzer/1.0)',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        })
    
    def _get_access_token(self) -> Optional[str]:
        """
        Obtiene un token de acceso OAuth de Idealista.
        
        Returns:
            Token de acceso o None si falla
        """
        if not self.api_key or not self.api_secret:
            logger.warning(
                "API key o secret de Idealista no disponible. "
                "Configura IDEALISTA_API_KEY y IDEALISTA_API_SECRET en variables de entorno."
            )
            return None
        
        # Si tenemos un token válido, reutilizarlo
        if self.access_token and self.token_expires_at:
            if time.time() < self.token_expires_at - 60:  # Renovar 1 minuto antes
                return self.access_token
        
        self._rate_limit()
        
        try:
            auth_data = {
                'grant_type': 'client_credentials',
                'scope': 'read'
            }
            
            response = self.session.post(
                self.OAUTH_URL,
                data=auth_data,
                auth=(self.api_key, self.api_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in
                logger.info("Token de acceso de Idealista obtenido correctamente")
                return self.access_token
            else:
                logger.error(
                    f"Error obteniendo token de Idealista: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Excepción obteniendo token de Idealista: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def search_properties(
        self,
        operation: str = "sale",  # "sale" o "rent"
        location: Optional[str] = None,
        max_items: int = 50,
        **kwargs
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Busca propiedades en Idealista usando la API oficial.
        
        Args:
            operation: Tipo de operación ("sale" o "rent")
            location: Ubicación (por defecto Barcelona)
            max_items: Número máximo de resultados (máx 50 por request)
            **kwargs: Parámetros adicionales de búsqueda (propertyType, center, distance, etc.)
            
        Returns:
            Tupla con (DataFrame o None, metadata)
        """
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "operation": operation,
            "source": "idealista_api",
        }
        
        token = self._get_access_token()
        if not token:
            logger.warning("No se pudo obtener token de acceso de Idealista")
            metadata["error"] = "No se pudo obtener token de acceso"
            return None, metadata
        
        self._rate_limit()
        
        # Preparar headers con token
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        # Parámetros de búsqueda
        search_params = {
            'operation': operation,
            'locationId': location or self.BARCELONA_LOCATION_ID,
            'maxItems': min(max_items, 50),  # API limita a 50 por request
            'numPage': 1,
            'language': 'es',
        }
        
        # Agregar parámetros adicionales
        search_params.update(kwargs)
        
        try:
            response = self.session.post(
                f"{self.API_URL}/es/search",
                headers=headers,
                data=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Procesar resultados
                element_list = data.get('elementList', [])
                pagination = data.get('pagination', {})
                
                if not element_list:
                    logger.warning("No se encontraron propiedades en Idealista")
                    metadata["success"] = True
                    metadata["num_results"] = 0
                    return pd.DataFrame(), metadata
                
                # Convertir a DataFrame
                df = pd.DataFrame(element_list)
                
                metadata["success"] = True
                metadata["num_results"] = len(df)
                metadata["total_results"] = pagination.get('total', len(df))
                metadata["num_pages"] = pagination.get('totalPages', 1)
                
                logger.info(
                    f"✓ Idealista: {len(df)} propiedades encontradas "
                    f"(total: {metadata['total_results']})"
                )
                
                return df, metadata
                
            elif response.status_code == 401:
                logger.error("Token de Idealista expirado o inválido")
                self.access_token = None  # Forzar renovación
                metadata["error"] = "Token expirado"
                return None, metadata
            else:
                logger.error(
                    f"Error en búsqueda de Idealista: {response.status_code} - {response.text}"
                )
                metadata["error"] = f"HTTP {response.status_code}"
                return None, metadata
                
        except Exception as e:
            logger.error(f"Excepción buscando propiedades en Idealista: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
            return None, metadata
    
    def extract_offer_by_barrio(
        self,
        barrio_names: Optional[List[str]] = None,
        operation: str = "sale",
        max_items_per_barrio: int = 50
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de oferta inmobiliaria por barrio.
        
        Args:
            barrio_names: Lista de nombres de barrios (None = todos los barrios de Barcelona)
            operation: Tipo de operación ("sale" o "rent")
            max_items_per_barrio: Máximo de resultados por barrio
            
        Returns:
            Tupla con (DataFrame o None, metadata)
        """
        logger.info(f"=== Extrayendo oferta de Idealista ({operation}) ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "operation": operation,
            "source": "idealista_api",
            "barrios_processed": 0,
            "total_properties": 0,
        }
        
        if not self.api_key or not self.api_secret:
            logger.warning(
                "API credentials de Idealista no disponibles. "
                "Configura IDEALISTA_API_KEY y IDEALISTA_API_SECRET."
            )
            metadata["error"] = "API credentials no disponibles"
            return None, metadata
        
        all_results = []
        
        # Si no se especifican barrios, buscar en toda Barcelona
        if not barrio_names:
            logger.info("Buscando propiedades en toda Barcelona...")
            df, search_metadata = self.search_properties(
                operation=operation,
                max_items=max_items_per_barrio
            )
            
            if df is not None and not df.empty:
                all_results.append(df)
                metadata["barrios_processed"] = 1
                metadata["total_properties"] = len(df)
        else:
            # Buscar por cada barrio
            for barrio_name in barrio_names:
                logger.info(f"Buscando propiedades en {barrio_name}...")
                self._rate_limit()
                
                df, search_metadata = self.search_properties(
                    operation=operation,
                    location=barrio_name,
                    max_items=max_items_per_barrio
                )
                
                if df is not None and not df.empty:
                    df['barrio_busqueda'] = barrio_name
                    all_results.append(df)
                    metadata["barrios_processed"] += 1
                    metadata["total_properties"] += len(df)
        
        if not all_results:
            logger.warning("No se encontraron propiedades en Idealista")
            metadata["success"] = True
            return pd.DataFrame(), metadata
        
        # Combinar todos los resultados
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Normalizar y procesar datos
        processed_df = self._process_idealista_data(combined_df, operation)
        
        # Guardar datos raw
        if processed_df is not None and not processed_df.empty:
            filepath = self._save_raw_data(
                processed_df,
                f"idealista_oferta_{operation}",
                'csv'
            )
            metadata["filepath"] = str(filepath)
            metadata["success"] = True
        
        return processed_df, metadata
    
    def _process_idealista_data(
        self,
        df: pd.DataFrame,
        operation: str
    ) -> Optional[pd.DataFrame]:
        """
        Procesa y normaliza datos de Idealista.
        
        Args:
            df: DataFrame con datos raw de Idealista
            operation: Tipo de operación ("sale" o "rent")
            
        Returns:
            DataFrame procesado o None
        """
        if df.empty:
            return None
        
        try:
            # Seleccionar y renombrar columnas relevantes
            columns_map = {
                'propertyCode': 'property_code',
                'price': 'precio',
                'size': 'superficie',
                'rooms': 'habitaciones',
                'bathrooms': 'banos',
                'floor': 'planta',
                'propertyType': 'tipo_propiedad',
                'address': 'direccion',
                'district': 'distrito',
                'neighborhood': 'barrio_idealista',
                'latitude': 'latitud',
                'longitude': 'longitud',
                'url': 'url_anuncio',
                'date': 'fecha_publicacion',
                'newDevelopment': 'obra_nueva',
                'parkingSpace': 'parking',
                'exterior': 'exterior',
                'elevator': 'ascensor',
            }
            
            # Crear DataFrame con columnas disponibles
            processed = pd.DataFrame()
            for idealista_col, our_col in columns_map.items():
                if idealista_col in df.columns:
                    processed[our_col] = df[idealista_col]
            
            # Agregar columnas calculadas
            if 'precio' in processed.columns and 'superficie' in processed.columns:
                processed['precio_m2'] = processed['precio'] / processed['superficie'].replace(0, pd.NA)
            
            # Agregar metadata
            processed['operacion'] = operation
            processed['fecha_extraccion'] = datetime.now().isoformat()
            processed['source'] = 'idealista_api'
            
            # Normalizar tipología
            if 'tipo_propiedad' in processed.columns:
                processed['tipologia'] = processed['tipo_propiedad'].map({
                    'flat': 'piso',
                    'house': 'casa',
                    'studio': 'estudio',
                    'penthouse': 'ático',
                    'duplex': 'dúplex',
                    'chalet': 'chalet',
                }).fillna(processed['tipo_propiedad'])
            
            return processed
            
        except Exception as e:
            logger.error(f"Error procesando datos de Idealista: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_housing_prices_by_neighborhood(
        self,
        neighborhood: str,
        operation: str = "sale",
        year_start: int = 2015,
        year_end: int = 2025
    ) -> pd.DataFrame:
        """
        Obtiene precios de vivienda por barrio (método legacy, usa extract_offer_by_barrio).
        
        Args:
            neighborhood: Nombre del barrio
            operation: Tipo de operación ("sale" o "rent")
            year_start: Año inicial (no usado, Idealista no proporciona datos históricos)
            year_end: Año final (no usado)
            
        Returns:
            DataFrame con precios de vivienda
        """
        logger.info(f"Extrayendo precios Idealista para {neighborhood} ({operation})")
        
        df, metadata = self.extract_offer_by_barrio(
            barrio_names=[neighborhood],
            operation=operation
        )
        
        return df if df is not None else pd.DataFrame()
    
    def _fetch_via_api(
        self,
        neighborhood: str,
        operation: str
    ) -> pd.DataFrame:
        """Obtiene datos usando la API oficial de Idealista (método legacy)."""
        return self.get_housing_prices_by_neighborhood(neighborhood, operation)
    
    def download_idealista_report(self, url: str) -> Optional[Path]:
        """
        Descarga un informe público de Idealista/data.
        
        Args:
            url: URL del informe a descargar
            
        Returns:
            Path del archivo descargado o None
        """
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            if not self._validate_response(response):
                return None
            
            # Detectar tipo de archivo
            content_type = response.headers.get('Content-Type', '')
            if 'csv' in content_type:
                ext = 'csv'
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                ext = 'xlsx'
            else:
                ext = 'pdf'
            
            filename = f"idealista_report_{datetime.now().strftime('%Y%m%d')}.{ext}"
            filepath = self.output_dir / "idealista" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Informe Idealista descargado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error descargando informe Idealista: {e}")
            return None


class PortalDadesExtractor(BaseExtractor):
    """
    Extractor para el Portal de Dades de Barcelona usando Playwright y API con Client ID.
    
    Este extractor:
    1. Usa Playwright para hacer scraping del portal (navegación JavaScript)
    2. Extrae IDs de indicadores del tema "Habitatge"
    3. Descarga datos usando la API con Client ID proporcionado
    
    Requiere la variable de entorno PORTALDADES_CLIENT_ID para autenticación con la API.
    """
    
    BASE_URL = "https://portaldades.ajuntament.barcelona.cat"
    API_EXPORT_URL = f"{BASE_URL}/services/backend/rest/statistic/export"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        rate_limit_delay: float = 2.0,
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor del Portal de Dades.
        
        Args:
            client_id: Client ID para la API (por defecto lee de PORTALDADES_CLIENT_ID)
            rate_limit_delay: Tiempo de espera entre peticiones
            output_dir: Directorio donde guardar los datos
        """
        super().__init__("PortalDades", rate_limit_delay, output_dir)
        
        # Obtener Client ID de parámetro o variable de entorno
        self.client_id = client_id or os.getenv("PORTALDADES_CLIENT_ID")
        if not self.client_id:
            logger.warning(
                "PORTALDADES_CLIENT_ID no encontrado. "
                "Configura la variable de entorno o pasa client_id al constructor."
            )
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "Playwright no está disponible. "
                "Instala con: pip install playwright && playwright install"
            )
        
        # Headers para la API
        self.api_headers = {
            "X-IBM-Client-Id": self.client_id or ""
        }
    
    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normaliza un título para usarlo como nombre de archivo."""
        if not title:
            return ""
        normalized = unicodedata.normalize("NFKD", title)
        normalized = normalized.encode("ascii", "ignore").decode("utf-8")
        normalized = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
        normalized = re.sub(r"[-\s]+", "_", normalized)
        return normalized
    
    def scrape_indicadores_habitatge(
        self,
        start_url: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Extrae metadatos de indicadores del tema "Habitatge" usando la API REST.
        
        Solo extrae datasets de tipo "Taula estadística" (source=STATISTICS), ignorando otros tipos
        como "Micodada", "Data Stories", "Enquesta", "Document", "Mapa", etc.
        
        Args:
            start_url: Ignorado (se usa la API REST directamente)
            max_pages: Número máximo de páginas a recorrer (None = todas)
            
        Returns:
            Lista de diccionarios con metadatos del indicador (solo "Taula estadística")
        """
        API_SEARCH_URL = f"{self.BASE_URL}/services/backend/rest/search"
        ROWS_PER_PAGE = 10
        
        logger.info("Extrayendo indicadores del Portal de Dades usando API REST")
        
        indicadores: List[Dict[str, str]] = []
        page_number = 1
        start = 0
        
        try:
            # Primera petición para obtener el total
            params = {
                "query": "",
                "start": 0,
                "rows": ROWS_PER_PAGE,
                "language": "ca",
                "source": "STATISTICS",
                "thesaurus": "Habitatge"
            }
            
            self._rate_limit()
            response = self.session.get(
                API_SEARCH_URL,
                params=params,
                headers=self.api_headers,
                timeout=60
            )
            
            if not self._validate_response(response):
                logger.error("Error en la primera petición a la API")
                return []
            
            data = response.json()
            total_count = data.get("count", 0)
            logger.info(f"Total de indicadores disponibles: {total_count}")
            
            if total_count == 0:
                logger.warning("No se encontraron indicadores")
                return []
            
            # Calcular número máximo de páginas
            total_pages = (total_count + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            logger.info(f"Procesando {total_pages} páginas (máximo {max_pages if max_pages else 'todas'})")
            
            # Procesar todas las páginas
            while start < total_count:
                if max_pages and page_number > max_pages:
                    logger.info(f"Límite de páginas alcanzado ({max_pages})")
                    break
                
                params["start"] = start
                self._rate_limit()
                
                try:
                    response = self.session.get(
                        API_SEARCH_URL,
                        params=params,
                        headers=self.api_headers,
                        timeout=60
                    )
                    
                    if not self._validate_response(response):
                        logger.warning(f"Error en la petición de la página {page_number}")
                        break
                    
                    data = response.json()
                    items = data.get("data", [])
                    
                    if not items:
                        logger.info(f"No hay más items en la página {page_number}")
                        break
                    
                    nuevos_en_pagina = 0
                    for item in items:
                        id_indicador = item.get("id")
                        if not id_indicador:
                            continue
                        
                        # Extraer metadatos
                        nombre = item.get("title", "Título no disponible")
                        descripcion = item.get("description", "")
                        doc_source = item.get("docSource", [])
                        origen_texto = ", ".join(doc_source) if doc_source else ""
                        publish_date = item.get("publishDate", "")
                        
                        # Formatear fecha
                        fecha_texto = ""
                        if publish_date:
                            try:
                                from datetime import datetime as dt
                                dt_obj = dt.fromisoformat(publish_date.replace("Z", "+00:00"))
                                fecha_texto = dt_obj.strftime("%d/%m/%Y")
                            except Exception:
                                fecha_texto = publish_date[:10] if len(publish_date) >= 10 else publish_date
                        
                        nombre_limpio = self._normalize_title(nombre)
                        detalle_url = f"{self.BASE_URL}/estadístiques/{id_indicador}"
                        
                        metadata = {
                            "id_indicador": id_indicador,
                            "nombre": nombre,
                            "nombre_limpio": nombre_limpio,
                            "descripcion": descripcion,
                            "fecha": fecha_texto,
                            "origen": origen_texto,
                            "tipo": "Taula estadística",
                            "categoria": "estadístiques",
                            "detalle_url": detalle_url
                        }
                        
                        indicadores.append(metadata)
                        nuevos_en_pagina += 1
                        logger.debug("Nuevo indicador: %s - %s", id_indicador, nombre[:80])
                    
                    logger.info(
                        "Página %s (start=%s): %s indicadores encontrados (total acumulado: %s)",
                        page_number,
                        start,
                        nuevos_en_pagina,
                        len(indicadores)
                    )
                    
                    start += ROWS_PER_PAGE
                    page_number += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando página {page_number}: {e}")
                    logger.debug(traceback.format_exc())
                    break
                    
        except Exception as e:
            logger.error(f"Error durante la extracción: {e}")
            logger.debug(traceback.format_exc())
        
        logger.info(
            f"Total de indicadores 'Taula estadística' extraídos: {len(indicadores)}"
        )
        return indicadores
    
    def descargar_indicador(
        self,
        id_indicador: str,
        nombre: str,
        formato: str = "CSV"
    ) -> Optional[Path]:
        """
        Descarga un indicador específico usando la API con Client ID.
        
        Args:
            id_indicador: ID del indicador
            nombre: Nombre descriptivo (para el archivo)
            formato: Formato de descarga ("CSV" o "Excel")
            
        Returns:
            Path del archivo descargado o None
        """
        self._rate_limit()
        
        params = {
            "id": id_indicador,
            "fileformat": formato
        }
        
        try:
            response = self.session.get(
                self.API_EXPORT_URL,
                params=params,
                headers=self.api_headers,
                timeout=60
            )
            
            if not self._validate_response(response):
                return None
            
            # Normalizar nombre del archivo
            nombre_limpio = re.sub(r'[^\w\s-]', '', nombre).strip()
            nombre_limpio = re.sub(r'[-\s]+', '_', nombre_limpio)
            
            extension = formato.lower()
            if extension == "excel":
                extension = "xlsx"
            
            filename = f"portaldades_{nombre_limpio}_{id_indicador}.{extension}"
            filepath = self.output_dir / "portaldades" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Descargado: {filename}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error descargando indicador {id_indicador}: {e}")
            return None
    
    def extraer_y_descargar_habitatge(
        self,
        descargar: bool = True,
        formato: str = "CSV",
        max_pages: Optional[int] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, Optional[Path]]]:
        """
        Extrae IDs de indicadores y opcionalmente los descarga.
        
        Args:
            descargar: Si True, descarga los indicadores después de extraerlos
            formato: Formato de descarga ("CSV" o "Excel")
            max_pages: Número máximo de páginas a recorrer
            
        Returns:
            Tupla con (lista de metadatos, diccionario de {id: path_descargado})
        """
        indicadores = self.scrape_indicadores_habitatge(max_pages=max_pages)
        
        if not indicadores:
            logger.warning("No se encontraron indicadores")
            return [], {}
        
        # Guardar lista de indicadores con metadatos
        metadata_file = self.output_dir / "portaldades" / "indicadores_habitatge.csv"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "id_indicador",
            "nombre",
            "nombre_limpio",
            "descripcion",
            "fecha",
            "origen",
            "tipo",
            "categoria",
            "detalle_url"
        ]
        
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for indicador in indicadores:
                writer.writerow({k: indicador.get(k, "") for k in fieldnames})
        
        logger.info(f"Lista de indicadores guardada en: {metadata_file}")
        
        # Descargar si se solicita
        archivos_descargados: Dict[str, Optional[Path]] = {}
        
        if descargar:
            logger.info(f"Descargando {len(indicadores)} indicadores en formato {formato}...")
            for i, indicador in enumerate(indicadores, 1):
                id_indicador = indicador.get("id_indicador")
                nombre = indicador.get("nombre") or id_indicador
                logger.info(f"[{i}/{len(indicadores)}] Descargando: {nombre[:80]}...")
                path = self.descargar_indicador(id_indicador, nombre, formato)
                archivos_descargados[id_indicador] = path
        
        return indicadores, archivos_descargados
    
    @staticmethod
    def _accept_cookies(page) -> None:
        """Intenta aceptar el banner de cookies si aparece."""
        cookie_selectors = [
            "button.lw-consent-accept",
            "button[aria-label='Accept all cookies']",
            "#lw-banner button.lw-consent-accept",
        ]
        for selector in cookie_selectors:
            try:
                button = page.locator(selector)
                if button.count() > 0 and button.is_visible():
                    button.click()
                    page.wait_for_timeout(500)
                    logger.debug("Banner de cookies aceptado (%s)", selector)
                    break
            except Exception:
                continue
    
    @staticmethod
    def _scroll_to_load_more(page, pause_ms: int = 1500) -> None:
        """Realiza un scroll hasta el final de la página para disparar la carga incremental."""
        try:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        except Exception:
            logger.debug("No se pudo ejecutar scroll mediante evaluate, usando mouse.wheel")
            try:
                page.mouse.wheel(0, 2000)
            except Exception:
                logger.debug("No se pudo realizar scroll con mouse.wheel")
        page.wait_for_timeout(pause_ms)


def validate_data_size(df: pd.DataFrame, source_name: str, min_records: int = MIN_RECORDS_WARNING) -> bool:
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
        
    Returns:
        Tupla con (diccionario de DataFrames por fuente, metadata de cobertura)
    
    Nota sobre paralelización futura:
        Para paralelizar, usar concurrent.futures.ThreadPoolExecutor o ProcessPoolExecutor.
        Considerar rate limits de cada fuente y usar semáforos para controlar concurrencia.
        Ejemplo futuro:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=len(sources)) as executor:
                futures = {executor.submit(extract_source, source): source for source in sources}
                for future in as_completed(futures):
                    source = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        logger.error(f"Error en {source}: {e}")
    """
    if sources is None:
        sources = ["ine", "opendatabcn", "idealista", "portaldades"]
    
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
                    max_pages=None  # Recorrer todas las páginas
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
                        "archivos_descargados": len([p for p in archivos.values() if p is not None]),
                        "archivos_fallidos": len([p for p in archivos.values() if p is None])
                    }
                    
                    is_valid = validate_data_size(df_indicadores, "PortalDades Indicadores")
                    if is_valid:
                        coverage_metadata["sources_success"].append("portaldades")
                    else:
                        coverage_metadata["sources_failed"].append("portaldades")
                else:
                    results["portaldades_indicadores"] = pd.DataFrame()
                    coverage_metadata["coverage_by_source"]["portaldades"] = {
                        "success": False,
                        "error": "No se encontraron indicadores"
                    }
                    coverage_metadata["sources_failed"].append("portaldades")
                    
            except Exception as e:
                logger.error(f"Error extrayendo datos del Portal de Dades: {e}")
                logger.debug(traceback.format_exc())
                results["portaldades_indicadores"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["portaldades"] = {"error": str(e)}
                coverage_metadata["sources_failed"].append("portaldades")
                if not continue_on_error:
                    raise
                    
        except Exception as e:
            error_msg = f"Error en extracción Portal de Dades: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            results["portaldades_indicadores"] = pd.DataFrame()
            coverage_metadata["sources_failed"].append("portaldades")
            coverage_metadata["coverage_by_source"]["portaldades"] = {"error": str(e)}
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


if __name__ == "__main__":
    """Ejemplo de uso del módulo de extracción."""
    
    # Extraer datos de todas las fuentes
    data, metadata = extract_all_sources(year_start=2015, year_end=2025)
    
    # Guardar resumen
    summary = {
        "extraction_date": datetime.now().isoformat(),
        "sources": {k: len(v) for k, v in data.items()},
        "coverage_metadata": metadata
    }
    
    summary_path = DATA_RAW_DIR / f"extraction_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Resumen de extracción guardado en: {summary_path}")
