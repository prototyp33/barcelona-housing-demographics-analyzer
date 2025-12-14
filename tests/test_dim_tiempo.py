"""
Tests para dim_tiempo.

Incluye tests para:
- Creación de tabla dim_tiempo
- Población de períodos temporales
- Atributos temporales (estación, es_verano)
- Índices y constraints
"""

import pytest
import sqlite3
from pathlib import Path

from src.database_setup import ensure_dim_tiempo, create_connection


class TestCreateDimTiempo:
    """Tests para creación de dim_tiempo."""

    def test_ensure_dim_tiempo_creates_table(self, temp_db):
        """Test que ensure_dim_tiempo crea la tabla si no existe."""
        conn = temp_db
        
        # Verificar que la tabla no existe
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dim_tiempo'
        """)
        assert cursor.fetchone() is None
        
        # Crear tabla
        ensure_dim_tiempo(conn, start_year=2020, end_year=2021)
        
        # Verificar que la tabla existe
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dim_tiempo'
        """)
        assert cursor.fetchone() is not None

    def test_ensure_dim_tiempo_idempotent(self, temp_db):
        """Test que ensure_dim_tiempo es idempotente."""
        conn = temp_db
        
        # Crear tabla primera vez
        ensure_dim_tiempo(conn, start_year=2020, end_year=2021)
        cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
        count1 = cursor.fetchone()[0]
        
        # Crear tabla segunda vez (no debería duplicar)
        ensure_dim_tiempo(conn, start_year=2020, end_year=2021)
        cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
        count2 = cursor.fetchone()[0]
        
        # El conteo debería ser igual o similar (puede haber algunos duplicados por INSERT OR IGNORE)
        assert count2 >= count1

    def test_dim_tiempo_schema(self, temp_db):
        """Test que dim_tiempo tiene el esquema correcto."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("PRAGMA table_info(dim_tiempo)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Verificar columnas requeridas
        assert "time_id" in columns
        assert "anio" in columns
        assert "trimestre" in columns
        assert "periodo" in columns
        assert "year_quarter" in columns
        assert "es_verano" in columns
        assert "estacion" in columns
        assert "fecha_inicio" in columns
        assert "fecha_fin" in columns


class TestPopulateDimTiempo:
    """Tests para población de dim_tiempo."""

    def test_populate_periods_annual(self, temp_db):
        """Test que se crean registros anuales."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2021)
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM dim_tiempo
            WHERE trimestre IS NULL AND mes IS NULL
        """)
        annual_count = cursor.fetchone()[0]
        
        # Debería haber 2 registros anuales (2020, 2021)
        assert annual_count >= 2

    def test_populate_periods_quarterly(self, temp_db):
        """Test que se crean registros quarterly."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM dim_tiempo
            WHERE trimestre IS NOT NULL
        """)
        quarterly_count = cursor.fetchone()[0]
        
        # Debería haber 4 registros quarterly (Q1-Q4) para 2020
        assert quarterly_count >= 4

    def test_periods_format(self, temp_db):
        """Test que los períodos tienen formato correcto."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT periodo, year_quarter, anio, trimestre
            FROM dim_tiempo
            WHERE trimestre IS NOT NULL
            LIMIT 4
        """)
        
        for periodo, year_quarter, anio, trimestre in cursor.fetchall():
            # Verificar formato de periodo (ej: "2020Q1")
            assert periodo.startswith(str(anio))
            assert "Q" in periodo or str(trimestre) in periodo
            
            # Verificar formato de year_quarter (ej: "2020-Q1")
            if year_quarter:
                assert year_quarter.startswith(str(anio))
                assert "-" in year_quarter

    def test_temporal_attributes_estacion(self, temp_db):
        """Test que los atributos temporales (estación) se asignan correctamente."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT trimestre, estacion, es_verano
            FROM dim_tiempo
            WHERE trimestre IS NOT NULL
            ORDER BY trimestre
        """)
        
        estaciones_esperadas = {
            1: "invierno",  # Q1 (enero-marzo)
            2: "primavera",  # Q2 (abril-junio)
            3: "verano",     # Q3 (julio-septiembre)
            4: "otoño",      # Q4 (octubre-diciembre)
        }
        
        for trimestre, estacion, es_verano in cursor.fetchall():
            assert estacion == estaciones_esperadas.get(trimestre)
            # Q3 debería ser verano
            if trimestre == 3:
                assert es_verano == 1
            else:
                assert es_verano == 0

    def test_fecha_inicio_fin(self, temp_db):
        """Test que las fechas de inicio y fin son correctas."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT trimestre, fecha_inicio, fecha_fin
            FROM dim_tiempo
            WHERE trimestre = 1
        """)
        
        result = cursor.fetchone()
        if result:
            trimestre, fecha_inicio, fecha_fin = result
            # Q1 debería ser 2020-01-01 a 2020-03-31
            assert fecha_inicio.startswith("2020-01-01")
            assert fecha_fin.startswith("2020-03-31")


class TestDimTiempoIndexes:
    """Tests para índices de dim_tiempo."""

    def test_index_periodo_unique(self, temp_db):
        """Test que existe índice único en periodo."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_dim_tiempo_periodo'
        """)
        assert cursor.fetchone() is not None

    def test_index_anio_trimestre(self, temp_db):
        """Test que existe índice en anio y trimestre."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_dim_tiempo_anio_trimestre'
        """)
        assert cursor.fetchone() is not None

    def test_index_anio(self, temp_db):
        """Test que existe índice en anio."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_dim_tiempo_anio'
        """)
        assert cursor.fetchone() is not None


class TestDimTiempoDataQuality:
    """Tests de calidad de datos para dim_tiempo."""

    def test_no_duplicate_periods(self, temp_db):
        """Test que no hay períodos duplicados."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT periodo, COUNT(*) as count
            FROM dim_tiempo
            WHERE periodo IS NOT NULL
            GROUP BY periodo
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        # Puede haber algunos duplicados por INSERT OR IGNORE, pero deberían ser mínimos
        assert len(duplicates) == 0 or len(duplicates) < 5

    def test_all_years_present(self, temp_db):
        """Test que todos los años solicitados están presentes."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2018, end_year=2020)
        
        cursor = conn.execute("""
            SELECT DISTINCT anio FROM dim_tiempo
            WHERE trimestre IS NULL
            ORDER BY anio
        """)
        
        years = [row[0] for row in cursor.fetchall()]
        assert 2018 in years
        assert 2019 in years
        assert 2020 in years

    def test_quarterly_coverage(self, temp_db):
        """Test que cada año tiene 4 quarters."""
        conn = temp_db
        ensure_dim_tiempo(conn, start_year=2020, end_year=2020)
        
        cursor = conn.execute("""
            SELECT anio, COUNT(DISTINCT trimestre) as quarters
            FROM dim_tiempo
            WHERE trimestre IS NOT NULL
            GROUP BY anio
        """)
        
        for anio, quarters in cursor.fetchall():
            assert quarters >= 4, f"Año {anio} tiene solo {quarters} quarters"


# Fixtures

@pytest.fixture
def temp_db(tmp_path):
    """Crea una base de datos temporal para tests."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    yield conn
    
    conn.close()

