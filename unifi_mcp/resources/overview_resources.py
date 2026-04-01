"""
Overview MCP resources for UniFi MCP Server.

Provides comprehensive dashboard and overview resources with glanceable information.
"""

import asyncio
import json
import logging

from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import get_device_type_name

logger = logging.getLogger(__name__)


def register_overview_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register overview and dashboard MCP resources."""

    async def _get_dashboard_data(site_name: str) -> str:
        try:
            dashboard = await client.get_dashboard_metrics(site_name)

            if isinstance(dashboard, dict) and "error" in dashboard:
                return f"Error retrieving dashboard for site {site_name}: {dashboard['error']}"

            if isinstance(dashboard, list):
                if not dashboard:
                    return (
                        f"**UniFi Dashboard Metrics - {site_name}**\n\nNo dashboard data available."
                    )

                latest_data = dashboard[-1]
                filtered_dashboard = {
                    "wan_tx_rate": latest_data.get(
                        "wan-tx_bytes", latest_data.get("tx_bytes-r", 0)
                    ),
                    "wan_rx_rate": latest_data.get(
                        "wan-rx_bytes", latest_data.get("rx_bytes-r", 0)
                    ),
                    "wlan_tx_rate": latest_data.get("tx_bytes-r", 0),
                    "wlan_rx_rate": latest_data.get("rx_bytes-r", 0),
                    "latency_avg": latest_data.get("latency_avg", 0),
                    "timestamp": latest_data.get("time", 0),
                    "data_points": len(dashboard),
                }
                return json.dumps(filtered_dashboard, indent=2, ensure_ascii=False)

            elif isinstance(dashboard, dict):
                filtered_dashboard = {
                    "wan_tx_rate": dashboard.get("wan", {}).get("tx_bytes-r", 0),
                    "wan_rx_rate": dashboard.get("wan", {}).get("rx_bytes-r", 0),
                    "wlan_tx_rate": dashboard.get("wlan", {}).get("tx_bytes-r", 0),
                    "wlan_rx_rate": dashboard.get("wlan", {}).get("rx_bytes-r", 0),
                    "latency_avg": dashboard.get("latency_avg", 0),
                    "timestamp": dashboard.get("time", 0),
                    "data_points": 1,
                }
                return json.dumps(filtered_dashboard, indent=2, ensure_ascii=False)

            return f"**UniFi Dashboard Metrics - {site_name}**\n\nUnexpected dashboard data format received."

        except Exception as e:
            logger.error(f"Error in dashboard resource for {site_name}: {e}")
            return f"Error retrieving dashboard for site {site_name}: {e!s}"

    async def _get_overview_data(site_name: str) -> str:
        try:
            devices, clients = await asyncio.gather(
                client.get_devices(site_name),
                client.get_clients(site_name),
            )

            if isinstance(devices, dict) and "error" in devices:
                return f"Error retrieving devices for site {site_name}: {devices['error']}"
            if isinstance(clients, dict) and "error" in clients:
                return f"Error retrieving clients for site {site_name}: {clients['error']}"

            if not isinstance(devices, list):
                devices = []
            if not isinstance(clients, list):
                clients = []

            try:
                port_forwarding = await client.get_port_forwarding_rules(site_name)
                if (
                    isinstance(port_forwarding, dict) and "error" in port_forwarding
                ) or not isinstance(port_forwarding, list):
                    port_forwarding = []
            except Exception:
                port_forwarding = []

            device_counts = {"Gateway": 0, "Access Point": 0, "Switch": 0, "Other": 0}
            online_devices = 0
            gateway_info = None

            for device in devices:
                device_type = get_device_type_name(device)
                state = device.get("state", 0)

                if device_type in device_counts:
                    device_counts[device_type] += 1
                else:
                    device_counts["Other"] += 1

                if state == 1:
                    online_devices += 1

                if device_type == "Gateway" and state == 1:
                    gateway_info = {
                        "name": device.get("name", "Gateway"),
                        "model": device.get("model", "Unknown"),
                        "wan_ip": device.get("wan1", {}).get("ip", "Unknown"),
                        "lan_ip": device.get("lan_ip", "Unknown"),
                        "uptime": device.get("uptime", 0),
                        "version": device.get("version", "Unknown"),
                    }

            wired_count = sum(1 for c in clients if c.get("is_wired", True))
            wireless_count = len(clients) - wired_count
            enabled_rules = [r for r in port_forwarding if r.get("enabled", False)]

            filtered_overview = {
                "summary": {
                    "total_devices": len(devices),
                    "online_devices": online_devices,
                    "device_types": device_counts,
                    "total_clients": len(clients),
                    "wireless_clients": wireless_count,
                    "wired_clients": wired_count,
                },
                "gateway": gateway_info,
                "port_forwarding": {
                    "total_rules": len(port_forwarding),
                    "enabled_rules": len(enabled_rules),
                }
                if port_forwarding
                else None,
            }
            return json.dumps(filtered_overview, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error in overview resource for {site_name}: {e}")
            return f"Error retrieving network overview for site {site_name}: {e!s}"

    @mcp.resource("unifi://dashboard")
    async def resource_dashboard():
        """Get dashboard metrics with clean formatting (default site)."""
        return await _get_dashboard_data("default")

    @mcp.resource("unifi://dashboard/{site_name}")
    async def resource_site_dashboard(site_name: str):
        """Get dashboard metrics with clean formatting for specific site."""
        return await _get_dashboard_data(site_name)

    @mcp.resource("unifi://overview")
    async def resource_overview():
        """Get comprehensive network overview with clean formatting (default site)."""
        return await _get_overview_data("default")

    @mcp.resource("unifi://overview/{site_name}")
    async def resource_site_overview(site_name: str):
        """Get comprehensive network overview with clean formatting for specific site."""
        return await _get_overview_data(site_name)
