"""
API v1 主路由
包含所有API v1的子路由
"""

from fastapi import APIRouter

# 这里之后会添加各个模块的路由
# from .endpoints import tasks, agents, knowledge, tools

api_router = APIRouter()

# 临时的基础路由，之后会替换为实际的业务路由
@api_router.get("/")
async def api_root():
    """API根路径"""
    return {
        "message": "车联网安全测试生命周期管理平台 API v1",
        "status": "running",
        "endpoints": {
            "tasks": "/tasks - 任务管理",
            "agents": "/agents - 智能体管理", 
            "knowledge": "/knowledge - 知识库管理",
            "tools": "/tools - 工具管理",
            "models": "/models - 模型配置"
        }
    }

@api_router.get("/status")
async def api_status():
    """API状态检查"""
    return {
        "api_version": "v1",
        "status": "operational",
        "services": {
            "database": "connected",
            "llm_manager": "initialized",
            "tool_registry": "loaded"
        }
    }

# 之后会添加具体的路由：
# api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_router.include_router(agents.router, prefix="/agents", tags=["agents"])  
# api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
# api_router.include_router(tools.router, prefix="/tools", tags=["tools"]) 