"""
Tests unitarios para prepare_movilidad.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.processing.prepare_movilidad import prepare_movilidad


@pytest.fixture
def barrios_sin_geometry() -> pd.DataFrame:
    """Barrios sin columna geometry_json (debe retornar DataFrame vacío)."""
    return pd.DataFrame({
        "barrio_id": [1, 2],
        "codi_barri": ["01", "02"],
        "barrio_nombre": ["Barrio 1", "Barrio 2"],
    })


@pytest.fixture
def barrios_con_geometry() -> pd.DataFrame:
    """Barrios con geometry_json válido (Polygon simple)."""
    geom = '{"type": "Polygon", "coordinates": [[[2.16, 41.38], [2.17, 41.38], [2.17, 41.39], [2.16, 41.39], [2.16, 41.38]]]}'
    return pd.DataFrame({
        "barrio_id": [1, 2],
        "codi_barri": ["01", "02"],
        "barrio_nombre": ["Barrio 1", "Barrio 2"],
        "geometry_json": [geom, geom],
    })


def test_prepare_movilidad_sin_geometry_json(
    tmp_path: Path,
    barrios_sin_geometry: pd.DataFrame,
) -> None:
    """Debe retornar DataFrame vacío si barrios_df no tiene geometry_json."""
    result = prepare_movilidad(raw_data_dir=tmp_path, barrios_df=barrios_sin_geometry)
    assert result.empty
    assert isinstance(result, pd.DataFrame)


def test_prepare_movilidad_sin_datos_transito(
    tmp_path: Path,
    barrios_con_geometry: pd.DataFrame,
) -> None:
    """Debe retornar DataFrame vacío si no hay archivos de bus/rail en tmb/."""
    tmb_dir = tmp_path / "tmb"
    tmb_dir.mkdir(parents=True, exist_ok=True)
    result = prepare_movilidad(raw_data_dir=tmp_path, barrios_df=barrios_con_geometry)
    assert result.empty


def test_prepare_movilidad_sin_directorio_tmb(
    tmp_path: Path,
    barrios_con_geometry: pd.DataFrame,
) -> None:
    """Debe retornar DataFrame vacío si el directorio tmb no existe."""
    result = prepare_movilidad(raw_data_dir=tmp_path, barrios_df=barrios_con_geometry)
    assert result.empty


def test_prepare_movilidad_barrios_geometry_nula(
    tmp_path: Path,
) -> None:
    """Debe retornar DataFrame vacío si todos los geometry_json son nulos."""
    barrios = pd.DataFrame({
        "barrio_id": [1, 2],
        "geometry_json": [None, None],
    })
    result = prepare_movilidad(raw_data_dir=tmp_path, barrios_df=barrios)
    assert result.empty
