"""Unit tests for the demo event socket client."""

import json
import socket
import threading

from automated_screenshot_connector.client import DemoClient


def collect_lines(server: socket.socket, received: list[bytes]) -> threading.Thread:
    def serve() -> None:
        conn, _ = server.accept()
        with conn:
            while chunk := conn.recv(4096):
                received.append(chunk)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread


def test_null_client_without_port_noops() -> None:
    client = DemoClient(port=None)
    client.send_started(1, hwnd=1234)
    client.send_screenshot("x")
    client.send_ended(1)
    client.close()


def test_client_sends_json_lines() -> None:
    server = socket.create_server(("127.0.0.1", 0))
    port = server.getsockname()[1]
    received: list[bytes] = []
    thread = collect_lines(server, received)

    client = DemoClient(port=port)
    client.send_started(1, hwnd=264854)
    client.send_screenshot("basic")
    client.send_ended(1)
    client.close()
    thread.join(timeout=5)
    server.close()

    lines = b"".join(received).decode("utf-8").strip().splitlines()
    events = [json.loads(line) for line in lines]
    assert events == [
        {"event": "demo_started", "demo": 1, "hwnd": 264854},
        {"event": "screenshot", "name": "basic"},
        {"event": "demo_ended", "demo": 1},
    ]


def test_started_without_hwnd_omits_key() -> None:
    server = socket.create_server(("127.0.0.1", 0))
    port = server.getsockname()[1]
    received: list[bytes] = []
    thread = collect_lines(server, received)

    client = DemoClient(port=port)
    client.send_started(1, hwnd=None)
    client.close()
    thread.join(timeout=5)
    server.close()

    event = json.loads(b"".join(received).decode("utf-8").strip())
    assert event == {"event": "demo_started", "demo": 1}


def test_client_survives_unreachable_port() -> None:
    # Nothing listening: client logs and degrades to a no-op instead of raising.
    sock = socket.create_server(("127.0.0.1", 0))
    dead_port = sock.getsockname()[1]
    sock.close()

    client = DemoClient(port=dead_port)
    client.send_started(1, hwnd=1)
    client.close()
