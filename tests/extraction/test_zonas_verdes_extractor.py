"""
Tests unitarios para ZonasVerdesExtractor.

Cobertura objetivo: ≥80%
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.extraction.zonas_verdes_extractor import (
    ZonasVerdesExtractor,
    BARCELONA_LAT_MIN,
    BARCELONA_LAT_MAX,
    BARCELONA_LON_MIN,
    BARCELONA_LON_MAX,
)


class MockResponse:
    """Respuesta simulada para requests."""

    def __init__(self, status_code: int, json_data: Any, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> Any:
        return self._json_data


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Directorio temporal para archivos raw."""
    return tmp_path / "data" / "raw"


@pytest.fixture
def sample_parques_data() -> pd.DataFrame:
    """Datos de ejemplo de parques y jardines."""
    return pd.DataFrame({
        "nom": ["Parc de la Ciutadella", "Jardins de Montjuïc"],
        "superficie": [31.0, 15.5],  # hectáreas (convertir a m²)
        "latitud": [41.388, 41.368],
        "longitud": [2.187, 2.164],
    })


@pytest.fixture
def sample_arbolado_data() -> pd.DataFrame:
    """Datos de ejemplo de arbolado."""
    return pd.DataFrame({
        "nom_cientific": ["Platanus x hispanica", "Quercus ilex"],
        "latitud": [41.388, 41.368],
        "longitud": [2.187, 2.164],
    })


def test_extract_parques_jardines_success(output_dir: Path, sample_parques_data: pd.DataFrame) -> None:
    """Debe extraer datos de parques y jardines correctamente."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    with patch.object(extractor.opendata_extractor, "download_dataset", return_value=(sample_parques_data, {})):
        df, meta = extractor.extract_parques_jardines()

    assert df is not None
    assert len(df) == 2
    assert meta["success"] is True
    assert meta["total_parques"] == 2
    assert meta["parques_with_valid_coords"] == 2


def test_extract_parques_jardines_no_datasets(output_dir: Path) -> None:
    """Debe manejar cuando no se encuentran datasets."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    with patch.object(extractor.opendata_extractor, "download_dataset", return_value=(None, {})):
        df, meta = extractor.extract_parques_jardines()

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_extract_arbolado_success(output_dir: Path, sample_arbolado_data: pd.DataFrame) -> None:
    """Debe extraer datos de arbolado correctamente."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    with patch.object(extractor.opendata_extractor, "download_dataset", return_value=(sample_arbolado_data, {})):
        df, meta = extractor.extract_arbolado()

    assert df is not None
    assert len(df) == 2
    assert meta["success"] is True
    assert meta["total_arboles"] == 2
    assert meta["arboles_with_valid_coords"] == 2


def test_extract_arbolado_no_datasets(output_dir: Path) -> None:
    """Debe manejar cuando no se encuentran datasets de arbolado."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    with patch.object(extractor.opendata_extractor, "download_dataset", return_value=(None, {})):
        df, meta = extractor.extract_arbolado()

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_extract_all_combines_sources(output_dir: Path, sample_parques_data: pd.DataFrame, sample_arbolado_data: pd.DataFrame) -> None:
    """Debe combinar datos de parques y arbolado."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    def mock_download(dataset_id: str, **kwargs):
        if "parc" in dataset_id.lower() or "jardi" in dataset_id.lower():
            return sample_parques_data, {}
        elif "arbre" in dataset_id.lower() or "arbol" in dataset_id.lower():
            return sample_arbolado_data, {}
        return None, {}

    with patch.object(extractor.opendata_extractor, "download_dataset", side_effect=mock_download):
        df, meta = extractor.extract_all()

    assert df is not None
    assert meta["has_parques"] is True
    assert meta["has_arbolado"] is True
    assert "tipo_zona_verde" in df.columns


def test_validate_coordinates_valid(output_dir: Path) -> None:
    """Debe validar coordenadas dentro del rango de Barcelona."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "latitud": [41.388, 41.368, 41.400],
        "longitud": [2.187, 2.164, 2.200],
    })

    df_validated = extractor._validate_coordinates(df)

    assert len(df_validated) == 3
    assert all(
        BARCELONA_LAT_MIN <= lat <= BARCELONA_LAT_MAX
        for lat in df_validated["latitud"]
    )
    assert all(
        BARCELONA_LON_MIN <= lon <= BARCELONA_LON_MAX
        for lon in df_validated["longitud"]
    )


def test_validate_coordinates_out_of_range(output_dir: Path) -> None:
    """Debe filtrar coordenadas fuera del rango de Barcelona."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "latitud": [41.388, 50.0, 41.368],  # 50.0 está fuera de rango
        "longitud": [2.187, 2.164, 10.0],  # 10.0 está fuera de rango
    })

    df_validated = extractor._validate_coordinates(df)

    assert len(df_validated) == 1  # Solo el primero es válido
    assert df_validated.iloc[0]["latitud"] == 41.388


def test_validate_coordinates_missing(output_dir: Path) -> None:
    """Debe manejar coordenadas faltantes."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "latitud": [41.388, None, 41.368],
        "longitud": [2.187, 2.164, None],
    })

    df_validated = extractor._validate_coordinates(df)

    assert len(df_validated) == 1  # Solo el primero tiene ambas coordenadas


def test_validate_coordinates_no_coord_columns(output_dir: Path) -> None:
    """Debe manejar cuando no hay columnas de coordenadas."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "nombre": ["Parque 1", "Parque 2"],
        "superficie": [1000, 2000],
    })

    df_validated = extractor._validate_coordinates(df)

    # Debe retornar el DataFrame original sin filtrar
    assert len(df_validated) == len(df)


def test_normalize_parques_columns(output_dir: Path) -> None:
    """Debe normalizar columnas de parques correctamente."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "nom": ["Parque 1"],
        "area": [1000],
        "lat": [41.388],
        "lon": [2.187],
        "barri": [1],
    })

    df_normalized = extractor._normalize_parques_columns(df)

    assert "nombre" in df_normalized.columns or "nom" in df_normalized.columns
    assert "superficie_m2" in df_normalized.columns or "area" in df_normalized.columns
    assert "latitud" in df_normalized.columns or "lat" in df_normalized.columns
    assert "longitud" in df_normalized.columns or "lon" in df_normalized.columns


def test_normalize_arbolado_columns(output_dir: Path) -> None:
    """Debe normalizar columnas de arbolado correctamente."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "nom_cientific": ["Platanus x hispanica"],
        "lat": [41.388],
        "lon": [2.187],
        "barri": [1],
    })

    df_normalized = extractor._normalize_arbolado_columns(df)

    assert "nombre_cientifico" in df_normalized.columns or "nom_cientific" in df_normalized.columns
    assert "latitud" in df_normalized.columns or "lat" in df_normalized.columns
    assert "longitud" in df_normalized.columns or "lon" in df_normalized.columns


def test_find_superficie_column(output_dir: Path) -> None:
    """Debe encontrar columna de superficie correctamente."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "nombre": ["Parque 1"],
        "superficie_m2": [1000],
    })

    superficie_col = extractor._find_superficie_column(df)

    assert superficie_col == "superficie_m2"


def test_find_superficie_column_not_found(output_dir: Path) -> None:
    """Debe retornar None cuando no hay columna de superficie."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    df = pd.DataFrame({
        "nombre": ["Parque 1"],
        "otra_columna": [1000],
    })

    superficie_col = extractor._find_superficie_column(df)

    assert superficie_col is None


def test_extract_all_only_parques(output_dir: Path, sample_parques_data: pd.DataFrame) -> None:
    """Debe retornar solo parques si no hay arbolado."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    def mock_download(dataset_id: str, **kwargs):
        if "parc" in dataset_id.lower() or "jardi" in dataset_id.lower():
            return sample_parques_data, {}
        return None, {}

    with patch.object(extractor.opendata_extractor, "download_dataset", side_effect=mock_download):
        df, meta = extractor.extract_all()

    assert df is not None
    assert meta["has_parques"] is True
    assert meta["has_arbolado"] is False


def test_extract_all_only_arbolado(output_dir: Path, sample_arbolado_data: pd.DataFrame) -> None:
    """Debe retornar solo arbolado si no hay parques."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    def mock_download(dataset_id: str, **kwargs):
        if "arbre" in dataset_id.lower() or "arbol" in dataset_id.lower():
            return sample_arbolado_data, {}
        return None, {}

    with patch.object(extractor.opendata_extractor, "download_dataset", side_effect=mock_download):
        df, meta = extractor.extract_all()

    assert df is not None
    assert meta["has_parques"] is False
    assert meta["has_arbolado"] is True


def test_extract_all_no_data(output_dir: Path) -> None:
    """Debe manejar cuando no hay datos disponibles."""
    extractor = ZonasVerdesExtractor(output_dir=output_dir)

    with patch.object(extractor.opendata_extractor, "download_dataset", return_value=(None, {})):
        df, meta = extractor.extract_all()

    assert df is None
    assert meta["success"] is False
    assert meta["has_parques"] is False
    assert meta["has_arbolado"] is False

