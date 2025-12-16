"""Tests para la dimensión temporal dim_tiempo."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from src.database_setup import create_connection, create_database_schema


def _get_conn(tmpdir: str) -> sqlite3.Connection:
    db_path = Path(tmpdir) / "test_dim_tiempo.db"
    return create_connection(db_path)


def test_dim_tiempo_created_and_populated() -> None:
    """Verifica que dim_tiempo se crea y se puebla para 2015-2024."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)

            cursor = conn.execute(
                """
                SELECT MIN(anio), MAX(anio), COUNT(*)
                FROM dim_tiempo
                """,
            )
            min_year, max_year, total = cursor.fetchone()

            assert min_year <= 2015
            assert max_year >= 2024
            # 10 años * (1 anual + 4 trimestrales) = 50 filas mínimas esperadas
            assert total >= 50
        finally:
            conn.close()


def test_dim_tiempo_idempotent() -> None:
    """Verifica que llamar a create_database_schema dos veces no duplica registros."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)
            cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
            first_count = cursor.fetchone()[0]

            create_database_schema(conn)
            cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
            second_count = cursor.fetchone()[0]

            assert first_count == second_count
        finally:
            conn.close()


