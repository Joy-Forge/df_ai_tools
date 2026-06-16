"""Calendar REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.calendar import service

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class EventIn(BaseModel):
    user_id: str
    title: str
    event_time: str
    remind_before: int = 10
    repeat: Optional[str] = ""


@router.post("/add")
def add_event(data: EventIn):
    result = service.add_event(
        data.user_id, data.title, data.event_time,
        data.remind_before, data.repeat,
    )
    if result["id"] == -1:
        raise HTTPException(status_code=400, detail=result["msg"])
    return result


@router.get("/list")
def list_events(user_id: str, days: int = 30, limit: int = 50):
    return service.list_events(user_id, days, limit)


@router.delete("/delete/{event_id}")
def delete_event(event_id: int, user_id: str):
    ok = service.delete_event(event_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="日程不存在")
    return {"msg": "已删除"}


@router.get("/pending_reminders")
def pending_reminders(user_id: str):
    return service.get_pending_reminders(user_id)


@router.get("/reminders_log")
def reminders_log(user_id: str, limit: int = 50):
    return service.get_reminders_log(user_id, limit)
