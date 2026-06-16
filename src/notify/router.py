"""Notify REST API router."""

import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.db import get_conn
import requests

router = APIRouter(prefix="/api/notify", tags=["notify"])


class NotifyIn(BaseModel):
    user_id: str
    channel: str
    target: str
    title: str
    body: str


class WebhookConfig(BaseModel):
    user_id: str
    name: str
    url: str
    method: str = "POST"
    headers: Optional[str] = "{}"


@router.post("/webhook/save")
def save_webhook(data: WebhookConfig):
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO webhooks (user_id, name, url, method, headers) VALUES (?, ?, ?, ?, ?)",
            (data.user_id, data.name, data.url, data.method, data.headers),
        )
        rid = c.lastrowid
    return {"id": rid, "msg": f"Webhook已保存: {data.name}"}


@router.get("/webhook/list")
def list_webhooks(user_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, url, method FROM webhooks WHERE user_id = ?", (user_id,)
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "url": r["url"], "method": r["method"]} for r in rows]


@router.post("/send")
def send_notify(data: NotifyIn):
    status = "pending"
    try:
        if data.channel == "webhook":
            with get_conn() as conn:
                webhook = conn.execute(
                    "SELECT url, method, headers FROM webhooks WHERE user_id = ? AND name = ?",
                    (data.user_id, data.target),
                ).fetchone()
            if not webhook:
                status = "error: webhook not found"
            else:
                headers = json.loads(webhook["headers"]) if webhook["headers"] else {}
                payload = {"title": data.title, "body": data.body}
                if webhook["method"].upper() == "GET":
                    r = requests.get(webhook["url"], params=payload, headers=headers, timeout=10)
                else:
                    r = requests.post(webhook["url"], json=payload, headers=headers, timeout=10)
                status = f"sent: {r.status_code}"
        else:
            status = f"unsupported channel: {data.channel}"
    except Exception as e:
        status = f"error: {str(e)}"

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notify_log (user_id, channel, target, title, body, status) VALUES (?, ?, ?, ?, ?, ?)",
            (data.user_id, data.channel, data.target, data.title, data.body, status),
        )
    return {"status": status}


@router.get("/log")
def get_log(user_id: str, limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT channel, target, title, status, created_at FROM notify_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        {"channel": r["channel"], "target": r["target"], "title": r["title"], "status": r["status"], "time": r["created_at"]}
        for r in rows
    ]
