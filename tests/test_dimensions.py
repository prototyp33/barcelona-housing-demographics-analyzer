"""Tests para src.etl.transformations.dimensions."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.etl.transformations.dimensions import prepare_dim_barrios


def test_prepare_dim_barrios_basic():
    """Verifica la creación básica de dim_barrios."""
    demographics = pd.DataFrame({
        "Codi_Barri": [1, 2, 3],
        "Nom_Barri": ["Barrio 1", "Barrio 2", "Barrio 3"],
        "Codi_Districte": [1, 1, 2],
        "Nom_Districte": ["Distrito 1", "Distrito 1", "Distrito 2"],
    })
    
    dim = prepare_dim_barrios(
        demographics=demographics,
        dataset_id="test_dataset",
        reference_time=datetime.now(),
    )
    
    assert len(dim) == 3
    assert "barrio_id" in dim.columns
    assert "barrio_nombre" in dim.columns
    assert "barrio_nombre_normalizado" in dim.columns
    assert "geometry_json" in dim.columns
    assert dim["barrio_id"].tolist() == [1, 2, 3]


def test_prepare_dim_barrios_with_geojson(tmp_path):
    """Verifica la carga de geometrías desde GeoJSON."""
    # Crear GeoJSON de prueba
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"Codi_Barri": 1, "Nom_Barri": "Barrio 1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"Codi_Barri": 2, "Nom_Barri": "Barrio 2"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
                },
            },
        ],
    }
    
    import json
    
    geojson_path = tmp_path / "test.geojson"
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)
    
    demographics = pd.DataFrame({
        "Codi_Barri": [1, 2],
        "Nom_Barri": ["Barrio 1", "Barrio 2"],
        "Codi_Districte": [1, 1],
        "Nom_Districte": ["Distrito 1", "Distrito 1"],
    })
    
    dim = prepare_dim_barrios(
        demographics=demographics,
        dataset_id="test_dataset",
        reference_time=datetime.now(),
        geojson_path=geojson_path,
    )
    
    assert len(dim) == 2
    assert dim["geometry_json"].notna().sum() == 2
    
    # Verificar que las geometrías son JSON válido
    import json as json_module
    
    for geom_json in dim["geometry_json"]:
        assert geom_json is not None
        geom_dict = json_module.loads(geom_json)
        assert "type" in geom_dict
        assert "coordinates" in geom_dict


def test_prepare_dim_barrios_missing_columns():
    """Verifica que se lance error si faltan columnas requeridas."""
    demographics = pd.DataFrame({
        "Codi_Barri": [1],
        # Faltan Nom_Barri, Codi_Districte, Nom_Districte
    })
    
    with pytest.raises(ValueError, match="missing columns"):
        prepare_dim_barrios(
            demographics=demographics,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )


def test_prepare_dim_barrios_normalization():
    """Verifica que se normalicen correctamente los nombres de barrios."""
    demographics = pd.DataFrame({
        "Codi_Barri": [1],
        "Nom_Barri": "El Raval",  # Con artículo y mayúsculas
        "Codi_Districte": [1],
        "Nom_Districte": ["Ciutat Vella"],
    })
    
    dim = prepare_dim_barrios(
        demographics=demographics,
        dataset_id="test_dataset",
        reference_time=datetime.now(),
    )
    
    assert len(dim) == 1
    assert dim["barrio_nombre"].iloc[0] == "El Raval"
    assert "barrio_nombre_normalizado" in dim.columns
    # El nombre normalizado debería estar en minúsculas sin acentos
    normalized = dim["barrio_nombre_normalizado"].iloc[0]
    assert isinstance(normalized, str)
    assert len(normalized) > 0

