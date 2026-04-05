# Justfile Recipes

Standard task runner recipes. Run `just --list` to see all available recipes.

## Development

| Recipe | Command | Description |
|--------|---------|-------------|
| `just dev` | `uv run python -m unifi_mcp.main` | Start dev server |

## Code Quality

| Recipe | Command | Description |
|--------|---------|-------------|
| `just lint` | `uv run ruff check .` | Lint with ruff |
| `just fmt` | `uv run ruff format .` | Format with ruff |
| `just typecheck` | `uv run ty check unifi_mcp` | Type check with ty |
| `just check` | lint + typecheck | All quality checks |

## Build

| Recipe | Command | Description |
|--------|---------|-------------|
| `just build` | `uv pip install -e .` | Install editable package |

## Tests

| Recipe | Command | Description |
|--------|---------|-------------|
| `just test` | `uv run pytest tests/ -v` | Run unit tests |
| `just test-live` | curl + json.tool | Live integration test |

## Docker

| Recipe | Command | Description |
|--------|---------|-------------|
| `just up` | `docker compose up -d` | Start containers |
| `just down` | `docker compose down` | Stop containers |
| `just restart` | `docker compose restart` | Restart containers |
| `just logs` | `docker compose logs -f` | Tail container logs |
| `just health` | curl health endpoint | Check health |

## Setup

| Recipe | Command | Description |
|--------|---------|-------------|
| `just setup` | `uv sync` | Install dependencies |
| `just gen-token` | python secrets | Generate bearer token |

## Validation

| Recipe | Command | Description |
|--------|---------|-------------|
| `just check-contract` | `echo "ok"` | Check contract drift (no-op) |
| `just validate-skills` | `echo "ok"` | Validate skill definitions (no-op) |

## Cleanup

| Recipe | Command | Description |
|--------|---------|-------------|
| `just clean` | rm -rf artifacts | Remove build artifacts and caches |

## Release

| Recipe | Command | Description |
|--------|---------|-------------|
| `just publish patch` | version bump + tag + push | Publish patch release |
| `just publish minor` | version bump + tag + push | Publish minor release |
| `just publish major` | version bump + tag + push | Publish major release |

## See Also

- [DEV](../mcp/DEV.md) — Development workflow
- [SCRIPTS.md](SCRIPTS.md) — Script reference
