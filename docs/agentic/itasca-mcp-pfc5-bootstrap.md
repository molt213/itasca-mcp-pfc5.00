# itasca-mcp-pfc5 Agent Bootstrap Guide

Use this guide when an agent needs to set up `itasca-mcp-pfc5` (the PFC 5.0
backport) execution end-to-end on a Windows machine.

> **PFC 5.0 only.** If you have PFC 6.0/7.0/9.0, use the upstream guide:
> <https://raw.githubusercontent.com/yusong652/itasca-mcp/main/docs/agentic/itasca-mcp-bootstrap.md>
>
> PFC 5.0 ships Python 2.7.9, while all later versions ship Python 3.6+.
> The bridge code is almost identical, but the embedded interpreter, the
> Qt availability, and the PyPI access change several steps.

## Target Outcome

1. MCP client is configured to run `itasca-mcp` (upstream, on the **host**
   machine, not inside PFC).
2. PFC 5.0 compatible `itasca-mcp-bridge` is installed in PFC 5.0's embedded
   Python 2.7 environment.
3. Bridge is started in the PFC 5.0 GUI via `itasca_mcp_bridge.start()`.
4. MCP execution tools are verified with `itasca_execute_code`.

## Architecture Reminder

```
Claude Code (MCP Client)
    ↕ MCP stdio 协议
itasca-mcp v0.6.0 (MCP Server, 宿主机 Python 3.10+)
    ↕ HTTP localhost:9001
itasca-mcp-bridge v0.4.2 (PFC 5.0 Python 2.7 进程内)
    ↕ Python SDK
PFC 5.0 (pfc3d500_gui_64.exe)
```

The MCP Server (`itasca-mcp`) runs on your host machine (Python 3.10+).
Only the Bridge (`itasca-mcp-bridge`) runs inside PFC 5.0's embedded
Python 2.7.9.

## Agent Execution Rules

- Use bounded, fast path detection for `pfc5_path`; avoid full-drive
  recursive scans by default.
- `pfc5_python` is always `{pfc5_path}/exe64/python27/python.exe`.
- The upstream `itasca-mcp` MCP server MUST be installed via `uv tool install`
  on the host machine. Only the bridge is PFC 5.0-specific.
- If a step fails, report the exact command and output, then apply the
  next fallback.
- Respect step ownership labels:
  - `[AGENT]` means the agent should execute the action.
  - `[USER ACTION REQUIRED]` means the user must execute it manually.
  - `[HOST]` means run on the host machine (outside PFC).

## Step 0 — Determine Host Python Version

[HOST][AGENT]

Before anything else, check which Python the host machine has available:

```bash
python --version
python3 --version
```

The MCP Server (`itasca-mcp`) requires **Python 3.10+** and uses `uv` as
its launcher. If Python 3.10+ is not available, install it first:
<https://www.python.org/downloads/>

Then install `uv`:
```bash
pip install uv
# Or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Step 1 — Configure MCP Client (Host Machine)

[HOST][AGENT]

The MCP Server `itasca-mcp` runs on the **host machine** (not inside PFC).
Configure your client to launch it via `uv tool run itasca-mcp`.

### Claude Code

```bash
claude mcp add itasca-mcp --scope user -- \
  uv tool run itasca-mcp
```

If the above doesn't work, create or edit the config file at
`C:\Users\<USER>\.claude.json`:
```json
{
  "mcpServers": {
    "itasca-mcp": {
      "command": "uv tool run itasca-mcp",
      "args": []
    }
  }
}
```

> **Windows proxy note:** If you get `502 Bad Gateway` errors later, the
> `trust_env=False` patch is needed. See Step 1a below.

### Step 1a — Windows Proxy Fix (if needed)

[HOST][AGENT]

If the host has Windows system proxy enabled, `httpx` (inside the MCP Server)
will route `localhost:9001` through the proxy and return **502 Bad Gateway**.

**Fix A — Patch client.py (recommended):**
```bash
# Find the installed client.py
$CLIENT_DIR = uv tool list --show-path itasca-mcp
$CLIENT = Join-Path $CLIENT_DIR "Lib\site-packages\itasca_mcp\bridge\client.py"
# Edit line ~58: add trust_env=False
# self._client = httpx.AsyncClient(base_url=self.url, trust_env=False)
```

**Fix B — Wrapper script (no modification needed):**
Create `run_itasca_mcp.py`:
```python
import os, sys, subprocess
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
cmd = ["uv", "tool", "run", "itasca-mcp"] + sys.argv[1:]
proc = subprocess.Popen(cmd)
try: proc.wait()
except KeyboardInterrupt: proc.terminate(); proc.wait()
```
Then in MCP config, replace `command` with `python run_itasca_mcp.py`.

## Step 2 — Resolve `pfc5_path`

[AGENT]

`pfc5_path` is the PFC 5.0 install directory containing `exe64/pfc3d500_gui_64.exe`.

### 2.0 Quick probe (fast path)

Try lightweight checks first:
```bash
ls "C:/Program Files/Itasca/PFC500"
ls "D:/Program Files/Itasca/PFC500"
ls "C:/PFC5.0"
ls "D:/PFC5.0"
```
If found, set `pfc5_path` to that directory and verify:
```bash
ls "{pfc5_path}/exe64/pfc3d500_gui_64.exe"
ls "{pfc5_path}/exe64/python27/python.exe"
```

### 2.1 Registry lookup (fallback)

```powershell
$keys=@('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*');
Get-ItemProperty $keys -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -match 'PFC 5|PFC500|Itasca' } |
  Select-Object DisplayName, InstallLocation
```

If still unresolved, ask user to provide exact `pfc5_path`.

## Step 3 — Install Bridge in PFC 5.0's Python 2.7

[AGENT]

> ⚠️ Unlike upstream (which uses `pip install`), PFC 5.0's Python 2.7.9
> has an SSL that is too old to connect to PyPI. We install the bridge by
> copying the compat-patched files directly.

### 3.1 Resolve PFC 5.0 Python

```powershell
$pfc5_python = Join-Path "{pfc5_path}" "exe64\python27\python.exe"
& $pfc5_python --version
# Expected: Python 2.7.9
```

### 3.2 Download or locate the patched bridge

The PFC 5.0 compatible bridge is available in the
[itasca-mcp-pfc5](https://github.com/molt213/itasca-mcp-pfc5.00) repo.

**Option A — From cloned/fetched repo:**
```bash
# Copy the entire bridge package into PFC 5.0's site-packages
xcopy /E /I bridge\itasca_mcp_bridge "{pfc5_path}\exe64\python27\Lib\site-packages\itasca_mcp_bridge"
```

**Option B — From addon.py (install + start in one step):**
[USER ACTION REQUIRED]
Ask the user to:
1. Open content of `scripts/addon.py` (or `addon.py` from the repo root)
2. Paste the entire content into PFC 5.0's Python console
3. Press Enter

The script will auto-detect the installed bridge, skip upgrade, and start
the service. See Step 4 for expected output.

### 3.3 Verify (if installed manually via Option A)

```powershell
& $pfc5_python -c "import itasca_mcp_bridge; print(itasca_mcp_bridge.__version__)"
# Expected: 0.4.1
```

## Step 4 — Start the Engine GUI and Bridge

[AGENT]

### 4.1 Start PFC 5.0 GUI (if not already open)

If the GUI is not yet running:
```bash
powershell -NoProfile -Command "$gui='{pfc5_path}/exe64/pfc3d500_gui_64.exe'; Start-Process $gui"
```

Wait a moment for the GUI to initialize, then confirm:
```bash
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Name -match 'pfc3d500' } | Select-Object Name,Id"
```

### 4.2 Start the Bridge

[USER ACTION REQUIRED]

Ask the user to run this in the **PFC 5.0 GUI Python console**:

**Option A — One-shot (recommended):**
```
1. Open scripts/addon.py from the itasca-mcp-pfc5 repo
2. Select all, copy, paste into PFC Python console, press Enter
```

**Option B — Minimal two-liner:**
```python
import itasca_mcp_bridge
itasca_mcp_bridge.start(port=9001, auto_upgrade=False)
```

> ⚠️ **Must pass `auto_upgrade=False`!** PFC 5.0's Python 2.7.9 cannot
> connect to PyPI (SSL too old). Without this flag, the bridge will crash
> on import of the upgrade module.

Expected output:
```
============================================================
Itasca MCP Bridge Server
============================================================
  Version:  0.4.1
  URL:      http://localhost:9001
  Log:      D:\PFC5.0\exe64\.itasca-mcp-bridge\bridge.log
============================================================

Task loop running via blocking poll (interval=20ms)
Bridge started in blocking mode (console). Press Ctrl+C to stop.
```

> ⚠️ **Qt not available:** PFC 5.0 does not ship PySide2/PySide6, so the
> bridge runs in **blocking poll** mode instead of Qt timer mode. This is
> normal and does not affect functionality. The HTTP server runs on a
> daemon thread.

## Step 5 — Restart MCP Client and Verify

[AGENT]

### 5.1 Restart the MCP client session

The `itasca-*` MCP tools will not appear until the client session is fully
restarted. Close and reopen Claude Code (or your MCP client).

### 5.2 Verify MCP Server connection

```bash
claude mcp list
# Expected: itasca-mcp: uv tool run itasca-mcp  - ✔ Connected
```

### 5.3 Test execution

Call the `itasca_execute_code` tool:

```
itasca_execute_code(code="print('PFC 5.0 connected!')", timeout=10)
```

Expected success:
```json
{"ok": true, "data": {"output": "PFC 5.0 connected!\n"}}
```

### 5.4 Test PFC API access

```
itasca_execute_code(code="import itasca as it; print('Balls:', it.ball.count())", timeout=10)
```

## Troubleshooting

### Bridge crashes on `from . import upgrade`

```
ImportError: cannot import name upgrade
```

**Cause:** The `start()` function tries to import the `upgrade` module before
checking whether auto-upgrade is needed.

**Fix:** Pass `auto_upgrade=False`:
```python
itasca_mcp_bridge.start(port=9001, auto_upgrade=False)
```
Or use `scripts/addon.py` which handles this automatically.

---

### Bridge crashes on `from . import runtime`

```
ImportError: cannot import name runtime
```

**Cause:** Python 2.7's relative import machinery fails when the parent
package was re-imported (e.g. after `del sys.modules["itasca_mcp_bridge"]`)
but submodules from the old import are still cached in `sys.modules`.
The new parent module object doesn't match the old submodule's parent.

**Fix:** If importing bridge manually, clear all submodule entries:
```python
for key in list(sys.modules):
    if key == "itasca_mcp_bridge" or key.startswith("itasca_mcp_bridge."):
        del sys.modules[key]
import itasca_mcp_bridge
```
Or use `scripts/addon.py` which handles this correctly.

---

### SSL / PyPI connection failure

```
SSLError: EOF occurred in violation of protocol
```

**Cause:** Python 2.7.9's OpenSSL (typically 1.0.1) only supports TLS 1.0
and 1.1. Modern PyPI requires TLS 1.2+.

**Fix:** 
- Pass `auto_upgrade=False` to `start()`
- Do NOT set `AUTO_UPGRADE = True`
- The bridge is already installed; no PyPI access is needed

---

### 502 Bad Gateway

**Cause:** httpx (inside the MCP Server process on the host) auto-detects
Windows system proxy settings and routes `localhost:9001` through the
corporate proxy.

**Fix:** See Step 1a — apply `trust_env=False` patch or use wrapper script.

---

### MCP tools not visible

```bash
claude mcp list
# Shows: ✗ Disconnected  or  tool not listed
```

**Causes and fixes:**
1. **Client session not restarted** after MCP config change — fully close
   and reopen the client.
2. **Bridge not running** — check PFC GUI console for bridge output.
3. **Wrong MCP config** — verify `claude mcp list` shows `itasca-mcp`.
4. **Re-install:** If all else fails, remove and re-add:
   ```bash
   claude mcp remove itasca-mcp
   claude mcp add itasca-mcp --scope user -- uv tool run itasca-mcp
   ```

---

### Qt not available / blocking mode

```
Task loop running via blocking poll (interval=20ms)
```

PFC 5.0 does not ship PySide2 or PySide6. The bridge runs in blocking poll
mode, which is normal for this version. The HTTP server runs on a daemon
thread and all MCP tools work as expected.

To stop the bridge, press Ctrl+C in the PFC Python console.

---

### Bridge already running / port in use

```
Port 9001 is already in use.
```

Stop the existing bridge (Ctrl+C in the PFC console where it's running,
or close and reopen PFC), then retry. Alternatively, use a different port:
```python
itasca_mcp_bridge.start(port=9002, auto_upgrade=False)
```
And update your MCP Server config's `--bridge-port` argument.

---

### `pip install` fails inside PFC Python

**Cause:** Python 2.7.9's SSL + old pip combined cannot talk to modern PyPI.

**Fix:** Do NOT use pip. Install the bridge by copying the patched files
directly (see Step 3.2 — Option A). If you must use pip, first upgrade
pip and SSL certs (not recommended, complex):
```bash
# This may not work; manual copy is the supported method
{pfc5_python} -m pip install --upgrade pip
```

---

### `python-reset-state false` fails

This is cosmetic. The bridge tries both command variants. PFC 5.0 does
not support this command, which is harmless. Ignore the error.
