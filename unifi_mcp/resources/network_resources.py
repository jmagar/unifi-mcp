"""
Network configuration MCP resources for UniFi MCP Server.

Provides structured access to network configurations, sites, and settings.
"""

import json
import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient

logger = logging.getLogger(__name__)


def register_network_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all network configuration MCP resources."""
    
    @mcp.resource("unifi://config/networks")
    async def resource_network_configs():
        """Get network configurations with clean formatting."""
        try:
            networks = await client.get_network_configs("default")
            
            if isinstance(networks, dict) and "error" in networks:
                return f"Error retrieving network configs: {networks['error']}"
            
            if not isinstance(networks, list):
                return "Error: Unexpected response format"
            
            # Filter networks to essential info
            filtered_networks = [{
                "name": net.get("name", "Unknown"),
                "purpose": net.get("purpose", "Unknown"),
                "vlan": net.get("vlan", "Unknown"),
                "subnet": net.get("ip_subnet", "Unknown"),
                "enabled": net.get("enabled", False)
            } for net in networks]
            return json.dumps(filtered_networks, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in network configs resource: {e}")
            return f"Error retrieving network configs: {str(e)}"
    
    
    @mcp.resource("unifi://config/networks/{site_name}")
    async def resource_site_network_configs(site_name: str):
        """Get network configurations with clean formatting for specific site."""
        try:
            networks = await client.get_network_configs(site_name)
            
            if isinstance(networks, dict) and "error" in networks:
                return f"Error retrieving network configs for site {site_name}: {networks['error']}"
            
            if not isinstance(networks, list):
                return "Error: Unexpected response format"
            
            # Filter networks to essential info
            filtered_networks = [{
                "name": net.get("name", "Unknown"),
                "purpose": net.get("purpose", "Unknown"),
                "vlan": net.get("vlan", "Unknown"),
                "subnet": net.get("ip_subnet", "Unknown"),
                "enabled": net.get("enabled", False)
            } for net in networks]
            return json.dumps(filtered_networks, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in site network configs resource for {site_name}: {e}")
            return f"Error retrieving network configs for site {site_name}: {str(e)}"
    
    
    @mcp.resource("unifi://config/wlans")
    async def resource_wlan_configs():
        """Get WLAN configurations with clean formatting (default site)."""
        try:
            wlans = await client.get_wlan_configs("default")
            
            if isinstance(wlans, dict) and "error" in wlans:
                return f"Error retrieving WLAN configs: {wlans['error']}"
            
            if not isinstance(wlans, list):
                return "Error: Unexpected response format"
            
            # Filter WLANs to essential info
            filtered_wlans = [{
                "name": wlan.get("name", "Unknown"),
                "ssid": wlan.get("x_passphrase", wlan.get("name", "Unknown")),
                "enabled": wlan.get("enabled", False),
                "security": wlan.get("security", "Unknown"),
                "wpa_mode": wlan.get("wpa_mode", "Unknown"),
                "channel": wlan.get("channel", "auto")
            } for wlan in wlans]
            return json.dumps(filtered_wlans, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in WLAN configs resource: {e}")
            return f"Error retrieving WLAN configs: {str(e)}"
    
    
    @mcp.resource("unifi://config/wlans/{site_name}")
    async def resource_site_wlan_configs(site_name: str):
        """Get WLAN configurations with clean formatting for specific site."""
        try:
            wlans = await client.get_wlan_configs(site_name)
            
            if isinstance(wlans, dict) and "error" in wlans:
                return f"Error retrieving WLAN configs for site {site_name}: {wlans['error']}"
            
            if not isinstance(wlans, list):
                return "Error: Unexpected response format"
            
            # Filter WLANs to essential info
            filtered_wlans = [{
                "name": wlan.get("name", "Unknown"),
                "ssid": wlan.get("x_passphrase", wlan.get("name", "Unknown")),
                "enabled": wlan.get("enabled", False),
                "security": wlan.get("security", "Unknown"),
                "wpa_mode": wlan.get("wpa_mode", "Unknown"),
                "channel": wlan.get("channel", "auto")
            } for wlan in wlans]
            return json.dumps(filtered_wlans, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in site WLAN configs resource for {site_name}: {e}")
            return f"Error retrieving WLAN configs for site {site_name}: {str(e)}"
    
    
    @mcp.resource("unifi://config/portforward")
    async def resource_port_forwarding():
        """Get port forwarding rules with clean formatting (default site)."""
        try:
            rules = await client.get_port_forwarding_rules("default")
            
            if isinstance(rules, dict) and "error" in rules:
                return f"Error retrieving port forwarding rules: {rules['error']}"
            
            if not isinstance(rules, list):
                return "Error: Unexpected response format"
            
            # Filter port forwarding rules to essential info
            filtered_rules = [{
                "name": rule.get("name", "Unknown"),
                "enabled": rule.get("enabled", False),
                "src": rule.get("src", "any"),
                "dst_port": rule.get("dst_port", "Unknown"),
                "fwd_port": rule.get("fwd_port", "Unknown"),
                "fwd_ip": rule.get("fwd", "Unknown"),
                "protocol": rule.get("proto", "tcp_udp")
            } for rule in rules]
            return json.dumps(filtered_rules, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in port forwarding resource: {e}")
            return f"Error retrieving port forwarding rules: {str(e)}"
    
    
    @mcp.resource("unifi://config/portforward/{site_name}")
    async def resource_site_port_forwarding(site_name: str):
        """Get port forwarding rules with clean formatting for specific site."""
        try:
            rules = await client.get_port_forwarding_rules(site_name)
            
            if isinstance(rules, dict) and "error" in rules:
                return f"Error retrieving port forwarding rules for site {site_name}: {rules['error']}"
            
            if not isinstance(rules, list):
                return "Error: Unexpected response format"
            
            # Filter port forwarding rules to essential info
            filtered_rules = [{
                "name": rule.get("name", "Unknown"),
                "enabled": rule.get("enabled", False),
                "src": rule.get("src", "any"),
                "dst_port": rule.get("dst_port", "Unknown"),
                "fwd_port": rule.get("fwd_port", "Unknown"),
                "fwd_ip": rule.get("fwd", "Unknown"),
                "protocol": rule.get("proto", "tcp_udp")
            } for rule in rules]
            return json.dumps(filtered_rules, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in site port forwarding resource for {site_name}: {e}")
            return f"Error retrieving port forwarding rules for site {site_name}: {str(e)}"
    
    
    @mcp.resource("unifi://channels")
    async def resource_current_channels():
        """Get current wireless channels with clean formatting (default site)."""
        try:
            channels = await client._make_request("GET", "/stat/current-channel", site_name="default")
            
            if isinstance(channels, dict) and "error" in channels:
                return f"Error retrieving wireless channels: {channels['error']}"
            
            if not isinstance(channels, list):
                return "Error: Unexpected response format"
            
            # Filter channels to essential info
            filtered_channels = [{
                "radio": ch.get("radio", "Unknown"),
                "channel": ch.get("channel", "Unknown"),
                "tx_power": ch.get("tx_power", "Unknown"),
                "utilization": ch.get("utilization", 0),
                "num_sta": ch.get("num_sta", 0)
            } for ch in channels]
            return json.dumps(filtered_channels, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in channels resource: {e}")
            return f"Error retrieving wireless channels: {str(e)}"
    
    
    @mcp.resource("unifi://channels/{site_name}")
    async def resource_site_current_channels(site_name: str):
        """Get current wireless channels with clean formatting for specific site."""
        try:
            channels = await client._make_request("GET", "/stat/current-channel", site_name=site_name)
            
            if isinstance(channels, dict) and "error" in channels:
                return f"Error retrieving wireless channels for site {site_name}: {channels['error']}"
            
            if not isinstance(channels, list):
                return "Error: Unexpected response format"
            
            # Filter channels to essential info
            filtered_channels = [{
                "radio": ch.get("radio", "Unknown"),
                "channel": ch.get("channel", "Unknown"),
                "tx_power": ch.get("tx_power", "Unknown"),
                "utilization": ch.get("utilization", 0),
                "num_sta": ch.get("num_sta", 0)
            } for ch in channels]
            return json.dumps(filtered_channels, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error in site channels resource for {site_name}: {e}")
            return f"Error retrieving wireless channels for site {site_name}: {str(e)}"