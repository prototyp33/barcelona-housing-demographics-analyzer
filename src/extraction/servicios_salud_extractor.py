"""
Extractor para datos de servicios sanitarios de Open Data BCN.

Fuentes:
- Centros de salud y hospitales: Open Data BCN
- Farmacias: Open Data BCN

URLs:
- Centros de salud: https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipaments-sanitaris
- Hospitales: https://opendata-ajuntament.barcelona.cat/data/es/dataset/hospitals
- Farmacias: https://opendata-ajuntament.barcelona.cat/data/es/dataset/farmacies
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


class ServiciosSaludExtractor(BaseExtractor):
    """
    Extractor para datos de servicios sanitarios (centros de salud, hospitales, farmacias)
    de Open Data BCN.
    
    Extrae:
    - Centros de salud y hospitales con ubicación geográfica
    - Farmacias con ubicación geográfica
    - Calcula métricas por barrio
    """
    
    # IDs potenciales de datasets de servicios sanitarios en Open Data BCN
    CENTROS_SALUD_DATASET_IDS = [
        "equipaments-sanitaris",
        "centres-salut",
        "centros-salud",
        "sanitat",
        "salut",
        "health",
        "hospitales",
        "hospitals",
    ]
    
    FARMACIAS_DATASET_IDS = [
        "farmacies",
        "farmacias",
        "pharmacy",
        "pharmacies",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de servicios sanitarios.
        
        Args:
            rate_limit_delay: Segundos de espera entre requests (default: 1.5).
            output_dir: Directorio donde guardar los datos descargados.
        """
        super().__init__("ServiciosSalud", rate_limit_delay, output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(
            rate_limit_delay=rate_limit_delay,
            output_dir=output_dir
        )
    
    def extract_centros_salud_hospitales(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de centros de salud y hospitales de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de centros/hospitales, metadata).
        """
        logger.info("=== Extrayendo datos de centros de salud y hospitales ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_centros": 0,
            "centros_with_valid_coords": 0,
            "centros_without_coords": 0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["sanitat", "salut", "hospital", "centro salud"]
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.CENTROS_SALUD_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de centros de salud y hospitales
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de servicios sanitarios
                        if not self._is_centros_salud_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de centros de salud, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Normalizar columnas
                        df = self._normalize_centros_salud_columns(df)
                        
                        # Filtrar solo centros de salud/hospitales (excluir farmacias)
                        if "tipo" in df.columns or "tipus" in df.columns:
                            tipo_col = "tipo" if "tipo" in df.columns else "tipus"
                            tipo_lower = df[tipo_col].astype(str).str.lower()
                            # Excluir farmacias
                            mask = ~tipo_lower.str.contains("farmacia|pharmacy", na=False)
                            df = df[mask].copy()
                            logger.info(f"Filtrados {len(df)} centros de salud/hospitales (excluyendo farmacias)")
                        elif "nombre" in df.columns:
                            # Si no hay columna tipo, intentar filtrar por nombre
                            nombre_lower = df["nombre"].astype(str).str.lower()
                            mask = ~nombre_lower.str.contains("farmacia|pharmacy", na=False)
                            df = df[mask].copy()
                            logger.info(f"Filtrados {len(df)} centros de salud/hospitales por nombre (excluyendo farmacias)")
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_centros"] = len(df)
                        coverage_metadata["centros_with_valid_coords"] = len(df_validated)
                        coverage_metadata["centros_without_coords"] = len(df) - len(df_validated)
                        
                        # Verificar criterio de aceptación: ≥100 centros
                        if len(df_validated) < 100:
                            logger.warning(
                                f"Criterio de aceptación no cumplido: "
                                f"{len(df_validated)} centros con coordenadas válidas "
                                f"(requerido: ≥100), continuando búsqueda..."
                            )
                            # Continuar buscando si no cumple el criterio
                            continue
                        else:
                            logger.info(
                                f"✅ Criterio cumplido: {len(df_validated)} centros "
                                f"con coordenadas válidas"
                            )
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"centros_salud_{dataset_id}",
                            format="csv",
                            data_type="servicios_salud"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Centros de salud/hospitales extraídos: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de centros de salud y hospitales"
            logger.warning("No se encontraron datasets de centros de salud y hospitales")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo centros de salud: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_farmacias(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de farmacias de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos de farmacias, metadata).
        """
        logger.info("=== Extrayendo datos de farmacias ===")
        
        coverage_metadata = {
            "source": "opendata_bcn",
            "success": False,
            "total_farmacias": 0,
            "farmacias_with_valid_coords": 0,
            "farmacias_without_coords": 0,
        }
        
        try:
            # Primero intentar búsqueda por palabras clave (optimizada)
            keywords = ["farmacia", "farmacie", "pharmacy"]
            found_datasets = []
            
            for keyword in keywords:
                logger.info(f"Buscando datasets con palabra clave: '{keyword}'")
                matching = self.opendata_extractor.search_datasets_by_keyword(keyword, limit=10)
                found_datasets.extend(matching)
                if len(found_datasets) >= 5:  # Si encontramos suficientes, parar
                    break
            
            # Combinar con IDs conocidos
            all_dataset_ids = list(set(found_datasets + self.FARMACIAS_DATASET_IDS))
            
            logger.info(f"Total datasets a probar: {len(all_dataset_ids)}")
            
            # Buscar datasets de farmacias
            for dataset_id in all_dataset_ids:
                try:
                    logger.info(f"Intentando dataset: {dataset_id}")
                    df, meta = self.opendata_extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format="csv"
                    )
                    
                    if df is not None and not df.empty:
                        # Validar que el dataset es realmente de farmacias
                        if not self._is_farmacias_dataset(df, dataset_id):
                            logger.debug(f"Dataset {dataset_id} no parece ser de farmacias, saltando...")
                            continue
                        
                        logger.info(f"✓ Dataset encontrado: {dataset_id}")
                        
                        # Normalizar columnas
                        df = self._normalize_farmacias_columns(df)
                        
                        # Si el dataset es específico de farmacias (sanitat-farmacies), 
                        # asumir que todos los registros son farmacias
                        if "farmacies" in dataset_id.lower() or "farmacias" in dataset_id.lower():
                            logger.info(f"Dataset específico de farmacias, usando todos los registros: {len(df)}")
                            # No filtrar, todos son farmacias
                        elif "tipo" in df.columns or "tipus" in df.columns:
                            tipo_col = "tipo" if "tipo" in df.columns else "tipus"
                            tipo_lower = df[tipo_col].astype(str).str.lower()
                            # Incluir solo farmacias
                            mask = tipo_lower.str.contains("farmacia|pharmacy", na=False)
                            df = df[mask].copy()
                            logger.info(f"Filtradas {len(df)} farmacias por tipo")
                        elif "nombre" in df.columns:
                            # Si no hay columna tipo, intentar filtrar por nombre
                            nombre_lower = df["nombre"].astype(str).str.lower()
                            mask = nombre_lower.str.contains("farmacia|pharmacy", na=False)
                            df = df[mask].copy()
                            logger.info(f"Filtradas {len(df)} farmacias por nombre")
                        
                        # Validar coordenadas
                        df_validated = self._validate_coordinates(df.copy())
                        
                        coverage_metadata["total_farmacias"] = len(df)
                        coverage_metadata["farmacias_with_valid_coords"] = len(df_validated)
                        coverage_metadata["farmacias_without_coords"] = len(df) - len(df_validated)
                        
                        # Verificar criterio de aceptación: ≥200 farmacias
                        if len(df_validated) < 200:
                            logger.warning(
                                f"Criterio de aceptación no cumplido: "
                                f"{len(df_validated)} farmacias con coordenadas válidas "
                                f"(requerido: ≥200), continuando búsqueda..."
                            )
                            # Continuar buscando si no cumple el criterio
                            continue
                        else:
                            logger.info(
                                f"✅ Criterio cumplido: {len(df_validated)} farmacias "
                                f"con coordenadas válidas"
                            )
                        
                        coverage_metadata["success"] = True
                        coverage_metadata["dataset_id"] = dataset_id
                        
                        # Guardar datos raw
                        filepath = self._save_raw_data(
                            data=df_validated,
                            filename=f"farmacias_{dataset_id}",
                            format="csv",
                            data_type="servicios_salud"
                        )
                        coverage_metadata["filepath"] = str(filepath)
                        
                        logger.info(
                            f"Farmacias extraídas: {len(df_validated)} "
                            f"con coordenadas válidas"
                        )
                        
                        return df_validated, coverage_metadata
                
                except Exception as e:
                    logger.debug(f"Error intentando dataset {dataset_id}: {e}")
                    continue
            
            coverage_metadata["error"] = "No se encontraron datasets de farmacias"
            logger.warning("No se encontraron datasets de farmacias")
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo farmacias: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_all(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los datos de servicios sanitarios disponibles.
        
        Returns:
            Tupla con (DataFrame combinado, metadata).
        """
        logger.info("=== Extrayendo todos los datos de servicios sanitarios ===")
        
        # Extraer centros de salud y hospitales
        df_centros, meta_centros = self.extract_centros_salud_hospitales()
        
        # Extraer farmacias
        df_farmacias, meta_farmacias = self.extract_farmacias()
        
        combined_metadata = {
            "source": "servicios_salud",
            "success": meta_centros.get("success", False) or meta_farmacias.get("success", False),
            "has_centros": df_centros is not None and not df_centros.empty,
            "has_farmacias": df_farmacias is not None and not df_farmacias.empty,
            "centros_metadata": meta_centros,
            "farmacias_metadata": meta_farmacias,
        }
        
        # Combinar si ambos están disponibles
        if df_centros is not None and df_farmacias is not None:
            # Añadir columna para distinguir tipo
            df_centros = df_centros.copy()
            df_centros["tipo_servicio"] = "centro_salud_hospital"
            
            df_farmacias = df_farmacias.copy()
            df_farmacias["tipo_servicio"] = "farmacia"
            
            # Combinar (usar concat con ignore_index)
            df_combined = pd.concat([df_centros, df_farmacias], ignore_index=True)
            logger.info(f"Datos combinados: {len(df_combined)} registros")
            return df_combined, combined_metadata
        
        # Retornar el que esté disponible
        if df_centros is not None:
            return df_centros, combined_metadata
        
        if df_farmacias is not None:
            return df_farmacias, combined_metadata
        
        return None, combined_metadata
    
    def _normalize_centros_salud_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de centros de salud y hospitales.
        
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
            "nom_equipament": "nombre",
            "nom_centre": "nombre",
            
            # Tipo
            "tipus": "tipo",
            "type": "tipo",
            "tipus_equipament": "tipo",
            "categoria": "tipo",
            
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
        }
        
        # Aplicar mapeo
        for old_col, new_col in column_mapping.items():
            if old_col in df_normalized.columns and new_col not in df_normalized.columns:
                df_normalized.rename(columns={old_col: new_col}, inplace=True)
        
        return df_normalized
    
    def _normalize_farmacias_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas de farmacias.
        
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
            "nom_farmacia": "nombre",
            
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
    
    def _is_centros_salud_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de centros de salud y hospitales.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de centros de salud/hospitales.
        """
        # Excluir datasets genéricos que no son específicos de salud
        excluded_datasets = [
            "fitxer_entitats",  # Dataset genérico de entidades
            "entitats",  # Entidades genéricas
            "equipaments",  # Equipamientos genéricos (sin especificar tipo)
        ]
        
        dataset_id_lower = dataset_id.lower()
        if any(excluded in dataset_id_lower for excluded in excluded_datasets):
            return False
        
        # Palabras clave que deben aparecer en el ID o columnas
        salud_keywords = [
            "sanitat", "salut", "salud", "health", "hospital", "centre", "centro",
            "equipament-sanitat", "clinica", "clinica"
        ]
        
        # Verificar ID - debe contener palabras clave específicas de salud
        if any(keyword in dataset_id_lower for keyword in salud_keywords):
            # Verificar que NO es de farmacias
            if "farmacia" in dataset_id_lower or "farmacie" in dataset_id_lower or "pharmacy" in dataset_id_lower:
                return False
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.str.lower())
        if any(keyword in columns_str for keyword in salud_keywords):
            # Verificar que NO es de farmacias
            if "farmacia" in columns_str or "pharmacy" in columns_str:
                return False
            return True
        
        # Verificar valores en las primeras filas
        sample_values = df.head(5).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in salud_keywords):
            # Verificar que NO es de farmacias
            if "farmacia" in sample_str or "pharmacy" in sample_str:
                return False
            return True
        
        return False
    
    def _is_farmacias_dataset(self, df: pd.DataFrame, dataset_id: str) -> bool:
        """
        Valida si un dataset es realmente de farmacias.
        
        Args:
            df: DataFrame a validar.
            dataset_id: ID del dataset.
        
        Returns:
            True si parece ser un dataset de farmacias.
        """
        # Palabras clave que deben aparecer en el ID o columnas
        farmacia_keywords = ["farmacia", "farmacie", "pharmacy", "pharmacies"]
        
        # Verificar ID
        dataset_id_lower = dataset_id.lower()
        if any(keyword in dataset_id_lower for keyword in farmacia_keywords):
            return True
        
        # Verificar columnas
        columns_str = " ".join(df.columns.str.lower())
        if any(keyword in columns_str for keyword in farmacia_keywords):
            return True
        
        # Verificar valores en las primeras filas
        sample_values = df.head(5).astype(str).values.flatten()
        sample_str = " ".join(sample_values).lower()
        if any(keyword in sample_str for keyword in farmacia_keywords):
            return True
        
        return False

