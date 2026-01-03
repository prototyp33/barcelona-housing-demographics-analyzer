
"""
OSM Extractor Module - Query OpenStreetMap data via Overpass API.
"""

import pandas as pd
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
from .base import BaseExtractor, logger

class OSMExtractor(BaseExtractor):
    """
    Extractor for OpenStreetMap features using Overpass API.
    """
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Bounding box for Barcelona city roughly
    BCN_BBOX = "41.32,2.05,41.48,2.23"
    
    def __init__(self, output_dir: Optional[Path] = None):
        super().__init__("OSM", output_dir=output_dir)
        
    def query_amenities(self, amenity_types: List[str]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Queries OSM for specific amenities in Barcelona.
        """
        amenity_str = "|".join(amenity_types)
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"{amenity_str}"]({self.BCN_BBOX});
          way["amenity"~"{amenity_str}"]({self.BCN_BBOX});
          relation["amenity"~"{amenity_str}"]({self.BCN_BBOX});
        );
        out body;
        >;
        out skel qt;
        """
        
        logger.info(f"Querying Overpass for amenities: {amenity_types}...")
        
        metadata = {
            "source": "osm_overpass",
            "amenities": amenity_types,
            "success": False,
        }
        
        try:
            response = self.session.post(self.OVERPASS_URL, data={'data': query}, timeout=60)
            if not self._validate_response(response):
                metadata["error"] = f"HTTP Error {response.status_code}"
                return None, metadata
            
            data = response.json()
            elements = data.get('elements', [])
            
            # Simple conversion to DataFrame
            # Extract tags and coordinates
            processed = []
            for el in elements:
                if 'tags' in el:
                    item = el['tags']
                    item['id'] = el['id']
                    item['type'] = el['type']
                    item['lat'] = el.get('lat') or (el.get('center', {}).get('lat'))
                    item['lon'] = el.get('lon') or (el.get('center', {}).get('lon'))
                    if item['lat'] and item['lon']:
                        processed.append(item)
            
            df = pd.DataFrame(processed)
            logger.info(f"Retrieved {len(df)} OSM features.")
            
            metadata["success"] = True
            metadata["count"] = len(df)
            
            filepath = self._save_raw_data(
                data=df,
                filename=f"osm_amenities_{amenity_types[0]}",
                format="csv",
                data_type="vibrancy"
            )
            metadata["filepath"] = str(filepath)
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error querying Overpass: {e}")
            metadata["error"] = str(e)
            return None, metadata

    def query_transport(self, transport_types: List[str] = ["bus_stop", "subway_entrance", "train_station"]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Queries OSM for public transport stops.
        """
        # Map simple terms to OSM keys/values
        mapping = {
            "bus_stop": 'node["highway"="bus_stop"]',
            "subway_entrance": 'node["railway"="subway_entrance"]',
            "train_station": 'node["railway"="station"]'
        }
        
        clauses = []
        for t in transport_types:
            if t in mapping:
                clauses.append(f'{mapping[t]}({self.BCN_BBOX});')
        
        query = f"""
        [out:json][timeout:25];
        (
          {"".join(clauses)}
        );
        out body;
        >;
        out skel qt;
        """
        
        logger.info(f"Querying Overpass for transport: {transport_types}...")
        
        metadata = {
            "source": "osm_overpass_transport",
            "types": transport_types,
            "success": False,
        }
        
        try:
            response = self.session.post(self.OVERPASS_URL, data={'data': query}, timeout=60)
            if not self._validate_response(response):
                metadata["error"] = f"HTTP Error {response.status_code}"
                return None, metadata
            
            data = response.json()
            elements = data.get('elements', [])
            
            processed = []
            for el in elements:
                if 'tags' in el:
                    item = el['tags']
                    item['lat'] = el.get('lat')
                    item['lon'] = el.get('lon')
                    item['osm_id'] = el['id']
                    if item['lat'] and item['lon']:
                        processed.append(item)
            
            df = pd.DataFrame(processed)
            logger.info(f"Retrieved {len(df)} transport nodes.")
            
            metadata["success"] = True
            metadata["count"] = len(df)
            
            filepath = self._save_raw_data(
                data=df,
                filename="osm_transport_stops",
                format="csv",
                data_type="transport"
            )
            metadata["filepath"] = str(filepath)
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error querying Overpass transport: {e}")
            metadata["error"] = str(e)
            return None, metadata

    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        # Default sanity check: basic essential services
        return self.query_amenities(["pharmacy", "supermarket", "school"])
