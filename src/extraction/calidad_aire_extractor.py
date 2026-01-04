"""
Extractor de datos de Calidad del Aire para Barcelona.

Fuentes:
1. Open Data BCN - Estaciones de medición de calidad del aire
2. Open Data BCN - Mediciones horarias/diarias de contaminantes
3. Gencat - Datos de la Xarxa de Vigilància i Previsió de la Contaminació Atmosfèrica (XVPCA)

Contaminantes principales:
- NO2 (Dióxido de nitrógeno)
- PM10 (Partículas en suspensión <10μm)
- PM2.5 (Partículas en suspensión <2.5μm)
- O3 (Ozono)
- SO2 (Dióxido de azufre)
"""

import logging
import pandas as pd
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CalidadAireExtractor:
    """Extractor para datos de calidad del aire en Barcelona."""
    
    # URLs de Open Data BCN
    CKAN_BASE = "https://opendata-ajuntament.barcelona.cat/data/api/3/action"
    
    # Datasets relevantes
    DATASETS = {
        "estaciones": "9d4c5915-0c83-4f06-9f3e-cd424e6ecb8c",  # Estaciones de medición
        "mediciones_horarias": "4f0d-f0f8-4a0b-b5e5-2e3c1d8f9a0b",  # Placeholder - verificar ID real
    }
    
    # Límites de la OMS y UE para calidad del aire
    LIMITES_OMS = {
        "NO2": {"anual": 10, "diario": 25},  # μg/m³
        "PM10": {"anual": 15, "diario": 45},
        "PM2.5": {"anual": 5, "diario": 15},
        "O3": {"8h": 100},  # Máximo de 8 horas
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Inicializa el extractor de calidad del aire.
        
        Args:
            data_dir: Directorio donde guardar los archivos descargados.
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "raw" / "calidad_aire"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CalidadAireExtractor inicializado. Directorio: {self.data_dir}")
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict]:
        """Obtiene información de un dataset de CKAN."""
        try:
            url = f"{self.CKAN_BASE}/package_show"
            response = requests.get(url, params={"id": dataset_id}, timeout=30)
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            logger.error(f"Error obteniendo info del dataset {dataset_id}: {e}")
            return None
    
    def search_datasets(self, query: str) -> List[Dict]:
        """Busca datasets relacionados con calidad del aire."""
        try:
            url = f"{self.CKAN_BASE}/package_search"
            response = requests.get(
                url,
                params={"q": query, "rows": 20},
                timeout=30
            )
            response.raise_for_status()
            results = response.json()["result"]["results"]
            
            logger.info(f"Encontrados {len(results)} datasets para '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error buscando datasets: {e}")
            return []
    
    def extract_estaciones(self) -> pd.DataFrame:
        """
        Extrae información de las estaciones de medición de calidad del aire.
        
        Returns:
            DataFrame con estaciones y su ubicación
        """
        logger.info("Buscando datasets de estaciones de calidad del aire...")
        
        # Buscar datasets relevantes
        datasets = self.search_datasets("qualitat aire estacions")
        
        if not datasets:
            logger.warning("No se encontraron datasets de estaciones")
            return pd.DataFrame()
        
        # Mostrar datasets encontrados
        logger.info(f"\nDatasets encontrados:")
        for i, ds in enumerate(datasets[:5]):
            logger.info(f"  {i+1}. {ds['title']} (ID: {ds['id']})")
        
        # TODO: Descargar y procesar el dataset correcto
        # Por ahora retornamos vacío hasta identificar el dataset exacto
        
        return pd.DataFrame()
    
    def extract_mediciones_agregadas(
        self,
        year: int,
        contaminantes: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Extrae mediciones agregadas por barrio y año.
        
        Args:
            year: Año a extraer
            contaminantes: Lista de contaminantes (NO2, PM10, PM2.5, O3)
                          Si None, extrae todos
        
        Returns:
            DataFrame con mediciones agregadas por barrio
        """
        if contaminantes is None:
            contaminantes = ["NO2", "PM10", "PM2.5", "O3"]
        
        logger.info(f"Extrayendo mediciones de {year} para {contaminantes}")
        
        # Buscar datasets de mediciones
        datasets = self.search_datasets(f"qualitat aire {year}")
        
        if not datasets:
            logger.warning(f"No se encontraron datos para {year}")
            return pd.DataFrame()
        
        # TODO: Implementar extracción real cuando se identifiquen los datasets
        
        return pd.DataFrame()
    
    def calcular_indice_calidad(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula un índice de calidad del aire basado en múltiples contaminantes.
        
        Metodología:
        - Compara cada contaminante con límites OMS
        - Calcula % de excedencia
        - Genera índice compuesto (0-100, donde 100 es excelente)
        
        Args:
            df: DataFrame con columnas de contaminantes
        
        Returns:
            DataFrame con columna 'indice_calidad_aire' añadida
        """
        if df.empty:
            return df
        
        # Calcular excedencias respecto a límites OMS
        scores = []
        
        for contaminante, limites in self.LIMITES_OMS.items():
            col_name = f"{contaminante}_promedio_anual"
            if col_name in df.columns:
                limite = limites.get("anual", limites.get("diario", 100))
                # Score: 100 si está por debajo del límite, decrece linealmente
                score = 100 * (1 - (df[col_name] / limite).clip(0, 2))
                scores.append(score)
        
        if scores:
            df["indice_calidad_aire"] = sum(scores) / len(scores)
            df["categoria_calidad"] = pd.cut(
                df["indice_calidad_aire"],
                bins=[0, 25, 50, 75, 100],
                labels=["Mala", "Regular", "Buena", "Excelente"]
            )
        
        return df
    
    def extract_all(self, year: int = 2024) -> Dict[str, pd.DataFrame]:
        """
        Extrae todos los datos de calidad del aire disponibles.
        
        Args:
            year: Año a extraer
        
        Returns:
            Diccionario con DataFrames de estaciones y mediciones
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Extrayendo datos de calidad del aire para {year}")
        logger.info(f"{'='*60}")
        
        results = {}
        
        # Estaciones
        logger.info("\n1. Extrayendo estaciones...")
        results["estaciones"] = self.extract_estaciones()
        
        # Mediciones
        logger.info("\n2. Extrayendo mediciones...")
        results["mediciones"] = self.extract_mediciones_agregadas(year)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Extracción completada")
        logger.info(f"{'='*60}")
        
        return results


def main():
    """Función principal para pruebas."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    extractor = CalidadAireExtractor()
    
    # Buscar datasets disponibles
    print("\n" + "="*60)
    print("BÚSQUEDA DE DATASETS DE CALIDAD DEL AIRE")
    print("="*60)
    
    queries = [
        "qualitat aire",
        "contaminación",
        "NO2",
        "PM10",
        "estacions mesura"
    ]
    
    for query in queries:
        print(f"\n🔍 Buscando: '{query}'")
        datasets = extractor.search_datasets(query)
        
        if datasets:
            print(f"   Encontrados: {len(datasets)} datasets")
            for i, ds in enumerate(datasets[:3]):
                print(f"   {i+1}. {ds['title']}")
                print(f"      ID: {ds['id']}")
                if 'resources' in ds and ds['resources']:
                    print(f"      Recursos: {len(ds['resources'])}")
        else:
            print("   No se encontraron datasets")
    
    # Intentar extracción
    print("\n" + "="*60)
    print("INTENTANDO EXTRACCIÓN")
    print("="*60)
    
    results = extractor.extract_all(2024)
    
    for key, df in results.items():
        print(f"\n{key}:")
        print(f"  Registros: {len(df)}")
        if not df.empty:
            print(f"  Columnas: {df.columns.tolist()}")


if __name__ == "__main__":
    main()
