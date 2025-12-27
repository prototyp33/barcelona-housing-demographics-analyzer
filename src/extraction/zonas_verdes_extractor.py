"""
Extractor para datos de zonas verdes y arbolado de Open Data BCN.

Fuentes:
- Parques y jardines: Open Data BCN
- Arbolado: Open Data BCN

URLs:
- Parques: https://opendata-ajuntament.barcelona.cat/data/es/dataset/parcs-i-jardins
- Arbolado: https://opendata-ajuntament.barcelona.cat/data/es/dataset/arbres
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger
from .opendata import OpenDataBCNExtractor

# Rango válido de coordenadas para Barcelona
BARCELONA_LAT_MIN = 41.35
BARCELONA_LAT_MAX = 41.45
BARCELONA_LON_MIN = 2.05
BARCELONA_LON_MAX = 2.25


class ZonasVerdesExtractor(BaseExtractor):
    """
    Extractor para datos de zonas verdes (parques y jardines) y arbolado de Open Data BCN.
    
    Extrae:
    - Parques y jardines con superficie (m²)
    - Arbolado con ubicación geográfica
    - Calcula métricas por barrio
    """
    
    # IDs potenciales de datasets de zonas verdes en Open Data BCN
    PARQUES_DATASET_IDS = [
        "parcs-i-jardins",
        "parques-jardines",
        "parcs-jardins",
        "parques",
        "jardines",
        "zones-verdes",
        "zonas-verdes",
    ]
    
    ARBOLADO_DATASET_IDS = [
        "arbres",
        "arbolado",
        "trees",
        "arboles",
        "arbrat",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de zonas verdes.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 1.5).
            output_dir: Directorio donde guardar los datos descargados.
        """
        super().__init__("ZonasVerdes", rate_limit_delay, output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(
            rate_limit_delay=rate_limit_delay,
            output_dir=output_dir
        )
    
    def extract_parques_jardines(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de parques y jardines de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de parques/jardines, metadata).
        """
        logger.info("=== Extrayendo datos de parques y jardines ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_parques": 0,
            "parques_with_valid_coords": 0,
            "parques_without_coords": 0,
            "total_superficie_m2": 0.0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["parc", "jardi"]  # Reducir a palabras clave más específicas
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.PARQUES_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de parques y jardines
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de parques/jardines
                        if not self._is_parques_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de parques/jardines, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Normalizar columnas
                        df = self._normalize_parques_columns(df)
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_parques"] = len(df)
                        coverage_metadata["parques_with_valid_coords"] = len(df_validated)
                        coverage_metadata["parques_without_coords"] = len(df) - len(df_validated)
                        
                        # Calcular superficie total si está disponible
                        superficie_col = self._find_superficie_column(df_validated)
                        if superficie_col:
                            total_superficie = df_validated[superficie_col].sum()
                            coverage_metadata["total_superficie_m2"] = float(total_superficie)
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"parques_jardines_{dataset_id}",
                            format="csv",
                            data_type="zonas_verdes"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Parques/jardines extraídos: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de parques y jardines"
            logger.warning("No se encontraron datasets de parques y jardines")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo parques y jardines: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_arbolado(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de arbolado de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de arbolado, metadata).
        """
        logger.info("=== Extrayendo datos de arbolado ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_arboles": 0,
            "arboles_with_valid_coords": 0,
            "arboles_without_coords": 0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["arbre", "arbol"]  # Reducir a palabras clave más específicas
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.ARBOLADO_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de arbolado
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de arbolado
                        if not self._is_arbolado_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de arbolado, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Normalizar columnas
                        df = self._normalize_arbolado_columns(df)
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_arboles"] = len(df)
                        coverage_metadata["arboles_with_valid_coords"] = len(df_validated)
                        coverage_metadata["arboles_without_coords"] = len(df) - len(df_validated)
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"arbolado_{dataset_id}",
                            format="csv",
                            data_type="zonas_verdes"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Árboles extraídos: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de arbolado"
            logger.warning("No se encontraron datasets de arbolado")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo arbolado: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los datos de zonas verdes disponibles.
        
        Returns:
            Tupla con (DataFrame combinado, metadata).
        """
        logger.info("=== Extrayendo todos los datos de zonas verdes ===")
        
        # Extraer parques y jardines
        df_parques, meta_parques = self.extract_parques_jardines()
        
        # Extraer arbolado
        df_arbolado, meta_arbolado = self.extract_arbolado()
        
        combined_metadata = {
            "source": "zonas_verdes",
            "success": meta_parques.get("success", False) or meta_arbolado.get("success", False),
            "has_parques": df_parques is not None and not df_parques.empty,
            "has_arbolado": df_arbolado is not None and not df_arbolado.empty,
            "parques_metadata": meta_parques,
            "arbolado_metadata": meta_arbolado,
        }
        
        # Combinar si ambos están disponibles
        if df_parques is not None and df_arbolado is not None:
            # Añadir columna para distinguir tipo
            df_parques = df_parques.copy()
            df_parques["tipo_zona_verde"] = "parque_jardin"
            
            df_arbolado = df_arbolado.copy()
            df_arbolado["tipo_zona_verde"] = "arbol"
            
            # Combinar (usar concat con ignore_index)
            df_combined = pd.concat([df_parques, df_arbolado], ignore_index=True)
            logger.info(f"Datos combinados: {len(df_combined)} registros")
            return df_combined, combined_metadata
        
        # Retornar el que esté disponible
        if df_parques is not None:
            return df_parques, combined_metadata
        
        if df_arbolado is not None:
            return df_arbolado, combined_metadata
        
        return None, combined_metadata
    
    def _normalize_parques_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de parques y jardines.
        
        Args:
            df: DataFrame con columnas originales.
        
        Returns:
            DataFrame con columnas normalizadas.
        """
        df_normalized = df.copy()
        
        # Mapeo de columnas comunes
        column_mapping = {
            # Nombre
            "nom": "nombre",
            "name": "nombre",
            "nom_parc": "nombre",
            "nom_jardi": "nombre",
            
            # Superficie
            "superficie": "superficie_m2",
            "area": "superficie_m2",
            "superficie_m2": "superficie_m2",
            "area_m2": "superficie_m2",
            
            # Coordenadas
            "latitud": "latitud",
            "lat": "latitud",
            "latitude": "latitud",
            "geo_epgs_4326_lat": "latitud",
            "y": "latitud",
            
            "longitud": "longitud",
            "lon": "longitud",
            "lng": "longitud",
            "longitude": "longitud",
            "geo_epgs_4326_lon": "longitud",
            "x": "longitud",
            
            # Barrio
            "barrio": "codi_barri",
            "barri": "codi_barri",
            "codi_barri": "codi_barri",
            "barrio_id": "codi_barri",
        }
        
        # Aplicar mapeo
        for old_col, new_col in column_mapping.items():
            if old_col in df_normalized.columns and new_col not in df_normalized.columns:
                df_normalized.rename(columns={old_col: new_col}, inplace=True)
        
        return df_normalized
    
    def _normalize_arbolado_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de arbolado.
        
        Args:
            df: DataFrame con columnas originales.
        
        Returns:
            DataFrame con columnas normalizadas.
        """
        df_normalized = df.copy()
        
        # Mapeo de columnas comunes
        column_mapping = {
            # Nombre/Especie
            "nom_cientific": "nombre_cientifico",
            "nom_castella": "nombre_castellano",
            "nom_catala": "nombre_catalan",
            "especie": "nombre_cientifico",
            "species": "nombre_cientifico",
            
            # Coordenadas
            "latitud": "latitud",
            "lat": "latitud",
            "latitude": "latitud",
            "geo_epgs_4326_lat": "latitud",
            "y": "latitud",
            
            "longitud": "longitud",
            "lon": "longitud",
            "lng": "longitud",
            "longitude": "longitud",
            "geo_epgs_4326_lon": "longitud",
            "x": "longitud",
            
            # Barrio
            "barrio": "codi_barri",
            "barri": "codi_barri",
            "codi_barri": "codi_barri",
            "barrio_id": "codi_barri",
        }
        
        # Aplicar mapeo
        for old_col, new_col in column_mapping.items():
            if old_col in df_normalized.columns and new_col not in df_normalized.columns:
                df_normalized.rename(columns={old_col: new_col}, inplace=True)
        
        return df_normalized
    
    def _validate_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida y filtra coordenadas dentro del rango geográfico de Barcelona.
        
        Args:
            df: DataFrame con coordenadas.
        
        Returns:
            DataFrame con solo registros con coordenadas válidas.
        """
        if df.empty:
            return df
        
        # Buscar columnas de coordenadas
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ["latitud", "lat", "latitude", "y"]:
                lat_col = col
            elif col_lower in ["longitud", "lon", "lng", "longitude", "x"]:
                lon_col = col
        
        if lat_col is None or lon_col is None:
            logger.warning("No se encontraron columnas de coordenadas")
            return df
        
        # Convertir a numérico
        df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
        df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
        
        # Filtrar coordenadas válidas dentro de Barcelona
        mask = (
            (df[lat_col] >= BARCELONA_LAT_MIN) &
            (df[lat_col] <= BARCELONA_LAT_MAX) &
            (df[lon_col] >= BARCELONA_LON_MIN) &
            (df[lon_col] <= BARCELONA_LON_MAX) &
            df[lat_col].notna() &
            df[lon_col].notna()
        )
        
        df_valid = df[mask].copy()
        
        logger.info(
            f"Coordenadas validadas: {len(df_valid)}/{len(df)} "
            f"registros con coordenadas válidas"
        )
        
        return df_valid
    
    def _find_superficie_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Busca la columna de superficie en el DataFrame.
        
        Args:
            df: DataFrame a buscar.
        
        Returns:
            Nombre de la columna de superficie o None.
        """
        superficie_keywords = ["superficie", "area", "surface"]
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in superficie_keywords):
                return col
        
        return None
    
    def _is_parques_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de parques y jardines.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de parques/jardines.
        """
        # Palabras clave que deben aparecer en el ID o columnas
        parques_keywords = ["parc", "jardi", "parque", "jardín", "zona verde", "zones verdes", "green", "park", "garden"]
        
        # Verificar ID
        dataset_id_lower = dataset_id.lower()
        if any(keyword in dataset_id_lower for keyword in parques_keywords):
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.str.lower())
        if any(keyword in columns_str for keyword in parques_keywords):
            return True
        
        # Verificar valores en las primeras filas
        sample_values = df.head(5).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in parques_keywords):
            return True
        
        return False
    
    def _is_arbolado_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de arbolado.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de arbolado.
        """
        # Palabras clave que deben aparecer en el ID o columnas
        arbolado_keywords = ["arbre", "arbol", "tree", "arbolado", "arbrat", "arbres"]
        
        # Verificar ID
        dataset_id_lower = dataset_id.lower()
        if any(keyword in dataset_id_lower for keyword in arbolado_keywords):
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.str.lower())
        if any(keyword in columns_str for keyword in arbolado_keywords):
            return True
        
        # Verificar valores en las primeras filas
        sample_values = df.head(5).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in arbolado_keywords):
            return True
        
        return False

