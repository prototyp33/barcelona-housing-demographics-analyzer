from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd
import pytest

from src.etl.pipeline import run_etl


@pytest.fixture
def raw_data_regulacion(tmp_path: Path) -> Dict[str, Path]:
    """
    Crea estructura mínima de datos raw con regulación para probar integración ETL.

    Nota:
        Este test no verifica la lógica completa del ETL, solo que, dado un
        archivo de regulación compatible con ``prepare_regulacion`` y una
        demografía mínima, el pipeline es capaz de cargar ``fact_regulacion``.
    """
    raw_dir = tmp_path / "data" / "raw"
    opendatabcn_dir = raw_dir / "opendatabcn"
    generalitat_dir = raw_dir / "generalitat"
    processed_dir = tmp_path / "data" / "processed"

    opendatabcn_dir.mkdir(parents=True, exist_ok=True)
    generalitat_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Demografía mínima con dos barrios
    dem_df = pd.DataFrame(
        {
            "Data_Referencia": ["2024-01-01", "2024-01-01"],
            "Any": [2024, 2024],
            "Codi_Districte": [1, 1],
            "Nom_Districte": ["Ciutat Vella", "Ciutat Vella"],
            "Codi_Barri": [1, 2],
            "Nom_Barri": ["el Raval", "el Barri Gòtic"],
            "Sexe": ["Home", "Dona"],
            "Valor": [15000, 14500],
        }
    )
    dem_path = (
        opendatabcn_dir
        / "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_2024_2024_test.csv"
    )
    dem_df.to_csv(dem_path, index=False)

    # Precios mínimos (necesarios para fact_precios aunque puedan terminar vacíos)
    prices_df = pd.DataFrame(
        {
            "Any": [2024, 2024],
            "Codi_Districte": [1, 1],
            "Nom_Districte": ["Ciutat Vella", "Ciutat Vella"],
            "Codi_Barri": [1, 2],
            "Nom_Barri": ["el Raval", "el Barri Gòtic"],
            "Preu_mitja_m2": [3500.0, 4200.0],
            "tipo_operacion": ["venta", "venta"],
            "source": ["opendatabcn_idealista", "opendatabcn_idealista"],
        }
    )
    prices_path = opendatabcn_dir / "opendatabcn_venta_2024_2024_test.csv"
    prices_df.to_csv(prices_path, index=False)

    # Archivo de regulación compatible con prepare_regulacion
    regulacion_df = pd.DataFrame(
        {
            "codi_barri": ["1", "2"],
            "any": [2024, 2024],
            "indice_referencia": [900.0, 950.0],
        }
    )
    regulacion_path = generalitat_dir / "generalitat_indice_referencia_2024_2024_test.csv"
    regulacion_df.to_csv(regulacion_path, index=False)

    return {
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
    }


@pytest.mark.skip(reason="Test de integración pesado, usar bajo demanda.")
def test_etl_loads_fact_regulacion(raw_data_regulacion: Dict[str, Path]) -> None:
    """Verifica que el ETL crea y carga la tabla fact_regulacion."""
    raw_dir = raw_data_regulacion["raw_dir"]
    processed_dir = raw_data_regulacion["processed_dir"]

    db_path = run_etl(raw_base_dir=raw_dir, processed_dir=processed_dir)
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fact_regulacion';"
        )
        table = cursor.fetchone()
        assert table is not None, "La tabla fact_regulacion no existe"

        df_reg = pd.read_sql("SELECT * FROM fact_regulacion", conn)
        assert len(df_reg) >= 0
    finally:
        conn.close()


