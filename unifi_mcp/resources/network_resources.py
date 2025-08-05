"""
Network configuration MCP resources for UniFi MCP Server.

Provides structured access to network configurations, sites, and settings.
"""

import logging
from fastmcp import FastMCP

from ..client import UnifiControllerClient
from ..formatters import format_site_summary

logger = logging.getLogger(__name__)


def register_network_resources(mcp: FastMCP, client: UnifiControllerClient) -> None:
    """Register all network configuration MCP resources."""
    
    @mcp.resource("unifi://sites")
    async def resource_all_sites():
        """Get all controller sites with clean formatting."""
        try:
            sites = await client.get_sites()
            
            if isinstance(sites, dict) and "error" in sites:
                return sites
            
            if not isinstance(sites, list):
                return {"error": "Unexpected response format"}
            
            formatted_sites = [format_site_summary(site) for site in sites]
            
            # Return clean formatted summary
            if len(formatted_sites) == 1:
                site = formatted_sites[0]
                summary = f"""**UniFi Controller Site**

**Site Information:**
• Name: {site.get('name', 'Unknown')}
• Site ID: {site.get('site_id', 'Unknown')}
• Role: {site.get('role', 'Unknown')}

**Health Status:**
• Overall Health: {site.get('health_score', 'Unknown')}
• Total Devices: {site.get('total_devices', 0)}
• Access Points: {site.get('access_points', 0)}
• Gateways: {site.get('gateways', 0)}
• Switches: {site.get('switches', 0)}
• Active Alerts: {site.get('alerts', 0)}"""
                return summary
            else:
                # Multiple sites
                summary = "**UniFi Controller Sites**\n\n"
                for site in formatted_sites:
                    summary += f"• **{site.get('name', 'Unknown')}** ({site.get('site_id', 'Unknown')})\n"
                    summary += f"  Health: {site.get('health_score', 'Unknown')}, Devices: {site.get('total_devices', 0)}\n\n"
                return summary.strip()
            
        except Exception as e:
            logger.error(f"Error in sites resource: {e}")
            return f"Error retrieving sites: {str(e)}"
    
    
    @mcp.resource("unifi://sites/{site_name}")
    async def resource_site_detail(site_name: str):
        """Get detailed site information with clean formatting."""
        try:
            sites = await client.get_sites()
            
            if isinstance(sites, dict) and "error" in sites:
                return f"Error retrieving sites: {sites['error']}"
            
            if not isinstance(sites, list):
                return "Error: Unexpected response format"
            
            # Find matching site
            for site in sites:
                if site.get("name") == site_name:
                    formatted_site = format_site_summary(site)
                    
                    summary = f"**UniFi Site Details - {site_name}**\n\n"
                    summary += f"**Site Information:**\n"
                    summary += f"  • Name: {formatted_site.get('name', 'Unknown')}\n"
                    summary += f"  • Site ID: {formatted_site.get('site_id', 'Unknown')}\n"
                    summary += f"  • Role: {formatted_site.get('role', 'Unknown')}\n\n"
                    
                    summary += f"**Health Status:**\n"
                    summary += f"  • Overall Health: {formatted_site.get('health_score', 'Unknown')}\n"
                    summary += f"  • Total Devices: {formatted_site.get('total_devices', 0)}\n"
                    summary += f"  • Access Points: {formatted_site.get('access_points', 0)}\n"
                    summary += f"  • Gateways: {formatted_site.get('gateways', 0)}\n"
                    summary += f"  • Switches: {formatted_site.get('switches', 0)}\n"
                    summary += f"  • Active Alerts: {formatted_site.get('alerts', 0)}\n"
                    
                    return summary.strip()
            
            return f"**Site Not Found**\n\nSite '{site_name}' was not found in the controller."
            
        except Exception as e:
            logger.error(f"Error in site detail resource for {site_name}: {e}")
            return f"Error retrieving site details for {site_name}: {str(e)}"
    
    
    @mcp.resource("unifi://config/networks")
    async def resource_network_configs():
        """Get network configurations with clean formatting."""
        try:
            networks = await client.get_network_configs("default")
            
            if isinstance(networks, dict) and "error" in networks:
                return f"Error retrieving network configs: {networks['error']}"
            
            if not isinstance(networks, list):
                return "Error: Unexpected response format"
            
            if not networks:
                return "**UniFi Network Configurations**\n\nNo networks configured."
            
            summary = f"**UniFi Network Configurations** ({len(networks)} total)\n\n"
            
            for network in networks:
                name = network.get("name", "Unknown Network")
                purpose = network.get("purpose", "Unknown")
                vlan = network.get("vlan", "None")
                subnet = network.get("ip_subnet", "Unknown")
                dhcp_enabled = network.get("dhcpd_enabled", False)
                guest_access = network.get("is_guest", False)
                
                # Determine network icon based on purpose
                if purpose == "corporate":
                    icon = "🏢"
                elif purpose == "wan":
                    icon = "🌍"
                elif purpose == "guest":
                    icon = "👥"
                elif purpose == "remote-user-vpn":
                    icon = "🔒"
                else:
                    icon = "🔗"
                
                summary += f"{icon} **{name}**\n"
                summary += f"  • Purpose: {purpose.replace('-', ' ').title()}\n"
                if vlan != "None":
                    summary += f"  • VLAN: {vlan}\n"
                if subnet != "Unknown":
                    summary += f"  • Subnet: {subnet}\n"
                if dhcp_enabled:
                    dhcp_start = network.get("dhcpd_start", "Unknown")
                    dhcp_stop = network.get("dhcpd_stop", "Unknown")
                    summary += f"  • DHCP: Enabled ({dhcp_start} - {dhcp_stop})\n"
                else:
                    summary += f"  • DHCP: Disabled\n"
                if guest_access:
                    summary += f"  • Guest Access: Yes\n"
                summary += "\n"
            
            return summary.strip()
            
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
            
            if not networks:
                return f"**UniFi Network Configurations - {site_name}**\n\nNo networks configured."
            
            summary = f"**UniFi Network Configurations - {site_name}** ({len(networks)} total)\n\n"
            
            for network in networks:
                name = network.get("name", "Unknown Network")
                purpose = network.get("purpose", "Unknown")
                vlan = network.get("vlan", "None")
                subnet = network.get("ip_subnet", "Unknown")
                dhcp_enabled = network.get("dhcpd_enabled", False)
                guest_access = network.get("is_guest", False)
                
                # Determine network icon based on purpose
                if purpose == "corporate":
                    icon = "🏢"
                elif purpose == "wan":
                    icon = "🌍"
                elif purpose == "guest":
                    icon = "👥"
                elif purpose == "remote-user-vpn":
                    icon = "🔒"
                else:
                    icon = "🔗"
                
                summary += f"{icon} **{name}**\n"
                summary += f"  • Purpose: {purpose.replace('-', ' ').title()}\n"
                if vlan != "None":
                    summary += f"  • VLAN: {vlan}\n"
                if subnet != "Unknown":
                    summary += f"  • Subnet: {subnet}\n"
                if dhcp_enabled:
                    dhcp_start = network.get("dhcpd_start", "Unknown")
                    dhcp_stop = network.get("dhcpd_stop", "Unknown")
                    summary += f"  • DHCP: Enabled ({dhcp_start} - {dhcp_stop})\n"
                else:
                    summary += f"  • DHCP: Disabled\n"
                if guest_access:
                    summary += f"  • Guest Access: Yes\n"
                summary += "\n"
            
            return summary.strip()
            
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
            
            if not wlans:
                return "**UniFi WLAN Configurations**\n\nNo WLANs configured."
            
            summary = f"**UniFi WLAN Configurations** ({len(wlans)} total)\n\n"
            
            for wlan in wlans:
                name = wlan.get("name", "Unknown WLAN")
                ssid = wlan.get("x_iapp_key", wlan.get("name", "Unknown"))
                enabled = wlan.get("enabled", False)
                security = wlan.get("security", "Unknown")
                wpa_mode = wlan.get("wpa_mode", "Unknown")
                vlan = wlan.get("vlan", "Default")
                guest_access = wlan.get("is_guest", False)
                hide_ssid = wlan.get("hide_ssid", False)
                mac_filter = wlan.get("mac_filter_enabled", False)
                band_steering = wlan.get("band_steering", False)
                
                # Determine WLAN status icon
                if enabled:
                    status_icon = "✅"
                    status_text = "Enabled"
                else:
                    status_icon = "❌"
                    status_text = "Disabled"
                
                # Determine security icon
                if security.lower() in ["wpapsk", "wpa2psk", "wpa3psk"]:
                    sec_icon = "🔒"
                elif security.lower() == "open":
                    sec_icon = "🔓"
                else:
                    sec_icon = "❓"
                
                summary += f"📶 **{name}** {status_icon}\n"
                summary += f"  • SSID: {ssid}\n"
                summary += f"  • Status: {status_text}\n"
                summary += f"  • Security: {sec_icon} {security} ({wpa_mode})\n"
                if vlan != "Default":
                    summary += f"  • VLAN: {vlan}\n"
                if guest_access:
                    summary += f"  • Guest Access: ✅ Yes\n"
                if hide_ssid:
                    summary += f"  • Hidden SSID: 👁️ Yes\n"
                if mac_filter:
                    summary += f"  • MAC Filter: 🚫 Enabled\n"
                if band_steering:
                    summary += f"  • Band Steering: 🔄 Enabled\n"
                summary += "\n"
            
            return summary.strip()
            
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
            
            if not wlans:
                return f"**UniFi WLAN Configurations - {site_name}**\n\nNo WLANs configured."
            
            summary = f"**UniFi WLAN Configurations - {site_name}** ({len(wlans)} total)\n\n"
            
            for wlan in wlans:
                name = wlan.get("name", "Unknown WLAN")
                ssid = wlan.get("x_iapp_key", wlan.get("name", "Unknown"))
                enabled = wlan.get("enabled", False)
                security = wlan.get("security", "Unknown")
                wpa_mode = wlan.get("wpa_mode", "Unknown")
                vlan = wlan.get("vlan", "Default")
                guest_access = wlan.get("is_guest", False)
                hide_ssid = wlan.get("hide_ssid", False)
                mac_filter = wlan.get("mac_filter_enabled", False)
                band_steering = wlan.get("band_steering", False)
                
                # Determine WLAN status icon
                if enabled:
                    status_icon = "✅"
                    status_text = "Enabled"
                else:
                    status_icon = "❌"
                    status_text = "Disabled"
                
                # Determine security icon
                if security.lower() in ["wpapsk", "wpa2psk", "wpa3psk"]:
                    sec_icon = "🔒"
                elif security.lower() == "open":
                    sec_icon = "🔓"
                else:
                    sec_icon = "❓"
                
                summary += f"📶 **{name}** {status_icon}\n"
                summary += f"  • SSID: {ssid}\n"
                summary += f"  • Status: {status_text}\n"
                summary += f"  • Security: {sec_icon} {security} ({wpa_mode})\n"
                if vlan != "Default":
                    summary += f"  • VLAN: {vlan}\n"
                if guest_access:
                    summary += f"  • Guest Access: ✅ Yes\n"
                if hide_ssid:
                    summary += f"  • Hidden SSID: 👁️ Yes\n"
                if mac_filter:
                    summary += f"  • MAC Filter: 🚫 Enabled\n"
                if band_steering:
                    summary += f"  • Band Steering: 🔄 Enabled\n"
                summary += "\n"
            
            return summary.strip()
            
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
            
            if not rules:
                return "**UniFi Port Forwarding Rules**\n\nNo port forwarding rules configured."
            
            enabled_rules = [r for r in rules if r.get('enabled', False)]
            disabled_rules = [r for r in rules if not r.get('enabled', False)]
            
            summary = f"**UniFi Port Forwarding Rules** ({len(rules)} total)\n\n"
            
            if enabled_rules:
                summary += f"✅ **Active Rules** ({len(enabled_rules)})\n"
                for rule in enabled_rules:
                    name = rule.get("name", "Unnamed Rule")
                    protocol = rule.get("proto", "Unknown").upper()
                    external_port = rule.get("dst_port", "Unknown")
                    internal_ip = rule.get("fwd", "Unknown")
                    internal_port = rule.get("fwd_port", "Unknown")
                    source = rule.get("src", "any")
                    log_enabled = rule.get("log", False)
                    
                    summary += f"• **{name}**\n"
                    summary += f"  • {protocol} {external_port} → {internal_ip}:{internal_port}\n"
                    if source != "any":
                        summary += f"  • Source: {source}\n"
                    if log_enabled:
                        summary += f"  • Logging: 📄 Enabled\n"
                    summary += "\n"
            
            if disabled_rules:
                summary += f"❌ **Disabled Rules** ({len(disabled_rules)})\n"
                for rule in disabled_rules[:5]:  # Limit to 5 disabled rules
                    name = rule.get("name", "Unnamed Rule")
                    protocol = rule.get("proto", "Unknown").upper()
                    external_port = rule.get("dst_port", "Unknown")
                    internal_ip = rule.get("fwd", "Unknown")
                    internal_port = rule.get("fwd_port", "Unknown")
                    
                    summary += f"• **{name}** ({protocol} {external_port} → {internal_ip}:{internal_port})\n"
                
                if len(disabled_rules) > 5:
                    summary += f"• ... and {len(disabled_rules) - 5} more disabled rules\n"
            
            return summary.strip()
            
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
            
            enabled_rules = [r for r in rules if r.get('enabled', False)]
            disabled_rules = [r for r in rules if not r.get('enabled', False)]
            
            summary = f"**UniFi Port Forwarding Rules - {site_name}** ({len(rules)} total)\n\n"
            
            if enabled_rules:
                summary += f"✅ **Active Rules** ({len(enabled_rules)})\n"
                for rule in enabled_rules:
                    name = rule.get("name", "Unnamed Rule")
                    protocol = rule.get("proto", "Unknown").upper()
                    external_port = rule.get("dst_port", "Unknown")
                    internal_ip = rule.get("fwd", "Unknown")
                    internal_port = rule.get("fwd_port", "Unknown")
                    source = rule.get("src", "any")
                    log_enabled = rule.get("log", False)
                    
                    summary += f"• **{name}**\n"
                    summary += f"  • {protocol} {external_port} → {internal_ip}:{internal_port}\n"
                    if source != "any":
                        summary += f"  • Source: {source}\n"
                    if log_enabled:
                        summary += f"  • Logging: 📄 Enabled\n"
                    summary += "\n"
            
            if disabled_rules:
                summary += f"❌ **Disabled Rules** ({len(disabled_rules)})\n"
                for rule in disabled_rules[:5]:  # Limit to 5 disabled rules
                    name = rule.get("name", "Unnamed Rule")
                    protocol = rule.get("proto", "Unknown").upper()
                    external_port = rule.get("dst_port", "Unknown")
                    internal_ip = rule.get("fwd", "Unknown")
                    internal_port = rule.get("fwd_port", "Unknown")
                    
                    summary += f"• **{name}** ({protocol} {external_port} → {internal_ip}:{internal_port})\n"
                
                if len(disabled_rules) > 5:
                    summary += f"• ... and {len(disabled_rules) - 5} more disabled rules\n"
            
            return summary.strip()
            
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
            
            return summary.strip()
            
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
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error in site channels resource for {site_name}: {e}")
            return f"Error retrieving wireless channels for site {site_name}: {str(e)}"