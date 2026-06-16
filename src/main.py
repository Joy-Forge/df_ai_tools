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
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP  # type: ignore[no-redef]

mcp = FastMCP("agent-tools-kit")

from src.accounting.tools import register_tools as register_accounting
from src.todo.tools import register_tools as register_todo
from src.calendar.tools import register_tools as register_calendar
from src.notify.tools import register_tools as register_notify

register_accounting(mcp)
register_todo(mcp)
register_calendar(mcp)
register_notify(mcp)

# ---------------------------------------------------------------------------
# Scheduler for calendar reminders
# ---------------------------------------------------------------------------
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan — init DB, start reminder scheduler."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    scheduler.start()
    scheduler.add_job(check_reminders, "interval", minutes=1, id="reminder_job")
    yield
    scheduler.shutdown()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Agent Tools Kit",
    description="4合1工具包：记账、待办、日历提醒、通知桥接 — 通过 REST API 和 MCP 协议供 Agent 调用",
    version="2.0.0",
    lifespan=lifespan,
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
        # Allow health checks and MCP SSE without auth
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
# Mount MCP SSE endpoint at /mcp
# ---------------------------------------------------------------------------
try:
    mcp_sse_app = mcp.sse_app()
    app.mount("/mcp", mcp_sse_app)
except Exception:
    logger.warning("Could not mount MCP SSE app — try 'python -m src.mcp_entry' for stdio mode")
