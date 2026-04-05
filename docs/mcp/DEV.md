# Development Workflow

Day-to-day development guide for unifi-mcp.

## Setup

```bash
git clone https://github.com/jmagar/unifi-mcp
cd unifi-mcp
uv sync
cp .env.example .env
chmod 600 .env
# Edit .env with your credentials
```

## Run

```bash
# Local dev server
just dev
# or
uv run python -m unifi_mcp.main

# Docker
just up
just logs
```

## Code Quality

```bash
# Lint with ruff
just lint
# or
uv run ruff check .

# Format with ruff
just fmt
# or
uv run ruff format .

# Type check with ty
just typecheck
# or
uv run ty check unifi_mcp

# All quality checks
just check
```

## Testing

```bash
# Unit tests with coverage
just test
# or
uv run pytest tests/ -v

# Live integration test (requires running server)
just test-live
# or
curl -sf http://localhost:8001/health | python3 -m json.tool

# Health check
just health
```

Test coverage target: 80% (enforced by `--cov-fail-under=80`).

## Project Layout

```
unifi_mcp/
  __init__.py
  main.py          # Entry point, create_app(), cli()
  server.py        # UniFiMCPServer class, tool registration
  client.py        # UnifiControllerClient (httpx-based)
  config.py        # UniFiConfig, ServerConfig, env loading
  formatters.py    # Data formatting utilities
  models/
    enums.py       # UnifiAction enum, action categories
    params.py      # UnifiParams Pydantic model
  services/
    base.py        # BaseService ABC
    unifi_service.py  # Router: action -> domain service
    device_service.py
    client_service.py
    network_service.py
    monitoring_service.py
  resources/
    overview_resources.py
    device_resources.py
    client_resources.py
    network_resources.py
    monitoring_resources.py
    site_resources.py
  tools/
    device_tools.py
    client_tools.py
    network_tools.py
    monitoring_tools.py
```

## Adding a New Action

1. Add the action to `UnifiAction` enum in `models/enums.py`
2. Add it to the appropriate category set (e.g., `DEVICE_ACTIONS`)
3. Add to `MAC_REQUIRED_ACTIONS` if it needs a MAC address
4. Add to `DESTRUCTIVE_ACTIONS` if it modifies state
5. Implement the handler in the appropriate service (e.g., `device_service.py`)
6. Add the handler to the service's `action_map`
7. Update the help text in `server.py` `_register_help_tool()`
8. Add tests in `tests/`
9. Update `skills/unifi/SKILL.md`

## Adding a New Resource

1. Create a resource function in the appropriate module under `resources/`
2. Register it with `@mcp.resource("unifi://uri")` decorator
3. Add to `__init__.py` exports if creating a new module
4. Register the module in `server.py` `initialize()`

## Dependency Management

```bash
# Add a runtime dependency
uv add package-name

# Add a dev dependency
uv add --extra dev package-name

# Sync lockfile
uv sync
```

## Common Justfile Recipes

```bash
just --list        # Show all recipes
just dev           # Start dev server
just test          # Run tests
just lint          # Lint
just fmt           # Format
just check         # Lint + typecheck
just up            # Docker compose up
just down          # Docker compose down
just logs          # Docker compose logs
just health        # Health check
just gen-token     # Generate bearer token
just clean         # Remove build artifacts
just publish       # Tag and release
```

## See Also

- [TESTS.md](TESTS.md) — Detailed testing guide
- [PRE-COMMIT.md](PRE-COMMIT.md) — Pre-commit hooks
- [PATTERNS.md](PATTERNS.md) — Code patterns
