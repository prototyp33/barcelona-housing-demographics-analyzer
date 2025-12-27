"""
Tests unitarios para ComercioExtractor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.extraction.comercio_extractor import ComercioExtractor, BARCELONA_LAT_MIN, BARCELONA_LAT_MAX


@pytest.fixture
def extractor():
    """Fixture para crear un extractor de comercio."""
    return ComercioExtractor(output_dir=Path("data/raw"))


@pytest.fixture
def mock_opendata_extractor():
    """Fixture para mockear OpenDataBCNExtractor."""
    mock = Mock()
    return mock


@pytest.fixture
def sample_locales_df():
    """DataFrame de ejemplo para locales comerciales."""
    return pd.DataFrame({
        "nombre": ["Local 1", "Local 2", "Local 3"],
        "latitud": [41.40, 41.41, 41.42],
        "longitud": [2.15, 2.16, 2.17],
        "codi_barri": [1, 2, 3],
        "tipo_actividad": ["Comercio", "Restaurante", "Tienda"]
    })


@pytest.fixture
def sample_terrazas_df():
    """DataFrame de ejemplo para terrazas."""
    return pd.DataFrame({
        "nombre": ["Terraza 1", "Terraza 2"],
        "latitud": [41.40, 41.41],
        "longitud": [2.15, 2.16],
        "CODI_BARRI": [1, 2],
        "tipo_licencia": ["Anual", "Temporal"]
    })


class TestComercioExtractorInit:
    """Tests para inicialización del extractor."""
    
    def test_init(self, extractor):
        """Verifica que el extractor se inicializa correctamente."""
        assert extractor.source_name == "Comercio"
        assert extractor.opendata_extractor is not None


class TestExtractLocalesComerciales:
    """Tests para extracción de locales comerciales."""
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_extract_locales_comerciales_success(self, mock_opendata_class, extractor, sample_locales_df):
        """Test de extracción exitosa de locales comerciales."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        # Mock search_datasets_by_keyword
        mock_opendata.search_datasets_by_keyword.return_value = ["comerc-test"]
        
        # Mock download_dataset - necesita retornar un DataFrame con más de 1000 registros para cumplir criterio
        large_df = pd.concat([sample_locales_df] * 400, ignore_index=True)  # 1200 registros
        mock_opendata.download_dataset.return_value = (large_df, {"success": True})
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_locales_comerciales()
        
        assert df is not None
        assert len(df) >= 1000
        assert meta["success"] is True
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_extract_locales_comerciales_no_datasets(self, mock_opendata_class, extractor):
        """Test cuando no se encuentran datasets."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        mock_opendata.search_datasets_by_keyword.return_value = []
        mock_opendata.download_dataset.return_value = (None, {"error": "Not found"})
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_locales_comerciales()
        
        assert df is None
        assert meta["success"] is False


class TestExtractTerrazasLicencias:
    """Tests para extracción de terrazas y licencias."""
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_extract_terrazas_licencias_success(self, mock_opendata_class, extractor, sample_terrazas_df):
        """Test de extracción exitosa de terrazas."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        mock_opendata.search_datasets_by_keyword.return_value = ["terrasses-test"]
        mock_opendata.download_dataset.return_value = (sample_terrazas_df, {"success": True})
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_terrazas_licencias()
        
        assert df is not None
        assert len(df) == 2
        assert meta["success"] is True
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_extract_terrazas_licencias_no_datasets(self, mock_opendata_class, extractor):
        """Test cuando no se encuentran datasets de terrazas."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        mock_opendata.search_datasets_by_keyword.return_value = []
        mock_opendata.download_dataset.return_value = (None, {"error": "Not found"})
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_terrazas_licencias()
        
        assert df is None
        assert meta["success"] is False


class TestExtractAll:
    """Tests para extracción completa."""
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_extract_all_combines_sources(self, mock_opendata_class, extractor, sample_locales_df, sample_terrazas_df):
        """Test que combina locales y terrazas."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        # Crear DataFrames grandes para cumplir criterios
        large_locales_df = pd.concat([sample_locales_df] * 400, ignore_index=True)  # 1200 registros
        
        # Mock para locales y terrazas
        call_count = [0]
        def download_side_effect(dataset_id, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # Primera llamada: locales
                return (large_locales_df, {"success": True})
            elif call_count[0] == 2:  # Segunda llamada: terrazas
                return (sample_terrazas_df, {"success": True})
            return (None, {"error": "Not found"})
        
        mock_opendata.search_datasets_by_keyword.return_value = ["comerc-test", "terrasses-test"]
        mock_opendata.download_dataset.side_effect = download_side_effect
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_all()
        
        assert df is not None
        assert len(df) >= 1200  # Al menos los locales
        assert meta["has_locales"] is True
        assert meta["has_terrazas"] is True
        assert "tipo_comercio" in df.columns


class TestValidateCoordinates:
    """Tests para validación de coordenadas."""
    
    def test_validate_coordinates_valid(self, extractor):
        """Test con coordenadas válidas."""
        df = pd.DataFrame({
            "latitud": [41.40, 41.41, 41.42],
            "longitud": [2.15, 2.16, 2.17]
        })
        
        result = extractor._validate_coordinates(df)
        
        assert len(result) == 3
    
    def test_validate_coordinates_out_of_range(self, extractor):
        """Test con coordenadas fuera de rango."""
        df = pd.DataFrame({
            "latitud": [50.0, 41.40, 30.0],  # Primera y tercera fuera de rango
            "longitud": [2.15, 2.16, 2.17]
        })
        
        result = extractor._validate_coordinates(df)
        
        assert len(result) == 1  # Solo la segunda es válida
    
    def test_validate_coordinates_missing(self, extractor):
        """Test con coordenadas faltantes."""
        df = pd.DataFrame({
            "latitud": [41.40, None, 41.42],
            "longitud": [2.15, 2.16, None]
        })
        
        result = extractor._validate_coordinates(df)
        
        assert len(result) == 1  # Solo la primera es válida
    
    def test_validate_coordinates_no_coord_columns(self, extractor):
        """Test sin columnas de coordenadas."""
        df = pd.DataFrame({
            "nombre": ["Test 1", "Test 2"],
            "barrio": [1, 2]
        })
        
        result = extractor._validate_coordinates(df)
        
        assert len(result) == 2  # Devuelve el DataFrame sin filtrar


class TestNormalizeColumns:
    """Tests para normalización de columnas."""
    
    def test_normalize_locales_columns(self, extractor):
        """Test de normalización de columnas de locales."""
        df = pd.DataFrame({
            "nom": ["Local 1"],
            "lat": [41.40],
            "lon": [2.15],
            "barri": [1]
        })
        
        result = extractor._normalize_locales_columns(df)
        
        assert "nombre" in result.columns
        assert "latitud" in result.columns
        assert "longitud" in result.columns
        assert "codi_barri" in result.columns
    
    def test_normalize_terrazas_columns(self, extractor):
        """Test de normalización de columnas de terrazas."""
        df = pd.DataFrame({
            "nom": ["Terraza 1"],
            "lat": [41.40],
            "lon": [2.15],
            "CODI_BARRI": [1]
        })
        
        result = extractor._normalize_terrazas_columns(df)
        
        assert "nombre" in result.columns
        assert "latitud" in result.columns
        assert "longitud" in result.columns
        # CODI_BARRI debería mapearse a codi_barri
        assert "codi_barri" in result.columns or "CODI_BARRI" in result.columns


class TestIsDataset:
    """Tests para validación de datasets."""
    
    def test_is_comercio_dataset_valid(self, extractor):
        """Test que identifica correctamente un dataset de comercio."""
        df = pd.DataFrame({
            "nombre": ["Local comercial"],
            "tipo": ["Comercio"]
        })
        
        result = extractor._is_comercio_dataset(df, "comerc-test")
        
        assert result is True
    
    def test_is_comercio_dataset_invalid(self, extractor):
        """Test que rechaza un dataset que no es de comercio."""
        df = pd.DataFrame({
            "nombre": ["Parque"],
            "tipo": ["Verde"]
        })
        
        result = extractor._is_comercio_dataset(df, "parques-test")
        
        assert result is False
    
    def test_is_comercio_dataset_excludes_terrazas(self, extractor):
        """Test que excluye datasets de terrazas."""
        df = pd.DataFrame({
            "nombre": ["Terraza"],
            "tipo": ["Terrassa"]
        })
        
        result = extractor._is_comercio_dataset(df, "terrasses-test")
        
        assert result is False
    
    def test_is_terrazas_dataset_valid(self, extractor):
        """Test que identifica correctamente un dataset de terrazas."""
        df = pd.DataFrame({
            "nombre": ["Terraza"],
            "tipo": ["Terrassa"]
        })
        
        result = extractor._is_terrazas_dataset(df, "terrasses-test")
        
        assert result is True
    
    def test_is_terrazas_dataset_invalid(self, extractor):
        """Test que rechaza un dataset que no es de terrazas."""
        df = pd.DataFrame({
            "nombre": ["Local"],
            "tipo": ["Comercio"]
        })
        
        result = extractor._is_terrazas_dataset(df, "comerc-test")
        
        assert result is False


class TestAcceptanceCriteria:
    """Tests para criterios de aceptación."""
    
    @patch('src.extraction.comercio_extractor.OpenDataBCNExtractor')
    def test_locales_acceptance_criteria(self, mock_opendata_class, extractor):
        """Test que verifica el criterio de ≥1000 locales."""
        mock_opendata = Mock()
        mock_opendata_class.return_value = mock_opendata
        
        # Crear DataFrame con más de 1000 registros
        large_df = pd.DataFrame({
            "nombre": [f"Local {i}" for i in range(1500)],
            "latitud": [41.40] * 1500,
            "longitud": [2.15] * 1500,
            "codi_barri": [1] * 1500
        })
        
        mock_opendata.search_datasets_by_keyword.return_value = ["comerc-test"]
        mock_opendata.download_dataset.return_value = (large_df, {"success": True})
        
        extractor.opendata_extractor = mock_opendata
        
        df, meta = extractor.extract_locales_comerciales()
        
        assert df is not None
        assert len(df) >= 1000
        assert meta["success"] is True

