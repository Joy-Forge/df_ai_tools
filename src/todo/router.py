"""Todo REST API router."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.db import get_conn

router = APIRouter(prefix="/api/todo", tags=["todo"])


class TodoIn(BaseModel):
    user_id: str
    content: str
    priority: Optional[int] = 1
    due_date: Optional[str] = ""


@router.post("/add")
def add_todo(data: TodoIn):
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO todos (user_id, content, priority, due_date) VALUES (?, ?, ?, ?)",
            (data.user_id, data.content, data.priority, data.due_date),
        )
        rid = c.lastrowid
    return {"id": rid, "msg": f"已添加待办: {data.content}"}


@router.get("/list")
def list_todos(user_id: str, done: Optional[int] = None, limit: int = 50):
    with get_conn() as conn:
        sql = "SELECT id, content, priority, due_date, done, created_at FROM todos WHERE user_id = ?"
        params = [user_id]
        if done is not None:
            sql += " AND done = ?"
            params.append(done)
        sql += " ORDER BY done ASC, priority ASC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    return [
        {
            "id": r["id"],
            "content": r["content"],
            "priority": r["priority"],
            "due_date": r["due_date"],
            "done": bool(r["done"]),
            "time": r["created_at"],
        }
        for r in rows
    ]


@router.post("/done/{todo_id}")
def mark_done(todo_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?", (todo_id, user_id))
    return {"msg": "已完成"}


@router.post("/undo/{todo_id}")
def mark_undo(todo_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE todos SET done = 0 WHERE id = ? AND user_id = ?", (todo_id, user_id))
    return {"msg": "已恢复未完成"}


@router.delete("/delete/{todo_id}")
def delete_todo(todo_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id))
    return {"msg": "已删除"}
