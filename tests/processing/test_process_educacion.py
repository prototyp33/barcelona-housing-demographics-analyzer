"""
Tests unitarios para process_educacion_data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


def test_classify_tipo_educacion() -> None:
    """Debe clasificar tipos de equipamientos correctamente."""
    from scripts.process_educacion_data import classify_tipo_educacion
    
    assert classify_tipo_educacion("Educació Infantil") == "infantil"
    assert classify_tipo_educacion("Escola Primària") == "primaria"
    assert classify_tipo_educacion("Institut") == "secundaria"
    assert classify_tipo_educacion("Formació Professional") == "fp"
    assert classify_tipo_educacion("Universitat") == "universidad"
    assert classify_tipo_educacion("Desconocido") is None
    assert classify_tipo_educacion(None) is None


def test_aggregate_by_barrio() -> None:
    """Debe agregar equipamientos por barrio correctamente."""
    from scripts.process_educacion_data import aggregate_by_barrio
    
    df_equipamientos = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Institut 1", "Escola 2"],
        "tipus_equipament": ["Educació Primària", "Educació Secundària", "Educació Primària"],
    })
    
    barrio_ids = pd.Series([1, 1, 2], dtype="Int64")
    anio = 2024
    
    result = aggregate_by_barrio(df_equipamientos, barrio_ids, anio)
    
    assert not result.empty
    assert len(result) == 2
    assert result[result["barrio_id"] == 1]["num_centros_primaria"].iloc[0] == 1
    assert result[result["barrio_id"] == 1]["num_centros_secundaria"].iloc[0] == 1
    assert result[result["barrio_id"] == 2]["num_centros_primaria"].iloc[0] == 1


def test_geocode_equipamientos_with_geometries(tmp_path: Path) -> None:
    """Debe geocodificar equipamientos usando geometrías si están disponibles."""
    try:
        from scripts.process_educacion_data import geocode_equipamientos_to_barrios
        from shapely.geometry import shape
        import geopandas as gpd
    except ImportError:
        pytest.skip("shapely o geopandas no están instalados")
    
    # Crear DataFrame de equipamientos con coordenadas
    df_equipamientos = pd.DataFrame({
        "nom_equipament": ["Escola 1", "Institut 1"],
        "latitud": [41.3851, 41.3900],
        "longitud": [2.1734, 2.1800],
    })
    
    # Crear DataFrame de barrios con geometrías simples
    geometries = [
        {"type": "Polygon", "coordinates": [[[2.17, 41.38], [2.18, 41.38], [2.18, 41.39], [2.17, 41.39], [2.17, 41.38]]]},
        {"type": "Polygon", "coordinates": [[[2.18, 41.39], [2.19, 41.39], [2.19, 41.40], [2.18, 41.40], [2.18, 41.39]]]},
    ]
    
    df_barrios = pd.DataFrame({
        "barrio_id": [1, 2],
        "barrio_nombre": ["Barrio 1", "Barrio 2"],
        "geometry_json": [json.dumps(g) for g in geometries],
    })
    
    result = geocode_equipamientos_to_barrios(df_equipamientos, df_barrios)
    
    assert len(result) == 2
    assert result.notna().any()  # Al menos uno debe estar mapeado


def test_aggregate_by_barrio_empty() -> None:
    """Debe manejar correctamente cuando no hay equipamientos."""
    from scripts.process_educacion_data import aggregate_by_barrio
    
    df_empty = pd.DataFrame()
    barrio_ids = pd.Series([], dtype="Int64")
    
    result = aggregate_by_barrio(df_empty, barrio_ids, 2024)
    
    assert result.empty
    assert "barrio_id" in result.columns
    assert "anio" in result.columns

