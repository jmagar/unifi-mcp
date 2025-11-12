"""Type definitions for UniFi API responses and data structures."""

from typing import TypedDict, Union, List, Optional


# Base UniFi API Response
class UniFiMeta(TypedDict, total=False):
    """UniFi API metadata."""
    rc: str
    msg: str


class UniFiResponse(TypedDict, total=False):
    """Base UniFi API response structure."""
    meta: UniFiMeta
    data: Union[List['UniFiDevice'], List['UniFiClient'], List['UniFiSite'], List[dict[str, 'JSONValue']], dict[str, 'JSONValue']]


# Device Types
class UniFiDevice(TypedDict, total=False):
    """UniFi device data structure."""
    _id: str
    mac: str
    name: str
    model: str
    type: str
    ip: str
    state: int
    adopted: bool
    disabled: bool
    version: str
    uptime: int
    last_seen: int
    upgradable: bool
    upgrade_to_firmware: str
    bytes: int
    tx_bytes: int
    rx_bytes: int
    num_sta: int
    user_num_sta: int
    guest_num_sta: int
    uplink: dict[str, 'JSONValue']
    config_network: dict[str, 'JSONValue']
    port_table: List[dict[str, 'JSONValue']]
    ethernet_table: List[dict[str, 'JSONValue']]
    temperatures: List[float]
    cpu: float
    mem: float
    system_stats: dict[str, 'JSONValue']
    site_id: str
    site_name: str


# Client Types
class UniFiClient(TypedDict, total=False):
    """UniFi client data structure."""
    _id: str
    mac: str
    name: str
    hostname: str
    ip: str
    network: str
    network_id: str
    oui: str
    is_wired: bool
    is_guest: bool
    essid: str
    bssid: str
    channel: int
    radio: str
    radio_proto: str
    rssi: int
    signal: int
    noise: int
    tx_rate: int
    rx_rate: int
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_retries: int
    rx_retries: int
    uptime: int
    last_seen: int
    first_seen: int
    idle_time: int
    satisfaction: int
    blocked: bool
    note: str
    site_id: str


# Site Types  
class UniFiSite(TypedDict, total=False):
    """UniFi site data structure."""
    _id: str
    name: str
    desc: str
    attr_hidden_id: str
    attr_no_delete: bool
    role: str


# Network Configuration Types
class UniFiNetwork(TypedDict, total=False):
    """UniFi network configuration."""
    _id: str
    name: str
    purpose: str
    vlan: int
    vlan_enabled: bool
    ip_subnet: str
    networkgroup: str
    dhcpd_enabled: bool
    dhcpd_start: str
    dhcpd_stop: str
    dhcp_relay_enabled: bool
    dhcpd_dns_enabled: bool
    dhcpd_gateway_enabled: bool
    dhcpd_time_offset_enabled: bool
    domain_name: str
    site_id: str


class UniFiWLAN(TypedDict, total=False):
    """UniFi WLAN configuration."""
    _id: str
    name: str
    enabled: bool
    security: str
    wpa_mode: str
    wpa_enc: str
    usergroup_id: str
    wlangroup_id: str
    hide_ssid: bool
    is_guest: bool
    vlan: int
    vlan_enabled: bool
    minrate_ng_enabled: bool
    minrate_ng_advertising_rates: bool
    minrate_ng_data_rate_kbps: int
    site_id: str


# Dashboard & Statistics Types
class UniFiDashboard(TypedDict, total=False):
    """UniFi dashboard metrics."""
    time: int
    wan_rx_bytes: int
    wan_tx_bytes: int
    wan2_rx_bytes: int
    wan2_tx_bytes: int
    wlan_rx_bytes: int
    wlan_tx_bytes: int
    lan_rx_bytes: int
    lan_tx_bytes: int
    num_ap: int
    num_adopted: int
    num_disabled: int
    num_disconnected: int
    num_pending: int
    num_sta: int
    num_user: int
    num_guest: int
    rx_bytes: int
    tx_bytes: int
    latency_avg: float


# DPI Statistics Types
class UniFiDPIStat(TypedDict, total=False):
    """UniFi DPI (Deep Packet Inspection) statistic."""
    app: int
    cat: int
    name: str
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int


# Event Types
class UniFiEvent(TypedDict, total=False):
    """UniFi event data."""
    _id: str
    time: int
    datetime: str
    key: str
    msg: str
    subsystem: str
    site_id: str
    user: str
    ap: str
    ap_name: str
    client: str
    guest: str
    hostname: str
    duration: int


# Alarm Types
class UniFiAlarm(TypedDict, total=False):
    """UniFi alarm data."""
    _id: str
    time: int
    datetime: str
    key: str
    msg: str
    archived: bool
    site_id: str
    subsystem: str


# Port Forwarding Types
class UniFiPortForward(TypedDict, total=False):
    """UniFi port forwarding rule."""
    _id: str
    name: str
    enabled: bool
    src: str
    dst_port: str
    fwd: str
    fwd_port: str
    proto: str
    log: bool
    site_id: str


# Firewall Types
class UniFiFirewallRule(TypedDict, total=False):
    """UniFi firewall rule."""
    _id: str
    name: str
    enabled: bool
    action: str
    protocol: str
    protocol_match_excepted: bool
    logging: bool
    src_firewallgroup_ids: List[str]
    src_mac_address: str
    src_address: str
    src_networkconf_id: str
    src_networkconf_type: str
    dst_firewallgroup_ids: List[str]
    dst_address: str
    dst_networkconf_id: str
    dst_networkconf_type: str
    dst_port: str
    rule_index: int
    site_id: str


class UniFiFirewallGroup(TypedDict, total=False):
    """UniFi firewall group."""
    _id: str
    name: str
    group_type: str
    group_members: List[str]
    site_id: str


# Static Route Types
class UniFiStaticRoute(TypedDict, total=False):
    """UniFi static route."""
    _id: str
    name: str
    enabled: bool
    static_route_network: str
    static_route_distance: int
    static_route_nexthop: str
    static_route_type: str
    site_id: str


# Controller Status Types
class UniFiControllerStatus(TypedDict, total=False):
    """UniFi controller status."""
    up: bool
    version: str
    server_version: str
    hostname: str
    https_port: int
    is_setup: bool
    timezone: str
    uptime: int


# Speed Test Types
class UniFiSpeedTest(TypedDict, total=False):
    """UniFi speed test result."""
    _id: str
    time: int
    status_download: int
    status_ping: int
    status_summary: int
    status_upload: int
    xput_download: float
    xput_upload: float
    latency: int
    test_server: str


# IPS Event Types  
class UniFiIPSEvent(TypedDict, total=False):
    """UniFi IPS (Intrusion Prevention System) event."""
    _id: str
    time: int
    datetime: str
    catname: str
    signature: str
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    inner_alert_gid: int
    inner_alert_rev: int
    inner_alert_signature: str
    inner_alert_signature_id: int


# Rogue AP Types
class UniFiRogueAP(TypedDict, total=False):
    """UniFi rogue access point."""
    _id: str
    age: int
    ap_mac: str
    band: str
    bssid: str
    bw: int
    center_freq: int
    channel: int
    essid: str
    freq: int
    is_adhoc: bool
    is_rogue: bool
    is_ubnt: bool
    last_seen: int
    noise: int
    oui: str
    radio: str
    radio_name: str
    report_time: int
    rssi: int
    rssi_age: int
    security: str
    signal: int
    site_id: str


# Guest Authorization Types
class UniFiGuestAuth(TypedDict, total=False):
    """UniFi guest authorization data."""
    mac: str
    minutes: int
    up: Optional[int]
    down: Optional[int]
    bytes: Optional[int]
    ap_mac: str


# JSON Value type for recursive structures
JSONValue = Union[
    None,
    bool,
    int,
    float,
    str,
    List['JSONValue'],
    dict[str, 'JSONValue']
]

# Union types for API responses
UniFiData = Union[
    List[UniFiDevice],
    List[UniFiClient],
    List[UniFiSite],
    List[UniFiNetwork],
    List[UniFiWLAN],
    List[UniFiDPIStat],
    List[UniFiEvent],
    List[UniFiAlarm],
    List[UniFiPortForward],
    List[UniFiFirewallRule],
    List[UniFiFirewallGroup],
    List[UniFiStaticRoute],
    List[UniFiSpeedTest],
    List[UniFiIPSEvent],
    List[UniFiRogueAP],
    UniFiDashboard,
    UniFiControllerStatus,
    List[dict[str, JSONValue]],
    dict[str, JSONValue]
]

# Error response type
class ErrorResponse(TypedDict):
    """Error response structure."""
    error: str


# Command response type for actions like restart, locate, etc.
class CommandResponse(TypedDict, total=False):
    """Command response structure."""
    meta: UniFiMeta
    data: List[dict[str, JSONValue]]
