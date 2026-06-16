"""Tests for Notify REST API."""

from unittest.mock import patch, AsyncMock
import httpx
import pytest
from httpx import Response


class TestNotifyAPI:
    def test_save_webhook(self, client):
        resp = client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "bark", "url": "https://bark.example.com/push"
        })
        assert resp.status_code == 200
        assert "已保存" in resp.json()["msg"]

    def test_list_webhooks(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "bark", "url": "https://bark.example.com"
        })
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "wechat", "url": "https://qyapi.example.com"
        })
        client.post("/api/notify/webhook/save", json={
            "user_id": "u2", "name": "other", "url": "https://other.example.com"
        })
        resp = client.get("/api/notify/webhook/list", params={"user_id": "u1"})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_send_notification_webhook(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "test", "url": "https://httpbin.org/post"
        })

        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch("httpx.AsyncClient.post", new=mock_post):
            resp = client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "test",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            assert "sent: 200" in resp.json()["status"]

    def test_send_notification_webhook_not_found(self, client):
        resp = client.post("/api/notify/send", json={
            "user_id": "u1", "channel": "webhook", "target": "不存在",
            "title": "测试", "body": "内容"
        })
        assert resp.status_code == 200
        assert "error" in resp.json()["status"]

    def test_send_notification_unsupported_channel(self, client):
        resp = client.post("/api/notify/send", json={
            "user_id": "u1", "channel": "email", "target": "test@example.com",
            "title": "测试", "body": "内容"
        })
        assert resp.status_code == 200
        assert "unsupported" in resp.json()["status"]

    def test_notify_log(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "test", "url": "https://example.com"
        })
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch("httpx.AsyncClient.post", new=mock_post):
            client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "test",
                "title": "测试", "body": "内容"
            })
        resp = client.get("/api/notify/log", params={"user_id": "u1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "测试"

    def test_webhook_with_custom_headers(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "custom",
            "url": "https://example.com", "headers": '{"Authorization": "Bearer token123"}'
        })
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            resp = client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "custom",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            _, kwargs = mock_post.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer token123"

    def test_webhook_get_method(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "gethook",
            "url": "https://example.com", "method": "GET"
        })
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            resp = client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "gethook",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            mock_get.assert_called_once()
