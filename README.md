# UniFi Local Controller MCP Server

> **Direct, real-time management for local UniFi controllers via the Model Context Protocol.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python Version](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Enabled-brightgreen.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

---

## ✨ Overview
UniFi MCP provides direct integration with local UniFi controllers (UDM Pro, Cloud Gateway Max, etc.) without cloud dependencies. It delivers clean, human-readable network data and granular device control.

### 🎯 Key Features
| Feature | Description |
|---------|-------------|
| **Device Control** | Restart, locate, and manage network infrastructure |
| **Client Management** | Reconnect, block, or rename connected clients |
| **Network Insights** | Real-time dashboard, DPI stats, and subsystem health |
| **Modular Design** | Site-aware resources with recursive data formatting |

---

## 🎯 Claude Code Integration
The easiest way to use this plugin is through the Claude Code marketplace:

```bash
# Add the marketplace
/plugin marketplace add jmagar/claude-homelab

# Install the plugin
/plugin install unifi-mcp @jmagar-claude-homelab
```

---

## ⚙️ Configuration & Credentials
Credentials follow the standardized `homelab-core` pattern.

**Location:** `~/.unifi-mcp/.env` (also supports shared `~/.claude-homelab/.env`)

### Required Variables
```bash
UNIFI_URL="https://10.1.0.1:443"         # UniFi OS (UDM/CGM)
UNIFI_USERNAME="admin"                   # Local admin account
UNIFI_PASSWORD="your-password"           # Local admin password
UNIFI_IS_UDM_PRO=true                    # Set false for legacy controllers
UNIFI_VERIFY_SSL=false                   # Usually false for self-signed certs
```

---

## 🛠️ Available Tools & Resources

### 🔧 Primary Tools
| Tool | Parameters | Description |
|------|------------|-------------|
| **`unifi`** | `action`, `confirm` | Unified tool for device, client, and network operations |
| **`unifi_help`** | `none` | Reference for all actions and parameters |

### 📊 Resources (`unifi://`)
| URI | Description | Output Format |
|-----|-------------|---------------|
| `unifi://overview` | Site-wide infrastructure and client summary | Clean Summary |
| `unifi://devices` | Detailed list of infrastructure devices | Prettified JSON |
| `unifi://health` | Real-time subsystem health status | Status Report |
| `unifi://dashboard` | Live bandwidth and traffic metrics | Real-time Stats |

---

## 🏗️ Architecture & Design
Built as a modular Python package powered by FastMCP:
- **Smart Formatting:** Custom engine converts raw JSON walls into human-readable summaries.
- **Session Management:** Handles JWT/CSRF tokens and persistent cookie authentication.
- **Site-Aware:** Automatic mapping to the "default" site with full multi-site support.

---

## 🔧 Development
### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup
```bash
uv sync
uv run python -m unifi_mcp.main
```

### Background Execution
```bash
./run.sh              # Start in background and stream logs
./run.sh logs         # Stream logs from running server
```

---

## 🐛 Troubleshooting
| Issue | Cause | Solution |
|-------|-------|----------|
| **401 Unauthorized** | Cloud/SSO Account | Use a **Local Admin** account |
| **SSL Errors** | Self-signed Cert | Set `UNIFI_VERIFY_SSL=false` |
| **Empty Devices** | Insufficient Perms | Verify admin-level access |

---

## 📄 License
MIT © jmagar
