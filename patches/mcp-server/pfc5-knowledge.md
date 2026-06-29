# MCP Server PFC 5.0 知识库补丁

启用 `browse_commands` 和 `query_command` 对 PFC 5.0 的支持。
修改路径基于 `uv tool list --show-path itasca-mcp` 的输出。

## 1. 复制知识库文件

```bash
xcopy /E /I knowledge\resources "C:\Users\<USER>\AppData\Roaming\uv\tools\itasca-mcp\Lib\site-packages\itasca_mcp\knowledge\resources"
```

## 2. 修改 utils.py

**文件:** `Lib/site-packages/itasca_mcp/utils.py`

在 `CommandDocVersion` 枚举中追加 `V5_0`:

```python
class CommandDocVersion(str, Enum):
    V5_0 = "5.0"     # ← 新增
    V6_0 = "6.0"
    V7_0 = "7.0"
    V9_0 = "9.0"
```

## 3. 修改 browse_commands.py

**文件:** `Lib/site-packages/itasca_mcp/tools/browse_commands.py`

在 `version` 参数的 `description` 末尾追加:

```
PFC 5.0 is also supported — pass version='5.0' to browse it.
```

## 4. 修改 query_command.py

**文件:** `Lib/site-packages/itasca_mcp/tools/query_command.py`

同上，在 `version` 参数的 `description` 末尾追加:

```
PFC 5.0 is also supported — pass version='5.0' to search it.
```
