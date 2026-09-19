import threading
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient

from db import connection


@pytest.fixture
def db_conn(tmp_path):
    """Point the shared DB connection at a fresh temp file for one test."""
    conn = connection.get_connection(tmp_path / "test.db")
    yield conn
    connection.close_connection()


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """A TestClient wired to a fresh temp DB and the simulator provider."""
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    connection.get_connection(tmp_path / "test.db")

    from main import app

    with TestClient(app) as client:
        yield client
    connection.close_connection()


@pytest.fixture
def live_server(tmp_path, monkeypatch):
    """Run the real app on a real socket.

    httpx's in-process ASGITransport (used by TestClient) buffers an ASGI
    call's entire response and only returns once the app coroutine finishes —
    it can't observe a never-ending SSE stream. A real socket behaves like
    production and supports reading a few lines before disconnecting.
    """
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    connection.get_connection(tmp_path / "test.db")

    from main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)

    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
    connection.close_connection()
