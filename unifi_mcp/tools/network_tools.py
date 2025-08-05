"""
Network configuration tools for UniFi MCP Server.

Provides tools for accessing network configurations, site information,
and network-related settings.
"""

import logging
from typing import Any, Dict, List
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_site_summary

logger = logging.getLogger(__name__)


def register_network_tools(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all network configuration tools."""
    
    @mcp.tool()
    async def get_sites() -> List[Dict[str, Any]]:
        """
        Get all controller sites with health information.
        
        Returns:
            List of sites with formatted health and device information
        """
        try:
            sites = await client.get_sites()
            
            if isinstance(sites, dict) and "error" in sites:
                return [sites]
            
            if not isinstance(sites, list):
                return [{"error": "Unexpected response format"}]
            
            # Format each site for clean output
            formatted_sites = []
            for site in sites:
                try:
                    formatted_site = format_site_summary(site)
                    formatted_sites.append(formatted_site)
                except Exception as e:
                    logger.error(f"Error formatting site {site.get('name', 'Unknown')}: {e}")
                    formatted_sites.append({
                        "name": site.get("name", "Unknown"),
                        "description": site.get("desc", "Unknown"),
                        "error": f"Formatting error: {str(e)}"
                    })
            
            return formatted_sites
            
        except Exception as e:
            logger.error(f"Error getting sites: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_wlan_configs(site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get wireless network (WLAN) configurations.
        
        Args:
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of WLAN configurations with essential settings
        """
        try:
            wlans = await client.get_wlan_configs(site_name)
            
            if isinstance(wlans, dict) and "error" in wlans:
                return [wlans]
            
            if not isinstance(wlans, list):
                return [{"error": "Unexpected response format"}]
            
            # Format WLAN configs for clean output
            formatted_wlans = []
            for wlan in wlans:
                formatted_wlan = {
                    "name": wlan.get("name", "Unknown WLAN"),
                    "ssid": wlan.get("x_iapp_key", wlan.get("name", "Unknown")),
                    "enabled": wlan.get("enabled", False),
                    "security": wlan.get("security", "Unknown"),
                    "wpa_mode": wlan.get("wpa_mode", "Unknown"),
                    "vlan": wlan.get("vlan", "Default"),
                    "guest_access": wlan.get("is_guest", False),
                    "hide_ssid": wlan.get("hide_ssid", False),
                    "mac_filter_enabled": wlan.get("mac_filter_enabled", False),
                    "band_steering": wlan.get("band_steering", False)
                }
                formatted_wlans.append(formatted_wlan)
            
            return formatted_wlans
            
        except Exception as e:
            logger.error(f"Error getting WLAN configs: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_network_configs(site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get network/VLAN configurations.
        
        Args:
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of network configurations with essential settings
        """
        try:
            networks = await client.get_network_configs(site_name)
            
            if isinstance(networks, dict) and "error" in networks:
                return [networks]
            
            if not isinstance(networks, list):
                return [{"error": "Unexpected response format"}]
            
            # Format network configs for clean output
            formatted_networks = []
            for network in networks:
                formatted_network = {
                    "name": network.get("name", "Unknown Network"),
                    "purpose": network.get("purpose", "Unknown"),
                    "vlan": network.get("vlan", "None"),
                    "subnet": network.get("ip_subnet", "Unknown"),
                    "dhcp_enabled": network.get("dhcpd_enabled", False),
                    "dhcp_range": {
                        "start": network.get("dhcpd_start"),
                        "stop": network.get("dhcpd_stop")
                    } if network.get("dhcpd_enabled") else None,
                    "domain_name": network.get("domain_name"),
                    "guest_access": network.get("is_guest", False)
                }
                formatted_networks.append(formatted_network)
            
            return formatted_networks
            
        except Exception as e:
            logger.error(f"Error getting network configs: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_port_configs(site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get switch port profile configurations.
        
        Args:
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of port profile configurations
        """
        try:
            ports = await client.get_port_configs(site_name)
            
            if isinstance(ports, dict) and "error" in ports:
                return [ports]
            
            if not isinstance(ports, list):
                return [{"error": "Unexpected response format"}]
            
            # Format port configs for clean output
            formatted_ports = []
            for port in ports:
                formatted_port = {
                    "name": port.get("name", "Unknown Port Profile"),
                    "enabled": port.get("enabled", False),
                    "native_vlan": port.get("native_networkconf_id", "Default"),
                    "tagged_vlans": port.get("tagged_networkconf_ids", []),
                    "port_security": port.get("port_security_enabled", False),
                    "storm_control": port.get("storm_ctrl_enabled", False),
                    "poe_mode": port.get("poe_mode", "auto"),
                    "speed": port.get("speed", "auto"),
                    "duplex": port.get("full_duplex", True)
                }
                formatted_ports.append(formatted_port)
            
            return formatted_ports
            
        except Exception as e:
            logger.error(f"Error getting port configs: {e}")
            return [{"error": str(e)}]
    
    
    @mcp.tool()
    async def get_port_forwarding_rules(site_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get port forwarding rules.
        
        Args:
            site_name: UniFi site name (default: "default")
            
        Returns:
            List of port forwarding rules with essential information
        """
        try:
            rules = await client.get_port_forwarding_rules(site_name)
            
            if isinstance(rules, dict) and "error" in rules:
                return [rules]
            
            if not isinstance(rules, list):
                return [{"error": "Unexpected response format"}]
            
            # Format port forwarding rules for clean output
            formatted_rules = []
            for rule in rules:
                formatted_rule = {
                    "name": rule.get("name", "Unknown Rule"),
                    "enabled": rule.get("enabled", False),
                    "protocol": rule.get("proto", "Unknown"),
                    "external_port": rule.get("dst_port", "Unknown"),
                    "internal_ip": rule.get("fwd", "Unknown"),
                    "internal_port": rule.get("fwd_port", "Unknown"),
                    "log": rule.get("log", False),
                    "source": rule.get("src", "any")
                }
                formatted_rules.append(formatted_rule)
            
            return formatted_rules
            
        except Exception as e:
            logger.error(f"Error getting port forwarding rules: {e}")
            return [{"error": str(e)}]