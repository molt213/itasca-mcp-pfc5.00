#!/usr/bin/env python3
"""Wrapper for itasca-mcp MCP server.

Sets NO_PROXY to bypass Windows system proxy detection that httpx performs.
Without this, httpx routes localhost requests through the corporate proxy
and the bridge returns 502 Bad Gateway errors.
"""
import os
import sys
import subprocess

# Prevent httpx from auto-detecting Windows system proxy
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

cmd = ["uv", "tool", "run", "itasca-mcp"] + sys.argv[1:]

if __name__ == "__main__":
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
