import uuid
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User, UserCreate, Token, UserInDB

router = APIRouter()

# 伪数据库，用于演示
FAKE_USERS_DB = {}

# 初始化一个默认用户
default_user_id = uuid.uuid4()
default_user = UserInDB(
    id=default_user_id,
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin"),
    role="admin",
    created_at="2024-01-01T00:00:00"
)
FAKE_USERS_DB[default_user.username] = default_user.model_dump()


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

@router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录获取访问令牌
    """
    user = get_user(FAKE_USERS_DB, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=User)
async def read_users_me():
    # 这是一个示例，实际应用中需要从token中解析出当前用户
    # For now, we'll return the default admin user.
    # A full implementation would require a `get_current_user` dependency.
    user = get_user(FAKE_USERS_DB, "admin")
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    return user 