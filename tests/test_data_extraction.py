"""
Tests for data extraction module
"""
import pytest
import pandas as pd
import json
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from src.data_extraction import OpenDataBCNExtractor, IdealistaExtractor

# --- Fixtures ---

@pytest.fixture
def mock_response():
    """Helper to create a mock response object."""
    def _create_response(status_code=200, json_data=None, content=b"", text=""):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        if json_data is not None:
            mock_resp.json.return_value = json_data
        mock_resp.content = content
        mock_resp.text = text
        return mock_resp
    return _create_response

@pytest.fixture
def opendata_extractor():
    with patch('src.data_extraction.requests.Session') as mock_session_cls:
        extractor = OpenDataBCNExtractor(output_dir=Path("/tmp"))
        # We need to mock the session instance created inside __init__
        extractor.session = MagicMock()
        yield extractor

@pytest.fixture
def idealista_extractor():
    with patch('src.data_extraction.requests.Session') as mock_session_cls:
        # Mock env vars if needed, or pass them in constructor
        extractor = IdealistaExtractor(
            api_key="fake_key", 
            api_secret="fake_secret", 
            output_dir=Path("/tmp")
        )
        extractor.session = MagicMock()
        yield extractor

# --- OpenDataBCNExtractor Tests ---

def test_opendata_get_dataset_list_success(opendata_extractor, mock_response):
    """Test successful retrieval of dataset list."""
    expected_result = ["dataset1", "dataset2"]
    mock_resp = mock_response(json_data={"success": True, "result": expected_result})
    opendata_extractor.session.get.return_value = mock_resp

    result = opendata_extractor.get_dataset_list()
    
    assert result == expected_result
    opendata_extractor.session.get.assert_called_once()
    assert "package_list" in opendata_extractor.session.get.call_args[0][0]

def test_opendata_get_dataset_list_failure(opendata_extractor, mock_response):
    """Test failure when retrieving dataset list."""
    mock_resp = mock_response(status_code=500)
    opendata_extractor.session.get.return_value = mock_resp

    result = opendata_extractor.get_dataset_list()
    
    assert result == []

def test_opendata_get_dataset_info_success(opendata_extractor, mock_response):
    """Test successful retrieval of dataset info."""
    dataset_id = "test-dataset"
    expected_info = {"id": dataset_id, "title": "Test Dataset"}
    mock_resp = mock_response(json_data={"success": True, "result": expected_info})
    opendata_extractor.session.get.return_value = mock_resp

    result = opendata_extractor.get_dataset_info(dataset_id)
    
    assert result == expected_info
    opendata_extractor.session.get.assert_called_once()
    assert "package_show" in opendata_extractor.session.get.call_args[0][0]

def test_opendata_get_dataset_info_failure(opendata_extractor, mock_response):
    """Test failure when retrieving dataset info."""
    mock_resp = mock_response(status_code=404)
    opendata_extractor.session.get.return_value = mock_resp

    result = opendata_extractor.get_dataset_info("non-existent")
    
    assert result is None

def test_opendata_download_dataset_success_csv(opendata_extractor, mock_response):
    """Test successful download of a CSV dataset."""
    dataset_id = "test-csv"
    csv_content = "col1,col2\nval1,val2"
    
    # Mock get_dataset_info response
    info_resp = mock_response(json_data={
        "success": True, 
        "result": {
            "resources": [{"format": "CSV", "url": "http://example.com/data.csv"}]
        }
    })
    
    # Mock download response
    download_resp = mock_response(text=csv_content)
    
    # Configure side_effect for sequential calls
    opendata_extractor.session.get.side_effect = [info_resp, download_resp]

    # Patch _save_raw_data to avoid file system operations
    with patch.object(opendata_extractor, '_save_raw_data') as mock_save:
        df, metadata = opendata_extractor.download_dataset(dataset_id)
        
        assert df is not None
        assert not df.empty
        assert list(df.columns) == ["col1", "col2"]
        assert metadata["success"] is True
        mock_save.assert_called_once()

def test_opendata_download_dataset_no_resources(opendata_extractor, mock_response):
    """Test download failure when no resources are found."""
    dataset_id = "empty-dataset"
    
    # Mock get_dataset_info response with no resources
    info_resp = mock_response(json_data={
        "success": True, 
        "result": {"resources": []}
    })
    opendata_extractor.session.get.return_value = info_resp

    df, metadata = opendata_extractor.download_dataset(dataset_id)
    
    assert df is None
    assert metadata["success"] is False
    assert metadata["error"] == "No se encontraron recursos"

def test_opendata_get_dataset_resources_ckan_success(opendata_extractor, mock_response):
    """Test successful retrieval of CKAN resources."""
    dataset_id = "test-resources"
    resources_data = {
        "success": True,
        "result": {
            "resources": [
                {"format": "CSV", "name": "2023 Data", "url": "http://ex.com/2023.csv"},
                {"format": "JSON", "name": "Metadata", "url": "http://ex.com/meta.json"}, # Should be ignored
                {"format": "CSV", "name": "Other Data", "url": "http://ex.com/other.csv"}
            ]
        }
    }
    mock_resp = mock_response(json_data=resources_data)
    opendata_extractor.session.get.return_value = mock_resp

    resources = opendata_extractor.get_dataset_resources_ckan(dataset_id)
    
    assert len(resources) == 2
    assert 2023 in resources # Extracted from name "2023 Data"
    assert "Other Data" in resources

def test_opendata_get_dataset_resources_ckan_404(opendata_extractor, mock_response):
    """Test retrieval of CKAN resources when dataset is not found."""
    mock_resp = mock_response(status_code=404)
    opendata_extractor.session.get.return_value = mock_resp

    resources = opendata_extractor.get_dataset_resources_ckan("missing")
    
    assert resources == {}

# --- IdealistaExtractor Tests ---

def test_idealista_get_access_token_success(idealista_extractor, mock_response):
    """Test successful OAuth token retrieval."""
    token_data = {"access_token": "fake_token", "expires_in": 3600}
    mock_resp = mock_response(json_data=token_data)
    idealista_extractor.session.post.return_value = mock_resp

    token = idealista_extractor._get_access_token()
    
    assert token == "fake_token"
    assert idealista_extractor.access_token == "fake_token"
    idealista_extractor.session.post.assert_called_once()

def test_idealista_get_access_token_failure(idealista_extractor, mock_response):
    """Test failure in OAuth token retrieval."""
    mock_resp = mock_response(status_code=401, text="Unauthorized")
    idealista_extractor.session.post.return_value = mock_resp

    token = idealista_extractor._get_access_token()
    
    assert token is None

def test_idealista_search_properties_success(idealista_extractor, mock_response):
    """Test successful property search."""
    # Mock token retrieval
    with patch.object(idealista_extractor, '_get_access_token', return_value="valid_token"):
        search_data = {
            "elementList": [
                {"propertyCode": "1", "price": 100000, "size": 80},
                {"propertyCode": "2", "price": 200000, "size": 100}
            ],
            "pagination": {"total": 2, "totalPages": 1}
        }
        mock_resp = mock_response(json_data=search_data)
        idealista_extractor.session.post.return_value = mock_resp

        df, metadata = idealista_extractor.search_properties(operation="sale")
        
        assert df is not None
        assert len(df) == 2
        assert metadata["success"] is True
        assert metadata["num_results"] == 2

def test_idealista_search_properties_no_token(idealista_extractor):
    """Test search failure when token cannot be obtained."""
    with patch.object(idealista_extractor, '_get_access_token', return_value=None):
        df, metadata = idealista_extractor.search_properties()
        
        assert df is None
        assert metadata["success"] is False
        assert "token" in metadata["error"]

def test_idealista_search_properties_empty(idealista_extractor, mock_response):
    """Test search with no results."""
    with patch.object(idealista_extractor, '_get_access_token', return_value="valid_token"):
        search_data = {
            "elementList": [],
            "pagination": {"total": 0}
        }
        mock_resp = mock_response(json_data=search_data)
        idealista_extractor.session.post.return_value = mock_resp

        df, metadata = idealista_extractor.search_properties()
        
        assert df is not None
        assert df.empty
        assert metadata["success"] is True
        assert metadata["num_results"] == 0

def test_idealista_extract_offer_by_barrio(idealista_extractor, mock_response):
    """Test extracting offer by barrio (high level method)."""
    # Mock search_properties to return a small DF
    mock_df = pd.DataFrame({
        'propertyCode': ['1'],
        'price': [100000],
        'size': [50],
        'propertyType': ['flat']
    })
    mock_metadata = {"success": True}
    
    with patch.object(idealista_extractor, 'search_properties', return_value=(mock_df, mock_metadata)):
        with patch.object(idealista_extractor, '_save_raw_data', return_value=Path("/tmp/file.csv")):
            
            df, metadata = idealista_extractor.extract_offer_by_barrio(
                barrio_names=["Eixample"],
                operation="sale"
            )
            
            assert df is not None
            assert not df.empty
            assert 'precio_m2' in df.columns # Check if processing happened
            assert metadata["success"] is True
            assert metadata["barrios_processed"] == 1

def test_idealista_process_idealista_data(idealista_extractor):
    """Test data processing logic for Idealista data."""
    raw_data = pd.DataFrame({
        'propertyCode': ['1', '2'],
        'price': [100000, 200000],
        'size': [50, 0], # 0 size to test division by zero handling
        'propertyType': ['flat', 'house'],
        'unknown_col': ['a', 'b']
    })
    
    processed = idealista_extractor._process_idealista_data(raw_data, operation="sale")
    
    assert processed is not None
    assert len(processed) == 2
    assert 'precio_m2' in processed.columns
    assert processed.iloc[0]['precio_m2'] == 2000.0
    assert pd.isna(processed.iloc[1]['precio_m2']) # Should be NA due to size 0
    assert 'tipologia' in processed.columns
    assert processed.iloc[0]['tipologia'] == 'piso'
