"""Calendar MCP tools — registered on the shared FastMCP instance."""

from src.calendar import service


def register_tools(mcp):
    """Register all calendar MCP tools."""

    @mcp.tool()
    def add_event(user_id: str, title: str, event_time: str,
                  remind_before: int = 10, repeat: str = "") -> str:
        """添加日历事件。event_time格式: 2026-06-15T09:00:00，remind_before: 提前几分钟提醒，repeat: daily/weekly/monthly/空"""
        result = service.add_event(user_id, title, event_time, remind_before, repeat)
        return result["msg"]

    @mcp.tool()
    def list_events(user_id: str, days: int = 30) -> str:
        """查询未来日程"""
        return service.list_events_text(user_id, days)

    @mcp.tool()
    def get_pending_reminders(user_id: str) -> str:
        """获取当前待提醒的事项"""
        return service.get_pending_reminders_text(user_id)

    @mcp.tool()
    def delete_event(user_id: str, event_id: int) -> str:
        """删除日程"""
        ok = service.delete_event(event_id, user_id)
        return "已删除" if ok else "日程不存在"
