"""Edge cases and boundary condition tests for all modules."""

from datetime import datetime, timedelta, timezone
import pytest


class TestAccountingEdgeCases:
    def test_zero_amount(self, client):
        resp = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 0, "category": "测试"})
        assert resp.status_code == 200

    def test_large_amount(self, client):
        resp = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 99999999.99, "category": "测试"})
        assert resp.status_code == 200

    def test_special_characters_in_category(self, client):
        resp = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 10, "category": "餐饮/外卖"})
        assert resp.status_code == 200

    def test_empty_note(self, client):
        resp = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 10, "category": "测试", "note": ""})
        assert resp.status_code == 200

    def test_summary_negative_totals(self, client):
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 100, "category": "收入"})
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": -200, "category": "支出"})
        resp = client.get("/api/accounting/summary", params={"user_id": "u1"})
        assert resp.json()["total"] == -100

    def test_nan_amount_rejected(self, client):
        """NaN 作为金额应该被拒绝（通过 MCP 直接调用可能传入）"""
        from src.accounting import service
        result = service.add_record("u1", float("nan"), "测试")
        assert "错误" in result["msg"] or result["id"] == -1

    def test_inf_amount_rejected(self, client):
        """Infinity 作为金额应该被拒绝"""
        from src.accounting import service
        result = service.add_record("u1", float("inf"), "测试")
        assert "错误" in result["msg"] or result["id"] == -1


class TestTodoEdgeCases:
    def test_empty_content(self, client):
        resp = client.post("/api/todo/add", json={"user_id": "u1", "content": ""})
        assert resp.status_code == 200

    def test_long_content(self, client):
        long_text = "任务" * 1000
        resp = client.post("/api/todo/add", json={"user_id": "u1", "content": long_text})
        assert resp.status_code == 200

    def test_invalid_priority(self, client):
        resp = client.post("/api/todo/add", json={"user_id": "u1", "content": "测试", "priority": 99})
        assert resp.status_code == 422  # priority out of range

    def test_mark_done_nonexistent(self, client):
        resp = client.post("/api/todo/done/99999", params={"user_id": "u1"})
        assert resp.status_code == 404  # not found

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/todo/delete/99999", params={"user_id": "u1"})
        assert resp.status_code == 404  # not found


class TestCalendarEdgeCases:
    def test_past_event_listed(self, client):
        recent_past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        client.post("/api/calendar/add", json={"user_id": "u1", "title": "一小时前", "event_time": recent_past})
        resp = client.get("/api/calendar/list", params={"user_id": "u1"})
        assert len(resp.json()) >= 1

    def test_remind_before_zero(self, client):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "测试", "event_time": future, "remind_before": 0
        })
        assert resp.status_code == 200

    def test_invalid_event_time_format(self, client):
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "测试", "event_time": "not-a-date"
        })
        assert resp.status_code == 400  # invalid format

    def test_negative_remind_before(self, client):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "测试", "event_time": future, "remind_before": -5
        })
        assert resp.status_code == 400  # negative remind_before not allowed


class TestNotifyEdgeCases:
    def test_empty_webhook_name(self, client):
        resp = client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "", "url": "https://example.com"
        })
        assert resp.status_code == 200

    def test_invalid_url(self, client):
        resp = client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "bad", "url": "not-a-url"
        })
        assert resp.status_code == 200

    def test_empty_title_body(self, client):
        resp = client.post("/api/notify/send", json={
            "user_id": "u1", "channel": "webhook", "target": "test",
            "title": "", "body": ""
        })
        assert resp.status_code == 200


class TestDbIndexes:
    """DB 索引存在性验证 — 确保高频查询列有索引支撑。"""

    @pytest.fixture(autouse=True)
    def _setup(self, test_db):
        import sqlite3
        self.conn = sqlite3.connect(test_db)
        yield
        self.conn.close()

    def _index_exists(self, idx_name: str) -> bool:
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (idx_name,)
        ).fetchall()
        return len(rows) > 0

    def test_idx_records_user_id(self):
        assert self._index_exists("idx_records_user_id")

    def test_idx_todos_user_id(self):
        assert self._index_exists("idx_todos_user_id")

    def test_idx_events_user_id_time(self):
        assert self._index_exists("idx_events_user_id_time")
