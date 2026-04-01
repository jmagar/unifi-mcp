"""
Integration tests for UniFi MCP Server.

These tests require actual UniFi controller connection and are marked with @pytest.mark.integration.
Following FastMCP testing patterns for integration testing.
"""

import os

import pytest
from fastmcp import Client
from fastmcp.utilities.tests import run_server_in_process

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.config import ServerConfig, UniFiConfig
from unifi_mcp.server import UniFiMCPServer


def create_test_server(host: str, port: int) -> None:
    """Function to run server in subprocess for transport testing."""
    # Only run if we have integration config
    controller_url = os.getenv("UNIFI_URL", os.getenv("UNIFI_CONTROLLER_URL"))
    username = os.getenv("UNIFI_USERNAME")
    password = os.getenv("UNIFI_PASSWORD")

    if not all([controller_url, username, password]):
        return

    unifi_config = UniFiConfig(
        controller_url=controller_url,
        username=username,
        password=password,
        verify_ssl=os.getenv("UNIFI_VERIFY_SSL", "false").lower() == "true",
        is_udm_pro=os.getenv("UNIFI_IS_UDM_PRO", "true").lower() == "true",
    )

    server_config = ServerConfig(host=host, port=port)
    import asyncio

    server = UniFiMCPServer(unifi_config, server_config)
    asyncio.run(server.run())


@pytest.mark.integration
class TestUniFiMCPIntegration:
    """Integration tests requiring real UniFi controller."""

    async def test_real_controller_connection(self, integration_config):
        """Test connection to real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        client = UnifiControllerClient(integration_config)

        try:
            async with client:
                assert client.is_authenticated is True

                # Test basic functionality
                devices = await client.get_devices()
                assert isinstance(devices, (list, dict))

                clients = await client.get_clients()
                assert isinstance(clients, (list, dict))

        except Exception as e:
            pytest.fail(f"Real controller connection test failed: {e}")

    async def test_real_server_tools_execution(self, integration_config):
        """Test tool execution with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig(host="127.0.0.1", port=8001)
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                devices_result = await client.call_tool("unifi", {"action": "get_devices"})
                assert devices_result is not None

                clients_result = await client.call_tool("unifi", {"action": "get_clients"})
                assert clients_result is not None

        except Exception as e:
            pytest.fail(f"Real server tools execution test failed: {e}")
        finally:
            await server.cleanup()

    async def test_real_server_resources_access(self, integration_config):
        """Test resource access with real UniFi controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig(host="127.0.0.1", port=8001)
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                resources = await client.list_resources()
                assert len(resources) > 0

                devices_resource = next(
                    (r for r in resources if "unifi://devices" in str(r.uri)), None
                )
                if devices_resource:
                    content = await client.read_resource(devices_resource.uri)
                    assert content is not None
                    assert len(content) > 0

        except Exception as e:
            pytest.fail(f"Real server resources access test failed: {e}")
        finally:
            await server.cleanup()


@pytest.mark.integration
@pytest.mark.client_process
class TestUniFiMCPTransport:
    """Integration tests for HTTP transport with subprocess."""

    async def test_http_transport_with_real_controller(self, integration_config):
        """Test HTTP transport with real controller using subprocess."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        try:
            with run_server_in_process(create_test_server, transport="http") as server_url:
                from fastmcp.client.transports import StreamableHttpTransport

                async with Client(transport=StreamableHttpTransport(f"{server_url}/mcp")) as client:
                    # Test ping
                    ping_result = await client.ping()
                    assert ping_result is True

                    # Test tool execution over HTTP
                    devices_result = await client.call_tool("unifi", {"action": "get_devices"})
                    assert devices_result is not None

        except Exception as e:
            pytest.fail(f"HTTP transport test failed: {e}")

    async def test_server_lifecycle_management(self, integration_config):
        """Test server startup and shutdown with real controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        try:
            with run_server_in_process(create_test_server, transport="http") as server_url:
                from fastmcp.client.transports import StreamableHttpTransport

                # Test multiple connections
                async with Client(
                    transport=StreamableHttpTransport(f"{server_url}/mcp")
                ) as client1:
                    async with Client(
                        transport=StreamableHttpTransport(f"{server_url}/mcp")
                    ) as client2:
                        # Both clients should work
                        result1 = await client1.ping()
                        result2 = await client2.ping()

                        assert result1 is True
                        assert result2 is True

        except Exception as e:
            pytest.fail(f"Server lifecycle test failed: {e}")


@pytest.mark.integration
class TestUniFiMCPEndToEnd:
    """End-to-end integration tests."""

    async def test_complete_device_workflow(self, integration_config):
        """Test complete device management workflow."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig()
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                # 1. Get all devices
                devices_result = await client.call_tool("unifi", {"action": "get_devices"})
                assert devices_result is not None

                # 2. If we have devices, test individual device lookup
                _data = getattr(devices_result, "data", None) or {}
                device_items = _data.get("data", [])
                if isinstance(device_items, list) and len(device_items) > 0:
                    device_mac = device_items[0].get("mac")
                    if device_mac:
                        # Test device lookup
                        device_result = await client.call_tool(
                            "unifi", {"action": "get_device_by_mac", "mac": device_mac}
                        )
                        assert device_result is not None

                        # Test device resource
                        device_uri = f"unifi://device/default/{device_mac}"
                        device_content = await client.read_resource(device_uri)
                        assert device_content is not None

        except Exception as e:
            pytest.fail(f"Complete device workflow test failed: {e}")
        finally:
            await server.cleanup()

    async def test_complete_client_workflow(self, integration_config):
        """Test complete client management workflow."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig()
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                # 1. Get all clients
                clients_result = await client.call_tool("unifi", {"action": "get_clients"})
                assert clients_result is not None

                # 2. Test filtering
                online_result = await client.call_tool(
                    "unifi", {"action": "get_clients", "connected_only": True}
                )
                assert online_result is not None

                # 3. If we have clients, test individual client lookup
                client_items = getattr(clients_result, "data", {}).get("data", [])
                if isinstance(client_items, list) and len(client_items) > 0:
                    client_mac = client_items[0].get("mac")
                    if client_mac:
                        # Test client lookup
                        client_result = await client.call_tool(
                            "unifi", {"action": "get_client_by_mac", "mac": client_mac}
                        )
                        assert client_result is not None

        except Exception as e:
            pytest.fail(f"Complete client workflow test failed: {e}")
        finally:
            await server.cleanup()

    async def test_error_handling_with_real_controller(self, integration_config):
        """Test error handling scenarios with real controller."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig()
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                # Test with non-existent MAC addresses
                nonexistent_device = await client.call_tool(
                    "unifi", {"action": "get_device_by_mac", "mac": "ff:ff:ff:ff:ff:ff"}
                )
                assert nonexistent_device is not None
                # Should handle gracefully, not crash

                nonexistent_client = await client.call_tool(
                    "unifi", {"action": "get_client_by_mac", "mac": "ff:ff:ff:ff:ff:ff"}
                )
                assert nonexistent_client is not None

                # Test invalid site names
                invalid_site_devices = await client.call_tool(
                    "unifi", {"action": "get_devices", "site_name": "nonexistent-site"}
                )
                assert invalid_site_devices is not None

        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
        finally:
            await server.cleanup()


@pytest.mark.integration
@pytest.mark.slow
class TestUniFiMCPPerformance:
    """Performance and stress tests (marked as slow)."""

    async def test_concurrent_requests(self, integration_config):
        """Test concurrent request handling."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        import asyncio

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig()
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            async with Client(server.mcp) as client:
                # Make multiple concurrent requests
                tasks = []
                for _ in range(5):
                    tasks.append(client.call_tool("unifi", {"action": "get_devices"}))
                    tasks.append(client.call_tool("unifi", {"action": "get_clients"}))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All requests should complete successfully
                for result in results:
                    assert not isinstance(result, Exception), f"Concurrent request failed: {result}"
                    assert result is not None

        except Exception as e:
            pytest.fail(f"Concurrent requests test failed: {e}")
        finally:
            await server.cleanup()

    async def test_resource_cleanup(self, integration_config):
        """Test that resources are properly cleaned up."""
        if integration_config is None:
            pytest.skip("Integration test environment variables not set")

        from unifi_mcp.server import UniFiMCPServer

        server_config = ServerConfig()
        server = UniFiMCPServer(integration_config, server_config)

        try:
            await server.initialize()
            # Create and destroy multiple client connections
            for _ in range(3):
                async with Client(server.mcp) as client:
                    await client.ping()
                    result = await client.call_tool("unifi", {"action": "get_devices"})
                    assert result is not None
                # Connection should be cleaned up automatically

        except Exception as e:
            pytest.fail(f"Resource cleanup test failed: {e}")
        finally:
            await server.cleanup()


# Helper functions for integration tests
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring external resources"
    )
    config.addinivalue_line(
        "markers", "client_process: marks tests that spawn separate client processes"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running (>1 second)")
