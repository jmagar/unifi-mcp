# UniFi MCP — Justfile
# Requires: just (https://github.com/casey/just)

set dotenv-load := true

# Default: list recipes
default:
    @just --list

# ── Development ──────────────────────────────────────────────────────────────

# Start dev server with auto-reload
dev:
    uv run python -m unifi_mcp.main

# ── Code Quality ─────────────────────────────────────────────────────────────

# Lint with ruff
lint:
    uv run ruff check .

# Format with ruff
fmt:
    uv run ruff format .

# Type-check with mypy
typecheck:
    uv run mypy unifi_mcp/

# Run all quality checks
check: lint typecheck

# ── Build ─────────────────────────────────────────────────────────────────────

# Build (install editable package)
build:
    uv pip install -e .

# ── Tests ─────────────────────────────────────────────────────────────────────

# Run unit tests
test:
    uv run pytest tests/ -v

# Run live integration tests (requires running server)
test-live:
    @echo "Running live integration tests against localhost:3003..."
    curl -sf http://localhost:3003/health | python3 -m json.tool

# ── Docker ────────────────────────────────────────────────────────────────────

# Start containers
up:
    docker compose up -d

# Stop containers
down:
    docker compose down

# Restart containers
restart:
    docker compose restart

# Tail container logs
logs:
    docker compose logs -f

# Check health endpoint
health:
    curl -sf http://localhost:3003/health | python3 -m json.tool

# ── Setup ─────────────────────────────────────────────────────────────────────

# Install dependencies
setup:
    uv sync

# Generate a secure token for UNIFI_MCP_TOKEN
gen-token:
    @python3 -c "import secrets; print(secrets.token_hex(32))"

# ── Validation ────────────────────────────────────────────────────────────────

# Check contract drift (skill tool names vs server)
check-contract:
    @bash scripts/lint-plugin.sh

# Validate skill definitions
validate-skills:
    @bash scripts/lint-plugin.sh

# ── Cleanup ───────────────────────────────────────────────────────────────────

# Remove build artifacts and caches
clean:
    rm -rf dist/ build/ *.egg-info __pycache__ .mypy_cache .ruff_cache .pytest_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
