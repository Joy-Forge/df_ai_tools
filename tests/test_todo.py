"""Tests for Todo REST API."""


class TestTodoAPI:
    def test_add_todo(self, client):
        resp = client.post("/api/todo/add", json={
            "user_id": "u1", "content": "买菜", "priority": 1, "due_date": "2026-06-20"
        })
        assert resp.status_code == 200
        assert "已添加" in resp.json()["msg"]

    def test_add_todo_minimal(self, client):
        resp = client.post("/api/todo/add", json={"user_id": "u1", "content": "简单任务"})
        assert resp.status_code == 200

    def test_list_todos(self, client):
        client.post("/api/todo/add", json={"user_id": "u1", "content": "任务A"})
        client.post("/api/todo/add", json={"user_id": "u1", "content": "任务B"})
        client.post("/api/todo/add", json={"user_id": "u2", "content": "任务C"})
        resp = client.get("/api/todo/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_todos_filter_done(self, client):
        r1 = client.post("/api/todo/add", json={"user_id": "u1", "content": "A"})
        r2 = client.post("/api/todo/add", json={"user_id": "u1", "content": "B"})
        client.post(f"/api/todo/done/{r1.json()['id']}", params={"user_id": "u1"})
        resp = client.get("/api/todo/list", params={"user_id": "u1", "done": 0})
        assert len(resp.json()) == 1
        assert resp.json()[0]["content"] == "B"
        resp = client.get("/api/todo/list", params={"user_id": "u1", "done": 1})
        assert len(resp.json()) == 1
        assert resp.json()[0]["content"] == "A"

    def test_mark_done(self, client):
        r = client.post("/api/todo/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.post(f"/api/todo/done/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert "已完成" in resp.json()["msg"]
        resp = client.get("/api/todo/list", params={"user_id": "u1", "done": 1})
        assert len(resp.json()) == 1

    def test_mark_undo(self, client):
        r = client.post("/api/todo/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        client.post(f"/api/todo/done/{tid}", params={"user_id": "u1"})
        resp = client.post(f"/api/todo/undo/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert "恢复" in resp.json()["msg"]
        resp = client.get("/api/todo/list", params={"user_id": "u1", "done": 0})
        assert len(resp.json()) == 1

    def test_delete_todo(self, client):
        r = client.post("/api/todo/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.delete(f"/api/todo/delete/{tid}", params={"user_id": "u1"})
        assert resp.status_code == 200
        resp = client.get("/api/todo/list", params={"user_id": "u1"})
        assert len(resp.json()) == 0

    def test_delete_todo_wrong_user(self, client):
        r = client.post("/api/todo/add", json={"user_id": "u1", "content": "测试"})
        tid = r.json()["id"]
        resp = client.delete(f"/api/todo/delete/{tid}", params={"user_id": "u2"})
        assert resp.status_code == 200
        resp = client.get("/api/todo/list", params={"user_id": "u1"})
        assert len(resp.json()) == 1

    def test_list_ordering(self, client):
        client.post("/api/todo/add", json={"user_id": "u1", "content": "低优先", "priority": 3})
        client.post("/api/todo/add", json={"user_id": "u1", "content": "高优先", "priority": 1})
        client.post("/api/todo/add", json={"user_id": "u1", "content": "中优先", "priority": 2})
        resp = client.get("/api/todo/list", params={"user_id": "u1"})
        data = resp.json()
        assert data[0]["content"] == "高优先"
        assert data[1]["content"] == "中优先"
        assert data[2]["content"] == "低优先"
