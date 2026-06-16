"""Accounting MCP tools — registered on the shared FastMCP instance."""

from src.db import get_conn


def register_tools(mcp):
    """Register all accounting MCP tools."""

    @mcp.tool()
    def add_record(user_id: str, amount: float, category: str, note: str = "") -> str:
        """记账：添加一笔收支记录。amount 为正数表示收入，负数表示支出。"""
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO records (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
                (user_id, amount, category, note),
            )
        return f"已记录: {category} {amount}元"

    @mcp.tool()
    def get_records(user_id: str, limit: int = 20) -> str:
        """查询最近记账记录"""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, amount, category, note, created_at FROM records WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        if not rows:
            return "暂无记录"
        return "\n".join(
            [f"{r['created_at'][:10]} | {r['category']} | {r['amount']}元 | {r['note']}" for r in rows]
        )

    @mcp.tool()
    def get_summary(user_id: str) -> str:
        """获取记账汇总统计"""
        with get_conn() as conn:
            total = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM records WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            by_cat = conn.execute(
                "SELECT category, COALESCE(SUM(amount), 0) FROM records WHERE user_id = ? GROUP BY category",
                (user_id,),
            ).fetchall()
        cats = "\n".join([f"  {c['category']}: {c[1]}元" for c in by_cat])
        return f"总计: {total}元\n分类统计:\n{cats}"

    @mcp.tool()
    def delete_record(user_id: str, record_id: int) -> str:
        """删除指定记账记录"""
        with get_conn() as conn:
            conn.execute("DELETE FROM records WHERE id = ? AND user_id = ?", (record_id, user_id))
        return "已删除"
