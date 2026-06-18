"""API contract tests — verify all REST endpoints return correct status codes
and response shapes. Equivalent to the PowerShell test-all-api.ps1 script
but using pytest + TestClient for CI integration."""

import pytest


class TestHealthContract:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "tools" in data


class TestAccountingContract:
    def test_add_record(self, client):
        resp = client.post("/api/accounting/add", json={
            "user_id": "contract_u1", "amount": 10, "category": "test", "note": "contract"
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_list_records(self, client):
        resp = client.get("/api/accounting/list", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_summary(self, client):
        resp = client.get("/api/accounting/summary", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert "total" in resp.json()

    def test_update_record(self, client):
        add = client.post("/api/accounting/add", json={
            "user_id": "contract_u1", "amount": 20, "category": "test"
        })
        rid = add.json()["id"]
        resp = client.put(f"/api/accounting/update/{rid}",
                          params={"user_id": "contract_u1"},
                          json={"amount": 30})
        assert resp.status_code == 200

    def test_update_nonexistent_record(self, client):
        resp = client.put("/api/accounting/update/99999",
                          params={"user_id": "contract_u1"},
                          json={"amount": 1})
        assert resp.status_code == 404

    def test_list_missing_user_param(self, client):
        resp = client.get("/api/accounting/list")
        assert resp.status_code == 422  # Missing required query param


class TestTodoContract:
    def test_add_todo(self, client):
        resp = client.post("/api/todo/add", json={
            "user_id": "contract_u1", "content": "contract task"
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_list_todos(self, client):
        resp = client.get("/api/todo/list", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_todos_filtered(self, client):
        resp = client.get("/api/todo/list", params={"user_id": "contract_u1", "done": 0})
        assert resp.status_code == 200

    def test_done_todo(self, client):
        add = client.post("/api/todo/add", json={
            "user_id": "contract_u1", "content": "mark done"
        })
        tid = add.json()["id"]
        resp = client.post(f"/api/todo/done/{tid}", params={"user_id": "contract_u1"})
        assert resp.status_code == 200

    def test_undo_todo(self, client):
        add = client.post("/api/todo/add", json={
            "user_id": "contract_u1", "content": "mark undo"
        })
        tid = add.json()["id"]
        client.post(f"/api/todo/done/{tid}", params={"user_id": "contract_u1"})
        resp = client.post(f"/api/todo/undo/{tid}", params={"user_id": "contract_u1"})
        assert resp.status_code == 200

    def test_edit_todo(self, client):
        add = client.post("/api/todo/add", json={
            "user_id": "contract_u1", "content": "original"
        })
        tid = add.json()["id"]
        resp = client.put(f"/api/todo/edit/{tid}",
                          params={"user_id": "contract_u1"},
                          json={"content": "edited"})
        assert resp.status_code == 200

    def test_done_nonexistent_todo(self, client):
        resp = client.post("/api/todo/done/99999", params={"user_id": "contract_u1"})
        assert resp.status_code == 404


class TestCalendarContract:
    def test_add_event(self, client):
        resp = client.post("/api/calendar/add", json={
            "user_id": "contract_u1", "title": "meeting",
            "event_time": "2026-12-31 10:00:00"
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_list_events(self, client):
        resp = client.get("/api/calendar/list", params={"user_id": "contract_u1", "days": 30})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_pending_reminders(self, client):
        resp = client.get("/api/calendar/pending_reminders", params={"user_id": "contract_u1"})
        assert resp.status_code == 200

    def test_reminders_log(self, client):
        resp = client.get("/api/calendar/reminders_log", params={"user_id": "contract_u1"})
        assert resp.status_code == 200

    def test_delete_event(self, client):
        add = client.post("/api/calendar/add", json={
            "user_id": "contract_u1", "title": "to_delete",
            "event_time": "2026-12-31 10:00:00"
        })
        eid = add.json()["id"]
        resp = client.delete(f"/api/calendar/delete/{eid}", params={"user_id": "contract_u1"})
        assert resp.status_code == 200


class TestNotifyContract:
    def test_save_webhook(self, client):
        resp = client.post("/api/notify/webhook/save", json={
            "user_id": "contract_u1", "name": "hook1", "url": "https://example.com"
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_list_webhooks(self, client):
        resp = client.get("/api/notify/webhook/list", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_notify_log(self, client):
        resp = client.get("/api/notify/log", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestBackupContract:
    def test_create_backup(self, client):
        resp = client.post("/api/backup/create")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_list_backups(self, client):
        resp = client.get("/api/backup/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_restore_nonexistent(self, client):
        resp = client.post("/api/backup/restore/nonexistent.db")
        assert resp.status_code == 500
        assert "不存在" in resp.json()["detail"]


class TestDataExchangeContract:
    def test_export_json(self, client):
        resp = client.get("/api/data/export/contract_u1")
        assert resp.status_code == 200
        assert "user_id" in resp.json()

    def test_export_csv(self, client):
        resp = client.get("/api/data/export/contract_u1/csv/accounting")
        # May be 404 if no data, which is valid
        assert resp.status_code in (200, 404)

    def test_import(self, client):
        resp = client.post("/api/data/import", json={
            "user_id": "contract_u1", "data": {}
        })
        assert resp.status_code == 200


class TestAuditContract:
    def test_audit_log(self, client):
        resp = client.get("/api/audit/log", params={"user_id": "contract_u1"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestMCPContract:
    def test_mcp_get_returns_406(self, client):
        """MCP endpoint rejects GET with 406 Not Acceptable."""
        resp = client.get("/mcp")
        assert resp.status_code == 406
