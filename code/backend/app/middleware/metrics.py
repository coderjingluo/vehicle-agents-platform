"""
KunlunSec AI Platform - 监控指标中间件

Prometheus监控指标中间件，收集API请求的性能指标。
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram, Gauge

# 定义Prometheus指标
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total HTTP Requests Count",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP Request Latency",
    ["method", "endpoint"]
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP Requests In Progress",
    ["method", "endpoint"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus监控指标中间件
    
    收集API请求的性能指标，包括请求计数、延迟和进行中的请求数。
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并收集指标
        
        参数:
            request: 请求对象
            call_next: 下一个处理函数
            
        返回:
            Response: 响应对象
        """
        method = request.method
        path = request.url.path
        
        # 排除指标端点本身
        if path == "/metrics":
            return await call_next(request)
        
        # 规范化路径，移除ID等变量部分
        endpoint = self._normalize_path(path)
        
        # 增加进行中的请求计数
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录请求计数和延迟
            status = response.status_code
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(
                time.time() - start_time
            )
            
            return response
        except Exception as e:
            # 记录异常请求
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            raise
        finally:
            # 减少进行中的请求计数
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_path(self, path: str) -> str:
        """
        规范化路径，将UUID等替换为占位符
        
        参数:
            path: 原始路径
            
        返回:
            str: 规范化后的路径
        """
        import re
        
        # 替换UUID
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            ":id",
            path
        )
        
        # 替换数字ID
        path = re.sub(r"/\d+", "/:id", path)
        
        return path 