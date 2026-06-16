"""Edge cases and boundary condition tests for all modules."""

from datetime import datetime, timedelta
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
        assert resp.status_code == 200

    def test_mark_done_nonexistent(self, client):
        resp = client.post("/api/todo/done/99999", params={"user_id": "u1"})
        assert resp.status_code == 200

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/todo/delete/99999", params={"user_id": "u1"})
        assert resp.status_code == 200


class TestCalendarEdgeCases:
    def test_past_event_listed(self, client):
        recent_past = (datetime.now() - timedelta(hours=1)).isoformat()
        client.post("/api/calendar/add", json={"user_id": "u1", "title": "一小时前", "event_time": recent_past})
        resp = client.get("/api/calendar/list", params={"user_id": "u1"})
        assert len(resp.json()) >= 1

    def test_remind_before_zero(self, client):
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "测试", "event_time": future, "remind_before": 0
        })
        assert resp.status_code == 200

    def test_invalid_event_time_format(self, client):
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "测试", "event_time": "not-a-date"
        })
        assert resp.status_code == 200


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
