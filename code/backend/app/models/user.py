from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: uuid.UUID
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 