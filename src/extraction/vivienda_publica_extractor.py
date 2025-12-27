"""
Vivienda Pública Extractor Module - Extracción de datos de vivienda pública.

Fuentes:
- IDESCAT: API REST (datos a nivel municipal)
- Open Data BCN: Datos de habitatge (cuotas catastrales, viviendas)

⚠️ IMPORTANTE: Los datos de IDESCAT son a nivel municipal (Barcelona), por lo que
requieren distribución proporcional por barrio usando población o renta como peso.
Los valores resultantes son ESTIMACIONES, no datos reales por barrio.
"""

import sqlite3
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger
from .opendata import OpenDataBCNExtractor


class ViviendaPublicaExtractor(BaseExtractor):
    """
    Extractor para datos de vivienda pública de IDESCAT y Open Data BCN.
    
    Los datos de IDESCAT son a nivel municipal, por lo que se deben distribuir
    proporcionalmente por barrio usando población o renta como peso.
    """
    
    IDESCAT_BASE_URL = "https://api.idescat.cat"
    
    # IDs de datasets Open Data BCN relacionados con vivienda
    OPENDATA_DATASETS = {
        "habitatge": "habitatge",  # Organización de datasets de vivienda
        "cuotas_catastrales": "cuotas-catastrales",
    }
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor de vivienda pública.
        
        Args:
            rate_limit_delay: Tiempo de espera entre peticiones.
            output_dir: Directorio donde guardar los datos.
        """
        super().__init__("ViviendaPublica", rate_limit_delay, output_dir)
        self.opendata_extractor = OpenDataBCNExtractor(
            rate_limit_delay=rate_limit_delay,
            output_dir=output_dir
        )
    
    def extract_idescat_alquiler(self, year: int) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de alquiler de IDESCAT a nivel municipal.
        
        Args:
            year: Año de los datos.
        
        Returns:
            Tupla con (DataFrame con datos municipales, metadata).
        """
        logger.info(f"Extrayendo datos de alquiler IDESCAT para {year}...")
        
        coverage_metadata = {
            "source": "idescat_api",
            "year": year,
            "success": False,
            "level": "municipal",  # Importante: datos a nivel municipal
        }
        
        try:
            # IDESCAT API endpoint para alquiler
            # Nota: La estructura exacta de la API puede variar
            # Este es un ejemplo basado en la documentación de IDESCAT
            endpoint = f"{self.IDESCAT_BASE_URL}/emex/v1"
            params = {
                "lang": "es",
                "year": year,
                "territory": "080193",  # Código INE de Barcelona
            }
            
            self._rate_limit()
            response = self.session.get(endpoint, params=params, timeout=30)
            
            if not self._validate_response(response):
                coverage_metadata["error"] = "Error en respuesta HTTP"
                return None, coverage_metadata
            
            data = response.json()
            
            # Parsear respuesta según estructura de IDESCAT
            # La estructura puede variar, este es un ejemplo
            if "data" in data:
                df = pd.DataFrame(data["data"])
            else:
                # Intentar parsear directamente como lista
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    logger.error("Estructura de respuesta IDESCAT inesperada")
                    coverage_metadata["error"] = "Estructura de respuesta inesperada"
                    return None, coverage_metadata
            
            logger.info(f"Datos IDESCAT extraídos: {len(df)} registros")
            coverage_metadata["success"] = True
            coverage_metadata["total_records"] = len(df)
            
            # Guardar datos raw
            filepath = self._save_raw_data(
                data=df,
                filename=f"idescat_alquiler_{year}",
                format="csv",
                data_type="vivienda_publica"
            )
            coverage_metadata["filepath"] = str(filepath)
            
            return df, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo datos IDESCAT: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def extract_opendata_habitatge(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de vivienda de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos, metadata).
        """
        logger.info("Extrayendo datos de vivienda de Open Data BCN...")
        
        coverage_metadata = {
            "source": "opendata_bcn_habitatge",
            "success": False,
        }
        
        try:
            # Buscar datasets de la organización "habitatge"
            # Esto puede requerir explorar la API CKAN
            logger.warning("Extractor de Open Data BCN habitatge no completamente implementado")
            logger.info("Usar OpenDataBCNExtractor directamente para datasets específicos")
            
            # TODO: Implementar búsqueda y descarga de datasets de habitatge
            coverage_metadata["error"] = "No implementado completamente"
            return None, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo datos Open Data BCN: {e}")
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata
    
    def distribute_to_barrios(
        self,
        municipal_data: pd.DataFrame,
        db_path: Optional[Path] = None,
        weight_type: str = "poblacion",
        year: Optional[int] = None
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Distribuye datos municipales proporcionalmente por barrio.
        
        ⚠️ IMPORTANTE: Los valores resultantes son ESTIMACIONES por distribución
        proporcional, no datos reales por barrio.
        
        Args:
            municipal_data: DataFrame con datos municipales (debe tener un solo registro).
            db_path: Ruta a la base de datos (para obtener pesos de barrios).
            weight_type: Tipo de peso ('poblacion' o 'renta').
            year: Año de los datos (para obtener pesos del año correcto).
        
        Returns:
            Tupla con (DataFrame distribuido por barrio, metadata con advertencias).
        """
        logger.warning(
            "⚠️  DISTRIBUCIÓN PROPORCIONAL: Los valores resultantes son ESTIMACIONES, "
            "no datos reales por barrio"
        )
        
        distribution_metadata = {
            "distribution_method": "proportional",
            "weight_type": weight_type,
            "is_estimated": True,  # Marcar claramente como estimado
            "warning": "Los valores son estimaciones por distribución proporcional",
            "success": False,
        }
        
        try:
            if municipal_data.empty:
                logger.error("DataFrame municipal vacío")
                distribution_metadata["error"] = "Datos municipales vacíos"
                return None, distribution_metadata
            
            if len(municipal_data) > 1:
                logger.warning(
                    f"DataFrame tiene {len(municipal_data)} registros. "
                    "Usando solo el primero para distribución municipal."
                )
                municipal_data = municipal_data.iloc[[0]].copy()
            
            # Obtener pesos de barrios desde la BD
            if db_path is None:
                from .base import BASE_DIR
                db_path = BASE_DIR / "data" / "processed" / "database.db"
            
            if not db_path.exists():
                logger.error(f"Base de datos no encontrada: {db_path}")
                distribution_metadata["error"] = "Base de datos no encontrada"
                return None, distribution_metadata
            
            conn = sqlite3.connect(db_path)
            barrios_df = self._get_barrios_with_weights(conn, weight_type, year)
            conn.close()
            
            if barrios_df.empty:
                logger.error("No hay barrios con pesos disponibles")
                distribution_metadata["error"] = "No hay barrios con pesos"
                return None, distribution_metadata
            
            # Extraer valores municipales
            row = municipal_data.iloc[0]
            
            # Buscar columnas relevantes
            renta_col = None
            contratos_col = None
            fianzas_col = None
            
            for col in municipal_data.columns:
                col_lower = col.lower()
                if "renta" in col_lower or "alquiler" in col_lower:
                    renta_col = col
                elif "contrato" in col_lower:
                    contratos_col = col
                elif "fianza" in col_lower:
                    fianzas_col = col
            
            # Distribuir valores
            results = []
            total_weight = barrios_df["peso"].sum()
            
            if total_weight == 0:
                logger.warning("Peso total es 0, distribuyendo uniformemente")
                n_barrios = len(barrios_df)
                uniform_proportion = 1.0 / n_barrios if n_barrios > 0 else 0
            else:
                uniform_proportion = None
            
            for _, barrio_row in barrios_df.iterrows():
                barrio_id = int(barrio_row["barrio_id"])
                peso = barrio_row["peso"]
                
                if uniform_proportion is not None:
                    proporcion = uniform_proportion
                else:
                    proporcion = peso / total_weight
                
                # Extraer valores municipales
                renta_media = (
                    float(row[renta_col]) if renta_col and renta_col in row.index and pd.notna(row[renta_col])
                    else None
                )
                contratos = (
                    float(row[contratos_col]) if contratos_col and contratos_col in row.index and pd.notna(row[contratos_col])
                    else None
                )
                fianzas = (
                    float(row[fianzas_col]) if fianzas_col and fianzas_col in row.index and pd.notna(row[fianzas_col])
                    else None
                )
                
                results.append({
                    "barrio_id": barrio_id,
                    "anio": year if year else None,
                    "renta_media_mensual_alquiler": (
                        round(renta_media * proporcion, 2) if renta_media is not None else None
                    ),
                    "contratos_alquiler_nuevos": (
                        int(round(contratos * proporcion)) if contratos is not None else None
                    ),
                    "fianzas_depositadas_euros": (
                        round(fianzas * proporcion, 2) if fianzas is not None else None
                    ),
                    "viviendas_proteccion_oficial": None,  # No disponible en IDESCAT municipal
                    "is_estimated": True,  # Marcar como estimado
                    "distribution_weight": weight_type,
                })
            
            df_distributed = pd.DataFrame(results)
            
            logger.info(f"Datos distribuidos para {len(df_distributed)} barrios")
            logger.warning(
                "⚠️  IMPORTANTE: Estos son valores ESTIMADOS por distribución proporcional, "
                "no datos reales por barrio"
            )
            
            distribution_metadata["success"] = True
            distribution_metadata["barrios_distributed"] = len(df_distributed)
            distribution_metadata["total_weight"] = float(total_weight)
            
            return df_distributed, distribution_metadata
            
        except Exception as e:
            logger.error(f"Error distribuyendo datos por barrios: {e}")
            logger.error(traceback.format_exc())
            distribution_metadata["error"] = str(e)
            return None, distribution_metadata
    
    def _get_barrios_with_weights(
        self,
        conn: sqlite3.Connection,
        weight_type: str = "poblacion",
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Obtiene los barrios con sus pesos para distribución proporcional.
        
        Args:
            conn: Conexión a la base de datos.
            weight_type: Tipo de peso ('poblacion' o 'renta').
            year: Año para obtener pesos (None = último año disponible).
        
        Returns:
            DataFrame con barrio_id, barrio_nombre, peso.
        """
        if weight_type == "poblacion":
            if year:
                query = """
                SELECT 
                    db.barrio_id,
                    db.barrio_nombre,
                    COALESCE(d.poblacion_total, 0) as peso
                FROM dim_barrios db
                LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id AND d.anio = ?
                WHERE peso > 0
                ORDER BY db.barrio_id
                """
                df = pd.read_sql_query(query, conn, params=[year])
            else:
                query = """
                SELECT 
                    db.barrio_id,
                    db.barrio_nombre,
                    COALESCE(MAX(d.poblacion_total), 0) as peso
                FROM dim_barrios db
                LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id
                GROUP BY db.barrio_id, db.barrio_nombre
                HAVING peso > 0
                ORDER BY db.barrio_id
                """
                df = pd.read_sql_query(query, conn)
        else:  # renta
            if year:
                query = """
                SELECT 
                    db.barrio_id,
                    db.barrio_nombre,
                    COALESCE(r.renta_mediana, 0) as peso
                FROM dim_barrios db
                LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id AND r.anio = ?
                WHERE peso > 0
                ORDER BY db.barrio_id
                """
                df = pd.read_sql_query(query, conn, params=[year])
            else:
                query = """
                SELECT 
                    db.barrio_id,
                    db.barrio_nombre,
                    COALESCE(MAX(r.renta_mediana), 0) as peso
                FROM dim_barrios db
                LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id
                GROUP BY db.barrio_id, db.barrio_nombre
                HAVING peso > 0
                ORDER BY db.barrio_id
                """
                df = pd.read_sql_query(query, conn)
        
        return df
    
    def extract_all(
        self,
        year: int,
        distribute: bool = True,
        weight_type: str = "poblacion",
        db_path: Optional[Path] = None
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae todos los datos de vivienda pública disponibles y opcionalmente los distribuye por barrio.
        
        ⚠️ IMPORTANTE: Si distribute=True, los valores resultantes son ESTIMACIONES
        por distribución proporcional, no datos reales por barrio.
        
        Args:
            year: Año de los datos.
            distribute: Si True, distribuye los datos municipales por barrio.
            weight_type: Tipo de peso para distribución ('poblacion' o 'renta').
            db_path: Ruta a la base de datos (requerido si distribute=True).
        
        Returns:
            Tupla con (DataFrame con datos, metadata con advertencias).
        """
        # Extraer datos IDESCAT
        df_idescat, meta_idescat = self.extract_idescat_alquiler(year)
        
        # Extraer datos Open Data BCN (opcional)
        df_opendata, meta_opendata = self.extract_opendata_habitatge()
        
        combined_metadata = {
            "source": "vivienda_publica",
            "year": year,
            "success": meta_idescat.get("success", False),
            "has_idescat": df_idescat is not None,
            "has_opendata": df_opendata is not None,
            "level": "municipal" if not distribute else "barrio",
            "is_estimated": distribute,  # Marcar como estimado si se distribuye
        }
        
        if df_idescat is None:
            return None, combined_metadata
        
        # Si se solicita distribución, distribuir por barrios
        if distribute:
            logger.info(f"Distribuyendo datos municipales por barrios usando peso: {weight_type}")
            df_distributed, dist_meta = self.distribute_to_barrios(
                df_idescat,
                db_path=db_path,
                weight_type=weight_type,
                year=year
            )
            
            if df_distributed is not None:
                combined_metadata.update(dist_meta)
                combined_metadata["warning"] = (
                    "⚠️ Los valores son ESTIMACIONES por distribución proporcional, "
                    "no datos reales por barrio"
                )
                return df_distributed, combined_metadata
        
        # Si no se distribuye o falla la distribución, retornar datos municipales
        combined_metadata["warning"] = (
            "Datos a nivel municipal. Usar distribute=True para distribución por barrio "
            "(valores estimados)"
        )
        return df_idescat, combined_metadata

