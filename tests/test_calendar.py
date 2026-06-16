"""Tests for Calendar REST API."""

from datetime import datetime, timedelta
import pytest


class TestCalendarAPI:
    def test_add_event(self, client):
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "开会", "event_time": future, "remind_before": 10
        })
        assert resp.status_code == 200
        assert "已添加" in resp.json()["msg"]

    def test_list_events(self, client):
        future1 = (datetime.now() + timedelta(days=1)).isoformat()
        future2 = (datetime.now() + timedelta(days=2)).isoformat()
        far_future = (datetime.now() + timedelta(days=60)).isoformat()
        client.post("/api/calendar/add", json={"user_id": "u1", "title": "明天", "event_time": future1})
        client.post("/api/calendar/add", json={"user_id": "u1", "title": "后天", "event_time": future2})
        client.post("/api/calendar/add", json={"user_id": "u1", "title": "两个月后", "event_time": far_future})
        client.post("/api/calendar/add", json={"user_id": "u2", "title": "别人的", "event_time": future1})
        resp = client.get("/api/calendar/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        resp = client.get("/api/calendar/list", params={"user_id": "u1", "days": 7})
        assert len(resp.json()) == 2

    def test_delete_event(self, client):
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        r = client.post("/api/calendar/add", json={"user_id": "u1", "title": "测试", "event_time": future})
        eid = r.json()["id"]
        resp = client.delete(f"/api/calendar/delete/{eid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        resp = client.get("/api/calendar/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_pending_reminders(self, client):
        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "已过期", "event_time": past, "remind_before": 10
        })
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "未来", "event_time": future, "remind_before": 10
        })
        resp = client.get("/api/calendar/pending_reminders", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "已过期"

    def test_reminders_log(self, client):
        resp = client.get("/api/calendar/reminders_log", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_check_reminders_function(self, app, test_db):
        """Test the check_reminders background function directly."""
        import sqlite3
        from datetime import datetime, timedelta
        from src.calendar.tools import check_reminders

        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO events (user_id, title, event_time, remind_before, reminded) VALUES (?, ?, ?, ?, ?)",
            ("u1", "测试提醒", past, 10, 0)
        )
        conn.commit()
        conn.close()

        import asyncio
        asyncio.run(check_reminders())

        conn = sqlite3.connect(test_db)
        logs = conn.execute("SELECT * FROM reminders_log WHERE user_id = ?", ("u1",)).fetchall()
        conn.close()
        assert len(logs) == 1
        conn = sqlite3.connect(test_db)
        event = conn.execute("SELECT reminded FROM events WHERE user_id = ?", ("u1",)).fetchone()
        conn.close()
        assert event[0] == 1

    def test_event_with_repeat(self, client):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        resp = client.post("/api/calendar/add", json={
            "user_id": "u1", "title": "周会", "event_time": future, "repeat": "weekly"
        })
        assert resp.status_code == 200
        resp = client.get("/api/calendar/list", params={"user_id": "u1"})
        assert resp.json()[0]["repeat"] == "weekly"
