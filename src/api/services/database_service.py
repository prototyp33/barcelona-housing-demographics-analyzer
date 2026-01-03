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
            # Try master.db first, then processed/database.db
            master_path = PROJECT_ROOT / "data" / "master.db"
            processed_path = PROJECT_ROOT / "data" / "processed" / "database.db"
            
            if master_path.exists():
                self.db_path = master_path
            elif processed_path.exists():
                self.db_path = processed_path
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
            
            return df.to_dict('records')
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
            tables = ["fact_precios", "fact_demografia", "fact_renta", "fact_renta_avanzada"]
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
            return df.to_dict('records')
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
            return df.to_dict('records')
        finally:
            conn.close()

    def get_renta(self, year: int = 2022) -> List[Dict[str, Any]]:
        """Get income data (prefers fact_renta_avanzada)."""
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            # Try fact_renta first as it matches 'renta_euros'
            try:
                df = pd.read_sql("SELECT barrio_id, renta_euros FROM fact_renta WHERE anio = ?", conn, params=[year])
                if not df.empty:
                    return df.to_dict('records')
            except Exception:
                pass
            
            # Fallback to fact_renta_avanzada
            df = pd.read_sql("SELECT barrio_id, renta_bruta_llar FROM fact_renta_avanzada WHERE anio = ?", conn, params=[year])
            return df.to_dict('records')
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
            
            # Price averages for comparison (2022 vs 2021)
            prices_cmp = pd.read_sql("""
                SELECT anio, AVG(precio_m2_venta) as avg_price, AVG(precio_mes_alquiler) as avg_rent
                FROM fact_precios 
                WHERE anio IN (2021, 2022) 
                GROUP BY anio
            """, conn)
            
            price_22 = float(prices_cmp[prices_cmp['anio'] == 2022]['avg_price'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == 2022].empty else 0.0
            price_21 = float(prices_cmp[prices_cmp['anio'] == 2021]['avg_price'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == 2021].empty else 0.0
            rent_22 = float(prices_cmp[prices_cmp['anio'] == 2022]['avg_rent'].iloc[0]) if not prices_cmp[prices_cmp['anio'] == 2022].empty else 0.0
            
            # Global income (2022)
            income_22 = pd.read_sql("SELECT AVG(renta_euros) as avg_income FROM fact_renta WHERE anio = 2022", conn).iloc[0]['avg_income']
            
            return {
                "total_barrios": int(barrios_n),
                "barrios_con_geometria": int(geom_n),
                "registros_precios": int(precios_n),
                "año_min": int(years['min_y'].iloc[0]) if pd.notna(years['min_y'].iloc[0]) else None,
                "año_max": int(years['max_y'].iloc[0]) if pd.notna(years['max_y'].iloc[0]) else None,
                "precio_medio_2022": price_22,
                "precio_medio_2021": price_21,
                "alquiler_medio_2022": rent_22,
                "renta_media_2022": float(income_22 or 0)
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
            
            return df.iloc[0].to_dict()
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
                df = pd.read_sql_query(query, conn, params=(barrio_id,))
            else:
                df = pd.read_sql_query(query, conn)
            
            query += " GROUP BY p.anio, b.barrio_nombre ORDER BY p.anio"
            
            return df
        except Exception as e:
            logger.error(f"Error fetching price evolution: {e}")
            return pd.DataFrame()
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
