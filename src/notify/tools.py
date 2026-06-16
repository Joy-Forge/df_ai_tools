"""Notify MCP tools — registered on the shared FastMCP instance."""

import json
import requests
from src.db import get_conn


def register_tools(mcp):
    """Register all notify MCP tools."""

    @mcp.tool()
    def save_webhook(user_id: str, name: str, url: str, method: str = "POST", headers: str = "{}") -> str:
        """保存一个Webhook配置，用于后续发送通知"""
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO webhooks (user_id, name, url, method, headers) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, url, method, headers),
            )
        return f"Webhook已保存: {name}"

    @mcp.tool()
    def list_webhooks(user_id: str) -> str:
        """列出已保存的Webhook"""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, name, url, method FROM webhooks WHERE user_id = ?", (user_id,)
            ).fetchall()
        if not rows:
            return "暂无Webhook"
        return "\n".join([f"[{r['id']}] {r['name']} | {r['method']} {r['url']}" for r in rows])

    @mcp.tool()
    def send_notification(user_id: str, channel: str, target: str, title: str, body: str) -> str:
        """发送通知。channel: webhook, target: webhook名称"""
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
                        r = requests.get(webhook["url"], params=payload, headers=headers, timeout=10)
                    else:
                        r = requests.post(webhook["url"], json=payload, headers=headers, timeout=10)
                    status = f"sent: {r.status_code}"
            else:
                status = f"unsupported channel: {channel}"
        except Exception as e:
            status = f"error: {str(e)}"

        with get_conn() as conn:
            conn.execute(
                "INSERT INTO notify_log (user_id, channel, target, title, body, status) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, channel, target, title, body, status),
            )
        return status

    @mcp.tool()
    def get_notify_log(user_id: str, limit: int = 20) -> str:
        """查询通知发送记录"""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT channel, target, title, status, created_at FROM notify_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        if not rows:
            return "暂无记录"
        return "\n".join(
            [f"{r['created_at'][:16]} | {r['channel']} | {r['title']} | {r['status']}" for r in rows]
        )
