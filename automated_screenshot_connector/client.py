"""Socket client reporting demo progress to the recording tool.

Protocol (see the tool's docs/AUTOMATION_INTERFACE.md): one JSON object per
newline-terminated UTF-8 line, client -> server only.

Without a port (manual runs) or on any socket failure the client degrades to a
no-op so the demo always keeps playing visually.

As a library this logs through ``logging.getLogger(__name__)`` — route or
silence it via your app's logging configuration.
"""

from __future__ import annotations

import json
import logging
import socket

logger = logging.getLogger(__name__)


class DemoClient:
    """Sends demo lifecycle events to the tool listening on localhost."""

    def __init__(self, port: int | None) -> None:
        self._sock: socket.socket | None = None
        if port is None:
            return
        try:
            self._sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        except OSError as e:
            logger.error("could not connect to demo port %s: %s", port, e)

    def _send(self, payload: dict[str, object]) -> None:
        if self._sock is None:
            return
        try:
            self._sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
        except OSError as e:
            logger.error("demo event send failed, disabling client: %s", e)
            self._sock = None

    def send_started(self, demo_id: int, hwnd: int | None) -> None:
        # The native window handle lets the tool record exactly our window
        payload: dict[str, object] = {"event": "demo_started", "demo": demo_id}
        if hwnd is not None:
            payload["hwnd"] = hwnd
        self._send(payload)

    def send_screenshot(self, name: str) -> None:
        self._send({"event": "screenshot", "name": name})

    def send_ended(self, demo_id: int) -> None:
        self._send({"event": "demo_ended", "demo": demo_id})

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
