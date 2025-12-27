"""
Tests unitarios para EducacionExtractor.

Cobertura objetivo: ≥80%
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from src.extraction.educacion_extractor import (
    BARCELONA_LAT_MAX,
    BARCELONA_LAT_MIN,
    BARCELONA_LON_MAX,
    BARCELONA_LON_MIN,
    EducacionExtractor,
)


class DummyResponse:
    """Respuesta simulada para requests."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> Any:
        return self._payload


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Directorio temporal para archivos raw."""
    return tmp_path / "data" / "raw"


def test_classify_tipo_educacion() -> None:
    """Debe clasificar correctamente los tipos de equipamientos."""
    extractor = EducacionExtractor()
    
    assert extractor.classify_tipo_educacion("Educació Infantil") == "infantil"
    assert extractor.classify_tipo_educacion("Escola Primària") == "primaria"
    assert extractor.classify_tipo_educacion("Institut") == "secundaria"
    assert extractor.classify_tipo_educacion("Formació Professional") == "fp"
    assert extractor.classify_tipo_educacion("Universitat") == "universidad"
    assert extractor.classify_tipo_educacion("Desconocido") is None


def test_extract_equipamientos_mock_data(monkeypatch, output_dir: Path) -> None:
    """Debe extraer equipamientos educativos usando OpenDataBCNExtractor."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    # Mock de OpenDataBCNExtractor.download_dataset
    mock_data = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Institut 1", "Universitat 1"],
        "tipus_equipament": ["Educació Primària", "Educació Secundària", "Universitat"],
        "latitud": [41.3851, 41.3900, 41.4000],
        "longitud": [2.1734, 2.1800, 2.1900],
    })
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        return mock_data, {"success": True}
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    assert not df.empty
    assert len(df) == 3
    assert meta["success"] is True
    assert meta["total_records"] == 3


def test_extract_equipamientos_no_data(monkeypatch, output_dir: Path) -> None:
    """Debe manejar correctamente cuando no hay datos."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        return None, {"success": False, "error": "No data"}
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    assert df is None
    assert meta["success"] is False


def test_extract_equipamientos_empty_dataframe(monkeypatch, output_dir: Path) -> None:
    """Debe manejar correctamente cuando el DataFrame está vacío."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        return pd.DataFrame(), {"success": True}
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_validate_coordinates_valid() -> None:
    """Debe validar correctamente coordenadas dentro del rango de Barcelona."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Institut 1"],
        "latitud": [41.3851, 41.3900],
        "longitud": [2.1734, 2.1800],
    })
    
    df_valid = extractor._validate_coordinates(df)
    
    assert len(df_valid) == 2
    assert all(df_valid["latitud"].notna())
    assert all(df_valid["longitud"].notna())


def test_validate_coordinates_out_of_range() -> None:
    """Debe filtrar coordenadas fuera del rango de Barcelona."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Escola 2", "Escola 3"],
        "latitud": [41.3851, 50.0, 41.4000],  # 50.0 está fuera de rango
        "longitud": [2.1734, 2.1800, 1.0],  # 1.0 está fuera de rango
    })
    
    df_valid = extractor._validate_coordinates(df)
    
    # Solo el primer registro debe ser válido
    assert len(df_valid) == 1
    assert df_valid.iloc[0]["nom_equipament"] == "Escola 1"


def test_validate_coordinates_missing() -> None:
    """Debe filtrar registros con coordenadas faltantes."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Escola 2", "Escola 3"],
        "latitud": [41.3851, None, 41.3900],
        "longitud": [2.1734, 2.1800, None],
    })
    
    df_valid = extractor._validate_coordinates(df)
    
    # Solo el primer registro debe ser válido
    assert len(df_valid) == 1
    assert df_valid.iloc[0]["nom_equipament"] == "Escola 1"


def test_validate_coordinates_different_column_names() -> None:
    """Debe detectar coordenadas con diferentes nombres de columnas."""
    extractor = EducacionExtractor()
    
    # Probar con diferentes nombres comunes
    test_cases = [
        ("latitude", "longitude"),
        ("coord_y", "coord_x"),
        ("lat", "lon"),
        ("y", "x"),
    ]
    
    for lat_col, lon_col in test_cases:
        df = pd.DataFrame({
            "nom_equipament": ["Escola 1"],
            lat_col: [41.3851],
            lon_col: [2.1734],
        })
        
        df_valid = extractor._validate_coordinates(df)
        assert len(df_valid) == 1, f"Falló con columnas {lat_col}, {lon_col}"


def test_validate_coordinates_no_coord_columns() -> None:
    """Debe retornar DataFrame vacío si no hay columnas de coordenadas."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1"],
        "tipus_equipament": ["Primària"],
    })
    
    df_valid = extractor._validate_coordinates(df)
    
    assert len(df_valid) == 0


def test_classify_tipo_educacion_all_types() -> None:
    """Debe clasificar correctamente todos los tipos educativos."""
    extractor = EducacionExtractor()
    
    test_cases = [
        ("Educació Infantil", "infantil"),
        ("Escola Bressol", "infantil"),
        ("Guarderia", "infantil"),
        ("Educació Primària", "primaria"),
        ("Escola Primària", "primaria"),
        ("Educació Secundària", "secundaria"),
        ("ESO", "secundaria"),
        ("Institut", "secundaria"),
        ("Formació Professional", "fp"),
        ("FP", "fp"),
        ("Cicles Formatius", "fp"),
        ("Universitat", "universidad"),
        ("Universidad", "universidad"),
        ("Campus", "universidad"),
        ("Autoescola", "autoescuela"),
        ("Autoescuela", "autoescuela"),
        ("Acadèmia", "academia"),
        ("Academia", "academia"),
        ("Català", "academia"),
    ]
    
    for tipo_input, expected in test_cases:
        result = extractor.classify_tipo_educacion(tipo_input)
        assert result == expected, f"Falló para '{tipo_input}': esperado {expected}, obtenido {result}"


def test_classify_tipo_educacion_case_insensitive() -> None:
    """Debe ser case-insensitive en la clasificación."""
    extractor = EducacionExtractor()
    
    assert extractor.classify_tipo_educacion("EDUCACIÓ INFANTIL") == "infantil"
    assert extractor.classify_tipo_educacion("educació infantil") == "infantil"
    assert extractor.classify_tipo_educacion("Educació Infantil") == "infantil"


def test_classify_tipo_educacion_unknown() -> None:
    """Debe retornar None para tipos desconocidos."""
    extractor = EducacionExtractor()
    
    assert extractor.classify_tipo_educacion("Tipo Desconocido") is None
    assert extractor.classify_tipo_educacion("") is None


def test_classify_tipo_educacion_nan() -> None:
    """Debe manejar valores NaN correctamente."""
    extractor = EducacionExtractor()
    
    import numpy as np
    assert extractor.classify_tipo_educacion(pd.NA) is None
    assert extractor.classify_tipo_educacion(np.nan) is None
    assert extractor.classify_tipo_educacion(None) is None


def test_get_coverage_stats() -> None:
    """Debe calcular estadísticas de cobertura correctamente."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Institut 1", "Universitat 1"],
        "tipus_equipament": ["Educació Primària", "Educació Secundària", "Universitat"],
        "barrio_id": [1, 1, 2],
    })
    
    stats = extractor.get_coverage_stats(df)
    
    assert stats["total_equipamientos"] == 3
    assert stats["barrios_con_equipamientos"] == 2
    assert stats["barrios_sin_equipamientos"] == 71  # 73 - 2
    assert "primaria" in stats["distribucion_por_tipo"]
    assert "secundaria" in stats["distribucion_por_tipo"]
    assert "universidad" in stats["distribucion_por_tipo"]


def test_get_coverage_stats_no_barrio_id() -> None:
    """Debe manejar DataFrames sin barrio_id."""
    extractor = EducacionExtractor()
    
    df = pd.DataFrame({
        "nom_equipament": ["Escola 1"],
        "tipus_equipament": ["Primària"],
    })
    
    stats = extractor.get_coverage_stats(df)
    
    assert stats["total_equipamientos"] == 1
    assert stats["barrios_con_equipamientos"] == 0


def test_extract_equipamientos_with_coordinate_validation(monkeypatch, output_dir: Path) -> None:
    """Debe validar coordenadas durante la extracción."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    # Mock data con coordenadas válidas e inválidas
    mock_data = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Escola 2", "Escola 3"],
        "tipus_equipament": ["Primària", "Secundària", "Primària"],
        "latitud": [41.3851, 50.0, 41.3900],  # 50.0 fuera de rango
        "longitud": [2.1734, 2.1800, None],  # None inválido
    })
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        return mock_data, {"success": True}
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    # Solo debe retornar registros con coordenadas válidas
    assert df is not None
    assert len(df) == 1  # Solo Escola 1 tiene coordenadas válidas
    assert meta["success"] is True
    assert meta["records_with_valid_coords"] == 1
    assert meta["records_without_coords"] == 2


def test_extract_equipamientos_500_plus_equipamientos(monkeypatch, output_dir: Path) -> None:
    """Debe manejar correctamente cuando hay ≥500 equipamientos."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    # Crear mock data con 500+ equipamientos
    mock_data = pd.DataFrame({
        "nom_equipament": [f"Escola {i}" for i in range(600)],
        "tipus_equipament": ["Primària"] * 600,
        "latitud": [41.3851] * 600,
        "longitud": [2.1734] * 600,
    })
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        return mock_data, {"success": True}
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    assert df is not None
    assert len(df) == 600
    assert meta["records_with_valid_coords"] == 600
    assert meta["total_records"] == 600


def test_extract_equipamientos_exception_handling(monkeypatch, output_dir: Path) -> None:
    """Debe manejar excepciones correctamente."""
    extractor = EducacionExtractor(output_dir=output_dir)
    
    def mock_download(self, dataset_id, **kwargs):  # noqa: ARG001
        raise Exception("Error de red")
    
    monkeypatch.setattr(
        "src.extraction.educacion_extractor.OpenDataBCNExtractor.download_dataset",
        mock_download
    )
    
    df, meta = extractor.extract_equipamientos()
    
    assert df is None
    assert meta["success"] is False
    assert "error" in meta

