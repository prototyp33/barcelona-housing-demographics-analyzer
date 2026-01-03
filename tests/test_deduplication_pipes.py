import pandas as pd
import pytest
from src.etl.transformations.market import prepare_fact_precios
from datetime import datetime

def test_fact_precios_deduplication_pipe_normalization():
    # Setup dummy data
    dim_barrios = pd.DataFrame({
        'barrio_id': [1],
        'barrio_nombre': ['El Raval'],
        'barrio_nombre_normalizado': ['elraval']
    })

    # Create dummy data with duplicated pipes in source
    # Case 1: "SourceA|SourceA" -> should be normalized to "SourceA"
    # Case 2: "SourceA" -> should remain "SourceA"
    # If normalization happens AFTER deduplication, we might end up with two rows for "SourceA"
    # if the input had one "SourceA" and one "SourceA|SourceA" and they were treated as distinct.

    venta_df = pd.DataFrame([
        {
            'Barris': 'El Raval',
            'año': 2023,
            'Valor': '3500.0',
            'source': 'SourceA'
        },
        {
            'Barris': 'El Raval',
            'año': 2023,
            'Valor': '3500.0',
            'source': 'SourceA|SourceA'
        }
    ])

    reference_time = datetime.now()

    # We use dataset_id='test_ds' for both rows coming from 'venta' argument
    fact = prepare_fact_precios(
        venta=venta_df,
        dim_barrios=dim_barrios,
        dataset_id_venta='test_ds',
        reference_time=reference_time
    )

    print("\nResulting Fact Table:")
    print(fact[['barrio_id', 'anio', 'source', 'precio_m2_venta']])

    # We expect exactly 1 row if deduplication works correctly with normalization
    assert len(fact) == 1, f"Should have 1 row, but got {len(fact)}. Duplicates were not handled correctly."
    assert fact.iloc[0]['source'] == 'SourceA'

if __name__ == "__main__":
    test_fact_precios_deduplication_pipe_normalization()
