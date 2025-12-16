"""Tests para migraciones de dim_barrios (centroides, área, códigos INE)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from src.database_setup import create_connection, create_database_schema
from src.etl.migrations import (
    calculate_area_km2,
    calculate_centroid,
    get_ine_codes,
    migrate_dim_barrios_if_needed,
)


def test_calculate_centroid_polygon() -> None:
    """Verifica que calculate_centroid calcula un centroide razonable para un polígono."""
    # Polígono rectangular aproximado en Barcelona
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [2.15, 41.39],
                [2.16, 41.39],
                [2.16, 41.40],
                [2.15, 41.40],
                [2.15, 41.39],
            ],
        ],
    }
    centroid = calculate_centroid(json.dumps(polygon))
    assert centroid is not None
    lat, lon = centroid
    # Rango aproximado de Barcelona
    assert 41.3 < lat < 41.5
    assert 2.1 < lon < 2.2


def test_calculate_area_km2_polygon() -> None:
    """Verifica que calculate_area_km2 devuelve un área positiva y razonable."""
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [2.15, 41.39],
                [2.16, 41.39],
                [2.16, 41.40],
                [2.15, 41.40],
                [2.15, 41.39],
            ],
        ],
    }
    area = calculate_area_km2(json.dumps(polygon))
    assert area is not None
    # Un rectángulo de ~0.01 x 0.01 grados debería dar un área pequeña pero >0
    assert 0.01 <= area <= 5.0


def test_get_ine_codes_missing_file_returns_empty_dict() -> None:
    """Verifica que get_ine_codes devuelve dict vacío si el archivo no existe."""
    mapping = get_ine_codes(mapping_path=Path("no_existe_ine_mapping.json"))
    assert mapping == {}


def test_migrate_dim_barrios_if_needed_updates_columns() -> None:
    """Verifica que la migración añade columnas y calcula centroides/área."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_dim_barrios_migration.db"
        conn = create_connection(db_path)
        try:
            create_database_schema(conn)

            # Insertar un barrio con geometría simple
            polygon = {
                "type": "Polygon",
                "coordinates": [
                    [
                        [2.15, 41.39],
                        [2.16, 41.39],
                        [2.16, 41.40],
                        [2.15, 41.40],
                        [2.15, 41.39],
                    ],
                ],
            }
            conn.execute(
                """
                INSERT INTO dim_barrios (
                    barrio_id, barrio_nombre, barrio_nombre_normalizado,
                    distrito_id, distrito_nombre, municipio, ambito,
                    codi_districte, codi_barri, geometry_json,
                    source_dataset, etl_created_at, etl_updated_at
                ) VALUES (1, 'Test', 'test', 1, 'Distrito', 'Barcelona', 'barri',
                          '01', '01', ?, 'test', 'ts', 'ts')
                """,
                (json.dumps(polygon),),
            )
            conn.commit()

            migrate_dim_barrios_if_needed(conn)

            cursor = conn.execute(
                """
                SELECT centroide_lat, centroide_lon, area_km2
                FROM dim_barrios
                WHERE barrio_id = 1
                """,
            )
            row = cursor.fetchone()
            assert row is not None
            centroide_lat, centroide_lon, area_km2 = row
            assert centroide_lat is not None
            assert centroide_lon is not None
            assert area_km2 is not None
            assert 41.3 < centroide_lat < 41.5
            assert 2.1 < centroide_lon < 2.2
            assert 0.01 <= area_km2 <= 5.0
        finally:
            conn.close()


