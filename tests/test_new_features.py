"""Tests for Backup, Auth, Data Exchange, and Audit modules."""

import pytest


# ============================================================
# Backup
# ============================================================
class TestBackup:
    def test_create_backup(self, client):
        resp = client.post("/api/backup/create")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "path" in data

    def test_list_backups(self, client):
        client.post("/api/backup/create")
        resp = client.get("/api/backup/list")
        assert resp.status_code == 200
        backups = resp.json()
        assert len(backups) >= 1
        assert "name" in backups[0]
        assert "size_bytes" in backups[0]

    def test_create_named_backup(self, client):
        resp = client.post("/api/backup/create", params={"name": "test_backup"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_restore_nonexistent_backup(self, client):
        resp = client.post("/api/backup/restore/nonexistent.db")
        assert resp.status_code == 500


# ============================================================
# Auth
# ============================================================
class TestAuth:
    def test_register_user(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "testuser", "password": "pass1234", "display_name": "Test User"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "user_id" in data

    def test_register_duplicate_user(self, client):
        client.post("/api/auth/register", json={
            "username": "dup_user", "password": "pass1234"
        })
        resp = client.post("/api/auth/register", json={
            "username": "dup_user", "password": "pass5678"
        })
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "shortpw", "password": "ab"
        })
        assert resp.status_code == 400

    def test_register_short_username(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "a", "password": "pass1234"
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "username": "loginuser", "password": "mypass123"
        })
        resp = client.post("/api/auth/login", json={
            "username": "loginuser", "password": "mypass123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data
        assert data["token"] is not None

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "username": "wrongpw", "password": "correct"
        })
        resp = client.post("/api/auth/login", json={
            "username": "wrongpw", "password": "wrong"
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nobody", "password": "nope"
        })
        assert resp.status_code == 401

    def test_list_users(self, client):
        client.post("/api/auth/register", json={
            "username": "listable", "password": "pass1234", "display_name": "Listable"
        })
        resp = client.get("/api/auth/users")
        assert resp.status_code == 200
        users = resp.json()
        assert any(u["username"] == "listable" for u in users)


# ============================================================
# Data Exchange
# ============================================================
class TestDataExchange:
    def _seed_data(self, client):
        client.post("/api/accounting/add", json={
            "user_id": "ex_u1", "amount": 100, "category": "test", "note": "seed"
        })
        client.post("/api/todo/add", json={
            "user_id": "ex_u1", "content": "test todo"
        })

    def test_export_json(self, client):
        self._seed_data(client)
        resp = client.get("/api/data/export/ex_u1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "ex_u1"
        assert len(data["accounting"]) >= 1
        assert len(data["todos"]) >= 1
        assert "exported_at" in data

    def test_export_csv(self, client):
        self._seed_data(client)
        resp = client.get("/api/data/export/ex_u1/csv/accounting")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_export_csv_invalid_table(self, client):
        resp = client.get("/api/data/export/ex_u1/csv/invalid_table")
        assert resp.status_code == 404

    def test_import_json(self, client):
        export_data = {
            "accounting": [
                {"amount": 50, "category": "imported", "note": "test"}
            ],
            "todos": [
                {"content": "imported todo", "priority": 2}
            ],
            "events": [],
            "webhooks": [],
        }
        resp = client.post("/api/data/import", json={
            "user_id": "import_u1", "data": export_data
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["counts"]["accounting"] == 1
        assert resp.json()["counts"]["todos"] == 1

    def test_export_import_roundtrip(self, client):
        self._seed_data(client)
        # Export
        export_resp = client.get("/api/data/export/ex_u1")
        exported = export_resp.json()
        # Import to new user
        import_resp = client.post("/api/data/import", json={
            "user_id": "roundtrip_u", "data": exported
        })
        assert import_resp.status_code == 200
        assert import_resp.json()["success"] is True
        # Verify the data was imported
        records = client.get("/api/accounting/list", params={"user_id": "roundtrip_u"})
        assert len(records.json()) >= 1


# ============================================================
# Audit
# ============================================================
class TestAudit:
    def test_audit_log_after_operations(self, client):
        # Perform some operations that write audit logs
        client.post("/api/accounting/add", json={
            "user_id": "audit_u1", "amount": 42, "category": "test"
        })
        client.post("/api/todo/add", json={
            "user_id": "audit_u1", "content": "audit test todo"
        })
        # Check audit log
        resp = client.get("/api/audit/log", params={"user_id": "audit_u1"})
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 2
        actions = {e["action"] for e in logs}
        assert "add_record" in actions
        assert "add_todo" in actions

    def test_audit_log_filter_by_action(self, client):
        client.post("/api/accounting/add", json={
            "user_id": "audit_f", "amount": 10, "category": "x"
        })
        resp = client.get("/api/audit/log", params={"user_id": "audit_f", "action": "add_record"})
        assert resp.status_code == 200
        logs = resp.json()
        assert all(e["action"] == "add_record" for e in logs)

    def test_audit_log_empty(self, client):
        resp = client.get("/api/audit/log", params={"user_id": "nobody"})
        assert resp.status_code == 200
        assert resp.json() == []
