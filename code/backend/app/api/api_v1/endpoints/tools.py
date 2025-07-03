"""
工具管理API端点

提供工具管理相关的API接口，包括注册、获取和执行工具
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.tool import Tool
from app.tool.tool_collection import get_global_tool_collection

router = APIRouter()


@router.get(
    "/",
    summary="获取工具列表"
)
async def get_tools(
    tool_type: Optional[str] = Query(None, description="工具类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取工具列表
    """
    try:
        # 获取实际的工具集合
        tool_collection = get_global_tool_collection()
        tools = list(tool_collection.tools)
        
        # 转换为API格式
        tool_list = []
        for tool in tools:
            # 确定工具类型
            current_type = "system"  # 默认类型
            if hasattr(tool, "tool_type"):
                current_type = tool.tool_type
            elif "browser" in tool.__class__.__name__.lower():
                current_type = "browser"
            elif "file" in tool.__class__.__name__.lower():
                current_type = "file"
            elif "search" in tool.__class__.__name__.lower():
                current_type = "search"
            elif "chart" in tool.__class__.__name__.lower():
                current_type = "chart"
            elif "python" in tool.__class__.__name__.lower() or "code" in tool.__class__.__name__.lower():
                current_type = "code"
            elif "mcp" in tool.__class__.__name__.lower():
                current_type = "mcp"
                
            # 应用类型过滤
            if tool_type and current_type != tool_type:
                continue
                
            # 添加到列表
            tool_list.append({
                "id": f"tool_{tool.name}",
                "name": getattr(tool, "display_name", tool.name),
                "description": tool.description,
                "tool_type": current_type,
                "is_active": True,
                "parameters": getattr(tool, "parameters", {})
            })
        
        # 应用分页
        total = len(tool_list)
        start = (page - 1) * limit
        end = start + limit
        paginated_list = tool_list[start:end]
        
        return {
            "success": True,
            "data": {
                "tools": paginated_list,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit
                }
            },
            "message": "获取工具列表成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@router.get(
    "/types",
    summary="获取工具类型"
)
async def get_tool_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取系统支持的工具类型
    """
    try:
        # 固定的工具类型列表
        tool_types = [
            {
                "code": "system",
                "name": "系统工具",
                "description": "与操作系统交互的工具"
            },
            {
                "code": "code",
                "name": "代码工具",
                "description": "执行和分析代码的工具"
            },
            {
                "code": "file",
                "name": "文件工具",
                "description": "操作文件的工具"
            },
            {
                "code": "search",
                "name": "搜索工具",
                "description": "搜索和获取信息的工具"
            },
            {
                "code": "mcp",
                "name": "MCP工具",
                "description": "通过MCP协议提供的外部工具"
            },
            {
                "code": "browser",
                "name": "浏览器工具",
                "description": "控制浏览器的工具"
            },
            {
                "code": "chart",
                "name": "图表工具",
                "description": "数据可视化工具"
            },
            {
                "code": "custom",
                "name": "自定义工具",
                "description": "用户自定义的工具"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "tool_types": tool_types
            },
            "message": "获取工具类型成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具类型失败: {str(e)}"
        )


@router.get(
    "/{tool_id}",
    summary="获取工具详情"
)
async def get_tool(
    tool_id: str = Path(..., description="工具ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取工具详情
    """
    try:
        # 从工具ID中提取工具名称
        if tool_id.startswith("tool_"):
            tool_name = tool_id[5:]  # 去掉 "tool_" 前缀
        else:
            tool_name = tool_id
        
        # 从工具集合中获取工具
        tool_collection = get_global_tool_collection()
        tool = tool_collection.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 {tool_id} 不存在"
            )
        
        # 确定工具类型
        tool_type = "system"  # 默认类型
        if hasattr(tool, "tool_type"):
            tool_type = tool.tool_type
        elif "browser" in tool.__class__.__name__.lower():
            tool_type = "browser"
        elif "file" in tool.__class__.__name__.lower():
            tool_type = "file"
        elif "search" in tool.__class__.__name__.lower():
            tool_type = "search"
        elif "chart" in tool.__class__.__name__.lower():
            tool_type = "chart"
        elif "python" in tool.__class__.__name__.lower() or "code" in tool.__class__.__name__.lower():
            tool_type = "code"
        elif "mcp" in tool.__class__.__name__.lower():
            tool_type = "mcp"
            
        # 构建响应
        tool_data = {
            "id": f"tool_{tool.name}",
            "name": getattr(tool, "display_name", tool.name),
            "description": tool.description,
            "tool_type": tool_type,
            "is_active": True,
            "parameters": getattr(tool, "parameters", {})
        }
        
        return {
            "success": True,
            "data": tool_data,
            "message": "获取工具详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具详情失败: {str(e)}"
        )


@router.post(
    "/{tool_id}/execute",
    summary="执行工具"
)
async def execute_tool(
    params: Dict[str, Any] = Body(...),
    tool_id: str = Path(..., description="工具ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    执行工具
    """
    try:
        # 从工具ID中提取工具名称
        if tool_id.startswith("tool_"):
            tool_name = tool_id[5:]  # 去掉 "tool_" 前缀
        else:
            tool_name = tool_id
        
        # 从工具集合中获取工具
        tool_collection = get_global_tool_collection()
        tool = tool_collection.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 {tool_id} 不存在"
            )
        
        # 执行工具
        result = await tool_collection.execute(name=tool_name, tool_input=params)
        
        # 处理结果
        output = None
        error = None
        if hasattr(result, "output"):
            output = result.output
        if hasattr(result, "error") and result.error:
            error = result.error
            
        # 构建响应
        response = {
            "success": error is None,
            "data": {
                "tool_id": tool_id,
                "result": output,
                "error": error
            },
            "message": "工具执行成功" if error is None else f"工具执行失败: {error}"
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工具失败: {str(e)}"
        )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="注册工具"
)
async def register_tool(
    tool_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    注册新工具
    """
    try:
        # 验证必要的数据
        if "name" not in tool_data or "description" not in tool_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="工具注册需要提供名称和描述"
            )
            
        # 检查工具是否已存在
        tool_collection = get_global_tool_collection()
        if tool_collection.get_tool(tool_data["name"]):
            raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"工具 {tool_data['name']} 已存在"
            )
    
        # 注册工具
        # 注意：这里应该实现实际的工具注册逻辑
        # 由于需要实际的工具类实现，这里仅记录注册信息
        tool = Tool(
            name=tool_data["name"],
            description=tool_data["description"],
            tool_type=tool_data.get("tool_type", "custom"),
            parameters=tool_data.get("parameters", {}),
            implementation=tool_data.get("implementation", {}),
            created_by=current_user.id
        )
        
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        
        return {
            "success": True,
            "data": {
                "id": f"tool_{tool.name}",
                "name": tool.name,
                "description": tool.description,
                "tool_type": tool.tool_type,
                "parameters": tool.parameters,
                "created_by": tool.created_by,
                "created_at": tool.created_at
            },
            "message": "工具注册成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册工具失败: {str(e)}"
        )

