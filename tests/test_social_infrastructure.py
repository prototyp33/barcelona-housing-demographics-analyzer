"""Unit tests for social infrastructure transformations."""

import pandas as pd
import pytest
from datetime import datetime
from src.etl.transformations.social_infrastructure import (
    prepare_fact_educacion,
    prepare_fact_vivienda_publica,
)

@pytest.fixture
def dim_barrios_sample():
    return pd.DataFrame({
        "barrio_id": [1, 2],
        "nom_barri": ["el Raval", "el Barri Gòtic"],
        "barrio_nombre_normalizado": ["el raval", "el barri gotic"],
        "codi_barri": ["01", "02"]
    })

def test_prepare_fact_educacion(dim_barrios_sample):
    # Mock data for education with expected OpenDataBCN columns
    raw_edu = pd.DataFrame({
        "register_id": ["1", "2", "3"],
        "addresses_neighborhood_id": [1, 1, 2],
        "secondary_filters_name": ["Escola bressol", "Escola primària", "Universitat"],
    })
    
    ref_time = datetime(2023, 1, 1)
    df_result = prepare_fact_educacion(raw_edu, dim_barrios_sample, ref_time)
    
    assert not df_result.empty
    assert "total_centros_educativos" in df_result.columns
    assert "num_centros_infantil" in df_result.columns
    
    # Check aggregation
    raval_result = df_result[df_result["barrio_id"] == 1]
    assert raval_result["total_centros_educativos"].iloc[0] == 2
    assert raval_result["num_centros_infantil"].iloc[0] == 1
    assert raval_result["num_centros_primaria"].iloc[0] == 1
    
    gotic_result = df_result[df_result["barrio_id"] == 2]
    assert gotic_result["num_centros_universidad"].iloc[0] == 1

def test_prepare_fact_vivienda_publica(dim_barrios_sample):
    # Mock data for public housing inside a dict
    raw_vivienda = pd.DataFrame({
        "addresses_neighborhood_id": [1, 2],
        "vivienda_id": ["V1", "V2"]
    })
    dfs = {"tutelats": raw_vivienda}
    
    ref_time = datetime(2023, 1, 1)
    df_result = prepare_fact_vivienda_publica(dfs, dim_barrios_sample, ref_time)
    
    assert not df_result.empty
    assert "viviendas_proteccion_oficial" in df_result.columns
    assert df_result[df_result["barrio_id"] == 1]["viviendas_proteccion_oficial"].iloc[0] == 1

def test_prepare_fact_vivienda_publica_empty(dim_barrios_sample):
    # Empty dict
    ref_time = datetime(2023, 1, 1)
    df_result = prepare_fact_vivienda_publica({}, dim_barrios_sample, ref_time)
    assert df_result.empty
