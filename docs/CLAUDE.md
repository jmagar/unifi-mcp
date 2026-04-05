# Documentation Index

Reference documentation for the unifi-mcp plugin.

## Directory index

### Root-level docs (this directory)

| File | Purpose |
| --- | --- |
| `README.md` | Main plugin README — badges, overview, tools, install, config, examples |
| `SETUP.md` | Step-by-step setup guide — clone, install, configure, verify |
| `CONFIG.md` | Configuration reference — all env vars, userConfig, .env conventions |
| `CHECKLIST.md` | Pre-release quality checklist — version sync, security, CI, registry |
| `GUARDRAILS.md` | Security guardrails — credentials, Docker, auth, input handling |
| `INVENTORY.md` | Component inventory — tools, resources, env vars, surfaces, deps |
| `CLAUDE.md` | This file — index and conventions for the docs tree |

### Subdirectories

| Directory | Scope |
| --- | --- |
| `mcp/` | MCP server docs: auth, transport, tools, resources, testing, deployment |
| `plugin/` | Plugin system docs: manifests, hooks, skills, commands, channels |
| `repo/` | Repository docs: git conventions, scripts, memory, rules |
| `stack/` | Technology stack docs: prerequisites, architecture, dependencies |
| `upstream/` | Upstream service docs: UniFi controller API, integration patterns |

## Cross-reference conventions

- Use relative links: `See [AUTH](mcp/AUTH.md)`, `See [CONFIG](CONFIG.md)`
- All env vars documented in both `CONFIG.md` (human reference) and `mcp/ENV.md` (machine-oriented)
- Tool documentation lives in `mcp/TOOLS.md`; resources in `mcp/RESOURCES.md`
