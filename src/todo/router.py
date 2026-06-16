"""Todo REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.todo import service

router = APIRouter(prefix="/api/todo", tags=["todo"])


class TodoIn(BaseModel):
    user_id: str
    content: str
    priority: Optional[int] = Field(default=1, ge=1, le=3)
    due_date: Optional[str] = ""


@router.post("/add")
def add_todo(data: TodoIn):
    result = service.add_todo(data.user_id, data.content, data.priority, data.due_date)
    return result


@router.get("/list")
def list_todos(user_id: str, done: Optional[int] = None, limit: int = 50):
    return service.list_todos(user_id, done=done, limit=limit)


@router.post("/done/{todo_id}")
def mark_done(todo_id: int, user_id: str):
    ok = service.mark_done(todo_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="待办不存在")
    return {"msg": "已完成"}


@router.post("/undo/{todo_id}")
def mark_undo(todo_id: int, user_id: str):
    ok = service.mark_undo(todo_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="待办不存在")
    return {"msg": "已恢复未完成"}


@router.delete("/delete/{todo_id}")
def delete_todo(todo_id: int, user_id: str):
    ok = service.delete_todo(todo_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="待办不存在")
    return {"msg": "已删除"}
