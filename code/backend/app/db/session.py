"""
KunlunSec AI Platform - 数据库会话管理

处理数据库连接、会话创建和表初始化。
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# 从PostgreSQL URL创建异步引擎
# 将postgresql:// 替换为 postgresql+asyncpg://
SQLALCHEMY_DATABASE_URL = str(settings.DATABASE_URL).replace(
    "postgresql://", "postgresql+asyncpg://"
)

# 同步数据库URL
SQLALCHEMY_SYNC_DATABASE_URL = str(settings.DATABASE_URL)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# 导出会话工厂
async_session = AsyncSessionLocal

# 创建基类
Base = declarative_base()

def get_db_url() -> str:
    """
    获取同步数据库URL
    
    Returns:
        str: 同步数据库URL
    """
    return SQLALCHEMY_SYNC_DATABASE_URL

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    生成:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_db_and_tables():
    """
    创建数据库表
    """
    async with engine.begin() as conn:
        from app.models import Base
        await conn.run_sync(Base.metadata.create_all)

async def close_db_connections():
    """
    关闭数据库连接
    """
    await engine.dispose() 