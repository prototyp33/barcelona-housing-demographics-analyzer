import sqlite3
import pytest
from pathlib import Path
from src.database_setup import create_connection, create_database_schema, VALID_TABLES

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_integration.db"
    conn = create_connection(db_path)
    create_database_schema(conn)
    yield conn
    conn.close()

def test_new_tables_exist(temp_db):
    cursor = temp_db.cursor()
    new_tables = [
        "fact_renta_avanzada",
        "fact_catastro_avanzado",
        "fact_hogares_avanzado",
        "fact_turismo_intensidad"
    ]
    
    for table in new_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert cursor.fetchone() is not None
        assert table in VALID_TABLES

def test_table_structures(temp_db):
    cursor = temp_db.cursor()
    
    # Verify fact_renta_avanzada
    cursor.execute("PRAGMA table_info(fact_renta_avanzada)")
    columns = {info[1] for info in cursor.fetchall()}
    expected = {"id", "barrio_id", "anio", "renta_bruta_llar", "indice_gini", "ratio_p80_p20", "dataset_id", "source", "etl_loaded_at"}
    assert expected.issubset(columns)

    # Verify fact_catastro_avanzado
    cursor.execute("PRAGMA table_info(fact_catastro_avanzado)")
    columns = {info[1] for info in cursor.fetchall()}
    expected = {"num_propietarios_fisica", "num_propietarios_juridica", "pct_propietarios_extranjeros", "superficie_media_m2", "num_plantas_avg", "antiguedad_media_bloque"}
    assert expected.issubset(columns)

    # Verify fact_hogares_avanzado
    cursor.execute("PRAGMA table_info(fact_hogares_avanzado)")
    columns = {info[1] for info in cursor.fetchall()}
    expected = {"promedio_personas_por_hogar", "num_hogares_con_menores", "pct_hogares_nacionalidad_extranjera", "pct_presencia_mujeres"}
    assert expected.issubset(columns)

    # Verify fact_turismo_intensidad
    cursor.execute("PRAGMA table_info(fact_turismo_intensidad)")
    columns = {info[1] for info in cursor.fetchall()}
    expected = {"indice_intensidad_turistica", "num_establecimientos_turisticos"}
    assert expected.issubset(columns)
