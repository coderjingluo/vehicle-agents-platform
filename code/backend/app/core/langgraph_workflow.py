"""
基于LangGraph的智能体工作流系统
实现多智能体协作和复杂任务执行工作流
"""

from typing import Any, Dict, List, Optional, Callable, TypedDict, Annotated
from enum import Enum
import asyncio
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from .llm_client import LLMClientManager
from .tool_registry import ToolRegistry


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentType(Enum):
    """智能体类型"""
    TARA = "tara"
    TEST_CASE = "test_case"
    AUTOMATION = "automation"
    REPORT = "report"
    KNOWLEDGE = "knowledge"


class WorkflowState(TypedDict):
    """工作流状态定义"""
    # 基础信息
    workflow_id: str
    user_request: str
    current_agent: str
    status: str
    
    # 消息历史
    messages: List[BaseMessage]
    
    # 智能体执行结果
    tara_result: Optional[Dict[str, Any]]
    test_case_result: Optional[Dict[str, Any]]
    automation_result: Optional[Dict[str, Any]]
    report_result: Optional[Dict[str, Any]]
    knowledge_result: Optional[Dict[str, Any]]
    
    # 工作流控制
    next_agent: Optional[str]
    iteration_count: int
    max_iterations: int
    
    # 错误处理
    errors: List[str]
    retry_count: int
    max_retries: int
    
    # 上下文数据
    context: Dict[str, Any]


class LangGraphWorkflowManager:
    """基于LangGraph的工作流管理器"""
    
    def __init__(
        self,
        llm_manager: LLMClientManager,
        tool_registry: ToolRegistry
    ):
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        
        # LangGraph组件
        self.checkpointer = MemorySaver()
        self.workflow_graph = None
        
        # 智能体回调映射
        self.agent_callbacks = {}
        
        # 初始化工作流图
        self._build_workflow_graph()
    
    def _build_workflow_graph(self):
        """构建工作流图"""
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点（智能体）
        workflow.add_node("router", self._router_node)
        workflow.add_node("tara_agent", self._tara_agent_node)
        workflow.add_node("test_case_agent", self._test_case_agent_node)
        workflow.add_node("automation_agent", self._automation_agent_node)
        workflow.add_node("report_agent", self._report_agent_node)
        workflow.add_node("knowledge_agent", self._knowledge_agent_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # 设置入口点
        workflow.set_entry_point("router")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "tara": "tara_agent",
                "test_case": "test_case_agent", 
                "automation": "automation_agent",
                "report": "report_agent",
                "knowledge": "knowledge_agent",
                "error": "error_handler",
                "end": END
            }
        )
        
        # 添加返回路由的边
        for agent in ["tara_agent", "test_case_agent", "automation_agent", "report_agent", "knowledge_agent"]:
            workflow.add_edge(agent, "router")
        
        # 错误处理边
        workflow.add_conditional_edges(
            "error_handler",
            self._handle_error_routing,
            {
                "retry": "router",
                "end": END
            }
        )
        
        # 编译图
        self.workflow_graph = workflow.compile(checkpointer=self.checkpointer)
    
    def _route_to_agent(self, state: WorkflowState) -> str:
        """路由决策函数"""
        # 检查是否超过最大迭代次数
        if state["iteration_count"] >= state["max_iterations"]:
            return "end"
        
        # 检查是否有错误需要处理
        if state["errors"] and state["retry_count"] < state["max_retries"]:
            return "error"
        
        # 如果有指定的下一个智能体
        if state.get("next_agent"):
            next_agent = state["next_agent"]
            state["next_agent"] = None  # 清除指定
            return next_agent
        
        # 根据当前状态决定下一个智能体
        if not state.get("tara_result"):
            return "tara"
        elif not state.get("test_case_result"):
            return "test_case"
        elif not state.get("automation_result"):
            return "automation"
        elif not state.get("report_result"):
            return "report"
        elif not state.get("knowledge_result"):
            return "knowledge"
        else:
            return "end"
    
    def _handle_error_routing(self, state: WorkflowState) -> str:
        """错误处理路由"""
        if state["retry_count"] < state["max_retries"]:
            return "retry"
        else:
            return "end"
    
    async def _router_node(self, state: WorkflowState) -> Dict[str, Any]:
        """路由节点 - 协调整个工作流"""
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        # 更新当前状态
        state["status"] = WorkflowStatus.RUNNING.value
        
        # 添加路由消息
        router_message = SystemMessage(
            content=f"工作流迭代 {state['iteration_count']}: 准备执行下一个智能体"
        )
        state["messages"].append(router_message)
        
        return state
    
    async def _tara_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """TARA智能体节点"""
        state["current_agent"] = "tara_agent"
        
        try:
            # 调用注册的TARA智能体回调
            if "tara" in self.agent_callbacks:
                result = await self.agent_callbacks["tara"](state)
                state["tara_result"] = result
                
                # 添加成功消息
                success_message = AIMessage(
                    content=f"TARA分析完成: {result.get('summary', '分析成功')}"
                )
                state["messages"].append(success_message)
            else:
                # 默认TARA处理
                result = await self._default_tara_processing(state)
                state["tara_result"] = result
                
        except Exception as e:
            state["errors"].append(f"TARA智能体执行失败: {str(e)}")
            
        return state
    
    async def _test_case_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """测试用例智能体节点"""
        state["current_agent"] = "test_case_agent"
        
        try:
            if "test_case" in self.agent_callbacks:
                result = await self.agent_callbacks["test_case"](state)
                state["test_case_result"] = result
                
                success_message = AIMessage(
                    content=f"测试用例生成完成: {result.get('test_count', 0)}个测试用例"
                )
                state["messages"].append(success_message)
            else:
                result = await self._default_test_case_processing(state)
                state["test_case_result"] = result
                
        except Exception as e:
            state["errors"].append(f"测试用例智能体执行失败: {str(e)}")
            
        return state
    
    async def _automation_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """自动化测试智能体节点"""
        state["current_agent"] = "automation_agent"
        
        try:
            if "automation" in self.agent_callbacks:
                result = await self.agent_callbacks["automation"](state)
                state["automation_result"] = result
                
                success_message = AIMessage(
                    content=f"自动化测试完成: {result.get('execution_summary', '执行成功')}"
                )
                state["messages"].append(success_message)
            else:
                result = await self._default_automation_processing(state)
                state["automation_result"] = result
                
        except Exception as e:
            state["errors"].append(f"自动化测试智能体执行失败: {str(e)}")
            
        return state
    
    async def _report_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """报告分析智能体节点"""
        state["current_agent"] = "report_agent"
        
        try:
            if "report" in self.agent_callbacks:
                result = await self.agent_callbacks["report"](state)
                state["report_result"] = result
                
                success_message = AIMessage(
                    content=f"报告生成完成: {result.get('report_type', '综合报告')}"
                )
                state["messages"].append(success_message)
            else:
                result = await self._default_report_processing(state)
                state["report_result"] = result
                
        except Exception as e:
            state["errors"].append(f"报告智能体执行失败: {str(e)}")
            
        return state
    
    async def _knowledge_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """知识库智能体节点"""
        state["current_agent"] = "knowledge_agent"
        
        try:
            if "knowledge" in self.agent_callbacks:
                result = await self.agent_callbacks["knowledge"](state)
                state["knowledge_result"] = result
                
                success_message = AIMessage(
                    content=f"知识库更新完成: {result.get('learned_items', 0)}个新知识点"
                )
                state["messages"].append(success_message)
            else:
                result = await self._default_knowledge_processing(state)
                state["knowledge_result"] = result
                
        except Exception as e:
            state["errors"].append(f"知识库智能体执行失败: {str(e)}")
            
        return state
    
    async def _error_handler_node(self, state: WorkflowState) -> Dict[str, Any]:
        """错误处理节点"""
        state["current_agent"] = "error_handler"
        state["retry_count"] = state.get("retry_count", 0) + 1
        
        # 记录错误处理消息
        error_message = SystemMessage(
            content=f"错误处理 (第{state['retry_count']}次重试): {'; '.join(state['errors'])}"
        )
        state["messages"].append(error_message)
        
        # 清除错误（为重试做准备）
        if state["retry_count"] < state["max_retries"]:
            state["errors"] = []
        
        return state
    
    def register_agent_callback(self, agent_type: str, callback: Callable):
        """注册智能体回调函数"""
        self.agent_callbacks[agent_type] = callback
    
    async def execute_workflow(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """执行工作流"""
        
        # 初始化状态
        workflow_id = str(uuid.uuid4())
        initial_state = WorkflowState(
            workflow_id=workflow_id,
            user_request=user_request,
            current_agent="",
            status=WorkflowStatus.PENDING.value,
            messages=[HumanMessage(content=user_request)],
            tara_result=None,
            test_case_result=None,
            automation_result=None,
            report_result=None,
            knowledge_result=None,
            next_agent=None,
            iteration_count=0,
            max_iterations=max_iterations,
            errors=[],
            retry_count=0,
            max_retries=max_retries,
            context=context or {}
        )
        
        # 配置运行
        config = RunnableConfig(
            configurable={"thread_id": workflow_id}
        )
        
        try:
            # 执行工作流
            final_state = await self.workflow_graph.ainvoke(initial_state, config)
            
            # 标记完成
            final_state["status"] = WorkflowStatus.COMPLETED.value
            
            return {
                "workflow_id": workflow_id,
                "status": final_state["status"],
                "results": {
                    "tara": final_state.get("tara_result"),
                    "test_case": final_state.get("test_case_result"),
                    "automation": final_state.get("automation_result"),
                    "report": final_state.get("report_result"),
                    "knowledge": final_state.get("knowledge_result")
                },
                "messages": [msg.content for msg in final_state["messages"]],
                "iterations": final_state["iteration_count"],
                "errors": final_state["errors"]
            }
            
        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "status": WorkflowStatus.FAILED.value,
                "error": str(e),
                "results": {},
                "messages": [],
                "iterations": 0,
                "errors": [str(e)]
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        config = RunnableConfig(
            configurable={"thread_id": workflow_id}
        )
        
        try:
            # 获取当前状态
            state = await self.workflow_graph.aget_state(config)
            
            return {
                "workflow_id": workflow_id,
                "current_agent": state.values.get("current_agent", ""),
                "status": state.values.get("status", "unknown"),
                "iteration_count": state.values.get("iteration_count", 0),
                "errors": state.values.get("errors", []),
                "next_tasks": list(state.next)
            }
            
        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "status": "error"
            }
    
    # 默认处理方法（当没有注册具体智能体时使用）
    async def _default_tara_processing(self, state: WorkflowState) -> Dict[str, Any]:
        """默认TARA处理"""
        return {
            "summary": "默认TARA分析完成",
            "threats": ["威胁1", "威胁2"],
            "risks": ["风险1", "风险2"],
            "recommendations": ["建议1", "建议2"]
        }
    
    async def _default_test_case_processing(self, state: WorkflowState) -> Dict[str, Any]:
        """默认测试用例处理"""
        return {
            "test_count": 5,
            "test_cases": ["测试用例1", "测试用例2", "测试用例3"],
            "coverage": "85%"
        }
    
    async def _default_automation_processing(self, state: WorkflowState) -> Dict[str, Any]:
        """默认自动化测试处理"""
        return {
            "execution_summary": "自动化测试执行完成",
            "passed": 8,
            "failed": 2,
            "total": 10
        }
    
    async def _default_report_processing(self, state: WorkflowState) -> Dict[str, Any]:
        """默认报告处理"""
        return {
            "report_type": "综合测试报告",
            "overall_score": 85,
            "recommendations": ["修复建议1", "修复建议2"]
        }
    
    async def _default_knowledge_processing(self, state: WorkflowState) -> Dict[str, Any]:
        """默认知识库处理"""
        return {
            "learned_items": 3,
            "updated_knowledge": ["知识点1", "知识点2", "知识点3"]
        } 