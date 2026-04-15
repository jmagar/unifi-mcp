# Git Hook Configuration

Git hooks for unifi-mcp. These run locally before each commit and are also enforced in CI.

## Setup

```bash
uv sync --extra dev
lefthook install
```

## Configuration

Defined in `lefthook.yml`:

```yaml
pre-commit:
  parallel: true
  commands:
    diff_check:
      run: git diff --check --cached
    yaml:
      glob: "*.{yml,yaml}"
      run: uv run python -c 'import sys, yaml; [yaml.safe_load(open(path, "r", encoding="utf-8")) for path in sys.argv[1:]]' {staged_files}
    lint:
      run: just lint
    format:
      run: just fmt
    typecheck:
      run: just typecheck
```

## Hooks

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| `diff_check` | Detect trailing whitespace and conflict markers in staged diff | no |
| `yaml` | Validate staged YAML syntax | no |
| `lint` | Lint Python code with Ruff | no |
| `format` | Format Python code with Ruff | yes |
| `typecheck` | Run `ty` against `unifi_mcp` | no |

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
