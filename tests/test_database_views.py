"""Tests para las vistas analíticas definidas en src.database_views."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from src.database_setup import create_connection, create_database_schema
from src.database_views import create_analytical_views


def _get_conn(tmpdir: str) -> sqlite3.Connection:
    db_path = Path(tmpdir) / "test_database_views.db"
    return create_connection(db_path)


def test_create_analytical_views_basic() -> None:
    """Verifica que las vistas principales se crean sin errores."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)
            create_analytical_views(conn)

            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'view'
                ORDER BY name
                """,
            )
            view_names = {row[0] for row in cursor.fetchall()}

            assert "v_affordability_quarterly" in view_names
            assert "v_precios_evolucion_anual" in view_names
            assert "v_demografia_resumen" in view_names
            assert "v_gentrificacion_tendencias" in view_names
        finally:
            conn.close()


def test_v_precios_evolucion_anual_returns_data() -> None:
    """Verifica que v_precios_evolucion_anual agrega correctamente precios anuales."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)

            # Insertar dim_barrios para cumplir la FK
            conn.execute(
                """
                INSERT INTO dim_barrios (
                    barrio_id, barrio_nombre, barrio_nombre_normalizado,
                    distrito_id, distrito_nombre, municipio, ambito,
                    codi_districte, codi_barri, geometry_json,
                    source_dataset, etl_created_at, etl_updated_at
                ) VALUES (1, 'Test', 'test', 1, 'Distrito', 'Barcelona', 'barri',
                          '01', '01', NULL, 'test', 'ts', 'ts')
                """,
            )

            # Insertar datos mínimos en fact_precios
            conn.execute(
                """
                INSERT INTO fact_precios (
                    barrio_id, anio, periodo, trimestre,
                    precio_m2_venta, precio_mes_alquiler,
                    dataset_id, source, etl_loaded_at
                ) VALUES (1, 2020, '2020', NULL, 3000.0, NULL, 'test', 'unit', 'ts')
                """,
            )
            conn.commit()

            create_analytical_views(conn)

            cursor = conn.execute(
                "SELECT barrio_id, anio, precio_m2_venta_promedio FROM v_precios_evolucion_anual",
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 1
            assert row[1] == 2020
            assert row[2] == 3000.0
        finally:
            conn.close()


def test_v_demografia_resumen_join_structure() -> None:
    """Verifica que v_demografia_resumen realiza el join con dim_barrios correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)

            conn.execute(
                """
                INSERT INTO dim_barrios (
                    barrio_id, barrio_nombre, barrio_nombre_normalizado,
                    distrito_id, distrito_nombre, municipio, ambito,
                    codi_districte, codi_barri, geometry_json,
                    source_dataset, etl_created_at, etl_updated_at
                ) VALUES (1, 'Test', 'test', 1, 'Distrito', 'Barcelona', 'barri',
                          '01', '01', NULL, 'test', 'ts', 'ts')
                """,
            )
            conn.execute(
                """
                INSERT INTO fact_demografia (
                    barrio_id, anio, poblacion_total,
                    poblacion_hombres, poblacion_mujeres,
                    hogares_totales, edad_media, porc_inmigracion,
                    densidad_hab_km2, pct_mayores_65, pct_menores_15,
                    indice_envejecimiento, dataset_id, source, etl_loaded_at
                ) VALUES (1, 2020, 1000, 480, 520, 400, 40.0, 10.0, 10000.0,
                          12.5, 15.0, 0.83, 'test', 'unit', 'ts')
                """,
            )
            conn.commit()

            create_analytical_views(conn)

            cursor = conn.execute(
                """
                SELECT barrio_id, barrio_nombre, anio, poblacion_total
                FROM v_demografia_resumen
                """,
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 1
            assert row[1] == "Test"
            assert row[2] == 2020
            assert row[3] == 1000
        finally:
            conn.close()


def test_v_gentrificacion_tendencias_basic_signal() -> None:
    """Verifica que v_gentrificacion_tendencias produce al menos una fila válida."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conn = _get_conn(tmpdir)
        try:
            create_database_schema(conn)

            conn.execute(
                """
                INSERT INTO dim_barrios (
                    barrio_id, barrio_nombre, barrio_nombre_normalizado,
                    distrito_id, distrito_nombre, municipio, ambito,
                    codi_districte, codi_barri, geometry_json,
                    source_dataset, etl_created_at, etl_updated_at
                ) VALUES (1, 'Test', 'test', 1, 'Distrito', 'Barcelona', 'barri',
                          '01', '01', NULL, 'test', 'ts', 'ts')
                """,
            )
            conn.execute(
                """
                INSERT INTO fact_precios (
                    barrio_id, anio, periodo, trimestre,
                    precio_m2_venta, precio_mes_alquiler,
                    dataset_id, source, etl_loaded_at
                ) VALUES
                    (1, 2015, '2015', NULL, 2000.0, NULL, 'test', 'unit', 'ts'),
                    (1, 2024, '2024', NULL, 4000.0, NULL, 'test', 'unit', 'ts')
                """,
            )
            conn.execute(
                """
                INSERT INTO fact_renta (
                    barrio_id, anio, renta_euros, renta_promedio,
                    renta_mediana, renta_min, renta_max,
                    num_secciones, barrio_nombre_normalizado,
                    dataset_id, source, etl_loaded_at
                ) VALUES
                    (1, 2015, 20000.0, 20000.0, 20000.0, 15000.0, 25000.0,
                     10, 'test', 'test', 'unit', 'ts'),
                    (1, 2024, 30000.0, 30000.0, 30000.0, 20000.0, 35000.0,
                     10, 'test', 'test', 'unit', 'ts')
                """,
            )
            conn.execute(
                """
                INSERT INTO fact_demografia (
                    barrio_id, anio, poblacion_total,
                    poblacion_hombres, poblacion_mujeres,
                    hogares_totales, edad_media, porc_inmigracion,
                    densidad_hab_km2, dataset_id, source, etl_loaded_at
                ) VALUES
                    (1, 2015, 1000, 480, 520, 400, 40.0, 10.0, 10000.0,
                     'test', 'unit', 'ts'),
                    (1, 2024, 1100, 520, 580, 420, 41.0, 11.0, 10500.0,
                     'test', 'unit', 'ts')
                """,
            )
            conn.commit()

            create_analytical_views(conn)

            cursor = conn.execute(
                """
                SELECT barrio_id, precio_2015, precio_2024, pct_cambio_precio
                FROM v_gentrificacion_tendencias
                """,
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 1
            assert row[1] == 2000.0
            assert row[2] == 4000.0
            # Cambio del 100%
            assert round(row[3], 1) == 100.0
        finally:
            conn.close()


