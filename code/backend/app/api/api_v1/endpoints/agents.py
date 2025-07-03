"""
代理(Agent)管理API端点

提供代理管理相关的API接口，包括创建、获取、更新和配置代理
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.agent import Agent
from app.agent.interface import AgentFactory

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="创建代理"
)
async def create_agent(
    agent_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新代理
    
    代理类型包括：
    - TARA分析代理
    - 测试用例生成代理
    - 自动化测试代理
    - 报告生成代理
    """
    try:
        # 检查是否已存在同名代理
        result = await db.execute(
            select(Agent).where(Agent.name == agent_data["name"])
        )
        existing_agent = result.scalars().first()
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已存在名为 '{agent_data['name']}' 的代理"
            )
        
        # 创建新代理记录
        agent = Agent(
            name=agent_data["name"],
            description=agent_data.get("description", ""),
            agent_type=agent_data["agent_type"],
            model_id=agent_data.get("model_id"),
            config=agent_data.get("config", {}),
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        # 初始化实际的智能体（仅验证可行性，不等待完成）
        try:
            agent_factory = AgentFactory()
            # 异步初始化代理，但不等待完成
            agent_factory.create_agent(agent.agent_type, **agent.config)
        except Exception as e:
            # 记录错误但不阻止API返回
            from app.core.logging import logger
            logger.error(f"初始化代理时出错: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "model_id": agent.model_id,
                "config": agent.config,
                "is_active": agent.is_active,
                "created_by": agent.created_by,
                "created_at": agent.created_at,
            },
            "message": "代理创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建代理失败: {str(e)}"
        )


@router.get(
    "/",
    summary="获取代理列表"
)
async def get_agents(
    agent_type: Optional[str] = Query(None, description="代理类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取代理列表
    """
    try:
        # 构建查询条件
        query = select(Agent)
        conditions = []
        
        if agent_type:
            conditions.append(Agent.agent_type == agent_type)
        if is_active is not None:
            conditions.append(Agent.is_active == is_active)
        
        # 应用所有条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总记录数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 应用排序和分页
        query = query.order_by(desc(Agent.created_at))
        query = query.offset((page - 1) * limit).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        agents = result.scalars().all()
        
        # 构建响应
        agent_list = []
        for agent in agents:
            agent_list.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "model_id": agent.model_id,
                "is_active": agent.is_active,
                "created_at": agent.created_at,
                "created_by": agent.created_by
            })
        
        return {
            "success": True,
            "data": {
                "agents": agent_list,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit
                }
            },
            "message": "获取代理列表成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取代理列表失败: {str(e)}"
        )


@router.get(
    "/{agent_id}",
    summary="获取代理详情"
)
async def get_agent(
    agent_id: str = Path(..., description="代理ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取代理详情
    """
    try:
        # 查询数据库中的代理
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalars().first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="代理不存在"
            )
        
        return {
            "success": True,
            "data": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "model_id": agent.model_id,
                "config": agent.config,
                "is_active": agent.is_active,
                "created_by": agent.created_by,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at
            },
            "message": "获取代理详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取代理详情失败: {str(e)}"
        )


@router.put(
    "/{agent_id}",
    summary="更新代理"
)
async def update_agent(
    agent_data: Dict[str, Any] = Body(...),
    agent_id: str = Path(..., description="代理ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新代理信息
    """
    try:
        # 查询数据库中的代理
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalars().first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="代理不存在"
            )
        
        # 更新属性
        if "name" in agent_data:
            agent.name = agent_data["name"]
        if "description" in agent_data:
            agent.description = agent_data["description"]
        if "model_id" in agent_data:
            agent.model_id = agent_data["model_id"]
        if "config" in agent_data:
            agent.config = agent_data["config"]
        if "is_active" in agent_data:
            agent.is_active = agent_data["is_active"]
        
        # 更新到数据库
        await db.commit()
        await db.refresh(agent)
        
        # 如果需要，重新初始化代理实例
        if "config" in agent_data:
            try:
                agent_factory = AgentFactory()
                # 异步重新初始化代理配置，但不等待完成
                agent_factory.get_agent(agent.agent_type, **agent.config)
            except Exception as e:
                # 记录错误但不阻止API返回
                from app.core.logging import logger
                logger.error(f"重新初始化代理时出错: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "model_id": agent.model_id,
                "config": agent.config,
                "is_active": agent.is_active,
                "updated_at": agent.updated_at
            },
            "message": "代理更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新代理失败: {str(e)}"
        )


@router.delete(
    "/{agent_id}",
    summary="删除代理"
)
async def delete_agent(
    agent_id: str = Path(..., description="代理ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除代理
    """
    try:
        # 查询数据库中的代理
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalars().first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="代理不存在"
            )
        
        # 删除代理
        await db.delete(agent)
        await db.commit()
        
        return {
            "success": True,
            "data": None,
            "message": "代理删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除代理失败: {str(e)}"
        )


@router.post(
    "/{agent_id}/tools",
    summary="配置代理工具"
)
async def configure_agent_tools(
    tools_data: List[Dict[str, Any]] = Body(...),
    agent_id: str = Path(..., description="代理ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    配置代理可用的工具
    """
    try:
        # 查询数据库中的代理
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalars().first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="代理不存在"
            )
        
        # 更新代理的工具配置
        if "config" not in agent.config:
            agent.config["config"] = {}
        
        # 存储工具配置
        agent.config["tools"] = tools_data
        
        # 更新到数据库
        await db.commit()
        await db.refresh(agent)
        
        # 尝试更新实际代理的工具配置
        try:
            agent_factory = AgentFactory()
            # 更新代理的工具配置，但不等待完成
            config = agent.config.copy()
            config["refresh_tools"] = True
            agent_factory.get_agent(agent.agent_type, **config)
        except Exception as e:
            # 记录错误但不阻止API返回
            from app.core.logging import logger
            logger.error(f"更新代理工具配置时出错: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "agent_id": agent.id,
                "tools": tools_data
            },
            "message": "代理工具配置成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置代理工具失败: {str(e)}"
        )

