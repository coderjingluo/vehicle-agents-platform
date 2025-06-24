"""
智能体管理API路由

提供智能体实例管理、状态监控、任务执行等功能的专门API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime
import uuid

from app.agents import (
    get_agent, 
    list_available_agents, 
    get_agent_info,
    AGENT_REGISTRY
)
from app.core.config import settings
from app.core.llm_client import get_llm_manager, LLMClientManager
from app.core.tool_registry import get_tool_registry, ToolRegistry
from app.models.task import (
    TaskCreate,
    TaskResponse, 
    TaskStatus,
    TaskUpdate,
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentStatus,
    AgentMetrics
)
from loguru import logger

router = APIRouter(prefix="/agents", tags=["agents"])

# 智能体实例缓存
agent_instances = {}
active_tasks = {}


@router.get("/", response_model=Dict[str, Any])
async def list_agents():
    """列出所有可用的智能体类型和详细信息"""
    try:
        agents = list_available_agents()
        agent_details = {}
        
        for agent_type in agents:
            agent_info = get_agent_info(agent_type)
            
            # 添加实例状态信息
            if agent_type in agent_instances:
                agent_info["instance_status"] = "active"
                agent_info["instance_id"] = agent_instances[agent_type].instance_id
            else:
                agent_info["instance_status"] = "inactive"
                agent_info["instance_id"] = None
            
            agent_details[agent_type] = agent_info
        
        return {
            "success": True,
            "agents": agent_details,
            "total_count": len(agents),
            "active_instances": len(agent_instances),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"列出智能体失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出智能体失败: {str(e)}")


@router.post("/{agent_type}/initialize")
async def initialize_agent(agent_type: str):
    """初始化指定类型的智能体实例"""
    try:
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 如果已有实例，返回现有实例信息
        if agent_type in agent_instances:
            return {
                "success": True,
                "message": "智能体实例已存在",
                "agent_type": agent_type,
                "instance_id": agent_instances[agent_type].instance_id,
                "status": "active"
            }
        
        # 创建新实例
        agent = get_agent(agent_type)
        agent.instance_id = str(uuid.uuid4())
        agent_instances[agent_type] = agent
        
        return {
            "success": True,
            "message": "智能体实例初始化成功",
            "agent_type": agent_type,
            "instance_id": agent.instance_id,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"初始化智能体失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化智能体失败: {str(e)}")


@router.delete("/{agent_type}/terminate")
async def terminate_agent(agent_type: str):
    """终止指定类型的智能体实例"""
    try:
        if agent_type not in agent_instances:
            raise HTTPException(
                status_code=404,
                detail=f"智能体实例不存在: {agent_type}"
            )
        
        # 清理实例
        instance_id = agent_instances[agent_type].instance_id
        del agent_instances[agent_type]
        
        # 清理相关任务
        tasks_to_remove = [
            task_id for task_id, task in active_tasks.items() 
            if task.get("agent_type") == agent_type
        ]
        for task_id in tasks_to_remove:
            del active_tasks[task_id]
        
        return {
            "success": True,
            "message": "智能体实例已终止",
            "agent_type": agent_type,
            "instance_id": instance_id,
            "cleaned_tasks": len(tasks_to_remove),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"终止智能体失败: {e}")
        raise HTTPException(status_code=500, detail=f"终止智能体失败: {str(e)}")


@router.post("/{agent_type}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_type: str,
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks
):
    """执行指定类型的智能体任务"""
    try:
        # 验证智能体类型
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 获取或创建智能体实例
        if agent_type not in agent_instances:
            agent = get_agent(agent_type)
            agent.instance_id = str(uuid.uuid4())
            agent_instances[agent_type] = agent
        else:
            agent = agent_instances[agent_type]
        
        # 创建任务
        task_id = str(uuid.uuid4())
        
        # 记录任务
        task_info = {
            "task_id": task_id,
            "agent_type": agent_type,
            "agent_instance_id": agent.instance_id,
            "request": request.model_dump(),
            "status": TaskStatus.RUNNING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        active_tasks[task_id] = task_info
        
        # 生成执行计划
        plan = await agent.generate_plan(request.user_request, request.context)
        
        # 执行任务
        result = await agent.execute(request.user_request, request.context)
        
        # 更新任务状态
        task_info.update({
            "status": TaskStatus.COMPLETED,
            "result": result,
            "updated_at": datetime.utcnow()
        })
        
        return AgentExecutionResponse(
            success=True,
            task_id=task_id,
            agent_type=agent_type,
            agent_instance_id=agent.instance_id,
            plan=plan.model_dump() if hasattr(plan, 'model_dump') else str(plan),
            result=result,
            status=TaskStatus.COMPLETED,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        # 更新任务状态为失败
        if 'task_id' in locals():
            active_tasks[task_id].update({
                "status": TaskStatus.FAILED,
                "error": str(e),
                "updated_at": datetime.utcnow()
            })
        
        logger.error(f"执行智能体任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行智能体任务失败: {str(e)}")


@router.post("/{agent_type}/stream")
async def stream_agent_execution(
    agent_type: str,
    request: AgentExecutionRequest
):
    """流式执行智能体任务（支持实时结果流）"""
    try:
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 获取或创建智能体实例
        if agent_type not in agent_instances:
            agent = get_agent(agent_type)
            agent.instance_id = str(uuid.uuid4())
            agent_instances[agent_type] = agent
        else:
            agent = agent_instances[agent_type]
        
        async def generate():
            task_id = str(uuid.uuid4())
            
            try:
                # 发送任务开始事件
                yield f"data: {json.dumps({
                    'event': 'task_started',
                    'task_id': task_id,
                    'agent_type': agent_type,
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                # 生成执行计划
                yield f"data: {json.dumps({
                    'event': 'planning',
                    'message': '正在生成执行计划...',
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                plan = await agent.generate_plan(request.user_request, request.context)
                
                yield f"data: {json.dumps({
                    'event': 'plan_generated',
                    'plan': plan.model_dump() if hasattr(plan, 'model_dump') else str(plan),
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                # 执行任务并流式返回结果
                yield f"data: {json.dumps({
                    'event': 'executing',
                    'message': '正在执行任务...',
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                # 这里应该实现流式执行，目前简化处理
                result = await agent.execute(request.user_request, request.context)
                
                yield f"data: {json.dumps({
                    'event': 'task_completed',
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({
                    'event': 'task_failed',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"流式执行智能体任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式执行智能体任务失败: {str(e)}")


@router.get("/{agent_type}/status", response_model=AgentStatus)
async def get_agent_status(agent_type: str):
    """获取智能体状态信息"""
    try:
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 获取基本信息
        agent_info = get_agent_info(agent_type)
        
        # 实例状态
        if agent_type in agent_instances:
            instance = agent_instances[agent_type]
            instance_status = "active"
            instance_id = instance.instance_id
        else:
            instance_status = "inactive"
            instance_id = None
        
        # 任务统计
        agent_tasks = [
            task for task in active_tasks.values() 
            if task.get("agent_type") == agent_type
        ]
        
        task_stats = {
            "total": len(agent_tasks),
            "running": len([t for t in agent_tasks if t.get("status") == TaskStatus.RUNNING]),
            "completed": len([t for t in agent_tasks if t.get("status") == TaskStatus.COMPLETED]),
            "failed": len([t for t in agent_tasks if t.get("status") == TaskStatus.FAILED])
        }
        
        return AgentStatus(
            agent_type=agent_type,
            name=agent_info.get("name", "未知智能体"),
            description=agent_info.get("description", ""),
            instance_status=instance_status,
            instance_id=instance_id,
            task_stats=task_stats,
            capabilities=agent_info.get("capabilities", []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"获取智能体状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取智能体状态失败: {str(e)}")


@router.get("/{agent_type}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_type: str,
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """获取智能体性能指标"""
    try:
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 这里应该从数据库或监控系统获取真实指标
        # 目前返回模拟数据
        
        metrics = AgentMetrics(
            agent_type=agent_type,
            period_days=days,
            total_executions=150,
            successful_executions=142,
            failed_executions=8,
            average_execution_time=45.5,
            success_rate=94.7,
            avg_response_time=2.3,
            error_rate=5.3,
            resource_usage={
                "cpu_avg": 25.6,
                "memory_avg": 512.3,
                "disk_usage": 1024.7
            },
            timestamp=datetime.utcnow()
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"获取智能体指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取智能体指标失败: {str(e)}")


@router.get("/{agent_type}/tools")
async def get_agent_tools(
    agent_type: str,
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """获取智能体可用工具列表"""
    try:
        if agent_type not in AGENT_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 获取智能体实例
        if agent_type in agent_instances:
            agent = agent_instances[agent_type]
        else:
            agent = get_agent(agent_type)
        
        # 获取智能体专用工具
        agent_tools = getattr(agent, 'available_tools', [])
        
        # 获取通用工具
        general_tools = tool_registry.list_tools()
        
        return {
            "success": True,
            "agent_type": agent_type,
            "agent_tools": agent_tools,
            "general_tools": general_tools,
            "total_tools": len(agent_tools) + len(general_tools),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取智能体工具失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取智能体工具失败: {str(e)}")


@router.get("/tasks/active")
async def list_active_tasks(
    agent_type: Optional[str] = Query(None, description="按智能体类型筛选"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """获取活跃任务列表"""
    try:
        tasks = list(active_tasks.values())
        
        # 按智能体类型筛选
        if agent_type:
            tasks = [t for t in tasks if t.get("agent_type") == agent_type]
        
        # 排序（最新的在前）
        tasks.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        
        # 分页
        total = len(tasks)
        tasks = tasks[offset:offset + limit]
        
        return {
            "success": True,
            "tasks": tasks,
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取活跃任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取活跃任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取任务详细信息"""
    try:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = active_tasks[task_id]
        
        return {
            "success": True,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务执行"""
    try:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = active_tasks[task_id]
        
        # 更新任务状态
        task.update({
            "status": TaskStatus.CANCELLED,
            "updated_at": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message": "任务已取消",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/batch/execute")
async def batch_execute_agents(
    requests: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """批量执行多个智能体任务"""
    try:
        batch_id = str(uuid.uuid4())
        batch_tasks = []
        
        for req in requests:
            agent_type = req.get("agent_type")
            if not agent_type or agent_type not in AGENT_REGISTRY:
                continue
            
            task_id = str(uuid.uuid4())
            
            # 记录批次任务
            task_info = {
                "task_id": task_id,
                "batch_id": batch_id,
                "agent_type": agent_type,
                "request": req,
                "status": TaskStatus.PENDING,
                "created_at": datetime.utcnow()
            }
            active_tasks[task_id] = task_info
            batch_tasks.append(task_id)
        
        # 在后台执行批次任务
        async def execute_batch():
            for task_id in batch_tasks:
                try:
                    task = active_tasks[task_id]
                    task["status"] = TaskStatus.RUNNING
                    
                    # 执行任务 (简化处理)
                    agent = get_agent(task["agent_type"])
                    result = await agent.execute(
                        task["request"].get("user_request", ""),
                        task["request"].get("context", {})
                    )
                    
                    task.update({
                        "status": TaskStatus.COMPLETED,
                        "result": result,
                        "updated_at": datetime.utcnow()
                    })
                    
                except Exception as e:
                    task.update({
                        "status": TaskStatus.FAILED,
                        "error": str(e),
                        "updated_at": datetime.utcnow()
                    })
        
        background_tasks.add_task(execute_batch)
        
        return {
            "success": True,
            "batch_id": batch_id,
            "task_ids": batch_tasks,
            "total_tasks": len(batch_tasks),
            "message": "批次任务已提交",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量执行失败: {str(e)}")


@router.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """获取批次任务状态"""
    try:
        batch_tasks = [
            task for task in active_tasks.values() 
            if task.get("batch_id") == batch_id
        ]
        
        if not batch_tasks:
            raise HTTPException(status_code=404, detail="批次任务不存在")
        
        # 统计状态
        status_stats = {}
        for task in batch_tasks:
            status = task.get("status", "unknown")
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 计算进度
        completed = status_stats.get(TaskStatus.COMPLETED, 0)
        failed = status_stats.get(TaskStatus.FAILED, 0)
        total = len(batch_tasks)
        progress = (completed + failed) / total * 100 if total > 0 else 0
        
        return {
            "success": True,
            "batch_id": batch_id,
            "total_tasks": total,
            "status_stats": status_stats,
            "progress": round(progress, 2),
            "tasks": batch_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批次状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取批次状态失败: {str(e)}")