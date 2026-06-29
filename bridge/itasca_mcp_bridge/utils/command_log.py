# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""Capture ITASCA console output from itasca.command() calls."""

import io
import logging
import os
import uuid
from contextlib import contextmanager

logger = logging.getLogger("itasca-mcp-bridge")


def _strip_footer(content):
    """Strip the trailing `program log off` echo + 3-line banner footer."""
    if not content:
        return content
    lines = content.splitlines(keepends=True)
    for i in range(len(lines) - 1, -1, -1):
        if "program log off" in lines[i]:
            return "".join(lines[:i])
    return content


@contextmanager
def capture_pfc_console(stdout_sink, log_dir):
    """Within this block, monkey-patch itasca.command() so each call's ITASCA
    console output is captured and written to ``stdout_sink``.

    If the ``program log`` subsystem is not available (PFC 5.0) the block
    is a no-op -- the caller's code still runs, but ITASCA command output
    is not captured.
    """
    import itasca
    orig_command = itasca.command
    try:
        orig_command("program log-file ''")
    except Exception:
        logger.info("capture_pfc_console: program log not supported, skipping capture")
        yield
        return
    itasca.command = orig_command

    log_dir = os.path.abspath(log_dir) if log_dir else log_dir
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            pass

    log_path = os.path.join(log_dir, "cmdtmp_%s.log" % uuid.uuid4().hex[:8])
    log_path_pfc = log_path.replace("\\", "/")

    def _read_and_strip():
        try:
            with io.open(log_path, encoding="utf-8", errors="replace") as f:
                return _strip_footer(f.read())
        except OSError:
            return ""

    def patched(cmd):
        orig_command("program log on truncate show-message off")
        try:
            orig_command(cmd)
        finally:
            orig_command("program log off")
            chunk = _read_and_strip()
            if chunk:
                try:
                    stdout_sink.write(chunk)
                except Exception as e:
                    logger.warning("capture_pfc_console: stdout write failed: %s", e)

    orig_command("program log-file '%s'" % log_path_pfc)
    itasca.command = patched
    try:
        yield
    finally:
        itasca.command = orig_command
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except OSError:
            pass
