"""Todo business logic — shared by REST API and MCP tools."""

from src.db import get_conn


def add_todo(user_id: str, content: str, priority: int = 1, due_date: str = "") -> dict:
    """Add a todo, return {id, msg}."""
    with get_conn() as conn:
        c = conn.execute(
            "INSERT INTO todos (user_id, content, priority, due_date) VALUES (?, ?, ?, ?)",
            (user_id, content, priority, due_date),
        )
        todo_id = c.lastrowid
    return {"id": todo_id, "msg": f"已添加待办: {content}"}


def list_todos(user_id: str, done: int | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return todos as a list of dicts."""
    with get_conn() as conn:
        sql = "SELECT id, content, priority, due_date, done, created_at FROM todos WHERE user_id = ?"
        params = [user_id]
        if done is not None:
            sql += " AND done = ?"
            params.append(done)
        sql += " ORDER BY done ASC, priority ASC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(sql, params).fetchall()
    return [
        {"id": r["id"], "content": r["content"], "priority": r["priority"],
         "due_date": r["due_date"], "done": bool(r["done"]), "time": r["created_at"]}
        for r in rows
    ]


def list_todos_text(user_id: str, status: str = "all", limit: int = 30, offset: int = 0) -> str:
    """Return todos as human-readable text (for MCP)."""
    done_map = {"all": None, "pending": 0, "done": 1}
    done_filter = done_map.get(status)
    todos = list_todos(user_id, done=done_filter, limit=limit, offset=offset)
    if not todos:
        return "暂无待办"
    lines = []
    for r in todos:
        flag = "✓" if r["done"] else "○"
        due = f" (截止:{r['due_date']})" if r["due_date"] else ""
        pri = {1: "🔴", 2: "🟡", 3: "🟢"}.get(r["priority"], "⚪")
        lines.append(f"{flag} [{r['id']}] {pri} {r['content']}{due}")
    return "\n".join(lines)


def mark_done(todo_id: int, user_id: str) -> bool:
    """Mark a todo as done. Return True if a row was updated."""
    with get_conn() as conn:
        c = conn.execute(
            "UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?", (todo_id, user_id)
        )
        return c.rowcount > 0


def mark_undo(todo_id: int, user_id: str) -> bool:
    """Mark a todo as not done. Return True if a row was updated."""
    with get_conn() as conn:
        c = conn.execute(
            "UPDATE todos SET done = 0 WHERE id = ? AND user_id = ?", (todo_id, user_id)
        )
        return c.rowcount > 0


def delete_todo(todo_id: int, user_id: str) -> bool:
    """Delete a todo. Return True if a row was deleted."""
    with get_conn() as conn:
        c = conn.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)
        )
        return c.rowcount > 0


def edit_todo(todo_id: int, user_id: str, content: str | None = None,
              priority: int | None = None, due_date: str | None = None) -> bool:
    """Update one or more fields of a todo. Return True if a row was updated."""
    fields = []
    params = []
    if content is not None:
        fields.append("content = ?")
        params.append(content)
    if priority is not None:
        fields.append("priority = ?")
        params.append(priority)
    if due_date is not None:
        fields.append("due_date = ?")
        params.append(due_date)
    if not fields:
        return False
    params.extend([todo_id, user_id])
    with get_conn() as conn:
        c = conn.execute(
            f"UPDATE todos SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        return c.rowcount > 0
