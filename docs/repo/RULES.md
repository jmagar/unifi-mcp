# Coding Rules

Standards and conventions enforced across unifi-mcp.

## Git Workflow

### Branch Strategy

- `main` — production-ready code
- Feature branches for new functionality
- PR required before merge

### Commit Conventions

```
<type>(<scope>): <description>
```

Types:
- `feat` — new feature (minor bump)
- `feat!` — breaking change (major bump)
- `fix` — bug fix (patch bump)
- `docs` — documentation (patch bump)
- `refactor` — code restructure (patch bump)
- `test` — test changes (patch bump)
- `chore` — maintenance (patch bump)

### Version Bumping

Every feature branch push must bump the version in ALL version-bearing files. See [PUBLISH](../mcp/PUBLISH.md).

## Python Standards

### Style

- Line length: 100 characters
- Target: Python 3.10+
- Formatter: ruff format
- Linter: ruff check

### Type Hints

- All function signatures must have type hints
- Use `str | None` syntax (not `Optional[str]`)
- Pydantic models for validation

### Imports

- Standard library first, then third-party, then local
- Enforced by ruff `I` rule (isort)

### Error Handling

- Return error objects instead of raising exceptions in service layer
- Use `create_error_result()` for consistent error ToolResults
- Log errors with context (action, MAC, etc.)

### Naming

| Convention | Usage |
|------------|-------|
| `snake_case` | functions, variables, module names |
| `PascalCase` | classes |
| `SCREAMING_SNAKE` | constants, enum values |
| `kebab-case` | file names (scripts), Docker names |

## Security Rules

- Never commit `.env` files
- Never log credentials (even at DEBUG)
- Use `compare_digest()` for token comparison
- Validate all input via Pydantic models
- Cap response sizes (512 KB)

## Testing Rules

- 80% coverage minimum (enforced by pytest-cov)
- Async tests with `asyncio_mode = "auto"`
- Mark external-dependency tests with `@pytest.mark.integration`

## See Also

- [PRE-COMMIT](../mcp/PRE-COMMIT.md) — Pre-commit hooks
- [DEV](../mcp/DEV.md) — Development workflow
