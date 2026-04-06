"""
Comprehensive in-memory tests for the UniFi MCP unified tool.

Tests the single `unifi` tool with all available actions using FastMCP's
in-memory Client for zero-network-call testing. Mocks the UnifiControllerClient
at the service layer to isolate the MCP tool logic.
"""

import pytest
import pytest_asyncio  # noqa: F401 – needed for @pytest_asyncio.fixture
from unittest.mock import AsyncMock, patch
from typing import Any

from fastmcp import FastMCP, Client
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from unifi_mcp.config import UniFiConfig, ServerConfig
from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.server import UniFiMCPServer


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_DEVICES = [
    {
        "_id": "dev1",
        "name": "Core Switch",
        "mac": "aa:bb:cc:dd:ee:01",
        "model": "US-24-250W",
        "type": "usw",
        "state": 1,
        "ip": "192.168.1.10",
        "uptime": 86400,
        "bytes": 1_000_000_000,
        "rx_bytes": 500_000_000,
        "tx_bytes": 500_000_000,
        "cpu": 12.0,
        "mem": 40.0,
    },
    {
        "_id": "dev2",
        "name": "Bedroom AP",
        "mac": "aa:bb:cc:dd:ee:02",
        "model": "U6-Lite",
        "type": "uap",
        "state": 1,
        "ip": "192.168.1.11",
        "uptime": 43200,
        "bytes": 500_000_000,
        "rx_bytes": 250_000_000,
        "tx_bytes": 250_000_000,
        "cpu": 5.0,
        "mem": 22.0,
    },
]

MOCK_CLIENTS = [
    {
        "_id": "cli1",
        "name": "Alice's Laptop",
        "mac": "cc:dd:ee:ff:00:01",
        "ip": "192.168.1.101",
        "hostname": "alice-laptop",
        "is_online": True,
        "is_wired": True,
        "rx_bytes": 1_000_000,
        "tx_bytes": 2_000_000,
        "uptime": 3600,
        "last_seen": 1700000000,
    },
    {
        "_id": "cli2",
        "name": "Bob's Phone",
        "mac": "cc:dd:ee:ff:00:02",
        "ip": "192.168.1.102",
        "hostname": "bobs-phone",
        "is_online": True,
        "is_wired": False,
        "essid": "HomeWifi",
        "signal": -55,
        "rx_bytes": 300_000,
        "tx_bytes": 100_000,
        "uptime": 1800,
        "last_seen": 1700000100,
    },
]

MOCK_SITES = [
    {
        "_id": "site1",
        "name": "default",
        "desc": "Default",
        "role": "admin",
        "health": [{"subsystem": "wan", "status": "ok"}],
    }
]

MOCK_WLANS = [
    {
        "_id": "wlan1",
        "name": "HomeWifi",
        "enabled": True,
        "security": "wpapsk",
        "vlan_enabled": False,
    },
]

MOCK_NETWORKS = [
    {
        "_id": "net1",
        "name": "LAN",
        "purpose": "corporate",
        "ip_subnet": "192.168.1.1/24",
        "vlan": 1,
    },
]

MOCK_PORT_CONFIGS = [
    {"_id": "port1", "name": "All", "speed": 0, "duplex": 0},
]

MOCK_PORT_FORWARDING = [
    {
        "_id": "pf1",
        "name": "Plex",
        "proto": "tcp",
        "fwd": "192.168.1.50",
        "fwd_port": 32400,
        "dst_port": 32400,
        "enabled": True,
    },
]

MOCK_FIREWALL_RULES = [
    {
        "_id": "fw1",
        "name": "Block Guest",
        "ruleset": "LAN_IN",
        "action": "drop",
        "enabled": True,
    },
]

MOCK_FIREWALL_GROUPS = [
    {
        "_id": "fg1",
        "name": "Trusted IPs",
        "group_type": "address-group",
        "group_members": ["192.168.1.0/24"],
    },
]

MOCK_STATIC_ROUTES = [
    {
        "_id": "sr1",
        "name": "IoT Route",
        "nh_network_id": "net1",
        "dst_addr": "10.0.0.0/24",
        "enabled": True,
    },
]

MOCK_EVENTS = [
    {
        "_id": "evt1",
        "datetime": "2024-01-01T00:00:00Z",
        "key": "EVT_WU_Connected",
        "subsystem": "wlan",
        "site_id": "site1",
        "msg": "User connected",
    },
]

MOCK_ALARMS = [
    {
        "_id": "alm1",
        "datetime": "2024-01-01T00:00:00Z",
        "key": "EVT_AD_Crash",
        "subsystem": "lan",
        "msg": "Switch port down",
        "archived": False,
    },
]

MOCK_DPI_STATS = [
    {"app": 1, "cat": 1, "rx_bytes": 10000, "tx_bytes": 5000},
]

MOCK_ROGUE_APS = [
    {
        "_id": "rogue1",
        "essid": "EvilAP",
        "bssid": "ff:ff:ff:ff:ff:ff",
        "rssi": -70,
        "channel": 6,
    },
]

MOCK_SPEEDTEST = [
    {"time": 1700000000, "xput_download": 500.0, "xput_upload": 100.0, "latency": 5},
]

MOCK_IPS_EVENTS = [
    {
        "_id": "ips1",
        "datetime": "2024-01-01T00:00:00Z",
        "src_ip": "1.2.3.4",
        "dst_ip": "192.168.1.100",
        "signature": "ET SCAN",
        "action": "blocked",
    },
]

MOCK_CONTROLLER_STATUS = {
    "meta": {"rc": "ok", "up": True, "server_version": "8.0.0"},
    "data": [{"is_default": True}],
}

MOCK_USERS_LIST = [
    {"_id": "user1", "mac": "cc:dd:ee:ff:00:01", "name": "Alice's Laptop"},
    {"_id": "user2", "mac": "cc:dd:ee:ff:00:02", "name": "Bob's Phone"},
]

MOCK_CMD_RESPONSE = {"meta": {"rc": "ok"}, "data": []}
MOCK_SPECTRUM_SCAN = {"meta": {"rc": "ok"}, "data": [{"state": "scanning"}]}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _build_mock_client() -> AsyncMock:
    """Build a fully-configured mock UnifiControllerClient."""
    mock = AsyncMock(spec=UnifiControllerClient)
    mock.is_authenticated = True
    mock.csrf_token = "test-csrf"
    mock.config = UniFiConfig(
        controller_url="https://192.168.1.1",
        username="admin",
        password="password",
        verify_ssl=False,
        is_udm_pro=True,
    )

    # Core methods
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.authenticate = AsyncMock(return_value=True)

    # Data methods
    mock.get_devices = AsyncMock(return_value=MOCK_DEVICES)
    mock.get_clients = AsyncMock(return_value=MOCK_CLIENTS)
    mock.get_sites = AsyncMock(return_value=MOCK_SITES)
    mock.get_wlan_configs = AsyncMock(return_value=MOCK_WLANS)
    mock.get_network_configs = AsyncMock(return_value=MOCK_NETWORKS)
    mock.get_port_configs = AsyncMock(return_value=MOCK_PORT_CONFIGS)
    mock.get_port_forwarding_rules = AsyncMock(return_value=MOCK_PORT_FORWARDING)
    mock.get_events = AsyncMock(return_value=MOCK_EVENTS)
    mock.get_alarms = AsyncMock(return_value=MOCK_ALARMS)
    mock.get_dpi_stats = AsyncMock(return_value=MOCK_DPI_STATS)
    mock.get_rogue_aps = AsyncMock(return_value=MOCK_ROGUE_APS)
    mock.get_speedtest_results = AsyncMock(return_value=MOCK_SPEEDTEST)

    # Command methods
    mock.restart_device = AsyncMock(return_value=MOCK_CMD_RESPONSE)
    mock.locate_device = AsyncMock(return_value=MOCK_CMD_RESPONSE)
    mock.reconnect_client = AsyncMock(return_value=MOCK_CMD_RESPONSE)

    # Low-level request method (used by some service operations)
    async def _make_request_side_effect(method: str, path: str, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})

        # Controller status
        if path == "/status":
            return MOCK_CONTROLLER_STATUS

        # Block/unblock/forget client commands
        if path == "/cmd/stamgr":
            cmd = data.get("cmd", "")
            if cmd in ("block-sta", "unblock-sta", "forget-sta", "kick-sta"):
                return MOCK_CMD_RESPONSE
            return MOCK_CMD_RESPONSE

        # set_client_name / set_client_note – user list lookup
        if method == "GET" and path == "/list/user":
            return MOCK_USERS_LIST

        # set_client_name / set_client_note – update call
        if method == "POST" and path.startswith("/upd/user/"):
            return MOCK_CMD_RESPONSE

        # Spectrum scan
        if "/cmd/devmgr" in path:
            return MOCK_CMD_RESPONSE

        # Spectrum scan state
        if "/stat/spectrum-scan" in path:
            return MOCK_SPECTRUM_SCAN

        # Authorize guest
        if "/cmd/hotspot" in path:
            return MOCK_CMD_RESPONSE

        # IPS events
        if "/stat/ips/event" in path:
            return MOCK_IPS_EVENTS

        # Speedtest
        if "/stat/report/archive.speedtest" in path:
            return MOCK_SPEEDTEST

        # Firewall rules
        if "/rest/firewallrule" in path:
            return MOCK_FIREWALL_RULES

        # Firewall groups
        if "/rest/firewallgroup" in path:
            return MOCK_FIREWALL_GROUPS

        # Static routes
        if "/rest/routing" in path:
            return MOCK_STATIC_ROUTES

        # Port forwarding
        if "/list/portforward" in path:
            return MOCK_PORT_FORWARDING

        # DPI stats
        if "/stat/dpi" in path:
            return MOCK_DPI_STATS

        # Events
        if "/stat/event" in path:
            return MOCK_EVENTS

        # Rogue APs
        if "/stat/rogueap" in path:
            return MOCK_ROGUE_APS

        return {"meta": {"rc": "ok"}, "data": []}

    mock._make_request = AsyncMock(side_effect=_make_request_side_effect)

    return mock


@pytest.fixture
def unifi_config() -> UniFiConfig:
    return UniFiConfig(
        controller_url="https://192.168.1.1",
        username="admin",
        password="password",
        verify_ssl=False,
        is_udm_pro=True,
    )


@pytest.fixture
def server_config() -> ServerConfig:
    return ServerConfig(host="127.0.0.1", port=8001, log_level="DEBUG", log_file=None)


@pytest_asyncio.fixture
async def mcp_server(unifi_config: UniFiConfig, server_config: ServerConfig) -> FastMCP:
    """Create a fully initialized FastMCP server backed by a mock UniFi client."""
    mock_client = _build_mock_client()

    with patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_client):
        server = UniFiMCPServer(unifi_config, server_config)
        await server.initialize()
        yield server.mcp
        await server.cleanup()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text(result: ToolResult) -> str:
    """Extract first text content from ToolResult."""
    assert result.content, "ToolResult has no content"
    item = result.content[0]
    assert isinstance(item, TextContent), f"Expected TextContent, got {type(item)}"
    return item.text


def _is_error(result: ToolResult) -> bool:
    """Return True if the result represents an error.

    Handles both direct "Error: ..." text responses and cases where
    the error is captured in structured_content (e.g. pydantic validation
    failures that the tool catches and wraps).
    """
    text = _text(result).lower()
    if text.startswith("error"):
        return True
    # Pydantic/service errors are captured as structured_content{"error": ...}
    sc = result.structured_content
    if isinstance(sc, dict) and "error" in sc:
        return True
    return False


def _data(result: ToolResult) -> Any:
    """Extract the data payload from a success ToolResult.

    The service layer wraps list results in::

        {"success": True, "message": "...", "data": [...]}

    This helper unwraps that envelope so tests can assert on the actual data.
    """
    sc = result.structured_content
    if isinstance(sc, dict) and "data" in sc:
        return sc["data"]
    return sc


# ===========================================================================
# Tool registration
# ===========================================================================


class TestToolRegistration:
    """Verify the unified tool is registered and properly described."""

    @pytest.mark.asyncio
    async def test_only_one_tool_registered(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
        assert len(tools) == 1

    @pytest.mark.asyncio
    async def test_tool_name_is_unifi(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
        assert tools[0].name == "unifi"

    @pytest.mark.asyncio
    async def test_tool_has_action_parameter(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
        schema = tools[0].inputSchema
        assert "action" in schema.get("properties", {})

    @pytest.mark.asyncio
    async def test_tool_has_optional_parameters(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
        schema = tools[0].inputSchema
        props = schema.get("properties", {})
        for param in ("mac", "limit", "site_name", "connected_only", "name", "note"):
            assert param in props, f"Expected parameter '{param}' in schema"

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "not_a_real_action"})
        assert not isinstance(result, Exception)
        text = _text(result).lower()
        assert "invalid action" in text or "available actions" in text


# ===========================================================================
# Device actions
# ===========================================================================


class TestDeviceActions:
    """Tests for device management actions."""

    @pytest.mark.asyncio
    async def test_get_devices_returns_list(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})
        assert not _is_error(result)
        devices = _data(result)
        assert isinstance(devices, list)
        assert len(devices) == 2

    @pytest.mark.asyncio
    async def test_get_devices_has_required_fields(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})
        devices = _data(result)
        assert isinstance(devices, list)
        first = devices[0]
        assert isinstance(first, dict)
        for field in ("name", "type", "status"):
            assert field in first, f"Expected field '{field}' in device summary"

    @pytest.mark.asyncio
    async def test_get_devices_with_custom_site(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_devices", "site_name": "office"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_device_by_mac_found(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "aa:bb:cc:dd:ee:01"}
            )
        assert not _is_error(result)
        assert isinstance(result.structured_content, dict)
        assert result.structured_content.get("name") == "Core Switch"

    @pytest.mark.asyncio
    async def test_get_device_by_mac_normalizes_format(
        self, mcp_server: FastMCP
    ) -> None:
        """MAC in uppercase dash format should still match."""
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "AA-BB-CC-DD-EE-01"}
            )
        assert not _is_error(result)
        assert isinstance(result.structured_content, dict)
        assert result.structured_content.get("name") == "Core Switch"

    @pytest.mark.asyncio
    async def test_get_device_by_mac_not_found(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "ff:ff:ff:ff:ff:ff"}
            )
        assert _is_error(result)

    @pytest.mark.asyncio
    async def test_restart_device_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "restart_device", "mac": "aa:bb:cc:dd:ee:01"}
            )
        assert not _is_error(result)
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert sc.get("success") is True

    @pytest.mark.asyncio
    async def test_locate_device_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "locate_device", "mac": "aa:bb:cc:dd:ee:02"}
            )
        assert not _is_error(result)
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert sc.get("success") is True

    @pytest.mark.asyncio
    async def test_device_actions_require_mac(self, mcp_server: FastMCP) -> None:
        """Actions that need a MAC should return an error when not supplied."""
        for action in ("restart_device", "locate_device", "get_device_by_mac"):
            async with Client(mcp_server) as client:
                result = await client.call_tool("unifi", {"action": action})
            assert _is_error(result), f"Expected error for {action} without mac"


# ===========================================================================
# Client actions
# ===========================================================================


class TestClientActions:
    """Tests for client management actions."""

    @pytest.mark.asyncio
    async def test_get_clients_returns_list(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_clients"})
        assert not _is_error(result)
        assert isinstance(_data(result), list)

    @pytest.mark.asyncio
    async def test_get_clients_connected_only_default(
        self, mcp_server: FastMCP
    ) -> None:
        """By default connected_only=True; both mock clients are online."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_clients"})
        assert not _is_error(result)
        clients = _data(result)
        assert isinstance(clients, list)
        # Both mock clients have is_online=True
        assert len(clients) == 2

    @pytest.mark.asyncio
    async def test_get_clients_with_connected_only_false(
        self, mcp_server: FastMCP
    ) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_clients", "connected_only": False}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_block_client_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "block_client", "mac": "cc:dd:ee:ff:00:01"}
            )
        assert not _is_error(result)
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert sc.get("success") is True

    @pytest.mark.asyncio
    async def test_unblock_client_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "unblock_client", "mac": "cc:dd:ee:ff:00:01"}
            )
        assert not _is_error(result)
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert sc.get("success") is True

    @pytest.mark.asyncio
    async def test_forget_client_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "forget_client", "mac": "cc:dd:ee:ff:00:01"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_reconnect_client_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "reconnect_client", "mac": "cc:dd:ee:ff:00:02"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_set_client_name_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi",
                {
                    "action": "set_client_name",
                    "mac": "cc:dd:ee:ff:00:01",
                    "name": "Alice Work",
                },
            )
        assert not _is_error(result)
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert sc.get("success") is True

    @pytest.mark.asyncio
    async def test_set_client_name_client_not_found(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi",
                {
                    "action": "set_client_name",
                    "mac": "ff:ff:ff:ff:ff:ff",
                    "name": "Ghost",
                },
            )
        # Should return a graceful "client not found" result (not a crash)
        assert result.content

    @pytest.mark.asyncio
    async def test_set_client_note_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi",
                {
                    "action": "set_client_note",
                    "mac": "cc:dd:ee:ff:00:02",
                    "note": "Bob's personal phone",
                },
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_client_actions_require_mac(self, mcp_server: FastMCP) -> None:
        for action in (
            "block_client",
            "unblock_client",
            "forget_client",
            "reconnect_client",
            "set_client_name",
            "set_client_note",
        ):
            async with Client(mcp_server) as client:
                result = await client.call_tool("unifi", {"action": action})
            assert _is_error(result), f"Expected error for {action} without mac"


# ===========================================================================
# Network actions
# ===========================================================================


class TestNetworkActions:
    """Tests for network configuration actions."""

    @pytest.mark.asyncio
    async def test_get_sites_returns_list(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_sites"})
        assert not _is_error(result)
        assert result.content

    @pytest.mark.asyncio
    async def test_get_wlan_configs_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_wlan_configs"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_network_configs_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_network_configs"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_port_configs_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_port_configs"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_port_forwarding_rules_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_port_forwarding_rules"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_firewall_rules_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_firewall_rules"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_firewall_groups_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_firewall_groups"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_static_routes_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_static_routes"})
        assert not _is_error(result)


# ===========================================================================
# Monitoring actions
# ===========================================================================


class TestMonitoringActions:
    """Tests for monitoring and statistics actions."""

    @pytest.mark.asyncio
    async def test_get_controller_status_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_controller_status"}
            )
        assert not _is_error(result)
        assert result.content

    @pytest.mark.asyncio
    async def test_get_events_returns_list(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_events"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_events_with_limit(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_events", "limit": 10}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_alarms_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_alarms"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_alarms_active_only(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_alarms", "active_only": True}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_dpi_stats_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_dpi_stats"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_dpi_stats_by_cat(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_dpi_stats", "by_filter": "by_cat"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_rogue_aps_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_rogue_aps"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_speedtest_results_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_speedtest_results"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_get_ips_events_success(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_ips_events"})
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_start_spectrum_scan_requires_mac(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "start_spectrum_scan"})
        assert _is_error(result)

    @pytest.mark.asyncio
    async def test_start_spectrum_scan_with_mac(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "start_spectrum_scan", "mac": "aa:bb:cc:dd:ee:02"}
            )
        # Should not crash (may succeed or return API error)
        assert result.content

    @pytest.mark.asyncio
    async def test_get_spectrum_scan_state_with_mac(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi",
                {"action": "get_spectrum_scan_state", "mac": "aa:bb:cc:dd:ee:02"},
            )
        assert result.content

    @pytest.mark.asyncio
    async def test_authorize_guest_requires_mac(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "authorize_guest"})
        assert _is_error(result)

    @pytest.mark.asyncio
    async def test_authorize_guest_with_all_params(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi",
                {
                    "action": "authorize_guest",
                    "mac": "cc:dd:ee:ff:00:02",
                    "minutes": 60,
                    "up_bandwidth": 5000,
                    "down_bandwidth": 10000,
                    "quota": 500,
                },
            )
        assert result.content


# ===========================================================================
# Error handling
# ===========================================================================


class TestErrorHandling:
    """Tests for graceful error handling in the unified tool."""

    @pytest.mark.asyncio
    async def test_api_failure_returns_error_result(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        """When the API client raises an exception the tool returns an error ToolResult."""
        failing_client = _build_mock_client()
        failing_client.get_devices = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        with patch(
            "unifi_mcp.server.UnifiControllerClient", return_value=failing_client
        ):
            server = UniFiMCPServer(unifi_config, server_config)
            await server.initialize()
            try:
                async with Client(server.mcp) as client:
                    result = await client.call_tool("unifi", {"action": "get_devices"})
                assert _is_error(result)
            finally:
                await server.cleanup()

    @pytest.mark.asyncio
    async def test_empty_device_list_handled(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        empty_client = _build_mock_client()
        empty_client.get_devices = AsyncMock(return_value=[])

        with patch("unifi_mcp.server.UnifiControllerClient", return_value=empty_client):
            server = UniFiMCPServer(unifi_config, server_config)
            await server.initialize()
            try:
                async with Client(server.mcp) as client:
                    result = await client.call_tool("unifi", {"action": "get_devices"})
                assert not _is_error(result)
                devices = _data(result)
                assert isinstance(devices, list)
                assert len(devices) == 0
            finally:
                await server.cleanup()

    @pytest.mark.asyncio
    async def test_api_error_dict_returned_as_error(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        """When the API client returns an error dict the tool returns an error."""
        error_client = _build_mock_client()
        error_client.get_clients = AsyncMock(return_value={"error": "Unauthorized"})

        with patch("unifi_mcp.server.UnifiControllerClient", return_value=error_client):
            server = UniFiMCPServer(unifi_config, server_config)
            await server.initialize()
            try:
                async with Client(server.mcp) as client:
                    result = await client.call_tool("unifi", {"action": "get_clients"})
                assert _is_error(result)
            finally:
                await server.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_mac_format_returns_error(self, mcp_server: FastMCP) -> None:
        """A badly-formatted MAC should produce an error, not a crash."""
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "not-a-mac"}
            )
        assert result.content  # Should return something (error or not-found)

    @pytest.mark.asyncio
    async def test_result_always_has_text_content(self, mcp_server: FastMCP) -> None:
        """Every tool call result should have at least one TextContent item."""
        actions_to_test = [
            {"action": "get_devices"},
            {"action": "get_clients"},
            {"action": "get_sites"},
            {"action": "get_controller_status"},
            {"action": "invalid_action"},
        ]
        async with Client(mcp_server) as client:
            for args in actions_to_test:
                result = await client.call_tool("unifi", args)
                assert len(result.content) > 0, f"No content for {args}"
                assert isinstance(result.content[0], TextContent), (
                    f"Expected TextContent for {args}, got {type(result.content[0])}"
                )

    @pytest.mark.asyncio
    async def test_structured_content_present_on_success(
        self, mcp_server: FastMCP
    ) -> None:
        """Successful responses should include structured_content."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})
        assert not _is_error(result)
        assert result.structured_content is not None

    @pytest.mark.asyncio
    async def test_invalid_action_lists_valid_actions(
        self, mcp_server: FastMCP
    ) -> None:
        """The error message for an invalid action should list valid options."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "does_not_exist"})
        text = _text(result).lower()
        assert "action" in text


# ===========================================================================
# Data integrity
# ===========================================================================


class TestDataIntegrity:
    """Tests verifying data shapes and types in tool responses."""

    @pytest.mark.asyncio
    async def test_device_summary_has_mac(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})
        devices = _data(result)
        assert isinstance(devices, list)
        for device in devices:
            assert isinstance(device, dict)
            assert "mac" in device

    @pytest.mark.asyncio
    async def test_device_summary_type_is_human_readable(
        self, mcp_server: FastMCP
    ) -> None:
        """Device type should be formatted as human-readable (e.g. 'Switch', not 'usw')."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_devices"})
        devices = _data(result)
        assert isinstance(devices, list)
        switch = next(d for d in devices if "Core Switch" in d.get("name", ""))
        # The formatter should produce something human-readable (not the raw type code)
        device_type = switch.get("type", "")
        assert device_type != "usw", (
            "Expected human-readable type, got raw API code 'usw'"
        )

    @pytest.mark.asyncio
    async def test_get_clients_structured_content_is_list(
        self, mcp_server: FastMCP
    ) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool("unifi", {"action": "get_clients"})
        assert isinstance(_data(result), list)

    @pytest.mark.asyncio
    async def test_get_device_by_mac_structured_content_is_dict(
        self, mcp_server: FastMCP
    ) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "aa:bb:cc:dd:ee:02"}
            )
        assert not _is_error(result)
        assert isinstance(result.structured_content, dict)
        assert result.structured_content.get("name") == "Bedroom AP"

    @pytest.mark.asyncio
    async def test_restart_device_response_shape(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "restart_device", "mac": "aa:bb:cc:dd:ee:01"}
            )
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert "success" in sc
        assert sc["success"] is True

    @pytest.mark.asyncio
    async def test_block_client_response_includes_mac(
        self, mcp_server: FastMCP
    ) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "block_client", "mac": "cc:dd:ee:ff:00:01"}
            )
        sc = result.structured_content
        assert isinstance(sc, dict)
        assert "mac" in sc
        # MAC should be normalised to colon format
        assert sc["mac"] == "cc:dd:ee:ff:00:01"


# ===========================================================================
# MAC normalisation
# ===========================================================================


class TestMacNormalisation:
    """Tests covering MAC address format normalisation end-to-end."""

    @pytest.mark.asyncio
    async def test_uppercase_mac_resolves_device(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "AA:BB:CC:DD:EE:02"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_dash_separated_mac_resolves_device(
        self, mcp_server: FastMCP
    ) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "aa-bb-cc-dd-ee-02"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_dot_separated_mac_resolves_device(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "get_device_by_mac", "mac": "aa.bb.cc.dd.ee.02"}
            )
        assert not _is_error(result)

    @pytest.mark.asyncio
    async def test_mixed_case_mac_resolves_client(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "unifi", {"action": "block_client", "mac": "CC:DD:EE:FF:00:01"}
            )
        assert not _is_error(result)


# ===========================================================================
# Server lifecycle
# ===========================================================================


class TestServerLifecycle:
    """Tests covering server initialization and teardown."""

    def test_server_creates_fastmcp_instance(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        mock_client = _build_mock_client()
        with patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_client):
            server = UniFiMCPServer(unifi_config, server_config)
        assert isinstance(server.mcp, FastMCP)

    def test_server_name(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        mock_client = _build_mock_client()
        with patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_client):
            server = UniFiMCPServer(unifi_config, server_config)
        assert "UniFi" in server.mcp.name

    def test_auth_disabled_by_default(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        import os

        mock_client = _build_mock_client()
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "unifi_mcp.server.UnifiControllerClient", return_value=mock_client
            ):
                server = UniFiMCPServer(unifi_config, server_config)
        assert server._auth_enabled is False

    @pytest.mark.asyncio
    async def test_server_initializes_and_registers_tool(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        mock_client = _build_mock_client()
        with patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_client):
            server = UniFiMCPServer(unifi_config, server_config)
            await server.initialize()
            try:
                async with Client(server.mcp) as client:
                    tools = await client.list_tools()
                assert any(t.name == "unifi" for t in tools)
            finally:
                await server.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup_disconnects_client(
        self, unifi_config: UniFiConfig, server_config: ServerConfig
    ) -> None:
        mock_client = _build_mock_client()
        with patch("unifi_mcp.server.UnifiControllerClient", return_value=mock_client):
            server = UniFiMCPServer(unifi_config, server_config)
            await server.initialize()
            await server.cleanup()
        mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_server_ping(self, mcp_server: FastMCP) -> None:
        async with Client(mcp_server) as client:
            result = await client.ping()
        assert result is True
