# itasca-mcp-pfc5

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**itasca-mcp** 的 **PFC 5.0 逆向移植版**。

原项目 [itasca-mcp](https://github.com/yusong652/itasca-mcp) 官方支持 PFC 6.0+/7.0 (Python 3.6+)。
本项目通过兼容层将其移植到 **PFC 5.0 (Python 2.7.9)**，并修复了 Windows 系统代理导致的连接问题。

---

## 架构

```
Claude Code (MCP Client)
    ↕ MCP stdio 协议
itasca-mcp v0.6.0 (MCP Server, Python 3.10+, 运行在宿主机)
    ↕ HTTP (localhost:9001)
itasca-mcp-bridge v0.4.1-pfc5 (兼容层, Python 2.7.9, 运行在 PFC 5.0 进程内)
    ↕ Python SDK
PFC 5.0 (pfc3d500_gui_64.exe)
```

## 前提条件

| 组件 | 要求 |
|---|---|
| PFC | 5.0 (pfc3d500_gui_64.exe) |
| Python (宿主机) | 3.10+ (用于 itasca-mcp MCP Server) |
| uv | 已安装 (`pip install uv`) |
| Claude Code | 已安装 |

## 快速开始

### 1. 安装 MCP Server (宿主机)

```bash
uv tool install itasca-mcp
```

验证安装：
```bash
uv tool run itasca-mcp --version
```

### 2. 配置 Claude Code MCP Server

```bash
claude mcp add itasca-mcp --scope user -- \
  uv tool run itasca-mcp
```

### 3. 安装 Bridge (PFC 5.0 内部)

Bridge 兼容层安装到 PFC 5.0 的 Python 2.7 环境中：

```bash
# 确保目标目录存在
xcopy /E /I bridge\itasca_mcp_bridge "D:\PFC5.0\exe64\python27\Lib\site-packages\itasca_mcp_bridge"
```

### 4. 启动 Bridge (PFC Python 控制台)

打开 PFC 5.0 GUI，在 Python 控制台中执行：

```python
import itasca_mcp_bridge
itasca_mcp_bridge.start(port=9001, auto_upgrade=False)
```

> **注意：** PFC 5.0 的 SSL 太旧无法连接 PyPI，必须传 `auto_upgrade=False`。

或者使用一次性启动脚本（推荐）：

```
1. 打开 scripts/addon.py
2. 复制全部内容到 PFC Python 控制台
3. 回车执行
```

### 5. 验证连接

回到 Claude Code，执行：

```python
itasca_execute_code(code="print('PFC 5.0 connected!')", timeout=10)
```

预期返回：
```json
{"ok": true, "data": {"output": "PFC 5.0 connected!\n"}}
```

## 与上游的差异

### Bridge 层 (PFC 5.0 兼容)

| 文件 | 修改内容 |
|---|---|
| `_compat.py` | Python 2/3 兼容层：`threading.get_ident`、`Future`、`TimeoutError`、`Queue/queue`、HTTP server、`urlopen`、`importlib.invalidate_caches`、`makedirs`、`logging.raiseExceptions` |
| `__init__.py` | `upgrade` 模块 import 异常保护 |
| `runtime.py` | `python-reset-state false` 命令兼容 PFC 5.0 语法 |
| `utils/file_buffer.py` | bytes→unicode 编解码保护 (`TextIOWrapper` 在 Python 2.7 只接受 `unicode`) |
| `utils/command_log.py` | `program log-file ''` 在 PFC 5.0 中不存在的兼容处理 |
| `execution/snippet.py` | 移除 PFC 5.0 不支持的 `capture_pfc_console`；`thread.get_ident` 回退链 |
| `execution/main_thread.py` | `traceback.format_exc()` 调用顺序修复 |
| `handlers/execute_code.py` | 异常时 traceback 完整日志输出 |
| `upgrade.py` | 全部使用 `_compat` 兼容层；`sys.version_info >= (3, 10)` 安全守卫 |

### MCP Server 层 (Windows 代理修复)

| 文件 | 修改内容 |
|---|---|
| `bridge/client.py` | `httpx.AsyncClient(trust_env=False)` 禁用 Windows 系统代理自动检测 |

### 辅助脚本

| 文件 | 作用 |
|---|---|
| `scripts/addon.py` | 一键启动引导脚本：加载已安装的 bridge，跳过 PyPI 升级，启动服务 |
| `scripts/run_itasca_mcp.py` | MCP Server 包装脚本：设置 `NO_PROXY` 环境变量 |

## 常见问题

### Bridge 连不上

1. 确认 PFC 5.0 GUI 在运行
2. 确认 Bridge 已在 Python 控制台启动（看是否有 `Bridge started` 输出）
3. 检查日志：`D:\PFC5.0\exe64\.itasca-mcp-bridge\bridge.log`

### MCP 工具返回 502

Windows 系统代理问题。确保：
- MCP Server 端：`trust_env=False` 在 `client.py` 中生效
- 或使用包装脚本：`scripts/run_itasca_mcp.py`

### MCP 工具不可见

重启 Claude Code 会话，然后检查：
```bash
claude mcp list
```
预期输出：`itasca-mcp: uv tool run itasca-mcp  - ✔ Connected`

## 许可证

MIT License。详见 [LICENSE](LICENSE)。

- 上游 [itasca-mcp](https://github.com/yusong652/itasca-mcp) © 2025-2026 Yusong Han, Nagisa Toyoura
- PFC 5.0 兼容层 © 2026 itasca-mcp-pfc5 contributors
