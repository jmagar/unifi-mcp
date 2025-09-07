"""
Tests for UniFi MCP client tools.

Following FastMCP testing patterns for client management functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.tools.client_tools import register_client_tools


@pytest.fixture
def client_tools_server(mock_unifi_client):
    """Create FastMCP server with only client tools registered."""
    mcp = FastMCP("ClientToolsTestServer")
    register_client_tools(mcp, mock_unifi_client)
    return mcp


class TestGetClientsTool:
    """Test get_clients tool functionality."""
    
    async def test_get_clients_success(self, client_tools_server, mock_client_data):
        """Test successful retrieval of clients."""
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_clients", {})
            
            assert isinstance(result, ToolResult)
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            # Should have structured content with formatted clients
            assert result.structured_content is not None
            assert isinstance(result.structured_content, list)
            assert len(result.structured_content) == 2
            
            # Check client formatting
            client1 = result.structured_content[0]
            assert client1["name"] == "John's iPhone"
            assert client1["is_online"] is True


    async def test_get_clients_online_only_filter(self, client_tools_server):
        """Test get_clients with online_only filter."""
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_clients", {"online_only": True})
            
            assert isinstance(result, ToolResult)
            # All mock clients are online, so should return both
            assert result.structured_content is not None


    async def test_get_clients_wired_only_filter(self, client_tools_server):
        """Test get_clients with wired_only filter."""
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_clients", {"wired_only": True})
            
            assert isinstance(result, ToolResult)
            # Should filter to only wired clients
            assert result.structured_content is not None


    async def test_get_clients_authentication_error(self, mock_failed_unifi_client):
        """Test get_clients with authentication failure."""
        mcp = FastMCP("FailedAuthClientTestServer")
        register_client_tools(mcp, mock_failed_unifi_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_clients", {})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "error" in content_text.lower()


class TestGetClientByMacTool:
    """Test get_client_by_mac tool functionality."""
    
    async def test_get_client_by_mac_success(self, client_tools_server):
        """Test successful retrieval of specific client by MAC."""
        target_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_client_by_mac", {"mac": target_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "John's iPhone" in content_text
            
            # Should return single client
            assert isinstance(result.structured_content, dict)
            assert result.structured_content["name"] == "John's iPhone"


    async def test_get_client_by_mac_not_found(self, client_tools_server):
        """Test get_client_by_mac when client not found."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_client_by_mac", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


    async def test_get_client_by_mac_normalization(self, client_tools_server):
        """Test MAC address normalization in get_client_by_mac."""
        mac_formats = [
            "AA:BB:CC:DD:EE:F1",
            "AA-BB-CC-DD-EE-F1",
            "aa.bb.cc.dd.ee.f1",
            "  aa:bb:cc:dd:ee:f1  "
        ]
        
        async with Client(client_tools_server) as client:
            for mac in mac_formats:
                result = await client.call_tool("get_client_by_mac", {"mac": mac})
                
                # All should find the same client
                assert isinstance(result, ToolResult)
                if "not found" not in result.content[0].text.lower():
                    assert "John's iPhone" in result.content[0].text


class TestBlockUnblockClientTools:
    """Test block_client and unblock_client tools."""
    
    async def test_block_client_success(self, client_tools_server):
        """Test successful client blocking."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("block_client", {"mac": client_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "blocked" in content_text.lower()


    async def test_unblock_client_success(self, client_tools_server):
        """Test successful client unblocking."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("unblock_client", {"mac": client_mac})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "unblocked" in content_text.lower()


    async def test_block_client_not_found(self, client_tools_server):
        """Test blocking non-existent client."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("block_client", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


class TestSetClientNameTool:
    """Test set_client_name tool functionality."""
    
    async def test_set_client_name_success(self, client_tools_server):
        """Test successful client name change."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        new_name = "Updated iPhone Name"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("set_client_name", {
                "mac": client_mac,
                "name": new_name
            })
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "name updated" in content_text.lower()
            assert new_name in content_text


    async def test_set_client_name_not_found(self, client_tools_server):
        """Test setting name for non-existent client."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("set_client_name", {
                "mac": nonexistent_mac,
                "name": "Test Name"
            })
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


    async def test_set_client_name_empty_name(self, client_tools_server):
        """Test setting empty client name."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("set_client_name", {
                "mac": client_mac,
                "name": ""
            })
            
            # Should handle empty name gracefully
            assert isinstance(result, ToolResult)


class TestSetClientNoteTool:
    """Test set_client_note tool functionality."""
    
    async def test_set_client_note_success(self, client_tools_server):
        """Test successful client note setting."""
        client_mac = "aa:bb:cc:dd:ee:f2"
        note = "Test note for desktop PC"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("set_client_note", {
                "mac": client_mac,
                "note": note
            })
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "note updated" in content_text.lower()


    async def test_set_client_note_not_found(self, client_tools_server):
        """Test setting note for non-existent client."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("set_client_note", {
                "mac": nonexistent_mac,
                "note": "Test note"
            })
            
            content_text = result.content[0].text
            assert "not found" in content_text.lower()


class TestClientToolsSchema:
    """Test client tools schema generation."""
    
    async def test_get_clients_schema(self, client_tools_server):
        """Test get_clients tool schema structure."""
        tools = client_tools_server.list_tools()
        get_clients_tool = next(tool for tool in tools if tool.name == "get_clients")
        
        schema = get_clients_tool.inputSchema
        assert schema == snapshot({
            "type": "object",
            "properties": {
                "site_name": {
                    "type": "string",
                    "default": "default",
                    "description": "UniFi site name (default: \"default\")"
                },
                "online_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return online clients"
                },
                "wired_only": {
                    "type": "boolean", 
                    "default": False,
                    "description": "Only return wired clients"
                }
            },
            "additionalProperties": False
        })


    async def test_set_client_name_schema(self, client_tools_server):
        """Test set_client_name tool schema structure."""
        tools = client_tools_server.list_tools()
        set_name_tool = next(tool for tool in tools if tool.name == "set_client_name")
        
        schema = set_name_tool.inputSchema
        assert schema == snapshot({
            "type": "object",
            "properties": {
                "mac": {
                    "type": "string",
                    "description": "Client MAC address (any format)"
                },
                "name": {
                    "type": "string",
                    "description": "New client name"
                },
                "site_name": {
                    "type": "string",
                    "default": "default",
                    "description": "UniFi site name (default: \"default\")"
                }
            },
            "required": ["mac", "name"],
            "additionalProperties": False
        })


    async def test_block_client_schema(self, client_tools_server):
        """Test block_client tool schema structure."""
        tools = client_tools_server.list_tools()
        block_tool = next(tool for tool in tools if tool.name == "block_client")
        
        schema = block_tool.inputSchema
        assert schema == snapshot({
            "type": "object",
            "properties": {
                "mac": {
                    "type": "string",
                    "description": "Client MAC address (any format)"
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


class TestClientToolsErrorHandling:
    """Test client tools error handling scenarios."""
    
    async def test_tools_handle_network_exceptions(self):
        """Test client tools handle network exceptions gracefully."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_clients = AsyncMock(side_effect=Exception("Network timeout"))
        
        mcp = FastMCP("NetworkErrorTestServer")
        register_client_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_clients", {})
            
            assert isinstance(result, ToolResult)
            content_text = result.content[0].text
            assert "error" in content_text.lower()


    async def test_tools_handle_malformed_data(self):
        """Test client tools handle malformed client data."""
        malformed_clients = [
            {"_id": "client1"},  # Missing required fields
            {"name": "Test Client"}  # Missing MAC
        ]
        
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_clients = AsyncMock(return_value=malformed_clients)
        
        mcp = FastMCP("MalformedDataTestServer")
        register_client_tools(mcp, mock_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_clients", {})
            
            # Should handle malformed data gracefully
            assert isinstance(result, ToolResult)


@pytest.mark.integration
class TestClientToolsIntegration:
    """Integration tests for client tools with real controller."""
    
    async def test_real_get_clients(self, integration_config):
        """Test get_clients with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("ClientIntegrationTestServer")
        register_client_tools(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    result = await test_client.call_tool("get_clients", {})
                    
                    assert isinstance(result, ToolResult)
                    assert len(result.content) > 0
                    
                    # Should have structured content
                    assert result.structured_content is not None
                    
        except Exception as e:
            pytest.fail(f"Client integration test failed: {e}")


    @pytest.mark.integration  
    async def test_real_client_lookup(self, integration_config):
        """Test client lookup with real controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")
            
        from unifi_mcp.client import UnifiControllerClient
        
        client = UnifiControllerClient(integration_config)
        mcp = FastMCP("ClientLookupIntegrationTestServer")
        register_client_tools(mcp, client)
        
        try:
            async with Client(mcp) as test_client:
                async with client:
                    # First get clients to find a valid MAC
                    clients_result = await test_client.call_tool("get_clients", {})
                    
                    if (isinstance(clients_result.structured_content, list) and 
                        len(clients_result.structured_content) > 0):
                        
                        client_mac = clients_result.structured_content[0].get("mac")
                        if client_mac:
                            # Test individual client lookup
                            lookup_result = await test_client.call_tool("get_client_by_mac", {"mac": client_mac})
                            assert isinstance(lookup_result, ToolResult)
                    
        except Exception as e:
            pytest.fail(f"Client lookup integration test failed: {e}")