"""Tests for Notify REST API."""

from unittest.mock import patch, MagicMock
import pytest


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

        with patch("src.notify.service.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_requests.post.return_value = mock_resp

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
        with patch("src.notify.service.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_requests.post.return_value = mock_resp
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
        with patch("src.notify.service.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_requests.post.return_value = mock_resp
            resp = client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "custom",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            call_args = mock_requests.post.call_args
            assert call_args[1]["headers"]["Authorization"] == "Bearer token123"

    def test_webhook_get_method(self, client):
        client.post("/api/notify/webhook/save", json={
            "user_id": "u1", "name": "gethook",
            "url": "https://example.com", "method": "GET"
        })
        with patch("src.notify.service.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_requests.get.return_value = mock_resp
            resp = client.post("/api/notify/send", json={
                "user_id": "u1", "channel": "webhook", "target": "gethook",
                "title": "测试", "body": "内容"
            })
            assert resp.status_code == 200
            mock_requests.get.assert_called_once()
