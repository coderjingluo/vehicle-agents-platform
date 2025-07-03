"""
MCP API端点

提供MCP服务器和工具管理的API接口
"""

import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.tool import MCPConnection, MCPTool
from app.tool.tool_collection import get_global_tool_collection, register_mcp_tool, register_mcp_tool_sse
from pydantic import BaseModel, Field

router = APIRouter()


class RegisterMCPToolRequest(BaseModel):
    """注册MCP工具请求"""
    command: str = Field(..., description="MCP服务器命令")
    args: List[str] = Field(default_factory=list, description="命令参数")
    server_id: str = Field("", description="服务器标识符")


class RegisterMCPToolSSERequest(BaseModel):
    """通过SSE注册MCP工具请求"""
    server_url: str = Field(..., description="MCP服务器URL")
    server_id: str = Field("", description="服务器标识符")


class MCPToolResponse(BaseModel):
    """MCP工具响应"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


@router.post(
    "/connections",
    status_code=status.HTTP_201_CREATED,
    summary="创建MCP连接"
)
async def create_mcp_connection(
    connection_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的MCP连接
    """
    try:
        # 调用MCP服务创建连接
        from app.services.mcp_service import MCPService
        mcp_service = MCPService(db)
        
        connection = await mcp_service.create_connection(
            name=connection_data["name"],
            connection_type=connection_data["type"],
            url=connection_data["url"],
            description=connection_data.get("description", "")
        )
        
        return {
            "success": True,
            "data": {
                "id": connection.id,
                "name": connection.name,
                "type": connection.connection_type,
                "url": connection.url,
                "description": connection.description,
                "status": connection.status,
                "tools": []
            },
            "message": "MCP连接创建成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/connections",
    summary="获取MCP连接列表"
)
async def get_mcp_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有MCP连接列表
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    connections = await mcp_service.list_connections()
    
    connection_list = []
    for conn in connections:
        # 获取连接的工具数量
        tool_count = await mcp_service.get_tool_count(conn.id)
        
        connection_list.append({
            "id": conn.id,
            "name": conn.name,
            "type": conn.connection_type,
            "url": conn.url,
            "description": conn.description,
            "status": conn.status,
            "last_heartbeat": conn.last_heartbeat,
            "tool_count": tool_count
        })
    
    return {
        "success": True,
        "data": {
            "connections": connection_list
        },
        "message": "获取MCP连接列表成功"
    }


@router.get(
    "/connections/{conn_id}",
    summary="获取MCP连接详情"
)
async def get_mcp_connection_detail(
    conn_id: str = Path(..., description="连接ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取MCP连接详细信息，包括可用工具
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    connection = await mcp_service.get_connection(conn_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP连接不存在"
        )
    
    # 获取连接的工具列表
    tools = await mcp_service.list_tools(conn_id)
    
    tool_list = []
    for tool in tools:
        tool_list.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        })
    
    return {
        "success": True,
        "data": {
            "id": connection.id,
            "name": connection.name,
            "type": connection.connection_type,
            "url": connection.url,
            "description": connection.description,
            "status": connection.status,
            "last_heartbeat": connection.last_heartbeat,
            "tools": tool_list
        },
        "message": "获取MCP连接详情成功"
    }


@router.delete(
    "/connections/{conn_id}",
    summary="删除MCP连接"
)
async def delete_mcp_connection(
    conn_id: str = Path(..., description="连接ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定的MCP连接
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    result = await mcp_service.delete_connection(conn_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP连接不存在"
        )
    
    return {
        "success": True,
        "data": None,
        "message": "MCP连接删除成功"
    }


# MCP服务器管理API

@router.get(
    "/servers",
    summary="获取所有MCP服务器"
)
async def get_mcp_servers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取系统中所有已配置的MCP服务器
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    servers = await mcp_service.list_servers()
    
    return {
        "status": "success",
        "data": {
            "servers": servers
        }
    }


@router.post(
    "/servers/connect",
    summary="连接MCP服务器"
)
async def connect_mcp_server(
    server_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    连接到指定的MCP服务器
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    server_id = server_data.get("server_id")
    if not server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供server_id"
        )
    
    result = await mcp_service.connect_server(server_id)
    
    return {
        "status": "success",
        "data": {
            "server_id": server_id,
            "connection_status": result["status"],
            "connected_at": result.get("connected_at")
        }
    }


@router.post(
    "/servers/disconnect",
    summary="断开MCP服务器"
)
async def disconnect_mcp_server(
    server_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    断开与指定MCP服务器的连接
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    server_id = server_data.get("server_id")
    if not server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供server_id"
        )
    
    result = await mcp_service.disconnect_server(server_id)
    
    return {
        "status": "success",
        "data": {
            "server_id": server_id,
            "connection_status": "disconnected",
            "disconnected_at": result.get("disconnected_at")
        }
    }


@router.post(
    "/servers",
    summary="添加MCP服务器配置"
)
async def add_mcp_server(
    server_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    添加新的MCP服务器配置
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    required_fields = ["id", "name", "type"]
    for field in required_fields:
        if field not in server_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )
    
    result = await mcp_service.add_server_config(
        server_id=server_data["id"],
        name=server_data["name"],
        server_type=server_data["type"],
        url=server_data.get("url"),
        command=server_data.get("command"),
        auto_connect=server_data.get("auto_connect", False)
    )
    
    return {
        "status": "success",
        "data": result
    }


@router.delete(
    "/servers/{server_id}",
    summary="删除MCP服务器配置"
)
async def delete_mcp_server(
    server_id: str = Path(..., description="服务器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定的MCP服务器配置
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    result = await mcp_service.delete_server_config(server_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP服务器配置不存在"
        )
    
    return {
        "status": "success",
        "data": {
            "message": "MCP服务器配置已删除"
        }
    }


# MCP工具管理API

@router.get(
    "/tools",
    summary="获取可用工具列表"
)
async def get_mcp_tools(
    server_id: Optional[str] = Query(None, description="服务器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有已连接MCP服务器上的可用工具
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    tools = await mcp_service.list_all_tools(server_id)
    
    return {
        "status": "success",
        "data": {
            "tools": tools
        }
    }


@router.post(
    "/tools/execute",
    summary="调用MCP工具"
)
async def execute_mcp_tool(
    tool_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    调用指定的MCP工具
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    required_fields = ["tool_name", "server_id", "parameters"]
    for field in required_fields:
        if field not in tool_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )
    
    try:
        result = await mcp_service.execute_tool(
            tool_name=tool_data["tool_name"],
            server_id=tool_data["server_id"],
            parameters=tool_data["parameters"]
        )
        
        return {
            "status": "success",
            "data": {
                "tool_name": tool_data["tool_name"],
                "server_id": tool_data["server_id"],
                "execution_id": result.get("execution_id"),
                "result": result.get("result")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"工具执行失败: {str(e)}"
        )


@router.get(
    "/tools/history",
    summary="获取工具执行历史"
)
async def get_tool_execution_history(
    tool_name: Optional[str] = Query(None, description="工具名称"),
    server_id: Optional[str] = Query(None, description="服务器ID"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页条目数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取MCP工具调用历史记录
    """
    from app.services.mcp_service import MCPService
    mcp_service = MCPService(db)
    
    history, total = await mcp_service.get_tool_execution_history(
        tool_name=tool_name,
        server_id=server_id,
        page=page,
        limit=limit
    )
    
    pages = (total + limit - 1) // limit
    
    return {
        "status": "success",
        "data": {
            "history": history,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }
        }
    } 


@router.post("/mcp/tools", status_code=status.HTTP_201_CREATED)
async def register_mcp_tool_endpoint(request: RegisterMCPToolRequest):
    """
    注册MCP工具
    """
    try:
        success = await register_mcp_tool(
            command=request.command,
            args=request.args,
            server_id=request.server_id
        )
        
        if success:
            # 获取注册的工具列表
            tool_collection = get_global_tool_collection()
            tools = tool_collection.get_tools()
            
            return {
                "success": True,
                "message": "MCP工具注册成功",
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                    for tool in tools if hasattr(tool, "server_id") and tool.server_id == request.server_id
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MCP工具注册失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP工具注册失败: {str(e)}"
        )


@router.post("/mcp/tools/sse", status_code=status.HTTP_201_CREATED)
async def register_mcp_tool_sse_endpoint(request: RegisterMCPToolSSERequest):
    """
    通过SSE注册MCP工具
    """
    try:
        success = await register_mcp_tool_sse(
            server_url=request.server_url,
            server_id=request.server_id
        )
        
        if success:
            # 获取注册的工具列表
            tool_collection = get_global_tool_collection()
            tools = tool_collection.get_tools()
            
            return {
                "success": True,
                "message": "MCP工具通过SSE注册成功",
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                    for tool in tools if hasattr(tool, "server_id") and tool.server_id == request.server_id
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MCP工具通过SSE注册失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP工具通过SSE注册失败: {str(e)}"
        )


@router.get("/mcp/tools", response_model=List[MCPToolResponse])
async def list_mcp_tools():
    """
    列出所有MCP工具
    """
    try:
        tool_collection = get_global_tool_collection()
        tools = tool_collection.get_tools()
        
        # 过滤出MCP工具
        mcp_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in tools if hasattr(tool, "server_id") and tool.server_id
        ]
        
        return mcp_tools
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取MCP工具列表失败: {str(e)}"
        )


@router.delete("/mcp/tools/{server_id}", status_code=status.HTTP_200_OK)
async def disconnect_mcp_server(server_id: str):
    """
    断开与MCP服务器的连接
    """
    try:
        tool_collection = get_global_tool_collection()
        
        if hasattr(tool_collection, "mcp_clients"):
            await tool_collection.mcp_clients.disconnect(server_id)
            
            # 移除相关工具
            tools_to_remove = []
            for tool_name, tool in tool_collection.tool_map.items():
                if hasattr(tool, "server_id") and tool.server_id == server_id:
                    tools_to_remove.append(tool_name)
            
            for tool_name in tools_to_remove:
                tool_collection.remove_tool(tool_name)
            
            return {
                "success": True,
                "message": f"已断开与MCP服务器 {server_id} 的连接"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP客户端未初始化"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"断开MCP服务器连接失败: {str(e)}"
        ) 