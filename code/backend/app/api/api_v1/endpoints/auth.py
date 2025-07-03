"""
认证API端点

提供用户认证、登出、令牌刷新和获取用户信息的API接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.config import settings
from app.core.security import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token, 
    get_current_active_user,
    get_current_user_from_refresh_token
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token, RefreshToken

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="用户登录"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录获取访问令牌
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # 更新用户最后登录时间
    user.update_last_login()
    await db.commit()
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        },
        "message": "登录成功"
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="用户登出"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出
    
    目前简单实现，客户端应当丢弃令牌
    """
    return {
        "success": True,
        "data": None,
        "message": "登出成功"
    }


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="刷新访问令牌"
)
async def refresh_token(
    refresh_token_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """
    使用刷新令牌获取新的访问令牌
    """
    user = await get_current_user_from_refresh_token(refresh_token_data.refresh_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        "message": "令牌刷新成功"
    }


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="获取当前用户信息"
)
async def get_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的信息
    """
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "last_login": current_user.last_login
        },
        "message": "获取用户信息成功"
    } 