# Common MCP Code Patterns

Reusable patterns used across the unifi-mcp server.

## Service Architecture

The server uses a layered service architecture:

```
Tool Registration (server.py)
  -> UnifiService (router)
    -> DeviceService
    -> ClientService
    -> NetworkService
    -> MonitoringService
```

Each domain service extends `BaseService` and implements `execute_action()` with an action map:

```python
class DeviceService(BaseService):
    async def execute_action(self, params: UnifiParams) -> ToolResult:
        action_map = {
            UnifiAction.GET_DEVICES: self._get_devices,
            UnifiAction.GET_DEVICE_BY_MAC: self._get_device_by_mac,
            ...
        }
        handler = action_map.get(params.action)
        return await handler(params)
```

## BaseService Helpers

### Error Handling

```python
# Standard error result
self.create_error_result("Device not found", raw_data)

# Standard success result
self.create_success_result(
    text="Devices (5 total)\n  ...",
    data=formatted_devices,
    success_message="Retrieved 5 devices"
)
```

### Response Validation

```python
# Check for error dict in API response
is_valid, error_msg = self.validate_response(result, params.action)
if not is_valid:
    return self.create_error_result(error_msg, result)

# Check list response (common pattern for collection endpoints)
error_result = self.check_list_response(response, params.action)
if error_result:
    return error_result
```

### MAC Address Handling

```python
mac = self.require_mac(params)  # Raises ValueError if missing
normalized = self.normalize_mac(mac)  # aa:bb:cc:dd:ee:ff format
```

### Dict Filtering

```python
# Filter non-dict items from loosely typed API responses
items = self.dict_items(response)  # [dict, dict, ...]
```

## Client Authentication Pattern

```python
# Auto-reauthentication on 401
async def _make_request(self, method, endpoint, site_name, data=None):
    await self.ensure_authenticated()
    response = await self.session.request(...)
    if response.status_code == 401:
        self.is_authenticated = False
        await self.authenticate()
        response = await self.session.request(...)  # Retry once
```

## Formatter Pattern

Formatters in `formatters.py` convert raw API data to structured summaries:

```python
def format_device_summary(device: dict) -> dict:
    return {
        "name": device.get("name", "Unknown"),
        "model": DEVICE_MODEL_MAP.get(device.get("model"), device.get("model")),
        "status": "Online" if device.get("state") == 1 else "Offline",
        ...
    }
```

All byte values are auto-converted to human-readable format via `format_data_values()`.

## Resource Registration Pattern

Resources use the `unifi://` URI scheme and are registered in module-level functions:

```python
def register_device_resources(mcp: FastMCP, client: UnifiControllerClient):
    @mcp.resource("unifi://devices")
    async def resource_devices():
        return await client.get_devices_formatted("default")
```

## Destructive Gate Pattern

```python
def _check_destructive(self, params: UnifiParams) -> ToolResult | None:
    if params.action not in DESTRUCTIVE_ACTIONS:
        return None  # Not destructive, proceed
    if env_bypass_active():
        return None  # Bypassed, proceed
    if params.confirm:
        return None  # Confirmed, proceed
    return ToolResult(...)  # Gate: return confirmation prompt
```

## See Also

- [SCHEMA.md](SCHEMA.md) — Schema definitions
- [DEV.md](DEV.md) — Development workflow
