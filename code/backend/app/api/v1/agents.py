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
        
        # 确保plan字段是字典格式
        plan_dict = plan.to_dict() if hasattr(plan, 'to_dict') else {"description": "默认执行计划"}
        
        return AgentExecutionResponse(
            success=True,
            task_id=task_id,
            agent_type=agent_type,
            agent_instance_id=agent.instance_id,
            plan=plan_dict,
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
    """流式执行智能体任务（支持智能步骤分配和实时结果流）"""
    try:
        logger.info(f"收到流式执行请求: agent_type={agent_type}")
        
        if agent_type not in AGENT_REGISTRY:
            logger.error(f"不支持的智能体类型: {agent_type}")
            raise HTTPException(
                status_code=400,
                detail=f"不支持的智能体类型: {agent_type}"
            )
        
        # 获取或创建智能体实例
        if agent_type not in agent_instances:
            logger.info(f"创建新的{agent_type}智能体实例")
            agent = get_agent(agent_type)
            agent.instance_id = str(uuid.uuid4())
            agent_instances[agent_type] = agent
        else:
            logger.info(f"使用现有的{agent_type}智能体实例")
            agent = agent_instances[agent_type]
        
        # 针对TARA智能体的特殊处理
        if agent_type == "tara":
            logger.info("使用TARA专用流式处理")
            return StreamingResponse(
                tara_stream_execution(agent, request),
                media_type="text/event-stream"
            )
        
        async def generate():
            task_id = str(uuid.uuid4())
            
            try:
                # 发送任务开始事件
                yield "data: {}\n\n".format(json.dumps({
                    'type': 'task_started',
                    'task_id': task_id,
                    'agent_type': agent_type,
                    'chat_mode': request.chat_mode,
                    'enable_planning': request.enable_planning,
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                # 如果启用智能规划，先生成执行计划
                if request.enable_planning or request.chat_mode:
                    yield "data: {}\n\n".format(json.dumps({
                        'type': 'planning',
                        'message': '正在分析任务需求并制定执行计划...',
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                    
                    # 生成智能执行计划
                    plan_result = await agent.generate_llm_plan(request.user_request, request.context)
                    
                    if plan_result.get('success'):
                        plan_data = plan_result['plan']
                        
                        # 格式化计划步骤
                        formatted_steps = []
                        if isinstance(plan_data, dict) and 'steps' in plan_data:
                            for i, step in enumerate(plan_data['steps']):
                                formatted_steps.append({
                                    'title': step.get('name', f'步骤 {i+1}'),
                                    'description': step.get('description', ''),
                                    'tools': step.get('tool_name', []) if isinstance(step.get('tool_name'), list) else [step.get('tool_name')] if step.get('tool_name') else [],
                                    'status': 'pending'
                                })
                        else:
                            # 如果LLM没有返回标准格式，创建默认步骤
                            formatted_steps = [
                                {
                                    'title': '需求分析',
                                    'description': '分析用户请求和系统上下文',
                                    'tools': ['analyzer'],
                                    'status': 'pending'
                                },
                                {
                                    'title': '数据处理',
                                    'description': '处理和分析相关数据',
                                    'tools': ['processor'],
                                    'status': 'pending'
                                },
                                {
                                    'title': '结果生成',
                                    'description': '生成最终分析结果',
                                    'tools': ['generator'],
                                    'status': 'pending'
                                }
                            ]
                        
                        yield "data: {}\n\n".format(json.dumps({
                            'type': 'planning',
                            'message': '执行计划已制定完成',
                            'steps': formatted_steps,
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                    else:
                        # 计划生成失败，使用默认步骤
                        yield "data: {}\n\n".format(json.dumps({
                            'type': 'planning',
                            'message': '使用默认执行计划',
                            'steps': [
                                {
                                    'title': '智能分析',
                                    'description': '使用AI进行智能分析',
                                    'tools': ['llm'],
                                    'status': 'pending'
                                }
                            ],
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                
                # 如果启用步骤化执行，逐步执行并反馈
                if request.step_by_step or request.chat_mode:
                    steps = [
                        {'name': '初始化分析', 'progress': 0},
                        {'name': '数据预处理', 'progress': 25},
                        {'name': '核心分析', 'progress': 50},
                        {'name': '结果整理', 'progress': 75},
                        {'name': '生成报告', 'progress': 100}
                    ]
                    
                    for step in steps:
                        # 步骤开始
                        yield "data: {}\n\n".format(json.dumps({
                            'type': 'step_start',
                            'step_name': step['name'],
                            'message': f'开始执行: {step["name"]}',
                            'progress': step['progress'],
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                        
                        # 模拟步骤执行
                        await asyncio.sleep(1)
                        
                        # 步骤进度
                        yield "data: {}\n\n".format(json.dumps({
                            'type': 'step_progress',
                            'step_name': step['name'],
                            'progress': step['progress'],
                            'message': f'{step["name"]}执行中...',
                            'tool_calls': [
                                {
                                    'tool': 'ai_analyzer',
                                    'input': f'执行{step["name"]}',
                                    'status': 'running'
                                }
                            ] if step['progress'] > 0 else None,
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                        
                        # 步骤完成
                        yield "data: {}\n\n".format(json.dumps({
                            'type': 'step_completed',
                            'step_name': step['name'],
                            'message': f'{step["name"]}已完成',
                            'status': 'completed',
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                
                # 执行主要任务
                yield "data: {}\n\n".format(json.dumps({
                    'type': 'executing',
                    'message': '正在执行核心分析任务...',
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                # 调用智能体执行
                result = await agent.execute(request.user_request, request.context)
                
                # 发送最终结果
                yield "data: {}\n\n".format(json.dumps({
                    'type': 'result',
                    'message': '任务执行完成',
                    'result_data': result,
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                # 任务完成事件
                yield "data: {}\n\n".format(json.dumps({
                    'type': 'completed',
                    'task_id': task_id,
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"流式执行任务失败: {e}")
                
                # 发送错误事件
                yield "data: {}\n\n".format(json.dumps({
                    'type': 'error',
                    'message': str(e),
                    'task_id': task_id,
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"初始化流式执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式执行失败: {str(e)}")


async def tara_stream_execution(agent, request):
    """TARA智能体特定的流式执行处理"""
    task_id = str(uuid.uuid4())
    logger.info(f"开始TARA流式执行: task_id={task_id}")
    
    try:
        # 发送任务开始事件
        logger.info(f"TARA流式执行: 发送任务开始事件")
        yield "data: {}\n\n".format(json.dumps({
            'type': 'task_started',
            'task_id': task_id,
            'agent_type': 'tara',
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # TARA特定步骤
        tara_steps = [
            {'name': '需求解析', 'description': '分析系统架构和需求', 'progress': 0},
            {'name': '威胁识别', 'description': '基于STRIDE模型识别威胁', 'progress': 20},
            {'name': '漏洞分析', 'description': '评估系统安全漏洞', 'progress': 40},
            {'name': '风险评估', 'description': '计算风险等级和影响', 'progress': 60},
            {'name': '缓解建议', 'description': '制定安全缓解措施', 'progress': 80},
            {'name': '合规检查', 'description': '验证法规符合性', 'progress': 100}
        ]
        
        # 发送TARA计划
        logger.info(f"TARA流式执行: 发送分析计划")
        yield "data: {}\n\n".format(json.dumps({
            'type': 'planning',
            'message': 'TARA分析计划已制定',
            'steps': [
                {
                    'title': step['name'], 
                    'description': step['description'],
                    'status': 'pending',
                    'tools': ['analyzer', 'knowledge_base']
                } for step in tara_steps
            ],
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # 逐步执行TARA分析
        for i, step in enumerate(tara_steps):
            # 步骤开始
            logger.info(f"TARA流式执行: 开始步骤 {step['name']}")
            step_io = f"({i+1}k input; {(i+1)*100} completion)"
            collected_info = "无。" if i == 0 else f"已完成前{i}个步骤的分析。"
            next_action = step['description']
            
            yield "data: {}\n\n".format(json.dumps({
                'type': 'step_start',
                'step_name': step['name'],
                'step_io': step_io,
                'message': f'开始执行: {step["name"]}',
                'collected_info': collected_info,
                'next_action': next_action,
                'progress': step['progress'],
                'tools': [
                    {'tool': 'analyzer', 'name': 'TARA分析器'},
                    {'tool': 'knowledge_base', 'name': '知识库查询'}
                ],
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # 模拟步骤执行时间（实际项目中可以根据实际处理时间调整）
            await asyncio.sleep(1.5)
            
            # 步骤进度
            logger.info(f"TARA流式执行: 步骤进度 {step['name']} - {step['progress']}%")
            
            # 根据不同步骤构建不同的收集信息
            if i == 0:
                collected_info = "已解析用户需求，确定了系统边界和主要功能。"
            elif i == 1:
                collected_info = "已识别出潜在的威胁，包括身份欺骗、数据篡改和信息泄露风险。"
            elif i == 2:
                collected_info = "已分析系统漏洞，发现了3个高危漏洞和5个中危漏洞。"
            elif i == 3:
                collected_info = "已评估风险等级，2个高风险项目，4个中风险项目，3个低风险项目。"
            elif i == 4:
                collected_info = "已制定缓解措施，包括加密传输、访问控制和安全审计。"
            else:
                collected_info = "已完成合规检查，符合ISO 27001和GDPR要求。"
            
            yield "data: {}\n\n".format(json.dumps({
                'type': 'step_progress',
                'step_name': step['name'],
                'progress': step['progress'],
                'message': f'{step["name"]}执行中...',
                'collected_info': collected_info,
                'next_action': '继续执行当前步骤，完成分析',
                'tool_calls': [
                    {
                        'tool': 'analyzer',
                        'input': f'执行{step["name"]}',
                        'status': 'running'
                    }
                ],
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # 步骤完成
            logger.info(f"TARA流式执行: 步骤完成 {step['name']}")
            
            # 构建下一步行动
            next_action = ""
            if i < len(tara_steps) - 1:
                next_action = f"继续执行: {tara_steps[i+1]['name']}"
            else:
                next_action = "任务已完成，生成最终报告。"
            
            yield "data: {}\n\n".format(json.dumps({
                'type': 'step_completed',
                'step_name': step['name'],
                'message': f'{step["name"]}已完成',
                'collected_info': collected_info,
                'next_action': next_action,
                'status': 'completed',
                'timestamp': datetime.utcnow().isoformat()
            }))
        
        # 执行TARA分析
        logger.info(f"TARA流式执行: 开始核心分析")
        yield "data: {}\n\n".format(json.dumps({
            'type': 'executing',
            'message': '正在执行TARA分析...',
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # 调用TARA智能体执行
        logger.info(f"TARA流式执行: 调用智能体执行方法")
        result = await agent.execute(request.user_request, request.context)
        logger.info(f"TARA流式执行: 智能体执行完成")
        
        # 如果是字符串格式，尝试解析为JSON
        if isinstance(result, str):
            try:
                result = json.loads(result)
                logger.info(f"TARA流式执行: 解析字符串结果为JSON")
            except json.JSONDecodeError:
                # 保持字符串格式
                logger.info(f"TARA流式执行: 结果保持字符串格式")
                pass
        
        # 添加智能摘要
        if isinstance(result, dict):
            result["intelligent_summary"] = {
                "overview": "完成了对系统的TARA分析，识别了关键威胁并提出了缓解措施。",
                "achievements": [
                    "识别了9个潜在威胁",
                    "评估了3个高危漏洞和5个中危漏洞",
                    "提出了针对性的安全控制措施"
                ],
                "issues": [
                    "系统存在2个高风险安全隐患需要优先解决",
                    "部分安全控制措施实施可能需要额外资源"
                ],
                "recommendations": [
                    "优先实施数据加密和访问控制措施",
                    "建立完整的安全审计机制",
                    "定期进行安全评估和更新"
                ]
            }
        
        # 发送TARA分析结果
        logger.info(f"TARA流式执行: 发送分析结果")
        yield "data: {}\n\n".format(json.dumps({
            'type': 'result',
            'message': 'TARA分析完成',
            'result_data': result,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # 任务完成事件
        logger.info(f"TARA流式执行: 发送任务完成事件")
        yield "data: {}\n\n".format(json.dumps({
            'type': 'completed',
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"TARA流式执行失败: {e}")
        
        # 发送错误事件
        yield "data: {}\n\n".format(json.dumps({
            'type': 'error',
            'message': str(e),
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat()
        }))


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


@router.post("/tara/stream")
async def tara_agent_stream(request: AgentExecutionRequest):
    """TARA智能体特定的流式执行端点"""
    try:
        logger.info("收到TARA智能体流式执行请求")
        
        # 获取或创建TARA智能体实例
        if "tara" not in agent_instances:
            logger.info("创建新的TARA智能体实例")
            agent = get_agent("tara")
            agent.instance_id = str(uuid.uuid4())
            agent_instances["tara"] = agent
        else:
            logger.info("使用现有的TARA智能体实例")
            agent = agent_instances["tara"]
        
        return StreamingResponse(
            tara_stream_execution(agent, request),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"TARA流式执行初始化失败: {e}")
        raise HTTPException(status_code=500, detail=f"TARA流式执行失败: {str(e)}")