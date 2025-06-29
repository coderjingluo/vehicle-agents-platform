"""
KunlunSec AI Platform - API路由

API路由配置，包含所有API端点。
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    users,
    tasks,
    agents,
    flows,
    tools,
    knowledge,
    mcp,
)

# 创建主API路由器
api_router = APIRouter()

# 添加各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(flows.router, prefix="/flows", tags=["执行流"])
api_router.include_router(tools.router, prefix="/tools", tags=["工具"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP"])