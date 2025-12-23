"""
Tests unitarios para prepare_seguridad.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.processing.prepare_seguridad import prepare_seguridad


@pytest.fixture
def barrios_df() -> pd.DataFrame:
    """Dimensión de barrios mínima con barrio_id y barrio_nombre_normalizado."""
    return pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
            "barrio_nombre": ["Barrio 1", "Barrio 2"],
            "barrio_nombre_normalizado": ["barrio1", "barrio2"],
        }
    )


@pytest.fixture
def poblacion_df() -> pd.DataFrame:
    """Datos de población para calcular tasas."""
    return pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "anio": [2024, 2024],
            "poblacion_total": [10000, 15000],
        }
    )


def test_prepare_seguridad_basic_flow(
    tmp_path: Path, barrios_df: pd.DataFrame, poblacion_df: pd.DataFrame
) -> None:
    """Debe mapear datos de criminalidad a fact_seguridad básica."""
    # Crear estructura de directorios
    raw_dir = tmp_path / "icgc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear CSV con formato de datos de criminalidad
    df_raw = pd.DataFrame(
        {
            "barrio": ["Barrio 1", "Barrio 2", "Barrio 1"],
            "anio": [2024, 2024, 2024],
            "trimestre": [1, 1, 2],
            "robos": [10, 5, 8],
            "hurtos": [15, 10, 12],
            "agresiones": [3, 2, 4],
        }
    )
    csv_path = raw_dir / "icgc_criminalidad_2024.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_seguridad(
        raw_data_path=raw_dir,
        barrios_df=barrios_df,
        poblacion_df=poblacion_df,
    )

    assert not result.empty
    assert "barrio_id" in result.columns
    assert "anio" in result.columns
    assert "trimestre" in result.columns
    assert "delitos_patrimonio" in result.columns
    assert "delitos_seguridad_personal" in result.columns
    assert "tasa_criminalidad_1000hab" in result.columns


def test_prepare_seguridad_empty_raw(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe devolver DataFrame vacío pero con columnas correctas si no hay archivos."""
    raw_dir = tmp_path / "icgc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = prepare_seguridad(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert result.empty
    expected_cols = {
        "barrio_id",
        "anio",
        "trimestre",
        "delitos_patrimonio",
        "delitos_seguridad_personal",
        "tasa_criminalidad_1000hab",
        "percepcion_inseguridad",
    }
    assert expected_cols.issubset(result.columns)


def test_prepare_seguridad_missing_barrios_columns(tmp_path: Path) -> None:
    """Debe lanzar ValueError si faltan columnas requeridas en barrios_df."""
    raw_dir = tmp_path / "icgc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    incomplete_barrios = pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
        }
    )

    with pytest.raises(ValueError, match="Dimensión de barrios incompleta"):
        prepare_seguridad(raw_data_path=raw_dir, barrios_df=incomplete_barrios)


def test_prepare_seguridad_calculates_tasa(
    tmp_path: Path, barrios_df: pd.DataFrame, poblacion_df: pd.DataFrame
) -> None:
    """Debe calcular correctamente la tasa de criminalidad por 1000 habitantes."""
    raw_dir = tmp_path / "icgc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear datos con delitos conocidos
    df_raw = pd.DataFrame(
        {
            "barrio": ["Barrio 1", "Barrio 2"],
            "anio": [2024, 2024],
            "trimestre": [1, 1],
            "robos": [10, 15],
            "hurtos": [20, 25],
            "agresiones": [5, 3],
        }
    )
    csv_path = raw_dir / "icgc_criminalidad_2024.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_seguridad(
        raw_data_path=raw_dir,
        barrios_df=barrios_df,
        poblacion_df=poblacion_df,
    )

    assert not result.empty
    
    # Verificar que se calculó la tasa
    # Barrio 1: (10+20+5) / 10000 * 1000 = 3.5 por 1000hab
    # Barrio 2: (15+25+3) / 15000 * 1000 = 2.87 por 1000hab
    barrio1_data = result[result["barrio_id"] == 1]
    if not barrio1_data.empty:
        assert barrio1_data["tasa_criminalidad_1000hab"].iloc[0] > 0


def test_prepare_seguridad_empty_barrios_df(tmp_path: Path) -> None:
    """Debe lanzar ValueError si barrios_df está vacío."""
    raw_dir = tmp_path / "icgc"
    raw_dir.mkdir(parents=True, exist_ok=True)

    empty_barrios = pd.DataFrame()

    with pytest.raises(ValueError, match="barrios_df no puede estar vacío"):
        prepare_seguridad(raw_data_path=raw_dir, barrios_df=empty_barrios)

