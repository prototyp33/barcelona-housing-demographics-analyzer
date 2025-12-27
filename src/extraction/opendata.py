"""
OpenData BCN Extractor Module - Extracción de datos de Open Data Barcelona.
"""

import io
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chardet
import pandas as pd

from .base import BaseExtractor, logger


class OpenDataBCNExtractor(BaseExtractor):
    """Extractor para datos de Open Data Barcelona."""
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    API_URL = f"{BASE_URL}/data/api/3/action"
    
    # IDs de datasets CKAN identificados y confirmados
    DATASETS = {
        "demographics": "pad_mdbas_sexe",  # Población por sexo y barrio
        "demographics_age": "est-padro-edat-any-a-any",  # Población por edad
        "housing_venta": "habitatges-2na-ma",  # Precios de venta (confirmado)
        "housing_alquiler": "est-lloguer-mitja-mensual",  # Precios de alquiler (reporte técnico)
        "housing_alquiler_trimestral": "est-lloguer-preu-trim",  # Trimestral
        # Nuevos datasets recomendados
        "housing_venta_evolucion": "h2mave-totalt3b",
        "housing_venta_anual": "h2mave-anualt3b",
        "income_gross_household": "atles-renda-bruta-per-llar",
        "income_gini": "atles-renda-index-gini",
        "income_p80_p20": "atles-renda-p80-p20-distribucio",
        "cadastre_year_const": "est-cadastre-habitatges-any-const",
        "cadastre_owner_type": "est-cadastre-carrecs-tipus-propietari",
        "cadastre_avg_surface": "est-cadastre-habitatges-superficie-mitjana",
        "cadastre_owner_nationality": "est-cadastre-locals-prop",
        "cadastre_floors": "immo-edif-hab-segons-num-plantes-sobre-rasant",
        "household_crowding": "pad_dom_mdbas_n-persones",
        "household_nationality": "pad_dom_mdbas_nacionalitat",
        "household_minors": "pad_dom_mdbas_edat-0018",
        "household_women": "pad_dom_mdbas_dones",
        "tourism_intensity": "intensitat-activitat-turistica",
        "tourism_hut": "habitatges-us-turistic",
        "environment_noise_map": "capacitat-mapa-estrategic-soroll",
        "geo_districts_neighborhoods": "districtes-barris",
        "geo_streets": "carrerer",
        "construction_licenses": "llicencies-obres-majors",
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
                # Detectar encoding del CSV (puede ser UTF-16, UTF-8, etc.)
                raw_data = response.content
                detected = chardet.detect(raw_data)
                detected_encoding = detected.get('encoding', 'utf-8')
                logger.debug(f"Encoding detectado para CSV: {detected_encoding} (confianza: {detected.get('confidence', 0):.2f})")
                
                # Intentar leer CSV con diferentes encodings y manejo de errores
                df = None
                encodings_to_try = [detected_encoding, 'utf-16', 'utf-8', 'latin-1', 'iso-8859-1']
                
                for encoding in encodings_to_try:
                    try:
                        # Usar BytesIO para mejor manejo de encoding
                        df = pd.read_csv(
                            io.BytesIO(raw_data),
                            encoding=encoding,
                            on_bad_lines='skip',  # pandas >= 1.3.0
                            engine='python'  # Más tolerante con errores
                        )
                        if not df.empty:
                            logger.info(f"CSV leído exitosamente con encoding: {encoding}")
                            break
                    except (TypeError, UnicodeDecodeError, pd.errors.ParserError) as e:
                        # Intentar con parámetros alternativos para versiones antiguas de pandas
                        try:
                            df = pd.read_csv(
                                io.BytesIO(raw_data),
                                encoding=encoding,
                                error_bad_lines=False,  # pandas < 1.3.0
                                warn_bad_lines=False,
                                engine='python'
                            )
                            if not df.empty:
                                logger.info(f"CSV leído exitosamente con encoding: {encoding} (modo compatibilidad)")
                                break
                        except Exception:
                            continue
                
                if df is None or df.empty:
                    logger.warning("No se pudo leer el CSV con ningún encoding, intentando último recurso...")
                    try:
                        df = pd.read_csv(io.BytesIO(raw_data), encoding='utf-8', engine='python')
                    except Exception as e:
                        logger.error(f"Error final leyendo CSV: {e}")
                        raise
            elif 'json' in format_type:
                df = pd.json_normalize(response.json())
            elif 'xlsx' in format_type or 'excel' in format_type:
                df = pd.read_excel(io.BytesIO(response.content))
            else:
                logger.warning(f"Formato {format_type} no soportado, intentando CSV")
                try:
                    df = pd.read_csv(
                        io.StringIO(response.text),
                        encoding='utf-8',
                        on_bad_lines='skip',
                        engine='python'
                    )
                except TypeError:
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
    
    def download_dataset_historical(
        self,
        dataset_id: str,
        year_start: int,
        year_end: int,
        resource_format: str = 'csv'
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Descarga un dataset histórico descargando todos los recursos por año.
        
        Detecta recursos con años en el nombre (ej: '2023_atles_renda_bruta_llar.csv')
        y los descarga todos para crear una serie temporal completa.
        
        Args:
            dataset_id: ID del dataset
            year_start: Año inicial
            year_end: Año final
            resource_format: Formato preferido ('csv', 'json', 'xlsx')
            
        Returns:
            Tupla con (DataFrame combinado con todos los años, metadata)
        """
        logger.info(f"Descargando dataset histórico {dataset_id} ({year_start}-{year_end})...")
        
        coverage_metadata = {
            "dataset_id": dataset_id,
            "requested_range": {"start": year_start, "end": year_end},
            "success": False,
            "resources_downloaded": []
        }
        
        try:
            dataset_info = self.get_dataset_info(dataset_id)
            if not dataset_info:
                logger.error(f"Dataset {dataset_id} no encontrado")
                coverage_metadata["error"] = "Dataset no encontrado"
                return None, coverage_metadata
            
            resources = dataset_info.get('resources', [])
            
            # Filtrar recursos que coincidan con el formato y tengan años en el nombre
            import re
            all_data = []
            requested_years = set(range(year_start, year_end + 1))
            found_years = set()
            
            for resource in resources:
                # Verificar formato
                if resource_format.lower() not in resource.get('format', '').lower():
                    continue
                
                # Buscar año en el nombre del recurso
                resource_name = resource.get('name', '')
                year_match = re.search(r'(\d{4})', resource_name)
                
                if year_match:
                    resource_year = int(year_match.group(1))
                    
                    # Si el año está en el rango solicitado
                    if resource_year in requested_years:
                        try:
                            download_url = resource.get('url')
                            if not download_url:
                                continue
                            
                            self._rate_limit()
                            response = self.session.get(download_url, timeout=60)
                            
                            if self._validate_response(response):
                                # Parsear según formato
                                format_type = resource.get('format', '').lower()
                                
                                if 'csv' in format_type:
                                    df = pd.read_csv(io.StringIO(response.text), encoding='utf-8')
                                elif 'json' in format_type:
                                    df = pd.json_normalize(response.json())
                                elif 'xlsx' in format_type or 'excel' in format_type:
                                    df = pd.read_excel(io.BytesIO(response.content))
                                else:
                                    continue
                                
                                # Añadir columna de año si no existe
                                year_cols = [col for col in df.columns 
                                           if any(kw in col.lower() for kw in ['any', 'año', 'year', 'anio'])]
                                if not year_cols:
                                    df['Any'] = resource_year
                                
                                all_data.append(df)
                                found_years.add(resource_year)
                                coverage_metadata["resources_downloaded"].append({
                                    "year": resource_year,
                                    "name": resource_name,
                                    "records": len(df)
                                })
                                
                                logger.debug(f"  ✓ {resource_year}: {len(df)} registros")
                        except Exception as e:
                            logger.warning(f"Error descargando recurso {resource_name}: {e}")
                            continue
            
            if not all_data:
                logger.warning(f"No se encontraron recursos históricos para {dataset_id}")
                coverage_metadata["error"] = "No se encontraron recursos históricos"
                return None, coverage_metadata
            
            # Combinar todos los DataFrames
            df_combined = pd.concat(all_data, ignore_index=True)
            
            # Asegurar que la columna de año esté normalizada
            year_cols = [col for col in df_combined.columns 
                        if any(kw in col.lower() for kw in ['any', 'año', 'year', 'anio'])]
            if year_cols:
                year_col = year_cols[0]
                df_combined[year_col] = pd.to_numeric(df_combined[year_col], errors='coerce')
                available_years = sorted(df_combined[year_col].dropna().unique().astype(int).tolist())
                coverage_metadata["available_years"] = available_years
                missing_years = sorted(list(requested_years - found_years))
                coverage_metadata["missing_years"] = missing_years
                coverage_metadata["coverage_percentage"] = len(found_years & requested_years) / len(requested_years) * 100
            
            # Guardar datos raw combinados
            self._save_raw_data(
                df_combined,
                f"opendatabcn_{dataset_id}",
                'csv',
                year_start=year_start,
                year_end=year_end
            )
            
            logger.info(f"Dataset histórico {dataset_id} descargado y guardado: {len(df_combined)} registros, años {sorted(found_years)}")
            return df_combined, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error descargando dataset histórico {dataset_id}: {e}")
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
    
    def search_datasets_by_keyword(self, keyword: str, limit: int = 20) -> List[str]:
        """
        Busca datasets en Open Data BCN por palabra clave usando la API de búsqueda de CKAN.
        
        Esta es una versión optimizada que usa package_search en lugar de iterar
        sobre todos los datasets.
        
        Args:
            keyword: Palabra clave para buscar (ej: "alquiler", "lloguer", "vivienda")
            limit: Número máximo de resultados a retornar (default: 20)
            
        Returns:
            Lista de IDs de datasets encontrados
        """
        logger.info(f"Buscando datasets con palabra clave: '{keyword}' (limit: {limit})")
        
        matching_datasets = []
        
        try:
            # Usar la API de búsqueda de CKAN (mucho más eficiente)
            self._rate_limit()
            url = f"{self.API_URL}/package_search"
            
            # Buscar en título, descripción y tags
            params = {
                "q": keyword,
                "rows": limit,
                "start": 0,
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if self._validate_response(response):
                data = response.json()
                results = data.get("result", {}).get("results", [])
                
                for result in results:
                    dataset_id = result.get("name") or result.get("id")
                    if dataset_id:
                        matching_datasets.append(dataset_id)
                        title = result.get("title", "Sin título")
                        logger.info(f"  Encontrado: {dataset_id} - {title}")
                
                logger.info(f"Total encontrados: {len(matching_datasets)} datasets")
            else:
                logger.warning(f"Error en búsqueda de CKAN para '{keyword}'")
                # Fallback: método anterior (más lento pero funciona)
                return self._search_datasets_fallback(keyword, limit)
                
        except Exception as e:
            logger.warning(f"Error en búsqueda optimizada: {e}")
            logger.info("Usando método de búsqueda alternativo...")
            # Fallback: método anterior
            return self._search_datasets_fallback(keyword, limit)
        
        return matching_datasets
    
    def _search_datasets_fallback(self, keyword: str, limit: int = 20) -> List[str]:
        """
        Método de búsqueda alternativo (más lento) cuando la API de búsqueda falla.
        
        Args:
            keyword: Palabra clave para buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de IDs de datasets encontrados
        """
        logger.info(f"Usando búsqueda alternativa para: '{keyword}'")
        
        all_datasets = self.get_dataset_list()
        matching_datasets = []
        
        # Limitar búsqueda a primeros N datasets para mejorar rendimiento
        search_limit = min(len(all_datasets), limit * 10)  # Buscar en más datasets de los que queremos
        
        for i, dataset_id in enumerate(all_datasets[:search_limit]):
            if len(matching_datasets) >= limit:
                break
                
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
            year_end=year_end,
            data_type="prices_venta"
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
            year_end=year_end,
            data_type="prices_alquiler"
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
            year_end=year_end,
            data_type="demographics"
        )
        
        return df_combined, coverage_metadata

