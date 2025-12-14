"""
Tests para migración de dim_barrios y cálculos geográficos.

Incluye tests para:
- Cálculo de centroides desde GeoJSON
- Cálculo de áreas desde geometrías
- Migración completa de dim_barrios
- Validación de datos geográficos
"""

import json
import pytest
import sqlite3
from pathlib import Path
from typing import Dict

from src.etl.migrations import (
    calculate_centroid,
    calculate_area_km2,
    migrate_dim_barrios_if_needed,
    get_ine_codes,
)


class TestCalculateCentroid:
    """Tests para cálculo de centroides."""

    def test_centroid_polygon_simple(self):
        """Test cálculo de centroide para Polygon simple."""
        geometry = {
            "type": "Polygon",
            "coordinates": [[[2.0, 41.0], [2.1, 41.0], [2.1, 41.1], [2.0, 41.1], [2.0, 41.0]]]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_centroid(geometry_json)
        
        assert result is not None
        lat, lon = result
        # Centroide debería estar en el centro del cuadrado
        assert 41.0 < lat < 41.1
        assert 2.0 < lon < 2.1
        assert abs(lat - 41.05) < 0.1
        assert abs(lon - 2.05) < 0.1

    def test_centroid_multipolygon(self):
        """Test cálculo de centroide para MultiPolygon."""
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[2.0, 41.0], [2.1, 41.0], [2.1, 41.1], [2.0, 41.1], [2.0, 41.0]]]
            ]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_centroid(geometry_json)
        
        assert result is not None
        lat, lon = result
        assert 41.0 < lat < 41.1
        assert 2.0 < lon < 2.1

    def test_centroid_invalid_geometry(self):
        """Test que retorna None para geometría inválida."""
        geometry = {
            "type": "Point",  # Tipo no soportado
            "coordinates": [2.0, 41.0]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_centroid(geometry_json)
        
        assert result is None

    def test_centroid_null_geometry(self):
        """Test que retorna None para geometría NULL."""
        result = calculate_centroid(None)
        assert result is None
        
        result = calculate_centroid("")
        assert result is None

    def test_centroid_invalid_json(self):
        """Test que retorna None para JSON inválido."""
        result = calculate_centroid("invalid json")
        assert result is None

    def test_centroid_barcelona_coordinates(self):
        """Test que centroides de Barcelona están en rango válido."""
        # Geometría aproximada de Barcelona
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [2.05, 41.35],  # SW
                [2.25, 41.35],  # SE
                [2.25, 41.45],  # NE
                [2.05, 41.45],  # NW
                [2.05, 41.35]   # Cerrar
            ]]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_centroid(geometry_json)
        
        assert result is not None
        lat, lon = result
        # Barcelona está aproximadamente en 41.38°N, 2.17°E
        assert 41.3 < lat < 41.5, f"Latitud {lat} fuera de rango Barcelona"
        assert 2.0 < lon < 2.3, f"Longitud {lon} fuera de rango Barcelona"


class TestCalculateArea:
    """Tests para cálculo de áreas."""

    def test_area_square_1km(self):
        """Test cálculo de área para cuadrado de ~1 km²."""
        # Cuadrado de ~1 grado (aproximadamente 111 km en latitud)
        # Para simplificar, usamos un cuadrado pequeño cerca de Barcelona
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [2.0, 41.0],
                [2.009, 41.0],  # ~1 km en longitud (aproximado)
                [2.009, 41.009],  # ~1 km en latitud
                [2.0, 41.009],
                [2.0, 41.0]
            ]]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_area_km2(geometry_json)
        
        assert result is not None
        assert result > 0
        # El área debería ser aproximadamente 1 km² (con tolerancia del 50% por aproximación)
        assert 0.5 < result < 2.0, f"Área {result} km² fuera de rango esperado"

    def test_area_multipolygon(self):
        """Test cálculo de área para MultiPolygon."""
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[2.0, 41.0], [2.01, 41.0], [2.01, 41.01], [2.0, 41.01], [2.0, 41.0]]],
                [[[2.02, 41.02], [2.03, 41.02], [2.03, 41.03], [2.02, 41.03], [2.02, 41.02]]]
            ]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_area_km2(geometry_json)
        
        assert result is not None
        assert result > 0

    def test_area_invalid_geometry(self):
        """Test que retorna None para geometría inválida."""
        geometry = {
            "type": "Point",
            "coordinates": [2.0, 41.0]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_area_km2(geometry_json)
        
        assert result is None

    def test_area_null_geometry(self):
        """Test que retorna None para geometría NULL."""
        result = calculate_area_km2(None)
        assert result is None
        
        result = calculate_area_km2("")
        assert result is None

    def test_area_barcelona_range(self):
        """Test que áreas de barrios de Barcelona están en rango razonable."""
        # Geometría típica de un barrio de Barcelona
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [2.15, 41.37],
                [2.16, 41.37],
                [2.16, 41.38],
                [2.15, 41.38],
                [2.15, 41.37]
            ]]
        }
        geometry_json = json.dumps(geometry)
        
        result = calculate_area_km2(geometry_json)
        
        assert result is not None
        # Barrios de Barcelona típicamente entre 0.1 y 20 km²
        assert 0.01 < result < 25.0, f"Área {result} km² fuera de rango razonable para barrio"


class TestGetINECodes:
    """Tests para función get_ine_codes()."""

    def test_get_ine_codes_loads_mapping(self):
        """Test que get_ine_codes() carga el mapeo correctamente."""
        codes = get_ine_codes()
        
        assert isinstance(codes, dict)
        # Debería tener al menos algunos códigos
        assert len(codes) > 0
        
        # Verificar formato de códigos
        for barrio_id, codigo in codes.items():
            assert isinstance(barrio_id, int)
            assert isinstance(codigo, str)
            # Formato esperado: 08019XXX
            assert codigo.startswith("08019"), f"Código {codigo} no sigue formato esperado"
            assert len(codigo) == 7, f"Código {codigo} no tiene longitud correcta"

    def test_get_ine_codes_all_barrios(self):
        """Test que el mapeo incluye todos los barrios (73)."""
        codes = get_ine_codes()
        
        # Debería tener 73 barrios
        assert len(codes) == 73, f"Esperado 73 barrios, encontrado {len(codes)}"
        
        # Verificar que los IDs van de 1 a 73
        barrio_ids = sorted(codes.keys())
        assert barrio_ids[0] == 1
        assert barrio_ids[-1] == 73


class TestMigrateDimBarrios:
    """Tests para migración completa de dim_barrios."""

    def test_migrate_dim_barrios_adds_columns(self, temp_db):
        """Test que la migración añade columnas si no existen."""
        conn = temp_db
        
        # Verificar que las columnas no existen inicialmente
        cursor = conn.execute("PRAGMA table_info(dim_barrios)")
        columns_before = {row[1] for row in cursor.fetchall()}
        
        # Ejecutar migración
        stats = migrate_dim_barrios_if_needed(conn)
        
        # Verificar que se añadieron columnas
        cursor = conn.execute("PRAGMA table_info(dim_barrios)")
        columns_after = {row[1] for row in cursor.fetchall()}
        
        new_columns = {"codigo_ine", "centroide_lat", "centroide_lon", "area_km2"}
        added_columns = new_columns - columns_before
        
        if added_columns:
            assert stats["columns_added"] > 0
            assert added_columns.issubset(columns_after)

    def test_migrate_dim_barrios_idempotent(self, temp_db_with_barrios):
        """Test que la migración es idempotente (puede ejecutarse múltiples veces)."""
        conn = temp_db_with_barrios
        
        # Ejecutar migración primera vez
        stats1 = migrate_dim_barrios_if_needed(conn)
        
        # Ejecutar migración segunda vez
        stats2 = migrate_dim_barrios_if_needed(conn)
        
        # La segunda vez no debería actualizar nada (o muy poco)
        # Verificar que los resultados son consistentes
        assert stats2["barrios_updated"] <= stats1["barrios_updated"]

    def test_migrate_dim_barrios_populates_ine_codes(self, temp_db_with_barrios):
        """Test que la migración pobla códigos INE."""
        conn = temp_db_with_barrios
        
        stats = migrate_dim_barrios_if_needed(conn)
        
        # Verificar que se poblaron códigos INE
        cursor = conn.execute("""
            SELECT COUNT(*) FROM dim_barrios WHERE codigo_ine IS NOT NULL
        """)
        count_with_ine = cursor.fetchone()[0]
        
        assert count_with_ine > 0
        assert stats.get("barrios_with_ine", 0) > 0

    def test_migrate_dim_barrios_validates_data(self, temp_db_with_barrios):
        """Test que la migración valida datos geográficos."""
        conn = temp_db_with_barrios
        
        stats = migrate_dim_barrios_if_needed(conn)
        
        # Verificar que centroides están en rango Barcelona
        cursor = conn.execute("""
            SELECT centroide_lat, centroide_lon
            FROM dim_barrios
            WHERE centroide_lat IS NOT NULL
            LIMIT 5
        """)
        
        for lat, lon in cursor.fetchall():
            assert 41.3 < lat < 41.5, f"Latitud {lat} fuera de rango Barcelona"
            assert 2.0 < lon < 2.3, f"Longitud {lon} fuera de rango Barcelona"
        
        # Verificar que áreas están en rango razonable
        cursor = conn.execute("""
            SELECT area_km2
            FROM dim_barrios
            WHERE area_km2 IS NOT NULL
            LIMIT 5
        """)
        
        for area, in cursor.fetchall():
            assert 0.01 < area < 25.0, f"Área {area} km² fuera de rango razonable"


# Fixtures

@pytest.fixture
def temp_db(tmp_path):
    """Crea una base de datos temporal para tests."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    # Crear tabla dim_barrios básica
    conn.execute("""
        CREATE TABLE dim_barrios (
            barrio_id INTEGER PRIMARY KEY,
            barrio_nombre TEXT NOT NULL,
            barrio_nombre_normalizado TEXT NOT NULL,
            geometry_json TEXT
        )
    """)
    conn.commit()
    
    yield conn
    
    conn.close()

@pytest.fixture
def temp_db_with_barrios(temp_db):
    """Crea base de datos temporal con algunos barrios de prueba."""
    conn = temp_db
    
    # Añadir algunos barrios con geometrías
    test_barrios = [
        (1, "el Raval", "el raval", json.dumps({
            "type": "Polygon",
            "coordinates": [[[2.17, 41.37], [2.18, 41.37], [2.18, 41.38], [2.17, 41.38], [2.17, 41.37]]]
        })),
        (2, "el Barri Gòtic", "el barri gotic", json.dumps({
            "type": "Polygon",
            "coordinates": [[[2.17, 41.38], [2.18, 41.38], [2.18, 41.39], [2.17, 41.39], [2.17, 41.38]]]
        })),
    ]
    
    conn.executemany("""
        INSERT INTO dim_barrios (barrio_id, barrio_nombre, barrio_nombre_normalizado, geometry_json)
        VALUES (?, ?, ?, ?)
    """, test_barrios)
    conn.commit()
    
    yield conn

