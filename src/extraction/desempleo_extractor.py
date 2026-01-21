"""
Extractor para datos de desempleo (atur registrat) de Open Data BCN.

Fuentes:
- Atur registrat per barri: Open Data BCN

URLs:
- Dataset principal: https://opendata-ajuntament.barcelona.cat/data/es/dataset/atur
- API CKAN: https://opendata-ajuntament.barcelona.cat/data/api/3/action/package_show?id=atur

Autor: Barcelona Housing Demographics Analyzer
Fecha: 2026-01-05
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger
from .opendata import OpenDataBCNExtractor


class DesempleoExtractor(BaseExtractor):
    """Extractor para datos de desempleo (atur registrat) de Open Data BCN.
    
    Extrae:
    - Número de desempleados por barrio y mes
    - Tasa de desempleo estimada
    - Series temporales mensuales
    
    El dataset de Open Data BCN proporciona datos mensuales de desempleo
    registrado por barrio de Barcelona.
    """
    
    # IDs de datasets conocidos en Open Data BCN
    DATASET_IDS = [
        'atur',
        'atur-registrat',
        'atur-barri',
        'desempleo',
        'desempleo-barrio'
    ]
    
    # Palabras clave para identificar datasets de desempleo
    KEYWORDS = [
        'atur',
        'desempleo',
        'desocupación',
        'paro',
        'unemployment'
    ]
    
    def __init__(
        self,
        rate_limit_delay: float = 1.5,
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor de desempleo.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 1.5).
            output_dir: Directorio donde guardar los datos descargados.
        """
        # Guardamos bajo el namespace de OpenDataBCN para mantener consistencia en data/raw/opendatabcn/
        super().__init__("OpenDataBCN", rate_limit_delay=rate_limit_delay, output_dir=output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(
            rate_limit_delay=rate_limit_delay,
            output_dir=output_dir
        )
    
    def extract_atur_registrat(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Extrae datos de atur registrat (desempleo registrado) de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de desempleo, metadata).
        """
        logger.info("Extrayendo datos de atur registrat de Open Data BCN...")
        
        # Intentar con diferentes IDs de dataset
        for dataset_id in self.DATASET_IDS:
            try:
                logger.info(f"Intentando con dataset_id: {dataset_id}")
                df, metadata = self.opendata_extractor.download_dataset(
                    dataset_id=dataset_id,
                    resource_format='csv'
                )
                
                if df is not None and not df.empty:
                    # Validar que sea un dataset de desempleo
                    if self._is_desempleo_dataset(df, dataset_id):
                        logger.info(f"✓ Dataset de desempleo encontrado: {dataset_id}")
                        logger.info(f"  Registros: {len(df):,}")
                        logger.info(f"  Columnas: {list(df.columns)}")
                        
                        # Normalizar columnas
                        df = self._normalize_columns(df)
                        
                        # Validar y limpiar datos
                        df = self._validate_and_clean(df)
                        
                        return df, metadata
                    else:
                        logger.warning(f"Dataset {dataset_id} no parece ser de desempleo")
                        
            except Exception as e:
                logger.warning(f"Error al extraer dataset {dataset_id}: {e}")
                continue
        
        # Si no se encontró ningún dataset, buscar por palabras clave
        logger.info("Buscando datasets de desempleo por palabras clave...")
        
        try:
            dataset_ids = self.opendata_extractor.search_datasets_by_keyword(
                keyword='atur',
                limit=10
            )
            
            if dataset_ids:
                logger.info(f"Encontrados {len(dataset_ids)} datasets potenciales")
                for dataset_id in dataset_ids[:3]:  # Intentar con los primeros 3
                    try:
                        logger.info(f"Intentando con: {dataset_id}")
                        
                        df, metadata = self.opendata_extractor.download_dataset(
                            dataset_id=dataset_id,
                            resource_format='csv'
                        )
                        
                        if df is not None and not df.empty and self._is_desempleo_dataset(df, dataset_id):
                            df = self._normalize_columns(df)
                            df = self._validate_and_clean(df)
                            return df, metadata
                            
                    except Exception as e:
                        logger.warning(f"Error: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error en búsqueda por palabras clave: {e}")
        
        logger.error("No se pudo encontrar ningún dataset de desempleo válido")
        return pd.DataFrame(), {}
    
    def extract_all(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Extrae todos los datos de desempleo disponibles.
        
        Returns:
            Tupla con (DataFrame con datos de desempleo, metadata).
        """
        return self.extract_atur_registrat()
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas del dataset de desempleo.
        
        Args:
            df: DataFrame con columnas originales.
        
        Returns:
            DataFrame con columnas normalizadas.
        """
        logger.info("Normalizando columnas...")
        
        # Mapeo de nombres de columnas comunes
        column_mapping = {
            # Barrio
            'barri': 'barrio_nombre',
            'nom_barri': 'barrio_nombre',
            'barrio': 'barrio_nombre',
            'neighbourhood': 'barrio_nombre',
            
            # Distrito
            'districte': 'distrito_nombre',
            'nom_districte': 'distrito_nombre',
            'distrito': 'distrito_nombre',
            
            # Año
            'any': 'anio',
            'año': 'anio',
            'year': 'anio',
            
            # Mes
            'mes': 'mes',
            'month': 'mes',
            
            # Desempleo
            'atur': 'num_desempleados',
            'atur_registrat': 'num_desempleados',
            'desempleados': 'num_desempleados',
            'parados': 'num_desempleados',
            'unemployed': 'num_desempleados',
            'numero_aturats': 'num_desempleados',
            'num_aturats': 'num_desempleados',
            
            # Tasa
            'tasa_atur': 'tasa_desempleo',
            'tasa_paro': 'tasa_desempleo',
            'taxa_atur': 'tasa_desempleo',
            'unemployment_rate': 'tasa_desempleo',
        }
        
        # Normalizar nombres (case-insensitive)
        df_normalized = df.copy()
        df_normalized.columns = df_normalized.columns.str.lower().str.strip()
        
        # Aplicar mapeo
        df_normalized = df_normalized.rename(columns=column_mapping)
        
        logger.info(f"Columnas después de normalización: {list(df_normalized.columns)}")
        
        return df_normalized
    
    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y limpia los datos de desempleo.
        
        Args:
            df: DataFrame a validar y limpiar.
        
        Returns:
            DataFrame limpio y validado.
        """
        logger.info("Validando y limpiando datos...")
        
        initial_count = len(df)
        
        # 1. Verificar columnas requeridas
        required_cols = ['barrio_nombre']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"Faltan columnas requeridas: {missing_cols}")
            logger.info(f"Columnas disponibles: {list(df.columns)}")
        
        # 2. Eliminar filas sin barrio
        if 'barrio_nombre' in df.columns:
            df = df[df['barrio_nombre'].notna()]
            df = df[df['barrio_nombre'] != '']
            logger.info(f"Registros después de filtrar barrios vacíos: {len(df)}")
        
        # 3. Convertir tipos de datos
        if 'anio' in df.columns:
            df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
            df = df[df['anio'].notna()]
            df['anio'] = df['anio'].astype(int)
        
        if 'mes' in df.columns:
            df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
            df = df[df['mes'].notna()]
            df['mes'] = df['mes'].astype(int)
            # Validar rango de meses (1-12)
            df = df[(df['mes'] >= 1) & (df['mes'] <= 12)]
        
        if 'num_desempleados' in df.columns:
            df['num_desempleados'] = pd.to_numeric(df['num_desempleados'], errors='coerce')
            df = df[df['num_desempleados'].notna()]
            df['num_desempleados'] = df['num_desempleados'].astype(int)
            # Validar que no sea negativo
            df = df[df['num_desempleados'] >= 0]
        
        if 'tasa_desempleo' in df.columns:
            df['tasa_desempleo'] = pd.to_numeric(df['tasa_desempleo'], errors='coerce')
            # Validar rango (0-100%)
            df.loc[df['tasa_desempleo'] > 100, 'tasa_desempleo'] = None
            df.loc[df['tasa_desempleo'] < 0, 'tasa_desempleo'] = None
        
        # 4. Normalizar nombres de barrios
        if 'barrio_nombre' in df.columns:
            df['barrio_nombre'] = df['barrio_nombre'].str.strip()
            df['barrio_nombre'] = df['barrio_nombre'].str.replace('  ', ' ')
        
        # 5. Añadir timestamp de extracción
        df['etl_loaded_at'] = datetime.now().isoformat()
        
        # 6. Eliminar duplicados
        if 'anio' in df.columns and 'mes' in df.columns and 'barrio_nombre' in df.columns:
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['barrio_nombre', 'anio', 'mes'], keep='last')
            if before_dedup > len(df):
                logger.info(f"Eliminados {before_dedup - len(df)} duplicados")
        
        final_count = len(df)
        logger.info(f"Registros finales: {final_count:,} (de {initial_count:,} iniciales)")
        
        if final_count < initial_count * 0.5:
            logger.warning(f"Se perdió más del 50% de los datos durante la limpieza")
        
        return df
    
    def _is_desempleo_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de desempleo.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de desempleo.
        """
        # Verificar ID del dataset
        if any(keyword in dataset_id.lower() for keyword in self.KEYWORDS):
            logger.info(f"Dataset ID contiene palabra clave de desempleo: {dataset_id}")
            return True
        
        # Verificar nombres de columnas
        column_names = ' '.join(df.columns.str.lower())
        
        desempleo_indicators = [
            'atur',
            'desempleo',
            'desocupación',
            'paro',
            'unemployed'
        ]
        
        if any(indicator in column_names for indicator in desempleo_indicators):
            logger.info("Columnas contienen indicadores de desempleo")
            return True
        
        # Verificar si tiene estructura temporal (año/mes)
        has_temporal = any(col in column_names for col in ['any', 'año', 'year', 'mes', 'month'])
        
        # Verificar si tiene información geográfica
        has_geo = any(col in column_names for col in ['barri', 'barrio', 'neighbourhood', 'districte', 'distrito'])
        
        if has_temporal and has_geo:
            logger.info("Dataset tiene estructura temporal y geográfica")
            return True
        
        logger.warning(f"Dataset {dataset_id} no parece ser de desempleo")
        logger.warning(f"Columnas: {list(df.columns)}")
        
        return False


def main():
    """Función principal para testing."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear extractor
    extractor = DesempleoExtractor()
    
    # Extraer datos
    df, metadata = extractor.extract_all()
    
    if not df.empty:
        print("\n" + "=" * 80)
        print("DATOS DE DESEMPLEO EXTRAÍDOS")
        print("=" * 80)
        print(f"\nRegistros: {len(df):,}")
        print(f"\nColumnas: {list(df.columns)}")
        print(f"\nPrimeras filas:")
        print(df.head(10))
        
        if 'anio' in df.columns:
            print(f"\nAños disponibles: {sorted(df['anio'].unique())}")
        
        if 'barrio_nombre' in df.columns:
            print(f"\nBarrios únicos: {df['barrio_nombre'].nunique()}")
            print(f"Barrios: {sorted(df['barrio_nombre'].unique())[:10]}...")
        
        print("\n" + "=" * 80)
    else:
        print("\n❌ No se pudieron extraer datos de desempleo")


if __name__ == "__main__":
    import logging
    main()
