# tests/test_live.sh — Test Coverage Reference

## 1. Overview

`tests/test_live.sh` is the canonical **live integration test suite** for the `unifi-mcp` MCP server. It exercises the running server end-to-end against a real UniFi controller, verifying that the MCP protocol layer, authentication enforcement, and each exposed tool action all behave correctly.

**Service under test:** UniFi Network Controller (UDM Pro or standalone controller)

**MCP server under test:** `unifi-mcp` — a Python MCP server that wraps the UniFi controller REST API and exposes it as two MCP tools: `unifi` (multi-action dispatcher) and `unifi_help` (documentation tool).

**Transport modes exercised:**
- `http` — JSON-RPC over HTTP against a pre-existing running server
- `docker` — builds the server image from source, starts a container, runs the full HTTP test suite, then tears down
- `stdio` — spawns the server in-process via `uvx` and communicates over stdin/stdout using the MCP stdio protocol

The script exits `0` if all tests pass or are skipped, `1` if any test fails, and `2` if a prerequisite or startup failure prevents tests from running.

---

## 2. Running the Tests

### Prerequisites

| Mode | Required tools |
|------|----------------|
| `http` | `curl`, `jq` |
| `docker` | `curl`, `jq`, `docker` |
| `stdio` | `uvx`, `jq`, `python3` |
| `all` | All of the above |

### Required Environment Variables

These must be set (or present in `~/.claude-homelab/.env`) before running any mode:

| Variable | Description |
|----------|-------------|
| `UNIFI_URL` | Full URL of the UniFi controller, e.g. `https://192.168.1.1` |
| `UNIFI_USERNAME` | Admin username for the controller |
| `UNIFI_PASSWORD` | Admin password for the controller |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8001` | Port the MCP server listens on (http/docker modes) |
| `UNIFI_MCP_TOKEN` | _(none)_ | Bearer token the running server requires (http mode) |
| `UNIFI_VERIFY_SSL` | `false` | Whether to verify the controller's TLS certificate |
| `UNIFI_IS_UDM_PRO` | `true` | Set to `true` for UDM Pro, `false` for standalone |

### Credential auto-load

If `UNIFI_URL` is not set in the environment, the script automatically sources `~/.claude-homelab/.env` before failing with a missing-credential error.

### Exact invocation commands

```bash
# Run all modes (default)
./tests/test_live.sh

# Run only against a pre-running HTTP server
./tests/test_live.sh --mode http

# Override server URL and bearer token for HTTP mode
./tests/test_live.sh --mode http --url http://myserver:8001 --token mysecret

# Build a Docker image, run container, test, tear down
./tests/test_live.sh --mode docker

# Run MCP stdio protocol tests only
./tests/test_live.sh --mode stdio

# Enable verbose output (prints full response bodies to stdout)
./tests/test_live.sh --verbose

# Show help
./tests/test_live.sh --help
```

---

## 3. Test Phases

The script is organised into four sequential phases. In `all` mode all phases run under each transport mode (HTTP and Docker share the same phase set; stdio has its own condensed set).

### Phase 1 — Health Check

**Purpose:** Verify the server process is up and responding to unauthenticated health probes.

**What it validates:**
- The `/health` endpoint responds with HTTP `200`.
- The JSON body contains the field `.status` equal to the exact string `"ok"`.

This phase is a gate: if it fails the problem is server startup, not application logic.

### Phase 2 — Authentication

**Purpose:** Verify that the server's bearer-token middleware behaves correctly across three scenarios.

**Sub-tests:**

| Sub-test | Scenario | Expected result |
|----------|----------|-----------------|
| 2a | Request to `/mcp/v1/messages` with **no** `Authorization` header | HTTP `401` |
| 2b | Request with a clearly invalid token (`definitely-wrong-token-abc123`) | HTTP `401` **or** `403` |
| 2c | Request with the configured valid token, sending a valid `initialize` payload | HTTP status is **not** `401` or `403` |

Phase 2c uses an `initialize` JSON-RPC payload (not a bare GET) because the messages endpoint requires a method body.

### Phase 3 — MCP Protocol Conformance

**Purpose:** Verify the server speaks the MCP JSON-RPC protocol correctly.

**Sub-tests:**

| Sub-test | Method | What is validated |
|----------|--------|-------------------|
| 3a | `initialize` | HTTP `200`; response body contains `.result.protocolVersion` or `.result.capabilities` |
| 3b | `tools/list` | HTTP `200`; `.result.tools` array contains at least one entry with `.name == "unifi"` AND at least one entry with `.name == "unifi_help"` |

The `initialize` payload used in Phase 3a specifies `protocolVersion: "2024-11-05"` and `clientInfo: {name: "test_live", version: "1.0"}`.

### Phase 4 — Tool Calls (HTTP and Docker modes)

**Purpose:** Call each read-only tool action via the MCP `tools/call` JSON-RPC method and verify the response contains meaningful data from the live controller. All calls go to `/mcp/v1/messages`.

See Section 4 for per-tool detail.

---

## 4. Tools Tested

All tool calls in Phase 4 are made via the `call_tool` helper, which constructs a JSON-RPC `tools/call` request:

```json
{
  "jsonrpc": "2.0",
  "id": <random>,
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": <args_json>
  }
}
```

The response is processed by `extract_tool_text`, which extracts `.result.content[].text` (where `.type == "text"`) or falls back to `.result.structuredContent` / `.result.structured_content`.

### 4.1 `unifi` — `get_devices`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_devices"}` |
| **Response path inspected** | `extract_tool_text` output |

**Assertions:**

The script first checks `type == "array"` via `jq 'if type == "array" then "yes" else "no" end'`. Then it checks `jq 'has("devices") or (type == "array")'`.

- PASS if the extracted text is a JSON array (`"yes"`) — i.e., a raw list of device objects.
- PASS if the extracted text is a JSON object with a `"devices"` key.
- PASS if neither of the above but the text is non-empty (formatted/prose output from the tool).
- FAIL if the extracted text is empty or if `call_tool` returns an empty body.
- FAIL if `.error.message` is present in the JSON-RPC response.

**Label:** `Phase 4 / get_devices: returns device list` or `Phase 4 / get_devices: returns non-empty response`

---

### 4.2 `unifi` — `get_clients`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_clients", "connected_only": true}` |
| **jq validation expression** | `. != null` |
| **Expected value** | _(none — truthy check)_ |

**Assertions:**

Uses the generic `_tool_test` helper. The jq expression `. != null` is evaluated on the extracted text content. This is a truthy check: the test passes as long as the response content is non-null and non-empty. If the content is plain text (not valid JSON), the test passes as long as the text is non-empty.

- PASS if content is non-empty and `. != null` evaluates truthy.
- FAIL if the response is empty, contains a JSON-RPC error, or `. != null` is falsy.

**Label:** `Phase 4 / get_clients(connected_only=true): response non-empty`

---

### 4.3 `unifi` — `get_sites`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_sites"}` |
| **Response path inspected** | `extract_tool_text` output |

**Assertions:**

Simpler check than `get_devices`: the script only verifies that `extract_tool_text` returns a non-empty string. No jq structural validation is performed.

- PASS if text content is non-empty.
- FAIL if text content is empty.

**Label:** `Phase 4 / get_sites: returns at least one site`

---

### 4.4 `unifi` — `get_wlan_configs`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_wlan_configs"}` |
| **jq validation expression** | `. != null` |

**Assertions:** Same truthy non-null check as `get_clients`.

- PASS if content is non-empty and non-null.
- FAIL if empty or contains a JSON-RPC error.

**Label:** `Phase 4 / get_wlan_configs: response non-empty`

---

### 4.5 `unifi` — `get_network_configs`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_network_configs"}` |
| **jq validation expression** | `. != null` |

**Assertions:** Same truthy non-null check.

- PASS if content is non-empty and non-null.
- FAIL if empty or contains a JSON-RPC error.

**Label:** `Phase 4 / get_network_configs: response non-empty`

---

### 4.6 `unifi` — `get_firewall_rules`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_firewall_rules"}` |
| **jq validation expression** | `. != null` |

**Assertions:** Same truthy non-null check.

- PASS if content is non-empty and non-null.
- FAIL if empty or contains a JSON-RPC error.

**Label:** `Phase 4 / get_firewall_rules: response non-empty`

---

### 4.7 `unifi` — `get_controller_status`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_controller_status"}` |
| **Response path inspected** | `extract_tool_text` output |

**Assertions (two-tier):**

The script attempts a version-field check first, then falls back gracefully:

1. **Tier 1 — JSON version field:** Evaluates `jq -r 'has("version") or has("Version") or (.version != null)'` on the text. If this returns `"true"`, passes with label `version field present`.
2. **Tier 2 — Text substring:** If the jq check fails (text is not JSON or has no version key), checks if the text contains the substring `"version"` (case-insensitive via `grep -qi`). Passes with label `version field present`.
3. **Tier 3 — Non-empty fallback:** If neither tier 1 nor tier 2 matches but text is non-empty, still passes with label `response non-empty`.

- FAIL only if the extracted text is entirely empty.

**Labels:**
- `Phase 4 / get_controller_status: version field present`
- `Phase 4 / get_controller_status: response non-empty`

---

### 4.8 `unifi` — `get_events`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi` |
| **Arguments** | `{"action": "get_events", "limit": 5}` |
| **jq validation expression** | `. != null` |

**Assertions:** Same truthy non-null check. The `limit: 5` argument requests at most 5 events, keeping the response compact for CI.

- PASS if content is non-empty and non-null.
- FAIL if empty or contains a JSON-RPC error.

**Label:** `Phase 4 / get_events(limit=5): response non-empty`

---

### 4.9 `unifi_help`

| Field | Value |
|-------|-------|
| **Tool name** | `unifi_help` |
| **Arguments** | `{}` |
| **Response path inspected** | `extract_tool_text` output |

**Assertions (two conditions, both must hold):**

1. The extracted text must be non-empty.
2. The text must contain the substring `"unifi"` (case-insensitive via `grep -qi`).

- FAIL if text is empty (reported as `empty response`).
- FAIL if text is non-empty but does not contain `"unifi"` (reported as `text does not mention 'unifi'`).
- PASS only when both conditions are satisfied.

**Label:** `Phase 4 / unifi_help: help text non-empty and mentions unifi`

---

## 5. Stdio Mode Tool Tests

The stdio mode runs a condensed subset of tool calls through the MCP stdio transport. Each call spawns a new `uvx` subprocess, performs the full MCP handshake, and terminates after receiving the response.

### Tools tested in stdio mode

| Tool | Arguments | Label pattern |
|------|-----------|---------------|
| `unifi_help` | `{}` | `stdio / Tool: unifi_help({})` |
| `unifi` | `{"action":"get_sites"}` | `stdio / Tool: unifi({"action":"get_sites"})` |
| `unifi` | `{"action":"get_controller_status"}` | `stdio / Tool: unifi({"action":"get_controller_status"})` |
| `unifi` | `{"action":"get_devices"}` | `stdio / Tool: unifi({"action":"get_devices"})` |
| `unifi` | `{"action":"get_clients","connected_only":true}` | `stdio / Tool: unifi({"action":"get_clients","connected_only":true})` |
| `unifi` | `{"action":"get_wlan_configs"}` | `stdio / Tool: unifi({"action":"get_wlan_configs"})` |
| `unifi` | `{"action":"get_firewall_rules"}` | `stdio / Tool: unifi({"action":"get_firewall_rules"})` |
| `unifi` | `{"action":"get_events","limit":5}` | `stdio / Tool: unifi({"action":"get_events","limit":5})` |

### Stdio mode assertions (per tool call)

For each entry the script:
1. Calls `_stdio_call <tool_name> <args_json>` which returns the raw JSON-RPC response object.
2. Checks `.error` and `.error.message` for any error value.
3. Extracts `.result.content[] | select(.type=="text") | .text`.
4. PASS if no error and content text is non-empty.
5. FAIL if `.error` or `.error.message` is non-empty, or if content text is empty.

There is no structural/semantic validation of the response content in stdio mode — the check is existence only.

---

## 6. Skipped / Excluded Operations

The following UniFi API capabilities are **intentionally not tested** to avoid mutating production network state:

| Action category | Reason for exclusion |
|-----------------|----------------------|
| Create/update network configurations | Would modify live network settings |
| Create/update WLAN configs | Could disrupt wireless connectivity |
| Create/update/delete firewall rules | Could break network security posture |
| Block/unblock clients | Would interrupt live clients |
| Device adoption, restart, upgrade | Would affect live infrastructure |
| Any action that writes state | General principle: read-only only |

Only **read-only `get_*` actions** are exercised. The script does not emit a `[SKIP]` line for these; they are simply absent from the test suite by design.

---

## 7. Authentication Tests in Detail

Phase 2 runs three sub-tests that together verify the server's bearer-token middleware. The endpoint probed is `/mcp/v1/messages`.

### 2a — No token

```bash
http_get "${base_url}/mcp/v1/messages"   # No Authorization header
```

Expected: HTTP `401`. Any other status code fails the test.

### 2b — Bad token

```bash
http_get "${base_url}/mcp/v1/messages" "definitely-wrong-token-abc123"
# Sends: Authorization: Bearer definitely-wrong-token-abc123
```

Expected: HTTP `401` **or** `403`. The script accepts either code because different middleware implementations may return 403 for a recognised-but-rejected token vs 401 for completely absent/unrecognised credentials. Any other status fails.

### 2c — Valid token

```bash
mcp_post "${base_url}/mcp/v1/messages" "${good_token}" \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
```

Expected: HTTP status is **not** `401` or `403`. The test does not assert a specific success code — it only asserts that the token was accepted. A `200` with a valid JSON-RPC response is the normal happy path.

**Token source (http mode):** `--token` CLI flag > `BEARER_TOKEN` env var > `UNIFI_MCP_TOKEN` env var. If none is set, a warning is logged and Phase 2c may fail.

**Token source (docker mode):** `--token` CLI flag > `BEARER_TOKEN` env var > hardcoded CI token `ci-integration-token`. The CI token is injected into the container as the `UNIFI_MCP_TOKEN` environment variable.

---

## 8. Docker Mode — Build, Run, Health Poll, Teardown

### Build

```bash
docker build -t "unifi-mcp-test:ci-<epoch>" "${REPO_DIR}"
```

- Builds from the repository root `Dockerfile`.
- Tag format: `unifi-mcp-test:ci-<unix_timestamp>` — unique per run.
- All build output is redirected to the log file only.
- Failure causes exit code `2`.

### Container startup

```bash
docker run -d \
  --name "unifi-mcp-test-<PID>" \
  -p "${PORT}:8001" \
  -e UNIFI_URL="${UNIFI_URL}" \
  -e UNIFI_USERNAME="${UNIFI_USERNAME}" \
  -e UNIFI_PASSWORD="${UNIFI_PASSWORD}" \
  -e UNIFI_MCP_TOKEN="${token}" \
  -e UNIFI_VERIFY_SSL="${UNIFI_VERIFY_SSL:-false}" \
  -e UNIFI_IS_UDM_PRO="${UNIFI_IS_UDM_PRO:-true}" \
  "${image_tag}"
```

- Container name: `unifi-mcp-test-<bash_PID>` — unique per run, prevents name collision.
- Port mapping: host `PORT` (default `8001`) → container `8001`.
- All five credential/config env vars are forwarded into the container.
- The token used is `BEARER_TOKEN` (from `--token` / env var) or `ci-integration-token` as fallback.

### Health polling

After the container starts, the script polls `GET http://localhost:${PORT}/health` up to **30 times at 1-second intervals**. It checks for HTTP `200`.

- If health is confirmed within 30 attempts: logs the attempt number and proceeds to `run_http_mode`.
- If health is not confirmed within 30 seconds: logs container output to the log file and returns exit `2`.

### Test execution

Once healthy, docker mode runs the **identical four phases** as HTTP mode (`phase_health`, `phase_auth`, `phase_protocol`, `phase_tools_http`) against `http://localhost:${PORT}`.

### Teardown

A `trap _docker_cleanup RETURN` is set for the `run_docker_mode` function. On return (success or failure):

1. `docker stop "${DOCKER_CONTAINER}"` — sends SIGTERM, waits for graceful shutdown.
2. `docker rm "${DOCKER_CONTAINER}"` — removes the stopped container.
3. `docker rmi "${image_tag}"` — removes the test image.

All teardown commands use `|| true` so a cleanup failure does not mask the original exit code. The global `DOCKER_CONTAINER` variable is cleared after stop+rm.

---

## 9. Stdio Mode — subprocess protocol details

Stdio mode uses an inline Python 3 heredoc (`_stdio_call`) executed via `python3 -`. Each individual tool call spawns a **fresh server subprocess**.

### Server invocation command

```python
cmd = ["uvx", "--directory", repo_dir, "--from", ".", entry_point]
# entry_point = "unifi-mcp"  (the pyproject.toml [project.scripts] key)
```

`uvx` installs and runs the package directly from the local repository directory without requiring a separate install step.

### Environment passed to subprocess

| Variable | Source |
|----------|--------|
| `UNIFI_URL` | From the test runner's environment |
| `UNIFI_USERNAME` | From the test runner's environment |
| `UNIFI_PASSWORD` | From the test runner's environment |
| `UNIFI_MCP_TRANSPORT` | Hardcoded `"stdio"` |
| `UNIFI_VERIFY_SSL` | From environment, default `"false"` |
| `UNIFI_IS_UDM_PRO` | From environment, default `"true"` |

### MCP handshake sequence

Each `_stdio_call` invocation performs the full MCP handshake:

1. **Send `initialize`** (id=1) with `protocolVersion: "2024-11-05"`.
2. **Read stdout lines** until an object with `id == 1` is found (deadline: 30 s).
3. **Send `notifications/initialized`** notification (no id — it's a notification, not a request).
4. **Send `tools/call`** (id=2) with the target tool name and arguments.
5. **Read stdout lines** until an object with `id == 2` is found (deadline: 30 s).
6. Print the matched response JSON to stdout and terminate the subprocess.

If the initialize response is not received within the deadline, the Python helper prints `{"error": "no initialize response"}` and terminates. If the tool response is not received, it prints `{"error": "timeout waiting for tool response"}`.

### Tools/list via stdio

The `tools/list` check in stdio mode uses a separate Python heredoc (not `_stdio_call`) that writes its output to a temp file created with `mktemp`. This is required because the `_stdio_call` helper is structured as a heredoc-in-a-subshell and capturing its output into a bash variable while also piping is not straightforward. The actual `tools/list` check uses a 45-second deadline (vs 30 seconds for individual tool calls).

The assertion checks:
- `[.result.tools[]? | select(.name == "unifi")] | length` >= 1
- `[.result.tools[]? | select(.name == "unifi_help")] | length` >= 1

Both must be true to pass.

---

## 10. Output Format and Interpretation

### Console output

Each test produces one line:

```
[PASS] <label>                                              <elapsed_ms>ms
[FAIL] <label>  <reason>
[SKIP] <label>  <reason>
```

Section banners are printed before each phase/tool group:
```
── Phase 1 — Health ─────────────────────────────────────────────────
```

Colours are auto-disabled when stdout is not a TTY (useful for CI log capture).

### Summary block

After all modes complete, a summary table is printed:

```
======================================================================
PASS                   <N>
FAIL                   <N>
SKIP                   <N>
TOTAL                  <N>
ELAPSED                <S>s (<ms>ms)
======================================================================

Failed tests:
  • Phase 2a / Auth: no token → 401
  • ...

Log: /tmp/test_live.20260404-120000.log
```

### Log file

All output is tee'd to a timestamped log file at `${TMPDIR:-/tmp}/test_live.<YYYYMMDD-HHMMSS>.log`. Full response bodies are always written to the log (regardless of `--verbose`). Docker build output and curl stderr also go to the log only.

When `--verbose` is set, full response bodies are also printed to stdout.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | All tests passed (or skipped) |
| `1` | One or more `[FAIL]` results |
| `2` | Prerequisite failure (missing env var, tool not in PATH, Docker build failed, container startup timeout) |

---

## 11. What "Proving Correct Operation" Means Per Tool

The test intentionally uses lenient assertions because the tool output format (JSON array, JSON object, or formatted prose) is not contractually fixed. The table below summarises what each test actually proves:

| Tool / action | What is proven |
|---------------|----------------|
| `GET /health` | The server process is running and the health handler returns `{"status":"ok"}` — the exact string, not just any truthy value |
| `initialize` | The server speaks MCP 2024-11-05; it returns either a `protocolVersion` or `capabilities` field in the result |
| `tools/list` | The server advertises both `unifi` and `unifi_help` as callable tools |
| `unifi / get_devices` | The controller's device list endpoint is reachable and returns either an array of device objects, an object with a `devices` key, or non-empty formatted text |
| `unifi / get_clients` | The client list endpoint is reachable with `connected_only=true` and returns a non-null response |
| `unifi / get_sites` | The sites endpoint is reachable and returns non-empty content (implies at least one site exists) |
| `unifi / get_wlan_configs` | The WLAN configuration endpoint is reachable and returns non-null content |
| `unifi / get_network_configs` | The network configuration endpoint is reachable and returns non-null content |
| `unifi / get_firewall_rules` | The firewall rules endpoint is reachable and returns non-null content |
| `unifi / get_controller_status` | The controller status endpoint is reachable and the response mentions the word `"version"` (indicating actual controller metadata was returned, not an empty stub) |
| `unifi / get_events` | The events endpoint is reachable with a `limit` parameter and returns non-null content |
| `unifi_help` | The help tool returns a non-empty text response that contains the word `"unifi"` (confirming it is tool documentation, not an empty or generic placeholder) |
| Auth — no token | The server rejects unauthenticated requests with `401` |
| Auth — bad token | The server rejects invalid tokens with `401` or `403` |
| Auth — valid token | The server accepts the configured token |

The tests do **not** prove:
- That specific devices, clients, sites, rules, or events exist (data-dependent).
- That field values are semantically correct (e.g., IP addresses are valid, MAC addresses are correctly formatted).
- That pagination works correctly.
- That error handling for malformed action arguments behaves correctly.
- That write operations function (excluded by design).
