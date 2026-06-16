"""Notify business logic — shared by REST API and MCP tools."""

import json
import requests
from src.db import get_conn


def save_webhook(user_id: str, name: str, url: str,
                 method: str = "POST", headers: str = "{}") -> dict:
    """Save a webhook config, return {id, msg}."""
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO webhooks (user_id, name, url, method, headers) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, url, method, headers),
        )
        wh_id = c.lastrowid
    return {"id": wh_id, "msg": f"Webhook已保存: {name}"}


def list_webhooks(user_id: str) -> list[dict]:
    """Return webhooks as a list of dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, url, method FROM webhooks WHERE user_id = ?", (user_id,)
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "url": r["url"], "method": r["method"]}
            for r in rows]


def list_webhooks_text(user_id: str) -> str:
    """Return webhooks as human-readable text (for MCP)."""
    hooks = list_webhooks(user_id)
    if not hooks:
        return "暂无Webhook"
    return "\n".join(f"[{r['id']}] {r['name']} | {r['method']} {r['url']}"
                     for r in hooks)


def send_notification(user_id: str, channel: str, target: str,
                      title: str, body: str) -> str:
    """Send a notification, return status string."""
    status = "pending"
    try:
        if channel == "webhook":
            with get_conn() as conn:
                webhook = conn.execute(
                    "SELECT url, method, headers FROM webhooks WHERE user_id = ? AND name = ?",
                    (user_id, target),
                ).fetchone()
            if not webhook:
                status = "error: webhook not found"
            else:
                headers = json.loads(webhook["headers"]) if webhook["headers"] else {}
                payload = {"title": title, "body": body}
                if webhook["method"].upper() == "GET":
                    r = requests.get(webhook["url"], params=payload,
                                     headers=headers, timeout=10)
                else:
                    r = requests.post(webhook["url"], json=payload,
                                      headers=headers, timeout=10)
                status = f"sent: {r.status_code}"
        else:
            status = f"unsupported channel: {channel}"
    except requests.RequestException as e:
        status = f"error: {str(e)}"
    except Exception as e:
        status = f"error: {str(e)}"

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notify_log (user_id, channel, target, title, body, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, channel, target, title, body, status),
        )
    return status


def get_notify_log(user_id: str, limit: int = 50) -> list[dict]:
    """Return notification send log."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT channel, target, title, status, created_at FROM notify_log "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        {"channel": r["channel"], "target": r["target"], "title": r["title"],
         "status": r["status"], "time": r["created_at"]}
        for r in rows
    ]


def get_notify_log_text(user_id: str, limit: int = 20) -> str:
    """Return log as human-readable text (for MCP)."""
    entries = get_notify_log(user_id, limit)
    if not entries:
        return "暂无记录"
    return "\n".join(
        f"{r['time'][:16]} | {r['channel']} | {r['title']} | {r['status']}"
        for r in entries
    )
