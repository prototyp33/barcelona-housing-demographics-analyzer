"""
Idealista Extractor Module - Extracción de datos de Idealista (API).
"""

import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger


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
                'csv',
                data_type=f"idealista_{operation}"
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

