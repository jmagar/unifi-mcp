# Agent Definitions

Patterns for defining autonomous agents within a Claude Code plugin.

## Current State

unifi-mcp does not define any agents. All functionality is tool-based through the `unifi` MCP tool.

## Adding Agents

If agents are needed (e.g., a network monitoring agent), create them in an `agents/` directory:

```
agents/
  network-monitor.md    # Autonomous network monitoring agent
```

Agent files define behavior, available tools, and workflow patterns for autonomous operation.

## See Also

- [SKILLS.md](SKILLS.md) — Skill definitions
- [PLUGINS.md](PLUGINS.md) — Plugin manifest
