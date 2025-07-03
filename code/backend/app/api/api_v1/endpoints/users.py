"""
用户管理API端点

提供用户管理相关的API接口，包括创建、查询、更新和删除用户
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.core.security import get_current_active_user, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="创建新用户"
)
async def create_user(
    user_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新用户（需要管理员权限）
    """
    # 验证当前用户是否为管理员
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    # 检查用户名或邮箱是否已存在
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_data["username"],
                User.email == user_data["email"]
            )
        )
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data["password"])
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=hashed_password,
        role=user_data.get("role", "user"),
        is_active=user_data.get("is_active", True)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "success": True,
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at
        },
        "message": "用户创建成功"
    }


@router.get(
    "/",
    summary="获取用户列表"
)
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None, description="按激活状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户列表（需要管理员权限）
    """
    # 验证当前用户是否为管理员
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    # 构建查询
    query = select(User)
    
    # 应用筛选条件
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # 获取总记录数
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # 应用分页
    query = query.offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 构建响应
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login
        })
    
    return {
        "success": True,
        "data": {
            "users": user_list,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        },
        "message": "获取用户列表成功"
    }


@router.get(
    "/{user_id}",
    summary="获取用户详情"
)
async def get_user(
    user_id: str = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定用户的详细信息
    """
    # 验证当前用户是否为管理员或查询自己的信息
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只能查看自己的信息"
        )
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login
        },
        "message": "获取用户详情成功"
    }


@router.put(
    "/{user_id}",
    summary="更新用户信息"
)
async def update_user(
    user_data: dict,
    user_id: str = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新指定用户的信息
    """
    # 验证当前用户是否为管理员或更新自己的信息
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只能更新自己的信息"
        )
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否已被其他用户使用
    if "email" in user_data and user_data["email"] != user.email:
        email_result = await db.execute(
            select(User).where(
                User.email == user_data["email"],
                User.id != user_id
            )
        )
        if email_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被其他用户使用"
            )
        user.email = user_data["email"]
    
    # 更新密码（如果提供）
    if "password" in user_data:
        # 如果是用户自己更新，需要验证旧密码
        if current_user.id == user_id and "old_password" not in user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新密码需要提供旧密码"
            )
        
        if current_user.id == user_id and not verify_password(user_data["old_password"], user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码不正确"
            )
        
        user.hashed_password = get_password_hash(user_data["password"])
    
    # 只有管理员可以更新角色和激活状态
    if current_user.role == "admin":
        if "role" in user_data:
            user.role = user_data["role"]
        if "is_active" in user_data:
            user.is_active = user_data["is_active"]
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "updated_at": user.updated_at
        },
        "message": "用户信息更新成功"
    }


@router.delete(
    "/{user_id}",
    summary="删除用户"
)
async def delete_user(
    user_id: str = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定用户（需要管理员权限）
    """
    # 验证当前用户是否为管理员
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    # 不能删除自己
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录的用户"
        )
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户
    await db.delete(user)
    await db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "用户删除成功"
    } 