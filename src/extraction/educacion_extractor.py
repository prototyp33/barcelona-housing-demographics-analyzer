"""
Educación Extractor Module - Extracción de equipamientos educativos de Open Data BCN.

Fuente: Open Data BCN - Equipament Educació
Dataset ID: equipament-educacio
Resource ID: d0471a29-821f-42aa-b631-19a76052bdff
"""

import io
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger
from .opendata import OpenDataBCNExtractor

# Rango válido de coordenadas para Barcelona (aproximado)
BARCELONA_LAT_MIN = 41.35
BARCELONA_LAT_MAX = 41.45
BARCELONA_LON_MIN = 2.05
BARCELONA_LON_MAX = 2.25


class EducacionExtractor(BaseExtractor):
    """
    Extractor para equipamientos educativos de Open Data BCN.
    
    Hereda de BaseExtractor para funcionalidades comunes (rate limiting, logging).
    Usa OpenDataBCNExtractor para acceso a la API CKAN.
    """
    
    DATASET_ID = "equipament-educacio"
    # Resource IDs disponibles:
    # - CSV: 29d9ff10-6892-4f16-9012-d5c4997857e7 (preferido)
    # - JSON: d0471a29-821f-42aa-b631-19a76052bdff
    RESOURCE_ID_CSV = "29d9ff10-6892-4f16-9012-d5c4997857e7"
    RESOURCE_ID_JSON = "d0471a29-821f-42aa-b631-19a76052bdff"
    
    # Tipos de equipamientos educativos según el dataset
    TIPOS_EDUCACION = {
        "infantil": ["Educació Infantil", "Escola Bressol", "Guarderia"],
        "primaria": ["Educació Primària", "Escola Primària"],
        "secundaria": ["Educació Secundària", "ESO", "Institut"],
        "fp": ["Formació Professional", "FP", "Cicles Formatius"],
        "universidad": ["Universitat", "Universidad", "Campus"],
        "autoescuela": ["Autoescola", "Autoescuela"],
        "academia": ["Acadèmia", "Academia", "Català"],
    }
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de educación.
        
        Args:
            rate_limit_delay: Tiempo de espera entre peticiones (segundos).
                             Default 2.0 para cumplir rate limit de 30 req/min.
            output_dir: Directorio donde guardar los datos.
        """
        super().__init__("Educacion", rate_limit_delay, output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(rate_limit_delay=rate_limit_delay, output_dir=output_dir)
    
    def extract_equipamientos(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los equipamientos educativos de Open Data BCN.
        
        Valida que todos los registros tengan coordenadas válidas dentro del rango
        geográfico de Barcelona.
        
        Returns:
            Tupla con (DataFrame con equipamientos validados, metadata de cobertura).
        """
        logger.info(f"Extrayendo equipamientos educativos: {self.DATASET_ID}")
        
        coverage_metadata = {
            "dataset_id": self.DATASET_ID,
            "resource_id": None,
            "success": False,
            "total_records": 0,
            "records_with_valid_coords": 0,
            "records_without_coords": 0,
            "records_invalid_coords": 0,
            "tipos_encontrados": {},
        }
        
        try:
            # Intentar descargar CSV primero (más eficiente)
            df, metadata = self.opendata_extractor.download_dataset(
                dataset_id=self.DATASET_ID,
                resource_format='csv',
            )
            
            # Si el CSV está vacío o falla, intentar con JSON
            if df is None or df.empty:
                logger.info("CSV vacío o no disponible, intentando con JSON...")
                df, metadata = self.opendata_extractor.download_dataset(
                    dataset_id=self.DATASET_ID,
                    resource_format='json',
                )
            
            if df is not None and not df.empty:
                coverage_metadata["resource_id"] = metadata.get("resource_id", "auto-detected")
            
            if df is None or df.empty:
                logger.error(f"No se pudieron extraer datos de {self.DATASET_ID}")
                coverage_metadata["error"] = "No se obtuvieron datos"
                return None, coverage_metadata
            
            logger.info(f"Equipamientos extraídos: {len(df)} registros")
            logger.info(f"Columnas disponibles: {df.columns.tolist()}")
            
            # Normalizar nombres de columnas según el formato del dataset
            df = self._normalize_columns(df)
            
            # Validar que tenemos las columnas necesarias después de normalización
            required_columns = ["nom_equipament", "tipus_equipament"]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                logger.warning(f"Columnas faltantes después de normalización: {missing}. Columnas disponibles: {df.columns.tolist()}")
            
            # Validar y limpiar coordenadas
            df_validated = self._validate_coordinates(df.copy())
            
            # Estadísticas de validación
            total_records = len(df)
            records_with_valid_coords = len(df_validated)
            records_without_coords = total_records - records_with_valid_coords
            
            coverage_metadata["total_records"] = total_records
            coverage_metadata["records_with_valid_coords"] = records_with_valid_coords
            coverage_metadata["records_without_coords"] = records_without_coords
            
            # Verificar criterio de aceptación: ≥500 equipamientos
            if records_with_valid_coords < 500:
                logger.warning(
                    f"Criterio de aceptación no cumplido: "
                    f"{records_with_valid_coords} equipamientos con coordenadas válidas "
                    f"(requerido: ≥500)"
                )
            else:
                logger.info(
                    f"✅ Criterio cumplido: {records_with_valid_coords} equipamientos "
                    f"con coordenadas válidas"
                )
            
            # Verificar que todos los registros tienen coordenadas válidas
            if records_without_coords > 0:
                logger.warning(
                    f"{records_without_coords} registros sin coordenadas válidas "
                    f"serán excluidos del procesamiento"
                )
            
            # Contar tipos de equipamientos
            if "tipus_equipament" in df_validated.columns:
                try:
                    # Intentar contar valores únicos (puede ser Series o DataFrame)
                    tipo_col = df_validated["tipus_equipament"]
                    if isinstance(tipo_col, pd.Series):
                        tipos = tipo_col.value_counts().to_dict()
                    else:
                        # Si es DataFrame, obtener valores únicos de todas las columnas
                        tipos = {}
                        for col in tipo_col.columns if hasattr(tipo_col, 'columns') else [tipo_col]:
                            unique_vals = df_validated[col].dropna().unique()
                            for val in unique_vals:
                                tipos[str(val)] = tipos.get(str(val), 0) + 1
                    coverage_metadata["tipos_encontrados"] = tipos
                    logger.info(f"Tipos de equipamientos encontrados: {len(tipos)}")
                except Exception as e:
                    logger.warning(f"Error contando tipos de equipamientos: {e}")
                    # Obtener valores únicos de forma más simple
                    try:
                        unique_tipos = df_validated["tipus_equipament"].dropna().unique()
                        tipos = {str(tipo): 1 for tipo in unique_tipos[:20]}  # Limitar a primeros 20
                        coverage_metadata["tipos_encontrados"] = tipos
                        logger.info(f"Tipos únicos encontrados (muestra): {len(tipos)}")
                    except Exception:
                        coverage_metadata["tipos_encontrados"] = {}
            
            coverage_metadata["success"] = True
            
            # Guardar datos raw (guardar el original completo)
            filepath = self._save_raw_data(
                data=df,
                filename="equipament_educacio",
                format="csv",
                data_type="educacion"
            )
            coverage_metadata["filepath"] = str(filepath)
            
            # Retornar DataFrame validado (solo con coordenadas válidas)
            return df_validated, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo equipamientos educativos: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza los nombres de columnas del dataset a formato estándar.
        
        El dataset de Open Data BCN usa diferentes nombres de columnas según la versión.
        Este método mapea los nombres comunes a un formato estándar.
        
        Args:
            df: DataFrame con columnas originales.
        
        Returns:
            DataFrame con columnas normalizadas.
        """
        df_normalized = df.copy()
        
        # Mapeo de nombres de columnas
        column_mapping = {
            # Nombre del equipamiento
            'name': 'nom_equipament',
            'nom_equipament': 'nom_equipament',
            'equipament': 'nom_equipament',
            
            # Tipo de equipamiento (puede estar en diferentes columnas)
            'values_attribute_name': 'tipus_equipament',
            'values_category': 'tipus_equipament',
            'tipus_equipament': 'tipus_equipament',
            'type': 'tipus_equipament',
            
            # Coordenadas (diferentes formatos)
            'geo_epgs_4326_lat': 'latitud',
            'geo_epgs_4326_lon': 'longitud',
            'latitude': 'latitud',
            'longitude': 'longitud',
            'lat': 'latitud',
            'lon': 'longitud',
            'coord_y': 'latitud',
            'coord_x': 'longitud',
        }
        
        # Renombrar columnas que existen, evitando duplicados
        rename_dict = {}
        columns_to_remove = []
        
        for old_name, new_name in column_mapping.items():
            if old_name in df_normalized.columns:
                if new_name not in df_normalized.columns:
                    rename_dict[old_name] = new_name
                elif old_name != new_name:
                    # Si la columna destino ya existe, marcar la original para eliminarla después
                    columns_to_remove.append(old_name)
        
        if rename_dict:
            df_normalized = df_normalized.rename(columns=rename_dict)
            logger.info(f"Columnas renombradas: {rename_dict}")
        
        # Eliminar columnas duplicadas
        if columns_to_remove:
            df_normalized = df_normalized.drop(columns=[col for col in columns_to_remove if col in df_normalized.columns])
        
        # Si no tenemos tipus_equipament pero tenemos values_attribute_name o values_category,
        # intentar construirla desde values
        # Nota: Estos campos pueden tener múltiples valores por fila, así que tomamos el primero no nulo
        if 'tipus_equipament' not in df_normalized.columns:
            if 'values_attribute_name' in df_normalized.columns:
                df_normalized['tipus_equipament'] = df_normalized['values_attribute_name']
            elif 'values_category' in df_normalized.columns:
                df_normalized['tipus_equipament'] = df_normalized['values_category']
        
        # Asegurar que tipus_equipament es una Serie simple (no DataFrame)
        if 'tipus_equipament' in df_normalized.columns:
            if isinstance(df_normalized['tipus_equipament'], pd.DataFrame):
                # Si es DataFrame, tomar la primera columna o concatenar
                df_normalized['tipus_equipament'] = df_normalized['tipus_equipament'].iloc[:, 0]
            # Convertir a string y manejar valores nulos
            df_normalized['tipus_equipament'] = df_normalized['tipus_equipament'].astype(str).replace('nan', pd.NA)
        
        # Eliminar columnas duplicadas si existen
        df_normalized = df_normalized.loc[:, ~df_normalized.columns.duplicated()]
        
        return df_normalized
    
    def _validate_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida que las coordenadas estén dentro del rango geográfico de Barcelona.
        
        Busca columnas de coordenadas con diferentes nombres posibles y valida
        que estén dentro del rango válido de Barcelona.
        
        Args:
            df: DataFrame con equipamientos educativos.
        
        Returns:
            DataFrame filtrado solo con registros que tienen coordenadas válidas.
        """
        # Buscar columnas de coordenadas
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ["latitud", "latitude", "coord_y", "y", "lat"]:
                lat_col = col
            elif col_lower in ["longitud", "longitude", "coord_x", "x", "lon", "lng"]:
                lon_col = col
        
        if lat_col is None or lon_col is None:
            logger.warning(
                f"No se encontraron columnas de coordenadas. "
                f"Columnas disponibles: {df.columns.tolist()}"
            )
            return pd.DataFrame()  # Retornar DataFrame vacío si no hay coordenadas
        
        # Convertir a numérico, forzando errores a NaN
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        
        # Filtrar registros con coordenadas válidas dentro del rango de Barcelona
        mask_valid = (
            df[lat_col].notna() &
            df[lon_col].notna() &
            (df[lat_col] >= BARCELONA_LAT_MIN) &
            (df[lat_col] <= BARCELONA_LAT_MAX) &
            (df[lon_col] >= BARCELONA_LON_MIN) &
            (df[lon_col] <= BARCELONA_LON_MAX)
        )
        
        df_valid = df[mask_valid].copy()
        
        invalid_count = (~mask_valid).sum()
        if invalid_count > 0:
            logger.info(
                f"Validación de coordenadas: {len(df_valid)} válidas, "
                f"{invalid_count} inválidas o fuera de rango"
            )
        
        return df_valid
    
    def classify_tipo_educacion(self, tipo_equipament: str) -> Optional[str]:
        """
        Clasifica un tipo de equipamiento en categoría educativa.
        
        Args:
            tipo_equipament: Tipo de equipamiento según el dataset.
        
        Returns:
            Categoría ('infantil', 'primaria', 'secundaria', 'fp', 'universidad', etc.)
            o None si no coincide.
        """
        if pd.isna(tipo_equipament):
            return None
        
        tipo_lower = str(tipo_equipament).lower()
        
        for categoria, keywords in self.TIPOS_EDUCACION.items():
            if any(keyword.lower() in tipo_lower for keyword in keywords):
                return categoria
        
        return None
    
    def get_coverage_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula estadísticas de cobertura geográfica por barrio.
        
        Args:
            df: DataFrame con equipamientos educativos (debe tener barrio_id).
        
        Returns:
            Diccionario con estadísticas de cobertura.
        """
        stats = {
            "total_equipamientos": len(df),
            "barrios_con_equipamientos": 0,
            "barrios_sin_equipamientos": 0,
            "distribucion_por_tipo": {},
        }
        
        if "barrio_id" in df.columns:
            barrios_con_datos = df["barrio_id"].notna().sum()
            stats["barrios_con_equipamientos"] = df["barrio_id"].nunique()
            stats["barrios_sin_equipamientos"] = 73 - stats["barrios_con_equipamientos"]
        
        if "tipus_equipament" in df.columns:
            tipo_col = "tipus_equipament"
            for _, row in df.iterrows():
                categoria = self.classify_tipo_educacion(row[tipo_col])
                if categoria:
                    stats["distribucion_por_tipo"][categoria] = (
                        stats["distribucion_por_tipo"].get(categoria, 0) + 1
                    )
        
        return stats

