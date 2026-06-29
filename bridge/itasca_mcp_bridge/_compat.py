# -*- coding: utf-8 -*-
"""Python 2/3 compatibility shim for itasca-mcp-bridge."""

from __future__ import absolute_import, print_function, division

import sys
import os
import threading
import logging

# Python 2.7.9 doesn't expose threading.get_ident() - patch it globally
# This function is THE canonical source so _compat.get_ident is always safe.
try:
    import thread as _patch_thread
    _get_ident = _patch_thread.get_ident
except ImportError:
    try:
        import _thread as _patch_thread2
        _get_ident = _patch_thread2.get_ident
    except ImportError:
        _get_ident = lambda: threading.current_thread().ident

# Also expose as a module-level function for direct use
def get_ident():
    return _get_ident()

# Patch threading.get_ident if missing
if not hasattr(threading, 'get_ident'):
    threading.get_ident = _get_ident
    # Force-patch into sys.modules so any module that references threading
    # (even via an already-cached reference) sees get_ident.
    for _mod in sys.modules.values():
        if _mod is not None and hasattr(_mod, 'threading'):
            try:
                _mod.threading.get_ident = _get_ident
            except Exception:
                pass
    # Also ensure sys.modules['threading'] is patched for future from-imports
    if 'threading' in sys.modules:
        sys.modules['threading'].get_ident = _get_ident
        sys.modules['threading']._get_ident = _get_ident

    logger = logging.getLogger("itasca-mcp-bridge")
    logger.info("threading.get_ident patched via _compat (Python 2.7 compat)")

PY2 = sys.version_info[0] == 2

# =============================================================================
# CompatInterruptedError - Python 3.5+ has InterruptedError; Python 2 doesn't
# =============================================================================
class CompatInterruptedError(Exception):
    pass

# =============================================================================
# Future - minimal concurrent.futures.Future replacement for Python 2.7
# =============================================================================
class Future(object):
    """Minimal Future implementation compatible with Python 2.7.
    
    Supports the subset of concurrent.futures.Future used by itasca-mcp-bridge:
    - result(timeout=None)
    - done()
    - running()
    - set_running_or_notify_cancel()
    - set_result(result)
    - set_exception(exception)
    - cancelled()
    """
    
    _STATE_PENDING = 'PENDING'
    _STATE_RUNNING = 'RUNNING'
    _STATE_FINISHED = 'FINISHED'
    _STATE_CANCELLED = 'CANCELLED'
    
    def __init__(self):
        self._condition = threading.Condition()
        self._state = self._STATE_PENDING
        self._result = None
        self._exception = None
    
    def done(self):
        with self._condition:
            return self._state in (self._STATE_FINISHED, self._STATE_CANCELLED)
    
    def running(self):
        with self._condition:
            return self._state == self._STATE_RUNNING
    
    def cancelled(self):
        with self._condition:
            return self._state == self._STATE_CANCELLED
    
    def result(self, timeout=None):
        with self._condition:
            if self._state == self._STATE_CANCELLED:
                raise Exception("Future cancelled")
            if self._state == self._STATE_FINISHED:
                if self._exception is not None:
                    raise self._exception
                return self._result
            self._condition.wait(timeout)
            if self._state == self._STATE_FINISHED:
                if self._exception is not None:
                    raise self._exception
                return self._result
            if self._state == self._STATE_CANCELLED:
                raise Exception("Future cancelled")
            raise TimeoutError("Future timed out after {} seconds".format(timeout))
    
    def set_running_or_notify_cancel(self):
        with self._condition:
            if self._state == self._STATE_CANCELLED:
                return False
            if self._state != self._STATE_PENDING:
                raise Exception("Future already executed")
            self._state = self._STATE_RUNNING
            return True
    
    def set_result(self, result):
        with self._condition:
            self._result = result
            self._state = self._STATE_FINISHED
            self._condition.notify_all()
    
    def set_exception(self, exception):
        with self._condition:
            self._exception = exception
            self._state = self._STATE_FINISHED
            self._condition.notify_all()
    
    def cancel(self):
        with self._condition:
            if self._state == self._STATE_PENDING:
                self._state = self._STATE_CANCELLED
                self._condition.notify_all()
                return True
            return False

# =============================================================================
# TimeoutError - Python 3 builtin, not in Python 2
# =============================================================================
try:
    TimeoutError = TimeoutError
except NameError:
    class TimeoutError(Exception):
        pass


# =============================================================================
# Queue - Python 3 has queue, Python 2 has Queue
# =============================================================================
if PY2:
    import Queue as _queue_mod
else:
    import queue as _queue_mod

Queue = _queue_mod.Queue
Empty = _queue_mod.Empty
Full = _queue_mod.Full
# Also provide the module itself for code that does queue.Queue()
queue = _queue_mod


# =============================================================================
# HTTP Server
# =============================================================================
if PY2:
    import BaseHTTPServer as _http_mod
    import SocketServer as _socket_mod
    http_server = _http_mod
    socketserver = _socket_mod
    HTTPServer = _http_mod.HTTPServer
    BaseHTTPRequestHandler = _http_mod.BaseHTTPRequestHandler
    ThreadingMixIn = _socket_mod.ThreadingMixIn
else:
    import http.server as _http_mod
    import socketserver as _socket_mod
    http_server = _http_mod
    socketserver = _socket_mod
    HTTPServer = _http_mod.HTTPServer
    BaseHTTPRequestHandler = _http_mod.BaseHTTPRequestHandler
    ThreadingMixIn = _socket_mod.ThreadingMixIn


# =============================================================================
# URL handling
# =============================================================================
if PY2:
    import urllib2 as _urllib2_mod
    urlopen = _urllib2_mod.urlopen
else:
    from urllib.request import urlopen


# =============================================================================
# importlib helpers
# =============================================================================
try:
    import importlib as _importlib
    if PY2:
        invalidate_import_caches = getattr(_importlib, 'invalidate_caches', lambda: None)
    else:
        invalidate_import_caches = _importlib.invalidate_caches
except ImportError:
    invalidate_import_caches = lambda: None


# =============================================================================
# os.makedirs with exist_ok (Python 2 doesn't have exist_ok param)
# =============================================================================
def makedirs(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


# =============================================================================
# Temporarily suppress exceptions from logging handlers
# =============================================================================
if PY2:
    def suppress_logging_raiseExceptions():
        prev = logging.raiseExceptions
        logging.raiseExceptions = 0
        return prev
    
    def restore_logging_raiseExceptions(prev):
        logging.raiseExceptions = prev
else:
    def suppress_logging_raiseExceptions():
        prev = logging.raiseExceptions
        logging.raiseExceptions = False
        return prev
    
    def restore_logging_raiseExceptions(prev):
        logging.raiseExceptions = prev
