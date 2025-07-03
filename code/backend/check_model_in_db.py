#!/usr/bin/env python3
"""
检查数据库中是否存在qwen3模型

此脚本用于检查数据库中是否存在qwen3模型配置。
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

async def check_model_exists(database_url):
    """检查qwen3模型是否存在"""
    # 创建异步引擎
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 查询模型
            query = text("""
                SELECT id, name, description, provider, model_id, api_base, api_key
                FROM model_configs
                WHERE name = 'qwen3'
            """)
            
            result = await session.execute(query)
            models = [dict(zip(['id', 'name', 'description', 'provider', 'model_id', 'api_base', 'api_key'], row)) for row in result]
            
            if models:
                logger.info(f"找到 {len(models)} 个qwen3模型配置:")
                for model in models:
                    # 隐藏API密钥的大部分内容
                    if model['api_key']:
                        key = model['api_key']
                        model['api_key'] = key[:4] + '*' * (len(key) - 8) + key[-4:] if len(key) > 8 else '****'
                    logger.info(f"  - ID: {model['id']}")
                    logger.info(f"    名称: {model['name']}")
                    logger.info(f"    描述: {model['description']}")
                    logger.info(f"    提供商: {model['provider']}")
                    logger.info(f"    模型ID: {model['model_id']}")
                    logger.info(f"    API基础URL: {model['api_base']}")
                    logger.info(f"    API密钥: {model['api_key']}")
                return True
            else:
                logger.warning("未找到qwen3模型配置")
                return False
        except Exception as e:
            logger.error(f"查询模型失败: {str(e)}")
            return False
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="检查qwen3模型是否存在")
    parser.add_argument("--db-url", help="数据库连接URL", default=DEFAULT_DATABASE_URL)
    args = parser.parse_args()
    
    database_url = args.db_url
    logger.info(f"使用数据库连接: {database_url}")
    
    logger.info("开始查询模型...")
    exists = await check_model_exists(database_url)
    if exists:
        logger.info("查询完成，找到qwen3模型配置")
    else:
        logger.error("查询完成，未找到qwen3模型配置")

if __name__ == "__main__":
    asyncio.run(main()) 