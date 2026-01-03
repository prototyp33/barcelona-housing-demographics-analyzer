
"""
TMB Extractor Module - Download and process GTFS data from TMB.
"""

import zipfile
import io
import pandas as pd
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import os
from .base import BaseExtractor, logger

class TMBExtractor(BaseExtractor):
    """
    Extractor for TMB (Transports Metropolitans de Barcelona) Static GTFS data.
    """
    
    GTFS_URL = "https://api.tmb.cat/v1/static/datasets/gtfs.zip"
    FALLBACK_URL = "https://opendata-ajuntament.barcelona.cat/data/dataset/e0c34739-823f-470d-8045-e10f28e80f2d/resource/e07dec0d-4aeb-40f3-b987-e1f35e088ce2/download"
    BUS_URL = "https://opendata-ajuntament.barcelona.cat/data/dataset/d395e808-697d-4722-8eb9-b672a8ba0916/resource/2d190658-93ac-4c43-a23f-c5d313b1ae9c/download"
    
    def __init__(self, output_dir: Optional[Path] = None, app_id: Optional[str] = None, app_key: Optional[str] = None):
        super().__init__("TMB", output_dir=output_dir)
        self.app_id = app_id or os.environ.get("TMB_APP_ID")
        self.app_key = app_key or os.environ.get("TMB_APP_KEY")
        
    def extract_gtfs_stops(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Downloads and extracts stops data from TMB GTFS.
        """
        metadata = {
            "source": "tmb_gtfs",
            "success": False,
        }
        
        if not self.app_id or not self.app_key:
            logger.warning("TMB API Keys not found. Falling back to Open Data BCN (CSV).")
            return self._extract_fallback()

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key
        }
        
        logger.info("Downloading TMB GTFS data with API Keys...")
        try:
            response = self.session.get(self.GTFS_URL, params=params, timeout=60)
            if response.status_code == 401:
                logger.error("TMB API Authentication failed (401). Falling back.")
                return self._extract_fallback()
                
            if not self._validate_response(response):
                metadata["error"] = f"HTTP Error {response.status_code}"
                return None, metadata
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open('stops.txt') as f:
                    df_stops = pd.read_csv(f)
            
            logger.info(f"Extracted {len(df_stops)} stops from GTFS.")
            metadata["success"] = True
            metadata["total_stops"] = len(df_stops)
            
            return df_stops, metadata
            
        except Exception as e:
            logger.error(f"Error extracting TMB GTFS: {e}")
            return self._extract_fallback()

    def _extract_fallback(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Fallback to Open Data BCN Transports CSV.
        """
        logger.info("Extracting transport data from Open Data BCN Fallback...")
        metadata = {"source": "opendatabcn_fallback", "success": False}
        try:
            response = self.session.get(self.FALLBACK_URL, timeout=30)
            if self._validate_response(response):
                df = pd.read_csv(io.BytesIO(response.content))
                metadata["success"] = True
                metadata["count"] = len(df)
                return df, metadata
        except Exception as e:
            logger.error(f"Fallback failed: {e}")
        return None, metadata

    def extract_bus_stops(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extracts bus stops from the official Open Data BCN dataset.
        """
        logger.info("Extracting official Barcelona Bus Stops data...")
        metadata = {"source": "opendatabcn_estacions_bus", "success": False}
        try:
            response = self.session.get(self.BUS_URL, timeout=30)
            if self._validate_response(response):
                df = pd.read_csv(io.BytesIO(response.content))
                metadata["success"] = True
                metadata["count"] = len(df)
                
                # Save raw
                self._save_raw_data(df, "barcelona_bus_stops", format="csv", data_type="transport")
                return df, metadata
        except Exception as e:
            logger.error(f"Error extracting bus stops: {e}")
        return None, metadata

    def extract_rail_from_fallback(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extracts Rail/Metro from the official 'transports' dataset.
        """
        df_all, meta = self._extract_fallback()
        if df_all is not None:
            # Filter for all rail-based transport as confirmed by OpenDataBCN
            rail_layers = [
                'Metro i línies urbanes FGC', 
                'Ferrocarrils Generalitat (FGC)', 
                'RENFE', 
                'Tramvia', 
                'Funicular',
                "Tren a l'aeroport",
                'Telefèric'
            ]
            df_rail = df_all[df_all['NOM_CAPA'].isin(rail_layers)].copy()
            meta['rail_count'] = len(df_rail)
            meta['layers_found'] = df_rail['NOM_CAPA'].unique().tolist()
            
            # Save raw rail data
            self._save_raw_data(df_rail, "barcelona_rail_stops", format="csv", data_type="transport")
            return df_rail, meta
        return None, meta

    def extract_all(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
        """
        Combined extraction from official sources.
        Returns a dictionary of DataFrames.
        """
        logger.info("Starting multi-modal transit extraction (TMB/BCN)...")
        df_bus, meta_bus = self.extract_bus_stops()
        df_rail, meta_rail = self.extract_rail_from_fallback()
        
        results = {}
        if df_bus is not None:
            results["bus_stops"] = df_bus
        if df_rail is not None:
            results["rail_stops"] = df_rail
            
        metadata = {
            "bus": meta_bus,
            "rail": meta_rail,
            "success": len(results) > 0
        }
        
        return results, metadata
