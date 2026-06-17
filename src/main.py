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
from src.logger import setup_logging, get_logger
from src.accounting.router import router as accounting_router
from src.todo.router import router as todo_router
from src.calendar.router import router as calendar_router
from src.notify.router import router as notify_router
from src.backup_router import router as backup_router
from src.auth_router import router as auth_router
from src.data_exchange_router import router as data_exchange_router
from src.audit_router import router as audit_router
from src.auth import init_users_table
from src.audit import init_audit_table
from src.calendar.service import check_reminders

# Configure logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_STRUCTURED = os.environ.get("LOG_STRUCTURED", "false").lower() == "true"
LOG_FILE = os.environ.get("LOG_FILE")
setup_logging(level=LOG_LEVEL, structured=LOG_STRUCTURED, log_file=LOG_FILE)

logger = get_logger(__name__)

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
    logger.info("Starting Agent Tools Kit", extra={"action": "startup"})
    init_db()
    init_users_table()
    init_audit_table()
    logger.info("Database initialized", extra={"action": "db_init"})
    
    scheduler.start()
    scheduler.add_job(
        check_reminders, "interval", minutes=1,
        id="reminder_job", max_instances=1, coalesce=True,
        misfire_grace_time=60,
    )
    logger.info("Scheduler started", extra={"action": "scheduler_start"})
    
    # Startup catch-up: run once immediately to compensate for any downtime
    try:
        check_reminders()
        logger.info("Startup reminder catch-up completed", extra={"action": "reminder_catchup"})
    except Exception as e:
        logger.error(f"Startup reminder catch-up failed: {e}", extra={"action": "reminder_catchup", "error": str(e)})
    
    yield
    
    scheduler.shutdown()
    logger.info("Scheduler stopped", extra={"action": "scheduler_stop"})
    logger.info("Agent Tools Kit stopped", extra={"action": "shutdown"})


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

# CORS — configurable via environment; defaults to * for personal NAS/VPS usage
_CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _CORS_ORIGINS.split(",")] if _CORS_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Optional API Key authentication
# ---------------------------------------------------------------------------
# Set env API_KEY to enable.  If unset, all requests pass through.
_API_KEY = os.environ.get("API_KEY", "")

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# Max requests per minute per IP (0 = disabled)
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
_rate_limit_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter based on client IP."""
    if RATE_LIMIT_PER_MINUTE > 0 and request.url.path.startswith("/api/"):
        import time
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old entries
        if client_ip in _rate_limit_store:
            _rate_limit_store[client_ip] = [
                t for t in _rate_limit_store[client_ip] if t > window_start
            ]
        else:
            _rate_limit_store[client_ip] = []

        if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )

        _rate_limit_store[client_ip].append(now)

    return await call_next(request)


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
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "action": "unhandled_exception",
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )

app.include_router(accounting_router)
app.include_router(todo_router)
app.include_router(calendar_router)
app.include_router(notify_router)
app.include_router(backup_router)
app.include_router(auth_router)
app.include_router(data_exchange_router)
app.include_router(audit_router)


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
