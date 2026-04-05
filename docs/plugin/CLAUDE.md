# Plugin Surface Documentation

Index for the `plugin/` documentation subdirectory. These docs cover every Claude Code plugin surface area available to unifi-mcp.

## File Index

| File | Surface | Description |
|------|---------|-------------|
| [PLUGINS.md](PLUGINS.md) | Manifests | Plugin manifest files (.claude-plugin, .codex-plugin, gemini-extension) |
| [CONFIG.md](CONFIG.md) | Settings | userConfig, env sync, plugin settings |
| [HOOKS.md](HOOKS.md) | Hooks | SessionStart and PostToolUse lifecycle hooks |
| [SKILLS.md](SKILLS.md) | Skills | Bundled skill definitions |
| [COMMANDS.md](COMMANDS.md) | Commands | Slash commands (none currently) |
| [AGENTS.md](AGENTS.md) | Agents | Agent definitions (none currently) |
| [CHANNELS.md](CHANNELS.md) | Channels | Channel integration (none currently) |
| [OUTPUT-STYLES.md](OUTPUT-STYLES.md) | Output styles | Custom formatting (none currently) |
| [MARKETPLACES.md](MARKETPLACES.md) | Marketplaces | Claude, Codex, Gemini, MCP Registry |
| [SCHEDULES.md](SCHEDULES.md) | Schedules | Scheduled tasks (none currently) |

## Active Surfaces

unifi-mcp uses these plugin surfaces:

- **Plugin manifests** — Claude Code, Codex, Gemini
- **userConfig** — Credential management via plugin settings
- **Hooks** — Env sync, permission fixing, ignore file enforcement
- **Skills** — Bundled `unifi` skill with SKILL.md
- **MCP server** — Primary functionality via the `unifi` tool
