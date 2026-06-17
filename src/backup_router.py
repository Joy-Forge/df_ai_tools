"""Backup REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.backup import backup_sqlite, list_backups, restore_backup

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("/create")
def create_backup(name: Optional[str] = None):
    """创建数据库备份"""
    result = backup_sqlite(name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["msg"])
    return result


@router.get("/list")
def get_backups():
    """列出所有备份"""
    return list_backups()


@router.post("/restore/{backup_name}")
def restore(backup_name: str):
    """从备份恢复数据库"""
    result = restore_backup(backup_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["msg"])
    return result
