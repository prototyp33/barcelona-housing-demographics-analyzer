"""
Tests para el módulo de métricas de calidad de datos.
"""

import pytest
from unittest.mock import Mock, patch

import pandas as pd

from src.app.data_quality_metrics import (
    calculate_completeness,
    calculate_consistency,
    calculate_timeliness,
    calculate_validity,
    detect_quality_issues,
)


@pytest.fixture
def mock_connection():
    """Mock de conexión a base de datos."""
    conn = Mock()
    return conn


@pytest.fixture
def sample_data():
    """Datos de ejemplo para tests."""
    return {
        "fact_precios": pd.DataFrame({
            "barrio_id": [1, 2, 3],
            "anio": [2022, 2022, 2022],
            "precio_m2": [3000, 4000, None],  # Un NULL
        }),
        "fact_demografia": pd.DataFrame({
            "barrio_id": [1, 2, 3],
            "anio": [2022, 2022, 2022],
            "poblacion": [1000, 2000, 3000],
        }),
    }


@patch("src.app.data_quality_metrics.get_connection")
def test_calculate_completeness(mock_get_conn, mock_connection):
    """Test cálculo de completitud."""
    # Mock de resultados SQL
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    
    # Mock de resultados de queries
    total_df = pd.DataFrame({"total": [100]})
    non_null_df = pd.DataFrame({"non_null": [95]})
    
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.side_effect = [total_df, non_null_df, total_df, non_null_df, total_df, non_null_df]
        
        result = calculate_completeness()
        
        assert isinstance(result, float)
        assert 0 <= result <= 100


@patch("src.app.data_quality_metrics.get_connection")
def test_calculate_validity(mock_get_conn):
    """Test cálculo de validez."""
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    
    total_df = pd.DataFrame({"total": [100]})
    valid_df = pd.DataFrame({"valid": [98]})
    
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.side_effect = [total_df, valid_df, total_df, valid_df]
        
        result = calculate_validity()
        
        assert isinstance(result, float)
        assert 0 <= result <= 100


@patch("src.app.data_quality_metrics.get_connection")
def test_calculate_consistency(mock_get_conn):
    """Test cálculo de consistencia."""
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    
    barrios_df = pd.DataFrame({"barrio_id": [1, 2, 3]})
    
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = barrios_df
        
        result = calculate_consistency()
        
        assert isinstance(result, float)
        assert 0 <= result <= 100


@patch("src.app.data_quality_metrics.get_connection")
def test_calculate_timeliness(mock_get_conn):
    """Test cálculo de actualidad."""
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    
    max_year_df = pd.DataFrame({"max_year": [2022]})
    
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = max_year_df
        
        result = calculate_timeliness()
        
        assert isinstance(result, int)
        assert result >= 0


@patch("src.app.data_quality_metrics.get_connection")
def test_detect_quality_issues(mock_get_conn):
    """Test detección de issues."""
    mock_conn = Mock()
    mock_get_conn.return_value = mock_conn
    
    empty_df = pd.DataFrame(columns=["barrio_nombre"])
    
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = empty_df
        
        result = detect_quality_issues()
        
        assert isinstance(result, pd.DataFrame)
        assert "Barrio" in result.columns or result.empty


def test_get_quality_history():
    """Test obtención de historial de calidad."""
    # Esta función usa otras funciones cached, así que solo verificamos estructura
    with patch("src.app.data_quality_metrics.calculate_completeness", return_value=96.2):
        with patch("src.app.data_quality_metrics.calculate_validity", return_value=98.5):
            with patch("src.app.data_quality_metrics.calculate_consistency", return_value=94.8):
                from src.app.data_quality_metrics import get_quality_history
                
                result = get_quality_history()
                
                assert isinstance(result, pd.DataFrame)
                assert "fecha" in result.columns
                assert "completeness" in result.columns
                assert "validity" in result.columns
                assert "consistency" in result.columns

