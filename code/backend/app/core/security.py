"""
KunlunSec AI Platform - 安全模块

处理用户认证、JWT令牌生成和验证。
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    参数:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    返回:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    
    参数:
        password: 明文密码
        
    返回:
        str: 哈希密码
    """
    return pwd_context.hash(password)

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    验证用户
    
    参数:
        db: 数据库会话
        username: 用户名
        password: 密码
        
    返回:
        Optional[User]: 如果验证成功返回用户对象，否则返回None
    """
    # 查询用户
    result = await db.execute(select(User).filter((User.username == username) | (User.email == username)))
    user = result.scalars().first()
    
    # 验证用户存在且密码正确
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    # 验证用户是否激活
    if not user.is_active:
        return None
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    参数:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    返回:
        str: JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌
    
    参数:
        data: 要编码的数据
        
    返回:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 刷新令牌有效期7天
    to_encode.update({"exp": expire, "refresh": True})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_token_from_query(request: Request) -> str:
    """
    从查询参数中获取令牌
    
    参数:
        request: FastAPI请求对象
        
    返回:
        str: JWT令牌
        
    异常:
        HTTPException: 认证失败
    """
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

async def get_current_user_from_refresh_token(
    refresh_token: str,
    db: AsyncSession
) -> Optional[User]:
    """
    从刷新令牌中获取当前用户
    
    参数:
        refresh_token: JWT刷新令牌
        db: 数据库会话
        
    返回:
        Optional[User]: 如果令牌有效则返回用户对象，否则返回None
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # 验证是否为刷新令牌
        if not payload.get("refresh"):
            return None
        
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            return None
            
        username: str = token_data.sub
        if username is None:
            return None
    except JWTError:
        return None
    
    result = await db.execute(select(User).filter((User.username == username) | (User.email == username)))
    user = result.scalars().first()
    
    return user

async def get_current_user_from_token(
    token: str,
    db: AsyncSession
) -> User:
    """
    从令牌中获取当前用户
    
    参数:
        token: JWT令牌
        db: 数据库会话
        
    返回:
        User: 当前用户
        
    异常:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            raise credentials_exception
            
        username: str = token_data.sub
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    from app.services.user import get_user_by_username
    user = await get_user_by_username(db, username)
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    
    参数:
        db: 数据库会话
        token: JWT令牌
        
    返回:
        User: 当前用户
        
    异常:
        HTTPException: 认证失败
    """
    return await get_current_user_from_token(token, db)

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户
    
    参数:
        current_user: 当前用户
        
    返回:
        User: 当前活跃用户
        
    异常:
        HTTPException: 用户不活跃
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户不活跃")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前管理员用户
    
    参数:
        current_user: 当前活跃用户
        
    返回:
        User: 当前管理员用户
        
    异常:
        HTTPException: 权限不足
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足"
        )
    return current_user 