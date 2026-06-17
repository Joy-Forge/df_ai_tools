"""Database backup module — SQLite backup via the online backup API."""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import src.db as db_module
from src.logger import get_logger

logger = get_logger(__name__)

# Backup directory — defaults to data/backups/
BACKUP_DIR = os.environ.get("BACKUP_DIR", "data/backups")
# Number of backups to keep (0 = unlimited)
BACKUP_RETENTION = int(os.environ.get("BACKUP_RETENTION", "7"))


def _ensure_backup_dir():
    """Create backup directory if it doesn't exist."""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def backup_sqlite(backup_name: str | None = None) -> dict:
    """Create a backup of the SQLite database using the online backup API.

    Args:
        backup_name: Optional custom name. Defaults to timestamp-based name.

    Returns:
        dict with keys: success, path, size_bytes, msg
    """
    _ensure_backup_dir()

    if not os.path.exists(db_module.DB_PATH):
        return {"success": False, "path": None, "size_bytes": 0, "msg": "数据库文件不存在"}

    # Generate backup filename
    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"toolkit_{timestamp}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        # Use SQLite online backup API — safe to run while the DB is in use
        source = sqlite3.connect(db_module.DB_PATH)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()

        size = os.path.getsize(backup_path)
        logger.info(
            f"Database backup created: {backup_path} ({size} bytes)",
            extra={"action": "backup_created", "path": backup_path, "size_bytes": size},
        )

        # Clean up old backups
        _cleanup_old_backups()

        return {
            "success": True,
            "path": backup_path,
            "size_bytes": size,
            "msg": f"备份成功: {backup_path} ({_format_size(size)})",
        }
    except Exception as e:
        logger.error(f"Backup failed: {e}", extra={"action": "backup_failed", "error": str(e)})
        return {"success": False, "path": None, "size_bytes": 0, "msg": f"备份失败: {e}"}


def list_backups() -> list[dict]:
    """List all backups in the backup directory."""
    _ensure_backup_dir()
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            stat = os.stat(path)
            backups.append({
                "name": f,
                "path": path,
                "size_bytes": stat.st_size,
                "size": _format_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return backups


def restore_backup(backup_name: str) -> dict:
    """Restore database from a backup file.

    Args:
        backup_name: Name of the backup file in BACKUP_DIR.

    Returns:
        dict with keys: success, msg
    """
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    if not os.path.exists(backup_path):
        return {"success": False, "msg": f"备份文件不存在: {backup_name}"}

    try:
        # Create a safety backup of current DB first
        safety_name = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if os.path.exists(db_module.DB_PATH):
            shutil.copy2(db_module.DB_PATH, os.path.join(BACKUP_DIR, safety_name))
            logger.info(f"Safety backup before restore: {safety_name}", extra={"action": "pre_restore_backup"})

        # Restore
        shutil.copy2(backup_path, db_module.DB_PATH)
        logger.info(f"Database restored from: {backup_name}", extra={"action": "restore_completed"})
        return {"success": True, "msg": f"恢复成功，已从 {backup_name} 还原（恢复前备份: {safety_name}）"}
    except Exception as e:
        logger.error(f"Restore failed: {e}", extra={"action": "restore_failed", "error": str(e)})
        return {"success": False, "msg": f"恢复失败: {e}"}


def _cleanup_old_backups():
    """Remove old backups beyond retention limit."""
    if BACKUP_RETENTION <= 0:
        return

    backups = list_backups()
    if len(backups) > BACKUP_RETENTION:
        for old in backups[BACKUP_RETENTION:]:
            try:
                os.remove(old["path"])
                logger.info(f"Removed old backup: {old['name']}", extra={"action": "backup_cleanup"})
            except Exception as e:
                logger.warning(f"Failed to remove old backup {old['name']}: {e}")


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
