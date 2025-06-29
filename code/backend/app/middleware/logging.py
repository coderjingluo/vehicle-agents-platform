"""
KunlunSec AI Platform - 日志中间件

请求日志记录中间件，记录所有API请求的详细信息。
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有请求的详细信息，包括方法、路径、状态码、处理时间等。
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        
        参数:
            request: 请求对象
            call_next: 下一个处理函数
            
        返回:
            Response: 响应对象
        """
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"
        
        # 记录请求日志
        logger.info(
            f"开始处理请求: {method} {path} "
            f"客户端: {client_host} "
            f"查询参数: {json.dumps(query_params)}"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应日志
            logger.info(
                f"请求完成: {method} {path} "
                f"状态码: {response.status_code} "
                f"处理时间: {process_time:.4f}秒"
            )
            
            # 添加处理时间头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # 记录异常日志
            process_time = time.time() - start_time
            logger.error(
                f"请求异常: {method} {path} "
                f"异常: {str(e)} "
                f"处理时间: {process_time:.4f}秒",
                exc_info=True
            )
            raise 