"""
Enums for UniFi MCP Server unified tool interface.

Defines all available actions that can be performed through the consolidated unifi tool.
"""

from enum import Enum


class UnifiAction(str, Enum):
    """Enumeration of all available UniFi actions.

    This enum defines the complete set of operations available through the
    unified unifi tool. Each action corresponds to a previously separate tool.
    """

    # Device Management Actions (4)
    GET_DEVICES = "get_devices"
    GET_DEVICE_BY_MAC = "get_device_by_mac"
    RESTART_DEVICE = "restart_device"
    LOCATE_DEVICE = "locate_device"

    # Client Management Actions (7)
    GET_CLIENTS = "get_clients"
    RECONNECT_CLIENT = "reconnect_client"
    BLOCK_CLIENT = "block_client"
    UNBLOCK_CLIENT = "unblock_client"
    FORGET_CLIENT = "forget_client"
    SET_CLIENT_NAME = "set_client_name"
    SET_CLIENT_NOTE = "set_client_note"

    # Network Configuration Actions (8)
    GET_SITES = "get_sites"
    GET_WLAN_CONFIGS = "get_wlan_configs"
    GET_NETWORK_CONFIGS = "get_network_configs"
    GET_PORT_CONFIGS = "get_port_configs"
    GET_PORT_FORWARDING_RULES = "get_port_forwarding_rules"
    GET_FIREWALL_RULES = "get_firewall_rules"
    GET_FIREWALL_GROUPS = "get_firewall_groups"
    GET_STATIC_ROUTES = "get_static_routes"

    # Monitoring and Statistics Actions (11)
    GET_CONTROLLER_STATUS = "get_controller_status"
    GET_EVENTS = "get_events"
    GET_ALARMS = "get_alarms"
    GET_DPI_STATS = "get_dpi_stats"
    GET_ROGUE_APS = "get_rogue_aps"
    START_SPECTRUM_SCAN = "start_spectrum_scan"
    GET_SPECTRUM_SCAN_STATE = "get_spectrum_scan_state"
    AUTHORIZE_GUEST = "authorize_guest"
    GET_SPEEDTEST_RESULTS = "get_speedtest_results"
    GET_IPS_EVENTS = "get_ips_events"

    # Authentication Action (1)
    GET_USER_INFO = "get_user_info"


# Action categorization for service routing
DEVICE_ACTIONS = {
    UnifiAction.GET_DEVICES,
    UnifiAction.GET_DEVICE_BY_MAC,
    UnifiAction.RESTART_DEVICE,
    UnifiAction.LOCATE_DEVICE,
}

CLIENT_ACTIONS = {
    UnifiAction.GET_CLIENTS,
    UnifiAction.RECONNECT_CLIENT,
    UnifiAction.BLOCK_CLIENT,
    UnifiAction.UNBLOCK_CLIENT,
    UnifiAction.FORGET_CLIENT,
    UnifiAction.SET_CLIENT_NAME,
    UnifiAction.SET_CLIENT_NOTE,
}

NETWORK_ACTIONS = {
    UnifiAction.GET_SITES,
    UnifiAction.GET_WLAN_CONFIGS,
    UnifiAction.GET_NETWORK_CONFIGS,
    UnifiAction.GET_PORT_CONFIGS,
    UnifiAction.GET_PORT_FORWARDING_RULES,
    UnifiAction.GET_FIREWALL_RULES,
    UnifiAction.GET_FIREWALL_GROUPS,
    UnifiAction.GET_STATIC_ROUTES,
}

MONITORING_ACTIONS = {
    UnifiAction.GET_CONTROLLER_STATUS,
    UnifiAction.GET_EVENTS,
    UnifiAction.GET_ALARMS,
    UnifiAction.GET_DPI_STATS,
    UnifiAction.GET_ROGUE_APS,
    UnifiAction.START_SPECTRUM_SCAN,
    UnifiAction.GET_SPECTRUM_SCAN_STATE,
    UnifiAction.AUTHORIZE_GUEST,
    UnifiAction.GET_SPEEDTEST_RESULTS,
    UnifiAction.GET_IPS_EVENTS,
}

AUTH_ACTIONS = {
    UnifiAction.GET_USER_INFO,
}

# Actions that require MAC address parameter
MAC_REQUIRED_ACTIONS = {
    UnifiAction.GET_DEVICE_BY_MAC,
    UnifiAction.RESTART_DEVICE,
    UnifiAction.LOCATE_DEVICE,
    UnifiAction.RECONNECT_CLIENT,
    UnifiAction.BLOCK_CLIENT,
    UnifiAction.UNBLOCK_CLIENT,
    UnifiAction.FORGET_CLIENT,
    UnifiAction.SET_CLIENT_NAME,
    UnifiAction.SET_CLIENT_NOTE,
    UnifiAction.START_SPECTRUM_SCAN,
    UnifiAction.GET_SPECTRUM_SCAN_STATE,
    UnifiAction.AUTHORIZE_GUEST,
}

# Actions that don't use site_name parameter
NO_SITE_ACTIONS = {
    UnifiAction.GET_SITES,
    UnifiAction.GET_CONTROLLER_STATUS,
    UnifiAction.GET_USER_INFO,
}