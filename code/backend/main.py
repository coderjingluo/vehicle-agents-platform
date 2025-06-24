"""
车联网安全测试生命周期管理平台 - 主应用入口
FastAPI应用程序的主入口点
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import logging

from app.core.config import settings
from app.core.database import init_database, close_database
from app.api.v1.api import api_router


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动车联网安全测试生命周期管理平台...")
    
    try:
        # 初始化数据库
        await init_database()
        logger.info("✅ 数据库初始化完成")
        
        # 这里可以添加其他初始化逻辑
        # - 初始化Redis连接
        # - 初始化Chroma向量数据库
        # - 加载模型配置
        # - 启动后台任务
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
    finally:
        # 关闭时执行
        logger.info("🔄 正在关闭应用...")
        await close_database()
        logger.info("✅ 应用关闭完成")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于多智能体协作的车联网安全测试生命周期管理平台",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间中间件"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}s")
    return response


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "请联系系统管理员" if not settings.debug else str(exc),
            "timestamp": time.time()
        }
    )


@app.get("/")
async def root():
    """根路径 - 系统信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": time.time(),
        "docs": "/docs" if settings.debug else "文档已禁用",
        "api": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version
    }


@app.get("/info")
async def system_info():
    """系统信息端点"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "environment": "development" if settings.debug else "production",
        "features": {
            "tara_agent": "威胁分析与风险评估智能体",
            "testcase_agent": "测试用例生成智能体", 
            "autotest_agent": "自动化测试智能体",
            "report_agent": "报告分析智能体",
            "knowledge_base": "知识库自学习系统",
            "mcp_tools": "MCP工具集成",
            "multi_llm": "多模型支持"
        }
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    # 直接运行时的配置
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    ) 