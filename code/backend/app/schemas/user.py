"""
用户相关的Pydantic模型
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基本信息"""
    username: str
    email: EmailStr
    role: str = Field(default="user", description="用户角色，如admin, user等")
    is_active: bool = Field(default=True, description="用户是否激活")


class UserCreate(UserBase):
    """创建用户的请求模型"""
    password: str


class UserUpdate(BaseModel):
    """更新用户的请求模型"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    old_password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: list[UserResponse]
    pagination: dict

    class Config:
        orm_mode = True



