"""
Tests for UniFi MCP Server initialization and configuration.

Following FastMCP testing patterns with in-memory testing and single behavior per test.
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import Client, FastMCP
from mcp.types import TextContent

from unifi_mcp.config import ServerConfig, UniFiConfig
from unifi_mcp.server import UniFiMCPServer


@pytest.mark.asyncio
async def test_server_initialization_with_basic_config(test_unifi_config, test_server_config):
    """Test that server initializes correctly with basic configuration."""
    with patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=False), patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        server = UniFiMCPServer(test_unifi_config, test_server_config)

        assert server.unifi_config == test_unifi_config
        assert server.server_config == test_server_config
        assert isinstance(server.mcp, FastMCP)
        assert server.mcp.name == "UniFi Local Controller MCP Server"


@pytest.mark.asyncio
async def test_server_tools_registration(test_server):
    """Test that the unified tool surface is registered with the server."""
    tools = await test_server._list_tools()
    tool_names = [tool.name for tool in tools]

    assert tool_names == ["unifi", "unifi_help"]


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
    """Test that the unified tool and help tool execute successfully."""
    async with Client(test_server) as client:
        result = await client.call_tool("unifi", {"action": "get_devices"})
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)

        help_result = await client.call_tool("unifi_help", {})
        assert len(help_result.content) > 0
        assert isinstance(help_result.content[0], TextContent)
        assert "Tool Reference" in help_result.content[0].text


@pytest.mark.asyncio
async def test_server_with_oauth_configuration():
    """Test server initialization with OAuth configuration."""
    with (
        patch.dict(
            os.environ,
            {
                "FASTMCP_SERVER_AUTH": "fastmcp.server.auth.providers.google.GoogleProvider",
                "UNIFI_MCP_TOKEN": "test-token",
            },
            clear=False,
        ),
        patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class,
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        config = UniFiConfig(controller_url="https://test.local", username="test", password="test")
        server_config = ServerConfig()

        server = UniFiMCPServer(config, server_config)

        assert isinstance(server.mcp, FastMCP)


@pytest.mark.asyncio
async def test_server_without_oauth_configuration():
    """Test server initialization without OAuth configuration."""
    with patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=True), patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        config = UniFiConfig(controller_url="https://test.local", username="test", password="test")
        server_config = ServerConfig()

        server = UniFiMCPServer(config, server_config)

        assert isinstance(server.mcp, FastMCP)


@pytest.mark.asyncio
async def test_server_handles_tool_errors_gracefully(test_unifi_config, test_server_config, mock_failed_unifi_client):
    """Test that server handles tool execution errors gracefully."""
    with (
        patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=False),
        patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_failed_unifi_client),
    ):
        server = UniFiMCPServer(test_unifi_config, test_server_config)
        await server.initialize()

        async with Client(server.mcp) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})

            assert len(result.content) > 0

            content_text = result.content[0].text
            assert "error" in content_text.lower()

        await server.cleanup()


@pytest.mark.asyncio
async def test_server_tool_schema_generation(test_server):
    """Test that tool schemas are generated correctly."""
    tools = await test_server._list_tools()
    unifi_tool = next(tool for tool in tools if tool.name == "unifi")

    schema = unifi_tool.parameters

    assert schema["type"] == "object"
    assert "action" in schema["properties"]
    assert "site_name" in schema["properties"]
    assert "confirm" in schema["properties"]
    assert schema["required"] == ["action"]


@pytest.mark.asyncio
async def test_server_resource_uri_patterns(test_server):
    """Test that core device resource URIs are registered."""
    resources = await test_server._list_resources()

    resource_uris = {str(resource.uri) for resource in resources}
    assert "unifi://devices" in resource_uris
    assert "unifi://device-tags" in resource_uris


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
    custom_config = UniFiConfig(controller_url="https://test.local", username="test", password="test")

    with patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=False), patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class:
        mock_client = AsyncMock()
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
    udm_config = UniFiConfig(controller_url="https://192.168.1.1:443", username="admin", password="password", is_udm_pro=True)

    server_config = ServerConfig()

    with patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=False), patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        server = UniFiMCPServer(udm_config, server_config)
        await server.initialize()

        mock_client_class.assert_called_once_with(udm_config)
        assert server.unifi_config.is_udm_pro is True

        await server.cleanup()


@pytest.mark.asyncio
async def test_server_initialization_with_legacy_config():
    """Test server initialization with legacy controller configuration."""
    legacy_config = UniFiConfig(controller_url="https://192.168.1.1:8443", username="admin", password="password", is_udm_pro=False)

    server_config = ServerConfig()

    with patch.dict(os.environ, {"UNIFI_MCP_TOKEN": "test-token"}, clear=False), patch("unifi_mcp.server.UnifiControllerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        server = UniFiMCPServer(legacy_config, server_config)
        await server.initialize()

        mock_client_class.assert_called_once_with(legacy_config)
        assert server.unifi_config.is_udm_pro is False

        await server.cleanup()
