"""
Tests unitarios para el extractor de IDESCAT.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

from src.extraction.idescat import IDESCATExtractor


class TestIDESCATExtractor:
    """Tests para la clase IDESCATExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Crea una instancia del extractor para testing."""
        return IDESCATExtractor(rate_limit_delay=0.1)
    
    @pytest.fixture
    def mock_dim_barrios(self):
        """Crea un DataFrame mock con datos de barrios."""
        return pd.DataFrame({
            "barrio_id": [1, 2, 3],
            "barrio_nombre": ["Ciutat Vella", "Eixample", "Gràcia"],
            "barrio_nombre_normalizado": ["ciutatvella", "eixample", "gracia"]
        })
    
    def test_init(self, extractor):
        """Verifica que el extractor se inicializa correctamente."""
        assert extractor.source_name == "IDESCAT"
        assert extractor.rate_limit_delay == 0.1
        assert extractor.BASE_URL == "https://www.idescat.cat"
        assert extractor.API_BASE_URL == "https://api.idescat.cat"
    
    def test_normalize_barrio_name(self, extractor):
        """Verifica la normalización de nombres de barrios."""
        # Test casos básicos
        assert extractor._normalize_barrio_name("Ciutat Vella") == "ciutatvella"
        assert extractor._normalize_barrio_name("Gràcia") == "gracia"
        assert extractor._normalize_barrio_name("L'Eixample") == "leixample"
        
        # Test con None
        assert extractor._normalize_barrio_name(None) == ""
        
        # Test con espacios y caracteres especiales
        assert extractor._normalize_barrio_name("  Sant Martí  ") == "santmarti"
    
    def test_map_barrio_to_id_exact_match(self, extractor, mock_dim_barrios):
        """Verifica el mapeo de barrio a ID con coincidencia exacta."""
        barrio_id = extractor._map_barrio_to_id("Ciutat Vella", mock_dim_barrios)
        assert barrio_id == 1
        
        barrio_id = extractor._map_barrio_to_id("Eixample", mock_dim_barrios)
        assert barrio_id == 2
    
    def test_map_barrio_to_id_partial_match(self, extractor, mock_dim_barrios):
        """Verifica el mapeo de barrio a ID con coincidencia parcial."""
        # Debería encontrar "Gràcia" aunque el nombre sea ligeramente diferente
        barrio_id = extractor._map_barrio_to_id("Gracia", mock_dim_barrios)
        assert barrio_id == 3
    
    def test_map_barrio_to_id_not_found(self, extractor, mock_dim_barrios):
        """Verifica que retorna None cuando no se encuentra el barrio."""
        barrio_id = extractor._map_barrio_to_id("Barrio Inexistente", mock_dim_barrios)
        assert barrio_id is None
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    @patch('src.extraction.idescat.IDESCATExtractor._try_public_files')
    def test_get_renta_by_barrio_api_success(
        self,
        mock_public_files,
        mock_web_scraping,
        mock_api_indicators,
        extractor
    ):
        """Verifica que get_renta_by_barrio usa la API cuando está disponible."""
        # Mock de datos exitosos desde API
        mock_df = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2020, 2020],
            "renta_media": [25000, 30000]
        })
        mock_metadata = {
            "strategy": "api_indicators",
            "success": True,
            "years_extracted": [2020]
        }
        
        mock_api_indicators.return_value = (mock_df, mock_metadata)
        mock_web_scraping.return_value = (pd.DataFrame(), {})
        mock_public_files.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert not df.empty
        assert len(df) == 2
        assert metadata["strategy_used"] == "api_indicators"
        assert metadata["success"] is True
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_not_called()
        mock_public_files.assert_not_called()
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    @patch('src.extraction.idescat.IDESCATExtractor._try_public_files')
    def test_get_renta_by_barrio_fallback_to_web(
        self,
        mock_public_files,
        mock_web_scraping,
        mock_api_indicators,
        extractor
    ):
        """Verifica que se hace fallback a web scraping si la API falla."""
        mock_df = pd.DataFrame({
            "barrio_id": [1],
            "anio": [2020],
            "renta_media": [25000]
        })
        mock_metadata = {
            "strategy": "web_scraping",
            "success": True
        }
        
        mock_api_indicators.return_value = (pd.DataFrame(), {})
        mock_web_scraping.return_value = (mock_df, mock_metadata)
        mock_public_files.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert not df.empty
        assert metadata["strategy_used"] == "web_scraping"
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_called_once()
        mock_public_files.assert_not_called()
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    @patch('src.extraction.idescat.IDESCATExtractor._try_public_files')
    def test_get_renta_by_barrio_all_strategies_fail(
        self,
        mock_public_files,
        mock_web_scraping,
        mock_api_indicators,
        extractor
    ):
        """Verifica el manejo cuando todas las estrategias fallan."""
        mock_api_indicators.return_value = (pd.DataFrame(), {})
        mock_web_scraping.return_value = (pd.DataFrame(), {})
        mock_public_files.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert df.empty
        assert metadata["success"] is False
        assert "error" in metadata
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_called_once()
        mock_public_files.assert_called_once()
    
    def test_try_api_indicators_success(self, extractor):
        """Verifica el acceso exitoso a la API de indicadores."""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "nodes": []
            }
        }
        
        # Mock de la sesión HTTP
        extractor.session = Mock()
        extractor.session.get.return_value = mock_response
        
        # Mock de _validate_response
        with patch.object(extractor, '_validate_response', return_value=True):
            df, metadata = extractor._try_api_indicators(2020, 2020)
            
            assert metadata["strategy"] == "api_indicators"
            extractor.session.get.assert_called_once()
    
    def test_try_api_indicators_failure(self, extractor):
        """Verifica el manejo de errores en la API de indicadores."""
        # Mock de respuesta con error
        mock_response = Mock()
        mock_response.status_code = 500
        extractor.session = Mock()
        extractor.session.get.return_value = mock_response
        
        with patch.object(extractor, '_validate_response', return_value=False):
            df, metadata = extractor._try_api_indicators(2020, 2020)
            
            assert df.empty
            assert metadata["strategy"] == "api_indicators"
            assert metadata["success"] is False
    
    def test_try_web_scraping_not_implemented(self, extractor):
        """Verifica que web scraping retorna DataFrame vacío (aún no implementado)."""
        df, metadata = extractor._try_web_scraping(2020, 2020)
        
        assert df.empty
        assert metadata["strategy"] == "web_scraping"
        assert metadata["success"] is False
        assert "note" in metadata
    
    def test_try_public_files_not_implemented(self, extractor):
        """Verifica que public files retorna DataFrame vacío (aún no implementado)."""
        df, metadata = extractor._try_public_files(2020, 2020)
        
        assert df.empty
        assert metadata["strategy"] == "public_files"
        assert "note" in metadata

