"""
KunlunSec AI Platform - 令牌模式

定义JWT令牌相关的Pydantic模式。
"""

from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    """访问令牌模式"""
    access_token: str
    token_type: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
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