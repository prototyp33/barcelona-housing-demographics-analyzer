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
from typing import Any, Dict, List, Optional, Tuple

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
        "habitatges_tutelats": "serveissocials-habitatgestutelats",
        "cuotas_catastrales": "cuotas-catastrales",
        "licencias_obra_mayor": "licencies-obres-majors",
        "licencias_obra_menor": "licencies-obres-menors",
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

    def extract_idescat_vivienda_publica(self, year: int) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de vivienda protegida de IDESCAT a nivel municipal (EMEX).
        
        Args:
            year: Año de los datos.
        
        Returns:
            Tupla con (DataFrame con datos municipales, metadata).
        """
        logger.info(f"Extrayendo datos de vivienda IDESCAT para {year}...")
        
        coverage_metadata = {
            "source": "idescat_api",
            "year": year,
            "success": False,
            "level": "municipal",
        }
        
        try:
            # IDESCAT API endpoint para datos municipales (EMEX)
            endpoint = f"{self.IDESCAT_BASE_URL}/emex/v1/dades.json"
            params = {
                "lang": "es",
                "id": "080193",  # Código INE de Barcelona
            }
            
            self._rate_limit()
            response = self.session.get(endpoint, params=params, timeout=30)
            
            if not self._validate_response(response):
                coverage_metadata["error"] = f"Error HTTP {response.status_code}"
                return None, coverage_metadata
            
            data = response.json()
            
            # IDs de indicadores en EMEX Barcelona:
            # f13: Viviendas iniciadas de protección oficial
            # f14: Viviendas iniciadas (Total)
            # f15: Viviendas terminadas de protección oficial
            # f16: Viviendas terminadas (Total)
            # f250: Viviendas familiares principales
            # f398: Viviendas familiares no principales
            
            extracted_data = {"territorio": "Barcelona", "anio": year}
            
            target_ids = ["f13", "f14", "f15", "f16", "f250", "f398"]
            
            def find_indicators(obj, target_ids):
                results = {}
                if isinstance(obj, dict):
                    if obj.get("id") in target_ids:
                        val_str = str(obj.get("v", ""))
                        if val_str:
                            # En EMEX, v suele ser "valor_mun,valor_comarca,valor_cat"
                            vals = val_str.split(",")
                            try:
                                results[obj["id"]] = float(vals[0]) if vals[0].strip() and vals[0] != "_" else None
                            except (ValueError, IndexError):
                                pass
                    for k, v in obj.items():
                        results.update(find_indicators(v, target_ids))
                elif isinstance(obj, list):
                    for item in obj:
                        results.update(find_indicators(item, target_ids))
                return results

            found = find_indicators(data, target_ids)
            
            mapping = {
                "f13": "viviendas_iniciadas_vpo",
                "f14": "viviendas_iniciadas_total",
                "f15": "viviendas_terminadas_vpo",
                "f16": "viviendas_terminadas_total",
                "f250": "viviendas_principales",
                "f398": "viviendas_no_principales"
            }
            
            for fid, col in mapping.items():
                if fid in found:
                    extracted_data[col] = found[fid]
            
            # Alias para mantener compatibilidad con columnas existentes
            if "viviendas_iniciadas_vpo" in extracted_data:
                extracted_data["viviendas_proteccion_oficial"] = extracted_data["viviendas_iniciadas_vpo"]
            
            if len(found) == 0:
                logger.warning("No se encontraron indicadores de vivienda (f13/f14) en IDESCAT")
                coverage_metadata["error"] = "No se encontraron indicadores f13/f14"
                return None, coverage_metadata
            
            df = pd.DataFrame([extracted_data])
            logger.info(f"Datos IDESCAT extraídos: {extracted_data}")
            coverage_metadata["success"] = True
            coverage_metadata["total_records"] = 1
            
            # Guardar datos raw
            filepath = self._save_raw_data(
                data=df,
                filename=f"idescat_vivienda_{year}",
                format="csv",
                data_type="vivienda_publica",
                year_start=year,
                year_end=year
            )
            coverage_metadata["filepath"] = str(filepath)
            
            return df, coverage_metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo datos IDESCAT: {e}")
            logger.error(traceback.format_exc())
            coverage_metadata["error"] = str(e)
            return None, coverage_metadata

    def extract_licencias_obra(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de licencias de obra (mayor y menor) de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con licencias agregadas por barrio, metadata).
        """
        all_data = []
        metadata = {"sources": [], "success": False}
        
        for key in ["licencias_obra_mayor", "licencias_obra_menor"]:
            dataset_id = self.OPENDATA_DATASETS[key]
            logger.info(f"Extrayendo dataset de licencias: {dataset_id}")
            try:
                df, meta = self.opendata_extractor.download_dataset(dataset_id, resource_format='csv')
                if df is not None and not df.empty:
                    df['tipo_obra'] = "mayor" if "mayor" in key else "menor"
                    all_data.append(df)
                    metadata["sources"].append(dataset_id)
            except Exception as e:
                logger.error(f"Error extrayendo {dataset_id}: {e}")
        
        if not all_data:
            return None, metadata
            
        df_combined = pd.concat(all_data, ignore_index=True)
        metadata["success"] = True
        
        # Guardar raw
        filepath = self._save_raw_data(
            df_combined, 
            "opendatabcn_licencias_obra", 
            'csv',
            data_type="vivienda_publica"
        )
        metadata["filepath"] = str(filepath)
        
        return df_combined, metadata

    def extract_opendata_habitatge(self) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de vivienda protegida (habitatges tutelats) de Open Data BCN.
        
        Returns:
            Tupla con (DataFrame con datos por barrio, metadata).
        """
        dataset_id = self.OPENDATA_DATASETS["habitatges_tutelats"]
        logger.info(f"Extrayendo dataset '{dataset_id}' de Open Data BCN...")
        
        try:
            df, meta = self.opendata_extractor.download_dataset(
                dataset_id,
                resource_format='csv'
            )
            
            if df is not None and not df.empty:
                logger.info(f"✓ Dataset '{dataset_id}' extraído: {len(df)} registros")
                
                # Guardar datos raw
                filepath = self._save_raw_data(
                    data=df,
                    filename=f"opendatabcn_{dataset_id.replace('-', '_')}",
                    format="csv",
                    data_type="vivienda_publica"
                )
                meta["filepath"] = str(filepath)
                return df, meta
            
            return None, meta
            
        except Exception as e:
            logger.error(f"Error extrayendo '{dataset_id}': {e}")
            return None, {"error": str(e), "success": False}
    
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
            vpo_col = "viviendas_proteccion_oficial" if "viviendas_proteccion_oficial" in row.index else None
            total_iniciadas_col = "viviendas_iniciadas_total" if "viviendas_iniciadas_total" in row.index else None
            
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
                vpo = (
                    float(row[vpo_col]) if vpo_col and pd.notna(row[vpo_col])
                    else None
                )
                total_iniciadas = (
                    float(row[total_iniciadas_col]) if total_iniciadas_col and pd.notna(row[total_iniciadas_col])
                    else None
                )
                
                results.append({
                    "barrio_id": barrio_id,
                    "anio": year if year else None,
                    "viviendas_proteccion_oficial": (
                        round(vpo * proporcion, 2) if vpo is not None else None
                    ),
                    "viviendas_iniciadas_total": (
                        round(total_iniciadas * proporcion, 2) if total_iniciadas is not None else None
                    ),
                    "is_estimated": True,  # Marcar como estimado
                    "distribution_weight": weight_type,
                })
            
            df_distributed = pd.DataFrame(results)
            
            logger.info(f"Datos distribuidos para {len(df_distributed)} barrios")
            
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
                LEFT JOIN v_demografia_aggregated d ON db.barrio_id = d.barrio_id AND d.anio = ?
                WHERE peso > 0
                ORDER BY db.barrio_id
                """
                df = pd.read_sql_query(query, conn, params=[year])
                
                # Fallback if no data for specific year
                if df.empty:
                    logger.warning(f"No hay datos demográficos para {year}, intentando último disponible...")
                    year = None
            
            if not year:
                query = """
                SELECT 
                    db.barrio_id,
                    db.barrio_nombre,
                    COALESCE(MAX(d.poblacion_total), 0) as peso
                FROM dim_barrios db
                LEFT JOIN v_demografia_aggregated d ON db.barrio_id = d.barrio_id
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
        """
        # Extraer datos IDESCAT
        df_idescat, meta_idescat = self.extract_idescat_vivienda_publica(year)
        
        # Extraer datos Open Data BCN (habitatges tutelats)
        df_opendata, meta_opendata = self.extract_opendata_habitatge()
        
        # Extraer Licencias de Obra
        df_licencias, meta_lic = self.extract_licencias_obra()
        
        # Extraer Gencat (Viviendas vacías, demanda, ayudas)
        from .gencat import GencatExtractor
        gencat = GencatExtractor(output_dir=self.output_dir)
        meta_gencat = gencat.extract_all_housing()
        
        combined_metadata = {
            "source": "vivienda_publica_consolidada",
            "year": year,
            "success": meta_idescat.get("success", False) or meta_opendata.get("success", False),
            "has_idescat": df_idescat is not None,
            "has_opendata": df_opendata is not None,
            "has_licencias": df_licencias is not None,
            "has_gencat": any(m["success"] for m in meta_gencat.values()),
            "level": "mixed",
        }
        
        # Para mantener compatibilidad con el retorno esperado por el script antiguo
        if df_opendata is not None:
            return df_opendata, combined_metadata
            
        return df_idescat, combined_metadata
