"""Pytest fixtures for Agent Tools Kit tests."""

import sys
import os
from pathlib import Path

# Ensure src/ is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary DB path and override src.db.DB_PATH."""
    db_path = tmp_path / "test_toolkit.db"
    # Override the DB path before any imports
    import src.db
    original = src.db.DB_PATH
    src.db.DB_PATH = str(db_path)
    # Init tables
    src.db.init_db()
    yield str(db_path)
    src.db.DB_PATH = original
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def app(test_db):
    """Return the FastAPI app with test DB."""
    from src.main import app
    return app


@pytest.fixture
def client(app):
    """Return a TestClient for the app."""
    with TestClient(app) as c:
        yield c
