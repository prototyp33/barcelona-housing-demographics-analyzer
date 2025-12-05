"""Tests para src.database_setup."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.database_setup import (
    InvalidTableNameError,
    create_connection,
    create_database_schema,
    ensure_database_path,
    register_etl_run,
    truncate_tables,
    validate_table_name,
)


def test_validate_table_name_valid():
    """Verifica que nombres de tabla válidos pasen la validación."""
    assert validate_table_name("dim_barrios") == "dim_barrios"
    assert validate_table_name("fact_precios") == "fact_precios"
    assert validate_table_name("fact_demografia") == "fact_demografia"


def test_validate_table_name_invalid():
    """Verifica que nombres de tabla inválidos lancen excepción."""
    with pytest.raises(InvalidTableNameError) as exc_info:
        validate_table_name("malicious_table; DROP TABLE users;--")
    
    assert "malicious_table" in str(exc_info.value)
    assert "Tablas permitidas" in str(exc_info.value)


def test_ensure_database_path_default():
    """Verifica que se cree la ruta por defecto correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        db_path = ensure_database_path(None, processed_dir)
        
        assert db_path == processed_dir / "database.db"
        assert processed_dir.exists()


def test_ensure_database_path_custom():
    """Verifica que se use la ruta personalizada si se proporciona."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        custom_path = Path(tmpdir) / "custom.db"
        db_path = ensure_database_path(custom_path, processed_dir)
        
        assert db_path == custom_path
        assert db_path.parent.exists()


def test_create_connection():
    """Verifica que se cree una conexión con foreign keys habilitadas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = create_connection(db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result[0] == 1  # Foreign keys habilitadas
        finally:
            conn.close()


def test_create_database_schema():
    """Verifica que se creen todas las tablas del esquema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = create_connection(db_path)
        
        try:
            create_database_schema(conn)
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                "dim_barrios",
                "fact_precios",
                "fact_demografia",
                "fact_demografia_ampliada",
                "fact_renta",
                "fact_oferta_idealista",
                "etl_runs",
            ]
            
            for table in expected_tables:
                assert table in tables, f"Tabla {table} no encontrada"
        finally:
            conn.close()


def test_truncate_tables():
    """Verifica que truncate_tables elimine datos correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = create_connection(db_path)
        
        try:
            create_database_schema(conn)
            
            # Insertar datos de prueba
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dim_barrios 
                (barrio_id, barrio_nombre, barrio_nombre_normalizado)
                VALUES (1, 'Test', 'test')
            """)
            cursor.execute("""
                INSERT INTO fact_precios 
                (barrio_id, anio, precio_m2_venta)
                VALUES (1, 2023, 3000.0)
            """)
            conn.commit()
            
            # Verificar que hay datos
            cursor.execute("SELECT COUNT(*) FROM dim_barrios")
            assert cursor.fetchone()[0] == 1
            cursor.execute("SELECT COUNT(*) FROM fact_precios")
            assert cursor.fetchone()[0] == 1
            
            # Truncar tablas
            truncate_tables(conn, ["dim_barrios", "fact_precios"])
            
            # Verificar que están vacías
            cursor.execute("SELECT COUNT(*) FROM dim_barrios")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM fact_precios")
            assert cursor.fetchone()[0] == 0
        finally:
            conn.close()


def test_truncate_tables_invalid_name():
    """Verifica que truncate_tables rechace nombres de tabla inválidos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = create_connection(db_path)
        
        try:
            create_database_schema(conn)
            
            with pytest.raises(InvalidTableNameError):
                truncate_tables(conn, ["malicious_table"])
        finally:
            conn.close()


def test_register_etl_run():
    """Verifica que se registre correctamente una ejecución ETL."""
    from datetime import datetime
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = create_connection(db_path)
        
        try:
            create_database_schema(conn)
            
            run_id = "test_run_123"
            started_at = datetime(2023, 1, 1, 10, 0, 0)
            finished_at = datetime(2023, 1, 1, 10, 5, 0)
            status = "success"
            parameters = {"year_start": 2020, "year_end": 2023}
            
            register_etl_run(
                conn, run_id, started_at, finished_at, status, parameters
            )
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT run_id, status FROM etl_runs WHERE run_id = ?",
                (run_id,)
            )
            result = cursor.fetchone()
            
            assert result is not None
            assert result[0] == run_id
            assert result[1] == status
        finally:
            conn.close()

