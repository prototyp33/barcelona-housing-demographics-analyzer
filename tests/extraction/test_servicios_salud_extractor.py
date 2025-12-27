"""
Tests unitarios para ServiciosSaludExtractor.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.extraction.servicios_salud_extractor import (
    BARCELONA_LAT_MAX,
    BARCELONA_LAT_MIN,
    BARCELONA_LON_MAX,
    BARCELONA_LON_MIN,
    ServiciosSaludExtractor,
)


@pytest.fixture
def extractor(tmp_path, mock_opendata_extractor):
    """Fixture para crear un extractor de servicios sanitarios."""
    extractor = ServiciosSaludExtractor(output_dir=tmp_path)
    # Reemplazar el opendata_extractor con el mock
    extractor.opendata_extractor = mock_opendata_extractor
    return extractor


@pytest.fixture
def mock_opendata_extractor():
    """Fixture para mockear OpenDataBCNExtractor."""
    with patch("src.extraction.servicios_salud_extractor.OpenDataBCNExtractor") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_centros_salud_df():
    """DataFrame de ejemplo con centros de salud."""
    return pd.DataFrame({
        "nombre": ["Centro de Salud A", "Hospital B", "Centro de Salud C"],
        "latitud": [41.38, 41.40, 41.39],
        "longitud": [2.15, 2.17, 2.16],
        "tipo": ["Centro de Salud", "Hospital", "Centro de Salud"],
    })


@pytest.fixture
def sample_farmacias_df():
    """DataFrame de ejemplo con farmacias."""
    return pd.DataFrame({
        "nombre": ["Farmacia A", "Farmacia B", "Farmacia C"],
        "latitud": [41.38, 41.40, 41.39],
        "longitud": [2.15, 2.17, 2.16],
        "tipo": ["Farmacia", "Farmacia", "Farmacia"],
    })


class TestServiciosSaludExtractor:
    """Tests para ServiciosSaludExtractor."""
    
    def test_init(self, tmp_path):
        """Test de inicialización."""
        extractor = ServiciosSaludExtractor(output_dir=tmp_path)
        assert extractor.output_dir == tmp_path
        assert hasattr(extractor, "opendata_extractor")
    
    def test_extract_centros_salud_hospitales_success(
        self, extractor, mock_opendata_extractor, sample_centros_salud_df
    ):
        """Test de extracción exitosa de centros de salud."""
        # Mock de búsqueda de datasets
        extractor.opendata_extractor.search_datasets_by_keyword.return_value = [
            "equipament-sanitat"
        ]
        
        # Mock de descarga de dataset
        extractor.opendata_extractor.download_dataset.return_value = (
            sample_centros_salud_df,
            {"success": True}
        )
        
        # Mock de get_dataset_info para validación
        extractor.opendata_extractor.get_dataset_info.return_value = {
            "title": "Equipaments Sanitaris",
            "notes": "Centros de salud y hospitales",
            "tags": [{"name": "sanitat"}]
        }
        
        df, metadata = extractor.extract_centros_salud_hospitales()
        
        assert df is not None
        assert len(df) == 3
        assert metadata["success"] is True
        assert metadata["centros_with_valid_coords"] == 3
    
    def test_extract_centros_salud_hospitales_no_datasets(
        self, extractor, mock_opendata_extractor
    ):
        """Test cuando no se encuentran datasets."""
        extractor.opendata_extractor = mock_opendata_extractor
        mock_opendata_extractor.search_datasets_by_keyword.return_value = []
        mock_opendata_extractor.download_dataset.return_value = (None, {})
        
        df, metadata = extractor.extract_centros_salud_hospitales()
        
        assert df is None
        assert metadata["success"] is False
        assert "error" in metadata
    
    def test_extract_farmacias_success(
        self, extractor, mock_opendata_extractor, sample_farmacias_df
    ):
        """Test de extracción exitosa de farmacias."""
        extractor.opendata_extractor = mock_opendata_extractor
        
        # Mock de búsqueda de datasets
        mock_opendata_extractor.search_datasets_by_keyword.return_value = [
            "sanitat-farmacies"
        ]
        
        # Mock de descarga de dataset
        mock_opendata_extractor.download_dataset.return_value = (
            sample_farmacias_df,
            {"success": True}
        )
        
        # Mock de get_dataset_info para validación
        mock_opendata_extractor.get_dataset_info.return_value = {
            "title": "Farmacies",
            "notes": "Farmacias de Barcelona",
            "tags": [{"name": "farmacia"}]
        }
        
        df, metadata = extractor.extract_farmacias()
        
        assert df is not None
        assert len(df) == 3
        assert metadata["success"] is True
        assert metadata["farmacias_with_valid_coords"] == 3
    
    def test_extract_farmacias_no_datasets(
        self, extractor, mock_opendata_extractor
    ):
        """Test cuando no se encuentran datasets de farmacias."""
        extractor.opendata_extractor = mock_opendata_extractor
        mock_opendata_extractor.search_datasets_by_keyword.return_value = []
        mock_opendata_extractor.download_dataset.return_value = (None, {})
        
        df, metadata = extractor.extract_farmacias()
        
        assert df is None
        assert metadata["success"] is False
        assert "error" in metadata
    
    def test_extract_all_combines_sources(
        self, extractor, mock_opendata_extractor,
        sample_centros_salud_df, sample_farmacias_df
    ):
        """Test de extract_all combinando centros y farmacias."""
        extractor.opendata_extractor = mock_opendata_extractor
        
        # Mock de búsqueda (diferentes respuestas según método)
        def search_side_effect(keyword, **kwargs):
            if keyword in ["sanitat", "salut", "hospital", "centro salud"]:
                return ["equipament-sanitat"]
            elif keyword in ["farmacia", "farmacie", "pharmacy"]:
                return ["sanitat-farmacies"]
            return []
        
        mock_opendata_extractor.search_datasets_by_keyword.side_effect = search_side_effect
        
        # Mock de descarga (diferentes respuestas según dataset)
        def download_side_effect(dataset_id, **kwargs):
            if "equipament-sanitat" in dataset_id:
                return sample_centros_salud_df, {"success": True}
            elif "farmacies" in dataset_id:
                return sample_farmacias_df, {"success": True}
            return None, {}
        
        mock_opendata_extractor.download_dataset.side_effect = download_side_effect
        
        # Mock de get_dataset_info
        def get_info_side_effect(dataset_id):
            if "equipament-sanitat" in dataset_id:
                return {
                    "title": "Equipaments Sanitaris",
                    "notes": "Centros de salud",
                    "tags": [{"name": "sanitat"}]
                }
            elif "farmacies" in dataset_id:
                return {
                    "title": "Farmacies",
                    "notes": "Farmacias",
                    "tags": [{"name": "farmacia"}]
                }
            return {}
        
        mock_opendata_extractor.get_dataset_info.side_effect = get_info_side_effect
        
        df, metadata = extractor.extract_all()
        
        assert df is not None
        assert len(df) == 6  # 3 centros + 3 farmacias
        assert "tipo_servicio" in df.columns
        assert metadata["has_centros"] is True
        assert metadata["has_farmacias"] is True
    
    def test_validate_coordinates_valid(self, extractor):
        """Test de validación de coordenadas válidas."""
        df = pd.DataFrame({
            "latitud": [41.38, 41.40, 41.39],
            "longitud": [2.15, 2.17, 2.16],
        })
        
        df_valid = extractor._validate_coordinates(df)
        
        assert len(df_valid) == 3
        assert all(df_valid["latitud"].between(BARCELONA_LAT_MIN, BARCELONA_LAT_MAX))
        assert all(df_valid["longitud"].between(BARCELONA_LON_MIN, BARCELONA_LON_MAX))
    
    def test_validate_coordinates_out_of_range(self, extractor):
        """Test de validación de coordenadas fuera de rango."""
        df = pd.DataFrame({
            "latitud": [41.50, 41.38, 50.0],  # Dos fuera de rango
            "longitud": [2.15, 2.17, 2.16],
        })
        
        df_valid = extractor._validate_coordinates(df)
        
        # Solo la segunda fila (41.38, 2.17) está dentro del rango
        assert len(df_valid) == 1
    
    def test_validate_coordinates_missing(self, extractor):
        """Test de validación con coordenadas faltantes."""
        df = pd.DataFrame({
            "latitud": [41.38, None, 41.39],
            "longitud": [2.15, 2.17, None],
        })
        
        df_valid = extractor._validate_coordinates(df)
        
        assert len(df_valid) == 1  # Solo la primera tiene ambas coordenadas
    
    def test_validate_coordinates_no_coord_columns(self, extractor):
        """Test cuando no hay columnas de coordenadas."""
        df = pd.DataFrame({
            "nombre": ["A", "B", "C"],
            "tipo": ["Centro", "Hospital", "Centro"],
        })
        
        df_valid = extractor._validate_coordinates(df)
        
        # Debe retornar el mismo DataFrame sin cambios
        assert len(df_valid) == len(df)
    
    def test_normalize_centros_salud_columns(self, extractor):
        """Test de normalización de columnas de centros de salud."""
        df = pd.DataFrame({
            "nom": ["Centro A"],
            "lat": [41.38],
            "lon": [2.15],
        })
        
        df_normalized = extractor._normalize_centros_salud_columns(df)
        
        assert "nombre" in df_normalized.columns
        assert "latitud" in df_normalized.columns
        assert "longitud" in df_normalized.columns
    
    def test_normalize_farmacias_columns(self, extractor):
        """Test de normalización de columnas de farmacias."""
        df = pd.DataFrame({
            "nom": ["Farmacia A"],
            "lat": [41.38],
            "lon": [2.15],
        })
        
        df_normalized = extractor._normalize_farmacias_columns(df)
        
        assert "nombre" in df_normalized.columns
        assert "latitud" in df_normalized.columns
        assert "longitud" in df_normalized.columns
    
    def test_is_centros_salud_dataset_valid(self, extractor):
        """Test de validación de dataset de centros de salud."""
        df = pd.DataFrame({
            "nombre": ["Centro de Salud"],
            "tipo": ["Centro de Salud"],
        })
        
        assert extractor._is_centros_salud_dataset(df, "equipament-sanitat") is True
    
    def test_is_centros_salud_dataset_invalid(self, extractor):
        """Test de validación de dataset que no es de centros de salud."""
        df = pd.DataFrame({
            "nombre": ["Farmacia"],
            "tipo": ["Farmacia"],
        })
        
        assert extractor._is_centros_salud_dataset(df, "farmacies") is False
    
    def test_is_farmacias_dataset_valid(self, extractor):
        """Test de validación de dataset de farmacias."""
        df = pd.DataFrame({
            "nombre": ["Farmacia A"],
            "tipo": ["Farmacia"],
        })
        
        assert extractor._is_farmacias_dataset(df, "sanitat-farmacies") is True
    
    def test_is_farmacias_dataset_invalid(self, extractor):
        """Test de validación de dataset que no es de farmacias."""
        df = pd.DataFrame({
            "nombre": ["Centro de Salud"],
            "tipo": ["Centro de Salud"],
        })
        
        assert extractor._is_farmacias_dataset(df, "equipament-sanitat") is False
    
    def test_extract_centros_salud_filters_farmacias(
        self, extractor
    ):
        """Test que filtra farmacias de centros de salud."""
        df_mixed = pd.DataFrame({
            "nombre": ["Centro A", "Farmacia B", "Hospital C"],
            "latitud": [41.38, 41.39, 41.40],
            "longitud": [2.15, 2.16, 2.17],
            "tipo": ["Centro de Salud", "Farmacia", "Hospital"],
        })
        
        extractor.opendata_extractor.search_datasets_by_keyword.return_value = [
            "equipament-sanitat"
        ]
        extractor.opendata_extractor.download_dataset.return_value = (df_mixed, {})
        extractor.opendata_extractor.get_dataset_info.return_value = {
            "title": "Equipaments",
            "notes": "Centros y farmacias",
            "tags": [{"name": "sanitat"}]
        }
        
        df, metadata = extractor.extract_centros_salud_hospitales()
        
        assert df is not None
        # Debe filtrar la farmacia
        assert len(df) == 2  # Solo Centro A y Hospital C
        assert "Farmacia B" not in df["nombre"].values
    
    def test_extract_farmacias_filters_centros(
        self, extractor, mock_opendata_extractor
    ):
        """Test que filtra centros de salud de farmacias."""
        extractor.opendata_extractor = mock_opendata_extractor
        
        df_mixed = pd.DataFrame({
            "nombre": ["Centro A", "Farmacia B", "Farmacia C"],
            "latitud": [41.38, 41.39, 41.40],
            "longitud": [2.15, 2.16, 2.17],
            "tipo": ["Centro de Salud", "Farmacia", "Farmacia"],
        })
        
        mock_opendata_extractor.search_datasets_by_keyword.return_value = [
            "sanitat-farmacies"
        ]
        mock_opendata_extractor.download_dataset.return_value = (df_mixed, {})
        mock_opendata_extractor.get_dataset_info.return_value = {
            "title": "Farmacies",
            "notes": "Farmacias",
            "tags": [{"name": "farmacia"}]
        }
        
        df, metadata = extractor.extract_farmacias()
        
        assert df is not None
        # Debe filtrar el centro de salud
        assert len(df) == 2  # Solo Farmacia B y Farmacia C
        assert "Centro A" not in df["nombre"].values

