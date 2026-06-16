"""Accounting MCP tools — registered on the shared FastMCP instance."""

from src.accounting import service


def register_tools(mcp):
    """Register all accounting MCP tools."""

    @mcp.tool()
    def add_record(user_id: str, amount: float, category: str, note: str = "") -> str:
        """记账：添加一笔收支记录。amount 为正数表示收入，负数表示支出。"""
        result = service.add_record(user_id, amount, category, note)
        return result["msg"]

    @mcp.tool()
    def get_records(user_id: str, limit: int = 20, offset: int = 0) -> str:
        """查询最近记账记录"""
        return service.get_records_text(user_id, limit, offset)

    @mcp.tool()
    def get_summary(user_id: str) -> str:
        """获取记账汇总统计"""
        return service.get_summary_text(user_id)

    @mcp.tool()
    def delete_record(user_id: str, record_id: int) -> str:
        """删除指定记账记录"""
        deleted = service.delete_record(record_id, user_id)
        return "已删除" if deleted else "记录不存在"

    @mcp.tool()
    def update_record(user_id: str, record_id: int,
                      amount: float | None = None,
                      category: str | None = None,
                      note: str | None = None) -> str:
        """更新记账记录。只传需要修改的字段，不传的保持原值。"""
        ok = service.update_record(record_id, user_id, amount, category, note)
        return "已更新" if ok else "记录不存在"
