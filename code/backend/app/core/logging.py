"""
KunlunSec AI Platform - 日志配置

配置应用程序的日志系统，支持文件和控制台输出。
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

def setup_logging():
    """
    设置应用程序日志
    
    返回:
        logger: 配置好的Logger实例
    """
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取根日志记录器
    logger = logging.getLogger("app")
    
    # 设置日志级别
    level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(level)
    
    # 防止重复处理程序
    if logger.handlers:
        return logger
    
    # 创建格式化器
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # 文件处理程序 - 使用RotatingFileHandler进行日志轮转
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理程序
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 设置传播
    logger.propagate = False
    
    return logger

# 预配置的日志记录器
logger = setup_logging() 