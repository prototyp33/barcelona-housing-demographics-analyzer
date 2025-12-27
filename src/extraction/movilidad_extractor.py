"""
Movilidad Extractor Module - Extracción de datos de transporte y movilidad.

Fuentes:
- Bicing: API GBFS (https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/)
- ATM: API de Autoritat del Transport Metropolità (requiere API key)
"""

import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger

# Rango válido de coordenadas para Barcelona (aproximado)
BARCELONA_LAT_MIN = 41.35
BARCELONA_LAT_MAX = 41.45
BARCELONA_LON_MIN = 2.05
BARCELONA_LON_MAX = 2.25


class BicingExtractor(BaseExtractor):
    """
    Extractor para datos de Bicing (sistema de bicicletas públicas de Barcelona).
    
    Usa la API GBFS (General Bikeshare Feed Specification) sin autenticación.
    """
    
    BASE_URL = "https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en"
    
    # Endpoints GBFS
    ENDPOINTS = {
        "station_information": f"{BASE_URL}/station_information",
        "station_status": f"{BASE_URL}/station_status",
    }
    
    def __init__(self, rate_limit_delay: float = 1.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de Bicing.
        
        Args:
            rate_limit_delay: Tiempo de espera entre peticiones (segundos).
                             Default 1.0 para cumplir rate limit de 60 req/min.
            output_dir: Directorio donde guardar los datos.
        """
        super().__init__("Bicing", rate_limit_delay, output_dir)
    
    def extract_station_information(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae información de estaciones de Bicing.
        
        Returns:
            Tupla con (DataFrame con estaciones, metadata).
        """
        logger.info("Extrayendo información de estaciones Bicing...")
        
        coverage_metadata = {
            "source": "bicing_gbfs",
            "endpoint": "station_information",
            "success": False,
            "total_stations": 0,
        }
        
        try:
            self._rate_limit()
            try:
                response = self.session.get(self.ENDPOINTS["station_information"], timeout=30)
            except Exception as e:
                # Capturar RetryError cuando todos los retries fallan con 503
                error_str = str(e)
                if "503" in error_str or "Service Unavailable" in error_str:
                    logger.warning("API de Bicing temporalmente no disponible (503). Intentar más tarde.")
                    coverage_metadata["error"] = "Service Unavailable (503)"
                    coverage_metadata["suggestion"] = "La API de Bicing está temporalmente caída. Intentar más tarde o usar datos AMB como alternativa."
                    return None, coverage_metadata
                # Re-lanzar otras excepciones
                raise
            
            # Manejar errores 503 (Service Unavailable) de forma más amigable
            if response.status_code == 503:
                logger.warning("API de Bicing temporalmente no disponible (503). Intentar más tarde.")
                coverage_metadata["error"] = "Service Unavailable (503)"
                coverage_metadata["suggestion"] = "La API de Bicing está temporalmente caída. Intentar más tarde o usar datos AMB como alternativa."
                return None, coverage_metadata
            
            if not self._validate_response(response):
                coverage_metadata["error"] = f"Error en respuesta HTTP: {response.status_code}"
                return None, coverage_metadata
            
            data = response.json()
            
            # GBFS estructura: {"data": {"stations": [...]}}
            if "data" in data and "stations" in data["data"]:
                stations = data["data"]["stations"]
                df = pd.DataFrame(stations)
                
                logger.info(f"Estaciones Bicing extraídas: {len(df)}")
                
                # Validar coordenadas
                df_validated = self._validate_coordinates(df.copy())
                
                coverage_metadata["total_stations"] = len(df)
                coverage_metadata["stations_with_valid_coords"] = len(df_validated)
                coverage_metadata["stations_without_coords"] = len(df) - len(df_validated)
                
                # Verificar criterio de aceptación: ≥200 estaciones
                if len(df_validated) < 200:
                    logger.warning(
                        f"Criterio de aceptación no cumplido: "
                        f"{len(df_validated)} estaciones con coordenadas válidas "
                        f"(requerido: ≥200)"
                    )
                else:
                    logger.info(
                        f"✅ Criterio cumplido: {len(df_validated)} estaciones "
                        f"con coordenadas válidas"
                    )
                
                coverage_metadata["success"] = True
                
                # Guardar datos raw (original completo)
                filepath = self._save_raw_data(
                    data=df,
                    filename="bicing_station_information",
                    format="csv",
                    data_type="movilidad"
                )
                coverage_metadata["filepath"] = str(filepath)
                
                # Retornar DataFrame validado (solo con coordenadas válidas)
                return df_validated, coverage_metadata
            else:
                logger.error("Estructura de respuesta GBFS inesperada")
                coverage_metadata["error"] = "Estructura de respuesta inesperada"
                return None, coverage_metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo estaciones Bicing: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_station_status(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae estado actual de estaciones de Bicing (bicis disponibles, etc.).
        
        Returns:
            Tupla con (DataFrame con estado, metadata).
        """
        logger.info("Extrayendo estado de estaciones Bicing...")
        
        coverage_metadata = {
            "source": "bicing_gbfs",
            "endpoint": "station_status",
            "success": False,
            "total_stations": 0,
        }
        
        try:
            self._rate_limit()
            try:
                response = self.session.get(self.ENDPOINTS["station_status"], timeout=30)
            except Exception as e:
                # Capturar RetryError cuando todos los retries fallan con 503
                error_str = str(e)
                if "503" in error_str or "Service Unavailable" in error_str:
                    logger.warning("API de Bicing temporalmente no disponible (503). Intentar más tarde.")
                    coverage_metadata["error"] = "Service Unavailable (503)"
                    coverage_metadata["suggestion"] = "La API de Bicing está temporalmente caída. Intentar más tarde o usar datos AMB como alternativa."
                    return None, coverage_metadata
                # Re-lanzar otras excepciones
                raise
            
            # Manejar errores 503 (Service Unavailable) de forma más amigable
            if response.status_code == 503:
                logger.warning("API de Bicing temporalmente no disponible (503). Intentar más tarde.")
                coverage_metadata["error"] = "Service Unavailable (503)"
                coverage_metadata["suggestion"] = "La API de Bicing está temporalmente caída. Intentar más tarde o usar datos AMB como alternativa."
                return None, coverage_metadata
            
            if not self._validate_response(response):
                coverage_metadata["error"] = f"Error en respuesta HTTP: {response.status_code}"
                return None, coverage_metadata
            
            data = response.json()
            
            # GBFS estructura: {"data": {"stations": [...]}}
            if "data" in data and "stations" in data["data"]:
                stations = data["data"]["stations"]
                df = pd.DataFrame(stations)
                
                logger.info(f"Estados de estaciones Bicing extraídos: {len(df)}")
                coverage_metadata["success"] = True
                coverage_metadata["total_stations"] = len(df)
                
                # Guardar datos raw
                filepath = self._save_raw_data(
                    data=df,
                    filename="bicing_station_status",
                    format="csv",
                    data_type="movilidad"
                )
                coverage_metadata["filepath"] = str(filepath)
                
                return df, coverage_metadata
            else:
                logger.error("Estructura de respuesta GBFS inesperada")
                coverage_metadata["error"] = "Estructura de respuesta inesperada"
                return None, coverage_metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo estado Bicing: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae toda la información de Bicing (estaciones + estado).
        
        Returns:
            Tupla con (DataFrame combinado, metadata).
        """
        # Extraer información de estaciones
        df_info, meta_info = self.extract_station_information()
        
        # Extraer estado
        df_status, meta_status = self.extract_station_status()
        
        if df_info is None:
            return None, meta_info
        
        # Combinar información y estado
        if df_status is not None and not df_status.empty:
            # Merge por station_id
            if "station_id" in df_info.columns and "station_id" in df_status.columns:
                df_combined = df_info.merge(
                    df_status,
                    on="station_id",
                    how="left",
                    suffixes=("_info", "_status")
                )
            else:
                logger.warning("No se encontró station_id para merge, usando solo información")
                df_combined = df_info
        else:
            df_combined = df_info
        
        combined_metadata = {
            "source": "bicing_gbfs",
            "success": meta_info["success"] and meta_status.get("success", False),
            "total_stations": len(df_combined),
            "has_status": df_status is not None and not df_status.empty,
        }
        
        return df_combined, combined_metadata
    
    def _validate_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida que las coordenadas estén dentro del rango geográfico de Barcelona.
        
        Busca columnas de coordenadas con diferentes nombres posibles y valida
        que estén dentro del rango válido de Barcelona.
        
        Args:
            df: DataFrame con estaciones Bicing.
        
        Returns:
            DataFrame filtrado solo con registros que tienen coordenadas válidas.
        """
        # Buscar columnas de coordenadas (GBFS usa 'lat' y 'lon')
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ["lat", "latitude", "latitud", "coord_y", "y"]:
                lat_col = col
            elif col_lower in ["lon", "longitude", "longitud", "lng", "coord_x", "x"]:
                lon_col = col
        
        if lat_col is None or lon_col is None:
            logger.warning(
                f"No se encontraron columnas de coordenadas. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
            return pd.DataFrame()  # Retornar DataFrame vacío si no hay coordenadas
        
        # Convertir a numérico, forzando errores a NaN
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        
        # Filtrar registros con coordenadas válidas dentro del rango de Barcelona
        mask_valid = (
            df[lat_col].notna() &
            df[lon_col].notna() &
            (df[lat_col] >= BARCELONA_LAT_MIN) &
            (df[lat_col] <= BARCELONA_LAT_MAX) &
            (df[lon_col] >= BARCELONA_LON_MIN) &
            (df[lon_col] <= BARCELONA_LON_MAX)
        )
        
        df_valid = df[mask_valid].copy()
        
        invalid_count = (~mask_valid).sum()
        if invalid_count > 0:
            logger.info(
                f"Validación de coordenadas: {len(df_valid)} válidas, "
                f"{invalid_count} inválidas o fuera de rango"
            )
        
        return df_valid


class ATMExtractor(BaseExtractor):
    """
    Extractor para datos de ATM/AMB (Autoritat del Transport Metropolità / Àrea Metropolitana de Barcelona).
    
    Usa el portal Open Data de la AMB (http://opendata.amb.cat) que es público y no requiere autenticación.
    """
    
    BASE_URL = "http://opendata.amb.cat"
    
    # Colecciones relevantes del portal Open Data AMB
    COLLECTIONS = {
        "infraestructures": f"{BASE_URL}/infraestructures/search",
        "equipaments": f"{BASE_URL}/equipaments/search",
        "estudis_mobilitat": f"{BASE_URL}/estudis/search?tipus_estudi=Mobilitat",
    }
    
    def __init__(
        self,
        rate_limit_delay: float = 2.0,
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor de ATM/AMB.
        
        Args:
            rate_limit_delay: Tiempo de espera entre peticiones.
            output_dir: Directorio donde guardar los datos.
        """
        super().__init__("ATM_AMB", rate_limit_delay, output_dir)
    
    def extract_infrastructures(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae infraestructuras de transporte del portal Open Data AMB.
        
        Returns:
            Tupla con (DataFrame con infraestructuras, metadata).
        """
        logger.info("Extrayendo infraestructuras de transporte de Open Data AMB...")
        
        coverage_metadata = {
            "source": "amb_opendata",
            "collection": "infraestructures",
            "success": False,
        }
        
        try:
            url = self.COLLECTIONS["infraestructures"]
            params = {
                "rows": 500,  # Máximo por página
                "format": "json",
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if not self._validate_response(response):
                coverage_metadata["error"] = "Error en respuesta HTTP"
                return None, coverage_metadata
            
            data = response.json()
            
            # Estructura de respuesta AMB: {"num": X, "count": Y, "items": [...]}
            if "items" in data and isinstance(data["items"], list):
                items = data["items"]
                df = pd.json_normalize(items)
                
                logger.info(f"Infraestructuras extraídas: {len(df)}")
                coverage_metadata["success"] = True
                coverage_metadata["total_records"] = len(df)
                coverage_metadata["total_available"] = data.get("count", len(df))
                
                # Guardar datos raw
                filepath = self._save_raw_data(
                    data=df,
                    filename="amb_infraestructures",
                    format="csv",
                    data_type="movilidad"
                )
                coverage_metadata["filepath"] = str(filepath)
                
                return df, coverage_metadata
            else:
                logger.error("Estructura de respuesta AMB inesperada")
                coverage_metadata["error"] = "Estructura de respuesta inesperada"
                return None, coverage_metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo infraestructuras AMB: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_equipaments(self, filter_type: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae equipamientos (puede incluir estaciones de transporte) del portal Open Data AMB.
        
        Args:
            filter_type: Filtrar por tipo de equipamiento (opcional).
        
        Returns:
            Tupla con (DataFrame con equipamientos, metadata).
        """
        logger.info("Extrayendo equipamientos de Open Data AMB...")
        
        coverage_metadata = {
            "source": "amb_opendata",
            "collection": "equipaments",
            "success": False,
        }
        
        try:
            url = self.COLLECTIONS["equipaments"]
            params = {
                "rows": 500,
                "format": "json",
            }
            
            if filter_type:
                params["subambit"] = filter_type
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if not self._validate_response(response):
                coverage_metadata["error"] = "Error en respuesta HTTP"
                return None, coverage_metadata
            
            data = response.json()
            
            if "items" in data and isinstance(data["items"], list):
                items = data["items"]
                df = pd.json_normalize(items)
                
                logger.info(f"Equipamientos extraídos: {len(df)}")
                coverage_metadata["success"] = True
                coverage_metadata["total_records"] = len(df)
                coverage_metadata["total_available"] = data.get("count", len(df))
                
                # Guardar datos raw
                filepath = self._save_raw_data(
                    data=df,
                    filename=f"amb_equipaments_{filter_type or 'all'}",
                    format="csv",
                    data_type="movilidad"
                )
                coverage_metadata["filepath"] = str(filepath)
                
                return df, coverage_metadata
            else:
                logger.error("Estructura de respuesta AMB inesperada")
                coverage_metadata["error"] = "Estructura de respuesta inesperada"
                return None, coverage_metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo equipamientos AMB: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_mobility_studies(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae estudios de movilidad del portal Open Data AMB.
        
        Returns:
            Tupla con (DataFrame con estudios, metadata).
        """
        logger.info("Extrayendo estudios de movilidad de Open Data AMB...")
        
        coverage_metadata = {
            "source": "amb_opendata",
            "collection": "estudis_mobilitat",
            "success": False,
        }
        
        try:
            url = self.COLLECTIONS["estudis_mobilitat"]
            params = {
                "rows": 500,
                "format": "json",
            }
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            
            if not self._validate_response(response):
                coverage_metadata["error"] = "Error en respuesta HTTP"
                return None, coverage_metadata
            
            data = response.json()
            
            if "items" in data and isinstance(data["items"], list):
                items = data["items"]
                df = pd.json_normalize(items)
                
                logger.info(f"Estudios de movilidad extraídos: {len(df)}")
                coverage_metadata["success"] = True
                coverage_metadata["total_records"] = len(df)
                coverage_metadata["total_available"] = data.get("count", len(df))
                
                # Guardar datos raw
                filepath = self._save_raw_data(
                    data=df,
                    filename="amb_estudis_mobilitat",
                    format="csv",
                    data_type="movilidad"
                )
                coverage_metadata["filepath"] = str(filepath)
                
                return df, coverage_metadata
            else:
                logger.error("Estructura de respuesta AMB inesperada")
                coverage_metadata["error"] = "Estructura de respuesta inesperada"
                return None, coverage_metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo estudios de movilidad AMB: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los datos de transporte/movilidad disponibles del portal AMB.
        
        Returns:
            Tupla con (DataFrame combinado, metadata).
        """
        # Extraer infraestructuras
        df_infra, meta_infra = self.extract_infrastructures()
        
        # Extraer equipamientos (puede incluir estaciones)
        df_equip, meta_equip = self.extract_equipaments()
        
        # Combinar si ambos están disponibles
        dfs = []
        if df_infra is not None and not df_infra.empty:
            df_infra["source_collection"] = "infraestructures"
            dfs.append(df_infra)
        
        if df_equip is not None and not df_equip.empty:
            df_equip["source_collection"] = "equipaments"
            dfs.append(df_equip)
        
        if dfs:
            df_combined = pd.concat(dfs, ignore_index=True)
            
            combined_metadata = {
                "source": "amb_opendata",
                "success": meta_infra.get("success", False) or meta_equip.get("success", False),
                "total_records": len(df_combined),
                "has_infrastructures": df_infra is not None and not df_infra.empty,
                "has_equipaments": df_equip is not None and not df_equip.empty,
            }
            
            return df_combined, combined_metadata
        
        return None, meta_infra

