"""Todo MCP tools — registered on the shared FastMCP instance."""

from src.todo import service


def register_tools(mcp):
    """Register all todo MCP tools."""

    @mcp.tool()
    def add_todo(user_id: str, content: str, priority: int = 1, due_date: str = "") -> str:
        """添加待办事项。priority: 1=高 2=中 3=低，due_date格式: YYYY-MM-DD"""
        result = service.add_todo(user_id, content, priority, due_date)
        return result["msg"]

    @mcp.tool()
    def list_todos(user_id: str, status: str = "all", limit: int = 30, offset: int = 0) -> str:
        """查询待办列表。status: all/pending/done"""
        return service.list_todos_text(user_id, status, limit, offset)

    @mcp.tool()
    def mark_done(user_id: str, todo_id: int) -> str:
        """标记待办为已完成"""
        ok = service.mark_done(todo_id, user_id)
        return "已完成" if ok else "待办不存在"

    @mcp.tool()
    def mark_undo(user_id: str, todo_id: int) -> str:
        """恢复待办为未完成"""
        ok = service.mark_undo(todo_id, user_id)
        return "已恢复" if ok else "待办不存在"

    @mcp.tool()
    def delete_todo(user_id: str, todo_id: int) -> str:
        """删除待办事项"""
        ok = service.delete_todo(todo_id, user_id)
        return "已删除" if ok else "待办不存在"

    @mcp.tool()
    def edit_todo(user_id: str, todo_id: int,
                  content: str | None = None,
                  priority: int | None = None,
                  due_date: str | None = None) -> str:
        """编辑待办事项。只传需要修改的字段，不传的保持原值。"""
        ok = service.edit_todo(todo_id, user_id, content, priority, due_date)
        return "已更新" if ok else "待办不存在"
