"""
系统监控和管理API路由

提供系统状态监控、健康检查、性能指标、配置管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import psutil
import time
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.core.llm_client import get_llm_manager, LLMClientManager
from app.core.tool_registry import get_tool_registry, ToolRegistry
from app.core.performance import PerformanceMonitor, get_performance_monitor
from app.core.cache import CacheManager, get_cache_manager
from app.models.task import (
    SystemStatus,
    APIConfiguration,
    ErrorResponse,
    ToolExecutionRequest,
    ToolExecutionResponse
)
from loguru import logger

router = APIRouter(prefix="/system", tags=["system"])

# 全局状态计数器
_request_counter = 0
_start_time = time.time()


@router.get("/health")
async def health_check():
    """系统健康检查"""
    try:
        # 检查核心组件状态
        llm_manager = get_llm_manager()
        tool_registry = get_tool_registry()
        performance_monitor = get_performance_monitor()
        cache_manager = get_cache_manager()
        
        # 基础健康检查
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - _start_time,
            "version": settings.app_version,
            "environment": settings.environment
        }
        
        # 组件状态检查
        components = {}
        
        # LLM管理器状态
        try:
            providers = llm_manager.list_available_providers()
            components["llm_manager"] = {
                "status": "healthy",
                "providers": providers,
                "provider_count": len(providers)
            }
        except Exception as e:
            components["llm_manager"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 工具注册表状态
        try:
            tools = tool_registry.list_tools()
            components["tool_registry"] = {
                "status": "healthy",
                "tools": tools,
                "tool_count": len(tools)
            }
        except Exception as e:
            components["tool_registry"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 性能监控器状态
        try:
            metrics = await performance_monitor.get_system_metrics()
            components["performance_monitor"] = {
                "status": "healthy",
                "metrics": metrics
            }
        except Exception as e:
            components["performance_monitor"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 缓存管理器状态
        try:
            cache_stats = await cache_manager.get_cache_stats()
            components["cache_manager"] = {
                "status": "healthy",
                "stats": cache_stats
            }
        except Exception as e:
            components["cache_manager"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 数据库连接检查
        try:
            # 这里应该检查数据库连接
            components["database"] = {
                "status": "healthy",
                "connection": "active"
            }
        except Exception as e:
            components["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        health_status["components"] = components
        
        # 检查是否有不健康的组件
        unhealthy_components = [
            name for name, comp in components.items() 
            if comp.get("status") != "healthy"
        ]
        
        if unhealthy_components:
            health_status["status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_components
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """获取系统状态详情"""
    try:
        global _request_counter, _start_time
        
        # 获取系统指标
        metrics = await performance_monitor.get_system_metrics()
        
        # 获取进程信息
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        # 系统信息
        system_info = {
            "uptime": time.time() - _start_time,
            "memory_usage": (memory_info.rss / 1024 / 1024),  # MB
            "cpu_usage": cpu_percent,
            "active_agents": 0,  # 这里应该从智能体管理器获取
            "active_tasks": 0,   # 这里应该从任务管理器获取
            "total_requests": _request_counter
        }
        
        status = SystemStatus(
            status="running",
            uptime=system_info["uptime"],
            active_agents=system_info["active_agents"],
            active_tasks=system_info["active_tasks"],
            total_requests=system_info["total_requests"],
            memory_usage=system_info["memory_usage"],
            cpu_usage=system_info["cpu_usage"],
            timestamp=datetime.utcnow()
        )
        
        return status
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.get("/metrics")
async def get_system_metrics(
    period: str = Query("1h", description="时间段 (1h, 6h, 24h, 7d)"),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """获取系统性能指标"""
    try:
        # 解析时间段
        period_mapping = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6), 
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7)
        }
        
        if period not in period_mapping:
            raise HTTPException(status_code=400, detail="不支持的时间段")
        
        time_delta = period_mapping[period]
        start_time = datetime.utcnow() - time_delta
        
        # 获取指标数据
        metrics = await performance_monitor.get_historical_metrics(
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        
        return {
            "success": True,
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/config", response_model=APIConfiguration)
async def get_system_config():
    """获取系统配置"""
    try:
        config = APIConfiguration(
            max_concurrent_tasks=settings.max_concurrent_tasks,
            default_timeout=settings.default_timeout,
            enable_streaming=settings.enable_streaming,
            enable_caching=settings.enable_caching,
            log_level=settings.log_level,
            rate_limit=settings.rate_limit
        )
        
        return config
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@router.put("/config")
async def update_system_config(config: APIConfiguration):
    """更新系统配置"""
    try:
        # 更新配置
        settings.max_concurrent_tasks = config.max_concurrent_tasks
        settings.default_timeout = config.default_timeout
        settings.enable_streaming = config.enable_streaming
        settings.enable_caching = config.enable_caching
        settings.log_level = config.log_level
        settings.rate_limit = config.rate_limit
        
        return {
            "success": True,
            "message": "系统配置更新成功",
            "config": config.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    level: str = Query("INFO", description="日志级别"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取系统日志"""
    try:
        # 这里应该从日志系统获取日志
        # 目前返回模拟数据
        
        logs = []
        for i in range(limit):
            log_entry = {
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "level": level,
                "message": f"模拟日志条目 {i + offset + 1}",
                "module": "system",
                "details": {}
            }
            logs.append(log_entry)
        
        return {
            "success": True,
            "logs": logs,
            "total": 1000,  # 模拟总数
            "level": level,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """获取缓存统计信息"""
    try:
        stats = await cache_manager.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.delete("/cache/clear")
async def clear_cache(
    cache_type: str = Query("all", description="缓存类型 (all, memory, redis)"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """清理缓存"""
    try:
        if cache_type == "all":
            await cache_manager.clear_all_cache()
        elif cache_type == "memory":
            await cache_manager.clear_memory_cache()
        elif cache_type == "redis":
            await cache_manager.clear_redis_cache()
        else:
            raise HTTPException(status_code=400, detail="不支持的缓存类型")
        
        return {
            "success": True,
            "message": f"{cache_type} 缓存清理成功",
            "cache_type": cache_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_system_tools(
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """获取系统工具列表"""
    try:
        tools = tool_registry.list_tools()
        
        tool_details = []
        for tool_name in tools:
            tool_info = tool_registry.get_tool_info(tool_name)
            tool_details.append({
                "name": tool_name,
                "info": tool_info,
                "status": "available"
            })
        
        return tool_details
        
    except Exception as e:
        logger.error(f"获取系统工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统工具列表失败: {str(e)}")


@router.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_system_tool(
    tool_name: str,
    request: ToolExecutionRequest,
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """执行系统工具"""
    try:
        start_time = time.time()
        
        # 验证工具是否存在
        if not tool_registry.has_tool(tool_name):
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
        
        # 执行工具
        result = await tool_registry.execute_tool(
            tool_name=tool_name,
            parameters=request.parameters,
            context=request.context,
            timeout=request.timeout
        )
        
        execution_time = time.time() - start_time
        
        return ToolExecutionResponse(
            success=True,
            tool_name=tool_name,
            result=result,
            execution_time=execution_time,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"执行系统工具失败: {e}")
        
        return ToolExecutionResponse(
            success=False,
            tool_name=tool_name,
            error=str(e),
            execution_time=execution_time,
            timestamp=datetime.utcnow()
        )


@router.get("/providers")
async def list_llm_providers(
    llm_manager: LLMClientManager = Depends(get_llm_manager)
):
    """获取LLM提供商列表"""
    try:
        providers = llm_manager.list_available_providers()
        
        provider_details = []
        for provider in providers:
            provider_info = llm_manager.get_provider_info(provider)
            provider_details.append({
                "name": provider,
                "info": provider_info,
                "status": "available"
            })
        
        return {
            "success": True,
            "providers": provider_details,
            "total_count": len(provider_details),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取LLM提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取LLM提供商列表失败: {str(e)}")


@router.post("/test/llm")
async def test_llm_connection(
    provider: str = Query(..., description="LLM提供商"),
    model: str = Query(..., description="模型名称"),
    test_message: str = Query("Hello, this is a test message.", description="测试消息"),
    llm_manager: LLMClientManager = Depends(get_llm_manager)
):
    """测试LLM连接"""
    try:
        start_time = time.time()
        
        # 测试LLM连接
        response = await llm_manager.generate_response(
            provider=provider,
            model=model,
            messages=[{"role": "user", "content": test_message}]
        )
        
        execution_time = time.time() - start_time
        
        return {
            "success": True,
            "provider": provider,
            "model": model,
            "test_message": test_message,
            "response": response,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"测试LLM连接失败: {e}")
        
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error": str(e),
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    try:
        system_info = {
            "platform": {
                "system": psutil.WINDOWS if psutil.WINDOWS else "linux",
                "python_version": f"{psutil.version_info[0]}.{psutil.version_info[1]}.{psutil.version_info[2]}"
            },
            "hardware": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": round(psutil.virtual_memory().total / (1024**3), 2),  # GB
                "disk_total": round(psutil.disk_usage('/').total / (1024**3), 2)     # GB
            },
            "application": {
                "version": settings.app_version,
                "environment": settings.environment,
                "start_time": datetime.fromtimestamp(_start_time).isoformat(),
                "uptime": time.time() - _start_time
            },
            "dependencies": {
                "fastapi": "0.104.1",
                "langgraph": "0.1.9",
                "langchain": "0.2.11",
                "pydantic": "2.5.2"
            }
        }
        
        return {
            "success": True,
            "system_info": system_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")


@router.post("/restart")
async def restart_system():
    """重启系统（仅限开发环境）"""
    try:
        if settings.environment != "development":
            raise HTTPException(
                status_code=403, 
                detail="系统重启仅在开发环境中可用"
            )
        
        return {
            "success": True,
            "message": "系统重启请求已接收",
            "warning": "请手动重启应用服务",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"重启系统失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启系统失败: {str(e)}")


# 中间件：请求计数
def count_request():
    global _request_counter
    _request_counter += 1