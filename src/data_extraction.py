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
import time
import traceback
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    
    # IDs de datasets relevantes (ejemplos - ajustar según necesidades)
    DATASETS = {
        "demographics": "demografia-per-barris",
        "housing": "habitatge-per-barris",
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
        """Obtiene datos demográficos por barrio."""
        return self.download_dataset(
            self.DATASETS.get("demographics", "demografia-per-barris"),
            year_start=year_start,
            year_end=year_end
        )
    
    def get_housing_data_by_neighborhood(
        self,
        year_start: int = 2015,
        year_end: int = 2025
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Obtiene datos de vivienda por barrio."""
        return self.download_dataset(
            self.DATASETS.get("housing", "habitatge-per-barris"),
            year_start=year_start,
            year_end=year_end
        )


class IdealistaExtractor(BaseExtractor):
    """Extractor para datos de Idealista (con prácticas éticas)."""
    
    BASE_URL = "https://www.idealista.com"
    API_URL = "https://api.idealista.com/3.5"
    
    # Barrios de Barcelona (códigos postales aproximados)
    BARCELONA_NEIGHBORHOODS = {
        "Ciutat Vella": ["08001", "08002", "08003"],
        "Eixample": ["08008", "08009", "08010", "08011", "08013", "08015"],
        "Sants-Montjuïc": ["08014", "08020", "08028", "08038"],
        "Les Corts": ["08014", "08028"],
        "Sarrià-Sant Gervasi": ["08017", "08021", "08022", "08023", "08034"],
        "Gràcia": ["08012", "08024"],
        "Horta-Guinardó": ["08025", "08031", "08032", "08041", "08042"],
        "Nou Barris": ["08030", "08033", "08035", "08037"],
        "Sant Andreu": ["08020", "08030", "08033"],
        "Sant Martí": ["08005", "08018", "08019", "08025", "08026", "08027"]
    }
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 3.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de Idealista.
        
        Args:
            api_key: API key de Idealista (opcional, para uso oficial)
            rate_limit_delay: Delay entre peticiones (más largo por ética)
            output_dir: Directorio donde guardar los datos
        """
        super().__init__("Idealista", rate_limit_delay, output_dir)
        self.api_key = api_key or os.getenv("IDEALISTA_API_KEY")
        
        # Headers éticos para scraping
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BarcelonaHousingAnalyzer/1.0; +https://github.com/yourrepo)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_housing_prices_by_neighborhood(
        self,
        neighborhood: str,
        operation: str = "sale",  # "sale" o "rent"
        year_start: int = 2015,
        year_end: int = 2025
    ) -> pd.DataFrame:
        """
        Obtiene precios de vivienda por barrio.
        
        Args:
            neighborhood: Nombre del barrio
            operation: Tipo de operación ("sale" o "rent")
            year_start: Año inicial
            year_end: Año final
            
        Returns:
            DataFrame con precios de vivienda
        """
        logger.info(f"Extrayendo precios Idealista para {neighborhood} ({operation})")
        
        # Nota: Idealista no proporciona datos históricos fácilmente
        # Este método es un placeholder para implementación futura
        # Se recomienda usar la API oficial de Idealista si está disponible
        
        if self.api_key:
            return self._fetch_via_api(neighborhood, operation)
        else:
            logger.warning(
                "API key de Idealista no disponible. "
                "Para uso ético, se recomienda usar la API oficial."
            )
            return pd.DataFrame()
    
    def _fetch_via_api(
        self,
        neighborhood: str,
        operation: str
    ) -> pd.DataFrame:
        """Obtiene datos usando la API oficial de Idealista."""
        # Placeholder para implementación con API oficial
        # Requiere autenticación OAuth y rate limits estrictos
        logger.info("Usando API oficial de Idealista (implementación pendiente)")
        return pd.DataFrame()
    
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
        sources = ["ine", "opendatabcn", "idealista"]
    
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
            
            # Demographics
            try:
                df_demo, metadata_demo = bcn_extractor.get_demographics_by_neighborhood(
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
            
            # Housing
            try:
                df_housing, metadata_housing = bcn_extractor.get_housing_data_by_neighborhood(
                    year_start, year_end
                )
                results["opendatabcn_housing"] = df_housing if df_housing is not None else pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_housing"] = metadata_housing
                
                # Validar tamaño de datos
                is_valid = validate_data_size(results["opendatabcn_housing"], "OpenDataBCN Housing")
                
                if df_housing is not None and not df_housing.empty and is_valid:
                    coverage_metadata["sources_success"].append("opendatabcn_housing")
                else:
                    coverage_metadata["sources_failed"].append("opendatabcn_housing")
            except Exception as e:
                logger.error(f"Error extrayendo housing de Open Data BCN: {e}")
                logger.debug(traceback.format_exc())
                results["opendatabcn_housing"] = pd.DataFrame()
                coverage_metadata["coverage_by_source"]["opendatabcn_housing"] = {"error": str(e)}
                coverage_metadata["sources_failed"].append("opendatabcn_housing")
                
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
            # Nota: Implementación pendiente según disponibilidad de API
            results["idealista"] = pd.DataFrame()
            coverage_metadata["coverage_by_source"]["idealista"] = {
                "success": False,
                "note": "Implementación pendiente"
            }
            validate_data_size(results["idealista"], "Idealista")
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
