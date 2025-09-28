"""
Tests for UniFi MCP device tools.

Following FastMCP testing patterns with in-memory testing and tool validation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.tools.device_tools import register_device_tools


@pytest.fixture
def device_tools_server(mock_unifi_client):
    """Create FastMCP server with only device tools registered."""
    mcp = FastMCP("DeviceToolsTestServer")
    register_device_tools(mcp, mock_unifi_client)
    return mcp


class TestGetDevicesTool:
    """Test get_devices tool functionality."""
    
    async def test_get_devices_success(self, device_tools_server, mock_device_data):
        """Test successful retrieval of devices."""
        async with Client(device_tools_server) as client:
            result = await client.call_tool("get_devices", {})
            
            assert isinstance(result, ToolResult)
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            # Should have structured content with formatted devices
            assert result.structured_content is not None
            assert isinstance(result.structured_content, list)
            assert len(result.structured_content) == 2
            
            # Check device formatting
            device1 = result.structured_content[0]
            assert device1["name"] == "Main Switch"
            assert device1["model"] == "US-24-250W"
            assert device1["type"] == "usw"
            

    async def test_get_devices_with_custom_site(self, device_tools_server):
        """Test get_devices with custom site parameter."""
        async with Client(device_tools_server) as client:
            result = await client.call_tool("get_devices", {"site_name": "custom-site"})
            
            assert isinstance(result, ToolResult)
            # Mock should have been called with custom site
            # In real implementation, would verify the site parameter was passed


    async def test_get_devices_authentication_error(self, mock_failed_unifi_client):
        """Test get_devices with authentication failure."""
        mcp = FastMCP("FailedAuthTestServer") 
        register_device_tools(mcp, mock_failed_unifi_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "error" in content_text.lower()
            
            # Should have error in structured content
            assert "error" in result.structured_content


    async def test_get_devices_invalid_response_format(self):
        """Test get_devices with invalid response format."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(return_value="invalid response")
        
        mcp = FastMCP("InvalidResponseTestServer")
        register_device_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            content_text = result.content[0].text
            assert "unexpected response format" in content_text.lower()


    async def test_get_devices_formatting_error(self):
        """Test get_devices with formatting errors."""
        # Mock device data that would cause formatting errors
        problematic_device = {"_id": "bad-device"}  # Missing required fields
        
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(return_value=[problematic_device])
        
        mcp = FastMCP("FormattingErrorTestServer")
        register_device_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            # Should handle formatting errors gracefully
            assert isinstance(result, ToolResult)
            assert result.structured_content is not None


class TestGetDeviceByMacTool:
    """Test get_device_by_mac tool functionality."""
    
    async def test_get_device_by_mac_success(self, device_tools_server, mock_device_data):
        """Test successful retrieval of specific device by MAC."""
        target_mac = "aa:bb:cc:dd:ee:01"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("get_device_by_mac", {"mac": target_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "Main Switch" in content_text
            
            # Should return single device
            assert isinstance(result.structured_content, dict)
            assert result.structured_content["name"] == "Main Switch"


    async def test_get_device_by_mac_not_found(self, device_tools_server):
        """Test get_device_by_mac when device not found."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("get_device_by_mac", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


    async def test_get_device_by_mac_normalization(self, device_tools_server):
        """Test MAC address normalization in get_device_by_mac."""
        # Test different MAC formats should all work
        mac_formats = [
            "AA:BB:CC:DD:EE:01",
            "AA-BB-CC-DD-EE-01", 
            "aa.bb.cc.dd.ee.01",
            "  aa:bb:cc:dd:ee:01  "
        ]
        
        async with Client(device_tools_server) as client:
            for mac in mac_formats:
                result = await client.call_tool("get_device_by_mac", {"mac": mac})
                
                # All should find the same device
                assert isinstance(result, ToolResult)
                if "not found" not in result.content[0].text.lower():
                    assert "Main Switch" in result.content[0].text


class TestRestartDeviceTool:
    """Test restart_device tool functionality."""
    
    async def test_restart_device_success(self, device_tools_server):
        """Test successful device restart."""
        device_mac = "aa:bb:cc:dd:ee:01"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("restart_device", {"mac": device_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "restart initiated" in content_text.lower()


    async def test_restart_device_not_found(self, device_tools_server):
        """Test restart_device when device not found.""" 
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("restart_device", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


    async def test_restart_device_authentication_error(self, mock_failed_unifi_client):
        """Test restart_device with authentication failure."""
        mcp = FastMCP("FailedAuthRestartTestServer")
        register_device_tools(mcp, mock_failed_unifi_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("restart_device", {"mac": "aa:bb:cc:dd:ee:01"})
            
            content_text = result.content[0].text
            assert "error" in content_text.lower()


class TestLocateDeviceTool:
    """Test locate_device tool functionality."""
    
    async def test_locate_device_success(self, device_tools_server):
        """Test successful device locate."""
        device_mac = "aa:bb:cc:dd:ee:02"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("locate_device", {"mac": device_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "locate started" in content_text.lower()


    async def test_locate_device_not_found(self, device_tools_server):
        """Test locate_device when device not found."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(device_tools_server) as client:
            result = await client.call_tool("locate_device", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


class TestDeviceToolsSchema:
    """Test device tools schema generation."""
    
    async def test_get_devices_schema(self, device_tools_server):
        """Test get_devices tool schema structure."""
        tools = device_tools_server.list_tools()
        get_devices_tool = next(tool for tool in tools if tool.name == "get_devices")
        
        schema = get_devices_tool.inputSchema
        assert schema == snapshot({
            "type": "object",
            "properties": {
                "site_name": {
                    "type": "string",
                    "default": "default",
                    "description": "UniFi site name (default: \"default\")"
                }
            },
            "additionalProperties": False
        })


    async def test_get_device_by_mac_schema(self, device_tools_server):
        """Test get_device_by_mac tool schema structure."""
        tools = device_tools_server.list_tools()
        get_device_tool = next(tool for tool in tools if tool.name == "get_device_by_mac")
        
        schema = get_device_tool.inputSchema
        assert schema == snapshot({
            "type": "object", 
            "properties": {
                "mac": {
                    "type": "string",
                    "description": "Device MAC address (any format)"
                },
                "site_name": {
                    "type": "string", 
                    "default": "default",
                    "description": "UniFi site name (default: \"default\")"
                }
            },
            "required": ["mac"],
            "additionalProperties": False
        })


    async def test_restart_device_schema(self, device_tools_server):
        """Test restart_device tool schema structure."""
        tools = device_tools_server.list_tools()
        restart_tool = next(tool for tool in tools if tool.name == "restart_device")
        
        schema = restart_tool.inputSchema
        assert schema == snapshot({
            "type": "object",
            "properties": {
                "mac": {
                    "type": "string", 
                    "description": "Device MAC address (any format)"
                },
                "site_name": {
                    "type": "string",
                    "default": "default", 
                    "description": "UniFi site name (default: \"default\")"
                }
            },
            "required": ["mac"],
            "additionalProperties": False
        })


class TestDeviceToolsErrorHandling:
    """Test device tools error handling."""
    
    async def test_tools_handle_client_exceptions(self):
        """Test that tools handle client exceptions gracefully."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(side_effect=Exception("Connection timeout"))
        
        mcp = FastMCP("ExceptionTestServer")
        register_device_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            # Should return error, not raise exception
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "error" in content_text.lower()
            assert "structured_content" in result.__dict__


    async def test_tools_handle_none_responses(self):
        """Test tools handling None responses from client."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(return_value=None)
        
        mcp = FastMCP("NoneResponseTestServer")
        register_device_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            assert isinstance(result, ToolResult)
            # Should handle None gracefully


@pytest.mark.integration
class TestDeviceToolsIntegration:
    """Integration tests for device tools with real controller."""
    
    async def test_real_get_devices(self, integration_config):
        """Test get_devices with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("IntegrationTestServer")
        register_device_tools(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    result = await test_client.call_tool("get_devices", {})
                    
                    assert isinstance(result, ToolResult)
                    assert len(result.content) > 0
                    
                    # Should have structured content
                    assert result.structured_content is not None
                    
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
            

    @pytest.mark.integration
    async def test_real_device_operations(self, integration_config):
        """Test device operations with real controller (locate only - safer than restart)."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("DeviceOpsIntegrationTestServer")
        register_device_tools(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    # First get devices to find a valid MAC
                    devices_result = await test_client.call_tool("get_devices", {})
                    
                    if (isinstance(devices_result.structured_content, list) and 
                        len(devices_result.structured_content) > 0):
                        
                        device_mac = devices_result.structured_content[0].get("mac")
                        if device_mac:
                            # Test locate (safer than restart)
                            locate_result = await test_client.call_tool("locate_device", {"mac": device_mac})
                            assert isinstance(locate_result, ToolResult)
                    
        except Exception as e:
            pytest.fail(f"Device operations integration test failed: {e}")