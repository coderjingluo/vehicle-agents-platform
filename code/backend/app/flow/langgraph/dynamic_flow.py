"""
KunlunSec AI Platform - LangGraph 动态流程

使用LangGraph实现的动态规划和执行流程，支持智能步骤分解和智能体协作。
"""

import uuid
import json
import re
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Union, Set
from enum import Enum
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import Runnable, RunnableLambda

from app.core.logging import logger
from app.agent.base import BaseAgent
from app.agent.adapter import LangGraphAgentAdapter
from app.agent.interface import AgentFactory


# 动态流程阶段
class DynamicFlowStage(str, Enum):
    INIT = "init"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    COMPLETE = "complete"
    ERROR = "error"


# 动态流程状态
class DynamicFlowState(TypedDict):
    """动态流程状态"""
    task: str                                # 任务描述
    plan: Dict[str, Any]                     # 动态生成的计划
    steps: Dict[str, Dict[str, Any]]         # 步骤信息
    current_step_id: Optional[str]           # 当前执行的步骤ID
    step_results: Dict[str, Any]             # 步骤执行结果
    agent_states: Dict[str, Dict[str, Any]]  # 各智能体状态
    tool_usages: Dict[str, List[Dict[str, Any]]]  # 工具使用记录
    current_stage: DynamicFlowStage          # 当前阶段
    status: str                              # 当前状态
    history: List[Dict[str, Any]]            # 执行历史
    error: Optional[str]                     # 错误信息(如果有)


class DynamicLangGraphFlow:
    """基于LangGraph实现的动态流程，支持智能步骤分解和智能体协作"""
    
    def __init__(self, agent_factory: AgentFactory, config: Dict[str, Any] = None):
        """
        初始化动态流程
        
        Args:
            agent_factory: 智能体工厂，用于获取不同类型的智能体
            config: 配置参数
        """
        self.config = config or {}
        self.agent_factory = agent_factory
        self.planning_agent_name = self.config.get("planning_agent", "toolcall")
        self.planning_agent = None
        self.agent_adapters = {}  # 智能体适配器缓存
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver()
        self.execution_id = None
        
    async def setup(self):
        """设置流程和初始智能体"""
        # 初始化规划智能体
        self.planning_agent = await self.agent_factory.get_agent(self.planning_agent_name)
        
        # 创建规划智能体适配器
        self.agent_adapters[self.planning_agent_name] = LangGraphAgentAdapter(self.planning_agent)
        
        # 构建动态工作流图
        self._build_graph()
        
        return self
        
    def _build_graph(self):
        """构建动态工作流图"""
        # 创建状态图
        self.graph = StateGraph(DynamicFlowState)
        
        # 添加节点
        self.graph.add_node(DynamicFlowStage.PLANNING, self._planning_step)
        self.graph.add_node(DynamicFlowStage.EXECUTING, self._executing_step)
        self.graph.add_node(DynamicFlowStage.EVALUATING, self._evaluating_step)
        
        # 添加边：定义流程
        self.graph.add_edge(DynamicFlowStage.PLANNING, DynamicFlowStage.EXECUTING)
        
        # 添加条件边：从执行到评估或完成
        self.graph.add_conditional_edges(
            DynamicFlowStage.EXECUTING,
            self._check_execution_condition,
            {
                "next_step": DynamicFlowStage.EXECUTING,  # 继续执行下一步骤
                "evaluate": DynamicFlowStage.EVALUATING,  # 评估当前执行结果
                "complete": DynamicFlowStage.COMPLETE,    # 所有步骤完成
                "error": DynamicFlowStage.ERROR           # 执行出错
            }
        )
        
        # 添加条件边：从评估到执行或完成
        self.graph.add_conditional_edges(
            DynamicFlowStage.EVALUATING,
            self._check_evaluation_condition,
            {
                "continue": DynamicFlowStage.EXECUTING,  # 继续执行
                "replan": DynamicFlowStage.PLANNING,     # 需要重新规划
                "complete": DynamicFlowStage.COMPLETE,   # 评估通过，完成流程
                "error": DynamicFlowStage.ERROR          # 评估失败
            }
        )
        
        # 设置入口节点
        self.graph.set_entry_point(DynamicFlowStage.PLANNING)
        
        # 添加结束节点
        self.graph.add_node(DynamicFlowStage.COMPLETE, self._complete_step)
        self.graph.add_edge(DynamicFlowStage.COMPLETE, END)
        
        # 添加错误节点
        self.graph.add_node(DynamicFlowStage.ERROR, self._error_step)
        self.graph.add_edge(DynamicFlowStage.ERROR, END)
        
        # 编译图
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    async def _planning_step(self, state: DynamicFlowState) -> DynamicFlowState:
        """规划步骤，动态生成执行计划"""
        logger.info("执行规划阶段")
        try:
            task = state["task"]
            
            # 准备提示
            planning_prompt = f"""
            你是KunlunSec AI平台的规划智能体，负责为复杂任务制定详细的执行计划。
            
            # 任务
            {task}
            
            # 你的职责
            1. 分析任务的本质和需求
            2. 将任务分解为逻辑步骤
            3. 为每个步骤选择最合适的专业智能体和工具
            4. 确定步骤之间的依赖关系
            5. 确保计划是动态生成的，而不是固定的步骤列表
            
            # 可用的智能体类型
            - toolcall: 通用工具调用智能体，适用于大多数基本操作
            - tara: 威胁分析和风险评估智能体，擅长安全分析
            - testcase: 测试用例生成智能体，擅长设计测试场景
            - automation: 自动化测试智能体，擅长执行测试
            - report: 报告分析和生成智能体，擅长总结和报告
            - react: ReAct模式智能体，适合推理和行动交替的任务
            - mcp: 多智能体协作控制智能体，适合协调多个智能体
            - browser: 浏览器操作智能体，适合网页浏览和交互
            - data: 数据分析智能体，适合处理和分析数据
            - collaboration: 协作智能体，适合需要多方协作的任务
            
            # 可用的工具
            - bash: 执行Shell命令
            - file_operator: 文件操作（读取、写入、删除等）
            - rag_query: 知识库查询
            - web_search: 网络搜索
            - browser_use: 浏览器操作
            - python_execute: 执行Python代码
            - str_replace_editor: 文本替换编辑器
            - create_chat_completion: 创建聊天完成
            - ask_human: 请求人类帮助
            - tara_analysis: 执行威胁分析
            - test_case_generator: 生成测试用例
            - test_executor: 执行测试
            - report_generator: 生成报告
            - chart_visualization: 数据可视化
            
            # 规划策略
            1. 针对不同类型的任务，采用不同的分解策略
            2. 对于车联网安全任务，可能需要TARA分析、测试用例生成、测试用例执行、报告生成等子任务
            3. 考虑子任务之间的依赖关系和执行顺序
            4. 对于每个子任务，智能体还应该能够进一步分解出更细粒度的步骤
            5. 确保步骤之间的衔接和数据传递合理
            6. 任务分解必须是动态的，根据任务特点自适应生成，而不是固定的模板
            
            # 输出要求
            请提供一个JSON格式的执行计划，包含以下内容：
            
            ```json
            {
                "main_task": "主任务简述",
                "steps": [
                    {
                        "id": "步骤ID",
                        "name": "步骤名称",
                        "description": "详细描述该步骤的目标和需要完成的工作",
                        "executor": "最适合执行该步骤的智能体类型",
                        "tools": ["该步骤可能需要使用的工具列表"],
                        "subtasks": [
                            {
                                "id": "子任务ID",
                                "name": "子任务名称",
                                "description": "详细描述子任务",
                                "tools": ["可能需要使用的工具"],
                                "actions": [
                                    "具体的操作步骤1",
                                    "具体的操作步骤2",
                                    "..."
                                ]
                            }
                        ],
                        "dependencies": ["该步骤依赖的其他步骤ID列表"]
                    }
                ]
            }
            ```
            
            请分析当前任务，提供适合的动态计划方案。不要套用固定模板，应根据具体任务特点进行灵活规划。
            """
            
            # 获取规划智能体
            if not self.planning_agent:
                self.planning_agent = await self.agent_factory.get_agent(self.planning_agent_name)
            
            # 执行规划
            planning_response = await self.planning_agent.run(planning_prompt)
            
            # 解析规划结果
            plan = self._parse_planning_response(planning_response)
            
            # 记录规划结果
            logger.info(f"生成执行计划，包含 {len(plan.get('steps', []))} 个主要步骤")
            
            # 初始化步骤状态
            steps = {}
            for step in plan.get("steps", []):
                step_id = step.get("id")
                steps[step_id] = {
                    "id": step_id,
                    "name": step.get("name", ""),
                    "description": step.get("description", ""),
                    "executor": step.get("executor", "toolcall"),
                    "tools": step.get("tools", []),
                    "subtasks": step.get("subtasks", []),
                    "dependencies": step.get("dependencies", []),
                    "status": "pending"  # 初始状态：待执行
            }
            
            # 更新状态
            new_state = {
                **state,
                "plan": plan,
                "steps": steps,
                "current_step_id": self._get_next_executable_step(steps, {}),
                "current_stage": DynamicFlowStage.EXECUTING,
                "status": "plan_generated"
            }
            
            # 记录历史
            if "history" not in new_state:
                new_state["history"] = []
            
            history_entry = {
                "timestamp": str(datetime.now()),
                "stage": DynamicFlowStage.PLANNING,
                "action": "生成执行计划",
                "result": f"创建了包含 {len(plan.get('steps', []))} 个步骤的执行计划"
            }
            
            new_state["history"].append(history_entry)
            
            # 验证状态
            if not new_state.get("current_step_id"):
                raise ValueError("无法确定下一个可执行步骤")
                
            return new_state
            
        except Exception as e:
            error_msg = f"规划阶段出错: {str(e)}"
            logger.error(error_msg)
            
            return {
                **state,
                "current_stage": DynamicFlowStage.ERROR,
                "status": "planning_failed",
                "error": error_msg
            }
    
    async def _executing_step(self, state: DynamicFlowState) -> DynamicFlowState:
        """执行步骤，调用相应的智能体执行当前步骤"""
        logger.info("执行执行阶段")
        
        try:
            # 获取当前步骤ID
            current_step_id = state["current_step_id"]
            if not current_step_id:
                raise ValueError("当前没有可执行的步骤")
                
            # 获取当前步骤信息
            steps = state["steps"]
            current_step = steps.get(current_step_id)
            if not current_step:
                raise ValueError(f"找不到步骤: {current_step_id}")
            
            # 获取执行者类型
            executor_type = current_step["executor"]
            
            # 准备执行环境和上下文
            execution_context = self._prepare_execution_context(state, current_step)
            
            # 获取相应的智能体
            agent = await self._get_agent(executor_type)
            if not agent:
                raise ValueError(f"无法创建智能体: {executor_type}")
            
            # 准备工具使用记录
            if "tool_usages" not in state:
                state["tool_usages"] = {}
            
            if executor_type not in state["tool_usages"]:
                state["tool_usages"][executor_type] = []
            
            # 记录步骤开始执行
            logger.info(f"开始执行步骤: {current_step.get('name')} (ID: {current_step_id}), 使用 {executor_type} 智能体")
            
            # 记录智能体状态
            if "agent_states" not in state:
                state["agent_states"] = {}
            
            if executor_type not in state["agent_states"]:
                state["agent_states"][executor_type] = {"status": "initializing"}
            
            # 更新步骤状态
            current_step["status"] = "executing"
            current_step["start_time"] = datetime.now().isoformat()
            
            # 获取任务类型，确保传递正确的类型给智能体
            task_type = state.get("task_type", "GENERAL")
            
            # 检查executor_type和task_type是否匹配，如果不匹配则更新task_type
            if executor_type.lower() == "tara" and task_type != "TARA":
                task_type = "TARA"
                logger.warning(f"任务类型不匹配，将任务类型从 {state.get('task_type')} 更新为 {task_type}")
            elif executor_type.lower() == "testcase" and task_type != "TEST_CASE":
                task_type = "TEST_CASE"
                logger.warning(f"任务类型不匹配，将任务类型从 {state.get('task_type')} 更新为 {task_type}")
            elif executor_type.lower() == "automation" and task_type != "AUTOMATION":
                task_type = "AUTOMATION"
                logger.warning(f"任务类型不匹配，将任务类型从 {state.get('task_type')} 更新为 {task_type}")
            elif executor_type.lower() == "report" and task_type != "REPORT":
                task_type = "REPORT"
                logger.warning(f"任务类型不匹配，将任务类型从 {state.get('task_type')} 更新为 {task_type}")
            
            # 更新状态中的任务类型
            state["task_type"] = task_type
            
            # 执行任务，确保使用正确的任务类型
            try:
                # 首先检查是否为ToolCallAgent的子类，如果是，则直接使用run方法
                # 这样可以确保所有步骤都使用相同的执行流程，而不是混用run和execute
                if hasattr(agent, "run"):
                    # 新版智能体接口，使用run方法
                    logger.info(f"使用 {executor_type} 智能体的run方法执行步骤")
                    result = await agent.run(execution_context)
                elif hasattr(agent, "execute"):
                    # 旧版智能体接口，使用execute方法
                    logger.info(f"使用 {executor_type} 智能体的execute方法执行步骤")
                    result = await agent.execute(execution_context)
                else:
                    raise ValueError(f"智能体 {executor_type} 没有可用的执行方法")
            except Exception as e:
                logger.error(f"执行步骤 {current_step_id} 失败: {str(e)}")
                raise
            
            # 更新步骤状态
            current_step["status"] = "completed"
            current_step["end_time"] = datetime.now().isoformat()
            
            # 保存步骤结果
            state["step_results"][current_step_id] = result
            
            # 如果有next_step指定，则设置为下一个步骤
            next_step_id = self._get_next_executable_step(steps, state["step_results"])
            state["current_step_id"] = next_step_id
            
            # 如果没有下一个步骤，则完成执行
            if not next_step_id:
                state["status"] = "completed"
            
            # 记录历史
            state["history"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "step_completed",
                "step_id": current_step_id,
                "step_name": current_step.get("name", ""),
                "executor": executor_type
            })
            
            return state
            
        except Exception as e:
            logger.error(f"执行步骤失败: {str(e)}")
            state["error"] = str(e)
            state["status"] = "error"
            state["current_stage"] = DynamicFlowStage.ERROR
            
            # 记录历史
            state["history"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "error",
                "error": str(e)
            })
            
            return state
    
    def _check_execution_condition(self, state: DynamicFlowState) -> Literal["next_step", "evaluate", "complete", "error"]:
        """检查执行条件，决定下一步操作"""
        # 检查是否有错误
        if state.get("error"):
            return "error"
        
        # 检查当前步骤ID
        current_step_id = state.get("current_step_id")
        
        # 如果没有下一步骤，表示所有步骤已完成
        if not current_step_id:
            return "complete"
        
        # 每执行N个步骤后进行评估(可配置)
        steps = state.get("steps", {})
        completed_steps = sum(1 for s in steps.values() if s.get("status") == "completed")
        evaluation_frequency = self.config.get("evaluation_frequency", 3)
        
        if completed_steps > 0 and completed_steps % evaluation_frequency == 0:
            return "evaluate"
        
        # 继续执行下一步骤
        return "next_step"
    
    async def _evaluating_step(self, state: DynamicFlowState) -> DynamicFlowState:
        """评估当前执行状态"""
        logger.info("执行评估阶段")
        try:
            task = state["task"]
            steps = state["steps"]
            step_results = state.get("step_results", {})
            
            # 使用规划智能体进行评估
            evaluation_prompt = f"""
            请评估以下任务的执行进展:
            
            原始任务:
            {task}
            
            已完成的步骤:
            {self._format_completed_steps(steps, step_results)}
            
            请评估:
            1. 当前执行进度是否符合预期
            2. 是否需要调整计划
            3. 是否有任何错误或问题需要解决
            4. 是否已经完成了任务目标
            
            返回评估结果，包括:
            1. 进度评估 (0-100%)
            2. 是否需要重新规划 (true/false)
            3. 是否已完成任务 (true/false)
            4. 评估意见
            """
            
            # 执行评估
            response = await self.planning_agent.run(evaluation_prompt)
            
            # 解析评估结果(简化实现)
            needs_replan = "需要重新规划" in response or "需要调整计划" in response
            is_complete = "已完成任务" in response or "任务已完成" in response
            
            # 记录历史
            history_entry = {
                "stage": DynamicFlowStage.EVALUATING,
                "input": evaluation_prompt,
                "output": response,
                "needs_replan": needs_replan,
                "is_complete": is_complete
            }
            
            # 更新状态
            return {
                **state,
                "evaluation": {
                    "result": response,
                    "needs_replan": needs_replan,
                    "is_complete": is_complete,
                    "timestamp": str(uuid.uuid4())  # 使用UUID作为时间戳
                },
                "current_stage": DynamicFlowStage.EVALUATING,  # 保持在评估阶段，由条件边决定下一步
                "status": "evaluated",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"评估失败: {str(e)}")
            return {
                **state,
                "error": f"评估失败: {str(e)}",
                "current_stage": DynamicFlowStage.ERROR,
                "status": "error"
            }
    
    def _check_evaluation_condition(self, state: DynamicFlowState) -> Literal["continue", "replan", "complete", "error"]:
        """检查评估结果，决定下一步操作"""
        # 检查是否有错误
        if state.get("error"):
            return "error"
        
        # 获取评估结果
        evaluation = state.get("evaluation", {})
        needs_replan = evaluation.get("needs_replan", False)
        is_complete = evaluation.get("is_complete", False)
        
        # 根据评估结果决定下一步
        if is_complete:
            return "complete"
        elif needs_replan:
            return "replan"
        else:
            return "continue"
    
    async def _complete_step(self, state: DynamicFlowState) -> DynamicFlowState:
        """完成流程，生成最终报告"""
        logger.info("执行完成阶段")
        try:
            task = state["task"]
            steps = state["steps"]
            step_results = state.get("step_results", {})
            
            # 使用规划智能体生成总结报告
            summary_prompt = f"""
            请为以下已完成的任务生成总结报告:
            
            原始任务:
            {task}
            
            执行步骤及结果:
            {self._format_completed_steps(steps, step_results)}
            
            请提供一份全面的总结报告，包括:
            1. 任务概述
            2. 执行过程
            3. 主要发现和结果
            4. 结论和建议
            """
            
            # 生成报告
            summary_report = await self.planning_agent.run(summary_prompt)
            
            # 记录历史
            history_entry = {
                "stage": DynamicFlowStage.COMPLETE,
                "input": summary_prompt,
                "output": summary_report
            }
            
            # 更新状态
            return {
                **state,
                "summary_report": summary_report,
                "current_stage": DynamicFlowStage.COMPLETE,
                "status": "completed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"生成总结报告失败: {str(e)}")
            return {
                **state,
                "error": f"生成总结报告失败: {str(e)}",
                "current_stage": DynamicFlowStage.ERROR,
                "status": "error"
            }
    
    async def _error_step(self, state: DynamicFlowState) -> DynamicFlowState:
        """处理错误状态"""
        logger.error(f"流程执行错误: {state.get('error')}")
        return {
            **state,
            "current_stage": DynamicFlowStage.ERROR,
            "status": "error"
        }
    
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
            # 如果无法解析，返回简单的默认计划
            return {
                "steps": [
                    {
                        "id": "step1",
                        "name": "执行任务",
                        "description": "执行用户请求的任务",
                        "executor": "toolcall",
                        "tools": [],
                        "dependencies": []
                    }
                ]
            }
    
    def _get_next_executable_step(self, steps: Dict[str, Dict[str, Any]], step_results: Dict[str, Any]) -> Optional[str]:
        """获取下一个可执行的步骤ID"""
        for step_id, step in steps.items():
            # 跳过已完成的步骤
            if step.get("status") == "completed":
                continue
                
            # 检查依赖是否满足
            dependencies_met = True
            for dep_id in step.get("dependencies", []):
                if dep_id not in step_results:
                    dependencies_met = False
                    break
                    
            if dependencies_met:
                return step_id
                
        return None
    
    def _prepare_execution_context(self, state: DynamicFlowState, current_step: Dict[str, Any]) -> str:
        """准备步骤执行的上下文信息"""
        context_parts = []
        
        # 添加任务描述
        task = state.get("task", "")
        if task:
            context_parts.append(f"任务: {task}")
        
        # 添加依赖步骤的输出
        step_results = state.get("step_results", {})
        for dep_id in current_step.get("dependencies", []):
            if dep_id in step_results:
                step = state["steps"][dep_id]
                context_parts.append(f"步骤 '{step['name']}' 的结果: {step_results[dep_id]}")
        
        return "\n\n".join(context_parts)
    
    def _format_completed_steps(self, steps: Dict[str, Dict[str, Any]], step_results: Dict[str, Any]) -> str:
        """格式化已完成步骤的信息"""
        completed_steps = []
        
        for step_id, step in steps.items():
            if step.get("status") == "completed" and step_id in step_results:
                completed_steps.append(f"""
步骤ID: {step_id}
名称: {step['name']}
描述: {step['description']}
执行者: {step['executor']}
结果: {step_results[step_id]}
""")
        
        return "\n".join(completed_steps)
    
    async def _get_agent(self, agent_type: str) -> BaseAgent:
        """获取指定类型的智能体"""
        agent = await self.agent_factory.get_agent(agent_type)
        
        # 缓存智能体适配器
        if agent_type not in self.agent_adapters:
            self.agent_adapters[agent_type] = LangGraphAgentAdapter(agent)
            
        return agent
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务描述
            
        Returns:
            执行结果
        """
        # 生成执行ID
        self.execution_id = str(uuid.uuid4())
        
        # 准备初始状态
        initial_state: DynamicFlowState = {
            "task": task,
            "plan": {},
            "steps": {},
            "current_step_id": None,
            "step_results": {},
            "agent_states": {},
            "tool_usages": {},
            "current_stage": DynamicFlowStage.PLANNING,
            "status": "initialized",
            "history": [],
            "error": None
        }
        
        # 执行流程
        try:
            logger.info(f"开始执行任务，执行ID: {self.execution_id}")
            result = await self.compiled_graph.ainvoke(initial_state, {"execution_id": self.execution_id})
            logger.info(f"任务执行完成，执行ID: {self.execution_id}")
            return result
        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}")
            return {
                **initial_state,
                "status": "error",
                "current_stage": DynamicFlowStage.ERROR,
                "error": f"任务执行失败: {str(e)}"
            }
    
    def get_graph_visualization(self) -> str:
        """获取图的可视化表示（Mermaid格式）"""
        if not self.graph:
            return "图尚未构建"
        return self.graph.get_mermaid(add_dependencies=True)
    
    def _format_dependencies_results(self, dependencies_results: Dict[str, Any]) -> str:
        """格式化依赖步骤的结果"""
        if not dependencies_results:
            return "无依赖步骤结果"
            
        formatted_results = []
        for step_id, result in dependencies_results.items():
            formatted_results.append(f"### 步骤 {step_id} 的结果:\n{result}")
            
        return "\n\n".join(formatted_results) 