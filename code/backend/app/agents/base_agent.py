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
    
    async def generate_plan(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> AgentPlan:
        """生成智能体执行计划，调用子类实现的_generate_plan方法"""
        try:
            return await self._generate_plan(user_request, context)
        except Exception as e:
            # 如果子类未实现_generate_plan，返回一个默认计划
            import uuid
            return AgentPlan(
                plan_id=str(uuid.uuid4()),
                description=f"{self.name}执行计划",
                steps=[
                    AgentStep(
                        step_id=str(uuid.uuid4()),
                        name="执行分析",
                        description=f"执行{self.name}分析",
                        tool_name=None,
                        parameters={},
                        dependencies=[]
                    )
                ]
            )
    
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
        plan = await self.generate_plan(user_request, context)
        
        # 更新当前计划
        self.current_plan = plan
        
        # 返回计划初始化信息
        yield {
            "type": "plan_init",
            "plan": plan.to_dict()
        }
        
        # 逐步执行计划
        results = {}
        
        for step in plan.steps:
            # 更新步骤状态
            step.status = "running"
            step.started_at = datetime.utcnow()
            
            # 返回步骤开始信息
            yield {
                "type": "step_start",
                "step_id": step.step_id,
                "step_name": step.name,
                "timestamp": step.started_at.isoformat()
            }
            
            try:
                # 执行步骤
                step_context = (context or {}).copy()
                step_context.update({
                    "previous_results": results,
                    "plan": plan.to_dict()
                })
                
                if hasattr(self, "execute_step"):
                    step_result = await self.execute_step(step, step_context)
                else:
                    # 如果没有实现execute_step，使用默认方法
                    step_result = {
                        "success": True, 
                        "result": f"{step.name}已执行",
                        "step_id": step.step_id
                    }
                
                # 更新步骤状态
                step.status = "completed"
                step.completed_at = datetime.utcnow()
                
                # 保存结果
                if step_result.get("success", False):
                    results[step.name] = step_result.get("result", {})
                    step.result = step_result
                
                                # 返回步骤完成信息
                yield {
                    "type": "step_complete",
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "result": step_result,
                    "timestamp": step.completed_at.isoformat()
                }
            
            except Exception as e:
                # 更新步骤状态
                step.status = "failed"
                step.error = str(e)
                step.completed_at = datetime.utcnow()
                
                # 返回步骤失败信息
                yield {
                    "type": "step_failed",
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "error": str(e),
                    "timestamp": step.completed_at.isoformat()
                }
                
                # 判断是否继续执行
                if not self._should_continue_after_failure(step):
                    break
        
        # 更新计划状态
        plan.update_progress()
        
        # 返回计划完成信息
        yield {
            "type": "plan_complete",
            "plan": plan.to_dict(),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 保存到执行历史
        self.execution_history.append(plan)
    
    def _should_continue_after_failure(self, failed_step: AgentStep) -> bool:
        """判断步骤失败后是否继续执行，子类可以重写"""
        return False
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词，子类可以重写"""
        return f"""
你是一个专业的{self.name}，负责{self.description}。
你需要按照专业标准执行任务，提供详细的分析结果和建议。
"""
    
    def _build_user_prompt(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """构建用户提示词，子类可以重写"""
        prompt = f"请执行以下任务：{user_request}\n\n"
        
        if context:
            prompt += f"上下文信息：\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        
        prompt += f"请提供详细的分析结果，包括所有必要的信息。"
        
        return prompt
    
    def _get_tools_description(self) -> str:
        """获取工具描述，用于提示词"""
        tools = self.get_available_tools()
        if not tools:
            return ""
        
        tools_desc = "可用工具:\n"
        for tool_name, tool_info in tools.items():
            tools_desc += f"- {tool_name}: {tool_info.get('description', '')}\n"
        
        return tools_desc
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的工具列表，子类可以重写"""
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.get_agent_type(),
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "execution_history_count": len(self.execution_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @abstractmethod
    async def execute(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        plan_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行智能体任务，子类必须实现"""
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """获取智能体类型，子类必须实现"""
        pass 