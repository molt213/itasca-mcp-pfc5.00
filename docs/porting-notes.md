# PFC 5.0 + itasca-mcp-bridge 移植调试记录

## 概述

**itasca-mcp-bridge** 官方支持 PFC 6.0/7.0 (Python 3.6+) 及以上版本。
本项目将其**逆向移植**到 PFC 5.0（Python 2.7.9），并修复了 MCP 客户端侧的
Windows 系统代理兼容性问题，使 `itasca-mcp` MCP 工具栈能在老版本 PFC 上完整运行。

**架构：**
```
Claude Code (MCP Client)
    ↕ MCP stdio
itasca-mcp v0.6.0 (MCP Server, uv tool)
    ↕ HTTP (localhost:9001)
itasca-mcp-bridge v0.4.1 (Python 2.7.9, 运行在 PFC 5.0 进程内)
    ↕ Python SDK
PFC 5.0 (pfc3d500_gui_64.exe)
```

## 兼容层改造汇总

### 改造前：itasca-mcp-bridge v0.4.1 的要求
- Python 3.6+（使用了 `threading.get_ident()`、`io.open(encoding=...)` 等 Python 3 特性）
- PFC 6.0+（`program log` 命令、`python-reset-state false` 等较新 API）
- `capture_pfc_console` 函数（PFC 6.0+ 才有兼容实现）

### 改造后：兼容 PFC 5.0 (Python 2.7.9) ✅
所有修改不改变上层逻辑，仅在底层做兼容适配。

---

## 已修改的文件（Bridge 层 — itasca-mcp-bridge）

### 1. `_compat.py` — threading.get_ident 不存在（Python 2.7.9 缺失）
- **文件：** `itasca_mcp_bridge/_compat.py`
- **问题：** Python 2.7.9 没有 `threading.get_ident()` 函数
- **修复：** 三级回退探测链
  1. `thread.get_ident`（Python 2 原生）
  2. `_thread.get_ident`（备选）
  3. `lambda: threading.current_thread().ident`（兜底）
- 暴露模块级 `get_ident()` 函数并全局注入 `sys.modules` 中的 `threading.get_ident`
- `snippet.py` 改为直接 `import thread; _get_ident = _thread_mod.get_ident`

### 2. `file_buffer.py` — io.open() 的 TextIOWrapper 只接受 unicode
- **文件：** `itasca_mcp_bridge/utils/file_buffer.py`
- **问题：** Python 2.7 中 `io.open(path, 'w', encoding='utf-8')` 返回的 `TextIOWrapper`
  只接受 `unicode` 类型，但 `print(42)` 产生 `str`（bytes 类型）
- **修复：** 在 `FileBuffer.write()` 和 `TeeBuffer.write()` 中添加：
  ```python
  if isinstance(s, bytes):
      s = s.decode('utf-8', 'replace')
  ```

### 3. `execute_code.py` — traceback 被吞
- **文件：** `itasca_mcp_bridge/handlers/execute_code.py`
- **问题：** 异常时没有完整 traceback 日志，难以排查错误
- **修复：** 添加 `traceback.print_exc()` + `traceback.format_exc()` 日志输出

### 4. `main_thread.py` — traceback 捕获顺序错误
- **文件：** `itasca_mcp_bridge/execution/main_thread.py`
- **问题：** `format_exc()` 在 `set_exception()` 之前调用，异常信息为空
- **修复：** 修复调用顺序，确保异常信息完整

### 5. `snippet.py` — 移除 PFC 5.0 不支持的 capture_pfc_console
- **文件：** `itasca_mcp_bridge/execution/snippet.py`
- **问题：** `capture_pfc_console` 依赖 PFC 6.0+ 的 `program log` 命令
- **修复：** 移除 `capture_pfc_console` 的所有导入和调用

### 6. `command_log.py` — program log 命令 PFC 5.0 不支持
- **文件：** `itasca_mcp_bridge/utils/command_log.py`
- **问题：** `program log-file ''` 命令在 PFC 5.0 中不存在
- **修复：** contextmanager 先发送探针命令，异常则静默跳过

---

## 已修改的文件（MCP Server 层 — itasca-mcp v0.6.0）

### 7. `client.py` — httpx 自动检测 Windows 系统代理导致 502
- **文件：** `itasca_mcp/bridge/client.py`（uv tool 安装目录）
- **问题：** `httpx` 默认自动检测 Windows 系统代理设置。系统代理无法处理
  `localhost:9001`，返回 **502 Bad Gateway**。直接使用 curl/urllib 正常（不经过代理），
  但通过 uv tool Python 环境的 httpx 请求全部走代理通道。
- **修复：** `httpx.AsyncClient()` 添加 `trust_env=False`，禁用代理自动检测
  ```python
  self._client = httpx.AsyncClient(base_url=self.url, trust_env=False)
  ```

### 8. `run_itasca_mcp.py` — 包装脚本（额外防御层）
- **文件：** `D:\claude\PFC_project\run_itasca_mcp.py`
- **作用：** 设置 `NO_PROXY=localhost,127.0.0.1,::1` 环境变量后启动 MCP 服务器，
  作为 `trust_env=False` 代码层修复之外的额外防御

---

## 运行状态（当前）

| 组件 | 状态 | 版本 | 端口 |
|---|---|---|---|
| PFC 5.0 GUI (pfc3d500_gui_64.exe) | ✅ 运行中 (PID 35088) | 5.0 | — |
| itasca-mcp-bridge | ✅ 运行中 | 0.4.1 (Python 2.7 compat patched) | TCP 9001 |
| itasca-mcp MCP Server | ✅ 已连接 (uv tool + NO_PROXY) | 0.6.0 | stdio 传输 |
| Bridge /health 端点 | ✅ 正常 | — | 200 OK |
| Bridge /events SSE 流 | ✅ 正常 | — | 200 OK |
| Bridge execute_code (POST) | ✅ 正常 | — | 200 OK |
| MCP Tools 注册 | ⏳ 需要重启客户端会话 | — | — |

## 已验证的功能

- ✅ HTTP 桥接服务启动和监听
- ✅ 健康检查端点 `/health`
- ✅ SSE 事件流 `/events`
- ✅ `execute_code` print() 输出捕获（Python 2.7 下正常工作）
- ✅ `execute_code` 多行代码执行
- ✅ `execute_code` 错误传播 (traceback)
- ✅ `execute_code` math 库等标准库操作
- ✅ 查询 PFC 命令文档（browse_commands、query_command）
- ✅ PFC 内 API 查询（query_python_api、browse_python_api）

## MCP 服务器配置

```json
{
  "mcpServers": {
    "itasca-mcp": {
      "type": "stdio",
      "command": "uv tool run itasca-mcp",
      "args": []
    }
  }
}
```

配置位置：用户级 `C:\Users\molt\.claude.json`（`--scope user`，全局生效）

## 启动/重启步骤

### 启动 Bridge（在 PFC 5.0 Python 控制台中）
```python
import itasca_mcp_bridge
itasca_mcp_bridge.start(auto_upgrade=False)
```
> `auto_upgrade=False` 跳过 PyPI 升级检测，避免因 Python 2.7 SSL 兼容性导致的问题。

### 启动 MCP 服务器（自动，无需手动操作）
通过 `claude mcp add --scope user` 配置后，Claude Code 自动管理 MCP 服务器进程。

### 验证 MCP 工具
```python
itasca_execute_code(code="print('hello from ITASCA')", timeout=10)
```

## 问题排查

### Bridge 连接失败
- 确认 PFC 5.0 GUI 在运行
- 确认 Bridge 已通过 Python 控制台启动
- 检查 `D:\PFC5.0\exe64\.itasca-mcp-bridge\bridge.log`

### MCP 工具返回 502
- httpx 代理问题：确认 `trust_env=False` 修改在 `client.py` 中生效
- 或通过包装脚本设置 `NO_PROXY=localhost,127.0.0.1,::1`

### MCP 工具不可见
- 重启 Claude Code 客户端会话
- 确认 `claude mcp list` 显示 `itasca-mcp` 为 `✔ Connected`
