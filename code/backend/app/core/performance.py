"""
性能监控和优化模块
包含数据库查询优化、异步任务队列、API响应压缩等功能
"""

import time
import asyncio
import gzip
import json
from typing import Any, Dict, List, Optional, Callable, Union
from functools import wraps
from datetime import datetime, timedelta
import psutil
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from contextlib import asynccontextmanager
from loguru import logger
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_async_session


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "api_calls": {},
            "database_queries": {},
            "cache_operations": {},
            "task_executions": {},
            "system_resources": {},
        }
        self.start_time = datetime.now()
    
    def record_api_call(self, endpoint: str, method: str, duration: float, status_code: int):
        """记录API调用"""
        key = f"{method}:{endpoint}"
        if key not in self.metrics["api_calls"]:
            self.metrics["api_calls"][key] = {
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "error_count": 0,
            }
        
        metrics = self.metrics["api_calls"][key]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)
        
        if status_code >= 400:
            metrics["error_count"] += 1
    
    def record_database_query(self, query_type: str, duration: float, affected_rows: int = 0):
        """记录数据库查询"""
        if query_type not in self.metrics["database_queries"]:
            self.metrics["database_queries"][query_type] = {
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "total_rows": 0,
            }
        
        metrics = self.metrics["database_queries"][query_type]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]
        metrics["total_rows"] += affected_rows
    
    def get_system_metrics(self) -> Dict:
        """获取系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络IO
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "uptime": (datetime.now() - self.start_time).total_seconds(),
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def get_performance_report(self) -> Dict:
        """生成性能报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.get_system_metrics(),
            "api_metrics": self.metrics["api_calls"],
            "database_metrics": self.metrics["database_queries"],
            "cache_metrics": self.metrics["cache_operations"],
            "task_metrics": self.metrics["task_executions"],
        }


class DatabaseOptimizer:
    """数据库查询优化器"""
    
    @staticmethod
    def optimize_query_with_eager_loading(query, *relationships):
        """使用预加载优化查询"""
        for relationship in relationships:
            if isinstance(relationship, str):
                query = query.options(selectinload(relationship))
            else:
                query = query.options(relationship)
        return query
    
    @staticmethod
    def optimize_query_with_joined_loading(query, *relationships):
        """使用连接加载优化查询"""
        for relationship in relationships:
            if isinstance(relationship, str):
                query = query.options(joinedload(relationship))
            else:
                query = query.options(relationship)
        return query
    
    @staticmethod
    async def execute_batch_operations(session: AsyncSession, operations: List[Callable]):
        """批量执行数据库操作"""
        try:
            for operation in operations:
                if asyncio.iscoroutinefunction(operation):
                    await operation(session)
                else:
                    operation(session)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"批量操作失败: {e}")
            return False
    
    @staticmethod
    async def analyze_slow_queries(min_duration: float = 1.0) -> List[Dict]:
        """分析慢查询"""
        # 这里可以连接到数据库日志或监控系统
        # 返回慢查询分析结果
        return []


class AsyncTaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.workers = []
        self.running = False
        self.task_results = {}
        self.task_status = {}
    
    async def start(self):
        """启动任务队列"""
        if self.running:
            return
        
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        logger.info(f"异步任务队列启动，工作线程数: {self.max_workers}")
    
    async def stop(self):
        """停止任务队列"""
        self.running = False
        
        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()
        
        # 等待所有工作线程结束
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        logger.info("异步任务队列已停止")
    
    async def submit_task(self, task_id: str, coro: Callable, *args, **kwargs) -> str:
        """提交任务"""
        task_info = {
            "id": task_id,
            "coro": coro,
            "args": args,
            "kwargs": kwargs,
            "submitted_at": datetime.now(),
        }
        
        await self.task_queue.put(task_info)
        self.task_status[task_id] = "pending"
        logger.debug(f"任务已提交: {task_id}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        return self.task_status.get(task_id)
    
    async def get_task_result(self, task_id: str) -> Any:
        """获取任务结果"""
        return self.task_results.get(task_id)
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        logger.debug(f"工作线程启动: {worker_name}")
        
        while self.running:
            try:
                # 等待任务
                task_info = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                task_id = task_info["id"]
                coro = task_info["coro"]
                args = task_info["args"]
                kwargs = task_info["kwargs"]
                
                logger.debug(f"开始执行任务: {task_id} (worker: {worker_name})")
                self.task_status[task_id] = "running"
                
                start_time = time.time()
                
                try:
                    # 执行任务
                    if asyncio.iscoroutinefunction(coro):
                        result = await coro(*args, **kwargs)
                    else:
                        result = coro(*args, **kwargs)
                    
                    # 保存结果
                    self.task_results[task_id] = {
                        "status": "completed",
                        "result": result,
                        "duration": time.time() - start_time,
                        "completed_at": datetime.now(),
                    }
                    self.task_status[task_id] = "completed"
                    
                    logger.debug(f"任务执行完成: {task_id}")
                    
                except Exception as e:
                    # 记录错误
                    self.task_results[task_id] = {
                        "status": "failed",
                        "error": str(e),
                        "duration": time.time() - start_time,
                        "completed_at": datetime.now(),
                    }
                    self.task_status[task_id] = "failed"
                    
                    logger.error(f"任务执行失败: {task_id}, 错误: {e}")
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # 超时，继续下一轮循环
                continue
            except asyncio.CancelledError:
                logger.debug(f"工作线程被取消: {worker_name}")
                break
            except Exception as e:
                logger.error(f"工作线程异常: {worker_name}, 错误: {e}")


class ResponseCompressor:
    """响应压缩器"""
    
    @staticmethod
    def should_compress(content_type: str, content_length: int) -> bool:
        """判断是否需要压缩"""
        # 只压缩文本类型的响应
        compressible_types = [
            "application/json",
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/xml",
        ]
        
        # 内容长度大于1KB才压缩
        return (
            any(ct in content_type for ct in compressible_types) 
            and content_length > 1024
        )
    
    @staticmethod
    def compress_response(content: bytes) -> bytes:
        """压缩响应内容"""
        return gzip.compress(content)
    
    @staticmethod
    def create_compressed_response(
        content: Any, 
        status_code: int = 200,
        headers: Optional[Dict] = None
    ) -> Response:
        """创建压缩响应"""
        if headers is None:
            headers = {}
        
        # 序列化内容
        if isinstance(content, (dict, list)):
            content_bytes = json.dumps(content, ensure_ascii=False).encode()
            content_type = "application/json; charset=utf-8"
        else:
            content_bytes = str(content).encode()
            content_type = "text/plain; charset=utf-8"
        
        # 检查是否需要压缩
        if ResponseCompressor.should_compress(content_type, len(content_bytes)):
            compressed_content = ResponseCompressor.compress_response(content_bytes)
            headers["Content-Encoding"] = "gzip"
            headers["Content-Length"] = str(len(compressed_content))
            content_bytes = compressed_content
        
        headers["Content-Type"] = content_type
        
        return Response(
            content=content_bytes,
            status_code=status_code,
            headers=headers
        )


# 装饰器
def monitor_performance(endpoint_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 记录性能指标
                duration = time.time() - start_time
                performance_monitor.record_api_call(
                    endpoint_name, 
                    "unknown", 
                    duration, 
                    200
                )
                
                return result
                
            except Exception as e:
                # 记录错误
                duration = time.time() - start_time
                performance_monitor.record_api_call(
                    endpoint_name, 
                    "unknown", 
                    duration, 
                    500
                )
                raise e
        
        return wrapper
    return decorator


def optimize_database_query(load_relationships: List[str] = None):
    """数据库查询优化装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录查询性能
                duration = time.time() - start_time
                performance_monitor.record_database_query(
                    func.__name__, 
                    duration
                )
                
                return result
                
            except Exception as e:
                logger.error(f"数据库查询失败: {func.__name__}, 错误: {e}")
                raise e
        
        return wrapper
    return decorator


# 连接池管理
@asynccontextmanager
async def get_optimized_db_session():
    """获取优化的数据库会话"""
    async with get_async_session() as session:
        try:
            # 设置查询超时
            await session.execute(text("SET statement_timeout = '30s'"))
            yield session
        except Exception as e:
            await session.rollback()
            raise e


# 全局实例
performance_monitor = PerformanceMonitor()
task_queue = AsyncTaskQueue(max_workers=settings.MAX_ASYNC_WORKERS if hasattr(settings, 'MAX_ASYNC_WORKERS') else 10)
db_optimizer = DatabaseOptimizer()
response_compressor = ResponseCompressor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return performance_monitor 