"""
KunlunSec AI Platform - 令牌模式

定义JWT令牌相关的Pydantic模式。
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TokenData(BaseModel):
    """令牌数据模式"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: Optional[Dict[str, Any]] = None

class Token(BaseModel):
    """API响应模式"""
    success: bool = True
    data: TokenData
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 691200,
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "user",
                        "email": "user@example.com",
                        "role": "user"
                    }
                },
                "message": "登录成功"
            }
        }

class TokenPayload(BaseModel):
    """令牌载荷模式"""
    sub: Optional[str] = None
    exp: int = Field(..., description="过期时间戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sub": "123e4567-e89b-12d3-a456-426614174000",
                "exp": 1609459200
            }
        }

class RefreshToken(BaseModel):
    """
    刷新令牌请求模型
    """
    refresh_token: str 