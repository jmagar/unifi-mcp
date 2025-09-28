"""
Network service for UniFi MCP Server.

Handles all network configuration operations including sites, WLANs, networks,
port configurations, and security settings.
"""

import logging
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .base import BaseService
from ..models.enums import UnifiAction
from ..models.params import UnifiParams
from ..formatters import (
    format_site_summary,
    format_sites_list,
    format_wlans_list,
    format_networks_list,
    format_port_forwarding_list,
    format_firewall_rules_list,
    format_firewall_groups_list,
    format_static_routes_list,
)

logger = logging.getLogger(__name__)


class NetworkService(BaseService):
    """Service for network configuration operations.

    Provides consolidated access to network configurations, site information,
    and security settings.
    """

    async def execute_action(self, params: UnifiParams) -> ToolResult:
        """Execute network-related actions.

        Args:
            params: Validated parameters containing action and arguments

        Returns:
            ToolResult with action response
        """
        action_map = {
            UnifiAction.GET_SITES: self._get_sites,
            UnifiAction.GET_WLAN_CONFIGS: self._get_wlan_configs,
            UnifiAction.GET_NETWORK_CONFIGS: self._get_network_configs,
            UnifiAction.GET_PORT_CONFIGS: self._get_port_configs,
            UnifiAction.GET_PORT_FORWARDING_RULES: self._get_port_forwarding_rules,
            UnifiAction.GET_FIREWALL_RULES: self._get_firewall_rules,
            UnifiAction.GET_FIREWALL_GROUPS: self._get_firewall_groups,
            UnifiAction.GET_STATIC_ROUTES: self._get_static_routes,
        }

        handler = action_map.get(params.action)
        if not handler:
            return self.create_error_result(
                f"Network action {params.action} not supported"
            )

        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"Error executing network action {params.action}: {e}")
            return self.create_error_result(str(e))

    async def _get_sites(self, params: UnifiParams) -> ToolResult:
        """Get all controller sites with health information."""
        try:
            sites = await self.client.get_sites()

            # Check for error response
            if isinstance(sites, dict) and "error" in sites:
                return self.create_error_result(sites.get('error','unknown error'), sites)

            if not isinstance(sites, list):
                return self.create_error_result("Unexpected response format")

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

            summary_text = format_sites_list(sites)
            return self.create_success_result(
                text=summary_text,
                data=formatted_sites,
                success_message=f"Retrieved {len(formatted_sites)} sites"
            )

        except Exception as e:
            logger.error(f"Error getting sites: {e}")
            return self.create_error_result(str(e))

    async def _get_wlan_configs(self, params: UnifiParams) -> ToolResult:
        """Get wireless network (WLAN) configurations."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            wlans = await self.client.get_wlan_configs(site_name)

            # Check for error response
            error_result = self.check_list_response(wlans, params.action)
            if error_result:
                return error_result

            # Format WLAN configs for clean output
            formatted_wlans = []
            for wlan in wlans:
                formatted_wlan = {
                    "name": wlan.get("name", "Unknown WLAN"),
                    # SSID is typically under 'ssid' (fallback to profile 'name')
                    "ssid": wlan.get("ssid", wlan.get("name", "Unknown SSID")),
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

            summary_text = format_wlans_list(wlans)
            return self.create_success_result(
                text=summary_text,
                data=formatted_wlans,
                success_message=f"Retrieved {len(formatted_wlans)} WLAN configurations"
            )

        except Exception as e:
            logger.error(f"Error getting WLAN configs: {e}")
            return self.create_error_result(str(e))

    async def _get_network_configs(self, params: UnifiParams) -> ToolResult:
        """Get network/VLAN configurations."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            networks = await self.client.get_network_configs(site_name)

            # Check for error response
            error_result = self.check_list_response(networks, params.action)
            if error_result:
                return error_result

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

            summary_text = format_networks_list(networks)
            return self.create_success_result(
                text=summary_text,
                data=formatted_networks,
                success_message=f"Retrieved {len(formatted_networks)} network configurations"
            )

        except Exception as e:
            logger.error(f"Error getting network configs: {e}")
            return self.create_error_result(str(e))

    async def _get_port_configs(self, params: UnifiParams) -> ToolResult:
        """Get switch port profile configurations."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            ports = await self.client.get_port_configs(site_name)

            # Check for error response
            error_result = self.check_list_response(ports, params.action)
            if error_result:
                return error_result

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

            # Compact summary: name | VLAN/native | PoE | Security
            lines = [f"Port Profiles ({len(formatted_ports)} total)"]
            lines.append(f"  {'En':<2} {'Profile Name':<28} {'Native VLAN':<11} {'Tagged Count':<13} {'PoE Mode':<8} {'Port Security':<13}")
            lines.append(f"  {'-'*2:<2} {'-'*28:<28} {'-'*11:<11} {'-'*13:<13} {'-'*8:<8} {'-'*13:<13}")
            for p in formatted_ports[:40]:
                en = '✓' if p.get('enabled') else '✗'
                name = str(p.get('name',''))[:28]
                native = str(p.get('native_vlan','Default'))[:11]
                tagged = str(len(p.get('tagged_vlans',[]) or []))[:13]
                poe = str(p.get('poe_mode','auto'))[:8]
                sec = '✓' if p.get('port_security') else '✗'
                lines.append(f"  {en:<2} {name:<28} {native:<11} {tagged:<13} {poe:<8} {sec:<13}")
            if len(formatted_ports) > 40:
                lines.append(f"  ... and {len(formatted_ports)-40} more")
            summary_text = "\n".join(lines)
            return self.create_success_result(
                text=summary_text,
                data=formatted_ports,
                success_message=f"Retrieved {len(formatted_ports)} port configurations"
            )

        except Exception as e:
            logger.error(f"Error getting port configs: {e}")
            return self.create_error_result(str(e))

    async def _get_port_forwarding_rules(self, params: UnifiParams) -> ToolResult:
        """Get port forwarding rules."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            rules = await self.client.get_port_forwarding_rules(site_name)

            # Check for error response
            error_result = self.check_list_response(rules, params.action)
            if error_result:
                return error_result

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

            summary_text = format_port_forwarding_list(formatted_rules)
            return self.create_success_result(
                text=summary_text,
                data=formatted_rules,
                success_message=f"Retrieved {len(formatted_rules)} port forwarding rules"
            )

        except Exception as e:
            logger.error(f"Error getting port forwarding rules: {e}")
            return self.create_error_result(str(e))

    async def _get_firewall_rules(self, params: UnifiParams) -> ToolResult:
        """Get firewall rules for security audit and management."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            rules = await self.client._make_request("GET", "/rest/firewallrule", site_name=site_name)

            # Check for error response
            if isinstance(rules, dict) and "error" in rules:
                return self.create_error_result(rules.get('error','unknown error'), rules)

            if not isinstance(rules, list):
                return self.create_error_result(f"Unexpected response format: {type(rules).__name__}", {"error": f"Unexpected response format: {type(rules).__name__}", "data": rules})

            # Add debug info if no rules found
            if not rules:
                empty = [{"message": "No firewall rules found", "rule_count": 0}]
                return ToolResult(
                    content=[TextContent(type="text", text="Firewall Rules (0 total)\n  -")],
                    structured_content=empty
                )

            # Format firewall rules for clean output
            formatted_rules = []
            for rule in rules:
                formatted_rule = {
                    "name": rule.get("name", "Unnamed Rule"),
                    "enabled": rule.get("enabled", False),
                    "action": rule.get("action", "unknown"),
                    "protocol": rule.get("protocol", "all"),
                    "src_address": rule.get("src_address", "any"),
                    "src_port": rule.get("src_port", "any"),
                    "dst_address": rule.get("dst_address", "any"),
                    "dst_port": rule.get("dst_port", "any"),
                    "ruleset": rule.get("ruleset", "unknown"),
                    "index": rule.get("rule_index", None),
                    "logging": rule.get("logging", False),
                    "established": rule.get("state_established", False),
                    "related": rule.get("state_related", False)
                }
                formatted_rules.append(formatted_rule)

            summary_text = format_firewall_rules_list(formatted_rules)
            return self.create_success_result(
                text=summary_text,
                data=formatted_rules,
                success_message=f"Retrieved {len(formatted_rules)} firewall rules"
            )

        except Exception as e:
            logger.error(f"Error getting firewall rules: {e}")
            return self.create_error_result(str(e))

    async def _get_firewall_groups(self, params: UnifiParams) -> ToolResult:
        """Get firewall groups for security management."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            groups = await self.client._make_request("GET", "/rest/firewallgroup", site_name=site_name)

            # Check for error response
            error_result = self.check_list_response(groups, params.action)
            if error_result:
                return error_result

            # Format firewall groups for clean output
            formatted_groups = []
            for group in groups:
                formatted_group = {
                    "name": group.get("name", "Unnamed Group"),
                    "group_type": group.get("group_type", "unknown"),
                    "group_members": group.get("group_members", []),
                    "member_count": len(group.get("group_members", [])),
                    "description": group.get("description", "No description")
                }
                formatted_groups.append(formatted_group)

            summary_text = format_firewall_groups_list(formatted_groups)
            return self.create_success_result(
                text=summary_text,
                data=formatted_groups,
                success_message=f"Retrieved {len(formatted_groups)} firewall groups"
            )

        except Exception as e:
            logger.error(f"Error getting firewall groups: {e}")
            return self.create_error_result(str(e))

    async def _get_static_routes(self, params: UnifiParams) -> ToolResult:
        """Get static routes for advanced network routing analysis."""
        try:
            defaults = params.get_action_defaults()
            site_name = defaults.get('site_name', 'default')

            routes = await self.client._make_request("GET", "/rest/routing", site_name=site_name)

            # Check for error response
            error_result = self.check_list_response(routes, params.action)
            if error_result:
                return error_result

            # Format static routes for clean output
            formatted_routes = []
            for route in routes:
                formatted_route = {
                    "name": route.get("name", "Unnamed Route"),
                    "enabled": route.get("enabled", False),
                    "destination": route.get("static-route_network", "unknown"),
                    "distance": route.get("static-route_distance", "unknown"),
                    "gateway": route.get("static-route_nexthop", "unknown"),
                    "interface": route.get("static-route_interface", "auto"),
                    "type": route.get("type", "static")
                }
                formatted_routes.append(formatted_route)

            summary_text = format_static_routes_list(formatted_routes)
            return self.create_success_result(
                text=summary_text,
                data=formatted_routes,
                success_message=f"Retrieved {len(formatted_routes)} static routes"
            )

        except Exception as e:
            logger.error(f"Error getting static routes: {e}")
            return self.create_error_result(str(e))