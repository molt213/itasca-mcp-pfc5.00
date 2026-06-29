<p align="center">
  <img src="https://raw.githubusercontent.com/yusong652/itasca-mcp/assets/header.gif" alt="itasca-mcp-pfc5.00" width="70%">
</p>

# itasca-mcp-pfc5

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 2.7](https://img.shields.io/badge/python-2.7-blue)](https://www.python.org/)
[![PFC 5.0](https://img.shields.io/badge/PFC-5.0-brightgreen)]()

**itasca-mcp** 的 **PFC 5.0 逆向移植版**。

原项目 [itasca-mcp](https://github.com/yusong652/itasca-mcp) (© Yusong Han, Nagisa Toyoura) 
官方支持 PFC 6.0+/7.0/9.0 (Python 3.6+)。本项目通过兼容层将其完整移植到 
**PFC 5.0 (Python 2.7.9)**。

由于此移植版项目完全由**AI**修改编写，有许多功能还没来得及测试，属于是能跑的起来就行的那种。readme也是ai写的，我不一定能保证给ai看了之后它跑不跑得起来，反正我是边修边跑的，现在能跑起来了。
同时因为本人最近准备考研了，后续应该就没有那么多时间维护这个项目，望见谅。

`pfc3d> ;老版本也能跑 MCP`

## 架构

```
Claude Code (MCP Client)
    ↕ MCP stdio 协议
itasca-mcp v0.6.0 (MCP Server, 宿主机 Python 3.10+)
    ↕ HTTP localhost:9001
itasca-mcp-bridge v0.4.1-pfc5 (兼容层, PFC 5.0 Python 2.7 进程内)
    ↕ Python SDK
PFC 5.0 (pfc3d500_gui_64.exe)
```

## 智能体自动配置（推荐）

将以下文本复制给你的 AI 智能体，让它自动完成配置：

```text
请全程用中文与我交流。然后获取并完整按照这份引导指南执行（指南为英文，照其步骤操作即可）：
https://raw.githubusercontent.com/molt213/itasca-mcp-pfc5.00/main/docs/agentic/itasca-mcp-pfc5-bootstrap.md
```

> 💡 指南涵盖：MCP Client 配置 → PFC 5.0 路径探测 → Bridge 安装 → 启动 → 验证。
> 你的 AI 智能体会一步步引导你走完整个过程。

---

## 前提条件

| 组件 | 要求 | 用途 |
|---|---|---|
| **PFC** | 5.0 (`pfc3d500_gui_64.exe`) | 运行模拟 |
| **Python (宿主机)** | 3.10+ | 运行 itasca-mcp MCP Server |
| **[uv](https://docs.astral.sh/uv/getting-started/installation/)** | 最新版 | 安装 MCP Server |
| **Claude Code** (或其他 MCP 客户端) | 最新版 | 与 AI 交互 |

> ⚠️ 不同于上游需要 Python 3.6+，本移植版的 Bridge 运行在 **PFC 5.0 内置的 Python 2.7.9** 中。

---

## 快速开始

### 1. 注册 MCP Server（宿主机，只需一次）

```bash
claude mcp add itasca-mcp --scope user -- \
  uv tool run itasca-mcp
```

> **Windows 代理问题？** 如果遇到 502 Bad Gateway，见下方[安装教程]的代理修复步骤。

### 2. 启动 Bridge（每次打开 PFC 后执行）

下载 [`addon.py`](addon.py)（本项目修改后的 PFC 5.0 兼容版），
然后在 PFC 5.0 GUI 的 Python 控制台中任选一种方式执行：

- **方式 A：** 打开 `addon.py`，全选复制全部内容，粘贴到 PFC Python 控制台，回车
- **方式 B：** 将 `addon.py` 保存到本地，在 PFC 控制台中执行：
  ```python
  exec(open(r'D:\path\to\addon.py').read())
  ```

预期输出：
```
============================================================
Itasca MCP Bridge Bootstrap
============================================================
Python: 2.7.9
Installed itasca-mcp-bridge: 0.4.1
AUTO_UPGRADE is off. Keeping the current installation.
Using itasca-mcp-bridge: 0.4.1
Starting bridge on port 9001 ...
...
Task loop running via blocking poll (interval=20ms)
```

> ⚠️ PFC 5.0 没有 Qt 库，Bridge 会以 blocking poll 模式运行，这不影响功能。

### 3. 验证

重启 Claude Code（或你的 MCP 客户端），然后向它提问：

```
请在 PFC 中执行 itasca_execute_code，打印 "PFC 5.0 connected!"
```

预期返回：
```json
{"ok": true, "data": {"output": "PFC 5.0 connected!\n"}}
```

---

## 详细安装教程

### 第一步：宿主机 — 安装 MCP Server

在宿主机（你的电脑）上安装 itasca-mcp MCP Server：

```bash
# 安装 uv（如果还未安装）
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 itasca-mcp
uv tool install itasca-mcp

# 验证
uv tool run itasca-mcp --version
# 预期输出: itasca-mcp 0.6.0
```

### 第二步：配置 Claude Code

将 itasca-mcp 注册为 Claude Code 的 MCP Server：

```bash
claude mcp add itasca-mcp --scope user -- \
  uv tool run itasca-mcp
```

验证配置：
```bash
claude mcp list
# 预期输出: itasca-mcp: uv tool run itasca-mcp  - ✗ Disconnected
#（此时未连接是正常的，Bridge 还没启动）
```

> **⚠️ Windows 代理问题（502 Bad Gateway）**
>
> 如果宿主机设置了 Windows 系统代理，httpx 会自动将 localhost 请求路由到代理服务器，
> 导致 502 错误。修复方法（二选一）：
>
> **方法 A：** 安装后手动打补丁
> ```bash
> # 找到 client.py 位置
> CLIENT=$(uv tool list --show-path itasca-mcp)/Lib/site-packages/itasca_mcp/bridge/client.py
> # 编辑第 58 行，在 httpx.AsyncClient() 中添加 trust_env=False
> # self._client = httpx.AsyncClient(base_url=self.url, trust_env=False)
> ```
>
> **方法 B：** 使用包装脚本（无需修改源码）
> ```bash
> # 在 Claude Code 的 MCP 配置中，将 command 改为：
> # "command": "python",
> # "args": ["scripts/run_itasca_mcp.py"]
> ```
> 包装脚本会自动设置 `NO_PROXY=localhost,127.0.0.1,::1` 环境变量。

### 第三步：安装 Bridge 到 PFC 5.0

将 PFC 5.0 兼容的 Bridge 复制到 PFC 5.0 的 Python 环境中：

```bash
# 从本项目复制 bridge 源码
# 方法 A：完整复制（推荐）
xcopy /E /I bridge\itasca_mcp_bridge "D:\PFC5.0\exe64\python27\Lib\site-packages\itasca_mcp_bridge"

# 方法 B：通过 pip 安装（需要有 setuptools）
# cd bridge
# "D:\PFC5.0\exe64\python27\python.exe" -m pip install -e .
```

验证安装：在 PFC Python 控制台中执行：
```python
import itasca_mcp_bridge
print(itasca_mcp_bridge.__version__)
# 预期输出: 0.4.1
```

### 第四步：启动 Bridge

打开 PFC 5.0 GUI，在 Python 控制台中执行：

**方式一：使用 addon.py（推荐）**
```
1. 打开 scripts/addon.py
2. 全选复制所有内容
3. 粘贴到 PFC Python 控制台
4. 回车执行
```

预期输出：
```
============================================================
Itasca MCP Bridge Bootstrap
============================================================
Python: 2.7.9
Installed itasca-mcp-bridge: 0.4.1
AUTO_UPGRADE is off. Keeping the current installation.
Using itasca-mcp-bridge: 0.4.1
Starting bridge on port 9001 ...
...
Bridge started in blocking mode (console). Press Ctrl+C to stop.
```

> ⚠️ PFC 5.0 没有 Qt 绑定，Bridge 会在 blocking mode 下运行。
> 这不会影响使用，HTTP 服务运行在独立线程中。

**方式二：手动启动**
```python
import itasca_mcp_bridge
itasca_mcp_bridge.start(port=9001, auto_upgrade=False)
```

> ⚠️ **必须传 `auto_upgrade=False`！** 
> PFC 5.0 的 Python 2.7.9 SSL 太旧，无法连接 PyPI，不跳过升级会崩溃。

### 第五步：验证连接

回到 Claude Code，MCP 服务器会自动连接。验证：

```
itasca_execute_code(code="print('PFC 5.0 connected!')", timeout=10)
```

预期返回：
```json
{
  "ok": true,
  "data": {
    "output": "PFC 5.0 connected!\n"
  }
}
```

也可以试试查询 PFC 状态：
```
itasca_execute_code(code="import itasca as it; print('Balls:', it.ball.count())", timeout=10)
```

---

## 日常使用

每次打开 PFC 后，只需重启 Bridge：

```python
import itasca_mcp_bridge
itasca_mcp_bridge.start(port=9001, auto_upgrade=False)
```

MCP 客户端配置长期有效，无需重复配置。

---

## 工具清单 (10 个)

本项目继承了原版全部的 10 个 MCP 工具：

**5 个文档工具** — 浏览和搜索 PFC 命令、Python API 和参考文档。不需要 Bridge 运行。

| 工具 | 用途 |
|---|---|
| `browse_commands` | 浏览 PFC 命令树 |
| `query_command` | 搜索 PFC 命令 |
| `browse_python_api` | 浏览 Python API |
| `query_python_api` | 搜索 Python API |
| `browse_reference` | 浏览参考文档 |

**5 个执行工具** — 交互式 REPL、任务提交、进度监控、中断和历史。需要 Bridge 运行。

| 工具 | 用途 |
|---|---|
| `execute_code` | 在 PFC 中执行 Python 代码 (REPL) |
| `execute_task` | 提交长时间运行的任务 |
| `check_task_status` | 检查任务进度 |
| `interrupt_task` | 中断运行中的任务 |
| `list_tasks` | 浏览任务历史 |

---

## 与上游的差异

### PFC 5.0 兼容性

| 模块 | 修改 |
|---|---|
| `_compat.py` | **核心兼容层** — 新增 `threading.get_ident`、`Future`、`TimeoutError`、`Queue/queue`、HTTP server、`urlopen`、`importlib.invalidate_caches`、`makedirs` 等 Python 2/3 桥接 |
| `__init__.py` | `upgrade` 模块 import 异常保护 |
| `runtime.py` | `python-reset-state false` 回退 PFC 5.0 语法 |
| `file_buffer.py` | bytes→unicode 编解码保护 |
| `command_log.py` | `program log` 不存在的兼容处理 |
| `snippet.py` | 移除 `capture_pfc_console`；`thread.get_ident` 回退 |
| `main_thread.py` | traceback 调用顺序修复 |
| `execute_code.py` | 异常时完整 traceback 日志 |
| `upgrade.py` | 全部使用 `_compat` 兼容层 |

### Windows 代理修复

| 文件 | 修改 |
|---|---|
| `bridge/client.py` | `httpx.AsyncClient(trust_env=False)` 禁用 Windows 系统代理自动检测 |

### 项目配置差异

| 项目 | 上游 | 本移植版 |
|---|---|---|
| Bridge Python 版本 | 3.6+ | **2.7+** |
| MCP Server Python 版本 | 3.10+ | 3.10+（不变） |
| PFC 版本 | 6.0 / 7.0 / 9.0 | **5.0** |
| `auto_upgrade` | True (可联网升级) | **必须 False** (SSL 太旧) |
| Qt timer 模式 | 支持 | 不支持，fallback 到 blocking poll |
| 系统代理 | 需要手动处理 | `trust_env=False` 自动绕过 |

---

## 问题排查

### Bridge 无法启动

```
ImportError: cannot import name ...
```

**原因：** `addon.py` 的 `_import_bridge()` 删除模块缓存时只删了顶层模块，
Python 2.7 的相对导入会因父子模块对象不匹配而失败。

**解决：** 确保使用本项目 `scripts/addon.py` 的最新版本，
它会在重载 Bridge 时清除所有子模块缓存。

---

### SSL 连接错误

```
SSLError: EOF occurred in violation of protocol
```

**原因：** Python 2.7.9 的 OpenSSL 太旧，无法与现代 PyPI 建立 TLS 1.2+ 连接。

**解决：** `start()` 时传 `auto_upgrade=False`，或用 `scripts/addon.py`。

---

### 502 Bad Gateway

**原因：** httpx 自动检测 Windows 系统代理，将 localhost 请求路由到代理服务器。

**解决：** 
1. 给 MCP Server 的 `client.py` 打补丁（加 `trust_env=False`）
2. 或使用 `scripts/run_itasca_mcp.py` 包装脚本
3. 或设置环境变量 `NO_PROXY=localhost,127.0.0.1,::1`

---

### 5057 MCP 工具不可见

```bash
claude mcp list
```

如果显示 `✗ Disconnected`，重启 Claude Code 会话即可。

---

### Qt 不可用

```
Task loop running via blocking poll (interval=20ms)
```

PFC 5.0 不包含 PySide2/PySide6，这是正常现象。Bridge 会以 blocking poll 
模式运行，不影响功能。

---

## 文件清单

```
itasca-mcp-pfc5/
├── LICENSE                         # MIT 许可证
├── README.md                       # 本文件
├── CHANGELOG.md                    # 更新日志
│
├── bridge/                         # PFC 5.0 兼容的 bridge 源码
│   ├── pyproject.toml
│   ├── setup.py
│   └── itasca_mcp_bridge/          # 32 个 .py 文件
│       ├── __init__.py
│       ├── _compat.py              # Python 2/3 兼容层
│       ├── runtime.py / server.py / upgrade.py / announce.py
│       ├── execution/              # 代码执行引擎
│       ├── handlers/               # MCP 请求处理器
│       ├── signals/                # PFC 事件回调
│       ├── tasks/                  # 任务管理
│       └── utils/                  # 工具函数
│
├── scripts/
│   ├── addon.py                    # PFC 5.0 一键启动引导脚本
│   └── run_itasca_mcp.py           # MCP Server 包装脚本
│
├── patches/
│   └── itasca-mcp/
│       └── client.py.trust_env.patch  # Windows 代理修复补丁
│
└── docs/
    └── porting-notes.md            # 完整移植调试记录
```

## 许可

MIT License。

- 上游 [itasca-mcp](https://github.com/yusong652/itasca-mcp) © 2025-2026 Yusong Han, Nagisa Toyoura
- PFC 5.0 兼容层 © 2026 itasca-mcp-pfc5 contributors
