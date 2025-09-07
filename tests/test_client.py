"""
Tests for UniFi Controller Client authentication and API communication.

Following FastMCP testing patterns with comprehensive authentication flow testing.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
import json
from inline_snapshot import snapshot

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.config import UniFiConfig


class TestUnifiControllerClientAuthentication:
    """Test authentication flows for both UDM Pro and legacy controllers."""
    
    async def test_udm_pro_authentication_success(self, test_unifi_config, mock_http_responses):
        """Test successful authentication with UDM Pro controller."""
        client = UnifiControllerClient(test_unifi_config)
        
        # Mock successful login response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value={}),
                cookies=httpx.Cookies({"TOKEN": "test-token"}),
                headers={"x-csrf-token": "test-csrf"}
            )
            
            await client.connect()
            result = await client.authenticate()
            
            assert result is True
            assert client.is_authenticated is True
            assert client.csrf_token == "test-csrf"
            
            # Verify correct API endpoint was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/api/auth/login" in call_args[0][0]
            assert call_args[1]["json"]["username"] == "admin"
            assert call_args[1]["json"]["password"] == "password123"


    async def test_legacy_controller_authentication_success(self, test_legacy_unifi_config, mock_http_responses):
        """Test successful authentication with legacy controller."""
        client = UnifiControllerClient(test_legacy_unifi_config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value={"data": [], "meta": {"rc": "ok"}}),
                cookies=httpx.Cookies({"unifises": "test-session"}),
                headers={}
            )
            
            await client.connect()
            result = await client.authenticate()
            
            assert result is True
            assert client.is_authenticated is True
            
            # Verify correct API endpoint was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/api/login" in call_args[0][0]
            
            # Legacy uses form data
            assert "username" in call_args[1]["data"]
            assert "password" in call_args[1]["data"]


    async def test_authentication_failure_invalid_credentials(self, test_unifi_config):
        """Test authentication failure with invalid credentials."""
        client = UnifiControllerClient(test_unifi_config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=401,
                json=Mock(return_value={"error": "Invalid credentials"}),
                cookies=httpx.Cookies({}),
                headers={}
            )
            
            await client.connect()
            result = await client.authenticate()
            
            assert result is False
            assert client.is_authenticated is False
            assert client.csrf_token is None


    async def test_authentication_network_error(self, test_unifi_config):
        """Test authentication failure due to network error."""
        client = UnifiControllerClient(test_unifi_config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            await client.connect()
            result = await client.authenticate()
            
            assert result is False
            assert client.is_authenticated is False


    async def test_session_initialization_and_cleanup(self, test_unifi_config):
        """Test session lifecycle management."""
        client = UnifiControllerClient(test_unifi_config)
        
        # Initially no session
        assert client.session is None
        assert client.is_authenticated is False
        
        with patch('httpx.AsyncClient') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            with patch.object(client, 'authenticate', return_value=True):
                await client.connect()
                
                # Session should be initialized
                assert client.session is not None
                mock_session_class.assert_called_once_with(
                    verify=test_unifi_config.verify_ssl,
                    timeout=30.0
                )
                
                await client.disconnect()
                
                # Session should be cleaned up
                mock_session.aclose.assert_called_once()
                assert client.session is None
                assert client.is_authenticated is False
                assert client.csrf_token is None


class TestUnifiControllerClientAPIRequests:
    """Test API request methods and error handling."""
    
    async def test_api_base_path_udm_pro(self, test_unifi_config):
        """Test API base path configuration for UDM Pro."""
        client = UnifiControllerClient(test_unifi_config)
        assert client.api_base == "/proxy/network/api"
    
    
    async def test_api_base_path_legacy(self, test_legacy_unifi_config):
        """Test API base path configuration for legacy controller."""
        client = UnifiControllerClient(test_legacy_unifi_config)
        assert client.api_base == "/api"


    async def test_get_devices_success(self, mock_unifi_client, mock_device_data):
        """Test successful device retrieval."""
        result = await mock_unifi_client.get_devices()
        
        assert result == mock_device_data
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Main Switch"
        assert result[1]["name"] == "Living Room AP"


    async def test_get_clients_success(self, mock_unifi_client, mock_client_data):
        """Test successful client retrieval."""
        result = await mock_unifi_client.get_clients()
        
        assert result == mock_client_data
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "John's iPhone"
        assert result[1]["name"] == "Desktop PC"


    async def test_get_networks_success(self, mock_unifi_client, mock_network_data):
        """Test successful network configuration retrieval."""
        result = await mock_unifi_client.get_networks()
        
        assert result == mock_network_data
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "LAN"
        assert result[1]["name"] == "Guest"


    async def test_device_management_operations(self, mock_unifi_client):
        """Test device management operations."""
        device_mac = "aa:bb:cc:dd:ee:01"
        
        # Test restart device
        result = await mock_unifi_client.restart_device(device_mac)
        assert result["message"] == "Device restart initiated"
        
        # Test locate device
        result = await mock_unifi_client.locate_device(device_mac)
        assert result["message"] == "Device locate started"


    async def test_client_management_operations(self, mock_unifi_client):
        """Test client management operations."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        # Test block client
        result = await mock_unifi_client.block_client(client_mac)
        assert result["message"] == "Client blocked"
        
        # Test unblock client
        result = await mock_unifi_client.unblock_client(client_mac)
        assert result["message"] == "Client unblocked"
        
        # Test set client name
        result = await mock_unifi_client.set_client_name(client_mac, "New Name")
        assert result["message"] == "Name updated"
        
        # Test set client note
        result = await mock_unifi_client.set_client_note(client_mac, "Test note")
        assert result["message"] == "Note updated"


class TestUnifiControllerClientErrorHandling:
    """Test error handling scenarios."""
    
    async def test_unauthenticated_requests(self, mock_failed_unifi_client):
        """Test that unauthenticated requests return error responses."""
        result = await mock_failed_unifi_client.get_devices()
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Authentication required"


    async def test_context_manager_usage(self, test_unifi_config):
        """Test using client as async context manager."""
        client = UnifiControllerClient(test_unifi_config)
        
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                async with client:
                    mock_connect.assert_called_once()
                
                mock_disconnect.assert_called_once()


    async def test_ensure_authenticated_method(self, test_unifi_config):
        """Test ensure_authenticated method behavior."""
        client = UnifiControllerClient(test_unifi_config)
        
        # Mock authenticated state
        client.is_authenticated = True
        with patch.object(client, 'authenticate') as mock_auth:
            await client.ensure_authenticated()
            mock_auth.assert_not_called()  # Should not re-authenticate
        
        # Mock unauthenticated state
        client.is_authenticated = False
        with patch.object(client, 'authenticate', return_value=True) as mock_auth:
            await client.ensure_authenticated()
            mock_auth.assert_called_once()  # Should authenticate


class TestUnifiControllerClientIntegration:
    """Integration tests requiring real UniFi controller (marked as integration)."""
    
    @pytest.mark.integration
    async def test_real_controller_authentication(self, integration_config):
        """Test authentication with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
        
        client = UnifiControllerClient(integration_config)
        
        try:
            async with client:
                assert client.is_authenticated is True
                
                # Test basic API call
                devices = await client.get_devices()
                assert isinstance(devices, (list, dict))
                
                if isinstance(devices, list):
                    # Successful response
                    for device in devices:
                        assert "name" in device or "_id" in device
                else:
                    # Error response
                    assert "error" in devices
                    
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")


    @pytest.mark.integration
    async def test_real_controller_site_operations(self, integration_config):
        """Test site operations with real controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        client = UnifiControllerClient(integration_config)
        
        try:
            async with client:
                # Test sites retrieval
                sites = await client.get_sites()
                assert isinstance(sites, (list, dict))
                
                if isinstance(sites, list):
                    assert len(sites) >= 1  # Should have at least default site
                    default_site = next((s for s in sites if s.get("name") == "default"), None)
                    assert default_site is not None
                    
        except Exception as e:
            pytest.fail(f"Site operations test failed: {e}")


class TestUnifiControllerClientConfiguration:
    """Test client configuration handling."""
    
    def test_client_initialization_with_ssl_verification(self):
        """Test client initialization with SSL verification enabled."""
        config = UniFiConfig(
            controller_url="https://test.local",
            username="admin",
            password="password",
            verify_ssl=True
        )
        
        client = UnifiControllerClient(config)
        assert client.config.verify_ssl is True


    def test_client_initialization_without_ssl_verification(self):
        """Test client initialization with SSL verification disabled."""
        config = UniFiConfig(
            controller_url="https://test.local",
            username="admin", 
            password="password",
            verify_ssl=False
        )
        
        client = UnifiControllerClient(config)
        assert client.config.verify_ssl is False


    def test_client_configuration_snapshot(self, test_unifi_config):
        """Test client configuration structure using snapshots."""
        client = UnifiControllerClient(test_unifi_config)
        
        config_dict = {
            "controller_url": client.config.controller_url,
            "username": client.config.username,
            "is_udm_pro": client.config.is_udm_pro,
            "verify_ssl": client.config.verify_ssl,
            "site_name": client.config.site_name,
            "api_base": client.api_base
        }
        
        assert config_dict == snapshot({
            "controller_url": "https://192.168.1.1:443",
            "username": "admin", 
            "is_udm_pro": True,
            "verify_ssl": False,
            "site_name": "default",
            "api_base": "/proxy/network/api"
        })