import pytest
from plugins.http_download import HTTPDownload

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