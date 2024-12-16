import pytest
from plugins.http_download import HTTPDownload
from unittest.mock import patch, MagicMock
import os
from tempfile import TemporaryDirectory

def test_get_rio_env_with_headers():
    """Test get_rio_env when headers are provided"""
    headers = {
        'Authorization': 'Bearer token123',
        'Accept': 'application/json'
    }
    
    plugin = HTTPDownload(headers=headers)
    env = plugin.get_rio_env()
    
    assert 'GDAL_HTTP_HEADERS' in env
    expected_headers = "Authorization: Bearer token123\r\nAccept: application/json"
    assert env['GDAL_HTTP_HEADERS'] == expected_headers

def test_get_rio_env_without_headers():
    """Test get_rio_env when no headers are provided"""
    plugin = HTTPDownload(headers=None)
    env = plugin.get_rio_env()
    
    assert env == {}

def test_get_rio_env_empty_headers():
    """Test get_rio_env when headers dict is empty"""
    plugin = HTTPDownload(headers={})
    env = plugin.get_rio_env()
    
    assert env == {} 

def test_discover_product_types_with_external_success():
    """Test product type discovery when external JSON fetch succeeds"""
    mock_types = {"provider1": {"type1": {}, "type2": {}}}
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_types
        mock_get.return_value = mock_response
        
        plugin = HTTPDownload(provider_name="provider1")
        types = plugin.discover_product_types()
        
        assert types == mock_types["provider1"]
        # Verify we didn't proceed with actual discovery
        assert not hasattr(plugin, '_discover_from_provider')

def test_discover_product_types_with_external_failure():
    """Test product type discovery falls back when external fetch fails"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")
        
        plugin = HTTPDownload(provider_name="provider1")
        result = plugin.discover_product_types()
        
        assert result is None  # Verify we skip discovery on external fetch failure

def test_fetch_external_product_types():
    """Test external product types fetch functionality"""
    mock_types = {"provider1": {"type1": {}, "type2": {}}}
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_types
        mock_get.return_value = mock_response
        
        plugin = HTTPDownload(provider_name="provider1")
        types = plugin._fetch_external_product_types()
        
        assert types == mock_types["provider1"]

def test_download_uses_product_filename_extension():
    """Test that download uses extension from _check_product_filename"""
    product = MagicMock()
    product.properties = {
        "title": "test_product.tiff",
        "downloadLink": "http://example.com/data.tiff"
    }
    
    plugin = HTTPDownload()
    
    # Mock the HTTP response
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {'content-disposition': 'filename=data.tiff'}
        mock_get.return_value = mock_response
        
        # Call download with a test directory
        with TemporaryDirectory() as tmp_dir:
            plugin.download(product, output_dir=tmp_dir)
            
            # Verify the downloaded file has .tiff extension
            downloaded_files = os.listdir(tmp_dir)
            assert len(downloaded_files) == 1
            assert downloaded_files[0].endswith('.tiff')
            assert not downloaded_files[0].endswith('.zip')

def test_download_handles_missing_extension():
    """Test download behavior when filename has no extension"""
    product = MagicMock()
    product.properties = {
        "title": "test_product",  # No extension
        "downloadLink": "http://example.com/data"
    }
    
    plugin = HTTPDownload()
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {'content-disposition': 'filename=data'}
        mock_get.return_value = mock_response
        
        with TemporaryDirectory() as tmp_dir:
            # Should handle missing extension without adding .zip
            plugin.download(product, output_dir=tmp_dir)
            
            downloaded_files = os.listdir(tmp_dir)
            assert len(downloaded_files) == 1
            assert not downloaded_files[0].endswith('.zip')
            assert downloaded_files[0] == 'test_product'  # Original name preserved