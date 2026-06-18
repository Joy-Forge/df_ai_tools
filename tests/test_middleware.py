"""Tests for src/main.py middleware — rate limiter, auth, startup catch-up."""

import os
import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Rate limiter tests
# ---------------------------------------------------------------------------
class TestRateLimiter:
    """Rate limiter is disabled in conftest (RATE_LIMIT_PER_MINUTE=0).
    These tests temporarily enable it."""

    @pytest.fixture(autouse=True)
    def _enable_rate_limit(self):
        """Temporarily enable rate limiting for these tests."""
        import src.main
        original = src.main.RATE_LIMIT_PER_MINUTE
        src.main.RATE_LIMIT_PER_MINUTE = 3  # 3 requests per minute
        src.main._rate_limit_store.clear()
        yield
        src.main.RATE_LIMIT_PER_MINUTE = original
        src.main._rate_limit_store.clear()

    def test_normal_request_passes(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_rate_limit_exceeded(self, client):
        # Fill up the rate limit store
        import src.main
        src.main._rate_limit_store["testclient"] = [time.time()] * 3
        resp = client.get("/api/health")
        assert resp.status_code == 429
        assert "请求过于频繁" in resp.json()["detail"]

    def test_non_api_path_bypasses_rate_limit(self, client):
        """Non-/api/ paths should not be rate-limited."""
        import src.main
        src.main._rate_limit_store["testclient"] = [time.time()] * 3
        # /mcp is not under /api/, should pass through
        resp = client.get("/mcp")
        assert resp.status_code != 429

    def test_expired_entries_cleaned(self, client):
        """Old entries beyond 60s window should be cleaned."""
        import src.main
        old_time = time.time() - 120  # 2 minutes ago
        src.main._rate_limit_store["testclient"] = [old_time, old_time]
        # Should allow request since old entries are cleaned
        resp = client.get("/api/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Auth middleware tests
# ---------------------------------------------------------------------------
class TestAuthMiddleware:
    """Auth middleware is normally disabled (API_KEY unset).
    These tests temporarily set API_KEY."""

    @pytest.fixture(autouse=True)
    def _enable_auth(self):
        """Temporarily enable API_KEY auth."""
        import src.main
        original = src.main._API_KEY
        src.main._API_KEY = "test-secret-key-123"
        yield
        src.main._API_KEY = original

    def test_valid_key_passes(self, client):
        resp = client.get(
            "/api/accounting/list",
            params={"user_id": "test"},
            headers={"X-API-Key": "test-secret-key-123"},
        )
        assert resp.status_code == 200

    def test_missing_key_returns_401(self, client):
        resp = client.get("/api/accounting/list", params={"user_id": "test"})
        assert resp.status_code == 401
        assert "API Key" in resp.json()["detail"]

    def test_wrong_key_returns_401(self, client):
        resp = client.get(
            "/api/accounting/list",
            params={"user_id": "test"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_health_exempt(self, client):
        """Health endpoint should be exempt from auth."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_mcp_exempt(self, client):
        """MCP endpoint should be exempt from auth."""
        resp = client.get("/mcp")
        # MCP returns 405/406 for GET, but NOT 401
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# Startup catch-up exception test
# ---------------------------------------------------------------------------
class TestStartupCatchUp:
    def test_catchup_exception_does_not_crash(self, test_db):
        """If check_reminders() throws during startup, app should still start."""
        with patch("src.main.check_reminders", side_effect=RuntimeError("db locked")):
            from src.main import app
            with TestClient(app) as c:
                resp = c.get("/api/health")
                assert resp.status_code == 200
