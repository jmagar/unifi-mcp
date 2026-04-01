"""
Tests for UniFi MCP client tools.

Following FastMCP testing patterns for client management functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client
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
            
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            payload = result.data
            assert payload is not None
            assert isinstance(payload["data"], list)
            assert len(payload["data"]) == 2
            
            # Check client formatting
            client1 = payload["data"][0]
            assert client1["name"] == "John's iPhone"
            assert client1["connection_type"] == "wireless"


    async def test_get_clients_connected_only_filter(self, client_tools_server):
        """Test get_clients with connected_only filter."""
        async with Client(client_tools_server) as client:
            result = await client.call_tool("get_clients", {"connected_only": True})
            
            assert result.data is not None


    async def test_get_clients_rejects_unknown_filter(self, client_tools_server):
        """Test get_clients rejects removed wired_only filter."""
        async with Client(client_tools_server) as client:
            with pytest.raises(Exception, match="wired_only"):
                await client.call_tool("get_clients", {"wired_only": True})


    async def test_get_clients_authentication_error(self, mock_failed_unifi_client):
        """Test get_clients with authentication failure."""
        mcp = FastMCP("FailedAuthClientTestServer")
        register_client_tools(mcp, mock_failed_unifi_client)
        
        async with Client(mcp) as client:
            result = await client.call_tool("get_clients", {})
            
            content_text = result.content[0].text
            assert "error" in content_text.lower()


class TestReconnectClientTool:
    """Test reconnect_client tool functionality."""
    
    async def test_reconnect_client_success(self, client_tools_server):
        """Test successful reconnect request for a client MAC."""
        target_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("reconnect_client", {"mac": target_mac})
            
            assert "reconnect requested" in result.content[0].text.lower()
            assert isinstance(result.data, dict)
            assert result.data["success"] is True


    async def test_reconnect_client_not_found_passthrough(self, client_tools_server):
        """Test reconnect_client still emits a command for an arbitrary MAC."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("reconnect_client", {"mac": nonexistent_mac})
            
            assert "reconnect requested" in result.content[0].text.lower()


    async def test_reconnect_client_normalization(self, client_tools_server):
        """Test MAC address normalization in reconnect_client."""
        mac_formats = [
            "AA:BB:CC:DD:EE:F1",
            "AA-BB-CC-DD-EE-F1",
            "aa.bb.cc.dd.ee.f1",
            "  aa:bb:cc:dd:ee:f1  "
        ]
        
        async with Client(client_tools_server) as client:
            for mac in mac_formats:
                result = await client.call_tool("reconnect_client", {"mac": mac})
                
                assert "reconnect requested" in result.content[0].text.lower()


class TestBlockUnblockClientTools:
    """Test block_client and unblock_client tools."""
    
    async def test_block_client_success(self, client_tools_server):
        """Test successful client blocking."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("block_client", {"mac": client_mac})
            
            content_text = result.content[0].text
            assert "blocked" in content_text.lower()


    async def test_unblock_client_success(self, client_tools_server):
        """Test successful client unblocking."""
        client_mac = "aa:bb:cc:dd:ee:f1"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("unblock_client", {"mac": client_mac})
            
            content_text = result.content[0].text
            assert "unblocked" in content_text.lower()


    async def test_block_client_not_found(self, client_tools_server):
        """Test blocking non-existent client."""
        nonexistent_mac = "ff:ff:ff:ff:ff:ff"
        
        async with Client(client_tools_server) as client:
            result = await client.call_tool("block_client", {"mac": nonexistent_mac})
            
            content_text = result.content[0].text
            assert "blocked" in content_text.lower()


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
            
            assert result.data is not None


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
        tools = await client_tools_server._list_tools()
        get_clients_tool = next(tool for tool in tools if tool.name == "get_clients")
        
        schema = get_clients_tool.parameters
        assert schema == snapshot({
            "properties": {
                "connected_only": {
                    "default": True,
                    "title": "Connected Only",
                    "type": "boolean",
                },
                "site_name": {
                    "default": "default",
                    "title": "Site Name",
                    "type": "string",
                },
            },
            "type": "object",
        })


    async def test_set_client_name_schema(self, client_tools_server):
        """Test set_client_name tool schema structure."""
        tools = await client_tools_server._list_tools()
        set_name_tool = next(tool for tool in tools if tool.name == "set_client_name")
        
        schema = set_name_tool.parameters
        assert schema == snapshot({
            "properties": {
                "mac": {"title": "Mac", "type": "string"},
                "name": {"title": "Name", "type": "string"},
                "site_name": {
                    "default": "default",
                    "title": "Site Name",
                    "type": "string",
                },
            },
            "required": ["mac", "name"],
            "type": "object",
        })


    async def test_block_client_schema(self, client_tools_server):
        """Test block_client tool schema structure."""
        tools = await client_tools_server._list_tools()
        block_tool = next(tool for tool in tools if tool.name == "block_client")
        
        schema = block_tool.parameters
        assert schema == snapshot({
            "properties": {
                "mac": {"title": "Mac", "type": "string"},
                "site_name": {
                    "default": "default",
                    "title": "Site Name",
                    "type": "string",
                },
            },
            "required": ["mac"],
            "type": "object",
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
            
            assert result.data is not None


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
