"""
Tests for UniFi MCP Server initialization and configuration.

Following FastMCP testing patterns with in-memory testing and single behavior per test.
"""

import pytest
import os
from unittest.mock import patch, Mock
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from unifi_mcp.server import UniFiMCPServer
from unifi_mcp.config import UniFiConfig, ServerConfig


@pytest.mark.asyncio
async def test_server_initialization_with_basic_config(test_unifi_config, test_server_config):
    """Test that server initializes correctly with basic configuration."""
    with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        server = UniFiMCPServer(test_unifi_config, test_server_config)
        
        assert server.unifi_config == test_unifi_config
        assert server.server_config == test_server_config
        assert isinstance(server.mcp, FastMCP)
        assert server.mcp.name == "UniFi Local Controller MCP Server"


@pytest.mark.asyncio
async def test_server_tools_registration(test_server):
    """Test that all expected tools are registered with the server."""
    tools = await test_server._list_tools()
    tool_names = [tool.name for tool in tools]
    
    # Device tools
    assert "get_devices" in tool_names
    assert "get_device_by_mac" in tool_names
    assert "restart_device" in tool_names
    assert "locate_device" in tool_names
    
    # Client tools
    assert "get_clients" in tool_names
    assert "block_client" in tool_names
    assert "unblock_client" in tool_names
    assert "set_client_name" in tool_names
    assert "set_client_note" in tool_names
    
    # Network tools
    assert "get_network_configs" in tool_names  # Actual name
    assert "get_wlan_configs" in tool_names
    assert "get_port_configs" in tool_names
    
    # Monitoring tools
    assert "get_events" in tool_names
    assert "get_alarms" in tool_names
    
    # Additional tools that should be present
    assert "get_sites" in tool_names
    assert "get_controller_status" in tool_names


@pytest.mark.asyncio
async def test_server_resources_registration(test_server):
    """Test that all expected resources are registered with the server."""
    resources = await test_server._list_resources()
    resource_uris = [str(resource.uri) for resource in resources]
    
    # Device resources
    assert "unifi://devices" in resource_uris
    
    # Client resources  
    assert "unifi://clients" in resource_uris
    
    # Network resources
    assert "unifi://config/networks" in resource_uris
    assert "unifi://config/wlans" in resource_uris
    
    # Monitoring resources
    assert "unifi://events" in resource_uris
    assert "unifi://alarms" in resource_uris
    assert "unifi://health" in resource_uris
    
    # Overview resources
    assert "unifi://overview" in resource_uris
    assert "unifi://dashboard" in resource_uris
    
    # Additional resources that should be present
    assert "unifi://sites" in resource_uris
    assert "unifi://sysinfo" in resource_uris


@pytest.mark.asyncio
async def test_server_tool_execution_with_mock_client(test_server):
    """Test that tools execute successfully with mocked client."""
    async with Client(test_server) as client:
        # Test device tool
        result = await client.call_tool("get_devices", {})
        assert isinstance(result, ToolResult)
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)
        
        # Test client tool
        result = await client.call_tool("get_clients", {})
        assert isinstance(result, ToolResult)
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)


@pytest.mark.asyncio
async def test_server_with_oauth_configuration():
    """Test server initialization with OAuth configuration."""
    with patch.dict(os.environ, {"FASTMCP_SERVER_AUTH": "google"}):
        with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            config = UniFiConfig(
                controller_url="https://test.local",
                username="test",
                password="test"
            )
            server_config = ServerConfig()
            
            server = UniFiMCPServer(config, server_config)
            
            # Should detect OAuth configuration
            assert hasattr(server, '_auth_enabled')


@pytest.mark.asyncio
async def test_server_without_oauth_configuration():
    """Test server initialization without OAuth configuration."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            config = UniFiConfig(
                controller_url="https://test.local", 
                username="test",
                password="test"
            )
            server_config = ServerConfig()
            
            server = UniFiMCPServer(config, server_config)
            
            # Should not have OAuth enabled
            assert hasattr(server, '_auth_enabled')
            assert server._auth_enabled is False


@pytest.mark.asyncio
async def test_server_handles_tool_errors_gracefully(test_unifi_config, test_server_config, mock_failed_unifi_client):
    """Test that server handles tool execution errors gracefully."""
    with patch('unifi_mcp.server.UnifiControllerClient', return_value=mock_failed_unifi_client):
        server = UniFiMCPServer(test_unifi_config, test_server_config)
        
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_devices", {})
            
            # Should return error response, not raise exception
            assert isinstance(result, ToolResult)
            assert len(result.content) > 0
            
            # Content should indicate error
            content_text = result.content[0].text
            assert "error" in content_text.lower()


@pytest.mark.asyncio
async def test_server_tool_schema_generation(test_server):
    """Test that tool schemas are generated correctly."""
    tools = test_server._list_tools()
    get_devices_tool = next(tool for tool in tools if tool.name == "get_devices")
    
    schema = get_devices_tool.inputSchema
    
    # Should have proper schema structure
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


@pytest.mark.asyncio
async def test_server_resource_uri_patterns(test_server):
    """Test that resource URI patterns are correctly configured."""
    resources = await test_server._list_resources()
    
    # Find device resource
    device_resources = [r for r in resources if "unifi://device/" in str(r.uri)]
    assert len(device_resources) > 0
    
    device_resource = device_resources[0]
    assert device_resource.name
    assert device_resource.description
    assert "mac" in str(device_resource.uri).lower()


@pytest.mark.asyncio
async def test_server_ping_functionality(test_server):
    """Test that server responds to ping requests."""
    async with Client(test_server) as client:
        result = await client.ping()
        assert result is True


@pytest.mark.asyncio
async def test_server_with_different_site_configurations():
    """Test server behavior with different site configurations."""
    # Test with custom config
    custom_config = UniFiConfig(
        controller_url="https://test.local",
        username="test", 
        password="test"
    )
    
    with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        server_config = ServerConfig()
        server = UniFiMCPServer(custom_config, server_config)
        
        assert server.unifi_config.controller_url == "https://test.local"


@pytest.mark.asyncio
async def test_server_mac_normalization_utility():
    """Test MAC address normalization utility function."""
    from unifi_mcp.server import _normalize_mac
    
    # Test different MAC formats
    assert _normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"
    assert _normalize_mac("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff" 
    assert _normalize_mac("AA.BB.CC.DD.EE.FF") == "aa:bb:cc:dd:ee:ff"
    assert _normalize_mac("  AA:BB:CC:DD:EE:FF  ") == "aa:bb:cc:dd:ee:ff"


@pytest.mark.asyncio
async def test_server_initialization_with_udm_pro_config():
    """Test server initialization with UDM Pro configuration."""
    udm_config = UniFiConfig(
        controller_url="https://192.168.1.1:443",
        username="admin",
        password="password",
        is_udm_pro=True
    )
    
    server_config = ServerConfig()
    
    with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        server = UniFiMCPServer(udm_config, server_config)
        
        # Verify client is initialized with UDM Pro config
        mock_client_class.assert_called_once_with(udm_config)
        assert server.unifi_config.is_udm_pro is True


@pytest.mark.asyncio
async def test_server_initialization_with_legacy_config():
    """Test server initialization with legacy controller configuration."""
    legacy_config = UniFiConfig(
        controller_url="https://192.168.1.1:8443",
        username="admin", 
        password="password",
        is_udm_pro=False
    )
    
    server_config = ServerConfig()
    
    with patch('unifi_mcp.server.UnifiControllerClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        server = UniFiMCPServer(legacy_config, server_config)
        
        # Verify client is initialized with legacy config
        mock_client_class.assert_called_once_with(legacy_config)
        assert server.unifi_config.is_udm_pro is False