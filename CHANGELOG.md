# Changelog

## v0.4.1-pfc5 (2026-06-29)

首个 PFC 5.0 兼容版本，基于 itasca-mcp-bridge v0.4.1 上游。

### 新增
- `_compat.py`: Python 2/3 兼容层，涵盖 `threading.get_ident`、`Future`、`TimeoutError`、
  `Queue/queue`、HTTP server、`urlopen`、`importlib.invalidate_caches`、`makedirs` 等
- `scripts/addon.py`: PFC 5.0 一键启动引导脚本（自动跳过 PyPI 升级）
- `scripts/run_itasca_mcp.py`: MCP Server 包装脚本（设置 `NO_PROXY` 环境变量）

### 修复
- **`__init__.py`**: `from . import upgrade` 用 `try/except ImportError` 保护，
  避免 upgrade 模块不存在时崩溃
- **`runtime.py`**: `python-reset-state false` 命令增加 PFC 5.0 语法回退
- **`utils/file_buffer.py`**: `TextIOWrapper` 在 Python 2.7 只接受 `unicode` 类型，
  添加 bytes→unicode 自动解码
- **`utils/command_log.py`**: `program log-file ''` 在 PFC 5.0 中不存在，
  通过探针命令+异常静默跳过
- **`execution/snippet.py`**: 移除 PFC 5.0 不支持的 `capture_pfc_console`；
  添加 `thread.get_ident` 兼容回退
- **`execution/main_thread.py`**: 修复 `traceback.format_exc()` 在 `set_exception()`
  之前调用的顺序错误
- **`handlers/execute_code.py`**: 异常时添加 `traceback.print_exc()` 完整日志
- **`bridge/client.py`** (MCP Server): `httpx.AsyncClient(trust_env=False)`
  禁用 Windows 系统代理自动检测，修复 502 Bad Gateway

### 兼容性
- 全部 32 个 `.py` 文件均添加 `from __future__ import absolute_import, print_function`
- 全部使用 `.format()` 风格字符串格式化（Python 2.6+），无 f-string
- 类型标注仅使用注释形式 (`# type:`)，无运行时类型提示
