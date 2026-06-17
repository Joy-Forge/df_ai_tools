"""Audit log module — stores operation audit trail in the database."""

import json
from datetime import datetime
from typing import Optional, Any

from src.db import get_conn
from src.logger import get_logger

logger = get_logger(__name__)


def init_audit_table():
    """Create audit_log table if it doesn't exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                status TEXT DEFAULT 'success'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        conn.commit()


def log_audit(
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: Any = None,
    details: dict | None = None,
    ip_address: str | None = None,
    status: str = "success",
):
    """Write an audit log entry to the database.

    Args:
        action: Action performed (e.g., 'add_record', 'delete_todo')
        user_id: User performing the action
        resource_type: Type of resource (e.g., 'accounting', 'todo')
        resource_id: ID of the resource
        details: Additional details as a dict
        ip_address: Client IP address
        status: 'success' or 'error'
    """
    try:
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO audit_log (user_id, action, resource_type, resource_id, details, ip_address, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, action, resource_type, str(resource_id) if resource_id is not None else None,
                 details_json, ip_address, status),
            )
            conn.commit()
    except Exception as e:
        # Don't let audit log failures break the main flow
        logger.warning(f"Failed to write audit log: {e}")


def get_audit_log(
    user_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Query audit log entries.

    Args:
        user_id: Filter by user ID (optional)
        action: Filter by action (optional)
        limit: Max entries to return
        offset: Pagination offset

    Returns:
        List of audit log entries as dicts
    """
    query = "SELECT id, timestamp, user_id, action, resource_type, resource_id, details, ip_address, status FROM audit_log"
    conditions = []
    params = []

    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    if action:
        conditions.append("action = ?")
        params.append(action)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": r["id"],
            "timestamp": r["timestamp"],
            "user_id": r["user_id"],
            "action": r["action"],
            "resource_type": r["resource_type"],
            "resource_id": r["resource_id"],
            "details": json.loads(r["details"]) if r["details"] else None,
            "ip_address": r["ip_address"],
            "status": r["status"],
        }
        for r in rows
    ]
