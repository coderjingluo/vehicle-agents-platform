#!/usr/bin/env python3
"""
创建管理员用户脚本

此脚本用于在automotive_security数据库的用户表中创建一个新的管理员用户。

使用方法:
    python create_admin_user.py [--db-url DATABASE_URL] [--username USERNAME] [--password PASSWORD] [--email EMAIL]

参数:
    --db-url DATABASE_URL     数据库连接URL (默认与add_role_column.py相同)
    --username USERNAME       管理员用户名 (默认: admin)
    --password PASSWORD       管理员密码 (默认: admin123)
    --email EMAIL             管理员邮箱 (默认: admin@example.com)
"""

import asyncio
import argparse
import logging
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认数据库连接配置（与add_role_column.py相同）
DEFAULT_DATABASE_URL = "postgresql+asyncpg://admin:admin123@localhost:5432/automotive_security"

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

async def create_admin_user(database_url, username, password, email):
    """创建管理员用户"""
    # 创建异步引擎
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 首先检查用户是否已存在
            check_query = text("SELECT id FROM users WHERE username = :username OR email = :email")
            result = await session.execute(check_query, {"username": username, "email": email})
            user_exists = result.scalar() is not None
            
            if user_exists:
                logger.warning(f"用户 {username} 或邮箱 {email} 已存在")
                # 尝试更新现有用户为管理员
                update_query = text("""
                    UPDATE users 
                    SET is_admin = TRUE, 
                        role = 'admin',
                        hashed_password = :hashed_password
                    WHERE username = :username OR email = :email
                """)
                await session.execute(update_query, {
                    "username": username,
                    "email": email,
                    "hashed_password": get_password_hash(password)
                })
                await session.commit()
                logger.info(f"已将用户 {username} 更新为管理员")
                return True
            
            # 检查表是否存在role列
            check_role_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='role'")
            result = await session.execute(check_role_query)
            role_column_exists = result.scalar() is not None
            
            # 生成UUID
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # 准备SQL语句
            if role_column_exists:
                # 如果存在role列
                insert_query = text("""
                    INSERT INTO users (
                        id, email, username, hashed_password, full_name, 
                        is_active, is_admin, role, preferences, 
                        created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :hashed_password, :full_name, 
                        :is_active, :is_admin, :role, :preferences, 
                        :created_at, :updated_at
                    )
                """)
                params = {
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "hashed_password": get_password_hash(password),
                    "full_name": f"{username.capitalize()} Admin",
                    "is_active": True,
                    "is_admin": True,
                    "role": "admin",
                    "preferences": "{}",
                    "created_at": now,
                    "updated_at": now
                }
            else:
                # 如果不存在role列
                insert_query = text("""
                    INSERT INTO users (
                        id, email, username, hashed_password, full_name, 
                        is_active, is_admin, preferences, 
                        created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :hashed_password, :full_name, 
                        :is_active, :is_admin, :preferences, 
                        :created_at, :updated_at
                    )
                """)
                params = {
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "hashed_password": get_password_hash(password),
                    "full_name": f"{username.capitalize()} Admin",
                    "is_active": True,
                    "is_admin": True,
                    "preferences": "{}",
                    "created_at": now,
                    "updated_at": now
                }
            
            # 执行SQL
            await session.execute(insert_query, params)
            await session.commit()
            logger.info(f"成功创建管理员用户: {username}")
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"创建管理员用户失败: {str(e)}")
            return False
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="创建管理员用户脚本")
    parser.add_argument("--db-url", help="数据库连接URL", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--username", help="管理员用户名", default="admin")
    parser.add_argument("--password", help="管理员密码", default="admin123")
    parser.add_argument("--email", help="管理员邮箱", default="admin@example.com")
    args = parser.parse_args()
    
    # 获取参数
    database_url = args.db_url
    username = args.username
    password = args.password
    email = args.email
    
    logger.info(f"使用数据库连接: {database_url}")
    logger.info(f"准备创建管理员用户: {username} ({email})")
    
    # 创建管理员用户
    success = await create_admin_user(database_url, username, password, email)
    if success:
        logger.info("管理员用户创建或更新成功")
    else:
        logger.error("管理员用户创建失败")

if __name__ == "__main__":
    asyncio.run(main()) 