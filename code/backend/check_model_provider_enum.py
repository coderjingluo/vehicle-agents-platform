#!/usr/bin/env python3
"""
检查数据库中ModelProvider枚举值

此脚本用于检查数据库中ModelProvider枚举类型的有效值。
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

async def check_enum_values(database_url):
    """检查ModelProvider枚举值"""
    # 创建异步引擎
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 查询枚举类型
            query = text("""
                SELECT e.enumlabel
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'modelprovider'
                ORDER BY e.enumsortorder
            """)
            
            result = await session.execute(query)
            enum_values = [row[0] for row in result]
            
            logger.info(f"ModelProvider枚举的有效值: {enum_values}")
            return enum_values
        except Exception as e:
            logger.error(f"查询枚举值失败: {str(e)}")
            return []
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="检查ModelProvider枚举值")
    parser.add_argument("--db-url", help="数据库连接URL", default=DEFAULT_DATABASE_URL)
    args = parser.parse_args()
    
    database_url = args.db_url
    logger.info(f"使用数据库连接: {database_url}")
    
    logger.info("开始查询枚举值...")
    enum_values = await check_enum_values(database_url)
    if enum_values:
        logger.info(f"查询完成，找到 {len(enum_values)} 个有效值")
    else:
        logger.error("查询失败或未找到有效值")

if __name__ == "__main__":
    asyncio.run(main()) 