"""
Tests unitarios para ViviendaPublicaExtractor.

Cobertura objetivo: ≥80%

⚠️ IMPORTANTE: Los tests verifican que las advertencias sobre estimaciones
sean claras y que la distribución proporcional funcione correctamente.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.extraction.vivienda_publica_extractor import ViviendaPublicaExtractor


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
def mock_municipal_data() -> pd.DataFrame:
    """Datos municipales simulados (esquema extract_idescat_vivienda_publica)."""
    return pd.DataFrame({
        "viviendas_proteccion_oficial": [500],
        "viviendas_iniciadas_total": [2000],
        "viviendas_iniciadas_vpo": [500],
    })


@pytest.fixture
def mock_barrios_weights() -> pd.DataFrame:
    """Pesos de barrios simulados."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 3],
        "barrio_nombre": ["Barrio 1", "Barrio 2", "Barrio 3"],
        "peso": [10000, 5000, 5000],  # Total: 20000
    })


@pytest.mark.skip(reason="extract_idescat_alquiler reemplazado por extract_idescat_vivienda_publica")
def test_extract_idescat_alquiler_success(output_dir: Path) -> None:
    """Debe extraer datos de alquiler IDESCAT correctamente."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_data = {
        "data": [
            {
                "renta_media_alquiler": 850.0,
                "contratos_nuevos": 5000,
                "fianzas_euros": 5000000.0,
            }
        ]
    }

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_idescat_alquiler(2024)

    assert df is not None
    assert len(df) == 1
    assert meta["success"] is True
    assert meta["level"] == "municipal"
    assert meta["year"] == 2024


@pytest.mark.skip(reason="extract_idescat_alquiler reemplazado por extract_idescat_vivienda_publica")
def test_extract_idescat_alquiler_list_response(output_dir: Path) -> None:
    """Debe manejar respuestas que son listas directamente."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_data = [
        {
            "renta_media_alquiler": 850.0,
            "contratos_nuevos": 5000,
        }
    ]

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_idescat_alquiler(2024)

    assert df is not None
    assert len(df) == 1


@pytest.mark.skip(reason="extract_idescat_alquiler reemplazado por extract_idescat_vivienda_publica")
def test_extract_idescat_alquiler_unexpected_structure(output_dir: Path) -> None:
    """Debe manejar estructuras de respuesta inesperadas."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_data = {"error": "Invalid structure"}

    mock_response = MockResponse(200, mock_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_idescat_alquiler(2024)

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_distribute_to_barrios_proportional(output_dir: Path, mock_municipal_data: pd.DataFrame, mock_barrios_weights: pd.DataFrame) -> None:
    """Debe distribuir datos municipales proporcionalmente por barrio."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    # Crear BD temporal
    mock_db_path = output_dir.parent / "database.db"
    mock_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(mock_db_path))
    conn.close()

    with patch.object(extractor, "_get_barrios_with_weights", return_value=mock_barrios_weights):
        df_distributed, meta = extractor.distribute_to_barrios(
            mock_municipal_data,
            db_path=mock_db_path,
            weight_type="poblacion",
            year=2024
        )

    assert df_distributed is not None
    assert len(df_distributed) == 3
    assert meta["is_estimated"] is True
    assert meta["distribution_method"] == "proportional"
    assert "warning" in meta
    
    # Verificar que los valores están distribuidos proporcionalmente
    # Barrio 1: 10000/20000 = 50%
    # Barrio 2: 5000/20000 = 25%
    # Barrio 3: 5000/20000 = 25%
    
    barrio_1 = df_distributed[df_distributed["barrio_id"] == 1].iloc[0]
    barrio_2 = df_distributed[df_distributed["barrio_id"] == 2].iloc[0]
    barrio_3 = df_distributed[df_distributed["barrio_id"] == 3].iloc[0]
    
    # Verificar proporciones (viviendas_proteccion_oficial: 500 total, 50%/25%/25%)
    assert abs(barrio_1["viviendas_proteccion_oficial"] - 250) < 1  # 50% de 500
    assert abs(barrio_2["viviendas_proteccion_oficial"] - 125) < 1  # 25% de 500
    assert abs(barrio_3["viviendas_proteccion_oficial"] - 125) < 1  # 25% de 500
    
    # Verificar que todos tienen is_estimated=True
    assert all(df_distributed["is_estimated"] == True)
    
    # Limpiar
    if mock_db_path.exists():
        mock_db_path.unlink()


def test_distribute_to_barrios_uniform_fallback(output_dir: Path, mock_municipal_data: pd.DataFrame) -> None:
    """Debe usar distribución uniforme cuando el peso total es 0."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    # Barrios con peso 0
    barrios_zero_weight = pd.DataFrame({
        "barrio_id": [1, 2],
        "barrio_nombre": ["Barrio 1", "Barrio 2"],
        "peso": [0, 0],
    })

    # Crear BD temporal
    mock_db_path = output_dir.parent / "database.db"
    mock_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(mock_db_path))
    conn.close()

    with patch.object(extractor, "_get_barrios_with_weights", return_value=barrios_zero_weight):
        df_distributed, meta = extractor.distribute_to_barrios(
            mock_municipal_data,
            db_path=mock_db_path,
            weight_type="poblacion",
            year=2024
        )

    assert df_distributed is not None
    assert len(df_distributed) == 2
    
    # Con distribución uniforme, cada barrio debería tener 50% (2 barrios)
    barrio_1 = df_distributed[df_distributed["barrio_id"] == 1].iloc[0]
    assert abs(barrio_1["viviendas_proteccion_oficial"] - 250) < 1  # 50% de 500
    
    # Limpiar
    if mock_db_path.exists():
        mock_db_path.unlink()


def test_distribute_to_barrios_empty_municipal_data(output_dir: Path) -> None:
    """Debe manejar DataFrame municipal vacío."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    empty_df = pd.DataFrame()

    mock_db_path = output_dir.parent / "database.db"

    df_distributed, meta = extractor.distribute_to_barrios(
        empty_df,
        db_path=mock_db_path,
        weight_type="poblacion",
        year=2024
    )

    assert df_distributed is None
    assert meta["success"] is False
    assert "error" in meta


def test_distribute_to_barrios_multiple_rows_warning(output_dir: Path, mock_barrios_weights: pd.DataFrame) -> None:
    """Debe advertir cuando hay múltiples filas municipales."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    # DataFrame con múltiples filas
    multi_row_df = pd.DataFrame({
        "renta_media_alquiler": [850.0, 900.0],
        "contratos_nuevos": [5000, 5500],
    })

    # Crear BD temporal
    mock_db_path = output_dir.parent / "database.db"
    mock_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(mock_db_path))
    conn.close()

    with patch.object(extractor, "_get_barrios_with_weights", return_value=mock_barrios_weights):
        df_distributed, meta = extractor.distribute_to_barrios(
            multi_row_df,
            db_path=mock_db_path,
            weight_type="poblacion",
            year=2024
        )

    # Debe usar solo la primera fila
    assert df_distributed is not None
    assert len(df_distributed) == 3
    
    # Limpiar
    if mock_db_path.exists():
        mock_db_path.unlink()


def test_get_barrios_with_weights_poblacion(output_dir: Path) -> None:
    """Debe obtener pesos de población correctamente."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)
    
    # Crear BD temporal
    db_path = output_dir.parent / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    
    # Crear tablas mínimas (poblacion usa v_demografia_aggregated)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_barrios (
            barrio_id INTEGER PRIMARY KEY,
            barrio_nombre TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS v_demografia_aggregated (
            barrio_id INTEGER,
            anio INTEGER,
            poblacion_total INTEGER
        )
    """)
    
    conn.execute("INSERT INTO dim_barrios VALUES (1, 'Barrio 1')")
    conn.execute("INSERT INTO dim_barrios VALUES (2, 'Barrio 2')")
    conn.execute("INSERT INTO v_demografia_aggregated VALUES (1, 2024, 10000)")
    conn.execute("INSERT INTO v_demografia_aggregated VALUES (2, 2024, 5000)")
    conn.commit()
    
    df = extractor._get_barrios_with_weights(conn, weight_type="poblacion", year=2024)
    
    conn.close()
    db_path.unlink()  # Limpiar
    
    assert len(df) == 2
    assert df["peso"].sum() == 15000
    assert "barrio_id" in df.columns
    assert "peso" in df.columns


def test_get_barrios_with_weights_renta(output_dir: Path) -> None:
    """Debe obtener pesos de renta correctamente."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)
    
    # Crear BD temporal
    db_path = output_dir.parent / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    
    # Crear tablas mínimas
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_barrios (
            barrio_id INTEGER PRIMARY KEY,
            barrio_nombre TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_renta (
            barrio_id INTEGER,
            anio INTEGER,
            renta_mediana REAL,
            FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
        )
    """)
    
    # Insertar datos de prueba
    conn.execute("INSERT INTO dim_barrios VALUES (1, 'Barrio 1')")
    conn.execute("INSERT INTO dim_barrios VALUES (2, 'Barrio 2')")
    conn.execute("INSERT INTO fact_renta VALUES (1, 2024, 30000)")
    conn.execute("INSERT INTO fact_renta VALUES (2, 2024, 25000)")
    conn.commit()
    
    df = extractor._get_barrios_with_weights(conn, weight_type="renta", year=2024)
    
    conn.close()
    db_path.unlink()  # Limpiar
    
    assert len(df) == 2
    assert df["peso"].sum() == 55000
    assert "barrio_id" in df.columns
    assert "peso" in df.columns


@pytest.mark.skip(reason="extract_all usa extract_idescat_vivienda_publica con API EMEX distinta; requiere mock complejo")
def test_extract_all_with_distribution(output_dir: Path, mock_barrios_weights: pd.DataFrame) -> None:
    """Debe extraer y distribuir datos correctamente."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_municipal_data = {
        "data": [
            {
                "renta_media_alquiler": 850.0,
                "contratos_nuevos": 5000,
            }
        ]
    }

    mock_response = MockResponse(200, mock_municipal_data)
    
    # Crear BD temporal
    mock_db_path = output_dir.parent / "database.db"
    mock_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(mock_db_path))
    conn.close()

    with patch.object(extractor.session, "get", return_value=mock_response):
        with patch.object(extractor, "_get_barrios_with_weights", return_value=mock_barrios_weights):
            df, meta = extractor.extract_all(
                year=2024,
                distribute=True,
                weight_type="poblacion",
                db_path=mock_db_path
            )

    assert df is not None
    assert meta["is_estimated"] is True
    assert meta["level"] == "barrio"
    assert "warning" in meta
    # Verificar que el warning menciona estimaciones o estimated
    warning_lower = meta["warning"].lower()
    assert "estimaciones" in warning_lower or "estimated" in warning_lower or "estimados" in warning_lower
    
    # Limpiar
    if mock_db_path.exists():
        mock_db_path.unlink()


@pytest.mark.skip(reason="extract_all usa extract_idescat_vivienda_publica con API EMEX; requiere red")
def test_extract_all_without_distribution(output_dir: Path) -> None:
    """Debe extraer datos municipales sin distribuir."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_municipal_data = {
        "data": [
            {
                "renta_media_alquiler": 850.0,
                "contratos_nuevos": 5000,
            }
        ]
    }

    mock_response = MockResponse(200, mock_municipal_data)

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_all(year=2024, distribute=False)

    assert df is not None
    assert meta["level"] == "municipal"
    assert "warning" in meta


def test_distribute_to_barrios_missing_db(output_dir: Path, mock_municipal_data: pd.DataFrame) -> None:
    """Debe manejar correctamente cuando la BD no existe."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    non_existent_db = output_dir.parent / "nonexistent.db"

    df_distributed, meta = extractor.distribute_to_barrios(
        mock_municipal_data,
        db_path=non_existent_db,
        weight_type="poblacion",
        year=2024
    )

    assert df_distributed is None
    assert meta["success"] is False
    assert "error" in meta


def test_distribute_to_barrios_no_barrios_with_weights(output_dir: Path, mock_municipal_data: pd.DataFrame) -> None:
    """Debe manejar cuando no hay barrios con pesos."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    empty_barrios = pd.DataFrame(columns=["barrio_id", "barrio_nombre", "peso"])

    mock_db_path = output_dir.parent / "database.db"

    with patch.object(extractor, "_get_barrios_with_weights", return_value=empty_barrios):
        df_distributed, meta = extractor.distribute_to_barrios(
            mock_municipal_data,
            db_path=mock_db_path,
            weight_type="poblacion",
            year=2024
        )

    assert df_distributed is None
    assert meta["success"] is False
    assert "error" in meta


def test_distribute_to_barrios_missing_columns(output_dir: Path, mock_barrios_weights: pd.DataFrame) -> None:
    """Debe manejar cuando faltan columnas en los datos municipales."""
    import sqlite3
    
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    # DataFrame sin columnas relevantes
    df_no_cols = pd.DataFrame({
        "otra_columna": [100],
    })

    # Crear BD temporal
    mock_db_path = output_dir.parent / "database.db"
    mock_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(mock_db_path))
    conn.close()

    with patch.object(extractor, "_get_barrios_with_weights", return_value=mock_barrios_weights):
        df_distributed, meta = extractor.distribute_to_barrios(
            df_no_cols,
            db_path=mock_db_path,
            weight_type="poblacion",
            year=2024
        )

    # Debe funcionar pero con valores None (sin columnas viviendas_proteccion_oficial/viviendas_iniciadas_total)
    assert df_distributed is not None
    assert len(df_distributed) == 3
    assert df_distributed["viviendas_proteccion_oficial"].isna().all()
    
    # Limpiar
    if mock_db_path.exists():
        mock_db_path.unlink()


@pytest.mark.skip(reason="extract_idescat_alquiler reemplazado por extract_idescat_vivienda_publica")
def test_extract_idescat_alquiler_http_error(output_dir: Path) -> None:
    """Debe manejar errores HTTP correctamente."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)

    mock_response = MockResponse(500, {})

    with patch.object(extractor.session, "get", return_value=mock_response):
        df, meta = extractor.extract_idescat_alquiler(2024)

    assert df is None
    assert meta["success"] is False
    assert "error" in meta


def test_extract_opendata_habitatge_success_with_mock(output_dir: Path) -> None:
    """Extrae habitatges tutelats de Open Data BCN cuando hay datos disponibles."""
    extractor = ViviendaPublicaExtractor(output_dir=output_dir)
    sample_df = pd.DataFrame({
        "register_id": ["99400216457", "99400286258"],
        "address": ["Calle A 1", "Calle B 2"],
    })

    with patch.object(
        extractor.opendata_extractor, "download_dataset", return_value=(sample_df, {"success": True})
    ):
        df, meta = extractor.extract_opendata_habitatge()

    assert df is not None
    assert len(df) == 2
    assert meta.get("success") or "filepath" in meta

