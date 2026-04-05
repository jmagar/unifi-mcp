# Memory Files

Claude Code memory system for persistent knowledge across sessions.

## What is Memory

Claude Code stores learned facts about a project in memory files. These persist across sessions and help the model maintain context about project-specific patterns, decisions, and conventions.

## CLAUDE.md

The primary memory file for unifi-mcp is `CLAUDE.md` in the repository root. It contains:

- Project context and package structure
- Development commands
- Key architecture patterns (auth flow, data formatting, MCP patterns)
- Critical implementation details (MAC handling, site parameters, error handling)
- Controller type detection (`UNIFI_IS_UDM_PRO`)
- Configuration requirements
- Testing and logging patterns
- Version bumping rules

## Session Memory

Session-specific memory is managed by the Claude Code framework. The `CLAUDE.md` file is read at the start of each session to establish project context.

## Keeping Memory Current

When making architectural changes:
1. Update `CLAUDE.md` with new patterns or changed conventions
2. Update relevant docs in `docs/` for detailed reference
3. The model reads `CLAUDE.md` at session start and uses docs for deeper context

## See Also

- Root `CLAUDE.md` — Primary project instructions
- [REPO.md](REPO.md) — Repository structure
