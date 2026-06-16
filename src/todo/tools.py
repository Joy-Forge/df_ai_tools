"""Todo MCP tools — registered on the shared FastMCP instance."""

from src.db import get_conn


def register_tools(mcp):
    """Register all todo MCP tools."""

    @mcp.tool()
    def add_todo(user_id: str, content: str, priority: int = 2, due_date: str = "") -> str:
        """添加待办事项。priority: 1=高 2=中 3=低，due_date格式: YYYY-MM-DD"""
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO todos (user_id, content, priority, due_date) VALUES (?, ?, ?, ?)",
                (user_id, content, priority, due_date),
            )
        return f"已添加待办: {content}"

    @mcp.tool()
    def list_todos(user_id: str, status: str = "all", limit: int = 30) -> str:
        """查询待办列表。status: all/pending/done"""
        done_map = {"all": None, "pending": 0, "done": 1}
        with get_conn() as conn:
            sql = "SELECT id, content, priority, due_date, done, created_at FROM todos WHERE user_id = ?"
            params = [user_id]
            if done_map[status] is not None:
                sql += " AND done = ?"
                params.append(done_map[status])
            sql += " ORDER BY done ASC, priority ASC, created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        if not rows:
            return "暂无待办"
        lines = []
        for r in rows:
            flag = "✓" if r["done"] else "○"
            due = f" (截止:{r['due_date']})" if r["due_date"] else ""
            pri = {1: "🔴", 2: "🟡", 3: "🟢"}.get(r["priority"], "⚪")
            lines.append(f"{flag} [{r['id']}] {pri} {r['content']}{due}")
        return "\n".join(lines)

    @mcp.tool()
    def mark_done(user_id: str, todo_id: int) -> str:
        """标记待办为已完成"""
        with get_conn() as conn:
            conn.execute("UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?", (todo_id, user_id))
        return "已完成"

    @mcp.tool()
    def delete_todo(user_id: str, todo_id: int) -> str:
        """删除待办事项"""
        with get_conn() as conn:
            conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id))
        return "已删除"
