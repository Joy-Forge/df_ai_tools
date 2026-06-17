"""End-to-end self-test for the MCP Streamable HTTP transport.

This test boots a real uvicorn server in-process and connects to it with
the official MCP Python SDK client (streamablehttp_client). It exercises
the full handshake an Agent would do — initialize, initialized, list
tools, call a tool — and asserts the responses match the expected
contract. Unlike tests/test_mcp.py (which calls tools in-process via
mcp.call_tool), this verifies the wire protocol over HTTP.

Skipped automatically if the `mcp` SDK is not installed (it is a dev
dependency, not a runtime one).
"""

import asyncio
import socket
import threading
import time

import httpx
import pytest
import uvicorn

mcp_sdk = pytest.importorskip("mcp")


# ---------------------------------------------------------------------------
# Real ASGI server fixture (in-process)
# ---------------------------------------------------------------------------

class _ServerThread(threading.Thread):
    """Run a uvicorn.Server in a background thread; shut down cleanly on stop."""

    def __init__(self, app, host: str, port: int):
        super().__init__(daemon=True)
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
            lifespan="on",
        )
        self._server = uvicorn.Server(config)
        # We're not on the main thread; don't touch signal handlers.
        self._server.install_signal_handlers = lambda: None

    def run(self):
        self._server.run()

    def stop(self):
        self._server.should_exit = True
        self.join(timeout=5)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def mcp_server(test_db):
    """Boot the real FastAPI app on a free port; yield base URL; shut down."""
    # Import lazily so test_db fixture runs first (sets DB_PATH)
    from src.main import app

    host = "127.0.0.1"
    port = _free_port()
    thread = _ServerThread(app, host, port)
    thread.start()

    base = f"http://{host}:{port}"
    # Wait for the server to be ready (poll /api/health)
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base}/api/health", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:  # pragma: no cover
        thread.stop()
        pytest.fail(f"MCP test server did not start within 10s on {base}")

    yield f"{base}/mcp"
    thread.stop()


# ---------------------------------------------------------------------------
# Tests — each test runs its own fresh event loop (asyncio.run), drives
# the SDK client to completion, and exits. We do not use pytest-asyncio
# to keep the test dep footprint minimal.
# ---------------------------------------------------------------------------

EXPECTED_TOOLS = {
    # accounting
    "add_record", "get_records", "get_summary",
    "update_record", "delete_record",
    # todo
    "add_todo", "list_todos", "mark_done", "mark_undo",
    "edit_todo", "delete_todo",
    # calendar
    "add_event", "list_events",
    "get_pending_reminders", "delete_event",
    # notify
    "save_webhook", "list_webhooks",
    "send_notification", "get_notify_log",
}


async def _exercise(url, fn):
    """Open an MCP streamable_http client, hand it to fn(session), close it."""
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


def _drive(url, fn):
    return asyncio.run(_exercise(url, fn))


class TestMCPStreamableHTTP:
    """Verify MCP Streamable HTTP endpoint works end-to-end."""

    def test_initialize_returns_server_info(self, mcp_server):
        async def body(session):
            # session is already initialized; just inspect capabilities
            result = await session.initialize()  # idempotent
            assert result.serverInfo.name == "agent-tools-kit"
            assert result.protocolVersion, "protocolVersion must be non-empty"
            assert result.capabilities.tools is not None
        _drive(mcp_server, body)

    def test_list_tools_returns_19(self, mcp_server):
        async def body(session):
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names == EXPECTED_TOOLS, (
                f"tool mismatch — missing={EXPECTED_TOOLS - names}, "
                f"extra={names - EXPECTED_TOOLS}"
            )
        _drive(mcp_server, body)

    def test_call_add_record_then_get(self, mcp_server):
        async def body(session):
            add_result = await session.call_tool(
                "add_record",
                {
                    "user_id": "transport-test",
                    "amount": -12.5,
                    "category": "餐饮",
                    "note": "transport smoke",
                },
            )
            add_text = add_result.content[0].text
            assert "已记录" in add_text

            get_result = await session.call_tool(
                "get_records",
                {"user_id": "transport-test", "limit": 5},
            )
            get_text = get_result.content[0].text
            assert "transport smoke" in get_text
            assert "餐饮" in get_text
        _drive(mcp_server, body)

    def test_get_summary_aggregates(self, mcp_server):
        async def body(session):
            for amount in (10.0, 20.0, 30.0):
                await session.call_tool(
                    "add_record",
                    {
                        "user_id": "sum-test",
                        "amount": amount,
                        "category": "test",
                    },
                )

            result = await session.call_tool(
                "get_summary", {"user_id": "sum-test"}
            )
            text = result.content[0].text
            assert "60" in text, f"expected 60 in summary, got: {text!r}"
        _drive(mcp_server, body)
