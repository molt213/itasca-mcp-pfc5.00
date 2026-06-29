# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import json
import logging
import threading
import time

from ._compat import http_server, socketserver, queue
from ._compat import HTTPServer, BaseHTTPRequestHandler, ThreadingMixIn
from ._compat import Queue, Empty, Full

from .execution import ScriptRunner
from .tasks import TaskManager
from .handlers import (
    ServerContext,
    handle_execute_task,
    handle_check_task_status,
    handle_list_tasks,
    handle_execute_code,
    handle_interrupt_task,
)

logger = logging.getLogger("itasca-mcp-bridge")
_SSE_KEEPALIVE_S = 15.0
_SSE_QUEUE_MAXSIZE = 256
_MAX_RESPONSE_BYTES = 50 * 2 ** 20
_TRUNCATED_TAIL_CHARS = 10000


def _json_bytes(obj):
    return json.dumps(obj).encode("utf-8")


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class _BridgeRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    @property
    def _bridge(self):
        return self.server.bridge

    def _write_json(self, status, payload_bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload_bytes)))
        self.end_headers()
        try:
            self.wfile.write(payload_bytes)
        except (IOError, OSError):
            pass

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        return self.rfile.read(length) if length > 0 else b""

    def do_POST(self):
        command = self.path.split("?", 1)[0].strip("/")
        raw = self._read_body()
        handler = self._bridge.handlers.get(command)
        if handler is None:
            self._write_json(404, _json_bytes({
                "type": "error", "status": "error",
                "message": "Unknown command: " + command,
                "error": {"code": "unknown_command",
                          "message": "Unknown command: " + command,
                          "details": {"available_commands": self._bridge.public_commands}},
            }))
            return
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (ValueError, UnicodeDecodeError) as exc:
            self._write_json(400, _json_bytes({
                "type": "error", "status": "error",
                "message": "Invalid JSON format",
                "error": {"code": "invalid_json",
                          "message": "Invalid JSON format",
                          "details": {"error": str(exc)}},
            }))
            return
        request_id = data.get("request_id", "unknown")
        summary = self._bridge.summarize_request(command, data)
        logger.info("[%s] >> %s %s", str(request_id)[:8], command, summary)
        t0 = time.time()
        try:
            response = handler(self._bridge.context, data)
        except Exception as exc:
            logger.error("[%s] handler error: %s", str(request_id)[:8], exc)
            self._write_json(500, _json_bytes({
                "type": "error", "request_id": request_id,
                "status": "error", "message": "Internal server error",
                "error": {"code": "internal_error",
                          "message": "Internal server error",
                          "details": {"error": str(exc)}},
            }))
            return
        elapsed_ms = (time.time() - t0) * 1000
        status = response.get("status", "unknown")
        logger.info("[%s] << %s status=%s (%.0fms)", str(request_id)[:8],
                    command, status, elapsed_ms)
        self._write_json(200, self._bridge.serialize_response(response, request_id))

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/events":
            self._serve_sse()
        elif path == "/health":
            self._serve_health()
        else:
            self._write_json(404, _json_bytes({
                "status": "error",
                "error": {"code": "not_found", "message": "Not found"}
            }))

    def _serve_health(self):
        from . import __version__
        payload = {"status": "success", "version": __version__,
                   "runtime_mode": self._bridge.context.runtime_mode}
        self._write_json(200, _json_bytes(payload))

    def _serve_sse(self):
        q = self._bridge.register_sse_client()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=_SSE_KEEPALIVE_S)
                except Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                self.wfile.write(b"data: " + msg.encode("utf-8") + b"\n\n")
                self.wfile.flush()
        except (IOError, OSError, ValueError):
            pass
        finally:
            self._bridge.unregister_sse_client(q)


class ItascaHttpServer(object):
    def __init__(self, main_executor, host="localhost", port=9001,
                 runtime_mode="unknown"):
        self.main_executor = main_executor
        self.host = host
        self.port = port
        self.active_connections = set()
        self._conn_lock = threading.Lock()
        task_manager = TaskManager(on_task_terminal=self._broadcast_task_status)
        self.script_runner = ScriptRunner(main_executor, task_manager)
        self.context = ServerContext(
            task_manager=task_manager, script_runner=self.script_runner,
            main_executor=self.main_executor, runtime_mode=runtime_mode,
        )
        self.handlers = {
            "execute_task": handle_execute_task,
            "check_task_status": handle_check_task_status,
            "list_tasks": handle_list_tasks,
            "interrupt_task": handle_interrupt_task,
            "execute_code": handle_execute_code,
        }
        self.public_commands = sorted(self.handlers)
        self._httpd = _ThreadingHTTPServer((host, port), _BridgeRequestHandler)
        self._httpd.bridge = self

    def register_sse_client(self):
        q = Queue(maxsize=_SSE_QUEUE_MAXSIZE)
        with self._conn_lock:
            self.active_connections.add(q)
            total = len(self.active_connections)
        logger.info("SSE client connected (total=%d)", total)
        return q

    def unregister_sse_client(self, q):
        with self._conn_lock:
            self.active_connections.discard(q)
            total = len(self.active_connections)
        logger.info("SSE client disconnected (total=%d)", total)

    def _broadcast_task_status(self, task_id, status):
        with self._conn_lock:
            if not self.active_connections:
                return
            queues = list(self.active_connections)
        msg = json.dumps({
            "type": "task_status_changed",
            "task_id": task_id, "status": status,
        })
        for q in queues:
            try:
                q.put_nowait(msg)
            except Full:
                pass

    def serialize_response(self, response, request_id="unknown"):
        payload = json.dumps(response)
        if len(payload) > _MAX_RESPONSE_BYTES:
            logger.warning("[%s] Response too large (%d bytes), truncating",
                           str(request_id)[:8], len(payload))
            response = self._truncate_response(response)
            payload = json.dumps(response)
        return payload.encode("utf-8")

    @staticmethod
    def _truncate_response(response):
        data = response.get("data", {})
        if isinstance(data, dict) and "output" in data:
            output = data["output"]
            if isinstance(output, basestring) and len(output) > _TRUNCATED_TAIL_CHARS:
                tail = output[-_TRUNCATED_TAIL_CHARS:]
                nl = tail.find("\n")
                if nl >= 0:
                    tail = tail[nl + 1:]
                omitted = len(output) - len(tail)
                data["output"] = ("... [TRUNCATED: %d earlier chars omitted, "
                    "showing most recent %d chars.]\n" % (omitted, len(tail))) + tail
                response["data"] = data
        return response

    def summarize_request(self, command, data):
        if command == "execute_code":
            code = data.get("code", "")
            preview = code[:80].replace("\n", "\\n")
            if len(code) > 80:
                preview += "..."
            return 'code="' + preview + '"'
        if command == "execute_task":
            return ('script="' + data.get("script_path", "?") +
                    '" desc="' + data.get("description", "")[:60] + '"')
        if command in ("check_task_status", "interrupt_task"):
            return "task_id=" + data.get("task_id", "?")
        if command == "list_tasks":
            return "offset=%d limit=%s" % (data.get("offset", 0),
                                           data.get("limit", "all"))
        return ""

    def serve_forever(self):
        logger.info("HTTP bridge listening on http://%s:%d", self.host, self.port)
        self._httpd.serve_forever()

    def shutdown(self):
        try:
            self._httpd.shutdown()
        except Exception:
            pass
        try:
            self._httpd.server_close()
        except Exception:
            pass
        logger.info("Server shutdown complete")

    def set_runtime_mode(self, runtime_mode):
        self.context.runtime_mode = runtime_mode


def create_server(main_executor, host="localhost", port=9001,
                  runtime_mode="unknown"):
    return ItascaHttpServer(main_executor, host=host, port=port,
                            runtime_mode=runtime_mode)
