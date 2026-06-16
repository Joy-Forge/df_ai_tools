"""Accounting REST API router."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.db import get_conn

router = APIRouter(prefix="/api/accounting", tags=["accounting"])


class RecordIn(BaseModel):
    user_id: str
    amount: float
    category: str
    note: Optional[str] = ""


@router.post("/add")
def add_record(data: RecordIn):
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO records (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
            (data.user_id, data.amount, data.category, data.note),
        )
        rid = c.lastrowid
    return {"id": rid, "msg": f"已记录: {data.category} {data.amount}元"}


@router.get("/list")
def list_records(user_id: str, limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        {"id": r["id"], "amount": r["amount"], "category": r["category"], "note": r["note"], "time": r["created_at"]}
        for r in rows
    ]


@router.get("/summary")
def summary(user_id: str):
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM records WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        by_cat = conn.execute(
            "SELECT category, COALESCE(SUM(amount), 0) FROM records WHERE user_id = ? GROUP BY category",
            (user_id,),
        ).fetchall()
    return {"total": total, "by_category": {c["category"]: c[1] for c in by_cat}}


@router.delete("/delete/{record_id}")
def delete_record(record_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM records WHERE id = ? AND user_id = ?", (record_id, user_id))
    return {"msg": "已删除"}
