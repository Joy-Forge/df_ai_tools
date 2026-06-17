"""Data import/export REST API router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional

from src.data_exchange import export_user_data, export_csv, import_user_data

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/export/{user_id}")
def export_json(user_id: str):
    """导出用户所有数据（JSON）"""
    return export_user_data(user_id)


@router.get("/export/{user_id}/csv/{table}")
def export_csv_endpoint(user_id: str, table: str):
    """导出单个表为 CSV（accounting/todos/events/webhooks）"""
    csv_data = export_csv(user_id, table)
    if not csv_data:
        raise HTTPException(status_code=404, detail=f"表 {table} 无数据或不存在")
    return PlainTextResponse(csv_data, media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={user_id}_{table}.csv"})


class ImportIn(BaseModel):
    user_id: str
    data: dict


@router.post("/import")
def import_json(body: ImportIn):
    """导入用户数据（JSON 格式，需与导出格式一致）"""
    result = import_user_data(body.user_id, body.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["msg"])
    return result
