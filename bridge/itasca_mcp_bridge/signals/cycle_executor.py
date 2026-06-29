# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""Cycle-gap executor for execute_code snippets."""

import logging
from .._compat import Future, Queue, Empty
from io import StringIO

from .positions import EXECUTOR_CALLBACK_POSITION, register_cycle_callback

logger = logging.getLogger("itasca-mcp-bridge")

_pending_queue = Queue()
MAX_BATCH_SIZE = 10


def submit_snippet(code, request_id):
    future = Future()
    _pending_queue.put((code, request_id, future))
    logger.debug("Snippet queued: request_id=%s (queue_size=%d)",
                 request_id, _pending_queue.qsize())
    return future


def _run_pending_snippet(code, request_id, future):
    from ..execution.snippet import run_snippet
    try:
        result = run_snippet(code, StringIO(), request_id=request_id)
        future.set_result(result)
    except BaseException as e:
        logger.error("Snippet callback execution failed: %s", e)
        future.set_exception(e)


def _pfc_executor_callback():
    if _pending_queue.empty():
        return
    executed = 0
    while executed < MAX_BATCH_SIZE:
        try:
            code, request_id, future = _pending_queue.get_nowait()
        except Empty:
            break
        _run_pending_snippet(code, request_id, future)
        executed += 1
    if executed > 0:
        logger.info("Executed %d snippet(s) via callback", executed)


_callback_registered = False


def register_executor_callback(itasca_module, position=EXECUTOR_CALLBACK_POSITION):
    global _callback_registered
    if _callback_registered:
        logger.warning("Executor callback already registered")
        return False
    try:
        import __main__
        __main__._pfc_executor_callback = _pfc_executor_callback
        register_cycle_callback(itasca_module, "_pfc_executor_callback", position)
        _callback_registered = True
        logger.info("Executor callback registered (position=%.1f)", position)
        return True
    except Exception as e:
        logger.error("Failed to register executor callback: %s", e)
        return False


def is_executor_callback_registered():
    return _callback_registered
