# MCP Elicitation

Destructive operation confirmation flow in unifi-mcp.

## Overview

Destructive actions require explicit confirmation before execution. This prevents accidental device restarts, client blocks, or data deletion.

## Destructive Actions

| Action | Effect |
|--------|--------|
| `restart_device` | Reboots a network device (AP, switch, gateway) |
| `block_client` | Blocks a client from all network access |
| `forget_client` | Permanently removes all client history and statistics |
| `reconnect_client` | Forcibly disconnects and reconnects a client |

## Confirmation Flow

### Step 1: Initial Call (No Confirmation)

```json
{"action": "restart_device", "mac": "aa:bb:cc:dd:ee:ff"}
```

### Step 2: Server Returns Gate Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "'restart_device' is a destructive operation. Pass confirm=true to proceed, or set UNIFI_MCP_ALLOW_DESTRUCTIVE=true / UNIFI_MCP_ALLOW_YOLO=true in the environment to bypass."
    }
  ],
  "structured_content": {
    "error": "confirmation_required",
    "action": "restart_device"
  }
}
```

### Step 3: Confirmed Call

```json
{"action": "restart_device", "mac": "aa:bb:cc:dd:ee:ff", "confirm": true}
```

## Bypass Paths

Three paths to bypass the confirmation gate:

| Path | Method | Use Case |
|------|--------|----------|
| Parameter | `confirm=true` on the tool call | Per-call confirmation |
| Environment | `UNIFI_MCP_ALLOW_DESTRUCTIVE=true` | CI/automation |
| YOLO mode | `UNIFI_MCP_ALLOW_YOLO=true` | Testing (skips all safety) |

### Resolution Order

The gate checks in order:
1. `UNIFI_MCP_ALLOW_DESTRUCTIVE` or `ALLOW_DESTRUCTIVE` env var
2. `UNIFI_MCP_ALLOW_YOLO` or `ALLOW_YOLO` env var
3. `confirm=true` parameter

If any check passes, the action proceeds without prompting.

## Implementation

The gate is implemented in `UniFiMCPServer._check_destructive()`:

- Returns `None` if action is not destructive (proceed)
- Returns `None` if any bypass is active (proceed)
- Returns `ToolResult` with `confirmation_required` error otherwise

The check happens before the action is dispatched to the service layer.

## See Also

- [TOOLS.md](TOOLS.md) — Tool reference with destructive action markers
- [GUARDRAILS](../GUARDRAILS.md) — Security guardrails
- [ENV.md](ENV.md) — Safety gate environment variables
