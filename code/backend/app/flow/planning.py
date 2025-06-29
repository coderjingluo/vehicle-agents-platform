import json
import re
from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, List

from app.flow.base import BaseFlow, FlowStatus, FlowStep
from app.agent.base import BaseAgent


class PlanningFlow(BaseFlow):
    """规划执行流"""
    
    def __init__(self, flow_id: str, name: str, description: Optional[str] = None, 
                planning_agent: Optional[str] = None, agent_factory=None):
        super().__init__(flow_id, name, description)
        self.planning_agent_name = planning_agent or "toolcall"  # 默认使用工具调用智能体
        self.step_statuses = {}  # 步骤状态管理
        self.agent_factory = agent_factory  # 智能体工厂函数或实例
        self.ws_manager = None  # WebSocket管理器，可选
    
    async def initialize(self, task: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """初始化规划执行流"""
        try:
            # 设置上下文
            self.context = context or {}
            self.context["task"] = task
            
            # 创建计划步骤
            planning_step = FlowStep(
                id="planning",
                name="制定执行计划",
                description="根据任务目标制定详细的执行计划",
                executor=self.planning_agent_name
            )
            self.steps["planning"] = planning_step
            
            return True
        except Exception as e:
            self.error = f"初始化规划执行流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            return False
    
    async def execute_step(self, step: FlowStep) -> FlowStep:
        """执行单个步骤"""
        if step.id == "planning":
            # 执行规划步骤
            return await self._execute_planning_step(step)
        else:
            # 执行常规步骤
            return await self._execute_regular_step(step)
    
    async def _execute_planning_step(self, step: FlowStep) -> FlowStep:
        """执行规划步骤，创建执行计划"""
        try:
            # 获取规划智能体
            agent = await self._get_agent(step.executor)
            
            # 获取任务和上下文
            task = self.context.get("task", "")
            
            # 使用智能体创建执行计划
            planning_prompt = f"""
            你需要为以下任务制定详细的执行计划:
            
            {task}
            
            请提供一个分步执行计划，包括每个步骤的:
            1. 步骤ID
            2. 步骤名称
            3. 步骤描述
            4. 合适的执行者(智能体类型)
            5. 任何依赖的步骤ID
            
            以JSON格式返回计划:
            ```json
            {{
                "steps": [
                    {{
                        "id": "step1",
                        "name": "步骤名称",
                        "description": "步骤详细描述",
                        "executor": "适合的智能体类型",
                        "dependencies": []
                    }},
                    // 更多步骤...
                ]
            }}
            ```
            """
            
            # 执行规划
            response = await agent.run(planning_prompt)
            
            # 解析规划结果
            plan = self._parse_planning_response(response)
            
            # 更新步骤状态
            step.status = FlowStatus.COMPLETED
            step.output = {"plan": plan}
            
            # 根据计划创建后续步骤
            for plan_step in plan.get("steps", []):
                step_id = plan_step.get("id")
                self.steps[step_id] = FlowStep(
                    id=step_id,
                    name=plan_step.get("name", ""),
                    description=plan_step.get("description", ""),
                    executor=plan_step.get("executor", "toolcall"),
                    dependencies=plan_step.get("dependencies", [])
                )
            
            return step
        except Exception as e:
            step.status = FlowStatus.FAILED
            step.error = f"规划失败: {str(e)}"
            raise
    
    async def _execute_regular_step(self, step: FlowStep) -> FlowStep:
        """执行常规步骤"""
        try:
            # 获取步骤的执行者智能体
            agent = await self._get_agent(step.executor)
            
            # 准备执行上下文
            execution_context = self._prepare_execution_context(step)
            
            # 执行步骤
            response = await agent.run(
                f"""
                请执行以下任务步骤:
                
                步骤: {step.name}
                描述: {step.description}
                
                任务上下文:
                {execution_context}
                
                请提供执行结果，以及下一步的建议。
                """
            )
            
            # 更新步骤状态
            step.status = FlowStatus.COMPLETED
            step.output = {"result": response}
            
            return step
        except Exception as e:
            step.status = FlowStatus.FAILED
            step.error = f"执行步骤失败: {str(e)}"
            raise
    
    async def _get_agent(self, agent_type: str):
        """获取指定类型的智能体"""
        if not self.agent_factory:
            raise ValueError("Agent factory is not provided")
        
        return await self.agent_factory.get_agent(agent_type)
    
    def _parse_planning_response(self, response: str) -> Dict[str, Any]:
        """解析规划响应中的JSON计划"""
        # 提取JSON部分
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析整个响应
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("无法从响应中解析出有效的JSON计划")
    
    def _prepare_execution_context(self, step: FlowStep) -> str:
        """准备步骤执行的上下文信息"""
        context_parts = []
        
        # 添加任务描述
        task = self.context.get("task", "")
        if task:
            context_parts.append(f"任务: {task}")
        
        # 添加依赖步骤的输出
        for dep_id in step.dependencies:
            if dep_id in self.steps and self.steps[dep_id].output:
                dep_step = self.steps[dep_id]
                context_parts.append(f"步骤 '{dep_step.name}' 的结果: {dep_step.output.get('result', '')}")
        
        # 添加额外上下文信息
        for key, value in self.context.items():
            if key != "task":
                context_parts.append(f"{key}: {value}")
        
        return "\n\n".join(context_parts)

    async def _create_plan(self, request: str) -> bool:
        """创建执行计划"""
        # 获取计划智能体
        planning_agent = await self._get_agent(self.planning_agent_name)
        
        # 为计划创建提示
        prompt = f"为以下任务创建详细执行计划：\n\n{request}\n\n" \
                f"计划应包括明确的步骤，并考虑到可能的依赖关系。"
        
        # 使用智能体生成计划
        try:
            # 执行计划生成
            response = await planning_agent.run(prompt)
            
            # 解析并保存计划
            plan = self._parse_planning_response(response)
            
            # 创建步骤
            self._create_steps_from_plan(plan)
            
            return True
        except Exception as e:
            self.error = f"计划创建失败：{str(e)}"
            self.status = FlowStatus.FAILED
            return False
    
    def _create_steps_from_plan(self, plan: Dict[str, Any]) -> None:
        """从计划创建步骤"""
        if "steps" not in plan:
            raise ValueError("计划中没有找到步骤列表")
            
        for step_data in plan["steps"]:
            step_id = step_data.get("id")
            if not step_id:
                continue
                
            self.steps[step_id] = FlowStep(
                id=step_id,
                name=step_data.get("name", ""),
                description=step_data.get("description", ""),
                executor=step_data.get("executor", "toolcall"),
                dependencies=step_data.get("dependencies", [])
            )
    
    async def _execute_step(self, executor: BaseAgent, step_info: dict) -> str:
        """执行单个步骤"""
        try:
            # 1. 设置步骤状态为执行中
            await self._update_step_status(self.current_step_id, FlowStatus.RUNNING)
            
            # 2. 格式化步骤描述为提示
            step_prompt = self._format_step_prompt(step_info)
            
            # 3. 使用执行器执行步骤
            step_result = await executor.run(step_prompt)
            
            # 4. 将结果保存到上下文
            self.context[f"step_{self.current_step_id}_result"] = step_result
            
            # 5. 标记步骤完成
            await self._update_step_status(self.current_step_id, FlowStatus.COMPLETED)
            
            return step_result
        except Exception as e:
            # 处理步骤执行失败
            await self._update_step_status(self.current_step_id, FlowStatus.FAILED)
            return f"步骤执行失败: {str(e)}"
    
    def _format_step_prompt(self, step_info: dict) -> str:
        """格式化步骤提示"""
        # 获取步骤文本
        step_text = step_info.get("text", "")
        
        # 获取之前步骤的结果作为上下文
        context_info = ""
        for step_id, step in self.steps.items():
            if step.status == FlowStatus.COMPLETED and f"step_{step_id}_result" in self.context:
                context_info += f"\n\n### 前序步骤 '{step.name}' 的结果:\n"
                context_info += self.context[f"step_{step_id}_result"]
        
        # 构建最终提示
        prompt = f"""### 当前任务步骤:
{step_text}

### 任务上下文:
{self.description}
{context_info}

请执行当前步骤，并提供详细的结果和发现。"""

        return prompt
    
    async def _update_step_status(self, step_id: str, status: FlowStatus) -> None:
        """更新步骤状态"""
        if step_id in self.steps:
            self.steps[step_id].status = status
            self.step_statuses[step_id] = status
            
            # 如果有WebSocket连接，发送状态更新
            if hasattr(self, "ws_manager") and getattr(self, "ws_manager", None):
                await self._notify_status_update()
    
    async def _notify_status_update(self) -> None:
        """通过WebSocket发送状态更新通知"""
        status_data = {
            "type": "step_status_update",
            "flow_id": self.id,
            "step_id": self.current_step_id,
            "status": self.steps[self.current_step_id].status,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.current_step_id in self.context:
            status_data["partial_result"] = self.context[self.current_step_id][:100] + "..." if len(self.context.get(self.current_step_id, "")) > 100 else self.context.get(self.current_step_id, "")
        
        await self.ws_manager.broadcast(f"flow_{self.id}", status_data)
    
    async def _visualize_plan(self) -> str:
        """生成计划可视化表示"""
        # 构建Mermaid流程图
        mermaid_code = "```mermaid\nflowchart TD\n"
        
        # 添加节点
        for step_id, step in self.steps.items():
            status = step.status
            style_class = "default"
            
            if status == FlowStatus.COMPLETED:
                style_class = "completed:::done"
            elif status == FlowStatus.RUNNING:
                style_class = "running:::active"
            elif status == FlowStatus.FAILED:
                style_class = "failed:::error"
                
            mermaid_code += f"    {step_id}[{step.name}]:::{style_class}\n"
        
        # 添加连接
        for step_id, step in self.steps.items():
            for dep_id in step.dependencies:
                mermaid_code += f"    {dep_id} --> {step_id}\n"
        
        # 添加样式
        mermaid_code += "    classDef done fill:#d4edda,stroke:#28a745\n"
        mermaid_code += "    classDef active fill:#fff3cd,stroke:#ffc107\n"
        mermaid_code += "    classDef error fill:#f8d7da,stroke:#dc3545\n"
        mermaid_code += "```"
        
        return mermaid_code
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """获取详细的执行状态"""
        # 基本状态信息
        status_info = self.get_status()
        
        # 添加步骤详细信息
        status_info["steps"] = {}
        for step_id, step in self.steps.items():
            status_info["steps"][step_id] = {
                "id": step_id,
                "name": step.name,
                "description": step.description,
                "status": step.status,
                "dependencies": step.dependencies,
                "has_output": f"step_{step_id}_result" in self.context,
                "error": step.error
            }
        
        # 添加可视化
        status_info["visualization"] = asyncio.run(self._visualize_plan())
        
        return status_info 