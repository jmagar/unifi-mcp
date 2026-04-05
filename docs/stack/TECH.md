# Technology Choices

Technology stack reference for unifi-mcp.

## Language

**Python 3.10+**

Chosen for:
- FastMCP framework availability
- Async/await for non-blocking I/O
- Pydantic for input validation
- Rich ecosystem for HTTP clients

## MCP Framework

**FastMCP 2.12.0**

- Provides `@mcp.tool()` and `@mcp.resource()` decorators
- Handles MCP JSON-RPC protocol
- Supports HTTP (streamable) and stdio transports
- Generates JSON Schema from Python type annotations

## HTTP Client

**httpx >= 0.28.1**

- Async HTTP client for UniFi controller communication
- Cookie-based session management
- Connection pooling and timeout handling
- SSL verification toggle support

## Web Framework

**FastAPI >= 0.116.1 + Uvicorn >= 0.30.0**

- FastAPI used implicitly via FastMCP's HTTP app
- Starlette wraps the app for /health endpoint and middleware
- Uvicorn as the ASGI server

## Configuration

**python-dotenv >= 1.1.1**

- Loads `.env` files for environment variables
- Supports override mode for explicit precedence

## Validation

**Pydantic (via FastMCP)**

- `UnifiParams` model validates all tool input
- Field validators for type-specific constraints
- Model validators for cross-field requirements

## Type Checking

**ty >= 0.0.1a6**

- Astral's type checker for Python
- Faster than mypy for CI

## Linting

**ruff >= 0.12.7**

- Linting and formatting in a single tool
- Replaces flake8, isort, black
- Configured for 100-character line length

## Testing

**pytest >= 8.4.1**

- pytest-asyncio for async test support
- pytest-cov for coverage reporting (80% minimum)
- inline-snapshot for snapshot testing

## Build

**uv (astral-sh)**

- Fast Python package manager
- Lockfile for reproducible builds
- `uv sync` for dependency installation
- `uv build` for package building

## Container

**Docker with multi-stage build**

- Builder: Python 3.11 slim + uv for dependency installation
- Runtime: Python 3.11 slim, non-root user, minimal dependencies
- Platforms: linux/amd64, linux/arm64

## Task Runner

**Just (casey/just)**

- Simple command runner
- Loads `.env` automatically (`set dotenv-load := true`)
- Cross-platform

## See Also

- [PRE-REQS.md](PRE-REQS.md) — Prerequisites
- [ARCH.md](ARCH.md) — Architecture overview
