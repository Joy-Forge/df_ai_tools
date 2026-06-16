"""Calendar business logic — shared by REST API and MCP tools.

All datetimes are stored as naive-UTC so comparisons work regardless
of the server's local timezone.  Both _now() and _parse_dt() return
naive-UTC (tzinfo stripped after conversion).
"""

from datetime import datetime, timedelta, timezone
import logging

from src.db import get_conn

logger = logging.getLogger(__name__)

# ISO format used for storage and exchange
ISO_FMT = "%Y-%m-%dT%H:%M:%S"


def _parse_dt(s: str) -> datetime | None:
    """Parse an ISO datetime string to a naive-UTC datetime, or None on failure.

    If the input carries a timezone offset it is converted to UTC and the
    tzinfo is stripped.  If it is already naive it is assumed to be UTC.
    This keeps all internal comparisons consistent (see _now).
    """
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        # naive input is assumed to be UTC
        return dt
    except (ValueError, TypeError):
        return None


def _now() -> datetime:
    """Current time as naive-UTC datetime (compatible with SQLite storage).

    Must be UTC-nave (same convention as _parse_dt) so comparisons
    in check_reminders, list_events, and get_pending_reminders are correct
    regardless of the server's local timezone.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def add_event(user_id: str, title: str, event_time: str,
              remind_before: int = 10, repeat: str = "") -> dict:
    """Add a calendar event, return {id, msg}."""
    if remind_before < 0:
        return {"id": -1, "msg": "错误: remind_before 不能为负值"}
    dt = _parse_dt(event_time)
    if dt is None:
        return {"id": -1, "msg": "错误: 日期格式无效，请使用 ISO 格式如 2026-06-15T09:00:00"}
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO events (user_id, title, event_time, remind_before, repeat) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, dt.strftime(ISO_FMT), remind_before, repeat),
        )
        eid = c.lastrowid
    return {"id": eid, "msg": f"已添加日程: {title} @ {event_time}"}


def list_events(user_id: str, days: int = 30, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return upcoming events as a list of dicts."""
    since = (_now() - timedelta(days=1)).strftime(ISO_FMT)
    until = (_now() + timedelta(days=days)).strftime(ISO_FMT)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, event_time, remind_before, repeat, reminded "
            "FROM events WHERE user_id = ? AND event_time BETWEEN ? AND ? "
            "ORDER BY event_time LIMIT ? OFFSET ?",
            (user_id, since, until, limit, offset),
        ).fetchall()
    return [
        {"id": r["id"], "title": r["title"], "event_time": r["event_time"],
         "remind_before": r["remind_before"], "repeat": r["repeat"],
         "reminded": bool(r["reminded"])}
        for r in rows
    ]


def list_events_text(user_id: str, days: int = 30, offset: int = 0) -> str:
    """Return upcoming events as human-readable text (for MCP)."""
    events = list_events(user_id, days, limit=999, offset=offset)
    if not events:
        return "暂无日程"
    lines = []
    for r in events:
        repeat = f" [{r['repeat']}]" if r["repeat"] else ""
        lines.append(f"[{r['id']}] {r['event_time'][:16]} | {r['title']}{repeat}")
    return "\n".join(lines)


def delete_event(event_id: int, user_id: str) -> bool:
    """Delete an event. Return True if a row was deleted."""
    with get_conn() as conn:
        c = conn.execute(
            "DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id)
        )
        return c.rowcount > 0


def get_pending_reminders(user_id: str) -> list[dict]:
    """Return events that are due but not yet reminded."""
    now = _now().strftime(ISO_FMT)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, event_time FROM events "
            "WHERE user_id = ? AND event_time <= ? AND reminded = 0 "
            "ORDER BY event_time",
            (user_id, now),
        ).fetchall()
    return [{"id": r["id"], "title": r["title"], "event_time": r["event_time"]}
            for r in rows]


def get_pending_reminders_text(user_id: str) -> str:
    """Return pending reminders as text (for MCP)."""
    items = get_pending_reminders(user_id)
    if not items:
        return "暂无待提醒事项"
    return "\n".join(f"⏰ {r['title']} @ {r['event_time']}" for r in items)


def get_reminders_log(user_id: str, limit: int = 50) -> list[dict]:
    """Return sent-reminder log entries."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT title, sent_at FROM reminders_log WHERE user_id = ? ORDER BY sent_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"title": r["title"], "sent_at": r["sent_at"]} for r in rows]


def _advance_repeat(event_time: str, repeat: str) -> str | None:
    """Advance event_time by one repeat interval.

    Returns the new event_time as ISO string, or None if repeat is empty.
    """
    if not repeat:
        return None
    dt = _parse_dt(event_time)
    if dt is None:
        return None

    intervals = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
        "monthly": timedelta(days=30),
    }
    delta = intervals.get(repeat)
    if delta is None:
        return None  # unknown repeat pattern, treat as one-off

    return (dt + delta).strftime(ISO_FMT)


def check_reminders():
    """Background task: check for events that need reminding (called by scheduler).

    All comparisons use naive-UTC (see _now / _parse_dt).
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_id, title, event_time, remind_before, repeat FROM events WHERE reminded = 0"
        ).fetchall()

        now = _now()
        for r in rows:
            event_dt = _parse_dt(r["event_time"])
            if event_dt is None:
                continue

            remind_time = event_dt - timedelta(minutes=r["remind_before"])
            if now >= remind_time:
                conn.execute(
                    "INSERT INTO reminders_log (event_id, user_id, title) VALUES (?, ?, ?)",
                    (r["id"], r["user_id"], r["title"]),
                )

                next_time = _advance_repeat(r["event_time"], r["repeat"])
                if next_time is not None:
                    conn.execute(
                        "UPDATE events SET reminded = 0, event_time = ? WHERE id = ?",
                        (next_time, r["id"]),
                    )
                else:
                    conn.execute("UPDATE events SET reminded = 1 WHERE id = ?", (r["id"],))

                conn.commit()
                logger.info("REMINDER %s: %s @ %s", r["user_id"], r["title"], event_dt)
