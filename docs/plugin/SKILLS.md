# Skill Definitions

Bundled skill definitions for unifi-mcp.

## Directory Structure

```
skills/
  unifi/
    SKILL.md    # Skill definition for Claude Code
```

## Bundled Skill: `unifi`

The `unifi` skill provides Claude Code with knowledge about the UniFi MCP tool surface. It describes available actions, parameters, and usage patterns so the model can invoke tools correctly.

### Location

`skills/unifi/SKILL.md`

### Contents

The skill file covers:
- Available tool names (`unifi`, `unifi_help`)
- All 31 actions organized by domain
- Parameter descriptions and defaults
- Destructive operation handling
- Example invocations

### How Skills Work

When installed as a plugin, Claude Code reads `SKILL.md` files from the `skills/` directory. The skill content is injected into the model's context, giving it the knowledge needed to use the MCP tools effectively.

The `.codex-plugin/plugin.json` references skills via:

```json
{
  "skills": "./skills/"
}
```

## Adding a Skill

To add a new skill:

1. Create `skills/<name>/SKILL.md`
2. Follow the skill format with frontmatter and sections
3. The plugin framework discovers it automatically from the `skills/` directory

## See Also

- [TOOLS](../mcp/TOOLS.md) — Tool reference
- [PLUGINS.md](PLUGINS.md) — Plugin manifest
