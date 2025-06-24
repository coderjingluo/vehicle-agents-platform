"""
基础智能体类
实现所有智能体的通用能力：任务分解、步骤执行、结果聚合
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
import json
from datetime import datetime

from app.core.llm_client import LLMClientManager, get_llm_manager
from app.core.tool_registry import ToolRegistry, get_tool_registry
from app.core.task_decomposer import TaskDecomposer
from app.core.step_executor import StepExecutor
from app.core.result_aggregator import ResultAggregator


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
    
    def __init__(self, plan_id: str, description: str, steps: List[AgentStep]):
        self.plan_id = plan_id
        self.description = description
        self.steps = steps
        self.created_at = datetime.utcnow()
        self.status = "pending"  # pending, running, completed, failed, cancelled
    
    def get_step(self, step_id: str) -> Optional[AgentStep]:
        """获取步骤"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[AgentStep]:
        """获取可以执行的步骤"""
        ready_steps = []
        completed_step_ids = {step.step_id for step in self.steps if step.status == "completed"}
        
        for step in self.steps:
            if step.status == "pending":
                # 检查依赖是否都已完成
                if all(dep_id in completed_step_ids for dep_id in step.dependencies):
                    ready_steps.append(step)
        
        return ready_steps
    
    @property
    def is_completed(self) -> bool:
        """判断计划是否完成"""
        return all(step.status in ["completed", "failed"] for step in self.steps)
    
    @property
    def progress(self) -> float:
        """计算进度百分比"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == "completed")
        return (completed_steps / len(self.steps)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "progress": self.progress,
            "is_completed": self.is_completed
        }


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        llm_manager: Optional[LLMClientManager] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        
        # 智能体通用能力组件
        self.llm_manager = llm_manager or get_llm_manager()
        self.tool_registry = tool_registry or get_tool_registry()
        self.task_decomposer = TaskDecomposer(self.llm_manager)
        self.step_executor = StepExecutor(self.tool_registry)
        self.result_aggregator = ResultAggregator(self.llm_manager)
        
        # 执行状态
        self.current_plan: Optional[AgentPlan] = None
        self.execution_history: List[AgentPlan] = []
    
    async def generate_plan(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> AgentPlan:
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
        
        # 解析计划
        plan = await self.task_decomposer.decompose(response, self.get_available_tools())
        
        self.current_plan = plan
        return plan
    
    async def execute_plan(self, plan: AgentPlan) -> Dict[str, Any]:
        """执行计划"""
        plan.status = "running"
        results = []
        
        try:
            while not plan.is_completed:
                # 获取可以执行的步骤
                ready_steps = plan.get_ready_steps()
                
                if not ready_steps:
                    # 没有可执行的步骤，检查是否有失败的步骤
                    failed_steps = [step for step in plan.steps if step.status == "failed"]
                    if failed_steps:
                        raise Exception(f"执行失败: {failed_steps[0].error}")
                    break
                
                # 并行执行准备好的步骤
                for step in ready_steps:
                    step_result = await self.step_executor.execute(step)
                    results.append(step_result)
            
            # 聚合结果
            final_result = await self.result_aggregator.aggregate(results)
            plan.status = "completed"
            
            return final_result
            
        except Exception as e:
            plan.status = "failed"
            raise e
        finally:
            self.execution_history.append(plan)
    
    async def process(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用处理流程：生成计划 -> 执行计划 -> 返回结果"""
        
        # 生成执行计划
        plan = await self.generate_plan(user_request, context)
        
        # 执行计划
        result = await self.execute_plan(plan)
        
        # 调用专业化处理逻辑
        specialized_result = await self.execute(user_request, context, result)
        
        return specialized_result
    
    async def stream_process(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理"""
        
        # 生成计划
        yield {"type": "planning", "message": "正在生成执行计划..."}
        plan = await self.generate_plan(user_request, context)
        yield {"type": "plan", "data": plan.to_dict()}
        
        # 执行计划
        plan.status = "running"
        results = []
        
        try:
            while not plan.is_completed:
                ready_steps = plan.get_ready_steps()
                
                if not ready_steps:
                    break
                
                for step in ready_steps:
                    yield {"type": "step_start", "step": step.to_dict()}
                    
                    step_result = await self.step_executor.execute(step)
                    results.append(step_result)
                    
                    yield {"type": "step_complete", "step": step.to_dict(), "result": step_result}
                    yield {"type": "progress", "progress": plan.progress}
            
            # 聚合结果
            yield {"type": "aggregating", "message": "正在聚合结果..."}
            final_result = await self.result_aggregator.aggregate(results)
            
            # 专业化处理
            yield {"type": "specializing", "message": "正在进行专业化处理..."}
            specialized_result = await self.execute(user_request, context, final_result)
            
            plan.status = "completed"
            yield {"type": "completed", "result": specialized_result}
            
        except Exception as e:
            plan.status = "failed"
            yield {"type": "error", "error": str(e)}
        finally:
            self.execution_history.append(plan)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""
你是一个名为{self.name}的专业智能体。

描述: {self.description}

可用工具:
{self._get_tools_description()}

你的任务是分析用户请求，制定详细的执行计划。计划应该包含具体的步骤，每个步骤都要指定使用的工具和参数。

请以JSON格式返回执行计划，格式如下：
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
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "execution_history_count": len(self.execution_history),
            "available_tools_count": len(self.get_available_tools())
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
        """获取智能体类型"""
        pass 