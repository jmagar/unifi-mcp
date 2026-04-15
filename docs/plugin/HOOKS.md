# Hook Configuration

Lifecycle hooks that run automatically during Claude Code sessions.

## File Location

`hooks/hooks.json`

## Hook Definitions

### SessionStart

Runs when a Claude Code session begins:

| Hook | Script | Purpose |
|------|--------|---------|
| sync-uv | `bin/sync-uv.sh` | Sync uv environment |

## Configuration Format

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/bin/sync-uv.sh"}
        ]
      }
    ]
  }
}
```

The `${CLAUDE_PLUGIN_ROOT}` variable resolves to the plugin installation directory.

## See Also

- [CONFIG.md](CONFIG.md) — Plugin settings
- [GUARDRAILS](../GUARDRAILS.md) — Security patterns
