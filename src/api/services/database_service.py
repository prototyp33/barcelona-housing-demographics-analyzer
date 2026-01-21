"""Database service for accessing SQLite data."""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database service.
        
        Args:
            db_path: Path to SQLite database. If None, uses default location.
        """
        if db_path is None:
            processed_path = PROJECT_ROOT / "data" / "processed" / "database.db"
            master_path = PROJECT_ROOT / "data" / "master.db"
            
            if processed_path.exists():
                self.db_path = processed_path
            elif master_path.exists():
                self.db_path = master_path
            else:
                logger.error("No database found")
                self.db_path = None
        else:
            self.db_path = db_path
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection.
        
        Returns:
            SQLite connection or None if database not found
        """
        if self.db_path is None or not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return None
    
    def _sanitize_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sanitize DataFrame by replacing NaN/Inf with None and converting to dict list.
        
        Args:
            df: DataFrame to sanitize
            
        Returns:
            List of dictionaries compatible with JSON
        """
        if df.empty:
            return []
        
        # Replace inf with NaN first
        df = df.replace([float('inf'), float('-inf')], pd.NA)
        
        # Convert to object and replace NA/NaN with None for JSON compliance
        return df.astype(object).where(pd.notnull(df), None).to_dict('records')

    def get_barrios(self, distrito: Optional[str] = None, include_geometry: bool = False) -> List[Dict[str, Any]]:
        """Get all barrios, optionally filtered by distrito.
        
        Args:
            distrito: Optional distrito name filter
            include_geometry: Whether to include GeoJSON geometry
            
        Returns:
            List of barrio dictionaries
        """
        conn = self.get_connection()
        if conn is None:
            return []
        
        try:
            cols = "barrio_id, barrio_nombre, distrito_id, distrito_nombre"
            if include_geometry:
                cols += ", geometry_json"
            
            query = f"SELECT {cols} FROM dim_barrios"
            
            if distrito:
                query += " WHERE distrito_nombre = ?"
                df = pd.read_sql_query(query, conn, params=(distrito,))
            else:
                df = pd.read_sql_query(query, conn)
            
            return self._sanitize_df(df)
        except Exception as e:
            logger.error(f"Error fetching barrios: {e}")
            return []
        finally:
            conn.close()

    def get_available_years(self) -> Dict[str, Dict[str, Optional[int]]]:
        """Get available years for data tables."""
        conn = self.get_connection()
        if conn is None:
            return {}
        
        try:
            result = {}
            tables = [
                "fact_precios", "v_demografia_aggregated", "fact_renta", 
                "fact_renta_avanzada", "fact_educacion", "fact_seguridad", 
                "fact_vivienda_publica", "fact_presion_turistica"
            ]
            for table in tables:
                try:
                    df = pd.read_sql(
                        f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {table}",
                        conn,
                    )
                    result[table] = {
                        "min": int(df["min_year"].iloc[0]) if pd.notna(df["min_year"].iloc[0]) else None,
                        "max": int(df["max_year"].iloc[0]) if pd.notna(df["max_year"].iloc[0]) else None,
                    }
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.error(f"Error fetching years: {e}")
            return {}
        finally:
            conn.close()

    def get_distritos(self) -> List[str]:
        """Get unique list of distritos."""
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            df = pd.read_sql("SELECT DISTINCT distrito_nombre FROM dim_barrios ORDER BY distrito_nombre", conn)
            return df["distrito_nombre"].tolist()
        finally:
            conn.close()

    def get_precios(self, year: int, distrito: Optional[str] = None, include_geometry: bool = False) -> List[Dict[str, Any]]:
        """Get consolidated prices for a year."""
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            geom_col = ", b.geometry_json" if include_geometry else ""
            query = f"""
            SELECT 
                p.barrio_id, b.barrio_nombre, b.distrito_nombre {geom_col},
                AVG(p.precio_m2_venta) as avg_precio_m2, 
                AVG(p.precio_mes_alquiler) as avg_alquiler
            FROM fact_precios p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.anio = ?
            """
            params = [year]
            if distrito:
                query += " AND b.distrito_nombre = ?"
                params.append(distrito)
            
            query += " GROUP BY p.barrio_id"
            df = pd.read_sql(query, conn, params=params)
            return self._sanitize_df(df)
        finally:
            conn.close()

    def get_investment_metrics(self, year: int) -> List[Dict[str, Any]]:
        """
        Get specialized investment metrics:
        - Entry Cost (X): "Venta: Precio Oferta" (dataset_id: bhl3ulphi5)
        - Return (Y): "Alquiler: Mensual" (dataset_id: b37xv8wcjh - Incasòl)
        """
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            query = """
            WITH offer_prices AS (
                SELECT barrio_id, AVG(precio_m2_venta) as entry_cost
                FROM fact_precios
                WHERE anio = ? AND dataset_id = 'bhl3ulphi5'
                GROUP BY barrio_id
            ),
            contract_rents AS (
                SELECT barrio_id, AVG(precio_mes_alquiler) as rental_income
                FROM fact_precios
                WHERE anio = ? AND dataset_id = 'b37xv8wcjh'
                GROUP BY barrio_id
            )
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre,
                o.entry_cost as avg_precio_m2,
                c.rental_income as avg_alquiler
            FROM dim_barrios b
            JOIN offer_prices o ON b.barrio_id = o.barrio_id
            JOIN contract_rents c ON b.barrio_id = c.barrio_id
            """
            df = pd.read_sql(query, conn, params=[year, year])
            return self._sanitize_df(df)
        finally:
            conn.close()

    def get_renta(self, year: int = 2023) -> List[Dict[str, Any]]:
        """Get income data (attempts multiple columns)."""
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            # Try fact_renta first but be flexible with column names
            query = """
                SELECT 
                    barrio_id, 
                    COALESCE(renta_mediana, renta_promedio, renta_euros) as renta_euros 
                FROM fact_renta 
                WHERE anio = ?
            """
            df = pd.read_sql(query, conn, params=[year])
            if not df.empty:
                return self._sanitize_df(df)
            
            # Fallback to fact_renta_avanzada
            df = pd.read_sql("SELECT barrio_id, renta_bruta_llar as renta_euros FROM fact_renta_avanzada WHERE anio = ?", conn, params=[year])
            return self._sanitize_df(df)
        except Exception as e:
            logger.error(f"Error fetching renta for year {year}: {e}")
            return []
        finally:
            conn.close()

    def get_kpis(self) -> Dict[str, Any]:
        """Get global project KPIs matching the dashboard expectations."""
        conn = self.get_connection()
        if conn is None: return {}
        try:
            # Total barrios
            barrios_n = pd.read_sql("SELECT COUNT(*) as n FROM dim_barrios", conn).iloc[0]['n']
            
            # Barrios con geometría
            geom_n = pd.read_sql("SELECT COUNT(*) as n FROM dim_barrios WHERE geometry_json IS NOT NULL", conn).iloc[0]['n']
            
            # Total precios records
            precios_n = pd.read_sql("SELECT COUNT(*) as n FROM fact_precios", conn).iloc[0]['n']
            
            # Years range from prices
            years = pd.read_sql("SELECT MIN(anio) as min_y, MAX(anio) as max_y FROM fact_precios", conn)
            max_year = int(years['max_y'].iloc[0]) if pd.notna(years['max_y'].iloc[0]) else 2022
            prev_year = max_year - 1
            
            # Price averages for comparison
            prices_cmp = pd.read_sql(f"""
                SELECT anio, AVG(precio_m2_venta) as avg_price, AVG(precio_mes_alquiler) as avg_rent
                FROM fact_precios 
                WHERE anio IN ({prev_year}, {max_year}) 
                GROUP BY anio
            """, conn)
            
            price_curr = float(prices_cmp[prices_cmp['anio'] == max_year]['avg_price'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == max_year].empty else 0.0
            price_prev = float(prices_cmp[prices_cmp['anio'] == prev_year]['avg_price'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == prev_year].empty else 0.0
            rent_curr = float(prices_cmp[prices_cmp['anio'] == max_year]['avg_rent'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == max_year].empty else 0.0
            
            # Global income (fallback logic for different years/columns)
            income_latest = pd.read_sql("SELECT AVG(renta_mediana) as avg_income FROM fact_renta WHERE anio = 2023", conn).iloc[0]['avg_income']
            if income_latest is None:
                income_latest = pd.read_sql("SELECT AVG(renta_euros) as avg_income FROM fact_renta WHERE anio = 2022", conn).iloc[0]['avg_income']
            
            return {
                "total_barrios": int(barrios_n),
                "barrios_con_geometria": int(geom_n),
                "registros_precios": int(precios_n),
                "año_min": int(years['min_y'].iloc[0]) if pd.notna(years['min_y'].iloc[0]) else None,
                "año_max": max_year,
                f"precio_medio_{max_year}": price_curr,
                f"precio_medio_{prev_year}": price_prev,
                f"alquiler_medio_{max_year}": rent_curr,
                "renta_media_actual": float(income_latest or 0)
            }
        finally:
            conn.close()
    
    def get_barrio_detail(self, barrio_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific barrio.
        
        Args:
            barrio_id: Barrio ID
            
        Returns:
            Dictionary with barrio details or None
        """
        conn = self.get_connection()
        if conn is None:
            return None
        
        try:
            query = """
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                p.precio_m2_venta as avg_venta_23,
                r.renta_bruta_llar,
                d.poblacion_total,
                c.num_plantas_avg,
                c.antiguedad_media_bloque,
                c.indice_penalizacion_topografica
            FROM dim_barrios b
            LEFT JOIN (
                SELECT barrio_id, AVG(precio_m2_venta) as precio_m2_venta
                FROM fact_precios
                WHERE anio = 2023 AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ) p ON b.barrio_id = p.barrio_id
            LEFT JOIN fact_renta_avanzada r ON b.barrio_id = r.barrio_id AND r.anio = 2023
            LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND d.anio = 2023
            LEFT JOIN fact_catastro_avanzado c ON b.barrio_id = c.barrio_id AND c.anio = 2023
            WHERE b.barrio_id = ?
            """
            
            df = pd.read_sql_query(query, conn, params=(barrio_id,))
            
            if df.empty:
                return None
            
            # Replace NaN/Inf in the single record
            record = df.iloc[0].to_dict()
            return {k: (v if pd.notnull(v) else None) for k, v in record.items()}
        except Exception as e:
            logger.error(f"Error fetching barrio detail: {e}")
            return None
        finally:
            conn.close()
    
    def get_price_evolution(self, barrio_id: Optional[int] = None) -> pd.DataFrame:
        """Get price evolution over time.
        
        Args:
            barrio_id: Optional barrio ID filter
            
        Returns:
            DataFrame with price evolution
        """
        conn = self.get_connection()
        if conn is None:
            return pd.DataFrame()
        
        try:
            query = """
            SELECT 
                p.anio,
                b.barrio_nombre,
                AVG(p.precio_m2_venta) as avg_price
            FROM fact_precios p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.precio_m2_venta IS NOT NULL
            """
            
            if barrio_id:
                query += " AND p.barrio_id = ?"
                query += " GROUP BY p.anio, b.barrio_nombre ORDER BY p.anio"
                df = pd.read_sql_query(query, conn, params=(barrio_id,))
            else:
                query += " GROUP BY p.anio, b.barrio_nombre ORDER BY p.anio"
                df = pd.read_sql_query(query, conn)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching price evolution: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_accessibility_metrics(self, year: int, distrito: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get accessibility and social infrastructure metrics."""
        conn = self.get_connection()
        if conn is None: return []
        try:
            query = """
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre,
                e.total_centros_educativos,
                e.num_centros_infantil,
                e.num_centros_primaria,
                e.num_centros_secundaria,
                e.num_centros_universidad,
                v.viviendas_proteccion_oficial as viviendas_publicas
            FROM dim_barrios b
            LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = ?
            LEFT JOIN fact_vivienda_publica v ON b.barrio_id = v.barrio_id AND v.anio = ?
            """
            params = [year, year]
            if distrito:
                query += " WHERE b.distrito_nombre = ?"
                params.append(distrito)
            
            df = pd.read_sql(query, conn, params=params)
            return self._sanitize_df(df)
        finally:
            conn.close()

    def get_safety_and_tourism(self, year: int, distrito: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get safety and tourism pressure metrics."""
        conn = self.get_connection()
        if conn is None: return []
        try:
            query = """
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre,
                s.tasa_criminalidad_1000hab,
                s.delitos_patrimonio,
                t.num_listings_airbnb,
                t.pct_entire_home,
                t.precio_noche_promedio
            FROM dim_barrios b
            LEFT JOIN fact_seguridad s ON b.barrio_id = s.barrio_id AND s.anio = ?
            LEFT JOIN fact_presion_turistica t ON b.barrio_id = t.barrio_id AND t.anio = ?
            """
            params = [year, year]
            if distrito:
                query += " WHERE b.distrito_nombre = ?"
                params.append(distrito)
            
            df = pd.read_sql(query, conn, params=params)
            return self._sanitize_df(df)
        finally:
            conn.close()

    def get_equity_metrics(self) -> List[Dict[str, Any]]:
        """Get model fairness/equity metrics.
        Note: Currently these are loaded from fact_model_fairness (if exists) 
        or return the latest calibrated results from Phase 3.
        """
        conn = self.get_connection()
        if conn is None: return []
        try:
            # Check if fact_model_fairness table exists
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fact_model_fairness'")
            if cursor.fetchone():
                query = "SELECT * FROM fact_model_fairness ORDER BY etl_loaded_at DESC"
                df = pd.read_sql(query, conn)
                return self._sanitize_df(df)
            else:
                # Return latest Phase 3 snapshot as fallback
                return [{
                    "model_version": "V2-Optimized",
                    "distrito_nombre": "Barcelona Global",
                    "mae": 409.40,
                    "r2": 0.7591,
                    "ges": 0.4266,
                    "ipr": 1.0027,
                    "status": "Target Met (IPR)"
                }]
        except Exception as e:
            logger.error(f"Error fetching equity metrics: {e}")
            return []
        finally:
            conn.close()

    def health_check(self) -> bool:
        """Check if database is accessible.
        
        Returns:
            True if database is accessible
        """
        conn = self.get_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM dim_barrios")
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            conn.close()


# Global instance
_db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """Get or create the global database service instance.
    
    Returns:
        DatabaseService instance
    """
    global _db_service
    
    if _db_service is None:
        _db_service = DatabaseService()
    
    return _db_service
