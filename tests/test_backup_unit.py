"""Tests for src/backup.py — backup, restore, cleanup, format_size."""

import os
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import src.db as db_module
import src.backup as backup_module
from src.backup import (
    backup_sqlite,
    list_backups,
    restore_backup,
    _cleanup_old_backups,
    _format_size,
)


@pytest.fixture
def backup_env(tmp_path):
    """Set up a temp backup dir and DB for backup tests."""
    backup_dir = str(tmp_path / "backups")
    db_path = str(tmp_path / "toolkit.db")

    # Create a minimal DB
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.execute("INSERT INTO test VALUES (1)")
    conn.commit()
    conn.close()

    original_db = db_module.DB_PATH
    original_backup_dir = backup_module.BACKUP_DIR
    db_module.DB_PATH = db_path
    backup_module.BACKUP_DIR = backup_dir

    yield {"db_path": db_path, "backup_dir": backup_dir, "tmp_path": tmp_path}

    db_module.DB_PATH = original_db
    backup_module.BACKUP_DIR = original_backup_dir


# ---------------------------------------------------------------------------
# backup_sqlite
# ---------------------------------------------------------------------------
class TestBackupSqlite:
    def test_db_not_exists(self, tmp_path):
        db_module.DB_PATH = str(tmp_path / "nonexistent.db")
        result = backup_sqlite()
        assert result["success"] is False
        assert "不存在" in result["msg"]

    def test_backup_exception(self, backup_env):
        with patch("src.backup.sqlite3.connect") as mock_connect:
            mock_connect.side_effect = RuntimeError("disk full")
            result = backup_sqlite()
            assert result["success"] is False
            assert "失败" in result["msg"]

    def test_backup_success(self, backup_env):
        result = backup_sqlite("test_backup.db")
        assert result["success"] is True
        assert result["size_bytes"] > 0
        assert os.path.exists(result["path"])

    def test_backup_auto_name(self, backup_env):
        result = backup_sqlite()
        assert result["success"] is True
        assert "toolkit_" in result["path"]


# ---------------------------------------------------------------------------
# restore_backup
# ---------------------------------------------------------------------------
class TestRestoreBackup:
    def test_restore_file_not_exists(self, backup_env):
        result = restore_backup("nonexistent.db")
        assert result["success"] is False
        assert "不存在" in result["msg"]

    def test_restore_exception(self, backup_env):
        # Create a backup file first
        backup_sqlite("restore_test.db")
        with patch("src.backup.shutil.copy2") as mock_copy:
            mock_copy.side_effect = PermissionError("access denied")
            result = restore_backup("restore_test.db")
            assert result["success"] is False
            assert "恢复失败" in result["msg"]

    def test_restore_success(self, backup_env):
        backup_sqlite("restore_ok.db")
        result = restore_backup("restore_ok.db")
        assert result["success"] is True
        assert "恢复成功" in result["msg"]


# ---------------------------------------------------------------------------
# _cleanup_old_backups
# ---------------------------------------------------------------------------
class TestCleanupOldBackups:
    def test_retention_zero_no_cleanup(self, backup_env):
        """When BACKUP_RETENTION <= 0, no files should be deleted."""
        original = backup_module.BACKUP_RETENTION
        backup_module.BACKUP_RETENTION = 0

        # Create 5 backup files
        for i in range(5):
            backup_sqlite(f"old_{i}.db")

        backups = list_backups()
        assert len(backups) == 5

        backup_module.BACKUP_RETENTION = original

    def test_os_remove_exception_does_not_crash(self, backup_env):
        """If os.remove fails, cleanup should not raise."""
        original = backup_module.BACKUP_RETENTION
        backup_module.BACKUP_RETENTION = 2

        # Create 3 backup files (exceeds retention of 2)
        for i in range(3):
            backup_sqlite(f"keep_{i}.db")

        with patch("src.backup.os.remove") as mock_remove:
            mock_remove.side_effect = OSError("file in use")
            _cleanup_old_backups()  # Should not raise

        backup_module.BACKUP_RETENTION = original


# ---------------------------------------------------------------------------
# _format_size
# ---------------------------------------------------------------------------
class TestFormatSize:
    def test_bytes(self):
        assert _format_size(500) == "500.0B"

    def test_kb(self):
        assert _format_size(2048) == "2.0KB"

    def test_mb(self):
        assert _format_size(1024 * 1024) == "1.0MB"

    def test_gb(self):
        assert _format_size(1024 ** 3) == "1.0GB"

    def test_tb(self):
        assert _format_size(1024 ** 4) == "1.0TB"

    def test_large_tb(self):
        result = _format_size(int(1.5 * 1024 ** 4))
        assert "TB" in result
