"""
Extractor para datos de comercio de Open Data BCN.

Fuentes:
- Locales comerciales: Open Data BCN
- Terrazas y licencias: Open Data BCN

URLs:
- Locales comerciales: https://opendata-ajuntament.barcelona.cat/data/es/dataset/comerc
- Terrazas: https://opendata-ajuntament.barcelona.cat/data/es/dataset/terrasses
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


class ComercioExtractor(BaseExtractor):
    """
    Extractor para datos de comercio (locales comerciales, terrazas, licencias)
    de Open Data BCN.
    
    Extrae:
    - Locales comerciales con ubicación geográfica
    - Terrazas y licencias con ubicación geográfica
    - Calcula métricas por barrio
    """
    
    # IDs potenciales de datasets de comercio en Open Data BCN
    LOCALES_COMERCIALES_DATASET_IDS = [
        "comerc",
        "comercio",
        "commercial",
        "locals-comercials",
        "locales-comerciales",
        "activitat-comercial",
        "actividad-comercial",
        "establiments",
        "establecimientos",
    ]
    
    TERRAZAS_DATASET_IDS = [
        "terrasses",
        "terrazas",
        "terrace",
        "licencia-terrassa",
        "licencia-terraza",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de comercio.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 1.5).
            output_dir: Directorio donde guardar los datos descargados.
        """
        super().__init__("Comercio", rate_limit_delay, output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(
            rate_limit_delay=rate_limit_delay,
            output_dir=output_dir
        )
    
    def extract_locales_comerciales(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de locales comerciales de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de locales comerciales, metadata).
        """
        logger.info("=== Extrayendo datos de locales comerciales ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_locales": 0,
            "locales_with_valid_coords": 0,
            "locales_without_coords": 0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["comerc", "comercio", "commercial", "local", "establiment"]
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.LOCALES_COMERCIALES_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de locales comerciales
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de comercio
                        if not self._is_comercio_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de comercio, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Normalizar columnas
                        df = self._normalize_locales_columns(df)
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_locales"] = len(df)
                        coverage_metadata["locales_with_valid_coords"] = len(df_validated)
                        coverage_metadata["locales_without_coords"] = len(df) - len(df_validated)
                        
                        # Verificar criterio de aceptación: ≥1000 locales
                        if len(df_validated) < 1000:
                            logger.warning(
                                f"Criterio de aceptación no cumplido: "
                                f"{len(df_validated)} locales con coordenadas válidas "
                                f"(requerido: ≥1000), continuando búsqueda..."
                            )
                            # Continuar buscando si no cumple el criterio
                            continue
                        else:
                            logger.info(
                                f"✅ Criterio cumplido: {len(df_validated)} locales "
                                f"con coordenadas válidas"
                            )
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"locales_comerciales_{dataset_id}",
                            format="csv",
                            data_type="comercio"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Locales comerciales extraídos: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de locales comerciales con ≥1000 registros"
            logger.warning("No se encontraron datasets de locales comerciales con ≥1000 registros")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo locales comerciales: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_terrazas_licencias(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de terrazas y licencias de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de terrazas/licencias, metadata).
        """
        logger.info("=== Extrayendo datos de terrazas y licencias ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_terrazas": 0,
            "terrazas_with_valid_coords": 0,
            "terrazas_without_coords": 0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["terrassa", "terraza", "terrace", "licencia"]
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.TERRAZAS_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de terrazas
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de terrazas
                        if not self._is_terrazas_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de terrazas, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Si el CSV tiene formato extraño (punto y coma mal parseado), intentar repararlo
                        if df.shape[1] == 1 and df.columns[0].startswith('3/'):
                            logger.info("Detectado CSV con formato extraño, intentando reparar...")
                            # Re-leer con punto y coma desde el archivo raw guardado
                            try:
                                raw_file = self.output_dir / "opendatabcn" / f"opendatabcn_{dataset_id}_*.csv"
                                import glob
                                matching_files = glob.glob(str(raw_file))
                                if matching_files:
                                    df_repaired = pd.read_csv(
                                        matching_files[0],
                                        sep=';',
                                        encoding='utf-8',
                                        on_bad_lines='skip',
                                        engine='python'
                                    )
                                    logger.info(f"CSV reparado: {len(df_repaired)} registros, {len(df_repaired.columns)} columnas")
                                    df = df_repaired
                            except Exception as e:
                                logger.warning(f"No se pudo reparar el CSV: {e}")
                        
                        # Normalizar columnas
                        df = self._normalize_terrazas_columns(df)
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_terrazas"] = len(df)
                        coverage_metadata["terrazas_with_valid_coords"] = len(df_validated)
                        coverage_metadata["terrazas_without_coords"] = len(df) - len(df_validated)
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"terrazas_{dataset_id}",
                            format="csv",
                            data_type="comercio"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Terrazas/licencias extraídas: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de terrazas y licencias"
            logger.warning("No se encontraron datasets de terrazas y licencias")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo terrazas: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los datos de comercio disponibles.
        
        Returns:
            Tupla con (DataFrame combinado, metadata).
        """
        logger.info("=== Extrayendo todos los datos de comercio ===")
        
        # Extraer locales comerciales
        df_locales, meta_locales = self.extract_locales_comerciales()
        
        # Extraer terrazas y licencias
        df_terrazas, meta_terrazas = self.extract_terrazas_licencias()
        
        combined_metadata = {
            "source": "comercio",
            "success": meta_locales.get("success", False) or meta_terrazas.get("success", False),
            "has_locales": df_locales is not None and not df_locales.empty,
            "has_terrazas": df_terrazas is not None and not df_terrazas.empty,
            "locales_metadata": meta_locales,
            "terrazas_metadata": meta_terrazas,
        }
        
        # Combinar si ambos están disponibles
        if df_locales is not None and df_terrazas is not None:
            # Añadir columna para distinguir tipo
            df_locales = df_locales.copy()
            df_locales["tipo_comercio"] = "local_comercial"
            
            df_terrazas = df_terrazas.copy()
            df_terrazas["tipo_comercio"] = "terraza"
            
            # Combinar (usar concat con ignore_index)
            df_combined = pd.concat([df_locales, df_terrazas], ignore_index=True)
            logger.info(f"Datos combinados: {len(df_combined)} registros")
            return df_combined, combined_metadata
        
        # Retornar el que esté disponible
        if df_locales is not None:
            return df_locales, combined_metadata
        
        if df_terrazas is not None:
            return df_terrazas, combined_metadata
        
        return None, combined_metadata
    
    def _normalize_locales_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de locales comerciales.
        
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
            "nom_establiment": "nombre",
            "nom_local": "nombre",
            
            # Tipo de actividad
            "tipus": "tipo_actividad",
            "type": "tipo_actividad",
            "activitat": "tipo_actividad",
            "actividad": "tipo_actividad",
            "categoria": "tipo_actividad",
            
            # Estado/ocupación
            "estat": "estado",
            "estado": "estado",
            "status": "estado",
            "ocupacio": "ocupacion",
            "ocupacion": "ocupacion",
            
            # Coordenadas
            "latitud": "latitud",
            "lat": "latitud",
            "latitude": "latitud",
            "geo_epgs_4326_lat": "latitud",
            "y": "latitud",
            
            "longitud": "longitud",
            "lon": "longitud",
            "lng": "longitude",
            "geo_epgs_4326_lon": "longitud",
            "x": "longitud",
            
            # Barrio
            "barrio": "codi_barri",
            "barri": "codi_barri",
            "codi_barri": "codi_barri",
            "barrio_id": "codi_barri",
            "addresses_neighborhood_id": "codi_barri",
        }
        
        # Aplicar mapeo
        for old_col, new_col in column_mapping.items():
            if old_col in df_normalized.columns and new_col not in df_normalized.columns:
                df_normalized.rename(columns={old_col: new_col}, inplace=True)
        
        return df_normalized
    
    def _normalize_terrazas_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de terrazas y licencias.
        
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
            "nom_terrassa": "nombre",
            
            # Tipo de licencia
            "tipus_licencia": "tipo_licencia",
            "tipo_licencia": "tipo_licencia",
            "licencia": "tipo_licencia",
            
            # Coordenadas
            "latitud": "latitud",
            "lat": "latitud",
            "latitude": "latitud",
            "geo_epgs_4326_lat": "latitud",
            "y": "latitud",
            
            "longitud": "longitud",
            "lon": "longitud",
            "lng": "longitude",
            "geo_epgs_4326_lon": "longitud",
            "x": "longitud",
            
            # Barrio
            "barrio": "codi_barri",
            "barri": "codi_barri",
            "codi_barri": "codi_barri",
            "barrio_id": "codi_barri",
            "addresses_neighborhood_id": "codi_barri",
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
    
    def _is_comercio_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de locales comerciales.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de locales comerciales.
        """
        # Excluir datasets de terrazas
        dataset_id_lower = dataset_id.lower()
        if "terrassa" in dataset_id_lower or "terraza" in dataset_id_lower or "terrace" in dataset_id_lower:
            return False
        
        # Palabras clave que deben aparecer en el ID o columnas
        comercio_keywords = [
            "comerc", "comercio", "commercial", "local", "establiment",
            "establecimiento", "activitat", "actividad"
        ]
        
        # Verificar ID
        if any(keyword in dataset_id_lower for keyword in comercio_keywords):
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.str.lower())
        if any(keyword in columns_str for keyword in comercio_keywords):
            # Verificar que NO es de terrazas
            if "terrassa" in columns_str or "terraza" in columns_str:
                return False
            return True
        
        # Verificar valores en las primeras filas
        sample_values = df.head(5).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in comercio_keywords):
            # Verificar que NO es de terrazas
            if "terrassa" in sample_str or "terraza" in sample_str:
                return False
            return True
        
        return False
    
    def _is_terrazas_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de terrazas.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de terrazas.
        """
        # Palabras clave que deben aparecer en el ID o columnas
        terrazas_keywords = ["terrassa", "terrasses", "terraza", "terrazas", "terrace", "licencia", "licencia"]
        
        # Verificar ID - prioridad alta si contiene palabras clave de terrazas
        dataset_id_lower = dataset_id.lower()
        if any(keyword in dataset_id_lower for keyword in terrazas_keywords):
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.astype(str).str.lower())
        if any(keyword in columns_str for keyword in terrazas_keywords):
            return True
        
        # Verificar valores en las primeras filas (más exhaustivo)
        sample_values = df.head(10).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in terrazas_keywords):
            return True
        
        return False

