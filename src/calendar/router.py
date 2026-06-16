"""Calendar REST API router."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from src.db import get_conn

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class EventIn(BaseModel):
    user_id: str
    title: str
    event_time: str
    remind_before: int = 10
    repeat: Optional[str] = ""


@router.post("/add")
def add_event(data: EventIn):
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO events (user_id, title, event_time, remind_before, repeat) VALUES (?, ?, ?, ?, ?)",
            (data.user_id, data.title, data.event_time, data.remind_before, data.repeat),
        )
        rid = c.lastrowid
    return {"id": rid, "msg": f"已添加日程: {data.title} @ {data.event_time}"}


@router.get("/list")
def list_events(user_id: str, days: int = 30, limit: int = 50):
    with get_conn() as conn:
        since = (datetime.now() - timedelta(days=1)).isoformat()
        until = (datetime.now() + timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT id, title, event_time, remind_before, repeat, reminded FROM events WHERE user_id = ? AND event_time BETWEEN ? AND ? ORDER BY event_time LIMIT ?",
            (user_id, since, until, limit),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "event_time": r["event_time"],
            "remind_before": r["remind_before"],
            "repeat": r["repeat"],
            "reminded": bool(r["reminded"]),
        }
        for r in rows
    ]


@router.delete("/delete/{event_id}")
def delete_event(event_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
    return {"msg": "已删除"}


@router.get("/pending_reminders")
def pending_reminders(user_id: str):
    with get_conn() as conn:
        now = datetime.now().isoformat()
        rows = conn.execute(
            "SELECT id, title, event_time FROM events WHERE user_id = ? AND event_time <= ? AND reminded = 0 ORDER BY event_time",
            (user_id, now),
        ).fetchall()
    return [{"id": r["id"], "title": r["title"], "event_time": r["event_time"]} for r in rows]


@router.get("/reminders_log")
def reminders_log(user_id: str, limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT title, sent_at FROM reminders_log WHERE user_id = ? ORDER BY sent_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"title": r["title"], "sent_at": r["sent_at"]} for r in rows]
