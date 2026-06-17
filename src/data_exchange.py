"""Data import/export module — JSON/CSV export and JSON import."""

import csv
import io
import json
from datetime import datetime

from src.db import get_conn
from src.logger import get_logger

logger = get_logger(__name__)


def export_user_data(user_id: str) -> dict:
    """Export all data for a user as a JSON-serializable dict.

    Returns:
        dict with keys: accounting, todos, events, webhooks, exported_at
    """
    with get_conn() as conn:
        # Accounting records
        records = conn.execute(
            "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()

        # Todos
        todos = conn.execute(
            "SELECT id, content, priority, due_date, done, created_at FROM todos WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()

        # Calendar events
        events = conn.execute(
            "SELECT id, title, event_time, remind_before, repeat, reminded, created_at FROM events WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()

        # Webhooks
        webhooks = conn.execute(
            "SELECT id, name, url, method, headers, created_at FROM webhooks WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()

    data = {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "accounting": [
            {"id": r["id"], "amount": r["amount"], "category": r["category"],
             "note": r["note"], "created_at": r["created_at"]}
            for r in records
        ],
        "todos": [
            {"id": r["id"], "content": r["content"], "priority": r["priority"],
             "due_date": r["due_date"], "done": bool(r["done"]), "created_at": r["created_at"]}
            for r in todos
        ],
        "events": [
            {"id": r["id"], "title": r["title"], "event_time": r["event_time"],
             "remind_before": r["remind_before"], "repeat": r["repeat"],
             "reminded": bool(r["reminded"]), "created_at": r["created_at"]}
            for r in events
        ],
        "webhooks": [
            {"id": r["id"], "name": r["name"], "url": r["url"],
             "method": r["method"], "headers": r["headers"], "created_at": r["created_at"]}
            for r in webhooks
        ],
    }

    logger.info(
        f"Data exported for user {user_id}: "
        f"{len(data['accounting'])} records, {len(data['todos'])} todos, "
        f"{len(data['events'])} events, {len(data['webhooks'])} webhooks",
        extra={"action": "data_export", "user_id": user_id},
    )
    return data


def export_csv(user_id: str, table: str) -> str:
    """Export a single table as CSV string.

    Args:
        user_id: User ID
        table: One of 'accounting', 'todos', 'events', 'webhooks'

    Returns:
        CSV string
    """
    table_queries = {
        "accounting": "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ?",
        "todos": "SELECT id, content, priority, due_date, done, created_at FROM todos WHERE user_id = ?",
        "events": "SELECT id, title, event_time, remind_before, repeat, reminded, created_at FROM events WHERE user_id = ?",
        "webhooks": "SELECT id, name, url, method, headers, created_at FROM webhooks WHERE user_id = ?",
    }

    if table not in table_queries:
        return ""

    with get_conn() as conn:
        rows = conn.execute(table_queries[table], (user_id,)).fetchall()

    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys())  # Header
    for row in rows:
        writer.writerow(list(row))

    return output.getvalue()


def import_user_data(user_id: str, data: dict) -> dict:
    """Import data for a user from a JSON dict (as exported by export_user_data).

    Args:
        user_id: Target user ID
        data: Dict with keys: accounting, todos, events, webhooks

    Returns:
        dict with keys: success, msg, counts
    """
    counts = {"accounting": 0, "todos": 0, "events": 0, "webhooks": 0}

    try:
        with get_conn() as conn:
            # Import accounting records
            for item in data.get("accounting", []):
                conn.execute(
                    "INSERT INTO records (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
                    (user_id, item["amount"], item["category"], item.get("note", "")),
                )
                counts["accounting"] += 1

            # Import todos
            for item in data.get("todos", []):
                conn.execute(
                    "INSERT INTO todos (user_id, content, priority, due_date, done) VALUES (?, ?, ?, ?, ?)",
                    (user_id, item["content"], item.get("priority", 1),
                     item.get("due_date", ""), int(item.get("done", False))),
                )
                counts["todos"] += 1

            # Import events
            for item in data.get("events", []):
                conn.execute(
                    "INSERT INTO events (user_id, title, event_time, remind_before, repeat) VALUES (?, ?, ?, ?, ?)",
                    (user_id, item["title"], item["event_time"],
                     item.get("remind_before", 10), item.get("repeat", "")),
                )
                counts["events"] += 1

            # Import webhooks
            for item in data.get("webhooks", []):
                conn.execute(
                    "INSERT INTO webhooks (user_id, name, url, method, headers) VALUES (?, ?, ?, ?, ?)",
                    (user_id, item["name"], item["url"],
                     item.get("method", "POST"), item.get("headers", "{}")),
                )
                counts["webhooks"] += 1

            conn.commit()

        logger.info(
            f"Data imported for user {user_id}: {counts}",
            extra={"action": "data_import", "user_id": user_id},
        )
        return {
            "success": True,
            "msg": f"导入成功: {counts['accounting']}条记账, {counts['todos']}个待办, {counts['events']}个日程, {counts['webhooks']}个webhook",
            "counts": counts,
        }
    except Exception as e:
        logger.error(f"Import failed: {e}", extra={"action": "data_import_failed", "error": str(e)})
        return {"success": False, "msg": f"导入失败: {e}", "counts": counts}
