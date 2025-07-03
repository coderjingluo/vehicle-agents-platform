"""
用户服务模块

提供用户相关的服务函数，如获取用户、创建用户等。
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.models.user import User

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    根据用户名或邮箱获取用户
    
    参数:
        db: 数据库会话
        username: 用户名或邮箱
        
    返回:
        Optional[User]: 如果找到则返回用户对象，否则返回None
    """
    result = await db.execute(
        select(User).where(or_(User.username == username, User.email == username))
    )
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    根据ID获取用户
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        
    返回:
        Optional[User]: 如果找到则返回用户对象，否则返回None
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    is_active: Optional[bool] = None
) -> list[User]:
    """
    获取用户列表
    
    参数:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 返回的最大记录数
        is_active: 过滤活跃状态
        
    返回:
        list[User]: 用户列表
    """
    query = select(User)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_active: bool = True,
    is_admin: bool = False,
) -> User:
    """
    创建新用户
    
    参数:
        db: 数据库会话
        username: 用户名
        email: 邮箱
        password: 密码（未哈希）
        full_name: 全名
        is_active: 是否活跃
        is_admin: 是否管理员
        
    返回:
        User: 创建的用户对象
    """
    from app.core.security import get_password_hash
    
    # 检查用户名和邮箱是否已存在
    result = await db.execute(
        select(User).where(or_(User.username == username, User.email == email))
    )
    existing_user = result.scalars().first()
    if existing_user:
        if existing_user.username == username:
            raise ValueError(f"用户名 '{username}' 已存在")
        else:
            raise ValueError(f"邮箱 '{email}' 已存在")
    
    # 创建新用户
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=is_active,
        is_admin=is_admin,
        role="admin" if is_admin else "user"
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user 