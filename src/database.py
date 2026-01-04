"""
Database management module for the Barcelona Housing Demographics Analyzer.

Provides a centralized class to manage SQLite connections, ensure referential
integrity, and compute data quality metrics.
"""

from __future__ import annotations

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

from src.app.config import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database connections and providing metrics for the dashboard.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initializes the DatabaseManager.

        Args:
            db_path: Path to the SQLite database. If None, uses DB_PATH from config.
        """
        self.db_path = db_path or DB_PATH
        if not self.db_path.exists():
            logger.warning(f"Database not found at {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Creates a connection to the SQLite database.

        Returns:
            SQLite connection with foreign keys enabled.

        Raises:
            FileNotFoundError: If the database file does not exist.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Calcula métricas de calidad de datos para el dashboard de monitoreo.

        Returns:
            Diccionario con completeness, validity, consistency y timeliness.
        """
        from src.app.data_quality_metrics import (
            calculate_completeness,
            calculate_validity,
            calculate_consistency,
            calculate_timeliness
        )
        
        return {
            "completeness": calculate_completeness(),
            "validity": calculate_validity(),
            "consistency": calculate_consistency(),
            "timeliness": calculate_timeliness()
        }

    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns the result as a pandas DataFrame.

        Args:
            query: SQL query to execute.
            params: Parameters for the query.

        Returns:
            DataFrame with the results.
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def table_exists(self, table_name: str) -> bool:
        """
        Checks if a table or view exists in the database.

        Args:
            table_name: Name of the table or view to check.

        Returns:
            True if the table/view exists, False otherwise.
        """
        query = "SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name=?"
        df = self.execute_query(query, (table_name,))
        return not df.empty

