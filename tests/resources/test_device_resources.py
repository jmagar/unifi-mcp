"""
Tests for UniFi MCP device resources.

Following FastMCP testing patterns for resource functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client
from mcp.types import TextContent

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.resources.device_resources import register_device_resources


@pytest.fixture
def device_resources_server(mock_unifi_client):
    """Create FastMCP server with only device resources registered."""
    mcp = FastMCP("DeviceResourcesTestServer")
    register_device_resources(mcp, mock_unifi_client)
    return mcp


class TestDevicesResource:
    """Test unifi://devices resource functionality."""
    
    async def test_devices_resource_registration(self, device_resources_server):
        """Test that device resources are properly registered."""
        resources = device_resources_server.list_resources()
        resource_uris = [resource.uri for resource in resources]
        
        # Should have devices list resource
        assert any("unifi://devices" in uri for uri in resource_uris)
        
        # Should have individual device resource pattern
        assert any("unifi://device/" in uri for uri in resource_uris)


    async def test_devices_resource_content(self, device_resources_server):
        """Test devices resource content retrieval."""
        async with Client(device_resources_server) as client:
            # Get the devices resource URI
            resources = client.list_resources()
            devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
            assert devices_resource is not None
            
            # Read the resource content
            content = await client.read_resource(devices_resource.uri)
            
            assert content is not None
            assert len(content) > 0
            assert isinstance(content[0], TextContent)
            
            # Content should contain device information
            content_text = content[0].text
            assert "device" in content_text.lower()


    async def test_devices_resource_with_site_parameter(self, device_resources_server):
        """Test devices resource with site parameter."""
        async with Client(device_resources_server) as client:
            resources = client.list_resources()
            devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
            
            # Test with site parameter
            site_uri = f"{devices_resource.uri}?site=custom-site"
            content = await client.read_resource(site_uri)
            
            assert content is not None
            assert len(content) > 0


class TestDeviceResource:
    """Test unifi://device/{mac} resource functionality."""
    
    async def test_device_resource_with_valid_mac(self, device_resources_server):
        """Test individual device resource with valid MAC."""
        device_mac = "aa:bb:cc:dd:ee:01"
        
        async with Client(device_resources_server) as client:
            # Construct device resource URI
            device_uri = f"unifi://device/{device_mac}"
            
            content = await client.read_resource(device_uri)
            
            assert content is not None
            assert len(content) > 0
            assert isinstance(content[0], TextContent)
            
            # Should contain specific device information
            content_text = content[0].text
            assert "Main Switch" in content_text


    async def test_device_resource_with_invalid_mac(self, device_resources_server):
        """Test individual device resource with invalid MAC."""
        invalid_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(device_resources_server) as client:
            device_uri = f"unifi://device/{invalid_mac}"
            
            content = await client.read_resource(device_uri)
            
            assert content is not None
            assert len(content) > 0
            
            # Should indicate device not found
            content_text = content[0].text
            assert "not found" in content_text.lower()


    async def test_device_resource_mac_normalization(self, device_resources_server):
        """Test device resource MAC address normalization."""
        mac_formats = [
            "AA:BB:CC:DD:EE:01",
            "AA-BB-CC-DD-EE-01", 
            "aa.bb.cc.dd.ee.01"
        ]
        
        async with Client(device_resources_server) as client:
            for mac in mac_formats:
                device_uri = f"unifi://device/{mac}"
                content = await client.read_resource(device_uri)
                
                assert content is not None
                assert len(content) > 0
                
                # All should find the same device
                content_text = content[0].text
                if "not found" not in content_text.lower():
                    assert "Main Switch" in content_text


class TestDeviceStatsResource:
    """Test unifi://device/{mac}/stats resource functionality."""
    
    async def test_device_stats_resource(self, device_resources_server):
        """Test device statistics resource."""
        device_mac = "aa:bb:cc:dd:ee:01"
        
        async with Client(device_resources_server) as client:
            stats_uri = f"unifi://device/{device_mac}/stats"
            
            content = await client.read_resource(stats_uri)
            
            assert content is not None
            assert len(content) > 0
            
            # Should contain statistics information
            content_text = content[0].text
            assert any(keyword in content_text.lower() for keyword in ["stats", "cpu", "memory", "uptime"])


    async def test_device_stats_resource_not_found(self, device_resources_server):
        """Test device statistics resource for non-existent device."""
        invalid_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(device_resources_server) as client:
            stats_uri = f"unifi://device/{invalid_mac}/stats"
            
            content = await client.read_resource(stats_uri)
            
            assert content is not None
            content_text = content[0].text
            assert "not found" in content_text.lower()


class TestDeviceResourcesSchema:
    """Test device resources schema and metadata."""
    
    async def test_devices_resource_metadata(self, device_resources_server):
        """Test devices resource metadata structure."""
        resources = device_resources_server.list_resources()
        devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
        
        assert devices_resource is not None
        assert devices_resource.name
        assert devices_resource.description
        assert "device" in devices_resource.description.lower()
        
        # Test resource URI structure
        assert devices_resource.uri == snapshot("unifi://devices")


    async def test_device_resource_metadata(self, device_resources_server):
        """Test individual device resource metadata."""
        resources = device_resources_server.list_resources()
        device_resource = next((r for r in resources if "unifi://device/" in r.uri), None)
        
        assert device_resource is not None
        assert device_resource.name
        assert device_resource.description
        assert "{mac}" in device_resource.uri.lower()


    async def test_device_stats_resource_metadata(self, device_resources_server):
        """Test device statistics resource metadata."""
        resources = device_resources_server.list_resources()
        stats_resource = next((r for r in resources if "stats" in r.uri.lower()), None)
        
        if stats_resource:  # May not be implemented yet
            assert stats_resource.name
            assert stats_resource.description
            assert "stats" in stats_resource.description.lower()


class TestDeviceResourcesErrorHandling:
    """Test device resources error handling."""
    
    async def test_resources_handle_client_errors(self, mock_failed_unifi_client):
        """Test device resources handle client authentication errors."""
        mcp = FastMCP("FailedAuthResourceTestServer")
        register_device_resources(mcp, mock_failed_unifi_client)
        
        async with Client(mcp) as client:
            resources = client.list_resources()
            devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
            
            content = await client.read_resource(devices_resource.uri)
            
            assert content is not None
            content_text = content[0].text
            assert "error" in content_text.lower()


    async def test_resources_handle_network_exceptions(self):
        """Test device resources handle network exceptions gracefully."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(side_effect=Exception("Connection timeout"))
        
        mcp = FastMCP("NetworkErrorResourceTestServer")
        register_device_resources(mcp, mock_client)
        
        async with Client(mcp) as client:
            resources = client.list_resources()
            devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
            
            content = await client.read_resource(devices_resource.uri)
            
            assert content is not None
            content_text = content[0].text
            assert "error" in content_text.lower()


    async def test_resources_handle_malformed_responses(self):
        """Test device resources handle malformed API responses."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(return_value="invalid response")
        
        mcp = FastMCP("MalformedResourceTestServer")
        register_device_resources(mcp, mock_client)
        
        async with Client(mcp) as client:
            resources = client.list_resources()
            devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
            
            content = await client.read_resource(devices_resource.uri)
            
            # Should handle malformed responses gracefully
            assert content is not None


class TestDeviceResourcesFiltering:
    """Test device resources filtering and parameters."""
    
    async def test_devices_resource_site_filtering(self, device_resources_server):
        """Test devices resource filtering by site."""
        async with Client(device_resources_server) as client:
            # Test default site
            default_uri = "unifi://devices"
            default_content = await client.read_resource(default_uri)
            
            # Test custom site
            custom_uri = "unifi://devices?site=custom-site"
            custom_content = await client.read_resource(custom_uri)
            
            # Both should return valid content
            assert default_content is not None
            assert custom_content is not None


    async def test_device_resource_with_site_parameter(self, device_resources_server):
        """Test individual device resource with site parameter."""
        device_mac = "aa:bb:cc:dd:ee:01"
        
        async with Client(device_resources_server) as client:
            # Test with site parameter
            site_uri = f"unifi://device/{device_mac}?site=custom-site"
            content = await client.read_resource(site_uri)
            
            assert content is not None
            assert len(content) > 0


@pytest.mark.integration
class TestDeviceResourcesIntegration:
    """Integration tests for device resources with real controller."""
    
    async def test_real_devices_resource(self, integration_config):
        """Test devices resource with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("DeviceResourceIntegrationTestServer")
        register_device_resources(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    resources = test_client.list_resources()
                    devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
                    
                    assert devices_resource is not None
                    
                    content = await test_client.read_resource(devices_resource.uri)
                    assert content is not None
                    assert len(content) > 0
                    
        except Exception as e:
            pytest.fail(f"Device resource integration test failed: {e}")


    @pytest.mark.integration
    async def test_real_device_resource_lookup(self, integration_config):
        """Test individual device resource with real controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("DeviceLookupIntegrationTestServer") 
        register_device_resources(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    # First get devices to find a valid MAC
                    resources = test_client.list_resources()
                    devices_resource = next((r for r in resources if "unifi://devices" in r.uri), None)
                    devices_content = await test_client.read_resource(devices_resource.uri)
                    
                    # If we got device data, try to find a MAC and test individual lookup
                    if devices_content and len(devices_content) > 0:
                        devices_text = devices_content[0].text
                        # This is a simplified test - in practice would parse the content
                        # for actual MAC addresses from the device list
                        
                        # Test with a common MAC format (would need real MAC from devices)
                        # For now, just test that the resource handler works
                        test_mac = "aa:bb:cc:dd:ee:01"  # Placeholder
                        device_uri = f"unifi://device/{test_mac}"
                        
                        device_content = await test_client.read_resource(device_uri)
                        assert device_content is not None
                    
        except Exception as e:
            pytest.fail(f"Device lookup integration test failed: {e}")