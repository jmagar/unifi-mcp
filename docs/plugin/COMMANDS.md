# Slash Commands

Patterns for defining user-invocable slash commands in Claude Code.

## Current State

unifi-mcp does not define any slash commands. All functionality is accessed through the `unifi` MCP tool.

## Adding Commands

If commands are needed in the future, create them in a `commands/` directory:

```
commands/
  unifi/
    status.md      # /unifi:status
    devices.md     # /unifi:devices
```

Each command file uses frontmatter for metadata:

```yaml
---
description: Check UniFi network status
allowed-tools: mcp__plugin_unifi-mcp_unifi-mcp__unifi
---

Check the status of the UniFi network by calling the unifi tool with action get_controller_status, then get_devices and get_clients.
```

## See Also

- [SKILLS.md](SKILLS.md) — Skill definitions (currently used instead of commands)
- [PLUGINS.md](PLUGINS.md) — Plugin manifest
