# Live Smoke Testing

End-to-end verification against a running unifi-mcp server. Complements unit/integration tests in [TESTS.md](TESTS.md).

## Purpose

Smoke tests verify the full request path: HTTP transport, bearer auth, tool dispatch, UniFi controller communication, and response formatting.

## Running

### Via Script

```bash
bash scripts/smoke-test.sh
```

### Via Justfile

```bash
just test-live
```

### Manual

```bash
# 1. Health check
curl -sf http://localhost:8001/health | python3 -m json.tool

# 2. List devices
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}' | python3 -m json.tool

# 3. Get help
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi_help","arguments":{}}}' | python3 -m json.tool

# 4. Test auth rejection
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer wrong-token" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"get_devices"}}}'
# Expect 403

# 5. Test invalid action
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNIFI_MCP_TOKEN" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"unifi","arguments":{"action":"nonexistent_action"}}}'
# Expect error with available_actions list
```

## CI Integration

Live tests run in the `mcp-integration` job after lint, typecheck, and test pass:

```yaml
mcp-integration:
  needs: [lint, typecheck, test]
  steps:
    - run: bash tests/test_live.sh
  env:
    UNIFI_URL: ${{ secrets.UNIFI_URL }}
    UNIFI_USERNAME: ${{ secrets.UNIFI_USERNAME }}
    UNIFI_PASSWORD: ${{ secrets.UNIFI_PASSWORD }}
```

## Expected Results

| Test | Expected |
|------|----------|
| Health check | `{"status": "ok", "service": "unifi-mcp"}` |
| get_devices | List of devices with name, model, status |
| get_clients | List of clients with connection info |
| Invalid action | Error with `available_actions` array |
| Wrong token | HTTP 403 |
| No token | HTTP 401 |

## See Also

- [TESTS.md](TESTS.md) — Unit and integration tests
- [DEPLOY.md](DEPLOY.md) — Server deployment
