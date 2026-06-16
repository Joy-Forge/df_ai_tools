"""Accounting business logic — shared by REST API and MCP tools."""

from src.db import get_conn


def add_record(user_id: str, amount: float, category: str, note: str = "") -> dict:
    """Add a financial record, return {id, msg}."""
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO records (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
            (user_id, amount, category, note),
        )
        record_id = c.lastrowid
    return {"id": record_id, "msg": f"已记录: {category} {amount}元"}


def get_records(user_id: str, limit: int = 20) -> list[dict]:
    """Return recent records as a list of dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        {"id": r["id"], "amount": r["amount"], "category": r["category"],
         "note": r["note"], "time": r["created_at"]}
        for r in rows
    ]


def get_records_text(user_id: str, limit: int = 20) -> str:
    """Return recent records as a human-readable string (for MCP)."""
    records = get_records(user_id, limit)
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
