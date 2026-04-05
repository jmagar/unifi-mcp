# MCP UI Patterns

Protocol-level UI patterns for unifi-mcp tool responses.

## Response Format

All tool responses use `ToolResult` with two layers:

### Human-Readable Layer (`content`)

Compact, token-efficient text designed for LLM consumption:

```
Devices (5 total)
  Cloud Gateway Max | UCGMAX | Online | 192.168.1.1 | Up: 14d 3h
  UniFi 6 Pro AP    | U6Pro  | Online | 192.168.1.2 | Up: 14d 3h
  UniFi 24-Port SW  | USW24  | Online | 192.168.1.3 | Up: 14d 3h
```

### Structured Layer (`structured_content`)

Machine-readable JSON for programmatic access:

```json
{
  "success": true,
  "message": "Retrieved 5 devices",
  "data": [
    {"name": "Cloud Gateway Max", "model": "UCGMAX", "status": "Online", "ip": "192.168.1.1"}
  ]
}
```

## Text Formatting Conventions

### Lists

Items are formatted as compact single-line summaries with pipe separators:

```
Clients (42 total)
  iPhone 15 | Wireless | 192.168.1.100 | -45 dBm | 120 Mbps
  MacBook Pro | Wired | 192.168.1.101 | — | 1 Gbps
```

### Tables

Port configs and firewall rules use aligned column format:

```
Port Profiles (8 total)
  En Profile Name                  Native VLAN Tagged Count PoE Mode Port Security
  -- ----------------------------  ----------- ------------ -------- -------------
  ✓  All                           Default     0            auto     ✗
  ✓  IoT                           10          2            auto     ✗
```

### Status Indicators

| Indicator | Meaning |
|-----------|---------|
| `✓` | Enabled/Online/OK |
| `✗` | Disabled/Offline/Fail |

### Data Formatting

- Byte values: Auto-converted to KB/MB/GB via `format_bytes()`
- Timestamps: Converted to ISO 8601 via `format_timestamp()`
- MAC addresses: Displayed in uppercase colon format
- Uptime: Formatted as `Xd Yh Zm`

## Error Responses

```
Error: Device with MAC aa:bb:cc:dd:ee:ff not found
```

Errors always start with `Error:` prefix in the text layer and have an `"error"` key in structured content.

## Truncation

Responses exceeding 512 KB are truncated:

```
... [truncated]
```

The structured content is not truncated — only the text layer.

## See Also

- [TOOLS.md](TOOLS.md) — Tool reference
- [PATTERNS.md](PATTERNS.md) — Code patterns
