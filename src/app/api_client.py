"""
API Client for the Barcelona Housing Streamlit Dashboard.
Connects to the FastAPI backend to fetch predictions, recommendations, and metrics.
"""

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

class ApiClient:
    """Client to interact with the Barcelona Housing API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._session = None
        self._api_available = None  # Cache del estado de la API
    
    def _get_session(self) -> requests.Session:
        """Obtiene o crea una sesión HTTP cacheada."""
        if self._session is None:
            self._session = requests.Session()
            # Configurar timeouts por defecto
            self._session.timeout = 2.0
        return self._session
    
    def _get(self, endpoint: str, params: Optional[Dict] = None, timeout: float = 2.0) -> Any:
        """
        Helper for GET requests con manejo robusto de errores.
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de query
            timeout: Timeout en segundos (default: 2.0)
        
        Returns:
            JSON response o None si hay error
        """
        # Si ya sabemos que la API no está disponible, no intentar
        if self._api_available is False:
            return None
            
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            session = self._get_session()
            response = session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            # Si llegamos aquí, la API está disponible
            self._api_available = True
            return response.json()
        except ConnectionError as e:
            # API no disponible - loguear solo en debug para evitar spam
            logger.debug(f"API no disponible (GET {endpoint}): {e}")
            self._api_available = False
            return None
        except Timeout as e:
            logger.debug(f"API timeout (GET {endpoint}): {e}")
            return None
        except RequestException as e:
            # Otros errores HTTP (4xx, 5xx) - loguear como warning
            logger.warning(f"API request error (GET {endpoint}): {e}")
            return None
        except Exception as e:
            # Errores inesperados - loguear como error
            logger.error(f"API error inesperado (GET {endpoint}): {e}", exc_info=True)
            return None
            
    def _post(self, endpoint: str, data: Dict, timeout: float = 2.0) -> Any:
        """
        Helper for POST requests con manejo robusto de errores.
        
        Args:
            endpoint: Endpoint de la API
            data: Datos JSON para enviar
            timeout: Timeout en segundos (default: 2.0)
        
        Returns:
            JSON response o None si hay error
        """
        # Si ya sabemos que la API no está disponible, no intentar
        if self._api_available is False:
            return None
            
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            session = self._get_session()
            response = session.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            # Si llegamos aquí, la API está disponible
            self._api_available = True
            return response.json()
        except ConnectionError as e:
            # API no disponible - loguear solo en debug para evitar spam
            logger.debug(f"API no disponible (POST {endpoint}): {e}")
            self._api_available = False
            return None
        except Timeout as e:
            logger.debug(f"API timeout (POST {endpoint}): {e}")
            return None
        except RequestException as e:
            # Otros errores HTTP (4xx, 5xx) - loguear como warning
            logger.warning(f"API request error (POST {endpoint}): {e}")
            return None
        except Exception as e:
            # Errores inesperados - loguear como error
            logger.error(f"API error inesperado (POST {endpoint}): {e}", exc_info=True)
            return None
    
    def check_health(self) -> bool:
        """
        Verifica si la API está disponible.
        
        Returns:
            True si la API está disponible, False en caso contrario
        """
        if self._api_available is False:
            return False
            
        try:
            health = self.get_health()
            is_available = health is not None and bool(health)
            self._api_available = is_available
            return is_available
        except Exception:
            self._api_available = False
            return False

    def get_health(self) -> Dict:
        """
        Check API health endpoint.
        
        Returns:
            Dict con información de salud de la API o {} si no está disponible
        """
        return self._get("health") or {}

    def get_barrios(self, distrito: Optional[str] = None, include_geometry: bool = False) -> List[Dict]:
        """Get list of neighborhoods."""
        params = {"include_geometry": include_geometry}
        if distrito:
            params["distrito"] = distrito
        return self._get("barrios/", params=params) or []

    def get_barrio_detail(self, barrio_id: int) -> Dict:
        """Get full neighborhood info."""
        return self._get(f"barrios/{barrio_id}") or {}

    def get_prediction(self, barrio_id: int) -> Dict:
        """Get price prediction for a neighborhood."""
        return self._post("predictions/", data={"barrio_id": barrio_id}) or {}

    def get_investment_recommendations(self, budget: float, strategy: str = "yield", max_results: int = 5) -> Dict:
        """Get investment simulator results."""
        data = {
            "budget": budget,
            "strategy": strategy,
            "max_results": max_results
        }
        return self._post("investment/recommend", data=data) or {}

    def get_clusters(self) -> Dict[str, Dict]:
        """Get neighborhood segmentation data."""
        return self._get("clusters/") or {}

    def get_years(self) -> Dict[str, Dict[str, int]]:
        """Get available years for fact tables."""
        return self._get("stats/years") or {}

    def get_distritos(self) -> List[str]:
        """Get list of unique distritos."""
        return self._get("stats/distritos") or []

    def get_precios(self, year: int, distrito: Optional[str] = None, include_geometry: bool = False) -> List[Dict]:
        """Get prices for a given year and district."""
        params = {"year": year, "include_geometry": include_geometry}
        if distrito:
            params["distrito"] = distrito
        return self._get("stats/precios", params=params) or []

    def get_renta(self, year: int) -> List[Dict]:
        """Get income data for a given year."""
        return self._get("stats/renta", params={"year": year}) or []

    def get_api_kpis(self) -> Dict:
        """Get global project KPIs from API."""
        return self._get("stats/kpis") or {}

    def get_investment_stats(self, year: int) -> List[Dict]:
        """Get specialized investment metrics from API."""
        return self._get("stats/investment", params={"year": year}) or []

    def get_accessibility_metrics(self, year: int, distrito: Optional[str] = None) -> List[Dict]:
        """Get social infrastructure accessibility metrics."""
        params = {"year": year}
        if distrito:
            params["distrito"] = distrito
        return self._get("accessibility/", params=params) or []

    def get_safety_metrics(self, year: int, distrito: Optional[str] = None) -> List[Dict]:
        """Get safety and tourism metrics."""
        params = {"year": year}
        if distrito:
            params["distrito"] = distrito
        return self._get("accessibility/safety", params=params) or []

    def get_equity_metrics(self) -> List[Dict]:
        """Get model fairness and equity metrics."""
        return self._get("equity/") or []

# Global client singleton
@st.cache_resource
def get_api_client(base_url: Optional[str] = None):
    """
    Obtiene el cliente API singleton.
    
    Args:
        base_url: URL base de la API. Si es None, usa el default o de secrets.
    
    Returns:
        Instancia de ApiClient
    """
    if base_url is None:
        # Intentar obtener de secrets, si no usar default
        try:
            if hasattr(st, 'secrets') and 'api' in st.secrets and 'base_url' in st.secrets.api:
                base_url = st.secrets.api.base_url
        except Exception:
            pass
        
        if base_url is None:
            base_url = "http://localhost:8000"
    
    return ApiClient(base_url=base_url)


def check_api_availability() -> bool:
    """
    Verifica si la API está disponible usando session_state para evitar checks repetidos.
    
    Returns:
        True si la API está disponible, False en caso contrario
    """
    # Usar session_state para cachear el resultado del health check
    if 'api_available' not in st.session_state:
        try:
            client = get_api_client()
            st.session_state['api_available'] = client.check_health()
        except Exception:
            st.session_state['api_available'] = False
    
    return st.session_state.get('api_available', False)
