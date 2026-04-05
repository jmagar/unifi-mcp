# Channel Integration

Bidirectional messaging between Claude Code and external services.

## Current State

unifi-mcp does not define any channels. UniFi controller events are accessed via the `get_events` and `get_alarms` actions through polling, not real-time channels.

## Potential Future Channels

A UniFi event channel could push real-time controller events (device connects/disconnects, firmware updates, security alerts) to Claude Code sessions. This would require WebSocket or SSE support from the UniFi controller API.

## See Also

- [TOOLS](../mcp/TOOLS.md) — Event and alarm actions
- [PLUGINS.md](PLUGINS.md) — Plugin manifest
