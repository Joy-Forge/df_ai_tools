"""User authentication module — simple JWT-based auth for personal use."""

import os
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.db import get_conn
from src.logger import get_logger

logger = get_logger(__name__)

# JWT secret — in production, set via env var
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "72"))  # 3 days default


def init_users_table():
    """Create users table if it doesn't exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash password with salt. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256(f"{salt}{password}".encode())
    return hash_obj.hexdigest(), salt


def register_user(username: str, password: str, display_name: str = "") -> dict:
    """Register a new user. Returns {success, msg, user_id}."""
    if len(username) < 2:
        return {"success": False, "msg": "用户名至少2个字符", "user_id": None}
    if len(password) < 4:
        return {"success": False, "msg": "密码至少4个字符", "user_id": None}
    
    password_hash, salt = _hash_password(password)
    
    try:
        with get_conn() as conn:
            c = conn.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
                (username, f"{salt}:{password_hash}", display_name or username),
            )
            user_id = c.lastrowid
            conn.commit()
        logger.info(f"User registered: {username}", extra={"action": "user_register", "user_id": user_id})
        return {"success": True, "msg": f"注册成功: {username}", "user_id": user_id}
    except sqlite3.IntegrityError:
        return {"success": False, "msg": f"用户名已存在: {username}", "user_id": None}


def login_user(username: str, password: str) -> dict:
    """Authenticate user and return a simple token. Returns {success, msg, token, user_id}."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, password_hash, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    
    if row is None:
        return {"success": False, "msg": "用户名或密码错误", "token": None, "user_id": None}
    
    stored_hash = row["password_hash"]
    salt, expected_hash = stored_hash.split(":", 1)
    actual_hash, _ = _hash_password(password, salt)
    
    if actual_hash != expected_hash:
        return {"success": False, "msg": "用户名或密码错误", "token": None, "user_id": None}
    
    # Generate simple token (base64 of user_id:expiry:secret_hash)
    import base64
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    token_data = f"{row['id']}:{int(expiry.timestamp())}"
    token_sig = hashlib.sha256(f"{token_data}:{JWT_SECRET}".encode()).hexdigest()[:16]
    token = base64.urlsafe_b64encode(f"{token_data}:{token_sig}".encode()).decode()
    
    logger.info(f"User logged in: {username}", extra={"action": "user_login", "user_id": row["id"]})
    return {
        "success": True,
        "msg": f"登录成功: {row['display_name']}",
        "token": token,
        "user_id": row["id"],
        "display_name": row["display_name"],
    }


def verify_token(token: str) -> Optional[dict]:
    """Verify a token and return user info if valid. Returns None if invalid."""
    try:
        import base64
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.rsplit(":", 1)
        if len(parts) != 2:
            return None
        
        token_data, token_sig = parts
        expected_sig = hashlib.sha256(f"{token_data}:{JWT_SECRET}".encode()).hexdigest()[:16]
        if token_sig != expected_sig:
            return None
        
        user_id_str, expiry_str = token_data.split(":")
        expiry = int(expiry_str)
        
        if datetime.now(timezone.utc).timestamp() > expiry:
            return None
        
        # Look up user
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, username, display_name FROM users WHERE id = ?",
                (int(user_id_str),),
            ).fetchone()
        
        if row is None:
            return None
        
        return {
            "user_id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
        }
    except Exception:
        return None


def list_users() -> list[dict]:
    """List all users (no passwords)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, display_name, created_at FROM users ORDER BY id"
        ).fetchall()
    return [
        {"id": r["id"], "username": r["username"], 
         "display_name": r["display_name"], "created_at": r["created_at"]}
        for r in rows
    ]
