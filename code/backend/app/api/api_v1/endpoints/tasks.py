"""
车联网安全测试生命周期管理平台 - 任务API

提供任务管理相关的API路由和处理方法，包括创建、查询、执行、暂停、恢复和取消任务等功能。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from fastapi import APIRouter, Body, Depends, Query, Path, HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskType
from app.core.security import get_current_active_user
from app.services.flow_service import get_flow_manager
from app.flow.flow_manager import FlowManager
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="创建任务"
)
async def create_task(
    task_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    创建新任务
    """
    try:
        # 创建任务记录
        task = Task(
            name=task_data["name"],
            description=task_data.get("description", ""),
            type=task_data["type"],
            status="pending",
            input_data=task_data.get("input_data", {}),
            user_id=current_user.id
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return {
            "success": True,
            "data": {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.type,
                "status": task.status,
                "user_id": task.user_id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "input_data": task.input_data
            },
            "message": "任务创建成功"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get(
    "/",
    summary="获取任务列表"
)
async def get_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="任务状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    sort: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序方式，asc或desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务列表
    """
    try:
        # 构建查询
        query = select(Task)
        
        # 应用筛选条件
        if status_filter:
            query = query.where(Task.status == status_filter)
        if task_type:
            query = query.where(Task.type == task_type)
        
        # 获取总记录数
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 应用排序
        if hasattr(Task, sort):
            order_by = getattr(Task, sort)
            if order.lower() == "desc":
                order_by = desc(order_by)
            query = query.order_by(order_by)
        
        # 应用分页
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 构建响应
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.type,
                "status": task.status,
                "progress": task.progress,
                "user_id": task.user_id,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            })
        
        return {
            "success": True,
            "data": {
                "tasks": task_list,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit
                }
            },
            "message": "获取任务列表成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get(
    "/{task_id}",
    summary="获取任务详情"
)
async def get_task_detail(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    获取任务详细信息，包括关联的执行流
    """
    try:
        # 查询任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 构建基本响应
        response_data = {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "type": task.type,
            "status": task.status,
            "progress": task.progress,
            "user_id": task.user_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "input_data": task.input_data,
            "output_data": task.output_data,
            "flow": None
        }
        
        # 如果任务有关联的执行流，获取执行流信息
        if task.flow_execution_id:
            try:
                flow_status = flow_manager.get_flow_status(task.flow_execution_id)
                
                # 添加执行流信息
                response_data["flow"] = {
                    "id": task.flow_execution_id,
                    "status": flow_status.get("status"),
                    "current_step": flow_status.get("current_step"),
                    "progress": flow_status.get("progress", {}),
                    "error": flow_status.get("error")
                }
                
                # 如果执行流已完成且任务结果为空，尝试获取执行流结果
                if flow_status.get("status") == "completed" and not task.output_data:
                    try:
                        flow_result = flow_manager.get_flow_result(task.flow_execution_id)
                        task.output_data = flow_result
                        task.updated_at = datetime.now()
                        await db.commit()
                        response_data["output_data"] = flow_result
                    except Exception as e:
                        logger.warning(f"获取执行流结果失败: {str(e)}")
            except Exception as e:
                # 如果获取执行流状态失败，不阻止API返回
                logger.error(f"获取执行流 {task.flow_execution_id} 状态失败: {str(e)}")
                response_data["flow"] = {
                    "id": task.flow_execution_id,
                    "status": "error",
                    "error": f"获取执行流状态失败: {str(e)}"
                }
        
        return {
            "success": True,
            "data": response_data,
            "message": "获取任务详情成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}"
        )


@router.post(
    "/{task_id}/execute",
    summary="执行任务"
)
async def execute_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    执行任务
    """
    try:
        # 查询任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查任务状态
        if task.status in ["running", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为 {task.status}，无法执行"
            )
        
        # 创建执行流
        # 根据任务类型确定流程类型
        flow_type_mapping = {
            TaskType.TARA: "tara",
            TaskType.TEST_CASE: "testcase",
            TaskType.AUTOMATION: "automation", 
            TaskType.REPORT: "report",
            TaskType.KNOWLEDGE: "knowledge"
        }
        logger.info(f"【tasks】task type: {task.type}")
        flow_type = flow_type_mapping.get(task.type, "dynamic")
        logger.info(f"【tasks】任务类型: {task.type}, 流程类型: {flow_type}")
        
        # 首先确保有一个默认的Flow记录用于关联
        from app.models.flow import Flow, FlowType
        # 检查是否已存在该类型的系统Flow
        system_flow_result = await db.execute(
            select(Flow).where(
                Flow.type == task.type,
                Flow.is_system == True
            )
        )
        system_flow = system_flow_result.scalars().first()
        
        # 如果不存在，则创建一个
        if not system_flow:
            system_flow = Flow(
                name=f"{task.type.value.upper()} 系统流程模板",
                description=f"用于{task.type.value}任务的系统预定义流程模板",
                type=task.type,
                is_system=True,
                user_id=task.user_id
            )
            db.add(system_flow)
            await db.flush()
            logger.info(f"创建系统Flow模板: {system_flow.id}")
        
        # 如果已有执行流，检查状态
        if task.flow_execution_id:
            try:
                flow_status = flow_manager.get_flow_status(task.flow_execution_id)
                flow_status_str = flow_status.get("status")
                
                # 如果执行流已失败或已完成，创建新的执行流
                if flow_status_str in ["failed", "completed"]:
                    flow_id = await flow_manager.create_flow(
                        flow_type=flow_type,
                        name=task.name,
                        description=task.description,
                        use_langgraph=True,
                        **task.input_data
                    )
                    
                    # 创建FlowExecution记录
                    from app.models.flow import FlowExecution, FlowStatus
                    flow_execution = FlowExecution(
                        id=uuid.UUID(flow_id),
                        flow_id=system_flow.id,  # 使用系统Flow模板ID
                        status=FlowStatus.PENDING,
                        input_data=task.input_data,
                        user_id=task.user_id
                    )
                    db.add(flow_execution)
                    await db.flush()
                    
                    # 更新任务的flow_execution_id
                    task.flow_execution_id = flow_execution.id
                    
                # 如果执行流已暂停，可以恢复
                elif flow_status_str == "paused":
                    # 恢复执行流
                    await flow_manager.resume_flow(task.flow_execution_id)
                # 如果执行流正在运行，不做任何操作
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"执行流状态为 {flow_status_str}，无法执行"
                    )
            except ValueError:
                # 如果执行流不存在，创建新的执行流
                flow_id = await flow_manager.create_flow(
                    flow_type=flow_type,
                    name=task.name,
                    description=task.description,
                    use_langgraph=True,
                    **task.input_data
                )
                
                # 创建FlowExecution记录
                from app.models.flow import FlowExecution, FlowStatus
                flow_execution = FlowExecution(
                    id=uuid.UUID(flow_id),
                    flow_id=system_flow.id,  # 使用系统Flow模板ID
                    status=FlowStatus.PENDING,
                    input_data=task.input_data,
                    user_id=task.user_id
                )
                db.add(flow_execution)
                await db.flush()
                
                # 更新任务的flow_execution_id
                task.flow_execution_id = flow_execution.id
        else:
            # 创建新的执行流
            flow_id = await flow_manager.create_flow(
                flow_type=flow_type,
                name=task.name,
                description=task.description,
                use_langgraph=True,
                **task.input_data
            )
            
            # 创建FlowExecution记录
            from app.models.flow import FlowExecution, FlowStatus
            flow_execution = FlowExecution(
                id=uuid.UUID(flow_id),
                flow_id=system_flow.id,  # 使用系统Flow模板ID
                status=FlowStatus.PENDING,
                input_data=task.input_data,
                user_id=task.user_id
            )
            db.add(flow_execution)
            await db.flush()
            
            # 更新任务的flow_execution_id
            task.flow_execution_id = flow_execution.id
        
        # 更新任务状态
        task.status = "running"
        task.updated_at = datetime.now()
        await db.commit()
        
        # 执行流程（异步）
        execution_config = {
            "task_id": task.id,
            "task_name": task.name,
            "task_description": task.description,
            **task.input_data
        }
        
        # 异步执行，不等待结果
        asyncio.create_task(execute_flow_and_update_task(
            flow_manager, str(task.flow_execution_id), execution_config, task.id, db))
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "flow_id": task.flow_execution_id,
                "status": "running"
            },
                "message": "任务已开始执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行任务失败: {str(e)}"
        )


async def execute_flow_and_update_task(flow_manager, flow_id, config, task_id, db):
    """执行流程并更新任务状态"""
    try:
        # 执行流程
        flow_result = await flow_manager.execute_flow(flow_id, **config)
        
        # 确保flow_result不是协程对象
        if hasattr(flow_result, '__await__'):
            flow_result = await flow_result
            
        # 创建新的数据库会话（因为这是在异步任务中，原始会话可能已关闭）
        from app.db.session import async_session
        import json
        async with async_session() as session:
            async with session.begin():
                # 获取任务
                task_query = await session.execute(select(Task).where(Task.id == task_id))
                task = task_query.scalars().first()
                
                if not task:
                    logger.error(f"任务 {task_id} 不存在，无法更新状态")
                    return
                logger.info(f"flow_result: {flow_result}")
                logger.info(f"flow_result: {type(flow_result)}")
                
                logger.info(f"flow_result: {dir(flow_result)}")
                
                # 更新任务状态和结果
                task.status = "completed"
                task.output_data = str(flow_result)
                task.completed_at = datetime.now()
                task.updated_at = datetime.now()
                
                # 计算任务进度
                task.progress = 100
                
                # 更新执行流状态
                from app.models.flow import FlowExecution, FlowStatus
                if task.flow_execution_id:
                    flow_exec_query = await session.execute(
                        select(FlowExecution).where(FlowExecution.id == task.flow_execution_id)
                    )
                    
                    flow_execution = flow_exec_query.scalars().first()
                    
                    if flow_execution:
                        flow_execution.status = FlowStatus.COMPLETED
                        flow_execution.output_data = str(flow_result)
                        flow_execution.completed_at = datetime.now()
                        flow_execution.progress = 100
            
        logger.info(f"任务 {task_id} 执行完成")
    except Exception as e:
        # 如果执行失败，更新任务状态为失败
        logger.error(f"任务 {task_id} 执行失败: {str(e)}")
        
        try:
            # 创建新的数据库会话（因为这是在异步任务中，原始会话可能已关闭）
            from app.db.session import async_session
            async with async_session() as session:
                async with session.begin():
                    task_query = await session.execute(select(Task).where(Task.id == task_id))
                    task = task_query.scalars().first()
                    
                    if task:
                        task.status = "failed"
                        task.error_message = str(e)
                        task.updated_at = datetime.now()
                        
                        # 更新执行流状态
                        from app.models.flow import FlowExecution, FlowStatus
                        if task.flow_execution_id:
                            flow_exec_query = await session.execute(
                                select(FlowExecution).where(FlowExecution.id == task.flow_execution_id)
                            )
                            flow_execution = flow_exec_query.scalars().first()
                            if flow_execution:
                                flow_execution.status = FlowStatus.FAILED
                                flow_execution.error_message = str(e)
        except Exception as db_error:
            logger.error(f"更新任务 {task_id} 状态失败: {str(db_error)}")


@router.post(
    "/{task_id}/pause",
    summary="暂停任务"
)
async def pause_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    暂停正在执行的任务
    """
    try:
        # 查询任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查任务状态
        if task.status != "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为 {task.status}，无法暂停"
            )
        
        # 检查是否有关联的执行流
        if not task.flow_execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务没有关联的执行流，无法暂停"
            )
        
        # 尝试暂停执行流
        try:
            await flow_manager.pause_flow(task.flow_execution_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"暂停执行流失败: {str(e)}"
            )
        
        # 更新任务状态
        task.status = "paused"
        task.updated_at = datetime.now()
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "status": "paused"
            },
            "message": "任务已暂停"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停任务失败: {str(e)}"
        )


@router.post(
    "/{task_id}/resume",
    summary="恢复任务"
)
async def resume_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    恢复已暂停的任务
    """
    try:
        # 查询任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查任务状态
        if task.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为 {task.status}，无法恢复"
            )
        
        # 检查是否有关联的执行流
        if not task.flow_execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务没有关联的执行流，无法恢复"
            )
        
        # 尝试恢复执行流
        try:
            await flow_manager.resume_flow(task.flow_execution_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"恢复执行流失败: {str(e)}"
            )
        
        # 更新任务状态
        task.status = "running"
        task.updated_at = datetime.now()
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "status": "running"
            },
            "message": "任务已恢复执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复任务失败: {str(e)}"
        )


@router.post(
    "/{task_id}/cancel",
    summary="取消任务"
)
async def cancel_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    flow_manager: FlowManager = Depends(get_flow_manager)
):
    """
    取消正在执行的任务
    """
    try:
        # 查询任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查任务状态
        if task.status not in ["running", "paused"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为 {task.status}，无法取消"
            )
        
        # 检查是否有关联的执行流
        if not task.flow_execution_id:
            # 如果没有关联的执行流，直接更新状态
            task.status = "cancelled"
            task.updated_at = datetime.now()
            await db.commit()
        else:
            # 尝试取消执行流
            try:
                await flow_manager.cancel_flow(task.flow_execution_id)
            except Exception as e:
                logger.warning(f"取消执行流失败: {str(e)}")
            
            # 更新任务状态
            task.status = "cancelled"
            task.updated_at = datetime.now()
            await db.commit()
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "status": "cancelled"
            },
            "message": "任务已取消"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}"
        ) 