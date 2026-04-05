# Plugin Checklist

Pre-release and quality checklist. Complete all items before tagging a release.

## Version and Metadata

- [ ] Version is consistent across all files:
  - `pyproject.toml` `[project].version`
  - `.claude-plugin/plugin.json` `version`
  - `.codex-plugin/plugin.json` `version`
  - `gemini-extension.json` `version`
  - `.app.json` `version`
  - `server.json` `version` and `packages[0].version`
- [ ] `CHANGELOG.md` has an entry for the new version
- [ ] Version sync CI job passes (`just check-contract`)

## Security

- [ ] `.env` is in `.gitignore`
- [ ] `.env` is in `.dockerignore`
- [ ] No credentials in code, docs, or commit history
- [ ] `UNIFI_MCP_TOKEN` is required by default (no `NO_AUTH=true` in production)
- [ ] Dockerfile runs as non-root user (`USER unifi`)
- [ ] Docker security checks pass (`scripts/check-docker-security.sh`)
- [ ] No baked env vars in Docker image (`scripts/check-no-baked-env.sh`)
- [ ] Ignore files are complete (`scripts/ensure-ignore-files.sh --check`)

## CI/CD

- [ ] All CI jobs pass: lint, typecheck, test, version-sync, contract-drift, docker-security
- [ ] Docker image builds for `linux/amd64` and `linux/arm64`
- [ ] PyPI publish workflow validated (tag trigger, version match)
- [ ] MCP Registry publish step included in PyPI workflow

## MCP Protocol

- [ ] `unifi` tool registered with correct parameter schema
- [ ] `unifi_help` tool returns accurate documentation
- [ ] All 31 actions are routable and tested
- [ ] Destructive actions require `confirm=true` or env var bypass
- [ ] Response size capped at 512 KB with truncation indicator
- [ ] Health endpoint returns 200 without authentication
- [ ] Bearer auth middleware validates tokens on all non-health routes

## Plugin Surfaces

- [ ] `.claude-plugin/plugin.json` has valid `userConfig` entries
- [ ] `.codex-plugin/plugin.json` has valid `interface` and `skills` paths
- [ ] `gemini-extension.json` has correct `mcpServers` config
- [ ] `server.json` follows MCP Registry schema
- [ ] `hooks/hooks.json` defines SessionStart and PostToolUse hooks
- [ ] `skills/unifi/SKILL.md` matches actual tool surface

## Testing

- [ ] Unit tests pass with 80%+ coverage (`just test`)
- [ ] Live integration tests pass against a real controller (`just test-live`)
- [ ] Health endpoint is reachable (`just health`)

## Documentation

- [ ] `docs/` directory has all required files
- [ ] Tool documentation matches actual parameter schema
- [ ] Resource URIs documented and match registered resources
- [ ] No template placeholders remain in docs
