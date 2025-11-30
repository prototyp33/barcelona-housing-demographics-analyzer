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
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_opendata_bcn')
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    def test_get_renta_by_barrio_opendata_success(
        self,
        mock_web_scraping,
        mock_api_indicators,
        mock_opendata_bcn,
        extractor
    ):
        """Verifica que get_renta_by_barrio usa Open Data BCN cuando está disponible."""
        # Mock de datos exitosos desde Open Data BCN
        mock_df = pd.DataFrame({
            "Codi_Barri": [1, 2],
            "Nom_Barri": ["Barrio 1", "Barrio 2"],
            "anio": [2020, 2020],
            "renta_media": [25000, 30000]
        })
        mock_metadata = {
            "strategy": "opendata_bcn",
            "success": True,
            "years_extracted": [2020]
        }
        
        mock_opendata_bcn.return_value = (mock_df, mock_metadata)
        mock_api_indicators.return_value = (pd.DataFrame(), {})
        mock_web_scraping.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert not df.empty
        assert len(df) == 2
        assert metadata["strategy_used"] == "opendata_bcn"
        assert metadata["success"] is True
        mock_opendata_bcn.assert_called_once()
        mock_api_indicators.assert_not_called()
        mock_web_scraping.assert_not_called()
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_opendata_bcn')
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    def test_get_renta_by_barrio_api_fallback(
        self,
        mock_web_scraping,
        mock_api_indicators,
        mock_opendata_bcn,
        extractor
    ):
        """Verifica que get_renta_by_barrio hace fallback a API cuando Open Data BCN falla."""
        # Mock de datos exitosos desde API (fallback)
        mock_df = pd.DataFrame({
            "territorio": ["Cataluña"],
            "anio": [2020],
            "renta_media_neta_persona": [25000]
        })
        mock_metadata = {
            "strategy": "api_indicators",
            "success": True
        }
        
        mock_opendata_bcn.return_value = (pd.DataFrame(), {})
        mock_api_indicators.return_value = (mock_df, mock_metadata)
        mock_web_scraping.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert not df.empty
        assert metadata["strategy_used"] == "api_indicators"
        mock_opendata_bcn.assert_called_once()
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_not_called()
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_opendata_bcn')
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    def test_get_renta_by_barrio_fallback_to_web(
        self,
        mock_web_scraping,
        mock_api_indicators,
        mock_opendata_bcn,
        extractor
    ):
        """Verifica que se hace fallback a web scraping si las otras estrategias fallan."""
        mock_df = pd.DataFrame({
            "barrio_id": [1],
            "anio": [2020],
            "renta_media": [25000]
        })
        mock_metadata = {
            "strategy": "web_scraping",
            "success": True
        }
        
        mock_opendata_bcn.return_value = (pd.DataFrame(), {})
        mock_api_indicators.return_value = (pd.DataFrame(), {})
        mock_web_scraping.return_value = (mock_df, mock_metadata)
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert not df.empty
        assert metadata["strategy_used"] == "web_scraping"
        mock_opendata_bcn.assert_called_once()
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_called_once()
    
    @patch('src.extraction.idescat.IDESCATExtractor._try_opendata_bcn')
    @patch('src.extraction.idescat.IDESCATExtractor._try_api_indicators')
    @patch('src.extraction.idescat.IDESCATExtractor._try_web_scraping')
    def test_get_renta_by_barrio_all_strategies_fail(
        self,
        mock_web_scraping,
        mock_api_indicators,
        mock_opendata_bcn,
        extractor
    ):
        """Verifica el manejo cuando todas las estrategias fallan."""
        mock_opendata_bcn.return_value = (pd.DataFrame(), {})
        mock_api_indicators.return_value = (pd.DataFrame(), {})
        mock_web_scraping.return_value = (pd.DataFrame(), {})
        
        df, metadata = extractor.get_renta_by_barrio(2020, 2020)
        
        assert df.empty
        assert metadata["success"] is False
        assert "error" in metadata
        mock_opendata_bcn.assert_called_once()
        mock_api_indicators.assert_called_once()
        mock_web_scraping.assert_called_once()
    
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
    
    def test_try_opendata_bcn_not_available(self, extractor):
        """Verifica que opendata_bcn maneja correctamente cuando no hay datos disponibles."""
        # Mock para simular que Open Data BCN no tiene datos
        # OpenDataBCNExtractor se importa dentro del método, así que mockeamos el módulo
        with patch('src.extraction.opendata.OpenDataBCNExtractor') as mock_bcn_class:
            mock_extractor = Mock()
            mock_extractor.download_dataset.return_value = (pd.DataFrame(), {})
            mock_bcn_class.return_value = mock_extractor
            
            df, metadata = extractor._try_opendata_bcn(2020, 2020)
            
            assert df.empty
            assert metadata["strategy"] == "opendata_bcn"
            assert metadata["success"] is False

