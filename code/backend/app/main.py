"""
FastAPI主应用
集成Phase 5性能优化功能
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.cache import cache_manager
from app.core.performance import performance_monitor, task_queue
from app.middleware.performance import create_performance_middleware
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动车联网安全测试生命周期管理平台...")
    
    try:
        # 初始化缓存管理器
        await cache_manager.initialize()
        logger.info("✅ 缓存管理器初始化完成")
        
        # 启动异步任务队列
        await task_queue.start()
        logger.info("✅ 异步任务队列启动完成")
        
        # 初始化性能监控
        performance_monitor.init() if hasattr(performance_monitor, 'init') else None
        logger.info("✅ 性能监控初始化完成")
        
        logger.info("🎉 平台启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise e
    
    yield
    
    # 关闭时清理
    logger.info("🔄 正在关闭应用...")
    
    try:
        # 停止异步任务队列
        await task_queue.stop()
        logger.info("✅ 异步任务队列已停止")
        
        # 关闭缓存连接
        await cache_manager.close()
        logger.info("✅ 缓存连接已关闭")
        
        logger.info("👋 应用已安全关闭")
        
    except Exception as e:
        logger.error(f"❌ 关闭过程中出现错误: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="车联网安全测试生命周期管理平台",
    description="基于LangGraph的多智能体协作平台，提供TARA分析、测试用例生成、自动化测试、报告分析等功能",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加性能优化中间件
performance_middlewares = create_performance_middleware(
    enable_compression=True,
    enable_caching=True,
    enable_rate_limit=True,
    max_requests=100,
    window_seconds=60
)

for middleware in performance_middlewares:
    app.add_middleware(middleware)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """系统健康检查"""
    try:
        # 检查各组件状态
        health_status = {
            "status": "healthy",
            "timestamp": performance_monitor.start_time.isoformat() if hasattr(performance_monitor, 'start_time') else None,
            "components": {
                "cache": "healthy" if cache_manager.redis_client else "unavailable",
                "task_queue": "running" if task_queue.running else "stopped",
                "performance_monitor": "active"
            },
            "metrics": await get_system_metrics()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# 性能指标端点
@app.get("/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    try:
        return {
            "performance": performance_monitor.get_performance_report(),
            "cache": await cache_manager.get_cache_stats(),
            "task_queue": {
                "running": task_queue.running,
                "workers": len(task_queue.workers),
                "queue_size": task_queue.task_queue.qsize(),
                "completed_tasks": len(task_queue.task_results),
            }
        }
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


async def get_system_metrics():
    """获取系统指标"""
    try:
        return performance_monitor.get_system_metrics()
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return {}


# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 静态文件服务（如果需要）
# app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境启动配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        # 性能优化配置
        loop="uvloop",  # 使用更快的事件循环
        http="httptools",  # 使用更快的HTTP解析器
        workers=1,  # 开发环境使用单个工作进程
        # 生产环境建议配置
        # workers=multiprocessing.cpu_count(),
        # ssl_keyfile="path/to/keyfile",
        # ssl_certfile="path/to/certfile",
    ) 