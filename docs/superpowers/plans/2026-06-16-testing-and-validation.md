# Agent Tools Kit - Testing & Validation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate all 4 services work correctly, write comprehensive unit tests, and ensure agent MCP integration is functional.

**Architecture:** Each service (accounting, todo, calendar, notify) has a FastAPI REST API (main.py) and an MCP server wrapper (mcp_server.py). We test the REST APIs with FastAPI's TestClient, and mock HTTP calls to test MCP servers. All tests use SQLite in-memory databases.

**Tech Stack:** pytest, httpx (TestClient), unittest.mock, sqlite3

---

## File Structure

```
agent_tools_kit/
├── tests/
│   ├── conftest.py              # Shared fixtures (tmp DB, test clients)
│   ├── test_accounting.py       # Accounting service tests
│   ├── test_todo.py             # Todo service tests
│   ├── test_calendar.py         # Calendar service tests
│   ├── test_notify.py           # Notify service tests
│   └── test_mcp_servers.py      # MCP server integration tests
├── accounting/
│   ├── main.py
│   └── mcp_server.py
├── todo/
│   ├── main.py
│   └── mcp_server.py
├── calendar/
│   ├── main.py
│   └── mcp_server.py
├── notify/
│   ├── main.py
│   └── mcp_server.py
└── requirements-test.txt        # Test dependencies
```

---

## Task 1: Project Setup & Shared Fixtures

**Files:**
- Create: `tests/conftest.py`
- Create: `requirements-test.txt`

- [ ] **Step 1: Create test requirements file**

```
pytest>=7.0
httpx>=0.24
pytest-cov>=4.0
```

- [ ] **Step 2: Create shared test fixtures**

```python
# tests/conftest.py
import sys
import os
import pytest
from pathlib import Path

# Add project root to path so we can import service modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def accounting_app():
    """Import and configure accounting app with temp DB."""
    os.chdir(PROJECT_ROOT / "accounting")
    from main import app, DB
    import sqlite3
    # Override DB path for tests
    test_db = "test_accounting.db"
    import main as m
    original_db = m.DB
    m.DB = test_db
    # Re-init with test DB
    conn = sqlite3.connect(test_db)
    conn.execute("DROP TABLE IF EXISTS records")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    yield app, test_db
    m.DB = original_db
    if os.path.exists(test_db):
        os.remove(test_db)
    os.chdir(PROJECT_ROOT)

@pytest.fixture
def todo_app():
    """Import and configure todo app with temp DB."""
    os.chdir(PROJECT_ROOT / "todo")
    from main import app
    import main as m
    import sqlite3
    test_db = "test_todo.db"
    original_db = m.DB
    m.DB = test_db
    conn = sqlite3.connect(test_db)
    conn.execute("DROP TABLE IF EXISTS todos")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            due_date TEXT,
            done INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    yield app, test_db
    m.DB = original_db
    if os.path.exists(test_db):
        os.remove(test_db)
    os.chdir(PROJECT_ROOT)

@pytest.fixture
def calendar_app():
    """Import and configure calendar app with temp DB."""
    os.chdir(PROJECT_ROOT / "calendar")
    from main import app
    import main as m
    import sqlite3
    test_db = "test_calendar.db"
    original_db = m.DB
    m.DB = test_db
    conn = sqlite3.connect(test_db)
    conn.execute("DROP TABLE IF EXISTS events")
    conn.execute("DROP TABLE IF EXISTS reminders_log")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            event_time TIMESTAMP NOT NULL,
            remind_before INTEGER DEFAULT 10,
            repeat TEXT,
            reminded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id TEXT,
            title TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    yield app, test_db
    m.DB = original_db
    if os.path.exists(test_db):
        os.remove(test_db)
    os.chdir(PROJECT_ROOT)

@pytest.fixture
def notify_app():
    """Import and configure notify app with temp DB."""
    os.chdir(PROJECT_ROOT / "notify")
    from main import app
    import main as m
    import sqlite3
    test_db = "test_notify.db"
    original_db = m.DB
    m.DB = test_db
    conn = sqlite3.connect(test_db)
    conn.execute("DROP TABLE IF EXISTS webhooks")
    conn.execute("DROP TABLE IF EXISTS notify_log")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            method TEXT DEFAULT 'POST',
            headers TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notify_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            channel TEXT,
            target TEXT,
            title TEXT,
            body TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    yield app, test_db
    m.DB = original_db
    if os.path.exists(test_db):
        os.remove(test_db)
    os.chdir(PROJECT_ROOT)
```

- [ ] **Step 3: Run pytest to verify setup**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/conftest.py -v`
Expected: No errors (collection may show 0 tests, that's fine)

---

## Task 2: Accounting Service Tests

**Files:**
- Create: `tests/test_accounting.py`

- [ ] **Step 1: Write accounting API tests**

```python
# tests/test_accounting.py
from fastapi.testclient import TestClient
import pytest

class TestAccountingAPI:
    def setup_method(self):
        """Reset DB before each test."""
        import sqlite3, os
        if os.path.exists("test_accounting.db"):
            os.remove("test_accounting.db")

    def test_add_record(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={
            "user_id": "u1", "amount": 50.5, "category": "餐饮", "note": "午饭"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "已记录" in data["msg"]

    def test_add_record_negative_amount(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={
            "user_id": "u1", "amount": -100, "category": "交通", "note": "打车"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "已记录" in data["msg"]

    def test_list_records(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        client.post("/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        client.post("/add", json={"user_id": "u1", "amount": 20, "category": "测试"})
        client.post("/add", json={"user_id": "u2", "amount": 30, "category": "测试"})
        resp = client.get("/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(r["amount"] in [10, 20] for r in data)

    def test_list_records_empty(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.get("/list", params={"user_id": "nobody"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_records_limit(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        for i in range(5):
            client.post("/add", json={"user_id": "u1", "amount": i, "category": "测试"})
        resp = client.get("/list", params={"user_id": "u1", "limit": 2})
        assert len(resp.json()) == 2

    def test_summary(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        client.post("/add", json={"user_id": "u1", "amount": 100, "category": "餐饮"})
        client.post("/add", json={"user_id": "u1", "amount": 200, "category": "交通"})
        client.post("/add", json={"user_id": "u1", "amount": 50, "category": "餐饮"})
        resp = client.get("/summary", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 350
        assert data["by_category"]["餐饮"] == 150
        assert data["by_category"]["交通"] == 200

    def test_summary_empty(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.get("/summary", params={"user_id": "nobody"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["by_category"] == {}

    def test_delete_record(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        rid = r.json()["id"]
        resp = client.delete(f"/delete/{rid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        # Verify deleted
        resp = client.get("/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_delete_record_wrong_user(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        rid = r.json()["id"]
        resp = client.delete(f"/delete/{rid}", params={"user_id": "u2"})
        assert resp.status_code == 200
        # Should still exist for u1
        resp = client.get("/list", params={"user_id": "u1"})
        assert len(resp.json()) == 1
```

- [ ] **Step 2: Run accounting tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_accounting.py -v`
Expected: All tests PASS

---

## Task 3: Todo Service Tests

**Files:**
- Create: `tests/test_todo.py`

- [ ] **Step 1: Write todo API tests**

```python
# tests/test_todo.py
from fastapi.testclient import TestClient
import pytest

class TestTodoAPI:
    def setup_method(self):
        import sqlite3, os
        if os.path.exists("test_todo.db"):
            os.remove("test_todo.db")

    def test_add_todo(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.post("/add", json={
            "user_id": "u1", "content": "买菜", "priority": 1, "due_date": "2026-06-20"
        })
        assert resp.status_code == 200
        assert "已添加" in resp.json()["msg"]

    def test_add_todo_minimal(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.post("/add", json={
            "user_id": "u1", "content": "简单任务"
        })
        assert resp.status_code == 200

    def test_list_todos(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        client.post("/add", json={"user_id": "u1", "content": "任务A"})
        client.post("/add", json={"user_id": "u1", "content": "任务B"})
        client.post("/add", json={"user_id": "u2", "content": "任务C"})
        resp = client.get("/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_todos_filter_done(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        r1 = client.post("/add", json={"user_id": "u1", "content": "A"})
        r2 = client.post("/add", json={"user_id": "u1", "content": "B"})
        client.post(f"/done/{r1.json()['id']}", params={"user_id": "u1"})
        # List pending only
        resp = client.get("/list", params={"user_id": "u1", "done": 0})
        assert len(resp.json()) == 1
        assert resp.json()[0]["content"] == "B"
        # List done only
        resp = client.get("/list", params={"user_id": "u1", "done": 1})
        assert len(resp.json()) == 1
        assert resp.json()[0]["content"] == "A"

    def test_mark_done(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.post(f"/done/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert "已完成" in resp.json()["msg"]
        # Verify
        resp = client.get("/list", params={"user_id": "u1", "done": 1})
        assert len(resp.json()) == 1

    def test_mark_undo(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        client.post(f"/done/{tid}", params={"user_id": "u1"})
        resp = client.post(f"/undo/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert "恢复" in resp.json()["msg"]
        resp = client.get("/list", params={"user_id": "u1", "done": 0})
        assert len(resp.json()) == 1

    def test_delete_todo(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.delete(f"/delete/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        resp = client.get("/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_delete_todo_wrong_user(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        r = client.post("/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.delete(f"/delete/{tid}", params={"user_id": "u2"})
        assert resp.status_code == 200
        resp = client.get("/list", params={"user_id": "u1"})
        assert len(resp.json()) == 1

    def test_list_ordering(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        client.post("/add", json={"user_id": "u1", "content": "低优先", "priority": 3})
        client.post("/add", json={"user_id": "u1", "content": "高优先", "priority": 1})
        client.post("/add", json={"user_id": "u1", "content": "中优先", "priority": 2})
        resp = client.get("/list", params={"user_id": "u1"})
        data = resp.json()
        # Should be sorted by priority ASC
        assert data[0]["content"] == "高优先"
        assert data[1]["content"] == "中优先"
        assert data[2]["content"] == "低优先"
```

- [ ] **Step 2: Run todo tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_todo.py -v`
Expected: All tests PASS

---

## Task 4: Calendar Service Tests

**Files:**
- Create: `tests/test_calendar.py`

- [ ] **Step 1: Write calendar API tests**

```python
# tests/test_calendar.py
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest

class TestCalendarAPI:
    def setup_method(self):
        import sqlite3, os
        if os.path.exists("test_calendar.db"):
            os.remove("test_calendar.db")

    def test_add_event(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        resp = client.post("/add", json={
            "user_id": "u1", "title": "开会", "event_time": future, "remind_before": 10
        })
        assert resp.status_code == 200
        assert "已添加" in resp.json()["msg"]

    def test_list_events(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        future1 = (datetime.now() + timedelta(days=1)).isoformat()
        future2 = (datetime.now() + timedelta(days=2)).isoformat()
        far_future = (datetime.now() + timedelta(days=60)).isoformat()
        client.post("/add", json={"user_id": "u1", "title": "明天", "event_time": future1})
        client.post("/add", json={"user_id": "u1", "title": "后天", "event_time": future2})
        client.post("/add", json={"user_id": "u1", "title": "两个月后", "event_time": far_future})
        client.post("/add", json={"user_id": "u2", "title": "别人的", "event_time": future1})
        # Default 30 days
        resp = client.get("/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # 7 days
        resp = client.get("/list", params={"user_id": "u1", "days": 7})
        assert len(resp.json()) == 2

    def test_delete_event(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        r = client.post("/add", json={"user_id": "u1", "title": "测试", "event_time": future})
        eid = r.json()["id"]
        resp = client.delete(f"/delete/{eid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        resp = client.get("/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_pending_reminders(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        # Past event (should be pending)
        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        client.post("/add", json={"user_id": "u1", "title": "已过期", "event_time": past, "remind_before": 10})
        # Future event (should NOT be pending)
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        client.post("/add", json={"user_id": "u1", "title": "未来", "event_time": future, "remind_before": 10})
        resp = client.get("/pending_reminders", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "已过期"

    def test_reminders_log(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        resp = client.get("/reminders_log", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_check_reminders_function(self, calendar_app):
        """Test the check_reminders background job logic."""
        import main as m
        app, db = calendar_app
        import sqlite3
        # Insert a past event
        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        conn = sqlite3.connect(db)
        conn.execute(
            "INSERT INTO events (user_id, title, event_time, remind_before, reminded) VALUES (?, ?, ?, ?, ?)",
            ("u1", "测试提醒", past, 10, 0)
        )
        conn.commit()
        conn.close()
        # Run check_reminders
        import asyncio
        asyncio.get_event_loop().run_until_complete(m.check_reminders())
        # Verify reminder was logged
        conn = sqlite3.connect(db)
        logs = conn.execute("SELECT * FROM reminders_log WHERE user_id = ?", ("u1",)).fetchall()
        conn.close()
        assert len(logs) == 1
        # Verify event marked as reminded
        conn = sqlite3.connect(db)
        event = conn.execute("SELECT reminded FROM events WHERE user_id = ?", ("u1",)).fetchone()
        conn.close()
        assert event[0] == 1

    def test_event_with_repeat(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        future = (datetime.now() + timedelta(days=1)).isoformat()
        resp = client.post("/add", json={
            "user_id": "u1", "title": "周会", "event_time": future, "repeat": "weekly"
        })
        assert resp.status_code == 200
        resp = client.get("/list", params={"user_id": "u1"})
        assert resp.json()[0]["repeat"] == "weekly"
```

- [ ] **Step 2: Run calendar tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_calendar.py -v`
Expected: All tests PASS

---

## Task 5: Notify Service Tests

**Files:**
- Create: `tests/test_notify.py`

- [ ] **Step 1: Write notify API tests**

```python
# tests/test_notify.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

class TestNotifyAPI:
    def setup_method(self):
        import sqlite3, os
        if os.path.exists("test_notify.db"):
            os.remove("test_notify.db")

    def test_save_webhook(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/webhook/save", json={
            "user_id": "u1", "name": "bark", "url": "https://bark.example.com/push"
        })
        assert resp.status_code == 200
        assert "已保存" in resp.json()["msg"]

    def test_list_webhooks(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "bark", "url": "https://bark.example.com"
        })
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "wechat", "url": "https://qyapi.example.com"
        })
        client.post("/webhook/save", json={
            "user_id": "u2", "name": "other", "url": "https://other.example.com"
        })
        resp = client.get("/webhook/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_send_notification_webhook(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "test", "url": "https://httpbin.org/post"
        })
        with patch("main.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_req.post.return_value = mock_resp
            resp = client.post("/send", json={
                "user_id": "u1", "channel": "webhook", "target": "test",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "sent: 200" in data["status"]

    def test_send_notification_webhook_not_found(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/send", json={
            "user_id": "u1", "channel": "webhook", "target": "不存在",
            "title": "测试", "body": "内容"
        })
        assert resp.status_code == 200
        assert "error" in resp.json()["status"]

    def test_send_notification_unsupported_channel(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/send", json={
            "user_id": "u1", "channel": "email", "target": "test@example.com",
            "title": "测试", "body": "内容"
        })
        assert resp.status_code == 200
        assert "unsupported" in resp.json()["status"]

    def test_notify_log(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "test", "url": "https://example.com"
        })
        with patch("main.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_req.post.return_value = mock_resp
            client.post("/send", json={
                "user_id": "u1", "channel": "webhook", "target": "test",
                "title": "测试", "body": "内容"
            })
        resp = client.get("/log", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "测试"

    def test_webhook_with_custom_headers(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "custom",
            "url": "https://example.com", "headers": '{"Authorization": "Bearer token123"}'
        })
        with patch("main.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_req.post.return_value = mock_resp
            resp = client.post("/send", json={
                "user_id": "u1", "channel": "webhook", "target": "custom",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            # Verify headers were passed
            call_kwargs = mock_req.post.call_args
            assert "Authorization" in call_kwargs[1]["headers"]

    def test_webhook_get_method(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        client.post("/webhook/save", json={
            "user_id": "u1", "name": "gethook",
            "url": "https://example.com", "method": "GET"
        })
        with patch("main.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_req.get.return_value = mock_resp
            resp = client.post("/send", json={
                "user_id": "u1", "channel": "webhook", "target": "gethook",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            mock_req.get.assert_called_once()
```

- [ ] **Step 2: Run notify tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_notify.py -v`
Expected: All tests PASS

---

## Task 6: MCP Server Tests

**Files:**
- Create: `tests/test_mcp_servers.py`

- [ ] **Step 1: Write MCP server tests**

```python
# tests/test_mcp_servers.py
"""Test MCP server wrappers by mocking HTTP calls to the REST APIs."""
from unittest.mock import patch, MagicMock
import pytest

class TestAccountingMCP:
    @patch("accounting.mcp_server.requests")
    def test_add_record(self, mock_requests):
        from accounting.mcp_server import add_record
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已记录: 餐饮 50.5元"}
        mock_requests.post.return_value = mock_resp
        result = add_record("u1", 50.5, "餐饮", "午饭")
        assert "已记录" in result
        mock_requests.post.assert_called_once()

    @patch("accounting.mcp_server.requests")
    def test_get_records(self, mock_requests):
        from accounting.mcp_server import get_records
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"time": "2026-06-15 10:00:00", "category": "餐饮", "amount": 50, "note": "午饭"}
        ]
        mock_requests.get.return_value = mock_resp
        result = get_records("u1")
        assert "餐饮" in result
        assert "50" in result

    @patch("accounting.mcp_server.requests")
    def test_get_records_empty(self, mock_requests):
        from accounting.mcp_server import get_records
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_requests.get.return_value = mock_resp
        result = get_records("u1")
        assert "暂无记录" in result

    @patch("accounting.mcp_server.requests")
    def test_get_summary(self, mock_requests):
        from accounting.mcp_server import get_summary
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total": 100, "by_category": {"餐饮": 60, "交通": 40}}
        mock_requests.get.return_value = mock_resp
        result = get_summary("u1")
        assert "100" in result
        assert "餐饮" in result

    @patch("accounting.mcp_server.requests")
    def test_delete_record(self, mock_requests):
        from accounting.mcp_server import delete_record
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已删除"}
        mock_requests.delete.return_value = mock_resp
        result = delete_record("u1", 1)
        assert "已删除" in result


class TestTodoMCP:
    @patch("todo.mcp_server.requests")
    def test_add_todo(self, mock_requests):
        from todo.mcp_server import add_todo
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已添加待办: 买菜"}
        mock_requests.post.return_value = mock_resp
        result = add_todo("u1", "买菜", 1, "2026-06-20")
        assert "已添加" in result

    @patch("todo.mcp_server.requests")
    def test_list_todos(self, mock_requests):
        from todo.mcp_server import list_todos
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"id": 1, "content": "买菜", "priority": 1, "due_date": "2026-06-20", "done": False}
        ]
        mock_requests.get.return_value = mock_resp
        result = list_todos("u1", "pending")
        assert "买菜" in result
        assert "○" in result  # Not done

    @patch("todo.mcp_server.requests")
    def test_list_todos_empty(self, mock_requests):
        from todo.mcp_server import list_todos
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_requests.get.return_value = mock_resp
        result = list_todos("u1")
        assert "暂无待办" in result

    @patch("todo.mcp_server.requests")
    def test_mark_done(self, mock_requests):
        from todo.mcp_server import mark_done
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已完成"}
        mock_requests.post.return_value = mock_resp
        result = mark_done("u1", 1)
        assert "已完成" in result

    @patch("todo.mcp_server.requests")
    def test_delete_todo(self, mock_requests):
        from todo.mcp_server import delete_todo
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已删除"}
        mock_requests.delete.return_value = mock_resp
        result = delete_todo("u1", 1)
        assert "已删除" in result


class TestCalendarMCP:
    @patch("calendar.mcp_server.requests")
    def test_add_event(self, mock_requests):
        from calendar.mcp_server import add_event
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已添加日程: 开会 @ 2026-06-16T09:00:00"}
        mock_requests.post.return_value = mock_resp
        result = add_event("u1", "开会", "2026-06-16T09:00:00")
        assert "已添加" in result

    @patch("calendar.mcp_server.requests")
    def test_list_events(self, mock_requests):
        from calendar.mcp_server import list_events
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"id": 1, "event_time": "2026-06-16T09:00:00", "title": "开会", "repeat": ""}
        ]
        mock_requests.get.return_value = mock_resp
        result = list_events("u1")
        assert "开会" in result

    @patch("calendar.mcp_server.requests")
    def test_list_events_empty(self, mock_requests):
        from calendar.mcp_server import list_events
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_requests.get.return_value = mock_resp
        result = list_events("u1")
        assert "暂无日程" in result

    @patch("calendar.mcp_server.requests")
    def test_get_pending_reminders(self, mock_requests):
        from calendar.mcp_server import get_pending_reminders
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"title": "开会", "event_time": "2026-06-16T09:00:00"}]
        mock_requests.get.return_value = mock_resp
        result = get_pending_reminders("u1")
        assert "开会" in result
        assert "⏰" in result

    @patch("calendar.mcp_server.requests")
    def test_delete_event(self, mock_requests):
        from calendar.mcp_server import delete_event
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "已删除"}
        mock_requests.delete.return_value = mock_resp
        result = delete_event("u1", 1)
        assert "已删除" in result


class TestNotifyMCP:
    @patch("notify.mcp_server.requests")
    def test_save_webhook(self, mock_requests):
        from notify.mcp_server import save_webhook
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"msg": "Webhook已保存: bark"}
        mock_requests.post.return_value = mock_resp
        result = save_webhook("u1", "bark", "https://bark.example.com")
        assert "已保存" in result

    @patch("notify.mcp_server.requests")
    def test_list_webhooks(self, mock_requests):
        from notify.mcp_server import list_webhooks
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": 1, "name": "bark", "url": "https://bark.example.com", "method": "POST"}]
        mock_requests.get.return_value = mock_resp
        result = list_webhooks("u1")
        assert "bark" in result

    @patch("notify.mcp_server.requests")
    def test_list_webhooks_empty(self, mock_requests):
        from notify.mcp_server import list_webhooks
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_requests.get.return_value = mock_resp
        result = list_webhooks("u1")
        assert "暂无Webhook" in result

    @patch("notify.mcp_server.requests")
    def test_send_notification(self, mock_requests):
        from notify.mcp_server import send_notification
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "sent: 200"}
        mock_requests.post.return_value = mock_resp
        result = send_notification("u1", "webhook", "bark", "测试", "内容")
        assert "sent: 200" in result

    @patch("notify.mcp_server.requests")
    def test_get_notify_log(self, mock_requests):
        from notify.mcp_server import get_notify_log
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"time": "2026-06-15 10:00:00", "channel": "webhook", "title": "测试", "status": "sent: 200"}
        ]
        mock_requests.get.return_value = mock_resp
        result = get_notify_log("u1")
        assert "测试" in result

    @patch("notify.mcp_server.requests")
    def test_get_notify_log_empty(self, mock_requests):
        from notify.mcp_server import get_notify_log
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_requests.get.return_value = mock_resp
        result = get_notify_log("u1")
        assert "暂无记录" in result
```

- [ ] **Step 2: Run MCP tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_mcp_servers.py -v`
Expected: All tests PASS

---

## Task 7: Run Full Test Suite & Coverage

**Files:**
- None (configuration only)

- [ ] **Step 1: Run all tests with coverage**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Generate coverage report**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/ --cov=accounting --cov=todo --cov=calendar --cov=notify --cov-report=term-missing`
Expected: High coverage across all services

- [ ] **Step 3: Fix any failing tests**

If any tests fail, fix the test or the source code as needed.

---

## Task 8: Edge Case & Bug Detection Tests

**Files:**
- Create: `tests/test_edge_cases.py`

- [ ] **Step 1: Write edge case tests**

```python
# tests/test_edge_cases.py
"""Edge cases and potential bug detection."""
from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta

class TestAccountingEdgeCases:
    def test_zero_amount(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "amount": 0, "category": "测试"})
        assert resp.status_code == 200

    def test_large_amount(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "amount": 99999999.99, "category": "测试"})
        assert resp.status_code == 200

    def test_special_characters_in_category(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "amount": 10, "category": "餐饮/外卖🍜"})
        assert resp.status_code == 200

    def test_empty_note(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "amount": 10, "category": "测试", "note": ""})
        assert resp.status_code == 200

    def test_summary_negative_totals(self, accounting_app):
        app, db = accounting_app
        client = TestClient(app)
        client.post("/add", json={"user_id": "u1", "amount": 100, "category": "收入"})
        client.post("/add", json={"user_id": "u1", "amount": -200, "category": "支出"})
        resp = client.get("/summary", params={"user_id": "u1"})
        assert resp.json()["total"] == -100


class TestTodoEdgeCases:
    def test_empty_content(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "content": ""})
        assert resp.status_code == 200

    def test_long_content(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        long_text = "任务" * 1000
        resp = client.post("/add", json={"user_id": "u1", "content": long_text})
        assert resp.status_code == 200

    def test_invalid_priority(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.post("/add", json={"user_id": "u1", "content": "测试", "priority": 99})
        # Should accept any integer
        assert resp.status_code == 200

    def test_mark_done_nonexistent(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.post("/done/99999", params={"user_id": "u1"})
        assert resp.status_code == 200
        # No error, just no effect

    def test_delete_nonexistent(self, todo_app):
        app, db = todo_app
        client = TestClient(app)
        resp = client.delete("/delete/99999", params={"user_id": "u1"})
        assert resp.status_code == 200


class TestCalendarEdgeCases:
    def test_past_event_listed(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        past = (datetime.now() - timedelta(days=1)).isoformat()
        client.post("/add", json={"user_id": "u1", "title": "昨天", "event_time": past})
        resp = client.get("/list", params={"user_id": "u1"})
        # Past events from yesterday should appear (since -1 day)
        assert len(resp.json()) >= 1

    def test_remind_before_zero(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        resp = client.post("/add", json={
            "user_id": "u1", "title": "测试", "event_time": future, "remind_before": 0
        })
        assert resp.status_code == 200

    def test_invalid_event_time_format(self, calendar_app):
        app, db = calendar_app
        client = TestClient(app)
        resp = client.post("/add", json={
            "user_id": "u1", "title": "测试", "event_time": "not-a-date"
        })
        # Should still insert (no validation on format)
        assert resp.status_code == 200


class TestNotifyEdgeCases:
    def test_empty_webhook_name(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/webhook/save", json={
            "user_id": "u1", "name": "", "url": "https://example.com"
        })
        assert resp.status_code == 200

    def test_invalid_url(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/webhook/save", json={
            "user_id": "u1", "name": "bad", "url": "not-a-url"
        })
        assert resp.status_code == 200

    def test_empty_title_body(self, notify_app):
        app, db = notify_app
        client = TestClient(app)
        resp = client.post("/send", json={
            "user_id": "u1", "channel": "webhook", "target": "test",
            "title": "", "body": ""
        })
        assert resp.status_code == 200
```

- [ ] **Step 2: Run edge case tests**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/test_edge_cases.py -v`
Expected: All tests PASS

---

## Task 9: Final Full Test Run

- [ ] **Step 1: Run complete test suite**

Run: `cd E:\sync\agentscode\agent_tools_kit && python -m pytest tests/ -v --tb=short --cov=accounting --cov=todo --cov=calendar --cov=notify --cov-report=term-missing`
Expected: All tests PASS, coverage report shows results

- [ ] **Step 2: Review results and document**

Ensure all services are tested and MCP integration works correctly.
