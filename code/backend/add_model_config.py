#!/usr/bin/env python3
"""
添加模型配置脚本

此脚本用于向数据库添加模型配置信息。

使用方法:
    python add_model_config.py [--db-url DATABASE_URL]

参数:
    --db-url DATABASE_URL  数据库连接URL (默认: postgresql+asyncpg://admin:admin123@localhost:5432/automotive_security)
"""

import asyncio
import argparse
import logging
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 默认数据库连接配置
DEFAULT_DATABASE_URL = "postgresql+asyncpg://admin:admin123@localhost:5432/automotive_security"

async def add_model_config(database_url):
    """添加模型配置到数据库"""
    # 创建异步引擎
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 检查模型是否已存在
            check_query = text("SELECT id FROM model_configs WHERE name = 'qwen3' AND api_base = 'http://172.31.15.200:9997/v1'")
            result = await session.execute(check_query)
            model_exists = result.scalar() is not None
            
            if model_exists:
                logger.info("模型配置已存在，将更新现有配置...")
                update_query = text("""
                    UPDATE model_configs 
                    SET 
                        api_key = :api_key,
                        updated_at = :updated_at
                    WHERE name = 'qwen3' AND api_base = 'http://172.31.15.200:9997/v1'
                """)
                await session.execute(update_query, {
                    "api_key": "sk-1234",
                    "updated_at": datetime.utcnow()
                })
                await session.commit()
                logger.info("成功更新模型配置")
            else:
                logger.info("添加新的模型配置...")
                
                # 获取一个管理员用户ID
                admin_query = text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
                admin_result = await session.execute(admin_query)
                admin_id = admin_result.scalar()
                
                if not admin_id:
                    logger.warning("未找到管理员用户，将使用第一个用户ID")
                    user_query = text("SELECT id FROM users LIMIT 1")
                    user_result = await session.execute(user_query)
                    admin_id = user_result.scalar()
                    
                    if not admin_id:
                        logger.error("未找到任何用户，无法添加模型配置")
                        return False
                
                # 添加模型配置
                insert_query = text("""
                    INSERT INTO model_configs (
                        id, name, description, provider, model_id, api_key, api_base,
                        default_parameters, supports_vision, supports_streaming, 
                        supports_function_calling, is_active, is_default, created_by,
                        created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :provider, :model_id, :api_key, :api_base,
                        :default_parameters, :supports_vision, :supports_streaming,
                        :supports_function_calling, :is_active, :is_default, :created_by,
                        :created_at, :updated_at
                    )
                """)
                
                await session.execute(insert_query, {
                    "id": uuid.uuid4(),
                    "name": "qwen3",
                    "description": "通义千问模型",
                    "provider": "OPENAI",
                    "model_id": "qwen3",
                    "api_key": "sk-1234",
                    "api_base": "http://172.31.15.200:9997/v1",
                    "default_parameters": '{"temperature": 0.7, "max_tokens": 2048}',
                    "supports_vision": False,
                    "supports_streaming": True,
                    "supports_function_calling": True,
                    "is_active": True,
                    "is_default": False,
                    "created_by": admin_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                await session.commit()
                logger.info("成功添加模型配置")
            
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"添加模型配置失败: {str(e)}")
            return False
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="添加模型配置脚本")
    parser.add_argument("--db-url", help="数据库连接URL", default=DEFAULT_DATABASE_URL)
    args = parser.parse_args()
    
    database_url = args.db_url
    logger.info(f"使用数据库连接: {database_url}")
    
    logger.info("开始添加模型配置...")
    success = await add_model_config(database_url)
    if success:
        logger.info("模型配置添加成功完成")
    else:
        logger.error("模型配置添加失败")

if __name__ == "__main__":
    asyncio.run(main()) 