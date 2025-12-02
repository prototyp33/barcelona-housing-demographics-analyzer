import pandas as pd
import pytest
from src.data_processing import prepare_fact_precios
from datetime import datetime

def test_fact_precios_deduplication():
    # Create dummy dim_barrios
    dim_barrios = pd.DataFrame({
        'barrio_id': [1],
        'barrio_nombre': ['El Raval'],
        'barrio_nombre_normalizado': ['elraval']
    })

    # Create dummy portaldades_venta dataframe (multiple datasets for same barrio/year)
    portaldades_venta = pd.DataFrame([
        {
            'barrio_id': 1,
            'anio': 2023,
            'periodo': '2023',
            'trimestre': pd.NA,
            'precio_m2_venta': 3500.0,
            'precio_mes_alquiler': pd.NA,
            'dataset_id': 'indicator_1',
            'source': 'portaldades',
            'etl_loaded_at': '2023-01-01T00:00:00'
        },
        {
            'barrio_id': 1,
            'anio': 2023,
            'periodo': '2023',
            'trimestre': pd.NA,
            'precio_m2_venta': 3200.0,
            'precio_mes_alquiler': pd.NA,
            'dataset_id': 'indicator_2',
            'source': 'portaldades',
            'etl_loaded_at': '2023-01-01T00:00:00'
        }
    ])

    reference_time = datetime.now()

    # Call prepare_fact_precios with two different indicators for the same barrio/year
    # We expect both to be preserved because they have different dataset_id
    fact = prepare_fact_precios(
        venta=pd.DataFrame(),
        dim_barrios=dim_barrios,
        dataset_id_venta='habitatges-2na-ma',
        reference_time=reference_time,
        portaldades_venta=portaldades_venta
    )

    print("\nResulting Fact Table:")
    print(fact[['barrio_id', 'anio', 'dataset_id', 'precio_m2_venta']])

    # Assertions
    assert len(fact) == 2, "Should preserve both rows with different dataset_id"
    assert 'indicator_1' in fact['dataset_id'].values
    assert 'indicator_2' in fact['dataset_id'].values

if __name__ == "__main__":
    test_fact_precios_deduplication()
