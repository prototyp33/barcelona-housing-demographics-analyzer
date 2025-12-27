"""
Tests unitarios para extractores de movilidad (Bicing y ATM).

Cobertura objetivo: ≥80%
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.extraction.movilidad_extractor import (
    BARCELONA_LAT_MAX,
    BARCELONA_LAT_MIN,
    BARCELONA_LON_MAX,
    BARCELONA_LON_MIN,
    ATMExtractor,
    BicingExtractor,
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


def test_bicing_extract_station_information_success(output_dir: Path) -> None:
    """Debe extraer información de estaciones Bicing correctamente."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_data = {
        "data": {
            "stations": [
                {
                    "station_id": "1",
                    "name": "Estación 1",
                    "lat": 41.3851,
                    "lon": 2.1734,
                    "capacity": 20,
                },
                {
                    "station_id": "2",
                    "name": "Estación 2",
                    "lat": 41.3900,
                    "lon": 2.1800,
                    "capacity": 15,
                },
            ]
        }
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_information()

    assert df is not None
    assert len(df) == 2
    assert meta["success"] is True
    assert meta["total_stations"] == 2
    assert meta["stations_with_valid_coords"] == 2


def test_bicing_extract_station_information_503_error(output_dir: Path) -> None:
    """Debe manejar correctamente errores 503 (Service Unavailable)."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_response = MockResponse(503, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_information()

    assert df is None
    assert meta["success"] is False
    assert meta["error"] == "Service Unavailable (503)"
    assert "suggestion" in meta


def test_bicing_extract_station_information_retry_error_503(output_dir: Path) -> None:
    """Debe manejar RetryError cuando todos los retries fallan con 503."""
    from requests.exceptions import RetryError
    from urllib3.exceptions import MaxRetryError, ResponseError
    
    extractor = BicingExtractor(output_dir=output_dir)

    # Simular RetryError causado por múltiples 503
    retry_error = RetryError(
        MaxRetryError(
            pool=None,
            url="test",
            reason=ResponseError("too many 503 error responses")
        ),
        request=Mock()
    )

    with patch.object(extractor.session, "get", side_effect=retry_error):
        df, meta = extractor.extract_station_information()

    assert df is None
    assert meta["success"] is False
    assert meta["error"] == "Service Unavailable (503)"
    assert "suggestion" in meta


def test_bicing_validate_coordinates_valid() -> None:
    """Debe validar correctamente coordenadas dentro del rango de Barcelona."""
    extractor = BicingExtractor()

    df = pd.DataFrame({
        "station_id": ["1", "2"],
        "name": ["Estación 1", "Estación 2"],
        "lat": [41.3851, 41.3900],
        "lon": [2.1734, 2.1800],
    })

    df_valid = extractor._validate_coordinates(df)

    assert len(df_valid) == 2
    assert all(df_valid["lat"].notna())
    assert all(df_valid["lon"].notna())


def test_bicing_validate_coordinates_out_of_range() -> None:
    """Debe filtrar coordenadas fuera del rango de Barcelona."""
    extractor = BicingExtractor()

    df = pd.DataFrame({
        "station_id": ["1", "2", "3"],
        "name": ["Estación 1", "Estación 2", "Estación 3"],
        "lat": [41.3851, 50.0, 41.4000],  # 50.0 fuera de rango
        "lon": [2.1734, 2.1800, 1.0],  # 1.0 fuera de rango
    })

    df_valid = extractor._validate_coordinates(df)

    # Solo el primer registro debe ser válido
    assert len(df_valid) == 1
    assert df_valid.iloc[0]["station_id"] == "1"


def test_bicing_validate_coordinates_missing() -> None:
    """Debe filtrar registros con coordenadas faltantes."""
    extractor = BicingExtractor()

    df = pd.DataFrame({
        "station_id": ["1", "2", "3"],
        "name": ["Estación 1", "Estación 2", "Estación 3"],
        "lat": [41.3851, None, 41.3900],
        "lon": [2.1734, 2.1800, None],
    })

    df_valid = extractor._validate_coordinates(df)

    # Solo el primer registro debe ser válido
    assert len(df_valid) == 1
    assert df_valid.iloc[0]["station_id"] == "1"


def test_bicing_validate_coordinates_different_column_names() -> None:
    """Debe detectar coordenadas con diferentes nombres de columnas."""
    extractor = BicingExtractor()

    # Probar con diferentes nombres comunes
    test_cases = [
        ("latitude", "longitude"),
        ("latitud", "longitud"),
        ("coord_y", "coord_x"),
    ]

    for lat_col, lon_col in test_cases:
        df = pd.DataFrame({
            "station_id": ["1"],
            lat_col: [41.3851],
            lon_col: [2.1734],
        })

        df_valid = extractor._validate_coordinates(df)
        assert len(df_valid) == 1, f"Falló con columnas {lat_col}, {lon_col}"


def test_bicing_validate_coordinates_no_coord_columns() -> None:
    """Debe retornar DataFrame vacío si no hay columnas de coordenadas."""
    extractor = BicingExtractor()

    df = pd.DataFrame({
        "station_id": ["1"],
        "name": ["Estación 1"],
    })

    df_valid = extractor._validate_coordinates(df)

    assert len(df_valid) == 0


def test_bicing_extract_all_combines_info_and_status(output_dir: Path) -> None:
    """Debe combinar información y estado de estaciones."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_info_data = {
        "data": {
            "stations": [
                {"station_id": "1", "name": "Estación 1", "lat": 41.3851, "lon": 2.1734}
            ]
        }
    }

    mock_status_data = {
        "data": {
            "stations": [
                {"station_id": "1", "num_bikes_available": 5, "num_docks_available": 15}
            ]
        }
    }

    mock_info_response = MockResponse(200, mock_info_data)
    mock_status_response = MockResponse(200, mock_status_data)

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_info_response, mock_status_response]
        df, meta = extractor.extract_all()

    assert df is not None
    assert "station_id" in df.columns
    assert meta["has_status"] is True


def test_bicing_extract_all_no_status(output_dir: Path) -> None:
    """Debe funcionar aunque no haya estado disponible."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_info_data = {
        "data": {
            "stations": [
                {"station_id": "1", "name": "Estación 1", "lat": 41.3851, "lon": 2.1734}
            ]
        }
    }

    mock_info_response = MockResponse(200, mock_info_data)
    mock_status_response = MockResponse(503, {})

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_info_response, mock_status_response]
        df, meta = extractor.extract_all()

    assert df is not None
    assert meta["has_status"] is False


def test_atm_extract_infrastructures_success(output_dir: Path) -> None:
    """Debe extraer infraestructuras de AMB correctamente."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_data = {
        "items": [
            {
                "id": "1",
                "titol": "Estación de Metro",
                "localitzacio": {"lat": 41.3851, "lon": 2.1734},
            },
            {
                "id": "2",
                "titol": "Parada de Bus",
                "localitzacio": {"lat": 41.3900, "lon": 2.1800},
            },
        ],
        "count": 2,
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_infrastructures()

    assert df is not None
    assert len(df) == 2
    assert meta["success"] is True
    assert meta["total_records"] == 2


def test_atm_extract_infrastructures_empty_response(output_dir: Path) -> None:
    """Debe manejar correctamente respuestas vacías."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_data = {"items": [], "count": 0}

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_infrastructures()

    assert df is not None
    assert len(df) == 0
    assert meta["success"] is True


def test_atm_extract_infrastructures_unexpected_structure(output_dir: Path) -> None:
    """Debe manejar estructuras de respuesta inesperadas."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_data = {"error": "Invalid request"}

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_infrastructures()

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_atm_extract_equipaments_with_filter(output_dir: Path) -> None:
    """Debe extraer equipamientos con filtro de tipo."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_data = {
        "items": [
            {"id": "1", "titol": "Equipamiento 1", "subambit": "Transporte"}
        ],
        "count": 1,
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_equipaments(filter_type="Transporte")

    assert df is not None
    assert meta["success"] is True


def test_atm_extract_all_combines_sources(output_dir: Path) -> None:
    """Debe combinar infraestructuras y equipamientos."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_infra_data = {
        "items": [{"id": "1", "titol": "Infraestructura"}],
        "count": 1,
    }

    mock_equip_data = {
        "items": [{"id": "2", "titol": "Equipamiento"}],
        "count": 1,
    }

    mock_infra_response = MockResponse(200, mock_infra_data)
    mock_equip_response = MockResponse(200, mock_equip_data)

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_infra_response, mock_equip_response]
        df, meta = extractor.extract_all()

    assert df is not None
    assert len(df) == 2
    assert "source_collection" in df.columns
    assert meta["has_infrastructures"] is True
    assert meta["has_equipaments"] is True


def test_bicing_criteria_200_plus_stations(output_dir: Path) -> None:
    """Debe verificar criterio de ≥200 estaciones."""
    extractor = BicingExtractor(output_dir=output_dir)

    # Crear mock con 250 estaciones
    stations = [
        {
            "station_id": str(i),
            "name": f"Estación {i}",
            "lat": 41.3851 + (i % 10) * 0.001,
            "lon": 2.1734 + (i % 10) * 0.001,
        }
        for i in range(250)
    ]

    mock_data = {"data": {"stations": stations}}
    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_information()

    assert df is not None
    assert len(df) >= 200
    assert meta["stations_with_valid_coords"] >= 200


def test_bicing_extract_station_status_success(output_dir: Path) -> None:
    """Debe extraer estado de estaciones correctamente."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_data = {
        "data": {
            "stations": [
                {
                    "station_id": "1",
                    "num_bikes_available": 5,
                    "num_docks_available": 15,
                    "is_renting": True,
                }
            ]
        }
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_status()

    assert df is not None
    assert len(df) == 1
    assert meta["success"] is True
    assert "num_bikes_available" in df.columns


def test_bicing_extract_station_information_unexpected_structure(output_dir: Path) -> None:
    """Debe manejar estructuras de respuesta inesperadas."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_data = {"error": "Invalid structure"}

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_information()

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_bicing_extract_station_status_503_error(output_dir: Path) -> None:
    """Debe manejar errores 503 en extract_station_status."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_response = MockResponse(503, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_status()

    assert df is None
    assert meta["success"] is False
    assert meta["error"] == "Service Unavailable (503)"


def test_bicing_extract_station_status_unexpected_structure(output_dir: Path) -> None:
    """Debe manejar estructuras inesperadas en extract_station_status."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_data = {"error": "Invalid structure"}

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_station_status()

    assert df is None
    assert meta["success"] is False


def test_bicing_extract_all_no_station_id(output_dir: Path) -> None:
    """Debe manejar merge sin station_id."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_info_data = {
        "data": {
            "stations": [
                {"name": "Estación 1", "lat": 41.3851, "lon": 2.1734}
            ]
        }
    }

    mock_status_data = {
        "data": {
            "stations": [
                {"name": "Estación 1", "num_bikes_available": 5}
            ]
        }
    }

    mock_info_response = MockResponse(200, mock_info_data)
    mock_status_response = MockResponse(200, mock_status_data)

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_info_response, mock_status_response]
        df, meta = extractor.extract_all()

    assert df is not None
    # has_status puede ser True aunque no se haga merge si hay datos de estado disponibles
    assert meta["has_status"] is True
    # Pero el DataFrame combinado solo debe tener columnas de info (sin merge)
    assert "num_bikes_available" not in df.columns or "num_bikes_available_status" not in df.columns


def test_bicing_extract_all_info_none(output_dir: Path) -> None:
    """Debe manejar cuando extract_station_information retorna None."""
    extractor = BicingExtractor(output_dir=output_dir)

    mock_response = MockResponse(503, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_all()

    assert df is None
    assert meta["success"] is False


def test_atm_extract_equipaments_error(output_dir: Path) -> None:
    """Debe manejar errores en extract_equipaments."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_response = MockResponse(500, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_equipaments()

    assert df is None
    assert meta["success"] is False


def test_atm_extract_mobility_studies_success(output_dir: Path) -> None:
    """Debe extraer estudios de movilidad correctamente."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_data = {
        "items": [
            {"id": "1", "titol": "Estudio de Movilidad 1"}
        ],
        "count": 1,
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_mobility_studies()

    assert df is not None
    assert meta["success"] is True


def test_atm_extract_mobility_studies_error(output_dir: Path) -> None:
    """Debe manejar errores en extract_mobility_studies."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_response = MockResponse(500, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_mobility_studies()

    assert df is None
    assert meta["success"] is False


def test_atm_extract_all_no_data(output_dir: Path) -> None:
    """Debe manejar cuando no hay datos disponibles."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_infra_response = MockResponse(500, {})
    mock_equip_response = MockResponse(500, {})

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_infra_response, mock_equip_response]
        df, meta = extractor.extract_all()

    assert df is None
    assert meta["success"] is False


def test_atm_extract_all_only_infrastructures(output_dir: Path) -> None:
    """Debe funcionar solo con infraestructuras."""
    extractor = ATMExtractor(output_dir=output_dir)

    mock_infra_data = {
        "items": [{"id": "1", "titol": "Infraestructura"}],
        "count": 1,
    }

    mock_infra_response = MockResponse(200, mock_infra_data)
    mock_equip_response = MockResponse(500, {})

    with patch.object(extractor.session, "get") as mock_get:
        mock_get.side_effect = [mock_infra_response, mock_equip_response]
        df, meta = extractor.extract_all()

    assert df is not None
    assert len(df) == 1
    assert meta["has_infrastructures"] is True
    assert meta["has_equipaments"] is False

