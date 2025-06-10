# Unifi MCP Tools Test Results

**Test Date:** $(date +%Y-%m-%d)

This document summarizes the test results for the Unifi MCP tools.

## Test Summary

| Tool                   | Parameters Tested                                                                     | Result    | Notes                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------ |
| `list_hosts`           | None                                                                                  | SUCCESS   | Retrieved host list. `host_id` for subsequent tests: `9C05D6CA813B000000000815818C0000000008834D900000000066544E25:938164743` |
| `get_host_by_id`       | `host_id="9C05D6CA813B000000000815818C0000000008834D900000000066544E25:938164743"`       | SUCCESS   | Retrieved host details.                                                                                |
| `list_sites`           | None                                                                                  | SUCCESS   | Retrieved site list. `siteId` for subsequent tests: `66b6e94d792b29626a54aab7`                          |
| `list_devices`         | None                                                                                  | SUCCESS   | Retrieved device list.                                                                                 |
| `get_isp_metrics`      | `metric_type="5m"`                                                                    | SUCCESS   | Retrieved ISP metrics.                                                                                 |
| `query_isp_metrics`    | `metric_type="5m"`, `sites_query=[{"hostId": "...", "siteId": "..."}]`               | SUCCESS   | Retrieved ISP metrics for specific site.                                                               |
| `list_sdwan_configs`   | `random_string="unifi_test"`                                                          | FAIL      | Tool call was interrupted or failed.                                                                   |
| `get_sdwan_config_by_id` | N/A                                                                                   | SKIPPED   | Depends on `list_sdwan_configs`.                                                                       |
| `get_sdwan_config_status`| N/A                                                                                   | SKIPPED   | Depends on `list_sdwan_configs`.                                                                       |

## Detailed Results

### `list_hosts`
<details>
<summary>SUCCESS</summary>
Successfully retrieved host list.
Host ID used for subsequent tests: `9C05D6CA813B000000000815818C0000000008834D900000000066544E25:938164743`
</details>

### `get_host_by_id`
<details>
<summary>SUCCESS</summary>
Successfully retrieved details for host `9C05D6CA813B000000000815818C0000000008834D900000000066544E25:938164743`.
</details>

### `list_sites`
<details>
<summary>SUCCESS</summary>
Successfully retrieved site list.
Site ID used for subsequent tests: `66b6e94d792b29626a54aab7`
</details>

### `list_devices`
<details>
<summary>SUCCESS</summary>
Successfully retrieved device list.
</details>

### `get_isp_metrics`
<details>
<summary>SUCCESS</summary>
Successfully retrieved ISP metrics for `metric_type="5m"`.
</details>

### `query_isp_metrics`
<details>
<summary>SUCCESS</summary>
Successfully retrieved ISP metrics for the specified site and host.
</details>

### `list_sdwan_configs`
<details>
<summary>FAIL</summary>
The tool call was interrupted or did not return a result.
</details>

### `get_sdwan_config_by_id`
<details>
<summary>SKIPPED</summary>
This test was skipped because `list_sdwan_configs` did not provide a `config_id`.
</details>

### `get_sdwan_config_status`
<details>
<summary>SKIPPED</summary>
This test was skipped because `list_sdwan_configs` did not provide a `config_id`.
</details>

---
*This report was auto-generated.* 