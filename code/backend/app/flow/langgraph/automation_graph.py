"""
KunlunSec AI Platform - LangGraph 自动化测试流程

使用LangGraph实现的自动化测试执行流程。
"""

import uuid
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Union
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import Runnable, RunnableLambda

from app.core.logging import logger
from app.agent.automation import AutomationTestAgent
from app.agent.adapter import LangGraphAgentAdapter
# 自动化测试阶段
class AutomationStage(str, Enum):
    INIT = "init"
    PREPARE_ENVIRONMENT = "prepare_environment"
    GENERATE_TEST_SCRIPTS = "generate_test_scripts"
    EXECUTE_TESTS = "execute_tests"
    COLLECT_RESULTS = "collect_results"
    ANALYZE_FAILURES = "analyze_failures"
    RETRY_FAILED_TESTS = "retry_failed_tests"
    FINALIZE_RESULTS = "finalize_results"
    COMPLETE = "complete"
    ERROR = "error"


# 自动化测试状态
class AutomationState(TypedDict):
    """自动化测试状态"""
    test_cases: List[Dict[str, Any]]            # 测试用例
    environment: Dict[str, Any]                 # 测试环境配置
    test_scripts: Dict[str, str]                # 生成的测试脚本
    test_results: Dict[str, Dict[str, Any]]     # 测试结果
    failed_tests: List[str]                     # 失败的测试
    retry_count: Dict[str, int]                 # 重试计数
    final_report: Optional[Dict[str, Any]]      # 最终报告
    current_stage: AutomationStage              # 当前阶段
    status: str                                 # 当前状态
    history: List[Dict[str, Any]]               # 执行历史
    error: Optional[str]                        # 错误信息(如果有)

class AutomationTestGraph:
    """基于LangGraph实现的自动化测试智能体图"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化自动化测试图
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.automation_agent = None
        self.agent_adapter = None
        self.tools_map = {}
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver()
        self.execution_id = None
        self.max_retries = self.config.get("max_retries", 2)
        
    async def setup(self):
        """设置智能体和工具"""
        # 初始化自动化测试智能体
        self.automation_agent = await AutomationTestAgent.create()
        
        # 创建适配器
        self.agent_adapter = LangGraphAgentAdapter(self.automation_agent)
        
        # 配置工具
        self.tools_map = {
            "test_executor": self.agent_adapter.get_tool_as_runnable("test_executor"),
            "file_operator": self.agent_adapter.get_tool_as_runnable("file_operator"),
            "code_generator": self.agent_adapter.get_tool_as_runnable("code_generator"),
        }
        # 构建工作流图
        self._build_graph()
        
        return self
        
    def _build_graph(self):
        """构建自动化测试工作流图"""
        # 创建状态图
        self.graph = StateGraph(AutomationState)
        
        # 添加节点
        self.graph.add_node(AutomationStage.PREPARE_ENVIRONMENT, self._prepare_environment)
        self.graph.add_node(AutomationStage.GENERATE_TEST_SCRIPTS, self._generate_test_scripts)
        self.graph.add_node(AutomationStage.EXECUTE_TESTS, self._execute_tests)
        self.graph.add_node(AutomationStage.COLLECT_RESULTS, self._collect_results)
        self.graph.add_node(AutomationStage.ANALYZE_FAILURES, self._analyze_failures)
        self.graph.add_node(AutomationStage.RETRY_FAILED_TESTS, self._retry_failed_tests)
        self.graph.add_node(AutomationStage.FINALIZE_RESULTS, self._finalize_results)
        
        # 添加边：定义标准执行流程
        self.graph.add_edge(AutomationStage.PREPARE_ENVIRONMENT, AutomationStage.GENERATE_TEST_SCRIPTS)
        self.graph.add_edge(AutomationStage.GENERATE_TEST_SCRIPTS, AutomationStage.EXECUTE_TESTS)
        self.graph.add_edge(AutomationStage.EXECUTE_TESTS, AutomationStage.COLLECT_RESULTS)
        
        # 添加条件边：从结果收集到失败分析或完成
        self.graph.add_conditional_edges(
            AutomationStage.COLLECT_RESULTS,
            self._check_test_failures,
            {
                "has_failures": AutomationStage.ANALYZE_FAILURES,
                "no_failures": AutomationStage.FINALIZE_RESULTS,
            }
        )
        
        # 添加条件边：从失败分析到重试或完成
        self.graph.add_conditional_edges(
            AutomationStage.ANALYZE_FAILURES,
            self._check_retry_condition,
            {
                "should_retry": AutomationStage.RETRY_FAILED_TESTS,
                "max_retries_reached": AutomationStage.FINALIZE_RESULTS,
            }
        )
        
        # 从重试返回到执行测试
        self.graph.add_edge(AutomationStage.RETRY_FAILED_TESTS, AutomationStage.EXECUTE_TESTS)
        
        # 最终完成
        self.graph.add_edge(AutomationStage.FINALIZE_RESULTS, END)
        
        # 设置入口节点
        self.graph.set_entry_point(AutomationStage.PREPARE_ENVIRONMENT)
        # 编译图
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    async def _prepare_environment(self, state: AutomationState) -> AutomationState:
        """准备测试环境"""
        logger.info("执行环境准备阶段")
        try:
            test_cases = state["test_cases"]
            
            # 准备提示
            test_cases_str = "\n".join([
                f"- {tc['id']}: {tc['title']}" 
                for tc in test_cases[:5]  # 限制显示数量
            ])
            
            prompt = f"""
            请为以下测试用例准备测试环境：

            测试用例:
            {test_cases_str}

            请提供以下信息：
            1. 所需的软件环境
            2. 硬件需求
            3. 网络配置
            4. 初始化步骤
            5. 测试数据准备
            """
            
            # 执行智能体
            response = await self.automation_agent.run(prompt)
            
            # 解析环境配置（简单模拟）
            environment = {
                "software": {
                    "os": "Linux",
                    "version": "Ubuntu 20.04",
                    "dependencies": ["python3", "pytest", "selenium"]
                },
                "hardware": {
                    "cpu": "4 cores",
                    "memory": "8GB",
                    "storage": "100GB"
                },
                "network": {
                    "type": "isolated",
                    "connections": ["internal"]
                },
                "data": {
                    "path": "/tmp/test_data",
                    "fixtures": ["sample1.json", "sample2.json"]
                }
            }
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.PREPARE_ENVIRONMENT,
                "input": test_cases,
                "output": response,
                "environment": environment
            }
            
            # 更新状态
            return {
                **state,
                "environment": environment,
                "current_stage": AutomationStage.GENERATE_TEST_SCRIPTS,
                "status": "environment_prepared",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"环境准备失败: {str(e)}")
            return {
                **state,
                "error": f"环境准备失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    async def _generate_test_scripts(self, state: AutomationState) -> AutomationState:
        """生成测试脚本"""
        logger.info("执行测试脚本生成阶段")
        try:
            test_cases = state["test_cases"]
            environment = state["environment"]
            
            # 准备提示
            prompt = f"""
            请为以下测试用例生成自动化测试脚本：

            测试环境:
            - 操作系统: {environment['software']['os']} {environment['software']['version']}
            - 依赖项: {', '.join(environment['software']['dependencies'])}

            请为每个测试用例生成一个Python测试脚本，使用pytest框架。
            """
            # 执行智能体
            response = await self.automation_agent.run(prompt)
            
            # 生成测试脚本（简单模拟）
            test_scripts = {}
            for tc in test_cases:
                test_id = tc["id"]
                test_scripts[test_id] = f"""
import pytest
import time

def test_{test_id.lower()}():
    \"\"\"
    {tc['title']}
    
    目标: {tc.get('objective', '测试目标')}
    \"\"\"
    # 设置
    print("设置测试环境")
    
    # 执行测试步骤
    print("执行测试步骤")
    
    # 验证结果
    assert True, "测试应该通过"
    
    # 清理
    print("清理测试环境")
"""
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.GENERATE_TEST_SCRIPTS,
                "input": {"test_cases": test_cases, "environment": environment},
                "output": response,
                "test_scripts": test_scripts
            }
            # 更新状态
            return {
                **state,
                "test_scripts": test_scripts,
                "current_stage": AutomationStage.EXECUTE_TESTS,
                "status": "scripts_generated",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试脚本生成失败: {str(e)}")
            return {
                **state,
                "error": f"测试脚本生成失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    async def _execute_tests(self, state: AutomationState) -> AutomationState:
        """执行测试脚本"""
        logger.info("执行测试阶段")
        try:
            test_scripts = state["test_scripts"]
            environment = state["environment"]
            retry_mode = state.get("current_stage") == AutomationStage.RETRY_FAILED_TESTS
            
            # 确定要执行的测试
            tests_to_execute = {}
            if retry_mode:
                # 如果是重试模式，只执行失败的测试
                failed_tests = state.get("failed_tests", [])
                tests_to_execute = {
                    test_id: script 
                    for test_id, script in test_scripts.items()
                    if test_id in failed_tests
                }
            else:
                # 否则执行所有测试
                tests_to_execute = test_scripts
            
            # 准备提示
            tests_str = "\n".join([f"- {test_id}" for test_id in tests_to_execute.keys()])
            prompt = f"""
            请在以下环境中执行这些测试脚本：

            测试环境:
            - 操作系统: {environment['software']['os']} {environment['software']['version']}
            - 依赖项: {', '.join(environment['software']['dependencies'])}

            要执行的测试:
            {tests_str}

            {"这是重试执行，请特别关注之前失败的部分。" if retry_mode else ""}
            """
            
            # 执行智能体
            response = await self.automation_agent.run(prompt)
            
            # 模拟测试执行结果
            import random
            test_results = {}
            for test_id in tests_to_execute.keys():
                # 在重试模式下提高通过率
                pass_probability = 0.8 if retry_mode else 0.6
                passed = random.random() < pass_probability
                
                test_results[test_id] = {
                    "status": "passed" if passed else "failed",
                    "duration": random.uniform(0.5, 5.0),
                    "output": f"Test {test_id} {'passed' if passed else 'failed'}",
                    "error": None if passed else "AssertionError: Test condition not met"
                }
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.EXECUTE_TESTS,
                "input": {"tests": tests_to_execute, "environment": environment},
                "output": response,
                "test_results": test_results,
                "is_retry": retry_mode
            }
            
            # 更新状态
            return {
                **state,
                "test_results": {**state.get("test_results", {}), **test_results},
                "current_stage": AutomationStage.COLLECT_RESULTS,
                "status": "tests_executed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试执行失败: {str(e)}")
            return {
                **state,
                "error": f"测试执行失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    async def _collect_results(self, state: AutomationState) -> AutomationState:
        """收集测试结果"""
        logger.info("执行结果收集阶段")
        try:
            test_results = state["test_results"]
            
            # 统计结果
            total = len(test_results)
            passed = sum(1 for result in test_results.values() if result["status"] == "passed")
            failed = total - passed
            
            # 找出失败的测试
            failed_tests = [
                test_id for test_id, result in test_results.items()
                if result["status"] == "failed"
            ]
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.COLLECT_RESULTS,
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed
                },
                "failed_tests": failed_tests
            }
            # 更新状态
            next_stage = AutomationStage.ANALYZE_FAILURES if failed_tests else AutomationStage.FINALIZE_RESULTS
            
            return {
                **state,
                "failed_tests": failed_tests,
                "current_stage": next_stage,
                "status": "results_collected",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"结果收集失败: {str(e)}")
            return {
                **state,
                "error": f"结果收集失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    def _check_test_failures(self, state: AutomationState) -> Literal["has_failures", "no_failures"]:
        """检查是否有测试失败"""
        failed_tests = state.get("failed_tests", [])
        if failed_tests:
            return "has_failures"
        return "no_failures"
    
    async def _analyze_failures(self, state: AutomationState) -> AutomationState:
        """分析失败的测试"""
        logger.info("执行失败分析阶段")
        try:
            failed_tests = state["failed_tests"]
            test_results = state["test_results"]
            
            # 准备提示
            failures_str = "\n".join([
                f"- {test_id}: {test_results[test_id]['error']}" 
                for test_id in failed_tests
            ])
            
            prompt = f"""
            请分析以下测试失败：

            失败的测试:
            {failures_str}

            对每个失败，请提供：
            1. 可能的失败原因
            2. 建议的修复方法
            3. 是否值得重试
            """
            
            # 执行智能体
            response = await self.automation_agent.run(prompt)
            
            # 更新重试计数
            retry_count = state.get("retry_count", {})
            for test_id in failed_tests:
                retry_count[test_id] = retry_count.get(test_id, 0) + 1
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.ANALYZE_FAILURES,
                "input": {"failed_tests": failed_tests, "test_results": test_results},
                "output": response,
                "retry_count": retry_count
            }
            # 更新状态
            return {
                **state,
                "retry_count": retry_count,
                "current_stage": AutomationStage.RETRY_FAILED_TESTS,
                "status": "failures_analyzed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"失败分析失败: {str(e)}")
            return {
                **state,
                "error": f"失败分析失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    def _check_retry_condition(self, state: AutomationState) -> Literal["should_retry", "max_retries_reached"]:
        """检查是否应该重试"""
        retry_count = state.get("retry_count", {})
        # 检查是否所有失败的测试都已达到最大重试次数
        for test_id in state.get("failed_tests", []):
            if retry_count.get(test_id, 0) <= self.max_retries:
                return "should_retry"
        return "max_retries_reached"
    
    async def _retry_failed_tests(self, state: AutomationState) -> AutomationState:
        """重试失败的测试"""
        logger.info("执行测试重试阶段")
        try:
            failed_tests = state["failed_tests"]
            retry_count = state.get("retry_count", {})
            
            # 记录历史
            history_entry = {
                "stage": AutomationStage.RETRY_FAILED_TESTS,
                "failed_tests": failed_tests,
                "retry_count": retry_count
            }
            
            # 更新状态
            return {
                **state,
                "current_stage": AutomationStage.EXECUTE_TESTS,
                "status": "retrying_tests",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试重试准备失败: {str(e)}")
            return {
                **state,
                "error": f"测试重试准备失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    async def _finalize_results(self, state: AutomationState) -> AutomationState:
        """完成测试结果"""
        logger.info("执行结果完成阶段")
        try:
            test_results = state["test_results"]
            failed_tests = state.get("failed_tests", [])
            
            # 统计结果
            total = len(test_results)
            passed = sum(1 for result in test_results.values() if result["status"] == "passed")
            failed = total - passed
            pass_rate = (passed / total) * 100 if total > 0 else 0
            
            # 准备提示
            prompt = f"""
            请生成测试执行报告，包含以下内容：

            1. 测试执行摘要
               - 总测试数: {total}
               - 通过测试数: {passed}
               - 失败测试数: {failed}
               - 通过率: {pass_rate:.2f}%

            2. 失败测试详情
            3. 测试执行环境
            4. 执行时间统计
            5. 建议和下一步行动
            """
            
            # 执行智能体
            response = await self.automation_agent.run(prompt)
            
            # 构建最终报告
            final_report = {
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate
                },
                "failed_tests": failed_tests,
                "test_results": test_results,
                "report": response
            }
            # 记录历史
            history_entry = {
                "stage": AutomationStage.FINALIZE_RESULTS,
                "output": response,
                "final_report": final_report
            }
            
            # 更新状态
            return {
                **state,
                "final_report": final_report,
                "current_stage": AutomationStage.COMPLETE,
                "status": "completed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"结果完成失败: {str(e)}")
            return {
                **state,
                "error": f"结果完成失败: {str(e)}",
                "current_stage": AutomationStage.ERROR,
                "status": "error"
            }
    
    async def run_tests(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """运行自动化测试"""
        # 生成执行ID
        self.execution_id = str(uuid.uuid4())
        
        # 准备初始状态
        initial_state: AutomationState = {
            "test_cases": test_cases,
            "environment": {},
            "test_scripts": {},
            "test_results": {},
            "failed_tests": [],
            "retry_count": {},
            "final_report": None,
            "current_stage": AutomationStage.PREPARE_ENVIRONMENT,
            "status": "initialized",
            "history": [],
            "error": None
        }
        
        # 执行测试流程
        try:
            logger.info(f"开始自动化测试执行，执行ID: {self.execution_id}")
            result = await self.compiled_graph.ainvoke(initial_state, {"execution_id": self.execution_id})
            logger.info(f"自动化测试执行完成，执行ID: {self.execution_id}")
            return result
        except Exception as e:
            logger.error(f"自动化测试执行失败: {str(e)}")
            return {
                **initial_state,
                "status": "error",
                "current_stage": AutomationStage.ERROR,
                "error": f"自动化测试执行失败: {str(e)}"
            }
    
    def get_graph_visualization(self) -> str:
        """获取流程图的可视化表示（Mermaid格式）"""
        if not self.graph:
            return "图尚未构建"
        return self.graph.get_mermaid(add_dependencies=True)