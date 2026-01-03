"""
API Client for the Barcelona Housing Streamlit Dashboard.
Connects to the FastAPI backend to fetch predictions, recommendations, and metrics.
"""

import requests
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

class ApiClient:
    """Client to interact with the Barcelona Housing API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Helper for GET requests."""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Error (GET {endpoint}): {e}")
            return None
            
    def _post(self, endpoint: str, data: Dict) -> Any:
        """Helper for POST requests."""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Error (POST {endpoint}): {e}")
            return None

    def get_health(self) -> Dict:
        """Check API sanity."""
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

# Global client singleton
@st.cache_resource
def get_api_client():
    return ApiClient()
