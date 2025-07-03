"""
KunlunSec AI Platform - 知识库初始化

这个模块负责知识库系统的初始化。
"""

import os
from app.core.config import settings
from app.core.logging import logger

async def init_knowledge_base():
    """
    初始化知识库系统
    
    此函数将在应用启动时调用，用于初始化向量数据库连接和知识库资源。
    """
    logger.info("正在初始化知识库系统...")
    
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # 确保向量数据库存储目录存在
    vector_db_path = os.path.join(settings.UPLOAD_DIR, "vectordb")
    os.makedirs(vector_db_path, exist_ok=True)
    
    logger.info("知识库系统初始化完成")

