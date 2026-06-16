"""Calendar MCP tools + background reminder checker — registered on the shared FastMCP instance."""

from datetime import datetime, timedelta

from src.db import get_conn


def register_tools(mcp):
    """Register all calendar MCP tools."""

    @mcp.tool()
    def add_event(user_id: str, title: str, event_time: str, remind_before: int = 10, repeat: str = "") -> str:
        """添加日历事件。event_time格式: 2026-06-15T09:00:00，remind_before: 提前几分钟提醒，repeat: daily/weekly/monthly/空"""
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO events (user_id, title, event_time, remind_before, repeat) VALUES (?, ?, ?, ?, ?)",
                (user_id, title, event_time, remind_before, repeat),
            )
        return f"已添加日程: {title} @ {event_time}"

    @mcp.tool()
    def list_events(user_id: str, days: int = 30) -> str:
        """查询未来日程"""
        with get_conn() as conn:
            since = (datetime.now() - timedelta(days=1)).isoformat()
            until = (datetime.now() + timedelta(days=days)).isoformat()
            rows = conn.execute(
                "SELECT id, title, event_time, repeat FROM events WHERE user_id = ? AND event_time BETWEEN ? AND ? ORDER BY event_time",
                (user_id, since, until),
            ).fetchall()
        if not rows:
            return "暂无日程"
        lines = []
        for r in rows:
            repeat = f" [{r['repeat']}]" if r["repeat"] else ""
            lines.append(f"[{r['id']}] {r['event_time'][:16]} | {r['title']}{repeat}")
        return "\n".join(lines)

    @mcp.tool()
    def get_pending_reminders(user_id: str) -> str:
        """获取当前待提醒的事项"""
        with get_conn() as conn:
            now = datetime.now().isoformat()
            rows = conn.execute(
                "SELECT id, title, event_time FROM events WHERE user_id = ? AND event_time <= ? AND reminded = 0 ORDER BY event_time",
                (user_id, now),
            ).fetchall()
        if not rows:
            return "暂无待提醒事项"
        return "\n".join([f"⏰ {r['title']} @ {r['event_time']}" for r in rows])

    @mcp.tool()
    def delete_event(user_id: str, event_id: int) -> str:
        """删除日程"""
        with get_conn() as conn:
            conn.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        return "已删除"


async def check_reminders():
    """Background task: check for events that need reminding (called by scheduler)."""
    with get_conn() as conn:
        now = datetime.now()
        rows = conn.execute(
            "SELECT id, user_id, title, event_time, remind_before FROM events WHERE reminded = 0"
        ).fetchall()
        for r in rows:
            try:
                event_time = datetime.fromisoformat(r["event_time"].replace("Z", "+00:00").replace("+00:00", ""))
            except Exception:
                continue
            remind_time = event_time - timedelta(minutes=r["remind_before"])
            if now >= remind_time:
                conn.execute(
                    "INSERT INTO reminders_log (event_id, user_id, title) VALUES (?, ?, ?)",
                    (r["id"], r["user_id"], r["title"]),
                )
                conn.execute("UPDATE events SET reminded = 1 WHERE id = ?", (r["id"],))
                conn.commit()
                print(f"[REMINDER] {r['user_id']}: {r['title']} @ {event_time}")
