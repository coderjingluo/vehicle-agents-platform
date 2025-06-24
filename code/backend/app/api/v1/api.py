"""
API路由模块
提供车联网安全测试生命周期管理的REST API接口
支持LangGraph工作流和多智能体协作
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime
import uuid
from loguru import logger

from app.core.config import settings
from app.core.llm_client import get_llm_manager, LLMClientManager
from app.core.tool_registry import get_tool_registry, ToolRegistry
from app.core.langgraph_workflow import LangGraphWorkflowManager
from app.agents.base_agent import BaseAgent
from app.agents.tara_agent import TARAAgent
from app.agents.testcase_agent import TestCaseAgent
from app.agents.automation_agent import AutomationAgent
from app.agents.report_agent import ReportAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.model_config import router as model_config_router
from app.api.v1.agents import router as agents_router
from app.api.v1.system import router as system_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.auth import router as auth_router


# 创建API路由器
api_router = APIRouter()

# 注册子路由器
api_router.include_router(auth_router, prefix="/v1", tags=["Authentication"])
api_router.include_router(agents_router, prefix="/v1")
api_router.include_router(system_router, prefix="/v1") 
api_router.include_router(workflows_router, prefix="/v1")
api_router.include_router(knowledge_base_router, prefix="/v1")
api_router.include_router(model_config_router, prefix="/v1")

# 全局工作流管理器
workflow_manager = None
agents = {}


async def get_workflow_manager() -> LangGraphWorkflowManager:
    """获取工作流管理器"""
    global workflow_manager
    if workflow_manager is None:
        llm_manager = get_llm_manager()
        tool_registry = get_tool_registry()
        workflow_manager = LangGraphWorkflowManager(llm_manager, tool_registry)
        
        # 初始化智能体
        await initialize_agents()
    
    return workflow_manager


async def initialize_agents():
    """初始化所有智能体"""
    global agents
    if agents:  # 避免重复初始化
        return

    # 创建并注册所有智能体
    agents["tara"] = TARAAgent()
    agents["test_case"] = TestCaseAgent()
    agents["automation_test"] = AutomationAgent()
    agents["report_analysis"] = ReportAgent()
    agents["knowledge_base"] = KnowledgeAgent()
    
    print(f"✅ 已初始化 {len(agents)} 个智能体: {list(agents.keys())}")


@api_router.get("/")
async def root():
    """根路径"""
    return {
        "message": "车联网安全测试生命周期管理平台 API",
        "version": settings.app_version,
        "framework": "LangGraph + FastAPI",
        "status": "running"
    }


@api_router.get("/health")
async def health_check():
    """健康检查"""
    workflow_mgr = await get_workflow_manager()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_providers": workflow_mgr.llm_manager.list_available_providers(),
        "registered_agents": list(agents.keys()),
        "workflow_callbacks": list(workflow_mgr.agent_callbacks.keys())
    }


@api_router.post("/workflow/execute")
async def execute_workflow(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """执行完整的LangGraph工作流"""
    
    try:
        user_request = request.get("user_request")
        context = request.get("context", {})
        max_iterations = request.get("max_iterations", 10)
        max_retries = request.get("max_retries", 3)
        
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request是必需的")
        
        workflow_mgr = await get_workflow_manager()
        
        # 执行工作流
        result = await workflow_mgr.execute_workflow(
            user_request=user_request,
            context=context,
            max_iterations=max_iterations,
            max_retries=max_retries
        )
        
        return {
            "success": True,
            "workflow_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@api_router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    
    try:
        workflow_mgr = await get_workflow_manager()
        status = await workflow_mgr.get_workflow_status(workflow_id)
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@api_router.get("/agents", response_model=Dict[str, Any])
async def list_agents():
    """列出所有可用的智能体"""
    try:
        from app.agents import list_available_agents, get_agent_info
        
        agents_list = list_available_agents()
        agent_details = {}
        
        for agent_type in agents_list:
            agent_details[agent_type] = get_agent_info(agent_type)
        
        return {
            "success": True,
            "agents": agent_details,
            "total_count": len(agents_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"列出智能体失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出智能体失败: {str(e)}")


@api_router.post("/agents/{agent_type}/execute", response_model=Dict[str, Any])
async def execute_agent(
    agent_type: str,
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """执行指定类型的智能体"""
    try:
        from app.agents import get_agent
        
        # 验证智能体类型
        valid_types = list_available_agents()
        if agent_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"不支持的智能体类型: {agent_type}")
        
        # 获取智能体实例
        agent = get_agent(agent_type)
        
        # 创建任务
        task_id = str(uuid.uuid4())
        user_request = request.get("request", "")
        context = request.get("context", {})
        
        # 生成执行计划
        plan = await agent.generate_plan(user_request, context)
        
        # 执行任务
        result = await agent.execute(user_request, context)
        
        return {
            "success": True,
            "task_id": task_id,
            "agent_type": agent_type,
            "plan": plan.to_dict() if hasattr(plan, 'to_dict') else str(plan),
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"执行智能体失败 {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=f"执行智能体失败: {str(e)}")


@api_router.post("/agents/{agent_type}/stream")
async def stream_agent_execution(
    agent_type: str,
    request: Dict[str, Any]
):
    """流式执行智能体"""
    async def generate():
        try:
            from app.agents import get_agent
            
            # 验证智能体类型
            valid_types = list_available_agents()
            if agent_type not in valid_types:
                yield f"data: {json.dumps({'error': f'不支持的智能体类型: {agent_type}'})}\n\n"
                return
            
            # 获取智能体实例
            agent = get_agent(agent_type)
            
            user_request = request.get("request", "")
            context = request.get("context", {})
            
            # 发送开始事件
            yield f"data: {json.dumps({'event': 'start', 'agent_type': agent_type, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # 生成计划
            yield f"data: {json.dumps({'event': 'planning', 'message': '正在生成执行计划...'})}\n\n"
            plan = await agent.generate_plan(user_request, context)
            
            yield f"data: {json.dumps({'event': 'plan_generated', 'plan': plan.to_dict() if hasattr(plan, 'to_dict') else str(plan)})}\n\n"
            
            # 执行步骤
            step_results = []
            for i, step in enumerate(plan.steps if hasattr(plan, 'steps') else []):
                yield f"data: {json.dumps({'event': 'step_start', 'step': i+1, 'total': len(plan.steps), 'step_name': step.name})}\n\n"
                
                step_result = await agent.execute_step(step, context)
                step_results.append(step_result)
                
                yield f"data: {json.dumps({'event': 'step_complete', 'step': i+1, 'result': step_result})}\n\n"
            
            # 发送完成事件
            final_result = await agent.aggregate_results(step_results, context)
            yield f"data: {json.dumps({'event': 'complete', 'result': final_result, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"流式执行智能体失败 {agent_type}: {e}")
            yield f"data: {json.dumps({'event': 'error', 'error': str(e), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")


@api_router.get("/agents/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """获取特定智能体的状态"""
    
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_type} 不存在")
    
    agent = agents[agent_type]
    status = agent.get_status()
    
    return {
        "success": True,
        "agent_status": status,
        "timestamp": datetime.utcnow().isoformat()
    }


@api_router.get("/agents/{agent_type}/tools")
async def get_agent_tools(agent_type: str):
    """获取智能体可用的工具"""
    
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail=f"智能体 {agent_type} 不存在")
    
    agent = agents[agent_type]
    tools = agent.get_available_tools()
    
    return {
        "success": True,
        "agent_type": agent_type,
        "available_tools": tools,
        "tools_count": len(tools),
        "timestamp": datetime.utcnow().isoformat()
    }


@api_router.post("/llm/generate")
async def generate_llm_response(
    request: Dict[str, Any],
    llm_manager: LLMClientManager = Depends(get_llm_manager)
):
    """直接调用LLM生成响应"""
    
    try:
        messages = request.get("messages", [])
        provider = request.get("provider")
        model = request.get("model")
        temperature = request.get("temperature", 0.7)
        max_tokens = request.get("max_tokens")
        
        if not messages:
            raise HTTPException(status_code=400, detail="messages是必需的")
        
        response = await llm_manager.generate_response(
            messages=messages,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response,
            "provider": provider,
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM响应生成失败: {str(e)}")


@api_router.get("/tools")
async def list_tools(
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """列出所有可用的工具"""
    
    tools = tool_registry.list_tools()
    
    return {
        "success": True,
        "tools": tools,
        "tools_count": len(tools),
        "timestamp": datetime.utcnow().isoformat()
    }


@api_router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    request: Dict[str, Any],
    tool_registry: ToolRegistry = Depends(get_tool_registry)
):
    """执行特定工具"""
    
    try:
        parameters = request.get("parameters", {})
        
        result = await tool_registry.execute_tool(tool_name, parameters)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具执行失败: {str(e)}")


# 演示端点
@api_router.post("/demo/tara-analysis")
async def demo_tara_analysis(request: Dict[str, Any]):
    """TARA分析演示端点"""
    
    try:
        # 示例：分析车联网T-Box系统
        demo_request = request.get("user_request", "分析车联网T-Box系统的安全威胁和风险")
        demo_context = request.get("context", {
            "system_description": "车联网T-Box远程信息处理单元",
            "components": ["4G/5G通信模块", "GPS定位模块", "CAN总线接口", "处理器", "存储器"],
            "interfaces": ["移动网络", "车载CAN网络", "OBD-II接口", "云端服务器"],
            "data_types": ["车辆状态数据", "位置信息", "驾驶行为数据", "诊断数据"],
            "security_requirements": "符合ISO 21434和UNECE WP.29法规要求"
        })
        
        workflow_mgr = await get_workflow_manager()
        
        # 执行TARA分析工作流
        result = await workflow_mgr.execute_workflow(
            user_request=demo_request,
            context=demo_context,
            max_iterations=5,
            max_retries=2
        )
        
        return {
            "success": True,
            "demo_type": "TARA分析",
            "demo_request": demo_request,
            "demo_context": demo_context,
            "analysis_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TARA分析演示失败: {str(e)}")


@api_router.post("/demo/test-case-generation")
async def demo_test_case_generation():
    """演示测试用例生成功能"""
    try:
        from app.agents import get_agent
        
        agent = get_agent("test_case")
        
        # 模拟TARA分析结果
        sample_tara_result = {
            "threats": [
                {
                    "id": "T001",
                    "name": "未授权访问车载网络",
                    "description": "攻击者通过CAN总线未授权访问车载网络",
                    "risk_score": 8.5,
                    "impact": "高",
                    "likelihood": "中",
                    "category": "网络安全"
                },
                {
                    "id": "T002", 
                    "name": "车载应用恶意代码注入",
                    "description": "通过OTA更新渠道注入恶意代码",
                    "risk_score": 7.2,
                    "impact": "高",
                    "likelihood": "低",
                    "category": "软件安全"
                }
            ],
            "risk_matrix": {
                "high_risk": 2,
                "medium_risk": 3,
                "low_risk": 1
            }
        }
        
        user_request = "基于TARA分析结果生成完整的安全测试用例"
        context = {"tara_result": sample_tara_result}
        
        result = await agent.execute(user_request, context)
        
        return {
            "success": True,
            "demo_type": "test_case_generation",
            "input": {
                "user_request": user_request,
                "tara_result": sample_tara_result
            },
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"测试用例生成演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


@api_router.post("/demo/automation-testing")
async def demo_automation_testing():
    """演示自动化测试功能"""
    try:
        from app.agents import get_agent
        
        agent = get_agent("automation_test")
        
        # 模拟测试用例数据
        sample_test_cases = {
            "test_cases": [
                {
                    "id": "TC001",
                    "name": "CAN总线认证绕过测试",
                    "type": "security",
                    "priority": "P0",
                    "automation_feasible": True,
                    "description": "测试CAN总线的认证机制是否可被绕过"
                },
                {
                    "id": "TC002",
                    "name": "OTA更新安全性测试", 
                    "type": "security",
                    "priority": "P1",
                    "automation_feasible": True,
                    "description": "测试OTA更新过程的安全性"
                }
            ]
        }
        
        user_request = "基于测试用例生成自动化测试脚本"
        context = {"test_cases": sample_test_cases}
        
        result = await agent.execute(user_request, context)
        
        return {
            "success": True,
            "demo_type": "automation_testing",
            "input": {
                "user_request": user_request,
                "test_cases": sample_test_cases
            },
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"自动化测试演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


@api_router.post("/demo/report-analysis")
async def demo_report_analysis():
    """演示报告分析功能"""
    try:
        from app.agents import get_agent
        
        agent = get_agent("report_analysis")
        
        # 模拟测试结果数据
        sample_test_results = {
            "tara_results": {
                "total_threats": 6,
                "high_risk_threats": 2,
                "medium_risk_threats": 3,
                "low_risk_threats": 1
            },
            "test_execution": {
                "total_tests": 25,
                "passed": 18,
                "failed": 5,
                "skipped": 2,
                "coverage": "85%"
            },
            "vulnerabilities_found": [
                {
                    "id": "V001",
                    "severity": "High",
                    "type": "Authentication Bypass",
                    "description": "CAN总线认证可被绕过"
                },
                {
                    "id": "V002", 
                    "severity": "Medium",
                    "type": "Code Injection",
                    "description": "OTA更新存在代码注入风险"
                }
            ]
        }
        
        user_request = "基于测试结果生成综合安全评估报告"
        context = {"test_results": sample_test_results}
        
        result = await agent.execute(user_request, context)
        
        return {
            "success": True,
            "demo_type": "report_analysis",
            "input": {
                "user_request": user_request,
                "test_results": sample_test_results
            },
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"报告分析演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


@api_router.post("/demo/knowledge-management")
async def demo_knowledge_management():
    """演示知识库管理功能"""
    try:
        from app.agents import get_agent
        
        agent = get_agent("knowledge_base")
        
        # 模拟项目数据
        sample_project_data = {
            "project_name": "智能网联汽车安全测试项目",
            "tara_insights": [
                "CAN总线缺乏认证机制是常见风险点",
                "OTA更新过程需要端到端安全验证",
                "车载娱乐系统是主要攻击入口"
            ],
            "test_results": {
                "effective_techniques": ["模糊测试", "渗透测试", "代码审计"],
                "common_issues": ["认证绕过", "权限提升", "数据泄露"],
                "best_practices": ["多层防护", "最小权限原则", "安全开发生命周期"]
            },
            "lessons_learned": [
                "早期威胁建模可以显著降低后期修复成本",
                "自动化测试提高了测试覆盖率和效率",
                "持续安全监控是必要的"
            ]
        }
        
        user_request = "从项目执行过程中提取和整理知识"
        context = {"project_data": sample_project_data}
        
        result = await agent.execute(user_request, context)
        
        return {
            "success": True,
            "demo_type": "knowledge_management",
            "input": {
                "user_request": user_request,
                "project_data": sample_project_data
            },
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"知识库管理演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


@api_router.post("/demo/multi-agent-workflow")
async def demo_multi_agent_workflow():
    """演示多智能体协作工作流"""
    try:
        # 模拟完整的工作流程
        workflow_steps = []
        
        # 1. TARA分析
        from app.agents import get_agent
        tara_agent = get_agent("tara")
        
        tara_request = "对智能网联汽车进行威胁分析和风险评估"
        tara_context = {
            "target_system": "智能网联汽车",
            "components": ["车载网关", "ECU", "车载娱乐系统", "OTA系统"]
        }
        
        tara_result = await tara_agent.execute(tara_request, tara_context)
        workflow_steps.append({
            "step": 1,
            "agent": "tara",
            "description": "TARA威胁分析与风险评估",
            "result": tara_result
        })
        
        # 2. 测试用例生成
        test_case_agent = get_agent("test_case")
        tc_result = await test_case_agent.execute(
            "基于TARA结果生成测试用例",
            {"tara_result": tara_result}
        )
        workflow_steps.append({
            "step": 2,
            "agent": "test_case", 
            "description": "基于TARA结果生成测试用例",
            "result": tc_result
        })
        
        # 3. 自动化测试
        automation_agent = get_agent("automation_test")
        auto_result = await automation_agent.execute(
            "生成自动化测试脚本",
            {"test_cases": tc_result}
        )
        workflow_steps.append({
            "step": 3,
            "agent": "automation_test",
            "description": "生成和执行自动化测试脚本",
            "result": auto_result
        })
        
        # 4. 报告分析
        report_agent = get_agent("report_analysis")
        report_result = await report_agent.execute(
            "生成综合安全评估报告",
            {
                "tara_result": tara_result,
                "test_cases": tc_result,
                "automation_result": auto_result
            }
        )
        workflow_steps.append({
            "step": 4,
            "agent": "report_analysis",
            "description": "综合分析结果并生成报告",
            "result": report_result
        })
        
        # 5. 知识归档
        knowledge_agent = get_agent("knowledge_base")
        knowledge_result = await knowledge_agent.execute(
            "归档项目知识和经验",
            {
                "project_results": {
                    "tara": tara_result,
                    "test_cases": tc_result,
                    "automation": auto_result,
                    "report": report_result
                }
            }
        )
        workflow_steps.append({
            "step": 5,
            "agent": "knowledge_base",
            "description": "项目知识归档和经验总结",
            "result": knowledge_result
        })
        
        return {
            "success": True,
            "demo_type": "multi_agent_workflow",
            "description": "完整的车联网安全测试生命周期管理流程",
            "workflow_steps": workflow_steps,
            "total_steps": len(workflow_steps),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"多智能体工作流演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


# 添加到主路由器
# 包含Phase 4高级功能路由
api_router.include_router(knowledge_base_router, prefix="/api/v1")
api_router.include_router(model_config_router, prefix="/api/v1")


def get_api_router() -> APIRouter:
    """获取API路由器"""
    return api_router 