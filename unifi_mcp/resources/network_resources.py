"""
Network configuration MCP resources for UniFi MCP Server.

Provides structured access to network configurations, sites, and settings.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_generic_list

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
            
            return format_generic_list(networks, "Network Configurations", ["name", "purpose", "vlan", "ip_subnet"])
            
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
            
            return format_generic_list(networks, "Network Configurations", ["name", "purpose", "vlan", "ip_subnet"])
            
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
            
            return format_generic_list(wlans, "WLAN Configurations", ["name", "enabled", "security", "vlan"])
            
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
            
            return format_generic_list(wlans, "WLAN Configurations", ["name", "enabled", "security", "vlan"])
            
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
            
            return format_generic_list(rules, "Port Forwarding Rules", ["name", "proto", "dst_port", "fwd", "enabled"])
            
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
            
            if not rules:
                return f"**UniFi Port Forwarding Rules - {site_name}**\n\nNo port forwarding rules configured."
            
            return format_generic_list(rules, "Port Forwarding Rules", ["name", "proto", "dst_port", "fwd", "enabled"])
            
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
            
            if not channels:
                return "**UniFi Wireless Channels**\n\nNo wireless channel data available."
            
            summary = f"**UniFi Wireless Channels** ({len(channels)} access points)\n\n"
            
            for channel_info in channels:
                ap_name = channel_info.get("name", "Unknown AP")
                ap_mac = channel_info.get("mac", "Unknown")
                
                summary += f"📡 **{ap_name}**\n"
                summary += f"  • MAC: {ap_mac}\n"
                
                # Radio information
                radios = channel_info.get("radio_table", [])
                for i, radio in enumerate(radios):
                    radio_name = radio.get("name", f"Radio {i+1}")
                    channel = radio.get("channel", "Unknown")
                    tx_power = radio.get("tx_power", "Unknown")
                    ht = radio.get("ht", "Unknown")
                    
                    # Determine band from channel
                    if isinstance(channel, int):
                        if channel <= 14:
                            band = "2.4GHz"
                        else:
                            band = "5GHz"
                    else:
                        band = "Unknown"
                    
                    summary += f"  • {radio_name} ({band}): Channel {channel}, {tx_power}dBm"
                    if ht != "Unknown":
                        summary += f", {ht}MHz"
                    summary += "\n"
                
                summary += "\n"
            
            return format_generic_list(channels, "Wireless Channels", ["name", "mac", "channel", "tx_power"])
            
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
            
            if not channels:
                return f"**UniFi Wireless Channels - {site_name}**\n\nNo wireless channel data available."
            
            summary = f"**UniFi Wireless Channels - {site_name}** ({len(channels)} access points)\n\n"
            
            for channel_info in channels:
                ap_name = channel_info.get("name", "Unknown AP")
                ap_mac = channel_info.get("mac", "Unknown")
                
                summary += f"📡 **{ap_name}**\n"
                summary += f"  • MAC: {ap_mac}\n"
                
                # Radio information
                radios = channel_info.get("radio_table", [])
                for i, radio in enumerate(radios):
                    radio_name = radio.get("name", f"Radio {i+1}")
                    channel = radio.get("channel", "Unknown")
                    tx_power = radio.get("tx_power", "Unknown")
                    ht = radio.get("ht", "Unknown")
                    
                    # Determine band from channel
                    if isinstance(channel, int):
                        if channel <= 14:
                            band = "2.4GHz"
                        else:
                            band = "5GHz"
                    else:
                        band = "Unknown"
                    
                    summary += f"  • {radio_name} ({band}): Channel {channel}, {tx_power}dBm"
                    if ht != "Unknown":
                        summary += f", {ht}MHz"
                    summary += "\n"
                
                summary += "\n"
            
            return format_generic_list(channels, "Wireless Channels", ["name", "mac", "channel", "tx_power"])
            
        except Exception as e:
            logger.error(f"Error in site channels resource for {site_name}: {e}")
            return f"Error retrieving wireless channels for site {site_name}: {str(e)}"