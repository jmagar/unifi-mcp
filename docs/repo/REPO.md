# Repository Structure

Standard layout for unifi-mcp.

## Directory Tree

```
unifi-mcp/
├── .claude-plugin/
│   └── plugin.json              # Claude Code plugin manifest
├── .codex-plugin/
│   └── plugin.json              # Codex plugin manifest
├── .github/
│   └── workflows/
│       ├── ci.yml               # CI: lint, test, security
│       ├── docker-publish.yml   # Docker image build and push
│       └── publish-pypi.yml     # PyPI and MCP Registry publish
├── assets/
│   ├── icon.png                 # Plugin icon
│   └── logo.svg                 # Plugin logo
├── docs/                        # Documentation (this tree)
│   ├── mcp/                     # MCP server docs
│   ├── plugin/                  # Plugin surface docs
│   ├── repo/                    # Repository docs
│   ├── stack/                   # Technology stack docs
│   └── upstream/                # Upstream service docs
├── bin/
│   └── sync-uv.sh               # SessionStart hook: sync uv environment
├── hooks/
│   └── hooks.json               # Hook definitions
├── scripts/
│   └── smoke-test.sh
├── skills/
│   └── unifi/
│       └── SKILL.md             # Bundled skill definition
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_formatters.py
│   ├── test_server.py
│   ├── test_integration.py
│   └── test_live.sh             # Live integration tests
├── unifi_mcp/                   # Python package
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── server.py                # FastMCP server
│   ├── client.py                # UniFi API client
│   ├── config.py                # Configuration
│   ├── formatters.py            # Data formatting
│   ├── models/
│   │   ├── enums.py             # Action enum
│   │   └── params.py            # Parameter model
│   ├── services/
│   │   ├── base.py              # Base service
│   │   ├── unifi_service.py     # Router
│   │   ├── device_service.py
│   │   ├── client_service.py
│   │   ├── network_service.py
│   │   └── monitoring_service.py
│   ├── resources/
│   │   ├── overview_resources.py
│   │   ├── device_resources.py
│   │   ├── client_resources.py
│   │   ├── network_resources.py
│   │   ├── monitoring_resources.py
│   │   └── site_resources.py
│   └── tools/
│       ├── device_tools.py
│       ├── client_tools.py
│       ├── network_tools.py
│       └── monitoring_tools.py
├── .env.example                 # Environment template
├── .mcp.json                    # MCP server config
├── .app.json                    # App metadata
├── lefthook.yml
├── CHANGELOG.md
├── CLAUDE.md                    # Claude Code instructions
├── Dockerfile
├── Justfile
├── LICENSE                      # MIT
├── README.md
├── docker-compose.yaml
├── entrypoint.sh
├── gemini-extension.json
├── pyproject.toml
├── server.json                  # MCP Registry entry
└── uv.lock
```

## See Also

- [SCRIPTS.md](SCRIPTS.md) — Script reference
- [RECIPES.md](RECIPES.md) — Justfile recipes
