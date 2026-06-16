"""Tests for Accounting REST API."""

import pytest


class TestAccountingAPI:
    """REST API tests."""

    def test_add_record(self, client):
        resp = client.post("/api/accounting/add", json={
            "user_id": "u1", "amount": 50.5, "category": "餐饮", "note": "午饭"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "已记录" in data["msg"]

    def test_add_record_negative(self, client):
        resp = client.post("/api/accounting/add", json={
            "user_id": "u1", "amount": -100, "category": "交通", "note": "打车"
        })
        assert resp.status_code == 200
        assert "已记录" in resp.json()["msg"]

    def test_list_records(self, client):
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 20, "category": "测试"})
        client.post("/api/accounting/add", json={"user_id": "u2", "amount": 30, "category": "测试"})
        resp = client.get("/api/accounting/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(r["amount"] in [10, 20] for r in data)

    def test_list_records_empty(self, client):
        resp = client.get("/api/accounting/list", params={"user_id": "nobody"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_records_limit(self, client):
        for i in range(5):
            client.post("/api/accounting/add", json={"user_id": "u1", "amount": i, "category": "测试"})
        resp = client.get("/api/accounting/list", params={"user_id": "u1", "limit": 2})
        assert len(resp.json()) == 2

    def test_summary(self, client):
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 100, "category": "餐饮"})
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 200, "category": "交通"})
        client.post("/api/accounting/add", json={"user_id": "u1", "amount": 50, "category": "餐饮"})
        resp = client.get("/api/accounting/summary", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 350
        assert data["by_category"]["餐饮"] == 150
        assert data["by_category"]["交通"] == 200

    def test_summary_empty(self, client):
        resp = client.get("/api/accounting/summary", params={"user_id": "nobody"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["by_category"] == {}

    def test_delete_record(self, client):
        r = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        rid = r.json()["id"]
        resp = client.delete(f"/api/accounting/delete/{rid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        resp = client.get("/api/accounting/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_delete_record_wrong_user(self, client):
        r = client.post("/api/accounting/add", json={"user_id": "u1", "amount": 10, "category": "测试"})
        rid = r.json()["id"]
        resp = client.delete(f"/api/accounting/delete/{rid}", params={"user_id": "u2"})
        assert resp.status_code == 404  # wrong user → not found
        resp = client.get("/api/accounting/list", params={"user_id": "u1"})
        assert len(resp.json()) == 1
