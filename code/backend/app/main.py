"""
KunlunSec AI Platform - 主应用程序入口

这个文件创建并配置FastAPI应用程序，包括中间件、路由和事件处理。
"""

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import create_db_and_tables
from app.api.api_v1.api import api_router
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.metrics import PrometheusMiddleware
from app.core.security import get_current_active_user

# 设置日志
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理
    """
    # 启动前执行
    logger.info("应用程序启动中...")
    
    # 创建数据库表
    await create_db_and_tables()
    
    # 初始化知识库
    from app.knowledge.init import init_knowledge_base
    await init_knowledge_base()
    
    # 初始化MCP系统
    from app.mcp.server import init_mcp_server
    await init_mcp_server()
    
    logger.info(f"应用程序已启动 - {settings.APP_NAME} v{settings.APP_VERSION}")
    
    yield
    
    # 关闭前执行
    logger.info("应用程序关闭中...")
    
    # 关闭MCP连接
    from app.mcp.server import shutdown_mcp_server
    await shutdown_mcp_server()
    
    # 关闭数据库连接
    from app.db.session import close_db_connections
    await close_db_connections()
    
    logger.info("应用程序已关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="车联网安全测试生命周期管理平台API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 添加Prometheus监控中间件（如果启用）
if settings.ENABLE_PROMETHEUS:
    app.add_middleware(PrometheusMiddleware)
    
    # 添加Prometheus指标端点
    from app.api.endpoints.metrics import metrics_router
    app.include_router(metrics_router)

# 添加API路由
app.include_router(api_router, prefix="/api/v1")

# 健康检查端点
@app.get("/api/v1/health", tags=["健康检查"])
async def health_check():
    """
    系统健康检查端点
    """
    return {"status": "ok", "version": settings.APP_VERSION}

# WebSocket路由
from app.api.endpoints.ws import ws_router
app.include_router(ws_router)

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理
    """
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误", "message": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    ) 