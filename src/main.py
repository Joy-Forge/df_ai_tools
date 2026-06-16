"""Agent Tools Kit — single FastAPI app with REST API + MCP SSE endpoint.

Usage:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db import init_db
from src.accounting.router import router as accounting_router
from src.todo.router import router as todo_router
from src.calendar.router import router as calendar_router
from src.notify.router import router as notify_router

# ---------------------------------------------------------------------------
# MCP — create one shared server, register all tools
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP

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
    init_db()
    scheduler.start()
    from src.calendar.tools import check_reminders
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

app.include_router(accounting_router)
app.include_router(todo_router)
app.include_router(calendar_router)
app.include_router(notify_router)


@app.get("/api/health")
def health():
    """服务健康检查"""
    return {"status": "ok", "tools": len(mcp._tool_manager._tools) if hasattr(mcp, '_tool_manager') else "unknown"}


# ---------------------------------------------------------------------------
# Mount MCP SSE endpoint at /mcp
# ---------------------------------------------------------------------------
try:
    # Mount the MCP SSE Starlette app under /mcp
    mcp_sse_app = mcp.sse_app()
    app.mount("/mcp", mcp_sse_app)
except Exception:
    # Fallback: some fastmcp versions use a different API
    print("WARNING: Could not mount MCP SSE app — try 'python -m src.mcp_entry' for stdio mode")
