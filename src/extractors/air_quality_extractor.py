"""
Air Quality Extractor - Phase 2
Source: ASPB (Agència de Salut Pública de Barcelona) stations
"""
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from src.extraction.base import BaseExtractor, logger

class AirQualityExtractor(BaseExtractor):
    """
    Extractor for air quality data from ASPB monitoring stations.
    Pollutants: NO2, PM2.5, PM10, O3.
    """
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Any] = None):
        super().__init__("AirQuality", rate_limit_delay, output_dir)

    def extract(self, year: int) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extract air quality sensor data for a specific year.
        """
        logger.info(f"Extracting air quality data for year {year}")
        # Implementation details will be added in ETL phase
        return None, {}

