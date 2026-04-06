# Testing Guide

Testing patterns for unifi-mcp. All non-live testing is covered here; see [MCPORTER.md](MCPORTER.md) for end-to-end smoke tests.

## Unit Tests

```bash
just test
# or
uv run pytest tests/ -v
```

### Test Structure

```
tests/
  conftest.py          # Shared fixtures (mock client, mock config)
  test_client.py       # UnifiControllerClient tests
  test_config.py       # Configuration loading tests
  test_formatters.py   # Data formatting tests
  test_server.py       # Server initialization and tool registration
  test_integration.py  # Cross-module integration tests
  test_live.sh         # Live integration tests (shell script)
```

### Fixtures

Key fixtures in `conftest.py`:

- Mock UniFi client with predefined API responses
- Mock configurations for UDM Pro and legacy controllers
- Sample device, client, and event data

### Coverage

Coverage is enforced at 80% with branch coverage:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=unifi_mcp",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-fail-under=80",
]
```

Coverage reports are generated in `.cache/htmlcov/`.

### Async Testing

All tests use `asyncio_mode = "auto"` — async test functions are detected and run automatically.

```python
async def test_get_devices():
    result = await service.execute_action(params)
    assert result.structured_content["success"]
```

### Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.integration` | Requires an external UniFi controller |
| `@pytest.mark.client_process` | Spawns separate client processes |
| `@pytest.mark.slow` | Slow-running tests |

CI runs: `pytest -m "not slow and not integration"`

## Live Integration Tests

```bash
just test-live
# or
bash tests/test_live.sh
```

The live test script (`tests/test_live.sh`) tests against a running server:

1. Health endpoint check
2. Tool call: get_devices
3. Tool call: get_clients
4. Tool call: get_controller_status
5. Error handling for invalid actions
6. Bearer token validation

Requires `UNIFI_URL`, `UNIFI_USERNAME`, `UNIFI_PASSWORD` environment variables (set in CI secrets).

## Smoke Tests

```bash
bash bin/smoke-test.sh
```

Quick verification that the server starts, responds to health checks, and handles basic tool calls.

## Running in CI

CI configuration in `.github/workflows/ci.yml`:

| Job | What it runs |
|-----|-------------|
| `lint` | `ruff check` + `ruff format --check` |
| `typecheck` | `ty check unifi_mcp/` |
| `test` | `pytest -m "not slow and not integration"` |
| `version-sync` | Version consistency across all manifests |
| `docker-security` | Dockerfile security + no baked env + ignore files |
| `mcp-integration` | `tests/test_live.sh` (requires secrets) |

## See Also

- [MCPORTER.md](MCPORTER.md) — Live smoke testing
- [DEV.md](DEV.md) — Development workflow
- [CICD.md](CICD.md) — CI/CD configuration
