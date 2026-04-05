# Upstream Service Integration

How unifi-mcp integrates with the UniFi Network Controller API.

## Upstream Service

**UniFi Network Controller** — Ubiquiti's network management platform running on UDM Pro, UDM SE, Cloud Gateway Max, or self-hosted UniFi Network Application.

## Authentication

UniFi uses **session-based authentication** with username and password. There are no API keys.

### UDM Pro / UniFi OS Devices

1. POST `/api/auth/login` with `{"username": "...", "password": "..."}`
2. Response sets `TOKEN` cookie (JWT)
3. Decode JWT to extract `csrfToken` from payload
4. Include `X-CSRF-Token` header on all subsequent requests
5. Session persists via cookies; reauthenticate on 401

### Legacy Controllers (Self-Hosted)

1. POST `/api/login` with `{"username": "...", "password": "...", "remember": true}`
2. Response sets `unifises` session cookie
3. CSRF token from response headers
4. Session persists via cookies; reauthenticate on 401

### Important Notes

- **Local admin only** — UniFi Cloud (SSO) accounts do not work for direct API access
- **Self-signed certificates** — Most controllers use self-signed certs; set `UNIFI_VERIFY_SSL=false`
- **Session timeout** — Sessions expire after ~30 minutes; the client handles reauthentication

## API Base Paths

| Controller Type | API Base | Login Endpoint |
|----------------|----------|----------------|
| UDM Pro / UniFi OS | `/proxy/network/api` | `/api/auth/login` |
| Legacy (self-hosted) | `/api` | `/api/login` |

## API Endpoints Used

### Device Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/stat/device` | GET | List all devices |
| `/cmd/devmgr` | POST | Device commands (restart, locate, spectrum scan) |

### Client Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/stat/sta` | GET | List connected clients |
| `/cmd/stamgr` | POST | Client commands (kick, block, unblock, forget, authorize guest) |
| `/list/user` | GET | List known users (for ID resolution) |
| `/upd/user/{id}` | POST | Update user name/note |

### Network Configuration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/self/sites` | GET | List all sites |
| `/rest/wlanconf` | GET | WLAN configurations |
| `/rest/networkconf` | GET | Network/VLAN configurations |
| `/rest/portconf` | GET | Port profile configurations |
| `/list/portforward` | GET | Port forwarding rules |
| `/rest/firewallrule` | GET | Firewall rules |
| `/rest/firewallgroup` | GET | Firewall groups |
| `/rest/routing` | GET | Static routes |

### Monitoring

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/system` | GET | Controller status (UDM Pro only) |
| `/stat/event` | POST | Events (legacy) |
| `/v2/api/site/{site}/events` | GET | Events (UDM Pro v2 API) |
| `/list/alarm` | GET | Alarms |
| `/stat/health` | GET | Site health |
| `/stat/dashboard` | GET | Dashboard metrics |
| `/stat/dpi` | GET | DPI statistics |
| `/stat/rogueap` | POST | Rogue access points |
| `/stat/report/archive.speedtest` | POST | Speed test history |
| `/stat/ips/event` | POST | IPS/IDS events |
| `/stat/spectrum-scan/{mac}` | GET | Spectrum scan results |

## URL Construction

All site-specific endpoints use the pattern:

```
{controller_url}{api_base}/s/{site_name}{endpoint}
```

For example:
```
https://192.168.1.1/proxy/network/api/s/default/stat/device
```

Site-independent endpoints (like `/self/sites`):
```
{controller_url}{api_base}{endpoint}
```

## Response Format

Most UniFi API responses follow this pattern:

```json
{
  "meta": {"rc": "ok"},
  "data": [...]
}
```

The client extracts the `data` array automatically. Error responses have `meta.rc != "ok"` with a `meta.msg` error message.

## Known Limitations

- **Events API**: Network Application 10.x removed the legacy `/stat/event` endpoint. The server falls back gracefully and suggests using `get_alarms` instead.
- **v2 API**: Available on modern UDM firmware (5.x+). The server tries v2 first, falls back to legacy.
- **Rate limiting**: No explicit rate limiting, but rapid authentication attempts may trigger temporary lockouts.

## See Also

- [AUTH](../mcp/AUTH.md) — Authentication reference
- [CONFIG](../CONFIG.md) — Controller URL and credential configuration
- [Ubiquiti API Documentation](https://ubntwiki.com/products/software/unifi-controller/api) — Community API reference
