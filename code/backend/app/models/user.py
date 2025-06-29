"""
KunlunSec AI Platform - 用户模型

定义用户数据库模型和相关方法。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base

class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # 用户角色和权限
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 用户偏好设置（JSON格式存储）
    preferences = Column(Text, default="{}")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.username}>" 