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
    
    def get_barrios(self, distrito: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all barrios, optionally filtered by distrito.
        
        Args:
            distrito: Optional distrito name filter
            
        Returns:
            List of barrio dictionaries
        """
        conn = self.get_connection()
        if conn is None:
            return []
        
        try:
            query = "SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios"
            
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
