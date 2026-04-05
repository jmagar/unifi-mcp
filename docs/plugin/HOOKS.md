# Hook Configuration

Lifecycle hooks that run automatically during Claude Code sessions.

## File Location

`hooks/hooks.json`

## Hook Definitions

### SessionStart

Runs when a Claude Code session begins:

| Hook | Script | Timeout | Purpose |
|------|--------|---------|---------|
| sync-env | `hooks/scripts/sync-env.sh` | 10s | Copy userConfig credentials to `.env` |
| ensure-ignore-files | `hooks/scripts/ensure-ignore-files.sh` | 5s | Verify `.gitignore` and `.dockerignore` entries |

### PostToolUse

Runs after Write, Edit, MultiEdit, or Bash tool calls:

| Hook | Script | Timeout | Purpose |
|------|--------|---------|---------|
| fix-env-perms | `hooks/scripts/fix-env-perms.sh` | 5s | Enforce `chmod 600` on `.env` |
| ensure-ignore-files | `hooks/scripts/ensure-ignore-files.sh` | 5s | Re-verify ignore file entries |

## Hook Scripts

### `sync-env.sh`

Reads userConfig values from the plugin framework and writes them to `.env`. Creates the file if it does not exist.

### `fix-env-perms.sh`

Checks `.env` file permissions and sets `chmod 600` if needed. Prevents accidental permission changes during file editing.

### `ensure-ignore-files.sh`

Verifies that `.gitignore` contains `.env` and other sensitive patterns. Verifies that `.dockerignore` excludes `.env`, `.git`, and build artifacts.

## Configuration Format

```json
{
  "description": "Sync userConfig credentials to .env and enforce permissions",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/sync-env.sh", "timeout": 10},
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/ensure-ignore-files.sh", "timeout": 5}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/fix-env-perms.sh", "timeout": 5},
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/ensure-ignore-files.sh", "timeout": 5}
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
