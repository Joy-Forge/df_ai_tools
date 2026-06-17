"""Agent Tools Kit — single FastAPI app with REST API + MCP SSE endpoint.

Usage:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db import init_db
from src.accounting.router import router as accounting_router
from src.todo.router import router as todo_router
from src.calendar.router import router as calendar_router
from src.notify.router import router as notify_router
from src.calendar.service import check_reminders

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP — create one shared server, register all tools
# ---------------------------------------------------------------------------
# Prefer the standalone fastmcp 3.x package over the bundled one inside
# the official MCP SDK. fastmcp 3.x provides http_app(path=...) which is
# the documented ASGI integration pattern; the SDK's streamable_http_app
# hard-codes the path to "/mcp" and would double-prefix if mounted.
try:
    from fastmcp import FastMCP  # type: ignore[no-redef]
    from fastmcp.utilities.lifespan import combine_lifespans  # type: ignore[import-not-found]
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore[no-redef]
    from mcp.server.fastmcp.utilities.lifespan import combine_lifespans  # type: ignore[no-redef]

mcp = FastMCP("agent-tools-kit")

from src.accounting.tools import register_tools as register_accounting
from src.todo.tools import register_tools as register_todo
from src.calendar.tools import register_tools as register_calendar
from src.notify.tools import register_tools as register_notify

register_accounting(mcp)
register_todo(mcp)
register_calendar(mcp)
register_notify(mcp)

# Build the MCP ASGI app at the root path. We then mount it under /mcp below,
# so the final endpoint becomes POST/GET /mcp. http_app(path="/") is the
# fastmcp 3.x recommended pattern (see https://gofastmcp.com/integrations/fastapi).
# Streamable HTTP transport (MCP protocol 2025-06-18). Replaces the legacy
# SSE transport; modern MCP clients (Claude Desktop, picoclaw, hermes, …)
# default to this. The endpoint supports both POST (send JSON-RPC) and GET
# (open SSE stream) per the spec.
mcp_app = mcp.http_app(path="/")

# ---------------------------------------------------------------------------
# Scheduler for calendar reminders
# ---------------------------------------------------------------------------
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """FastAPI lifespan — init DB, start reminder scheduler."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    scheduler.start()
    scheduler.add_job(check_reminders, "interval", minutes=1, id="reminder_job")
    yield
    scheduler.shutdown()


# Combine app lifespan with MCP session-manager lifespan — both are required
# for the MCP endpoint to initialize sessions correctly.
app_lifespan_combined = combine_lifespans(app_lifespan, mcp_app.lifespan)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Agent Tools Kit",
    description="4合1工具包：记账、待办、日历提醒、通知桥接 — 通过 REST API 和 MCP 协议供 Agent 调用",
    version="2.1.0",
    lifespan=app_lifespan_combined,
)

# CORS — allow all origins for personal NAS/VPS usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Optional API Key authentication
# ---------------------------------------------------------------------------
# Set env API_KEY to enable.  If unset, all requests pass through.
_API_KEY = os.environ.get("API_KEY", "")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if _API_KEY:
        # Allow health checks and MCP endpoint without auth
        path = request.url.path
        if not path.startswith("/api/health") and not path.startswith("/mcp"):
            api_key = request.headers.get("X-API-Key", "")
            if api_key != _API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid API Key"},
                )
    return await call_next(request)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a JSON error (no internal details leaked)."""
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )

app.include_router(accounting_router)
app.include_router(todo_router)
app.include_router(calendar_router)
app.include_router(notify_router)


@app.get("/api/health")
async def health():
    """服务健康检查"""
    tool_count = "unknown"
    try:
        tools = await mcp.list_tools()
        tool_count = len(tools)
    except Exception:
        pass
    return {"status": "ok", "tools": tool_count}


# ---------------------------------------------------------------------------
# Mount MCP Streamable HTTP endpoint at /mcp
# ---------------------------------------------------------------------------
# mcp_app was created earlier with path="/" so that the FastMCP routes
# sit at the root of the mounted sub-app; combined with app.mount("/mcp", ...)
# the final public URL is POST/GET /mcp. The session manager relies on
# lifespan=combine_lifespans(...) above being wired in.
app.mount("/mcp", mcp_app)
