"""Notify REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.notify import service

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
    return service.save_webhook(data.user_id, data.name, data.url, data.method, data.headers)


@router.get("/webhook/list")
def list_webhooks(user_id: str):
    return service.list_webhooks(user_id)


@router.post("/send")
async def send_notify(data: NotifyIn):
    status = await service.send_notification(data.user_id, data.channel, data.target, data.title, data.body)
    return {"status": status}


@router.get("/log")
def get_log(user_id: str, limit: int = 50, offset: int = 0):
    return service.get_notify_log(user_id, limit, offset)
