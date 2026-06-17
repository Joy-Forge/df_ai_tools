"""Audit log REST API router."""

from fastapi import APIRouter, Query
from typing import Optional

from src.audit import get_audit_log

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/log")
def audit_log(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    """查询操作审计日志"""
    return get_audit_log(user_id=user_id, action=action, limit=limit, offset=offset)
