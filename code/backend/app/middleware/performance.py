"""
FastAPI性能优化中间件
集成缓存、压缩、监控等功能
"""

import time
import gzip
import json
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from loguru import logger
import asyncio

from app.core.cache import cache_manager
from app.core.performance import (
    performance_monitor, 
    task_queue, 
    response_compressor
)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能优化中间件"""
    
    def __init__(self, app, enable_compression: bool = True, enable_caching: bool = True):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.enable_caching = enable_caching
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()
        
        # 生成请求ID
        request_id = f"{int(start_time * 1000)}-{id(request)}"
        request.state.request_id = request_id
        
        try:
            # 检查缓存
            if self.enable_caching and request.method == "GET":
                cached_response = await self._check_cache(request)
                if cached_response:
                    await self._record_performance(
                        request, 
                        None, 
                        time.time() - start_time, 
                        200, 
                        cache_hit=True
                    )
                    return cached_response
            
            # 处理请求
            response = await call_next(request)
            
            # 记录性能指标
            duration = time.time() - start_time
            await self._record_performance(request, response, duration, response.status_code)
            
            # 应用优化
            if self.enable_compression:
                response = await self._apply_compression(request, response)
            
            if self.enable_caching and request.method == "GET" and response.status_code == 200:
                await self._cache_response(request, response)
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            await self._record_performance(
                request, 
                None, 
                duration, 
                500, 
                error=str(e)
            )
            raise e
    
    async def _check_cache(self, request: Request) -> Optional[Response]:
        """检查缓存"""
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await cache_manager.get(cache_key)
            
            if cached_data:
                return JSONResponse(
                    content=cached_data,
                    headers={"X-Cache": "HIT"}
                )
            
        except Exception as e:
            logger.error(f"缓存检查失败: {e}")
        
        return None
    
    async def _cache_response(self, request: Request, response: Response):
        """缓存响应"""
        try:
            # 只缓存JSON响应
            if response.headers.get("content-type", "").startswith("application/json"):
                cache_key = self._generate_cache_key(request)
                
                # 读取响应体
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # 解析JSON数据
                response_data = json.loads(body.decode())
                
                # 缓存数据
                ttl = self._get_cache_ttl(request.url.path)
                await cache_manager.set(cache_key, response_data, ttl)
                
                # 重建响应
                response.body_iterator = self._generate_body_iterator(body)
                
        except Exception as e:
            logger.error(f"缓存响应失败: {e}")
    
    async def _apply_compression(self, request: Request, response: Response) -> Response:
        """应用压缩"""
        try:
            # 检查客户端是否支持gzip
            accept_encoding = request.headers.get("accept-encoding", "")
            if "gzip" not in accept_encoding:
                return response
            
            content_type = response.headers.get("content-type", "")
            content_length = int(response.headers.get("content-length", "0"))
            
            # 检查是否需要压缩
            if not response_compressor.should_compress(content_type, content_length):
                return response
            
            # 读取响应体
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # 压缩内容
            compressed_body = response_compressor.compress_response(body)
            
            # 更新响应头
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed_body))
            response.headers["Vary"] = "Accept-Encoding"
            
            # 重建响应
            response.body_iterator = self._generate_body_iterator(compressed_body)
            
        except Exception as e:
            logger.error(f"响应压缩失败: {e}")
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 包含路径、查询参数、用户信息等
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("authorization", "anonymous")[:10]  # 用户标识
        ]
        return f"api_cache:{'|'.join(key_parts)}"
    
    def _get_cache_ttl(self, path: str) -> int:
        """获取缓存TTL"""
        # 根据不同路径设置不同的缓存时间
        if path.startswith("/api/v1/health"):
            return 60  # 健康检查缓存1分钟
        elif path.startswith("/api/v1/models"):
            return 300  # 模型信息缓存5分钟
        elif path.startswith("/api/v1/knowledge-bases"):
            return 600  # 知识库信息缓存10分钟
        else:
            return 180  # 默认缓存3分钟
    
    async def _generate_body_iterator(self, body: bytes):
        """生成响应体迭代器"""
        yield body
    
    async def _record_performance(
        self, 
        request: Request, 
        response: Optional[Response], 
        duration: float, 
        status_code: int,
        cache_hit: bool = False,
        error: Optional[str] = None
    ):
        """记录性能指标"""
        try:
            performance_monitor.record_api_call(
                request.url.path,
                request.method,
                duration,
                status_code
            )
            
            # 记录详细信息
            logger.debug(
                f"API调用: {request.method} {request.url.path} "
                f"状态:{status_code} 耗时:{duration:.3f}s "
                f"缓存:{'HIT' if cache_hit else 'MISS'}"
            )
            
            # 记录慢请求
            if duration > 2.0:  # 超过2秒的请求
                logger.warning(
                    f"慢请求检测: {request.method} {request.url.path} "
                    f"耗时:{duration:.3f}s"
                )
            
            # 记录错误
            if error:
                logger.error(f"请求处理错误: {error}")
                
        except Exception as e:
            logger.error(f"性能记录失败: {e}")


class AsyncTaskMiddleware(BaseHTTPMiddleware):
    """异步任务中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 确保任务队列已启动
        if not task_queue.running:
            await task_queue.start()
        
        # 处理请求
        response = await call_next(request)
        
        return response


class DatabaseConnectionMiddleware(BaseHTTPMiddleware):
    """数据库连接优化中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 在请求开始时可以进行连接池预热等操作
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录数据库相关的性能指标
        if hasattr(request.state, 'db_queries'):
            query_count = len(request.state.db_queries)
            if query_count > 10:
                logger.warning(f"请求包含过多数据库查询: {query_count} 个查询")
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = request.client.host
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 检查限流
        if self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests per {self.window_seconds} seconds"
                },
                headers={
                    "Retry-After": str(self.window_seconds)
                }
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加限流头
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期记录"""
        expired_ips = []
        for ip, timestamps in self.request_counts.items():
            # 移除过期的时间戳
            self.request_counts[ip] = [
                ts for ts in timestamps 
                if current_time - ts < self.window_seconds
            ]
            
            # 如果没有有效记录，标记为删除
            if not self.request_counts[ip]:
                expired_ips.append(ip)
        
        # 删除过期IP记录
        for ip in expired_ips:
            del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否被限流"""
        if client_ip not in self.request_counts:
            return False
        
        valid_requests = [
            ts for ts in self.request_counts[client_ip]
            if current_time - ts < self.window_seconds
        ]
        
        return len(valid_requests) >= self.max_requests
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """获取剩余请求数"""
        if client_ip not in self.request_counts:
            return self.max_requests
        
        valid_requests = [
            ts for ts in self.request_counts[client_ip]
            if current_time - ts < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(valid_requests))


# 中间件工厂函数
def create_performance_middleware(
    enable_compression: bool = True,
    enable_caching: bool = True,
    enable_rate_limit: bool = True,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """创建性能优化中间件组合"""
    middlewares = []
    
    # 安全头中间件（最外层）
    middlewares.append(SecurityHeadersMiddleware)
    
    # 限流中间件
    if enable_rate_limit:
        middlewares.append(
            lambda app: RateLimitMiddleware(
                app, 
                max_requests=max_requests, 
                window_seconds=window_seconds
            )
        )
    
    # 性能优化中间件
    middlewares.append(
        lambda app: PerformanceMiddleware(
            app,
            enable_compression=enable_compression,
            enable_caching=enable_caching
        )
    )
    
    # 异步任务中间件
    middlewares.append(AsyncTaskMiddleware)
    
    # 数据库连接中间件
    middlewares.append(DatabaseConnectionMiddleware)
    
    return middlewares 