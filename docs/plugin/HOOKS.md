# Hook Configuration - unifi-mcp

## Overview

`unifi-mcp` registers a `SessionStart` hook in `hooks/hooks.json` to keep the Python environment in sync with `uv.lock`.

## Hook definition

**File**: `hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/bin/sync-uv.sh"
          }
        ]
      }
    ]
  }
}
```

## Behavior

- The hook runs at session start before normal work begins.
- `bin/sync-uv.sh` runs `uv sync` against the repo root.
- The installed virtual environment lives under `${CLAUDE_PLUGIN_DATA}/.venv`.

## See Also

- [../GUARDRAILS.md](../GUARDRAILS.md) - Security patterns enforced by hooks
- [CONFIG.md](CONFIG.md) - Repository configuration and environment variables
