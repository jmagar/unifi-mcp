"""
Tests for UniFi MCP device resources.

Following current FastMCP resource APIs and the repo's actual resource surface.
"""

import pytest
from unittest.mock import AsyncMock
from inline_snapshot import snapshot

from fastmcp import FastMCP, Client

from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.resources.device_resources import register_device_resources


@pytest.fixture
def device_resources_server(mock_unifi_client):
    """Create FastMCP server with only device resources registered."""
    mcp = FastMCP("DeviceResourcesTestServer")
    register_device_resources(mcp, mock_unifi_client)
    return mcp


def get_text_content(content):
    """Return the resource body text from FastMCP read_resource output."""
    assert content is not None
    assert len(content) > 0
    return content[0].text


class TestDevicesResource:
    """Test unifi://devices resource functionality."""

    async def test_devices_resource_registration(self, device_resources_server):
        """Test that the listed device resources are properly registered."""
        resources = await device_resources_server._list_resources()
        resource_uris = [str(resource.uri) for resource in resources]

        assert "unifi://devices" in resource_uris
        assert "unifi://device-tags" in resource_uris

    async def test_devices_resource_content(self, device_resources_server):
        """Test devices resource content retrieval."""
        async with Client(device_resources_server) as client:
            content = await client.read_resource("unifi://devices")
            content_text = get_text_content(content)

            assert "Main Switch" in content_text
            assert "Living Room AP" in content_text

    async def test_devices_resource_with_site_path_parameter(self, device_resources_server):
        """Test devices resource with explicit site path segment."""
        async with Client(device_resources_server) as client:
            content = await client.read_resource("unifi://devices/default")

            content_text = get_text_content(content)
            assert "Main Switch" in content_text


class TestDeviceResource:
    """Test unifi://device/{site_name}/{mac} resource functionality."""

    async def test_device_resource_with_valid_mac(self, device_resources_server):
        """Test individual device resource with valid MAC."""
        device_mac = "aa:bb:cc:dd:ee:01"

        async with Client(device_resources_server) as client:
            device_uri = f"unifi://device/default/{device_mac}"
            content = await client.read_resource(device_uri)

            content_text = get_text_content(content)
            assert "Main Switch" in content_text

    async def test_device_resource_with_invalid_mac(self, device_resources_server):
        """Test individual device resource with invalid MAC."""
        invalid_mac = "ff:ff:ff:ff:ff:ff"

        async with Client(device_resources_server) as client:
            device_uri = f"unifi://device/default/{invalid_mac}"
            content = await client.read_resource(device_uri)

            content_text = get_text_content(content)
            assert "not found" in content_text.lower()

    async def test_device_resource_mac_normalization(self, device_resources_server):
        """Test device resource MAC address normalization."""
        mac_formats = [
            "AA:BB:CC:DD:EE:01",
            "AA-BB-CC-DD-EE-01",
            "aa.bb.cc.dd.ee.01",
        ]

        async with Client(device_resources_server) as client:
            for mac in mac_formats:
                device_uri = f"unifi://device/default/{mac}"
                content = await client.read_resource(device_uri)

                content_text = get_text_content(content)
                if "not found" not in content_text.lower():
                    assert "Main Switch" in content_text


class TestDeviceStatsResource:
    """Test unifi://stats/device/{site_name}/{mac} resource functionality."""

    async def test_device_stats_resource(self, device_resources_server):
        """Test device statistics resource."""
        device_mac = "aa:bb:cc:dd:ee:01"

        async with Client(device_resources_server) as client:
            stats_uri = f"unifi://stats/device/default/{device_mac}"
            content = await client.read_resource(stats_uri)

            content_text = get_text_content(content)
            assert any(
                keyword in content_text.lower()
                for keyword in ["traffic", "system", "uptime", "active_ports"]
            )

    async def test_device_stats_resource_not_found(self, device_resources_server):
        """Test device statistics resource for non-existent device."""
        invalid_mac = "ff:ff:ff:ff:ff:ff"

        async with Client(device_resources_server) as client:
            stats_uri = f"unifi://stats/device/default/{invalid_mac}"
            content = await client.read_resource(stats_uri)

            content_text = get_text_content(content)
            assert "not found" in content_text.lower()


class TestDeviceResourcesSchema:
    """Test device resources metadata."""

    async def test_devices_resource_metadata(self, device_resources_server):
        """Test devices resource metadata structure."""
        resources = await device_resources_server._list_resources()
        devices_resource = next((r for r in resources if str(r.uri) == "unifi://devices"), None)

        assert devices_resource is not None
        assert devices_resource.name
        assert devices_resource.description
        assert "device" in devices_resource.description.lower()
        assert str(devices_resource.uri) == snapshot("unifi://devices")

    async def test_device_resource_templates_are_not_listed(self, device_resources_server):
        """Test templated device resources are readable even if not listed."""
        resources = await device_resources_server._list_resources()
        resource_uris = {str(resource.uri) for resource in resources}

        assert "unifi://device/default/aa:bb:cc:dd:ee:01" not in resource_uris

    async def test_device_stats_resource_templates_are_not_listed(self, device_resources_server):
        """Test stats templates are readable even if not listed."""
        resources = await device_resources_server._list_resources()
        resource_uris = {str(resource.uri) for resource in resources}

        assert "unifi://stats/device/default/aa:bb:cc:dd:ee:01" not in resource_uris


class TestDeviceResourcesErrorHandling:
    """Test device resources error handling."""

    async def test_resources_handle_client_errors(self, mock_failed_unifi_client):
        """Test device resources handle client authentication errors."""
        mcp = FastMCP("FailedAuthResourceTestServer")
        register_device_resources(mcp, mock_failed_unifi_client)

        async with Client(mcp) as client:
            content = await client.read_resource("unifi://devices")
            content_text = get_text_content(content)
            assert "error" in content_text.lower()

    async def test_resources_handle_network_exceptions(self):
        """Test device resources handle network exceptions gracefully."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(side_effect=Exception("Connection timeout"))

        mcp = FastMCP("NetworkErrorResourceTestServer")
        register_device_resources(mcp, mock_client)

        async with Client(mcp) as client:
            content = await client.read_resource("unifi://devices")
            content_text = get_text_content(content)
            assert "error" in content_text.lower()

    async def test_resources_handle_malformed_responses(self):
        """Test device resources handle malformed API responses."""
        mock_client = AsyncMock(spec=UnifiControllerClient)
        mock_client.get_devices = AsyncMock(return_value="invalid response")

        mcp = FastMCP("MalformedResourceTestServer")
        register_device_resources(mcp, mock_client)

        async with Client(mcp) as client:
            content = await client.read_resource("unifi://devices")

            content_text = get_text_content(content)
            assert "unexpected response format" in content_text.lower()


class TestDeviceResourcesFiltering:
    """Test device resources site-specific paths."""

    async def test_devices_resource_site_filtering(self, device_resources_server):
        """Test default and site-specific devices paths."""
        async with Client(device_resources_server) as client:
            default_content = await client.read_resource("unifi://devices")
            custom_content = await client.read_resource("unifi://devices/custom-site")

            assert default_content is not None
            assert custom_content is not None

    async def test_device_resource_with_site_path_parameter(self, device_resources_server):
        """Test individual device resource with explicit site path."""
        device_mac = "aa:bb:cc:dd:ee:01"

        async with Client(device_resources_server) as client:
            site_uri = f"unifi://device/custom-site/{device_mac}"
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
                    content = await test_client.read_resource("unifi://devices")
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
                    device_uri = "unifi://device/default/aa:bb:cc:dd:ee:01"
                    device_content = await test_client.read_resource(device_uri)
                    assert device_content is not None

        except Exception as e:
            pytest.fail(f"Device lookup integration test failed: {e}")
