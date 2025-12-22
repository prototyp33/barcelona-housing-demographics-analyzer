"""
Tests unitarios para prepare_presion_turistica.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.processing.prepare_presion_turistica import prepare_presion_turistica


@pytest.fixture
def barrios_df() -> pd.DataFrame:
    """Dimensión de barrios mínima con barrio_id y barrio_nombre_normalizado."""
    return pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
            "barrio_nombre": ["Barrio 1", "Barrio 2"],
            "barrio_nombre_normalizado": ["barrio1", "barrio2"],
            "geometry_json": [None, None],  # Sin geometrías para tests básicos
        }
    )


def test_prepare_presion_turistica_basic_flow(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe mapear datos de Inside Airbnb a fact_presion_turistica básica."""
    # Crear estructura de directorios
    raw_dir = tmp_path / "airbnb"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear CSV de listings con formato Inside Airbnb
    listings_df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "neighbourhood": ["Barrio 1", "Barrio 2", "Barrio 1"],
            "latitude": [41.3851, 41.3874, 41.3851],
            "longitude": [2.1734, 2.1750, 2.1734],
            "room_type": ["Entire home/apt", "Private room", "Entire home/apt"],
            "price": ["100", "50", "120"],
            "last_review": ["2024-01-15", "2024-02-20", "2024-03-10"],
        }
    )
    listings_path = raw_dir / "insideairbnb_listings_20240101.csv"
    listings_df.to_csv(listings_path, index=False)

    result = prepare_presion_turistica(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert not result.empty
    assert "barrio_id" in result.columns
    assert "anio" in result.columns
    assert "mes" in result.columns
    assert "num_listings_airbnb" in result.columns
    assert "pct_entire_home" in result.columns
    assert "precio_noche_promedio" in result.columns
    assert "tasa_ocupacion" in result.columns
    assert "num_reviews_mes" in result.columns


def test_prepare_presion_turistica_empty_raw(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe devolver DataFrame vacío pero con columnas correctas si no hay archivos."""
    raw_dir = tmp_path / "airbnb"
    raw_dir.mkdir(parents=True, exist_ok=True)

    result = prepare_presion_turistica(raw_data_path=raw_dir, barrios_df=barrios_df)

    assert result.empty
    expected_cols = {
        "barrio_id",
        "anio",
        "mes",
        "num_listings_airbnb",
        "pct_entire_home",
        "precio_noche_promedio",
        "tasa_ocupacion",
        "num_reviews_mes",
    }
    assert expected_cols.issubset(result.columns)


def test_prepare_presion_turistica_missing_barrios_columns(
    tmp_path: Path,
) -> None:
    """Debe lanzar ValueError si faltan columnas requeridas en barrios_df."""
    raw_dir = tmp_path / "airbnb"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # DataFrame sin barrio_nombre_normalizado
    incomplete_barrios = pd.DataFrame(
        {
            "barrio_id": [1, 2],
            "codi_barri": ["01", "02"],
        }
    )

    with pytest.raises(ValueError, match="Dimensión de barrios incompleta"):
        prepare_presion_turistica(raw_data_path=raw_dir, barrios_df=incomplete_barrios)


def test_prepare_presion_turistica_calculates_metrics(
    tmp_path: Path, barrios_df: pd.DataFrame
) -> None:
    """Debe calcular correctamente las métricas agregadas."""
    raw_dir = tmp_path / "airbnb"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Crear listings con datos suficientes para calcular métricas
    listings_df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "neighbourhood": ["Barrio 1", "Barrio 1", "Barrio 2", "Barrio 2"],
            "latitude": [41.3851, 41.3851, 41.3874, 41.3874],
            "longitude": [2.1734, 2.1734, 2.1750, 2.1750],
            "room_type": [
                "Entire home/apt",
                "Entire home/apt",
                "Private room",
                "Entire home/apt",
            ],
            "price": ["100", "120", "50", "80"],
            "last_review": ["2024-01-15", "2024-01-20", "2024-01-10", "2024-01-25"],
        }
    )
    listings_path = raw_dir / "insideairbnb_listings_20240101.csv"
    listings_df.to_csv(listings_path, index=False)

    result = prepare_presion_turistica(raw_data_path=raw_dir, barrios_df=barrios_df)

    # Verificar que se calcularon métricas
    assert not result.empty
    
    # Verificar que pct_entire_home se calculó correctamente
    # Barrio 1: 2 listings, ambos Entire home/apt = 100%
    # Barrio 2: 2 listings, 1 Entire home/apt = 50%
    barrio1_data = result[result["barrio_id"] == 1]
    if not barrio1_data.empty:
        assert barrio1_data["pct_entire_home"].iloc[0] == 100.0
    
    barrio2_data = result[result["barrio_id"] == 2]
    if not barrio2_data.empty:
        assert barrio2_data["pct_entire_home"].iloc[0] == 50.0


def test_prepare_presion_turistica_empty_barrios_df(tmp_path: Path) -> None:
    """Debe lanzar ValueError si barrios_df está vacío."""
    raw_dir = tmp_path / "airbnb"
    raw_dir.mkdir(parents=True, exist_ok=True)

    empty_barrios = pd.DataFrame()

    with pytest.raises(ValueError, match="barrios_df no puede estar vacío"):
        prepare_presion_turistica(raw_data_path=raw_dir, barrios_df=empty_barrios)

