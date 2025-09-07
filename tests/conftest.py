"""
Shared test fixtures and configuration for UniFi MCP Server tests.

Following FastMCP testing patterns for reusable test resources.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List, Optional
import httpx
from fastmcp import FastMCP, Client

from unifi_mcp.config import UniFiConfig, ServerConfig
from unifi_mcp.client import UnifiControllerClient
from unifi_mcp.server import UniFiMCPServer


@pytest.fixture
def test_unifi_config() -> UniFiConfig:
    """Test UniFi configuration."""
    return UniFiConfig(
        controller_url="https://192.168.1.1:443",
        username="admin",
        password="password123",
        verify_ssl=False,
        is_udm_pro=True
    )


@pytest.fixture
def test_legacy_unifi_config() -> UniFiConfig:
    """Test legacy UniFi configuration."""
    return UniFiConfig(
        controller_url="https://192.168.1.1:8443",
        username="admin",
        password="password123",
        verify_ssl=False,
        is_udm_pro=False
    )


@pytest.fixture
def test_server_config() -> ServerConfig:
    """Test server configuration."""
    return ServerConfig(
        host="127.0.0.1",
        port=8001,
        log_level="DEBUG",
        log_file=None
    )


@pytest.fixture
def mock_device_data() -> List[Dict[str, Any]]:
    """Mock device data for testing."""
    return [
        {
            "_id": "device1",
            "name": "Main Switch",
            "mac": "aa:bb:cc:dd:ee:01",
            "model": "US-24-250W",
            "type": "usw",
            "state": 1,
            "ip": "192.168.1.10",
            "uptime": 86400,
            "bytes": 1000000000,
            "rx_bytes": 500000000,
            "tx_bytes": 500000000,
            "cpu": 15.5,
            "mem": 45.2,
            "temperature": 42.1,
            "port_overrides": [],
            "port_table": [
                {"port_idx": 1, "name": "Port 1", "up": True},
                {"port_idx": 2, "name": "Port 2", "up": False}
            ]
        },
        {
            "_id": "device2", 
            "name": "Living Room AP",
            "mac": "aa:bb:cc:dd:ee:02",
            "model": "U6-Pro",
            "type": "uap",
            "state": 1,
            "ip": "192.168.1.11",
            "uptime": 43200,
            "bytes": 2000000000,
            "rx_bytes": 1200000000,
            "tx_bytes": 800000000,
            "cpu": 8.3,
            "mem": 32.1,
            "temperature": 38.5,
            "radio_table": [
                {"name": "wifi0", "channel": 36, "tx_power": 20},
                {"name": "wifi1", "channel": 6, "tx_power": 17}
            ]
        }
    ]


@pytest.fixture
def mock_client_data() -> List[Dict[str, Any]]:
    """Mock client data for testing."""
    return [
        {
            "_id": "client1",
            "name": "John's iPhone",
            "mac": "aa:bb:cc:dd:ee:f1",
            "ip": "192.168.1.100",
            "hostname": "Johns-iPhone",
            "is_online": True,
            "is_wired": False,
            "ap_mac": "aa:bb:cc:dd:ee:02",
            "essid": "HomeWiFi",
            "channel": 36,
            "signal": -45,
            "rx_bytes": 1000000,
            "tx_bytes": 2000000,
            "uptime": 7200,
            "last_seen": 1640995200,
            "user_id": "user1",
            "first_seen": 1640908800,
            "satisfaction": 95,
            "anomalies": 0
        },
        {
            "_id": "client2",
            "name": "Desktop PC",
            "mac": "aa:bb:cc:dd:ee:f2", 
            "ip": "192.168.1.101",
            "hostname": "desktop-pc",
            "is_online": True,
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:01",
            "sw_port": 1,
            "rx_bytes": 5000000,
            "tx_bytes": 3000000,
            "uptime": 25200,
            "last_seen": 1640995200,
            "user_id": "user2",
            "first_seen": 1640822400,
            "satisfaction": 100,
            "anomalies": 0
        }
    ]


@pytest.fixture
def mock_network_data() -> List[Dict[str, Any]]:
    """Mock network configuration data."""
    return [
        {
            "_id": "net1",
            "name": "LAN",
            "purpose": "corporate",
            "ip_subnet": "192.168.1.1/24",
            "vlan": 1,
            "dhcp_enabled": True,
            "dhcp_start": "192.168.1.100",
            "dhcp_stop": "192.168.1.200",
            "dhcp_lease": 86400
        },
        {
            "_id": "net2", 
            "name": "Guest",
            "purpose": "guest",
            "ip_subnet": "192.168.2.1/24",
            "vlan": 10,
            "dhcp_enabled": True,
            "dhcp_start": "192.168.2.100",
            "dhcp_stop": "192.168.2.200",
            "dhcp_lease": 3600
        }
    ]


@pytest.fixture
def mock_site_data() -> Dict[str, Any]:
    """Mock site data."""
    return {
        "_id": "site1",
        "name": "default",
        "desc": "Default Site",
        "role": "admin",
        "num_new_alarms": 0,
        "health": [
            {"subsystem": "wan", "status": "ok"},
            {"subsystem": "lan", "status": "ok"},
            {"subsystem": "wlan", "status": "warning"}
        ]
    }


@pytest.fixture
def mock_unifi_client(test_unifi_config, mock_device_data, mock_client_data, mock_network_data, mock_site_data):
    """Mock UniFi client with standard responses."""
    mock_client = AsyncMock(spec=UnifiControllerClient)
    mock_client.config = test_unifi_config
    mock_client.is_authenticated = True
    mock_client.csrf_token = "test-csrf-token"
    
    # Mock authentication methods
    mock_client.authenticate = AsyncMock(return_value=True)
    mock_client.ensure_authenticated = AsyncMock(return_value=True)
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    
    # Mock API methods
    mock_client.get_devices = AsyncMock(return_value=mock_device_data)
    mock_client.get_clients = AsyncMock(return_value=mock_client_data)
    mock_client.get_networks = AsyncMock(return_value=mock_network_data)
    mock_client.get_sites = AsyncMock(return_value=[mock_site_data])
    mock_client.get_site = AsyncMock(return_value=mock_site_data)
    
    # Mock device management methods
    mock_client.restart_device = AsyncMock(return_value={"message": "Device restart initiated"})
    mock_client.locate_device = AsyncMock(return_value={"message": "Device locate started"})
    mock_client.get_device_stats = AsyncMock(return_value={"stats": "mock_stats"})
    
    # Mock client management methods
    mock_client.block_client = AsyncMock(return_value={"message": "Client blocked"})
    mock_client.unblock_client = AsyncMock(return_value={"message": "Client unblocked"})
    mock_client.set_client_name = AsyncMock(return_value={"message": "Name updated"})
    mock_client.set_client_note = AsyncMock(return_value={"message": "Note updated"})
    
    return mock_client


@pytest.fixture
def mock_failed_unifi_client():
    """Mock UniFi client that fails authentication."""
    mock_client = AsyncMock(spec=UnifiControllerClient)
    mock_client.is_authenticated = False
    mock_client.authenticate = AsyncMock(return_value=False)
    mock_client.ensure_authenticated = AsyncMock(side_effect=Exception("Authentication failed"))
    
    # All API calls should return errors
    error_response = {"error": "Authentication required"}
    mock_client.get_devices = AsyncMock(return_value=error_response)
    mock_client.get_clients = AsyncMock(return_value=error_response)
    mock_client.get_networks = AsyncMock(return_value=error_response)
    
    return mock_client


@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for different scenarios."""
    return {
        "login_success_udm": {
            "status_code": 200,
            "json": {},
            "cookies": {"TOKEN": "test-token"},
            "headers": {"x-csrf-token": "test-csrf"}
        },
        "login_success_legacy": {
            "status_code": 200,
            "json": {"data": [], "meta": {"rc": "ok"}},
            "cookies": {"unifises": "test-session"},
            "headers": {}
        },
        "login_failure": {
            "status_code": 401,
            "json": {"error": "Invalid credentials"},
            "cookies": {},
            "headers": {}
        },
        "devices_response": {
            "status_code": 200,
            "json": {"data": [], "meta": {"rc": "ok"}},
        },
        "network_error": {
            "status_code": 500,
            "json": {"error": "Internal server error"}
        }
    }


@pytest_asyncio.fixture
async def test_server(test_unifi_config, test_server_config, mock_unifi_client) -> FastMCP:
    """Create test FastMCP server with mocked UniFi client."""
    with patch('unifi_mcp.server.UnifiControllerClient', return_value=mock_unifi_client):
        server = UniFiMCPServer(test_unifi_config, test_server_config)
        await server.initialize()
        yield server.mcp
        await server.cleanup()


@pytest.fixture
def integration_config() -> Optional[UniFiConfig]:
    """Configuration for integration tests - returns None if env vars not set."""
    import os
    
    controller_url = os.getenv("UNIFI_CONTROLLER_URL")
    username = os.getenv("UNIFI_USERNAME") 
    password = os.getenv("UNIFI_PASSWORD")
    
    if not all([controller_url, username, password]):
        return None
        
    return UniFiConfig(
        controller_url=controller_url,
        username=username,
        password=password,
        verify_ssl=os.getenv("UNIFI_VERIFY_SSL", "false").lower() == "true",
        is_udm_pro=os.getenv("UNIFI_IS_UDM_PRO", "true").lower() == "true"
    )


# Helper functions for tests
def normalize_mac(mac: str) -> str:
    """Normalize MAC address format for testing."""
    return mac.strip().lower().replace("-", ":").replace(".", ":")


def mock_httpx_response(status_code: int, json_data: Dict[str, Any] = None, 
                       cookies: Dict[str, str] = None, headers: Dict[str, str] = None):
    """Create mock httpx Response object."""
    response = Mock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.cookies = httpx.Cookies(cookies or {})
    response.headers = httpx.Headers(headers or {})
    response.text = json.dumps(json_data or {})
    return response