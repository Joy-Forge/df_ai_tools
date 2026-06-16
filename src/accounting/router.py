"""Accounting REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.accounting import service

router = APIRouter(prefix="/api/accounting", tags=["accounting"])


class RecordIn(BaseModel):
    user_id: str
    amount: float
    category: str
    note: Optional[str] = ""


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    note: Optional[str] = None


@router.post("/add")
def add_record(data: RecordIn):
    result = service.add_record(data.user_id, data.amount, data.category, data.note)
    return result


@router.get("/list")
def list_records(user_id: str, limit: int = 50, offset: int = 0):
    records = service.get_records(user_id, limit, offset)
    return records


@router.get("/summary")
def summary(user_id: str):
    return service.get_summary(user_id)


@router.delete("/delete/{record_id}")
def delete_record(record_id: int, user_id: str):
    deleted = service.delete_record(record_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"msg": "已删除"}


@router.put("/update/{record_id}")
def update_record(record_id: int, user_id: str, data: RecordUpdate):
    ok = service.update_record(record_id, user_id,
                                amount=data.amount,
                                category=data.category,
                                note=data.note)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在或未提供修改字段")
    return {"msg": "已更新"}
