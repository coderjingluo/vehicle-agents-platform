"""
基础智能体类
实现所有智能体的通用能力：LangGraph工作流集成、工具管理
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
import json
from datetime import datetime

from app.core.llm_client import LLMClientManager, get_llm_manager
from app.core.tool_registry import ToolRegistry, get_tool_registry
from app.core.langgraph_workflow import LangGraphWorkflowManager, WorkflowState


class AgentStep:
    """智能体执行步骤"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None
    ):
        self.step_id = step_id
        self.name = name
        self.description = description
        self.tool_name = tool_name
        self.parameters = parameters or {}
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, running, completed, failed
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class AgentPlan:
    """智能体执行计划"""
    
    def __init__(
        self,
        plan_id: str,
        description: str,
        steps: List[AgentStep]
    ):
        self.plan_id = plan_id
        self.description = description
        self.steps = steps
        self.status = "pending"  # pending, running, completed, failed
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_steps = len(steps)
        self.completed_steps = 0
        self.failed_steps = 0
    
    def update_progress(self):
        """更新进度"""
        self.completed_steps = sum(1 for step in self.steps if step.status == "completed")
        self.failed_steps = sum(1 for step in self.steps if step.status == "failed")
        
        if self.failed_steps > 0:
            self.status = "failed"
        elif self.completed_steps == self.total_steps:
            self.status = "completed"
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif any(step.status == "running" for step in self.steps):
            self.status = "running"
            if not self.started_at:
                self.started_at = datetime.utcnow()
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_steps == 0:
            return 100.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        self.update_progress()
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "status": self.status,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "progress_percentage": self.get_progress_percentage(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [step.to_dict() for step in self.steps]
        }


class BaseAgent(ABC):
    """基础智能体类 - 支持LangGraph工作流"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        llm_manager: Optional[LLMClientManager] = None,
        tool_registry: Optional[ToolRegistry] = None,
        workflow_manager: Optional[LangGraphWorkflowManager] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        
        # 智能体通用能力组件
        self.llm_manager = llm_manager or get_llm_manager()
        self.tool_registry = tool_registry or get_tool_registry()
        
        # LangGraph工作流管理器
        self.workflow_manager = workflow_manager or LangGraphWorkflowManager(
            self.llm_manager, 
            self.tool_registry
        )
        
        # 执行状态
        self.current_plan: Optional[AgentPlan] = None
        self.execution_history: List[AgentPlan] = []
        
        # 注册自己到工作流管理器
        self._register_to_workflow()
    
    def _register_to_workflow(self):
        """注册到工作流管理器"""
        agent_type = self.get_agent_type()
        self.workflow_manager.register_agent_callback(agent_type, self._workflow_callback)
    
    async def _workflow_callback(self, state: WorkflowState) -> Dict[str, Any]:
        """工作流回调 - 被LangGraph调用"""
        try:
            # 从工作流状态中提取上下文
            context = {
                "workflow_id": state["workflow_id"],
                "user_request": state["user_request"],
                "messages": state["messages"],
                "context": state["context"]
            }
            
            # 根据智能体类型获取相关的前置结果
            if self.get_agent_type() == "test_case" and state.get("tara_result"):
                context["tara_result"] = state["tara_result"]
            elif self.get_agent_type() == "automation" and state.get("test_case_result"):
                context["test_case_result"] = state["test_case_result"]
            elif self.get_agent_type() == "report":
                context["tara_result"] = state.get("tara_result")
                context["test_case_result"] = state.get("test_case_result")
                context["automation_result"] = state.get("automation_result")
            elif self.get_agent_type() == "knowledge":
                context["all_results"] = {
                    "tara": state.get("tara_result"),
                    "test_case": state.get("test_case_result"),
                    "automation": state.get("automation_result"),
                    "report": state.get("report_result")
                }
            
            # 执行具体的智能体逻辑
            result = await self.execute(
                user_request=state["user_request"],
                context=context
            )
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "agent_id": self.agent_id
            }
    
    async def generate_llm_plan(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """基于大模型生成执行计划"""
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt()
        
        # 构建用户请求
        user_prompt = self._build_user_prompt(user_request, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用LLM生成计划
        response = await self.llm_manager.generate_response(messages)
        
        try:
            # 尝试解析JSON响应
            plan_data = json.loads(response.strip())
            return {
                "success": True,
                "plan": plan_data,
                "raw_response": response
            }
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始响应
            return {
                "success": False,
                "plan": None,
                "raw_response": response,
                "error": "LLM响应不是有效的JSON格式"
            }
    
    async def execute_with_workflow(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用LangGraph工作流执行"""
        return await self.workflow_manager.execute_workflow(
            user_request=user_request,
            context=context
        )
    
    async def execute_stream(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行 - 实时返回执行状态"""
        
        # 生成计划
        plan_result = await self.generate_llm_plan(user_request, context)
        
        yield {
            "type": "plan_generated",
            "data": plan_result
        }
        
        if not plan_result["success"]:
            yield {
                "type": "error",
                "data": {"error": "计划生成失败", "details": plan_result}
            }
            return
        
        # 执行计划
        try:
            result = await self.execute(user_request, context, plan_result["plan"])
            
            yield {
                "type": "execution_completed",
                "data": result
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""
你是一个名为{self.name}的专业智能体。

描述: {self.description}

可用工具:
{self._get_tools_description()}

你的任务是分析用户请求，制定详细的执行计划或直接处理请求。

请根据请求的复杂度选择合适的回复方式：
1. 对于复杂任务：返回JSON格式的执行计划
2. 对于简单任务：直接返回处理结果

JSON计划格式：
{{
    "plan_id": "唯一计划ID",
    "description": "计划描述",
    "steps": [
        {{
            "step_id": "步骤ID",
            "name": "步骤名称",
            "description": "步骤描述",
            "tool_name": "工具名称",
            "parameters": {{"param1": "value1"}},
            "dependencies": ["依赖的步骤ID列表"]
        }}
    ]
}}
"""
    
    def _build_user_prompt(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """构建用户提示词"""
        prompt = f"用户请求: {user_request}"
        
        if context:
            prompt += f"\n\n上下文信息: {json.dumps(context, ensure_ascii=False, indent=2)}"
        
        return prompt
    
    def _get_tools_description(self) -> str:
        """获取工具描述"""
        tools = self.get_available_tools()
        descriptions = []
        
        for tool_name, tool in tools.items():
            desc = f"- {tool_name}: {tool.get('description', '无描述')}"
            if 'parameters' in tool:
                params = tool['parameters']
                desc += f"\n  参数: {', '.join(params.keys())}"
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取可用工具列表（子类可重写以过滤工具）"""
        return self.tool_registry.list_tools()
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.get_agent_type(),
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "execution_history_count": len(self.execution_history),
            "available_tools_count": len(self.get_available_tools()),
            "workflow_registered": self.get_agent_type() in self.workflow_manager.agent_callbacks
        }
    
    @abstractmethod
    async def execute(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        plan_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """子类必须实现的具体执行方法"""
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """获取智能体类型（用于工作流注册）"""
        pass 