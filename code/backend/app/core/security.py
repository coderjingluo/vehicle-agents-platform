"""
KunlunSec AI Platform - 安全模块

处理用户认证、JWT令牌生成和验证。
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
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

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    参数:
        subject: 令牌主题（通常是用户ID）
        expires_delta: 过期时间增量
        
    返回:
        str: JWT令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

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
            
        user_id: str = token_data.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    from app.services.user import get_user_by_id
    user = await get_user_by_id(db, user_id)
    
    if user is None:
        raise credentials_exception
        
    return user

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