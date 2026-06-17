"""Tests for MCP tools — invoke tools through the shared FastMCP server."""

import asyncio
import pytest


class TestMCPTools:
    """Test MCP tools are registered and return expected results."""

    @pytest.fixture
    def mcp(self, app, test_db):
        """Get the shared MCP server from main."""
        from src.main import mcp as _mcp
        return _mcp

    def _call(self, mcp_fn, tool_name, args):
        """Helper: run an async MCP call synchronously, return text.

        fastmcp 3.x returns a ToolResult object (with .content/.meta)
        rather than the (content, meta) tuple used by the old SDK.
        """
        result = asyncio.run(mcp_fn(tool_name, args))
        content = result.content
        return content[0].text

    def _list(self, mcp):
        """Helper: list tools synchronously."""
        # fastmcp 3.x returns a list directly; SDK returned list too.
        return asyncio.run(mcp.list_tools())

    def test_tools_are_registered(self, mcp):
        """Verify all expected tools are registered."""
        tools = self._list(mcp)
        tool_names = {t.name for t in tools}
        expected = {
            "add_record", "get_records", "get_summary", "delete_record", "update_record",
            "add_todo", "list_todos", "mark_done", "mark_undo", "delete_todo", "edit_todo",
            "add_event", "list_events", "get_pending_reminders", "delete_event",
            "save_webhook", "list_webhooks", "send_notification", "get_notify_log",
        }
        missing = expected - tool_names
        extra = tool_names - expected
        assert not missing, f"Missing tools: {missing}"
        assert not extra, f"Unexpected tools: {extra}"

    def test_add_record_tool(self, mcp):
        text = self._call(mcp.call_tool, "add_record", {
            "user_id": "u1", "amount": 50.5, "category": "餐饮", "note": "午饭"
        })
        assert "已记录" in text

    def test_get_records_tool(self, mcp):
        self._call(mcp.call_tool, "add_record", {"user_id": "u1", "amount": 10, "category": "测试"})
        text = self._call(mcp.call_tool, "get_records", {"user_id": "u1"})
        assert "测试" in text

    def test_get_records_empty(self, mcp):
        text = self._call(mcp.call_tool, "get_records", {"user_id": "nobody"})
        assert "暂无记录" in text

    def test_get_summary_tool(self, mcp):
        self._call(mcp.call_tool, "add_record", {"user_id": "u1", "amount": 100, "category": "餐饮"})
        self._call(mcp.call_tool, "add_record", {"user_id": "u1", "amount": 50, "category": "交通"})
        text = self._call(mcp.call_tool, "get_summary", {"user_id": "u1"})
        assert "150" in text

    def test_add_todo_tool(self, mcp):
        text = self._call(mcp.call_tool, "add_todo", {
            "user_id": "u1", "content": "买菜", "priority": 1, "due_date": "2026-06-20"
        })
        assert "已添加" in text

    def test_list_todos_tool(self, mcp):
        self._call(mcp.call_tool, "add_todo", {"user_id": "u1", "content": "任务A"})
        text = self._call(mcp.call_tool, "list_todos", {"user_id": "u1", "status": "all"})
        assert "任务A" in text

    def test_add_event_tool(self, mcp):
        from datetime import datetime, timedelta, timezone
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        text = self._call(mcp.call_tool, "add_event", {
            "user_id": "u1", "title": "开会", "event_time": future, "remind_before": 10
        })
        assert "已添加" in text

    def test_list_events_tool(self, mcp):
        from datetime import datetime, timedelta, timezone
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        self._call(mcp.call_tool, "add_event", {"user_id": "u1", "title": "明天", "event_time": future})
        text = self._call(mcp.call_tool, "list_events", {"user_id": "u1"})
        assert "明天" in text

    def test_save_webhook_tool(self, mcp):
        text = self._call(mcp.call_tool, "save_webhook", {
            "user_id": "u1", "name": "bark", "url": "https://bark.example.com"
        })
        assert "已保存" in text

    def test_list_webhooks_tool(self, mcp):
        self._call(mcp.call_tool, "save_webhook", {"user_id": "u1", "name": "bark", "url": "https://bark.example.com"})
        text = self._call(mcp.call_tool, "list_webhooks", {"user_id": "u1"})
        assert "bark" in text

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    # -----------------------------------------------------------------------
    # Missing-tool coverage: delete / done / send / log
    # -----------------------------------------------------------------------

    def test_delete_record_tool(self, mcp):
        self._call(mcp.call_tool, "add_record", {"user_id": "u1", "amount": 99, "category": "测试"})
        text = self._call(mcp.call_tool, "delete_record", {"user_id": "u1", "record_id": 1})
        assert "已删除" in text

    def test_delete_record_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "delete_record", {"user_id": "u1", "record_id": 999})
        assert "不存在" in text

    def test_mark_done_tool(self, mcp):
        self._call(mcp.call_tool, "add_todo", {"user_id": "u1", "content": "测试任务"})
        text = self._call(mcp.call_tool, "mark_done", {"user_id": "u1", "todo_id": 1})
        assert "已完成" in text

    def test_mark_done_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "mark_done", {"user_id": "u1", "todo_id": 999})
        assert "不存在" in text

    def test_mark_undo_tool(self, mcp):
        self._call(mcp.call_tool, "add_todo", {"user_id": "u1", "content": "测试撤销"})
        self._call(mcp.call_tool, "mark_done", {"user_id": "u1", "todo_id": 1})
        text = self._call(mcp.call_tool, "mark_undo", {"user_id": "u1", "todo_id": 1})
        assert "已恢复" in text

    def test_mark_undo_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "mark_undo", {"user_id": "u1", "todo_id": 999})
        assert "不存在" in text

    def test_delete_todo_tool(self, mcp):
        self._call(mcp.call_tool, "add_todo", {"user_id": "u1", "content": "待删除"})
        text = self._call(mcp.call_tool, "delete_todo", {"user_id": "u1", "todo_id": 1})
        assert "已删除" in text

    def test_delete_todo_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "delete_todo", {"user_id": "u1", "todo_id": 999})
        assert "不存在" in text

    def test_delete_event_tool(self, mcp):
        from datetime import datetime, timedelta, timezone
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        self._call(mcp.call_tool, "add_event", {"user_id": "u1", "title": "待删日程", "event_time": future})
        text = self._call(mcp.call_tool, "delete_event", {"user_id": "u1", "event_id": 1})
        assert "已删除" in text

    def test_delete_event_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "delete_event", {"user_id": "u1", "event_id": 999})
        assert "不存在" in text

    def test_get_pending_reminders_tool_empty(self, mcp):
        text = self._call(mcp.call_tool, "get_pending_reminders", {"user_id": "u1"})
        assert "暂无" in text

    def test_get_notify_log_tool(self, mcp):
        self._call(mcp.call_tool, "save_webhook", {"user_id": "u1", "name": "t", "url": "https://ex.com"})
        text = self._call(mcp.call_tool, "get_notify_log", {"user_id": "u1"})
        assert "暂无" in text

    def test_update_record_tool(self, mcp):
        self._call(mcp.call_tool, "add_record", {"user_id": "u1", "amount": 10, "category": "餐饮", "note": "原备注"})
        text = self._call(mcp.call_tool, "update_record", {
            "user_id": "u1", "record_id": 1, "amount": 99, "note": "新备注"
        })
        assert "已更新" in text

    def test_update_record_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "update_record", {"user_id": "u1", "record_id": 999, "amount": 10})
        assert "不存在" in text

    def test_edit_todo_tool(self, mcp):
        self._call(mcp.call_tool, "add_todo", {"user_id": "u1", "content": "原任务", "priority": 3})
        text = self._call(mcp.call_tool, "edit_todo", {
            "user_id": "u1", "todo_id": 1, "content": "新任务", "priority": 1
        })
        assert "已更新" in text

    def test_edit_todo_tool_not_found(self, mcp):
        text = self._call(mcp.call_tool, "edit_todo", {"user_id": "u1", "todo_id": 999, "content": "测试"})
        assert "不存在" in text
