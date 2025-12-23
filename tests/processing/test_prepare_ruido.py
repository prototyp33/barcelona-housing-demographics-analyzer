"""
Tests unitarios para prepare_ruido.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.processing.prepare_ruido import prepare_ruido


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
    """Datos de población para calcular porcentaje expuesto."""
    return pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "anio": [2022, 2022],
            "poblacion_total": [10000, 15000],
        }
    )


def test_prepare_ruido_basic_flow(
    tmp_path: Path, barrios_df: pd.DataFrame, poblacion_df: pd.DataFrame
) -> None:
    """Debe mapear datos de ruido a fact_ruido básica."""
    # Crear estructura de directorios
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear CSV con formato de datos de ruido
    df_raw = pd.DataFrame(
        {
            "barrio": ["Barrio 1", "Barrio 2"],
            "anio": [2022, 2022],
            "nivel_lden": [65.5, 58.2],
            "nivel_ld": [68.0, 60.0],
            "nivel_ln": [55.0, 50.0],
        }
    )
    csv_path = raw_dir / "ruido_2022.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_ruido(
        raw_data_path=raw_dir,
        barrios_df=barrios_df,
        poblacion_df=poblacion_df,
    )

    assert not result.empty
    assert "barrio_id" in result.columns
    assert "anio" in result.columns
    assert "nivel_lden_medio" in result.columns
    assert "nivel_ld_dia" in result.columns
    assert "nivel_ln_noche" in result.columns


def test_prepare_ruido_empty_raw(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe devolver DataFrame vacío pero con columnas correctas si no hay archivos."""
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = prepare_ruido(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert result.empty
    expected_cols = {
        "barrio_id",
        "anio",
        "nivel_lden_medio",
        "nivel_ld_dia",
        "nivel_ln_noche",
        "pct_poblacion_expuesta_65db",
    }
    assert expected_cols.issubset(result.columns)


def test_prepare_ruido_missing_barrios_columns(tmp_path: Path) -> None:
    """Debe lanzar ValueError si faltan columnas requeridas en barrios_df."""
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    incomplete_barrios = pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
        }
    )

    with pytest.raises(ValueError, match="Dimensión de barrios incompleta"):
        prepare_ruido(raw_data_path=raw_dir, barrios_df=incomplete_barrios)


def test_prepare_ruido_calculates_exposure(
    tmp_path: Path, barrios_df: pd.DataFrame, poblacion_df: pd.DataFrame
) -> None:
    """Debe calcular correctamente el porcentaje de población expuesta a >65 dB(A)."""
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear datos con niveles conocidos
    df_raw = pd.DataFrame(
        {
            "barrio": ["Barrio 1", "Barrio 2"],
            "anio": [2022, 2022],
            "nivel_lden": [70.0, 60.0],  # Barrio 1 > 65, Barrio 2 < 65
            "nivel_ld": [72.0, 62.0],
            "nivel_ln": [60.0, 55.0],
        }
    )
    csv_path = raw_dir / "ruido_2022.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_ruido(
        raw_data_path=raw_dir,
        barrios_df=barrios_df,
        poblacion_df=poblacion_df,
    )

    assert not result.empty
    
    # Verificar que se calculó la exposición
    # Barrio 1: nivel_lden > 65, debería tener 100% expuesto
    barrio1_data = result[result["barrio_id"] == 1]
    if not barrio1_data.empty:
        assert barrio1_data["pct_poblacion_expuesta_65db"].iloc[0] == 100.0
    
    # Barrio 2: nivel_lden < 65, debería tener 0% expuesto
    barrio2_data = result[result["barrio_id"] == 2]
    if not barrio2_data.empty:
        assert barrio2_data["pct_poblacion_expuesta_65db"].iloc[0] == 0.0


def test_prepare_ruido_empty_barrios_df(tmp_path: Path) -> None:
    """Debe lanzar ValueError si barrios_df está vacío."""
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    empty_barrios = pd.DataFrame()

    with pytest.raises(ValueError, match="barrios_df no puede estar vacío"):
        prepare_ruido(raw_data_path=raw_dir, barrios_df=empty_barrios)


def test_prepare_ruido_aggregates_by_barrio_year(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe agregar múltiples registros por barrio y año."""
    raw_dir = tmp_path / "ruido"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear datos con múltiples registros para el mismo barrio
    df_raw = pd.DataFrame(
        {
            "barrio": ["Barrio 1", "Barrio 1", "Barrio 2"],
            "anio": [2022, 2022, 2022],
            "nivel_lden": [65.0, 66.0, 58.0],
            "nivel_ld": [68.0, 69.0, 60.0],
            "nivel_ln": [55.0, 56.0, 50.0],
        }
    )
    csv_path = raw_dir / "ruido_2022.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_ruido(
        raw_data_path=raw_dir,
        barrios_df=barrios_df,
    )

    assert not result.empty
    
    # Debe haber solo 2 registros (uno por barrio)
    assert len(result) == 2
    
    # Barrio 1 debería tener el promedio de 65.0 y 66.0 = 65.5
    barrio1_data = result[result["barrio_id"] == 1]
    if not barrio1_data.empty:
        assert abs(barrio1_data["nivel_lden_medio"].iloc[0] - 65.5) < 0.1

