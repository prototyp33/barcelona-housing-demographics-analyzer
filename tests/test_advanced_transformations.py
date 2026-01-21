"""Unit tests for advanced transformations (Security and Tourism)."""

import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.processing.prepare_seguridad import prepare_seguridad
from src.etl.transformations.advanced_analysis import prepare_fact_presion_turistica

@pytest.fixture
def dim_barrios_sample():
    return pd.DataFrame({
        "barrio_id": [1, 2],
        "barrio_nombre": ["el Raval", "el Barri Gòtic"],
        "barrio_nombre_normalizado": ["el raval", "el barri gotic"],
        "distrito_nombre": ["Ciutat Vella", "Ciutat Vella"]
    })

def test_prepare_seguridad_icgc(dim_barrios_sample):
    # Mock ICGC data
    raw_icgc = pd.DataFrame({
        "barrio": ["el Raval", "el Barri Gòtic"],
        "any": [2023, 2023],
        "trimestre": [1, 1],
        "delitos_patrimonio_robo": [100, 50],
        "delitos_personal_agresion": [20, 10],
    })
    
    with patch("src.processing.prepare_seguridad._load_icgc_data") as mock_load:
        mock_load.return_value = raw_icgc
        
        # Poblacion mock
        poblacion = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2023, 2023],
            "poblacion_total": [50000, 20000]
        })
        
        df_result = prepare_seguridad(Path("dummy"), dim_barrios_sample, poblacion)
        
        assert not df_result.empty
        assert "tasa_criminalidad_1000hab" in df_result.columns
        assert df_result[df_result["barrio_id"] == 1]["delitos_patrimonio"].iloc[0] == 100
        # Tasa: (120 / 50000) * 1000 = 2.4
        assert df_result[df_result["barrio_id"] == 1]["tasa_criminalidad_1000hab"].iloc[0] == pytest.approx(2.4)

def test_prepare_fact_presion_turistica(dim_barrios_sample):
    # Mock InsideAirbnb data
    raw_airbnb = pd.DataFrame({
        "id": [1, 2, 3],
        "neighbourhood_cleansed": ["el Raval", "el Raval", "el Barri Gòtic"],
        "room_type": ["Entire home/apt", "Private room", "Entire home/apt"],
        "price": ["$100.00", "$50.00", "$150.00"],
        "availability_365": [365, 180, 0],
        "reviews_per_month": [1.5, 0.5, 2.0]
    })
    
    ref_time = datetime(2023, 6, 1)
    df_result = prepare_fact_presion_turistica(raw_airbnb, dim_barrios_sample, ref_time)
    
    assert not df_result.empty
    assert "num_listings_airbnb" in df_result.columns
    assert "pct_entire_home" in df_result.columns
    
    raval = df_result[df_result["barrio_id"] == 1]
    assert raval["num_listings_airbnb"].iloc[0] == 2
    assert raval["pct_entire_home"].iloc[0] == 50.0 # 1 Entire house out of 2
    assert raval["precio_noche_promedio"].iloc[0] == 75.0
    
    gotic = df_result[df_result["barrio_id"] == 2]
    assert gotic["num_listings_airbnb"].iloc[0] == 1
    assert gotic["pct_entire_home"].iloc[0] == 100.0
