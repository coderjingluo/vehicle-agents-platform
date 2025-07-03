#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加用户角色列

此脚本用于向users表添加role列，解决数据库模式与代码不一致的问题。

使用方法:
    python add_role_column.py [--db-url DATABASE_URL]

参数:
    --db-url DATABASE_URL  数据库连接URL (默认: postgresql+asyncpg://postgres:postgres@localhost:5432/tara_platform)
"""

import asyncio
import argparse
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认数据库连接配置
DEFAULT_DATABASE_URL = "postgresql+asyncpg://admin:admin123@localhost:5432/automotive_security"

async def add_role_column(database_url):
    """添加role列到users表"""
    # 创建异步引擎
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 检查列是否存在
            check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='role'")
            result = await session.execute(check_query)
            column_exists = result.scalar() is not None
            
            if not column_exists:
                logger.info("添加role列到users表...")
                # 添加role列，默认值为'user'
                add_column_query = text("ALTER TABLE users ADD COLUMN role VARCHAR(255) DEFAULT 'user'")
                await session.execute(add_column_query)
                await session.commit()
                logger.info("成功添加role列")
            else:
                logger.info("role列已存在，无需添加")
                
            # 更新现有管理员用户的角色
            update_admin_query = text("UPDATE users SET role = 'admin' WHERE is_admin = TRUE")
            await session.execute(update_admin_query)
            await session.commit()
            logger.info("已更新管理员用户的角色")
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"添加role列失败: {str(e)}")
            return False
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="数据库迁移脚本 - 添加用户角色列")
    parser.add_argument("--db-url", help="数据库连接URL", default=DEFAULT_DATABASE_URL)
    args = parser.parse_args()
    
    database_url = args.db_url
    logger.info(f"使用数据库连接: {database_url}")
    
    logger.info("开始数据库迁移...")
    success = await add_role_column(database_url)
    if success:
        logger.info("数据库迁移成功完成")
    else:
        logger.error("数据库迁移失败")

if __name__ == "__main__":
    asyncio.run(main()) 