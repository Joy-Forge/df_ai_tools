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
        """Helper: run an async MCP call synchronously, return text."""
        content, _meta = asyncio.run(mcp_fn(tool_name, args))
        return content[0].text

    def _list(self, mcp):
        """Helper: list tools synchronously."""
        return asyncio.run(mcp.list_tools())

    def test_tools_are_registered(self, mcp):
        """Verify all expected tools are registered."""
        tools = self._list(mcp)
        tool_names = {t.name for t in tools}
        expected = {
            "add_record", "get_records", "get_summary", "delete_record",
            "add_todo", "list_todos", "mark_done", "delete_todo",
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
        from datetime import datetime, timedelta
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        text = self._call(mcp.call_tool, "add_event", {
            "user_id": "u1", "title": "开会", "event_time": future, "remind_before": 10
        })
        assert "已添加" in text

    def test_list_events_tool(self, mcp):
        from datetime import datetime, timedelta
        future = (datetime.now() + timedelta(days=1)).isoformat()
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
