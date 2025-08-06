<div align="center">

# 🌐 UniFi Local Controller MCP Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-Enabled-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-Open%20Source-brightgreen.svg)](#license)
[![UniFi](https://img.shields.io/badge/UniFi-Controller%20Ready-0559C9.svg)](https://ui.com)

*A powerful Model Context Protocol (MCP) server for seamless UniFi controller integration*

🚀 **Direct Local Access** • 📊 **Real-time Monitoring** • 🔧 **Device Management** • 🎯 **Clean Data Output**

</div>

---

## ✨ Overview

This MCP server provides **direct, real-time integration** with your local UniFi controller through a comprehensive suite of tools and resources. Built with modern FastMCP framework, it eliminates the need for cloud dependencies while delivering clean, formatted data output.

### 🎯 **Key Features**

| Feature | Description |
|---------|-------------|
| 🏠 **Local Integration** | Direct controller access - no cloud dependencies |
| 📡 **Real-time Data** | Live device status, statistics, and monitoring |
| 🎨 **Clean Output** | Human-readable formatting - no JSON walls |
| 🔧 **Device Control** | Restart, locate, and manage network devices |
| 📊 **Smart Analytics** | Bandwidth, DPI stats, and network insights |
| 🌐 **Universal Support** | Works with UDM Pro, Cloud Gateway Max, legacy controllers |
| ⚡ **FastMCP Powered** | Modern MCP framework with streamable HTTP transport |

## 🚀 Quick Start

### 📋 Prerequisites

> **Before you begin**, ensure you have:

- 🏠 **Local UniFi Controller** (Cloud Gateway Max, UDM Pro, or traditional controller)
- 🌐 **Direct Network Access** to the controller
- 👤 **Local Admin Account** (not UniFi Cloud/SSO)
- 🐍 **Python 3.11+**
- 📦 **`uv` Package Manager**

### 🔌 Controller Compatibility

| Controller Type | Port | Examples |
|----------------|------|----------|
| 🆕 **UniFi OS Devices** | `443` | UDM Pro, UDM SE, Cloud Gateway Max, Cloud Key Gen2+ |
| 🔄 **Legacy Controllers** | `8443` | Software controllers, Cloud Key Gen1 |

> ⚠️ **Authentication Note**: Requires local admin account, **not** UniFi Cloud credentials

### ⚡ Installation

<details>
<summary><b>📥 Step-by-Step Setup</b></summary>

#### 1️⃣ **Clone and Setup**
```bash
cd unifi-mcp
uv sync
```

#### 2️⃣ **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your controller details
```

#### 3️⃣ **Launch Server**
```bash
./run.sh
# Or directly: uv run python unifi-local-mcp-server.py
```

</details>

🎯 **Server Endpoint**: `http://localhost:8001/mcp`

## ⚙️ Configuration

### 🔑 Required Environment Variables

<details>
<summary><b>📝 Configuration Template</b></summary>

```bash
# 🏠 Controller Connection (scheme and port required)
UNIFI_CONTROLLER_URL=https://10.1.0.1:443  # UniFi OS (UDM Pro, Cloud Gateway Max)
# UNIFI_CONTROLLER_URL=https://10.1.0.1:8443  # Legacy controllers
UNIFI_USERNAME=admin                        # Local controller admin username
UNIFI_PASSWORD=your_password               # Local controller admin password

# 🔧 Controller Type Configuration
UNIFI_IS_UDM_PRO=true                 # true for UniFi OS devices, false for legacy
UNIFI_VERIFY_SSL=false                # false for self-signed certs, true for valid SSL

# 🌐 Optional Server Settings
UNIFI_LOCAL_MCP_HOST=0.0.0.0          # Server bind address
UNIFI_LOCAL_MCP_PORT=8001             # Server port
UNIFI_LOCAL_MCP_LOG_LEVEL=INFO        # Logging level
```

</details>

### 🌐 Controller URL Examples

| Type | URL Format | Use Case |
|------|------------|----------|
| 🆕 **UniFi OS** | `https://192.168.1.1:443` | UDM Pro, Cloud Gateway Max, Cloud Key Gen2+ |
| 🔄 **Legacy** | `https://unifi.example.com:8443` | Software controllers, Cloud Key Gen1 |
| 🔧 **Custom** | `https://controller:PORT` | Non-standard port configurations |

### 🔒 SSL Certificate Handling

| Certificate Type | Setting | Description |
|-----------------|---------|-------------|
| 🔓 **Self-signed** | `UNIFI_VERIFY_SSL=false` | Most common setup |
| ✅ **Valid SSL** | `UNIFI_VERIFY_SSL=true` | Trusted certificate authority |
| 📁 **Custom CA** | Provide CA bundle path | Enterprise environments |

## 🛠️ Available Tools

<div align="center">

### 🎯 **Tool Categories**

</div>

<details>
<summary><b>📱 Device Management</b></summary>

| Tool | Description | Output |
|------|-------------|--------|
| `get_devices` | List all devices | 🎨 Clean, formatted summaries |
| `get_device_by_mac` | Specific device details | 📊 Formatted device info |
| `restart_device` | Restart UniFi device | ⚡ Device reboot |
| `locate_device` | Trigger locate LED | 💡 Visual device identification |

</details>

<details>
<summary><b>👥 Client Management</b></summary>

| Tool | Description | Output |
|------|-------------|--------|
| `get_clients` | Connected clients | 🔗 Connection details |
| `reconnect_client` | Force reconnection | 🔄 Client refresh |

</details>

<details>
<summary><b>🌐 Network Configuration</b></summary>

| Tool | Description | Output |
|------|-------------|--------|
| `get_sites` | Controller sites | 🏢 Site information |
| `get_wlan_configs` | Wireless networks | 📡 WiFi configurations |
| `get_network_configs` | Network/VLAN setup | 🔧 Network topology |
| `get_port_configs` | Switch port profiles | 🔌 Port configurations |
| `get_port_forwarding_rules` | Port forwarding | ➡️ Traffic routing rules |

</details>

<details>
<summary><b>📊 Monitoring & Statistics</b></summary>

| Tool | Description | Output |
|------|-------------|--------|
| `get_controller_status` | System information | 💻 Controller health |
| `get_events` | Recent controller events | 📅 Event timeline |
| `get_alarms` | Active system alarms | 🚨 Alert notifications |
| `get_dpi_stats` | Deep Packet Inspection | 🔍 Traffic analysis |
| `get_rogue_aps` | Rogue access points | ⚠️ Security threats |
| `start_spectrum_scan` | RF spectrum analysis | 📡 Wireless diagnostics |
| `get_spectrum_scan_state` | Scan results | 📊 RF environment data |
| `authorize_guest` | Guest network access | 🎫 Visitor authorization |

</details>

## MCP Resources

Access structured data using the `unifi://` URI scheme:

### Root Level Resources
- `unifi://sites` - All controller sites
- `unifi://devices` - All devices with clean formatting (default site)
- `unifi://clients` - All connected clients with essential details (default site)
- `unifi://dashboard` - Dashboard metrics and time-series data (default site)

<details>
<summary><b>🎨 Data Formatting Engine</b></summary>

| Feature | Description |
|---------|-------------|
| 🧠 **Smart Summarization** | Essential info only - no JSON walls |
| 📱 **Device-Type Aware** | Custom formatting per device type |
| 🔌 **Connection-Type Aware** | Tailored wired vs wireless details |
| 📊 **Auto Conversion** | Bytes, uptimes, timestamps |
| 🔄 **Recursive Formatting** | Clean nested data structures |

</details>

### 🔐 Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant MCP Server
    participant UniFi Controller
    
    Client->>MCP Server: Request
    MCP Server->>UniFi Controller: Login (username/password)
    UniFi Controller->>MCP Server: TOKEN/unifises cookie
    MCP Server->>UniFi Controller: Parse CSRF token (UDM Pro)
    MCP Server->>UniFi Controller: API Request + Auth Headers
    UniFi Controller->>MCP Server: Response Data
    MCP Server->>Client: Formatted Response
```

### 🎯 Key Design Decisions

| Decision | Rationale | Benefit |
|----------|-----------|----------|
| 📄 **Single-file server** | Complete implementation simplicity | Easy deployment & maintenance |
| 🎯 **Default site assumption** | Most operations use "default" | Simplified API calls |
| 🎨 **Clean data presentation** | Smart formatting helpers | No overwhelming JSON |
| 📊 **Comprehensive resources** | Dashboard + detailed monitoring | Complete network visibility |
| 🔧 **Resource vs Tool pattern** | Resources for data, tools for ops | Clear separation of concerns |

## 👨‍💻 Development

### 🔥 Hot Reload Development

<details>
<summary><b>🚀 Development Setup</b></summary>

```bash
# Install development dependencies
uv sync --extra dev

# Run with hot reload (if available)
uv run reloaderoo unifi-local-mcp-server.py
```

</details>

### 🧪 Testing Tools

<details>
<summary><b>🔧 API Testing Commands</b></summary>

```bash
# List available tools
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# Test a specific tool
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_devices"}}'
```

</details>

### 🌐 API Endpoints

| Endpoint | Purpose | Description |
|----------|---------|-------------|
| 💚 **Health** | `http://localhost:8001/health` | Server health check |
| 🔗 **MCP** | `http://localhost:8001/mcp` | Main MCP endpoint |
| ⚡ **Tools** | `http://localhost:8001/mcp/call` | Tool execution |

## 🔧 Troubleshooting

<div align="center">

### 🚨 **Common Issues & Solutions**

</div>

<details>
<summary><b>🔐 Authentication Issues</b></summary>

| Issue | Solution | Notes |
|-------|----------|-------|
| 🚫 **401 Errors** | Check username/password and controller URL | Verify credentials |
| 🔒 **MFA Required** | Disable MFA or implement MFA support | Contact admin |
| 🛡️ **SSL Errors** | Set `UNIFI_VERIFY_SSL=false` | For self-signed certs |

</details>

<details>
<summary><b>🎛️ Controller Type Issues</b></summary>

| Controller Type | Setting | Description |
|----------------|---------|-------------|
| 🆕 **UDM Pro/Cloud Gateway Max** | `UNIFI_IS_UDM_PRO=true` | Modern UniFi OS devices |
| 🔄 **Legacy Controllers** | `UNIFI_IS_UDM_PRO=false` | Traditional controllers |

</details>

<details>
<summary><b>⚠️ Common Problems</b></summary>

| Problem | Cause | Solution |
|---------|-------|----------|
| 📊 **Empty DPI Stats** | DPI disabled | Enable DPI in controller settings |
| 📱 **No Devices Found** | Insufficient permissions | Verify admin access |
| ⏱️ **Connection Timeouts** | Network issues | Check connectivity & availability |

</details>

## 🔬 Technical Details

### 🛠️ Built With

<div align="center">

| Component | Description | Link |
|-----------|-------------|------|
| 🐍 **unifi-controller-api** | Python UniFi library | [GitHub](https://github.com/tnware/unifi-controller-api) |
| ⚡ **FastMCP** | Modern MCP framework | [GitHub](https://github.com/jlowin/fastmcp) |
| 📦 **PyPI Package** | Controller API package | [PyPI](https://pypi.org/project/unifi-controller-api/) |

</div>

### 💡 Implementation Highlights

<details>
<summary><b>🎯 Smart Features</b></summary>

| Feature | Description | Benefit |
|---------|-------------|----------|
| 🏷️ **Device Model Mapping** | Translates codes ("U7PG2" → "UniFi AC Pro AP") | Human-readable names |
| 🔄 **Authentication Retry** | Auto-retry on auth failure | Network resilience |
| 🍪 **Session Management** | Handles TOKEN/unifises cookies | Seamless authentication |
| 🛡️ **CSRF Protection** | JWT token extraction & application | Security compliance |

</details>

### 🌐 Network Requirements

<details>
<summary><b>📋 Prerequisites Checklist</b></summary>

- ✅ **Direct Access**: Server → UniFi controller connectivity
- ✅ **Port Access**: HTTPS port (443/8443) accessibility  
- ✅ **Account Type**: Local controller account (not Cloud/SSO)
- ✅ **Admin Privileges**: Administrative controller access

</details>

---

<div align="center">

## 📄 License

**This project is open source.** See repository for license details.

---

*Made with ❤️ for the UniFi community*

**[⭐ Star this repo](https://github.com/jmagar/unifi-mcp)** • **[🐛 Report Issues](https://github.com/jmagar/unifi-mcp/issues)** • **[💡 Request Features](https://github.com/jmagar/unifi-mcp/issues/new)**

</div>