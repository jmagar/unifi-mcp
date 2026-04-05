# Pre-commit Hook Configuration

Pre-commit hooks for unifi-mcp. These run locally before each commit and are also enforced in CI.

## Setup

```bash
uv sync --extra dev
uv run pre-commit install
```

## Configuration

Defined in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Hooks

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| `ruff` | Lint Python code | yes (with `--fix`) |
| `ruff-format` | Format Python code | yes |

## Ruff Configuration

From `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH", "RUF"]
```

### Rule Sets

| Code | Category |
|------|----------|
| E | pycodestyle errors |
| F | pyflakes |
| W | pycodestyle warnings |
| I | isort (import sorting) |
| N | PEP8 naming |
| UP | pyupgrade |
| B | flake8-bugbear |
| A | flake8-builtins |
| SIM | flake8-simplify |
| TCH | flake8-type-checking |
| RUF | ruff-specific rules |

## CI Enforcement

The `lint` job in CI runs the same checks:

```bash
uv run ruff check unifi_mcp/ tests/
uv run ruff format --check unifi_mcp/ tests/
```

## See Also

- [DEV.md](DEV.md) — Development workflow
- [CICD.md](CICD.md) — CI configuration
