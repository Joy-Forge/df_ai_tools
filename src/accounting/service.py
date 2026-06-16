"""Accounting business logic — shared by REST API and MCP tools."""

import math

from src.db import get_conn


def _check_amount(amount: float) -> str | None:
    """Validate amount. Return error message or None."""
    if math.isnan(amount):
        return "错误: 金额不能为 NaN"
    if math.isinf(amount):
        return "错误: 金额不能为 Infinity"
    return None


def add_record(user_id: str, amount: float, category: str, note: str = "") -> dict:
    """Add a financial record, return {id, msg}."""
    err = _check_amount(amount)
    if err:
        return {"id": -1, "msg": err}
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO records (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
            (user_id, amount, category, note),
        )
        record_id = c.lastrowid
    return {"id": record_id, "msg": f"已记录: {category} {amount}元"}


def get_records(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Return recent records as a list of dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
    return [
        {"id": r["id"], "amount": r["amount"], "category": r["category"],
         "note": r["note"], "time": r["created_at"]}
        for r in rows
    ]


def get_records_text(user_id: str, limit: int = 20, offset: int = 0) -> str:
    """Return recent records as a human-readable string (for MCP)."""
    records = get_records(user_id, limit, offset)
    if not records:
        return "暂无记录"
    return "\n".join(
        [f"{r['time'][:10]} | {r['category']} | {r['amount']}元 | {r['note']}"
         for r in records]
    )


def get_summary(user_id: str) -> dict:
    """Return total and by-category summary."""
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM records WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        by_cat = conn.execute(
            "SELECT category, COALESCE(SUM(amount), 0) FROM records WHERE user_id = ? GROUP BY category",
            (user_id,),
        ).fetchall()
    return {"total": total, "by_category": {c["category"]: c[1] for c in by_cat}}


def get_summary_text(user_id: str) -> str:
    """Return summary as a human-readable string (for MCP)."""
    summary = get_summary(user_id)
    cats = "\n".join(f"  {k}: {v}元" for k, v in summary["by_category"].items())
    return f"总计: {summary['total']}元\n分类统计:\n{cats}"


def delete_record(record_id: int, user_id: str) -> bool:
    """Delete a record, return True if a row was deleted."""
    with get_conn() as conn:
        c = conn.execute(
            "DELETE FROM records WHERE id = ? AND user_id = ?", (record_id, user_id)
        )
        return c.rowcount > 0


def update_record(record_id: int, user_id: str, amount: float | None = None,
                  category: str | None = None, note: str | None = None) -> bool:
    """Update one or more fields of a record. Return True if a row was updated.

    Only non-None fields are updated.  At least one field must be provided.
    """
    fields = []
    params = []
    if amount is not None:
        fields.append("amount = ?")
        params.append(amount)
    if category is not None:
        fields.append("category = ?")
        params.append(category)
    if note is not None:
        fields.append("note = ?")
        params.append(note)
    if not fields:
        return False
    params.extend([record_id, user_id])
    with get_conn() as conn:
        c = conn.execute(
            f"UPDATE records SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        return c.rowcount > 0
