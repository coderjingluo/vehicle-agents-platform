# 执行流系统详细设计

## 1. 执行流系统概述

执行流系统是整个平台的核心控制组件，负责管理复杂任务的执行流程、协调多智能体协作、跟踪执行状态和处理异常情况。参考OpenManus项目中的flow模块设计，我们将构建一个灵活可扩展的执行流架构，支持各种类型的复杂工作流。

### 1.1 执行流系统架构

```
┌────────────────────┐      ┌────────────────────┐
│                    │      │                    │
│    用户请求层      │◄────►│    API服务层       │
│                    │      │                    │
└─────────┬──────────┘      └─────────┬──────────┘
          │                           │
          │                           ▼
┌─────────▼──────────────────────────────────────┐
│                                                │
│               执行流系统                        │
│                                                │
│  ┌─────────────────────┐  ┌─────────────────┐  │
│  │                     │  │                 │  │
│  │     基础Flow        │  │   专业化Flow    │  │
│  │                     │  │                 │  │
│  └─────────────────────┘  └─────────────────┘  │
│                                                │
└──────────────────────┬───────────────────────┬─┘
                       │                       │
          ┌────────────▼─────────┐   ┌─────────▼────────┐
          │                      │   │                  │
          │     智能体系统       │   │     工具系统     │
          │                      │   │                  │
          └──────────────────────┘   └──────────────────┘
```

### 1.2 执行流设计原则

- **声明式定义**: 通过简洁清晰的方式声明执行流程和条件
- **状态隔离**: 明确的状态管理和流程控制
- **可重试性**: 允许从失败点恢复和重试
- **可观测性**: 完整的执行日志和状态跟踪
- **可配置性**: 支持灵活的流程配置和调整
- **可扩展性**: 易于扩展新的执行流类型

## 2. 基础执行流设计

### 2.1 执行流基类 (BaseFlow)

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FlowStatus(str, Enum):
    """执行流状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    PAUSED = "paused"         # 已暂停


class FlowStep(BaseModel):
    """执行流步骤定义"""
    id: str                               # 步骤ID
    name: str                             # 步骤名称
    description: Optional[str] = None     # 步骤描述
    status: FlowStatus = FlowStatus.PENDING  # 当前状态
    input: Dict[str, Any] = {}            # 输入参数
    output: Optional[Dict[str, Any]] = None  # 输出结果
    error: Optional[str] = None           # 错误信息
    executor: Optional[str] = None        # 执行器（如智能体名称）
    dependencies: List[str] = []          # 依赖的步骤ID
    retry_count: int = 0                  # 已重试次数
    max_retries: int = 3                  # 最大重试次数


class BaseFlow(ABC):
    """执行流基类"""
    
    def __init__(self, flow_id: str, name: str, description: Optional[str] = None):
        self.id = flow_id                            # 流程ID
        self.name = name                             # 流程名称
        self.description = description               # 流程描述
        self.status = FlowStatus.PENDING             # 当前状态
        self.steps: Dict[str, FlowStep] = {}         # 步骤字典
        self.current_step_id: Optional[str] = None   # 当前执行的步骤ID
        self.context: Dict[str, Any] = {}            # 上下文数据
        self.error: Optional[str] = None             # 错误信息
    
    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """初始化执行流，创建步骤和设置初始参数"""
        pass
    
    @abstractmethod
    async def execute_step(self, step: FlowStep) -> FlowStep:
        """执行单个步骤"""
        pass
    
    async def execute(self) -> bool:
        """执行整个流程"""
        if self.status == FlowStatus.RUNNING:
            raise RuntimeError("Flow is already running")
        
        try:
            # 更新状态为运行中
            self.status = FlowStatus.RUNNING
            
            # 获取未执行或失败的步骤
            pending_steps = self._get_executable_steps()
            
            # 循环执行步骤直到所有步骤完成
            while pending_steps:
                # 获取下一个可执行步骤
                step_id = next(iter(pending_steps))
                step = self.steps[step_id]
                
                # 更新当前步骤
                self.current_step_id = step_id
                
                # 执行步骤
                try:
                    self.steps[step_id] = await self.execute_step(step)
                except Exception as e:
                    # 步骤执行失败
                    self.steps[step_id].status = FlowStatus.FAILED
                    self.steps[step_id].error = str(e)
                    
                    # 检查是否需要重试
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        self.steps[step_id].status = FlowStatus.PENDING
                    else:
                        # 超过最大重试次数，整个流程失败
                        self.status = FlowStatus.FAILED
                        self.error = f"Step {step_id} failed: {str(e)}"
                        return False
                
                # 更新可执行步骤列表
                pending_steps = self._get_executable_steps()
            
            # 所有步骤执行完成
            self.status = FlowStatus.COMPLETED
            return True
        except Exception as e:
            # 流程执行异常
            self.status = FlowStatus.FAILED
            self.error = str(e)
            return False
    
    def _get_executable_steps(self) -> Dict[str, FlowStep]:
        """获取当前可执行的步骤"""
        executable = {}
        
        for step_id, step in self.steps.items():
            # 跳过已完成的步骤
            if step.status == FlowStatus.COMPLETED:
                continue
            
            # 检查是否状态为未执行
            if step.status != FlowStatus.PENDING:
                continue
            
            # 检查依赖是否满足
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_step = self.steps.get(dep_id)
                if not dep_step or dep_step.status != FlowStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                executable[step_id] = step
        
        return executable
    
    async def pause(self) -> bool:
        """暂停执行流"""
        if self.status != FlowStatus.RUNNING:
            return False
        
        self.status = FlowStatus.PAUSED
        return True
    
    async def resume(self) -> bool:
        """恢复执行流"""
        if self.status != FlowStatus.PAUSED:
            return False
        
        self.status = FlowStatus.RUNNING
        return await self.execute()
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态和进度"""
        total_steps = len(self.steps)
        completed_steps = sum(1 for step in self.steps.values() if step.status == FlowStatus.COMPLETED)
        failed_steps = sum(1 for step in self.steps.values() if step.status == FlowStatus.FAILED)
        
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "progress": {
                "total": total_steps,
                "completed": completed_steps,
                "failed": failed_steps,
                "pending": total_steps - completed_steps - failed_steps,
                "percentage": int(completed_steps / total_steps * 100) if total_steps > 0 else 0
            },
            "current_step": self.current_step_id,
            "error": self.error
        }
    
    def get_result(self) -> Dict[str, Any]:
        """获取执行流的结果"""
        if self.status != FlowStatus.COMPLETED:
            raise ValueError(f"Flow is not completed yet, current status: {self.status}")
        
        results = {}
        for step_id, step in self.steps.items():
            if step.output:
                results[step_id] = step.output
        
        return {
            "flow_id": self.id,
            "results": results,
            "context": self.context
        }
```

## 3. 规划执行流设计

参考OpenManus项目的PlanningFlow设计，实现以下规划执行流：

### 3.1 规划执行流 (PlanningFlow)

规划执行流是一种特殊类型的执行流，它首先制定执行计划，然后按照计划分步执行。

```python
class PlanningFlow(BaseFlow):
    """规划执行流"""
    
    def __init__(self, flow_id: str, name: str, description: Optional[str] = None, 
                planning_agent: Optional[str] = None, agent_factory=None):
        super().__init__(flow_id, name, description)
        self.planning_agent_name = planning_agent or "toolcall"  # 默认使用工具调用智能体
        self.step_statuses = {}  # 步骤状态管理
        self.agent_factory = agent_factory  # 智能体工厂函数或实例
    
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
        import json
        import re
        
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
        planning_agent = self._get_agent(self.planning_agent_name)
        
        # 为计划创建提示
        prompt = f"为以下任务创建详细执行计划：\n\n{request}\n\n" \
                f"计划应包括明确的步骤，并考虑到可能的依赖关系。"
        
        # 使用智能体生成计划
        try:
            # 执行计划生成
            response = await planning_agent.run(prompt)
            
            # 解析并保存计划
            plan = self._parse_plan(response)
            
            # 创建步骤
            self._create_steps_from_plan(plan)
            
            return True
        except Exception as e:
            self.error = f"计划创建失败：{str(e)}"
            self.status = FlowStatus.FAILED
            return False
    
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
```

## 4. 专业执行流设计

根据不同业务场景，我们定义以下特定领域的执行流：

### 4.1 TARA分析流 (TaraAnalysisFlow)

```python
class TaraAnalysisFlow(PlanningFlow):
    """TARA分析执行流"""
    
    def __init__(self, flow_id: str, name: str = "TARA分析", 
                description: Optional[str] = "威胁分析与风险评估执行流程",
                planning_agent: Optional[str] = "TARA",
                agent_factory=None):
        super().__init__(flow_id, name, description, planning_agent, agent_factory)
    
    async def initialize(self, target_system: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """初始化TARA分析流"""
        try:
            # 设置上下文
            self.context = context or {}
            self.context["target_system"] = target_system
            
            # 构建TARA分析任务描述
            task = f"""
            对以下车联网系统进行威胁分析与风险评估(TARA):
            
            {target_system}
            
            需要完成的任务:
            1. 识别系统资产和边界
            2. 分析潜在威胁
            3. 评估风险等级
            4. 提出缓解措施建议
            5. 检查法规合规性
            """
            
            self.context["task"] = task
            
            # 调用基类初始化方法
            return await super().initialize(task, self.context, **kwargs)
        except Exception as e:
            self.error = f"初始化TARA分析流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            return False
```

### 4.2 测试用例生成流 (TestCaseGenerationFlow)

```python
class TestCaseGenerationFlow(PlanningFlow):
    """测试用例生成执行流"""
    
    def __init__(self, flow_id: str, name: str = "测试用例生成", 
                description: Optional[str] = "基于TARA分析结果生成测试用例",
                planning_agent: Optional[str] = "TestCase",
                agent_factory=None):
        super().__init__(flow_id, name, description, planning_agent, agent_factory)
    
    async def initialize(self, tara_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """初始化测试用例生成流"""
        try:
            # 设置上下文
            self.context = context or {}
            self.context["tara_result"] = tara_result
            
            # 构建测试用例生成任务描述
            task = f"""
            基于以下TARA分析结果生成测试用例:
            
            {json.dumps(tara_result, indent=2, ensure_ascii=False)}
            
            需要生成的测试用例类型:
            1. 确认测试(Confirmation Test)
            2. 验证测试(Validation Test)
            
            每个测试用例需要包括:
            1. 测试ID和标题
            2. 测试目的
            3. 测试步骤
            4. 预期结果
            5. 跟踪到的威胁/风险
            """
            
            self.context["task"] = task
            
            # 调用基类初始化方法
            return await super().initialize(task, self.context, **kwargs)
        except Exception as e:
            self.error = f"初始化测试用例生成流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            return False
```

### 4.3 自动化测试流 (AutomationTestFlow)

```python
class AutomationTestFlow(PlanningFlow):
    """自动化测试执行流"""
    
    def __init__(self, flow_id: str, name: str = "自动化测试执行", 
                description: Optional[str] = "执行自动化测试并收集结果",
                planning_agent: Optional[str] = "AutomationTest",
                agent_factory=None):
        super().__init__(flow_id, name, description, planning_agent, agent_factory)
    
    async def initialize(self, test_cases: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """初始化自动化测试流"""
        try:
            # 设置上下文
            self.context = context or {}
            self.context["test_cases"] = test_cases
            
            # 构建自动化测试任务描述
            task = f"""
            基于以下测试用例执行自动化测试:
            
            {json.dumps(test_cases, indent=2, ensure_ascii=False)}
            
            需要完成的任务:
            1. 准备测试环境
            2. 生成测试脚本
            3. 执行测试脚本
            4. 收集测试结果
            5. 进行初步分析
            """
            
            self.context["task"] = task
            
            # 调用基类初始化方法
            return await super().initialize(task, self.context, **kwargs)
        except Exception as e:
            self.error = f"初始化自动化测试流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            return False
```

### 4.4 报告生成流 (ReportGenerationFlow)

```python
class ReportGenerationFlow(PlanningFlow):
    """测试报告生成执行流"""
    
    def __init__(self, flow_id: str, name: str = "测试报告生成", 
                description: Optional[str] = "基于测试结果生成综合分析报告",
                planning_agent: Optional[str] = "ReportAnalysis",
                agent_factory=None):
        super().__init__(flow_id, name, description, planning_agent, agent_factory)
    
    async def initialize(self, test_results: Dict[str, Any], context: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """初始化报告生成流"""
        try:
            # 设置上下文
            self.context = context or {}
            self.context["test_results"] = test_results
            
            # 构建报告生成任务描述
            task = f"""
            基于以下自动化测试结果生成综合分析报告:
            
            {json.dumps(test_results, indent=2, ensure_ascii=False)}
            
            需要完成的任务:
            1. 分析测试结果
            2. 识别并分类问题
            3. 生成风险评估矩阵
            4. 提出修复建议
            5. 生成综合分析报告
            """
            
            self.context["task"] = task
            
            # 调用基类初始化方法
            return await super().initialize(task, self.context, **kwargs)
        except Exception as e:
            self.error = f"初始化报告生成流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            return False
```

## 5. 执行流工厂

为了方便创建各种类型的执行流，我们设计一个执行流工厂：

```python
class FlowFactory:
    """执行流工厂"""
    
    def __init__(self, agent_factory=None):
        self.agent_factory = agent_factory
    
    def create_flow(self, flow_type: str, flow_id: str, name: str = None, description: str = None, **kwargs):
        """创建执行流"""
        if flow_type == "planning":
            return PlanningFlow(flow_id, name or "规划执行", description, agent_factory=self.agent_factory)
        elif flow_type == "tara":
            return TaraAnalysisFlow(flow_id, name or "TARA分析", description, agent_factory=self.agent_factory)
        elif flow_type == "testcase":
            return TestCaseGenerationFlow(flow_id, name or "测试用例生成", description, agent_factory=self.agent_factory)
        elif flow_type == "automation":
            return AutomationTestFlow(flow_id, name or "自动化测试执行", description, agent_factory=self.agent_factory)
        elif flow_type == "report":
            return ReportGenerationFlow(flow_id, name or "报告生成", description, agent_factory=self.agent_factory)
        else:
            raise ValueError(f"Unsupported flow type: {flow_type}")
```

## 6. 执行流管理器

为了管理多个执行流的生命周期和状态，我们设计一个执行流管理器：

```python
class FlowManager:
    """执行流管理器"""
    
    def __init__(self, agent_factory=None):
        self.flows: Dict[str, BaseFlow] = {}
        self.flow_factory = FlowFactory(agent_factory)
    
    async def create_flow(self, flow_type: str, flow_id: str = None, name: str = None, 
                        description: str = None, **kwargs) -> str:
        """创建新的执行流"""
        flow_id = flow_id or str(uuid.uuid4())
        
        # 检查ID是否已存在
        if flow_id in self.flows:
            raise ValueError(f"Flow with ID {flow_id} already exists")
        
        # 创建执行流
        flow = self.flow_factory.create_flow(flow_type, flow_id, name, description)
        
        # 初始化执行流
        await flow.initialize(**kwargs)
        
        # 保存执行流
        self.flows[flow_id] = flow
        
        return flow_id
    
    async def execute_flow(self, flow_id: str) -> Dict[str, Any]:
        """执行指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        flow = self.flows[flow_id]
        success = await flow.execute()
        
        return {
            "success": success,
            "status": flow.status,
            "error": flow.error
        }
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """获取指定执行流的状态"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        return self.flows[flow_id].get_status()
    
    def get_flow_result(self, flow_id: str) -> Dict[str, Any]:
        """获取指定执行流的结果"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        flow = self.flows[flow_id]
        if flow.status != FlowStatus.COMPLETED:
            raise ValueError(f"Flow {flow_id} is not completed yet, current status: {flow.status}")
        
        return flow.get_result()
    
    async def pause_flow(self, flow_id: str) -> bool:
        """暂停指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        return await self.flows[flow_id].pause()
    
    async def resume_flow(self, flow_id: str) -> Dict[str, Any]:
        """恢复指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        success = await self.flows[flow_id].resume()
        
        flow = self.flows[flow_id]
        return {
            "success": success,
            "status": flow.status,
            "error": flow.error
        }
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """列出所有执行流及其状态"""
        return [
            {
                "id": flow_id,
                "name": flow.name,
                "description": flow.description,
                "status": flow.status,
                "type": flow.__class__.__name__
            }
            for flow_id, flow in self.flows.items()
        ]
```

## 7. 智能体框架选择

为了实现KunlunSec AI Platform的执行流系统，我们需要选择一个合适的智能体框架。在当前流行的框架中，LangChain和LangGraph是两个主要选择，下面我们将对比这两个框架，并提出我们的选择建议。

### 7.1 框架对比分析

#### 7.1.1 LangChain

**优势：**
- 成熟的生态系统，拥有大量预定义组件
- 广泛的集成能力，支持多种LLM、工具和服务
- 较低的学习曲线和丰富的文档资源
- 强大的链式处理和组合能力
- 完善的记忆管理机制

**局限性：**
- 对复杂多智能体协作支持有限
- 执行流程可视化能力较弱
- 状态管理相对简单，不适合复杂状态转换
- 调试和监控复杂流程较为困难

#### 7.1.2 LangGraph

**优势：**
- 专为复杂智能体工作流设计，基于有向图模型
- 优秀的状态管理机制，支持复杂状态转换和分支
- 内置执行流程可视化能力
- 对多智能体协作有更好的支持
- 基于LangChain构建，可复用其组件生态
- 更适合需要条件分支和循环的复杂工作流

**局限性：**
- 相对较新，社区和文档不如LangChain完善
- 学习曲线较陡峭
- API可能还在演进中

### 7.2 项目需求分析

KunlunSec AI Platform有以下关键需求：

1. **复杂的工作流程**: 车联网安全测试包含多阶段、多条件分支的复杂流程
2. **多智能体协作**: 需要专业化智能体之间的有效协作
3. **状态管理**: 需要严谨的状态跟踪和流程控制
4. **可视化能力**: 需要清晰可视化执行流程，便于监控和调试
5. **灵活扩展**: 需要支持新的智能体和工具的便捷集成

### 7.3 框架选择建议

基于项目需求和框架对比，我们建议采用**LangGraph作为主要框架**，同时利用LangChain的组件生态。具体原因如下：

1. **更适合复杂流程**: LangGraph的有向图模型天然适合表达我们的TARA分析、测试生成和执行等复杂流程
2. **优秀的状态管理**: 车联网安全测试需要严格的状态管理，LangGraph在这方面优势明显
3. **流程可视化**: LangGraph内置的可视化能力可以帮助我们监控和调试复杂流程
4. **多智能体协作**: 我们设计的专业化智能体协作模式与LangGraph的设计理念契合
5. **可复用性**: LangGraph基于LangChain构建，可以利用LangChain的组件和集成能力

### 7.4 实施建议

我们建议按照以下方式集成LangGraph到我们的系统中：

```python
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

class PlanningFlowGraph:
    """基于LangGraph实现的规划执行流图"""
    
    def __init__(self, agent_factory, flow_id: str, name: str, description: Optional[str] = None):
        self.agent_factory = agent_factory
        self.flow_id = flow_id
        self.name = name
        self.description = description
        self.graph = self._build_graph()
        # 使用内存保存检查点，可以根据需要替换为持久化存储
        self.checkpoint_saver = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpoint_saver)
    
    def _build_graph(self) -> StateGraph:
        """构建执行流图"""
        # 定义状态类型
        from typing import TypedDict, List, Dict, Any
        
        class PlanningState(TypedDict):
            task: str
            plan: Optional[Dict[str, Any]]
            current_step_id: Optional[str]
            steps: Dict[str, Dict[str, Any]]
            results: Dict[str, Any]
            status: str
            error: Optional[str]
        
        # 创建状态图
        graph = StateGraph(PlanningState)
        
        # 添加节点
        graph.add_node("planning", self._planning_step)
        graph.add_node("execute_step", self._execute_step)
        graph.add_node("check_completion", self._check_completion)
        
        # 添加边和条件
        graph.add_edge("planning", "execute_step")
        graph.add_conditional_edges(
            "execute_step",
            self._next_step_condition,
            {
                "next_step": "execute_step",
                "completed": "check_completion",
                "error": END
            }
        )
        graph.add_conditional_edges(
            "check_completion",
            self._check_completion_condition,
            {
                "completed": END,
                "incomplete": "execute_step"
            }
        )
        
        # 设置入口节点
        graph.set_entry_point("planning")
        
        return graph
    
    async def _planning_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """规划步骤，创建执行计划"""
        # 使用规划智能体创建计划
        agent = await self.agent_factory.get_agent("planning")
        
        try:
            # 准备规划提示
            task = state["task"]
            planning_prompt = self._create_planning_prompt(task)
            
            # 执行规划
            response = await agent.run(planning_prompt)
            
            # 解析计划
            plan = self._parse_planning_response(response)
            
            # 更新状态
            return {
                **state,
                "plan": plan,
                "steps": {step["id"]: {**step, "status": "pending"} for step in plan["steps"]},
                "current_step_id": self._get_first_executable_step(plan["steps"]),
                "status": "planning_completed"
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error": f"规划失败: {str(e)}"
            }
    
    async def _execute_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        # 获取当前步骤信息
        current_step_id = state["current_step_id"]
        if not current_step_id:
            return {**state, "status": "error", "error": "没有可执行的步骤"}
            
        step = state["steps"][current_step_id]
        
        # 获取执行智能体
        agent = await self.agent_factory.get_agent(step["executor"])
        
        try:
            # 准备执行提示
            execution_context = self._prepare_execution_context(state, step)
            step_prompt = self._format_step_prompt(step, execution_context)
            
            # 执行步骤
            result = await agent.run(step_prompt)
            
            # 更新步骤状态
            updated_steps = {**state["steps"]}
            updated_steps[current_step_id] = {
                **step,
                "status": "completed",
                "result": result
            }
            
            # 更新结果集合
            updated_results = {**state["results"], current_step_id: result}
            
            return {
                **state,
                "steps": updated_steps,
                "results": updated_results,
                "current_step_id": None,  # 将在next_step_condition中设置
                "status": "step_completed"
            }
        except Exception as e:
            # 更新步骤状态为失败
            updated_steps = {**state["steps"]}
            updated_steps[current_step_id] = {
                **step,
                "status": "failed",
                "error": str(e)
            }
            
            return {
                **state,
                "steps": updated_steps,
                "status": "step_failed",
                "error": f"执行步骤 {current_step_id} 失败: {str(e)}"
            }
    
    def _next_step_condition(self, state: Dict[str, Any]) -> str:
        """确定下一步操作"""
        # 如果有错误，结束执行
        if state.get("status") == "error" or state.get("status") == "step_failed":
            return "error"
        
        # 获取下一个可执行的步骤
        next_step_id = self._get_next_executable_step(state["steps"])
        
        if next_step_id:
            # 更新当前步骤ID
            state["current_step_id"] = next_step_id
            return "next_step"
        else:
            # 没有更多步骤，检查完成状态
            return "completed"
    
    async def _check_completion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """检查所有步骤是否完成"""
        # 检查是否所有步骤都已完成
        all_completed = all(
            step["status"] == "completed"
            for step in state["steps"].values()
        )
        
        if all_completed:
            return {
                **state,
                "status": "completed"
            }
        else:
            # 查找未完成的步骤
            incomplete_steps = [
                step_id for step_id, step in state["steps"].items()
                if step["status"] != "completed"
            ]
            
            return {
                **state,
                "status": "incomplete",
                "error": f"有未完成的步骤: {', '.join(incomplete_steps)}"
            }
    
    def _check_completion_condition(self, state: Dict[str, Any]) -> str:
        """检查是否所有任务都已完成"""
        if state["status"] == "completed":
            return "completed"
        else:
            return "incomplete"
    
    def _get_first_executable_step(self, steps: List[Dict[str, Any]]) -> Optional[str]:
        """获取第一个可执行的步骤ID"""
        for step in steps:
            if not step.get("dependencies"):
                return step["id"]
        return None
    
    def _get_next_executable_step(self, steps: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """获取下一个可执行的步骤ID"""
        for step_id, step in steps.items():
            # 跳过已完成或失败的步骤
            if step["status"] != "pending":
                continue
                
            # 检查依赖是否满足
            dependencies_met = True
            for dep_id in step.get("dependencies", []):
                if dep_id not in steps or steps[dep_id]["status"] != "completed":
                    dependencies_met = False
                    break
                    
            if dependencies_met:
                return step_id
                
        return None
    
    # 其他辅助方法...
    
    async def execute(self, task: str) -> Dict[str, Any]:
        """执行整个流程"""
        # 准备初始状态
        initial_state = {
            "task": task,
            "plan": None,
            "current_step_id": None,
            "steps": {},
            "results": {},
            "status": "initialized",
            "error": None
        }
        
        # 执行图
        try:
            result = await self.compiled_graph.invoke(initial_state)
            return result
        except Exception as e:
            return {
                **initial_state,
                "status": "error",
                "error": f"执行流程失败: {str(e)}"
            }
    
    def get_visualization(self) -> str:
        """获取执行流程的可视化表示"""
        return self.graph.get_graph().draw_mermaid()
```

通过这种实现方式，我们可以充分利用LangGraph的有向图模型、状态管理和可视化能力，同时也可以集成现有的智能体架构。

实施过程中，我们应当关注：

1. **逐步集成**: 从核心流程开始，逐步将系统迁移到LangGraph架构
2. **兼容层设计**: 为现有智能体设计兼容层，便于集成到LangGraph中
3. **状态持久化**: 根据需要配置适当的检查点保存机制，确保长时间运行的流程可恢复
4. **监控与可视化**: 充分利用LangGraph的可视化能力，构建有效的监控机制
``` 