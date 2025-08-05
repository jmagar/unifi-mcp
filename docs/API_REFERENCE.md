Of course. Based on the Python code you provided for the `UnifiController` class, here is a comprehensive documentation of all the API endpoints it interacts with.

The endpoints are grouped by their general function (e.g., Site Management, Device Management, Client Management, etc.). Note that, as mentioned in the code's docstring, these are **undocumented private APIs**, and their behavior or existence may change between UniFi Controller versions. The path parameters like `{site_name}`, `{device_id}`, and `{mac}` are placeholders.

### Authentication

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `authenticate` | `POST` | `/api/login` | Authenticates with a legacy UniFi Controller. |
| `authenticate` | `POST` | `/api/auth/login` | Authenticates with a UniFi OS Controller (UDM Pro, Cloud Key G2+, etc.). |

---

### Site, System, and Health Endpoints

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_unifi_site` | `GET` | `/api/self/sites` | Fetches basic information for all sites. |
| `get_unifi_site` | `GET` | `/api/stat/sites` | Fetches detailed information, including health metrics, for all sites. |
| `get_unifi_site_health` | `GET` | `/api/s/{site_name}/stat/health` | Retrieves detailed health and status for each subsystem of a specific site. |
| `get_controller_status` | `GET` | `/status` | Checks the basic status of the controller. Does not always require login. |
| `get_sysinfo` | `GET` | `/api/s/{site_name}/stat/sysinfo` | Fetches system information for the controller and site. |
| `get_self` | `GET` | `/api/s/{site_name}/self` | Retrieves information about the currently authenticated user and their session. |
| `get_site_settings` | `GET` | `/api/s/{site_name}/get/setting` | Fetches a collection of all configuration settings for a specific site. |
| `get_auto_backups` | `POST` | `/api/s/{site_name}/cmd/backup` | Lists available automatic controller backups. |
| `get_site_admins` | `POST` | `/api/s/{site_name}/cmd/sitemgr` | Fetches a list of administrators with access to the specified site. |
| `get_all_admins` | `GET` | `/api/stat/admin` | Fetches a list of all administrators on the entire controller. |
| `reboot_cloudkey` | `POST` | `/api/s/{site_name}/cmd/system` | Sends a command to reboot the controller hardware (e.g., Cloud Key). |

---

### Device Information & Management

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_unifi_site_device` | `GET` | `/api/s/{site_name}/stat/device-basic` | Retrieves a basic list of devices for a site. |
| `get_unifi_site_device` | `GET` | `/api/s/{site_name}/stat/device` | Retrieves a detailed list of devices for a site. |
| `get_device_name_mappings` | `GET` | `/dl/firmware/bundles.json` | Fetches the official device model and name mappings from the controller. |
| `get_device_tags` | `GET` | `/api/s/{site_name}/rest/tag` | Fetches all device tags configured for the site (Controller v5.5+). |
| `adopt_device` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Adopts a device into the specified site. |
| `adopt_device_advanced` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Adopts a device using custom SSH credentials and inform URL. |
| `delete_device` | `POST` | `/api/s/{site_name}/cmd/sitemgr` | Forgets/deletes a device from a site. |
| `disable_device` | `PUT` | `/api/s/{site_name}/rest/device/{device_id}` | Disables or enables a specific device. |
| `force_provision_device`| `POST` | `/api/s/{site_name}/cmd/devmgr/` | Forces a device to re-provision its configuration. |
| `locate_device` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Enables (`set-locate`) or disables (`unset-locate`) the flashing LED on a device. |
| `migrate_device` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Migrates a device to a new controller by setting its inform URL. |
| `cancel_migrate_device`| `POST` | `/api/s/{site_name}/cmd/devmgr` | Cancels an in-progress device migration. |
| `move_device_to_site` | `POST` | `/api/s/{current_site}/cmd/sitemgr` | Moves a device from its current site to a different site. |
| `power_cycle_switch_port`| `POST` | `/api/s/{site_name}/cmd/devmgr` | Issues a PoE power-cycle command to a specific port on a UniFi switch. |
| `restart_device` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Reboots one or more devices (soft or hard/PoE cycle). |
| `set_device_led_override`| `PUT` | `/api/s/{site_name}/rest/device/{device_id}`| Sets the LED mode for a specific device ('on', 'off', or 'default'). |
| `set_device_name` | `POST` | `/api/s/{site_name}/upd/device/{device_id}`| Sets the alias/name for a specific device. |
| `set_device_radio_settings`| `POST` | `/api/s/{site_name}/upd/device/{device_id}`| Updates radio settings (channel, power, etc.) for an AP. |
| `set_device_wlan_group`| `POST` | `/api/s/{site_name}/upd/device/{device_id}`| Assigns a device's radio to a specific WLAN group. |
| `set_device_settings_base`| `PUT` | `/api/s/{site_name}/rest/device/{device_id}`| Generic endpoint to update multiple device settings with a PUT request. |
| `start_spectrum_scan` | `POST` | `/api/s/{site_name}/cmd/devmgr` | Starts an RF spectrum scan on a specific AP. |
| `get_spectrum_scan_state`| `GET` | `/api/s/{site_name}/stat/spectrum-scan/{ap_mac}` | Checks the status and results of an ongoing or completed RF scan. |

---

### Client (Station) Information & Management

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_unifi_site_client` | `GET` | `/api/s/{site_name}/stat/sta` | Fetches a list of currently active clients on a site. |
| `get_all_known_clients` | `GET` | `/api/s/{site_name}/list/user` | Fetches all clients that have ever connected to the site (including offline). |
| `get_all_clients_history`| `POST` | `/api/s/{site_name}/stat/alluser` | Fetches historical data for all clients that connected within a given time. |
| `get_client_details`| `GET` | `/api/s/{site_name}/stat/user/{mac}` | Fetches detailed information for a single client by its MAC address. |
| `get_guests` | `POST` | `/api/s/{site_name}/stat/guest` | Fetches a list of guest clients with valid access within a specified time. |
| `get_active_clients_v2` | `GET` | `/v2/api/site/{site_name}/clients/active` | V2 API to fetch active clients. |
| `get_offline_clients_v2`| `GET` | `/v2/api/site/{site_name}/clients/history`| V2 API to fetch historical (offline) clients. |
| `get_fingerprint_devices_v2`|`GET`| `/v2/api/fingerprint_devices/{fingerprint_source}`| V2 API to fetch client device fingerprints. |
| `authorize_client_guest`| `POST` | `/api/s/{site_name}/cmd/stamgr` | Authorizes a guest client for a specified duration with optional limits. |
| `unauthorize_client_guest`|`POST`| `/api/s/{site_name}/cmd/stamgr` | Revokes network access for a guest client. |
| `reconnect_client`| `POST` | `/api/s/{site_name}/cmd/stamgr` | Forces a wireless client to disconnect and reconnect (kicks the client). |
| `block_client` | `POST` | `/api/s/{site_name}/cmd/stamgr` | Blocks a client from accessing the network. |
| `unblock_client`| `POST` | `/api/s/{site_name}/cmd/stamgr` | Unblocks a previously blocked client. |
| `forget_client` | `POST` | `/api/s/{site_name}/cmd/stamgr` | Removes historical data for one or more clients. |
| `create_client_user`| `POST` | `/api/s/{site_name}/group/user` | Pre-defines a client entry, assigning it to a user group. |
| `assign_client_to_group`| `POST`| `/api/s/{site_name}/upd/user/{client_id}`| Moves a client to a different user group. |
| `set_client_note` | `POST` | `/api/s/{site_name}/upd/user/{client_id}`| Adds, modifies, or removes the note for a specific client. |
| `set_client_name` | `POST` | `/api/s/{site_name}/upd/user/{client_id}`| Sets or removes the alias/name for a specific client. |
| `set_client_name_rest` | `PUT` | `/api/s/{site_name}/rest/user/{client_id}` | Updates a client's name using the REST endpoint. |
| `set_client_fixed_ip` | `PUT` | `/api/s/{site_name}/rest/user/{client_id}` | Sets or removes a fixed IP address for a client. |

---

### Configuration Listings

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_unifi_site_wlanconf` | `GET` | `/api/s/{site_name}/rest/wlanconf` | Fetches all WLAN (Wi-Fi network) configurations for a site. |
| `get_unifi_site_wlanconf` | `GET` | `/api/s/{site_name}/rest/wlanconf/{wlan_id}` | Fetches a single WLAN configuration by its ID. |
| `get_unifi_site_networkconf`|`GET`| `/api/s/{site_name}/rest/networkconf` | Fetches all network (LAN, VLAN, etc.) configurations for a site. |
| `get_unifi_site_networkconf`|`GET`| `/api/s/{site_name}/rest/networkconf/{network_id}`| Fetches a single network configuration by its ID. |
| `get_unifi_site_portconf`| `GET` | `/api/s/{site_name}/rest/portconf` | Fetches all port profile configurations for a site. |
| `get_wlan_groups` | `GET` | `/api/s/{site_name}/list/wlangroup` | Fetches the list of WLAN groups for a site. |
| `get_port_forwarding_rules`|`GET`| `/api/s/{site_name}/list/portforward` | Fetches the list of all configured port forwarding rules. |
| `get_firewall_groups` | `GET` | `/api/s/{site_name}/rest/firewallgroup` | Fetches all configured firewall groups. |
| `get_firewall_groups` | `GET` | `/api/s/{site_name}/rest/firewallgroup/{group_id}` | Fetches a single firewall group by its ID. |
| `get_firewall_rules` | `GET` | `/api/s/{site_name}/rest/firewallrule` | Fetches all configured firewall rules. |
| `get_current_channels` | `GET` | `/api/s/{site_name}/stat/current-channel` | Fetches the list of currently available Wi-Fi channels based on country settings. |
| `get_country_codes` | `GET` | `/api/s/{site_name}/stat/ccode` | Fetches the list of available country codes. |
| `get_static_routes` | `GET` | `/api/s/{site_name}/rest/routing` | Fetches all configured static routes. |
| `get_static_routes` | `GET` | `/api/s/{site_name}/rest/routing/{route_id}` | Fetches a single static route by its ID. |
| `get_dynamic_dns_config`| `GET` | `/api/s/{site_name}/rest/dynamicdns` | Fetches the dynamic DNS configurations for the site. |
| `get_voip_extensions` | `GET` | `/api/s/{site_name}/list/extension` | Fetches configured VoIP extensions. |

---

### User Group Management

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `list_user_groups`| `GET` | `/api/s/{site_name}/list/usergroup` | Fetches all user groups for a site. |
| `create_user_group`| `POST` | `/api/s/{site_name}/rest/usergroup` | Creates a new user group with specified bandwidth limits. |
| `edit_user_group` | `PUT` | `/api/s/{site_name}/rest/usergroup/{group_id}`| Modifies an existing user group. |
| `delete_user_group`| `DELETE`| `/api/s/{site_name}/rest/usergroup/{group_id}`| Deletes a user group. |

---

### Statistics, Events, and Reporting

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_unifi_site_event`| `POST` | `/api/s/{site_name}/stat/event` | Fetches a list of system events for a site. |
| `get_unifi_site_alarm`| `GET`/`POST`| `/api/s/{site_name}/list/alarm` | Fetches a list of alarms (alerts and warnings) for a site. |
| `get_unifi_site_rogueap`| `POST` | `/api/s/{site_name}/stat/rogueap` | Fetches a list of neighboring ("rogue") access points detected. |
| `count_alarms` | `GET` | `/api/s/{site_name}/cnt/alarm` | Counts the number of alarms (all or un-archived). |
| `get_site_stats_5minutes`| `POST` | `/api/s/{site_name}/stat/report/5minutes.site`| Fetches 5-minute interval statistics for the entire site. |
| `get_site_stats_hourly`| `POST` | `/api/s/{site_name}/stat/report/hourly.site`| Fetches hourly statistics for the entire site. |
| `get_site_stats_daily` | `POST` | `/api/s/{site_name}/stat/report/daily.site`| Fetches daily statistics for the entire site. |
| `get_site_stats_monthly`| `POST` | `/api/s/{site_name}/stat/report/monthly.site`| Fetches monthly statistics for the entire site. |
| `get_aps_stats_5minutes`| `POST` | `/api/s/{site_name}/stat/report/5minutes.ap`| Fetches 5-minute interval statistics for access points. |
| `get_aps_stats_hourly`| `POST` | `/api/s/{site_name}/stat/report/hourly.ap`| Fetches hourly statistics for access points. |
| `get_aps_stats_daily` | `POST` | `/api/s/{site_name}/stat/report/hourly.user`| (BUG in code) Fetches hourly client stats instead of daily AP stats. |
| `get_client_stats_5minutes`|`POST`| `/api/s/{site_name}/stat/report/5minutes.user`| Fetches 5-minute statistics for clients. |
| `get_client_stats_hourly`| `POST` | `/api/s/{site_name}/stat/report/hourly.user`| Fetches hourly statistics for clients. |
| `get_client_stats_daily`| `POST` | `/api/s/{site_name}/stat/report/daily.user`| Fetches daily statistics for clients. |
| `get_client_stats_monthly`|`POST`| `/api/s/{site_name}/stat/report/monthly.user`| Fetches monthly statistics for clients. |
| `get_gateway_stats_5minutes`|`POST`|`/api/s/{site_name}/stat/report/5minutes.gw`| Fetches 5-minute statistics for the site's gateway. |
| `get_gateway_stats_hourly`|`POST`| `/api/s/{site_name}/stat/report/hourly.gw`| Fetches hourly statistics for the site's gateway. |
| `get_gateway_stats_daily`|`POST` | `/api/s/{site_name}/stat/report/daily.gw`| Fetches daily statistics for the site's gateway. |
| `get_gateway_stats_monthly`|`POST`|`/api/s/{site_name}/stat/report/monthly.gw`| Fetches monthly statistics for the site's gateway. |
| `get_speedtest_results`|`POST` | `/api/s/{site_name}/stat/report/archive.speedtest`| Fetches historical speed test results. |
| `get_ips_events` | `POST` | `/api/s/{site_name}/stat/ips/event` | Fetches IPS/IDS threat detection events. |
| `get_client_sessions`| `POST` | `/api/s/{site_name}/stat/session` | Fetches client connection/disconnection sessions over a time period. |
| `get_client_sessions_latest`|`POST`|`/api/s/{site_name}/stat/session` | Fetches the last 'n' sessions for a specific client. |
| `get_authorizations`| `POST` | `/api/s/{site_name}/stat/authorization`| Fetches client authorization records (e.g., guest portal logins). |
| `get_port_forward_stats`|`GET` | `/api/s/{site_name}/stat/portforward` | Fetches traffic statistics for port forwarding rules. |
| `get_dpi_stats` | `GET` | `/api/s/{site_name}/stat/dpi` | Fetches overall Deep Packet Inspection (DPI) statistics for the site. |
| `get_dpi_stats_filtered`|`POST`| `/api/s/{site_name}/stat/sitedpi` | Fetches DPI stats grouped by application or category. |
| `get_dashboard_metrics`|`GET` | `/api/s/{site_name}/stat/dashboard` | Fetches the time-series data used to power the main dashboard graphs. |

---

### Hotspot & RADIUS

| Function Name | HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- | :--- |
| `get_vouchers` | `POST` | `/api/s/{site_name}/stat/voucher` | Fetches hotspot voucher information. |
| `get_payments` | `GET` | `/api/s/{site_name}/stat/payment` | Fetches hotspot payment records. |
| `get_hotspot_operators`| `GET` | `/api/s/{site_name}/rest/hotspotop` | Fetches configured hotspot operators. |
| `get_radius_profiles` | `GET` | `/api/s/{site_name}/rest/radiusprofile` | Fetches RADIUS server profiles (Controller v5.5.19+). |
| `get_radius_accounts` | `GET` | `/api/s/{site_name}/rest/account` | Fetches RADIUS user accounts (Controller v5.5.19+). |