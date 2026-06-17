"""Auth REST API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.auth import register_user, login_user, list_users

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    username: str
    password: str
    display_name: str = ""


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(data: RegisterIn):
    """注册新用户"""
    result = register_user(data.username, data.password, data.display_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["msg"])
    return result


@router.post("/login")
def login(data: LoginIn):
    """用户登录，返回 token"""
    result = login_user(data.username, data.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["msg"])
    return result


@router.get("/users")
def get_users():
    """列出所有用户"""
    return list_users()
