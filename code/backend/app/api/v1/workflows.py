"""
工作流管理API路由

提供LangGraph工作流的创建、执行、监控和管理功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime, timedelta
import uuid

from app.core.langgraph_workflow import LangGraphWorkflowManager, get_workflow_manager
from app.core.llm_client import get_llm_manager, LLMClientManager
from app.core.tool_registry import get_tool_registry, ToolRegistry
from app.models.task import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowExecution,
    WorkflowStatus,
    TaskProgressUpdate
)
from loguru import logger

router = APIRouter(prefix="/workflows", tags=["workflows"])

# 工作流实例缓存
active_workflows = {}


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    workflow_manager: LangGraphWorkflowManager = Depends(get_workflow_manager)
):
    """执行LangGraph工作流"""
    try:
        workflow_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # 记录工作流
        workflow_info = WorkflowExecution(
            workflow_id=workflow_id,
            user_request=request.user_request,
            context=request.context,
            status=WorkflowStatus.RUNNING,
            current_step="开始执行",
            steps_completed=0,
            total_steps=0,
            created_at=start_time,
            updated_at=start_time,
            started_at=start_time
        )
        active_workflows[workflow_id] = workflow_info
        
        # 执行工作流
        result = await workflow_manager.execute_workflow(
            user_request=request.user_request,
            context=request.context,
            max_iterations=request.max_iterations,
            max_retries=request.max_retries
        )
        
        # 更新工作流状态
        end_time = datetime.utcnow()
        workflow_info.status = WorkflowStatus.COMPLETED
        workflow_info.result = result
        workflow_info.completed_at = end_time
        workflow_info.updated_at = end_time
        
        execution_duration = (end_time - start_time).total_seconds()
        
        return WorkflowExecutionResponse(
            success=True,
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            result=result,
            steps_executed=workflow_info.steps_completed,
            execution_duration=execution_duration,
            timestamp=end_time
        )
        
    except Exception as e:
        # 更新工作流状态为失败
        if workflow_id in active_workflows:
            workflow_info = active_workflows[workflow_id]
            workflow_info.status = WorkflowStatus.FAILED
            workflow_info.error = str(e)
            workflow_info.updated_at = datetime.utcnow()
        
        logger.error(f"执行工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行工作流失败: {str(e)}")


@router.post("/execute/stream")
async def execute_workflow_stream(
    request: WorkflowExecutionRequest,
    workflow_manager: LangGraphWorkflowManager = Depends(get_workflow_manager)
):
    """流式执行LangGraph工作流"""
    try:
        workflow_id = str(uuid.uuid4())
        
        async def generate():
            try:
                # 发送工作流开始事件
                yield f"data: {json.dumps({
                    'event': 'workflow_started',
                    'workflow_id': workflow_id,
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                # 记录工作流
                workflow_info = WorkflowExecution(
                    workflow_id=workflow_id,
                    user_request=request.user_request,
                    context=request.context,
                    status=WorkflowStatus.RUNNING,
                    current_step="初始化",
                    steps_completed=0,
                    total_steps=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    started_at=datetime.utcnow()
                )
                active_workflows[workflow_id] = workflow_info
                
                # 发送初始化事件
                yield f"data: {json.dumps({
                    'event': 'initializing',
                    'message': '正在初始化工作流...',
                    'workflow_id': workflow_id,
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
                # 执行工作流（这里需要实现流式执行）
                # 目前简化为逐步更新
                steps = [
                    "分析用户请求",
                    "制定执行计划", 
                    "选择适当智能体",
                    "执行智能体任务",
                    "聚合结果",
                    "生成最终响应"
                ]
                
                workflow_info.total_steps = len(steps)
                
                for i, step in enumerate(steps):
                    # 更新当前步骤
                    workflow_info.current_step = step
                    workflow_info.steps_completed = i
                    workflow_info.updated_at = datetime.utcnow()
                    
                    # 发送步骤进度
                    yield f"data: {json.dumps({
                        'event': 'step_progress',
                        'current_step': step,
                        'step_index': i,
                        'total_steps': len(steps),
                        'progress': (i / len(steps)) * 100,
                        'workflow_id': workflow_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })}\n\n"
                    
                    # 模拟步骤执行时间
                    await asyncio.sleep(1)
                
                # 执行实际工作流
                result = await workflow_manager.execute_workflow(
                    user_request=request.user_request,
                    context=request.context,
                    max_iterations=request.max_iterations,
                    max_retries=request.max_retries
                )
                
                # 更新最终状态
                workflow_info.status = WorkflowStatus.COMPLETED
                workflow_info.result = result
                workflow_info.completed_at = datetime.utcnow()
                workflow_info.updated_at = datetime.utcnow()
                workflow_info.steps_completed = len(steps)
                
                # 发送完成事件
                yield f"data: {json.dumps({
                    'event': 'workflow_completed',
                    'result': result,
                    'workflow_id': workflow_id,
                    'execution_time': (workflow_info.completed_at - workflow_info.started_at).total_seconds(),
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
                
            except Exception as e:
                # 更新错误状态
                if workflow_id in active_workflows:
                    workflow_info = active_workflows[workflow_id]
                    workflow_info.status = WorkflowStatus.FAILED
                    workflow_info.error = str(e)
                    workflow_info.updated_at = datetime.utcnow()
                
                # 发送错误事件
                yield f"data: {json.dumps({
                    'event': 'workflow_failed',
                    'error': str(e),
                    'workflow_id': workflow_id,
                    'timestamp': datetime.utcnow().isoformat()
                })}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"流式执行工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式执行工作流失败: {str(e)}")


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    try:
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        workflow = active_workflows[workflow_id]
        
        return {
            "success": True,
            "workflow": workflow.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流状态失败: {str(e)}")


@router.get("/{workflow_id}/progress")
async def get_workflow_progress(workflow_id: str):
    """获取工作流进度"""
    try:
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        workflow = active_workflows[workflow_id]
        
        # 计算进度百分比
        if workflow.total_steps > 0:
            progress = (workflow.steps_completed / workflow.total_steps) * 100
        else:
            progress = 0.0 if workflow.status == WorkflowStatus.RUNNING else 100.0
        
        progress_info = TaskProgressUpdate(
            task_id=workflow_id,
            agent_type="workflow",
            progress=progress,
            current_step=workflow.current_step or "未知",
            message=f"工作流状态: {workflow.status.value}",
            timestamp=datetime.utcnow()
        )
        
        return {
            "success": True,
            "progress": progress_info.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流进度失败: {str(e)}")


@router.delete("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """取消工作流执行"""
    try:
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=404, detail="工作流不存在")
        
        workflow = active_workflows[workflow_id]
        
        # 只能取消正在运行的工作流
        if workflow.status not in [WorkflowStatus.RUNNING, WorkflowStatus.IDLE]:
            raise HTTPException(
                status_code=400, 
                detail=f"无法取消状态为 {workflow.status.value} 的工作流"
            )
        
        # 更新状态
        workflow.status = WorkflowStatus.CANCELLED
        workflow.updated_at = datetime.utcnow()
        
        return {
            "success": True,
            "message": "工作流已取消",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消工作流失败: {str(e)}")


@router.get("/")
async def list_workflows(
    status: Optional[WorkflowStatus] = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """获取工作流列表"""
    try:
        workflows = list(active_workflows.values())
        
        # 按状态筛选
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        # 排序（最新的在前）
        workflows.sort(key=lambda x: x.created_at, reverse=True)
        
        # 分页
        total = len(workflows)
        workflows = workflows[offset:offset + limit]
        
        # 转换为字典
        workflow_data = [w.model_dump() for w in workflows]
        
        return {
            "success": True,
            "workflows": workflow_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流列表失败: {str(e)}")


@router.get("/stats")
async def get_workflow_stats():
    """获取工作流统计信息"""
    try:
        workflows = list(active_workflows.values())
        
        # 统计各种状态的工作流
        status_stats = {}
        for status in WorkflowStatus:
            status_stats[status.value] = len([w for w in workflows if w.status == status])
        
        # 计算平均执行时间
        completed_workflows = [w for w in workflows if w.status == WorkflowStatus.COMPLETED and w.started_at and w.completed_at]
        avg_execution_time = 0.0
        if completed_workflows:
            total_time = sum((w.completed_at - w.started_at).total_seconds() for w in completed_workflows)
            avg_execution_time = total_time / len(completed_workflows)
        
        # 成功率
        total_finished = len([w for w in workflows if w.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]])
        success_rate = 0.0
        if total_finished > 0:
            successful = len([w for w in workflows if w.status == WorkflowStatus.COMPLETED])
            success_rate = (successful / total_finished) * 100
        
        stats = {
            "total_workflows": len(workflows),
            "status_distribution": status_stats,
            "average_execution_time": round(avg_execution_time, 2),
            "success_rate": round(success_rate, 2),
            "active_workflows": len([w for w in workflows if w.status == WorkflowStatus.RUNNING])
        }
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取工作流统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流统计失败: {str(e)}")


@router.delete("/cleanup")
async def cleanup_workflows(
    status_filter: Optional[str] = Query(None, description="清理特定状态的工作流"),
    older_than_hours: int = Query(24, description="清理多少小时前的工作流")
):
    """清理历史工作流"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        workflows_to_remove = []
        
        for workflow_id, workflow in active_workflows.items():
            # 检查时间条件
            if workflow.created_at < cutoff_time:
                # 检查状态条件
                if status_filter:
                    if workflow.status.value == status_filter:
                        workflows_to_remove.append(workflow_id)
                else:
                    # 只清理已完成、失败或取消的工作流
                    if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                        workflows_to_remove.append(workflow_id)
        
        # 删除工作流
        for workflow_id in workflows_to_remove:
            del active_workflows[workflow_id]
        
        return {
            "success": True,
            "message": f"已清理 {len(workflows_to_remove)} 个工作流",
            "cleaned_workflows": len(workflows_to_remove),
            "remaining_workflows": len(active_workflows),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理工作流失败: {str(e)}")


@router.get("/templates")
async def list_workflow_templates():
    """获取工作流模板列表"""
    try:
        # 这里应该从数据库或配置文件获取模板
        # 目前返回预定义模板
        
        templates = [
            {
                "id": "tara_analysis",
                "name": "TARA威胁分析",
                "description": "执行完整的威胁分析与风险评估",
                "agents": ["tara"],
                "estimated_time": "5-10分钟",
                "inputs": ["系统描述", "安全需求"]
            },
            {
                "id": "full_security_test",
                "name": "完整安全测试",
                "description": "从TARA分析到测试执行的完整流程",
                "agents": ["tara", "test_case", "automation_test", "report_analysis"],
                "estimated_time": "15-30分钟",
                "inputs": ["系统描述", "安全需求", "测试环境信息"]
            },
            {
                "id": "knowledge_extraction",
                "name": "知识提取与归档",
                "description": "从文档中提取知识并自动归档",
                "agents": ["knowledge_base"],
                "estimated_time": "3-5分钟",
                "inputs": ["文档内容", "分类标签"]
            }
        ]
        
        return {
            "success": True,
            "templates": templates,
            "total_count": len(templates),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取工作流模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工作流模板失败: {str(e)}")


@router.post("/templates/{template_id}/execute")
async def execute_workflow_template(
    template_id: str,
    template_params: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """基于模板执行工作流"""
    try:
        # 根据模板ID构建工作流请求
        template_configs = {
            "tara_analysis": {
                "user_request": f"请对以下系统进行TARA分析：{template_params.get('system_description', '')}",
                "context": {
                    "analysis_type": "tara",
                    "security_requirements": template_params.get('security_requirements', []),
                    "template_id": template_id
                }
            },
            "full_security_test": {
                "user_request": f"请对以下系统执行完整的安全测试：{template_params.get('system_description', '')}",
                "context": {
                    "analysis_type": "full_test",
                    "security_requirements": template_params.get('security_requirements', []),
                    "test_environment": template_params.get('test_environment', {}),
                    "template_id": template_id
                }
            },
            "knowledge_extraction": {
                "user_request": f"请从以下内容中提取和归档知识：{template_params.get('content', '')}",
                "context": {
                    "extraction_type": "knowledge",
                    "categories": template_params.get('categories', []),
                    "template_id": template_id
                }
            }
        }
        
        if template_id not in template_configs:
            raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")
        
        config = template_configs[template_id]
        
        # 创建工作流执行请求
        request = WorkflowExecutionRequest(
            user_request=config["user_request"],
            context=config["context"],
            max_iterations=10,
            max_retries=3,
            timeout=1800  # 30分钟
        )
        
        # 执行工作流
        return await execute_workflow(request, background_tasks)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行工作流模板失败: {str(e)}")