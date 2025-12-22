from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.processing.prepare_regulacion import prepare_regulacion


@pytest.fixture
def barrios_df() -> pd.DataFrame:
    """Dimensión de barrios mínima con codi_barri, barrio_id y barrio_nombre_normalizado."""
    return pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
            "barrio_nombre": ["Barrio 1", "Barrio 2"],
            "barrio_nombre_normalizado": ["barrio1", "barrio2"],
        }
    )


def test_prepare_regulacion_basic_flow(tmp_path: Path, barrios_df: pd.DataFrame) -> None:
    """Debe mapear datos del Portal de Dades a fact_regulacion básica."""
    # Crear estructura de directorios como espera el código
    raw_dir = tmp_path / "regulacion"
    portaldades_dir = raw_dir / "portaldades"
    portaldades_dir.mkdir(parents=True, exist_ok=True)

    # Crear CSV con formato Portal de Dades (b37xv8wcjh)
    df_raw = pd.DataFrame(
        {
            "Dim-00:TEMPS": ["2024Q1", "2024Q2"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 2"],
            "Dim-01:TERRITORI (order)": [1, 2],
            "Dim-01:TERRITORI (type)": ["barri", "barri"],
            "VALUE": [900.0, 950.0],
        }
    )
    csv_path = portaldades_dir / "portaldades_precio_medio_alquiler_barrio_b37xv8wcjh.csv"
    df_raw.to_csv(csv_path, index=False)

    result = prepare_regulacion(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert not result.empty
    assert set(result["barrio_id"].unique()) == {1, 2}
    assert set(result["anio"].unique()) == {2024}
    assert "indice_referencia_alquiler" in result.columns
    assert "zona_tensionada" in result.columns
    assert "nivel_tension" in result.columns


def test_prepare_regulacion_empty_raw(tmp_path: Path, barrios_df: pd.DataFrame) -> None:
    """Debe devolver DataFrame vacío pero con columnas correctas si no hay archivos."""
    raw_dir = tmp_path / "regulacion"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = prepare_regulacion(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert result.empty
    expected_cols = {
        "barrio_id",
        "anio",
        "zona_tensionada",
        "nivel_tension",
        "indice_referencia_alquiler",
        "num_licencias_vut",
        "derecho_tanteo",
    }
    assert expected_cols.issubset(result.columns)


