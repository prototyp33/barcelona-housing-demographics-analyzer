"""
Gencat Extractor Module - Extracción de datos de la Generalitat de Catalunya.

Proporciona acceso a las APIs de Socrata (analisi.transparenciacatalunya.cat)
para indicadores de vivienda, demanda y ayudas.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

from .base import BaseExtractor, logger

class GencatExtractor(BaseExtractor):
    """
    Extractor para datos del Portal de Dades Obertes de la Generalitat.
    """
    
    BASE_URL = "https://analisi.transparenciacatalunya.cat/resource"
    
    # IDs de datasets Socrata
    DATASETS = {
        "demanda_vpo": "jtbt-v6ub",  # Solicitantes de vivienda protegida
        "viviendas_vacias": "vqqv-szjk", # Registro viviendas vacías
        "ayudas_alquiler": "vbp2-ryij", # Ayudas alquiler
    }
    
    def __init__(self, rate_limit_delay: float = 1.0, output_dir: Optional[Path] = None):
        super().__init__("Gencat", rate_limit_delay, output_dir)
        
    def download_socrata(self, dataset_id: str, query: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Descarga datos de una API Socrata."""
        url = f"{self.BASE_URL}/{dataset_id}.json"
        
        # Filtrar por Barcelona municipio si es posible (id_municipi=08019)
        params = {"$limit": 50000}
        if query:
            params.update({"$where": query})
        else:
            # Por defecto intentar filtrar por Barcelona
            params.update({"$where": "codi_municipi='08019' OR municipi_nom='Barcelona'"})
            
        logger.info(f"Descargando Gencat Socrata: {dataset_id}")
        
        try:
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=60)
            if not self._validate_response(response):
                return pd.DataFrame(), {"success": False}
                
            data = response.json()
            df = pd.DataFrame(data)
            
            if not df.empty:
                # Guardar raw
                self._save_raw_data(
                    df, 
                    f"gencat_{dataset_id}", 
                    'csv',
                    data_type="vivienda_publica"
                )
                
            return df, {"success": True, "records": len(df)}
            
        except Exception as e:
            logger.error(f"Error descargando {dataset_id}: {e}")
            return pd.DataFrame(), {"success": False, "error": str(e)}

    def extract_all_housing(self) -> Dict[str, Any]:
        """Extrae todos los indicadores de vivienda de Gencat."""
        results = {}
        for name, ds_id in self.DATASETS.items():
            df, meta = self.download_socrata(ds_id)
            results[name] = {"success": meta["success"], "records": len(df)}
        return results

