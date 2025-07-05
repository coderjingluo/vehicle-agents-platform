"""
KunlunSec AI Platform - LangGraph 测试用例生成流程

使用LangGraph实现的测试用例生成流程。
"""

import uuid
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Union
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import Runnable, RunnableLambda

from app.core.logging import logger
from app.agent.testcase import TestCaseAgent
from app.agent.adapter import LangGraphAgentAdapter


# 测试用例生成阶段
class TestCaseStage(str, Enum):
    INIT = "init"
    ANALYZE_TARA_RESULTS = "analyze_tara_results"
    GENERATE_TEST_CASES = "generate_test_cases"
    VALIDATE_COVERAGE = "validate_coverage"
    OPTIMIZE_TEST_CASES = "optimize_test_cases"
    FINALIZE_TEST_SUITE = "finalize_test_suite"
    COMPLETE = "complete"
    ERROR = "error"


# 测试用例生成状态
class TestCaseState(TypedDict):
    """测试用例生成状态"""
    tara_result: Dict[str, Any]                # TARA分析结果
    threats: List[Dict[str, Any]]              # 提取的威胁
    test_cases: List[Dict[str, Any]]           # 生成的测试用例
    coverage: Dict[str, float]                 # 覆盖率指标
    optimized_test_cases: List[Dict[str, Any]] # 优化后的测试用例
    final_test_suite: Dict[str, Any]           # 最终测试套件
    current_stage: TestCaseStage               # 当前阶段
    status: str                                # 当前状态
    history: List[Dict[str, Any]]              # 执行历史
    error: Optional[str]                       # 错误信息(如果有)


class TestCaseAgentGraph:
    """基于LangGraph实现的测试用例生成智能体图"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化测试用例生成图
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.testcase_agent = None
        self.agent_adapter = None
        self.tools_map = {}
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver()
        self.execution_id = None
        
    async def setup(self):
        """设置智能体和工具"""
        # 初始化测试用例生成智能体
        self.testcase_agent = await TestCaseAgent.create()
        
        # 创建适配器
        self.agent_adapter = LangGraphAgentAdapter(self.testcase_agent)
        
        # 配置工具
        self.tools_map = {
            "test_case_generator": self.agent_adapter.get_tool_as_runnable("test_case_generator"),
            "rag_query": self.agent_adapter.get_tool_as_runnable("rag_query"),
            "file_operator": self.agent_adapter.get_tool_as_runnable("file_operator"),
        }
        
        # 构建工作流图
        self._build_graph()
        
        return self
        
    def _build_graph(self):
        """构建测试用例生成工作流图"""
        # 创建状态图
        self.graph = StateGraph(TestCaseState)
        
        # 添加节点
        self.graph.add_node(TestCaseStage.ANALYZE_TARA_RESULTS, self._analyze_tara_results)
        self.graph.add_node(TestCaseStage.GENERATE_TEST_CASES, self._generate_test_cases)
        self.graph.add_node(TestCaseStage.VALIDATE_COVERAGE, self._validate_coverage)
        self.graph.add_node(TestCaseStage.OPTIMIZE_TEST_CASES, self._optimize_test_cases)
        self.graph.add_node(TestCaseStage.FINALIZE_TEST_SUITE, self._finalize_test_suite)
        
        # 添加边：定义标准执行流程
        self.graph.add_edge(TestCaseStage.ANALYZE_TARA_RESULTS, TestCaseStage.GENERATE_TEST_CASES)
        self.graph.add_edge(TestCaseStage.GENERATE_TEST_CASES, TestCaseStage.VALIDATE_COVERAGE)
        
        # 添加条件边：从覆盖率验证到优化或完成
        self.graph.add_conditional_edges(
            TestCaseStage.VALIDATE_COVERAGE,
            self._check_coverage_condition,
            {
                "sufficient": TestCaseStage.FINALIZE_TEST_SUITE,
                "insufficient": TestCaseStage.OPTIMIZE_TEST_CASES,
            }
        )
        
        # 从优化返回到验证
        self.graph.add_edge(TestCaseStage.OPTIMIZE_TEST_CASES, TestCaseStage.VALIDATE_COVERAGE)
        
        # 最终完成
        self.graph.add_edge(TestCaseStage.FINALIZE_TEST_SUITE, END)
        
        # 设置入口节点
        self.graph.set_entry_point(TestCaseStage.ANALYZE_TARA_RESULTS)
        
        # 编译图
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    async def _analyze_tara_results(self, state: TestCaseState) -> TestCaseState:
        """分析TARA结果，提取威胁信息"""
        logger.info("执行TARA结果分析阶段")
        try:
            tara_result = state["tara_result"]
            
            # 准备提示
            prompt = f"""
            请分析以下TARA（威胁分析与风险评估）结果，提取所有需要进行测试的威胁：

            TARA结果概要:
            - 资产数量: {len(tara_result.get('assets', []))}
            - 威胁数量: {len(tara_result.get('threats', {}))}
            - 风险数量: {len(tara_result.get('risks', {}))}
            
            请提供以下信息：
            1. 每个威胁的详细描述
            2. 威胁的优先级和严重程度
            3. 受影响的资产
            4. 可能的攻击路径
            """
            
            # 执行智能体
            response = await self.testcase_agent.run(prompt)
            
            # 提取威胁（简化示例）
            threats = []
            
            # 从TARA结果中提取威胁
            for threat_id, threat_info in tara_result.get("threats", {}).items():
                threats.append({
                    "id": threat_id,
                    "name": threat_info.get("name", "未命名威胁"),
                    "description": threat_info.get("description", ""),
                    "severity": threat_info.get("severity", "中"),
                    "affected_assets": threat_info.get("affected_assets", []),
                    "attack_vectors": threat_info.get("attack_vectors", [])
                })
            
            # 记录历史
            history_entry = {
                "stage": TestCaseStage.ANALYZE_TARA_RESULTS,
                "input": {"tara_result_summary": "TARA分析结果摘要"},
                "output": response,
                "threats": threats
            }
            
            # 更新状态
            return {
                **state,
                "threats": threats,
                "current_stage": TestCaseStage.GENERATE_TEST_CASES,
                "status": "tara_analyzed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"TARA结果分析失败: {str(e)}")
            return {
                **state,
                "error": f"TARA结果分析失败: {str(e)}",
                "current_stage": TestCaseStage.ERROR,
                "status": "error"
            }
    
    async def _generate_test_cases(self, state: TestCaseState) -> TestCaseState:
        """生成测试用例"""
        logger.info("执行测试用例生成阶段")
        try:
            threats = state["threats"]
            
            # 准备提示
            threats_str = "\n".join([
                f"- {t['id']}: {t['name']} (严重性: {t['severity']})" 
                for t in threats[:5]  # 限制显示数量
            ])
            
            prompt = f"""
            请基于以下威胁生成详细的测试用例:

            威胁列表:
            {threats_str}

            每个测试用例需要包含:
            1. 测试ID和标题
            2. 测试目的
            3. 前置条件
            4. 测试步骤
            5. 预期结果
            6. 关联的威胁ID
            """
            
            # 执行智能体
            response = await self.testcase_agent.run(prompt)
            
            # 使用专用工具生成测试用例
            test_case_generator = self.tools_map.get("test_case_generator")
            if test_case_generator:
                test_cases_result = await test_case_generator({"threats": threats})
                test_cases = test_cases_result.get("test_cases", [])
            else:
                # 如果工具不可用，使用简单模拟数据
                test_cases = []
                for i, threat in enumerate(threats):
                    test_cases.append({
                        "id": f"TC{i+1:03d}",
                        "title": f"测试 {threat['name']}",
                        "purpose": f"验证系统是否能防御{threat['name']}",
                        "preconditions": "系统处于正常运行状态",
                        "steps": ["步骤1: 准备测试环境", "步骤2: 执行测试", "步骤3: 验证结果"],
                        "expected_results": "系统应当成功防御攻击",
                        "threat_ids": [threat["id"]]
                    })
            
            # 记录历史
            history_entry = {
                "stage": TestCaseStage.GENERATE_TEST_CASES,
                "input": {"threats_count": len(threats)},
                "output": response,
                "test_cases": test_cases
            }
            
            # 更新状态
            return {
                **state,
                "test_cases": test_cases,
                "current_stage": TestCaseStage.VALIDATE_COVERAGE,
                "status": "test_cases_generated",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试用例生成失败: {str(e)}")
            return {
                **state,
                "error": f"测试用例生成失败: {str(e)}",
                "current_stage": TestCaseStage.ERROR,
                "status": "error"
            }
    
    async def _validate_coverage(self, state: TestCaseState) -> TestCaseState:
        """验证测试覆盖率"""
        logger.info("执行测试覆盖率验证阶段")
        try:
            threats = state["threats"]
            test_cases = state["test_cases"]
            
            # 计算覆盖率
            threat_ids = {threat["id"] for threat in threats}
            covered_threats = set()
            
            for test_case in test_cases:
                covered_threats.update(test_case.get("threat_ids", []))
            
            threat_coverage = len(covered_threats) / len(threat_ids) if threat_ids else 0
            
            # 按严重程度分类威胁
            high_severity_threats = {t["id"] for t in threats if t.get("severity") == "高"}
            medium_severity_threats = {t["id"] for t in threats if t.get("severity") == "中"}
            low_severity_threats = {t["id"] for t in threats if t.get("severity") == "低"}
            
            # 计算不同严重程度的覆盖率
            high_covered = len(high_severity_threats.intersection(covered_threats))
            medium_covered = len(medium_severity_threats.intersection(covered_threats))
            low_covered = len(low_severity_threats.intersection(covered_threats))
            
            high_coverage = high_covered / len(high_severity_threats) if high_severity_threats else 1.0
            medium_coverage = medium_covered / len(medium_severity_threats) if medium_severity_threats else 1.0
            low_coverage = low_covered / len(low_severity_threats) if low_severity_threats else 1.0
            
            # 计算综合覆盖率（加权）
            weighted_coverage = (
                high_coverage * 0.6 + 
                medium_coverage * 0.3 + 
                low_coverage * 0.1
            )
            
            coverage = {
                "total": threat_coverage,
                "high_severity": high_coverage,
                "medium_severity": medium_coverage,
                "low_severity": low_coverage,
                "weighted": weighted_coverage,
                "uncovered_threats": list(threat_ids - covered_threats)
            }
            
            # 记录历史
            history_entry = {
                "stage": TestCaseStage.VALIDATE_COVERAGE,
                "input": {"test_cases_count": len(test_cases)},
                "output": f"覆盖率分析完成，总体覆盖率: {threat_coverage:.2%}",
                "coverage": coverage
            }
            
            # 更新状态
            return {
                **state,
                "coverage": coverage,
                "current_stage": TestCaseStage.VALIDATE_COVERAGE,  # 保持当前阶段，由条件边决定下一步
                "status": "coverage_validated",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"覆盖率验证失败: {str(e)}")
            return {
                **state,
                "error": f"覆盖率验证失败: {str(e)}",
                "current_stage": TestCaseStage.ERROR,
                "status": "error"
            }
    
    def _check_coverage_condition(self, state: TestCaseState) -> Literal["sufficient", "insufficient"]:
        """检查覆盖率是否足够"""
        coverage = state.get("coverage", {})
        weighted_coverage = coverage.get("weighted", 0)
        high_coverage = coverage.get("high_severity", 0)
        
        # 设定覆盖率阈值
        min_weighted_coverage = 0.85  # 85%的加权覆盖率
        min_high_coverage = 0.95      # 95%的高严重性威胁覆盖率
        
        if weighted_coverage >= min_weighted_coverage and high_coverage >= min_high_coverage:
            return "sufficient"
        else:
            return "insufficient"
    
    async def _optimize_test_cases(self, state: TestCaseState) -> TestCaseState:
        """优化测试用例"""
        logger.info("执行测试用例优化阶段")
        try:
            test_cases = state["test_cases"]
            coverage = state["coverage"]
            threats = state["threats"]
            
            # 找出未覆盖的威胁
            uncovered_threat_ids = set(coverage.get("uncovered_threats", []))
            uncovered_threats = [t for t in threats if t["id"] in uncovered_threat_ids]
            
            # 准备提示
            uncovered_threats_str = "\n".join([
                f"- {t['id']}: {t['name']} (严重性: {t['severity']})" 
                for t in uncovered_threats
            ])
            
            prompt = f"""
            需要为以下未覆盖的威胁生成额外的测试用例:

            未覆盖威胁:
            {uncovered_threats_str}

            当前测试用例数量: {len(test_cases)}
            当前覆盖率: {coverage.get('total', 0):.2%}
            高严重性威胁覆盖率: {coverage.get('high_severity', 0):.2%}

            请生成针对这些未覆盖威胁的测试用例，确保每个测试用例都有明确的目的和步骤。
            """
            
            # 执行智能体
            response = await self.testcase_agent.run(prompt)
            
            # 生成额外的测试用例（简化示例）
            additional_test_cases = []
            for i, threat in enumerate(uncovered_threats):
                additional_test_cases.append({
                    "id": f"TC_OPT{i+1:03d}",
                    "title": f"优化测试 - {threat['name']}",
                    "purpose": f"验证系统是否能防御{threat['name']}",
                    "preconditions": "系统处于正常运行状态",
                    "steps": ["步骤1: 准备测试环境", "步骤2: 执行测试", "步骤3: 验证结果"],
                    "expected_results": "系统应当成功防御攻击",
                    "threat_ids": [threat["id"]],
                    "optimized": True
                })
            
            # 合并测试用例
            optimized_test_cases = test_cases + additional_test_cases
            
            # 记录历史
            history_entry = {
                "stage": TestCaseStage.OPTIMIZE_TEST_CASES,
                "input": {"uncovered_threats_count": len(uncovered_threats)},
                "output": response,
                "additional_test_cases": additional_test_cases
            }
            
            # 更新状态
            return {
                **state,
                "optimized_test_cases": optimized_test_cases,
                "test_cases": optimized_test_cases,  # 更新主测试用例列表
                "current_stage": TestCaseStage.VALIDATE_COVERAGE,  # 返回验证阶段
                "status": "test_cases_optimized",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试用例优化失败: {str(e)}")
            return {
                **state,
                "error": f"测试用例优化失败: {str(e)}",
                "current_stage": TestCaseStage.ERROR,
                "status": "error"
            }
    
    async def _finalize_test_suite(self, state: TestCaseState) -> TestCaseState:
        """完成测试套件"""
        logger.info("执行测试套件完成阶段")
        try:
            test_cases = state["test_cases"]
            coverage = state["coverage"]
            
            # 准备提示
            prompt = f"""
            请整理以下测试用例集，形成最终的测试套件:

            测试用例数量: {len(test_cases)}
            覆盖率: {coverage.get('total', 0):.2%}
            
            请提供:
            1. 测试套件摘要
            2. 测试执行建议
            3. 测试环境要求
            4. 测试优先级排序
            """
            
            # 执行智能体
            response = await self.testcase_agent.run(prompt)
            
            # 构建最终测试套件
            final_test_suite = {
                "name": "车联网安全测试套件",
                "description": "基于TARA分析结果生成的安全测试套件",
                "test_cases": test_cases,
                "coverage": coverage,
                "execution_recommendations": response,
                "total_test_cases": len(test_cases),
                "creation_date": "2023-01-01"  # 应使用实际日期
            }
            
            # 记录历史
            history_entry = {
                "stage": TestCaseStage.FINALIZE_TEST_SUITE,
                "input": {"test_cases_count": len(test_cases)},
                "output": response,
                "final_test_suite": {"name": final_test_suite["name"], "total_test_cases": len(test_cases)}
            }
            
            # 更新状态
            return {
                **state,
                "final_test_suite": final_test_suite,
                "current_stage": TestCaseStage.COMPLETE,
                "status": "completed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试套件完成失败: {str(e)}")
            return {
                **state,
                "error": f"测试套件完成失败: {str(e)}",
                "current_stage": TestCaseStage.ERROR,
                "status": "error"
            }
    
    async def generate_test_cases(self, tara_result: Dict[str, Any]) -> Dict[str, Any]:
        """运行完整测试用例生成流程"""
        # 生成执行ID
        self.execution_id = str(uuid.uuid4())
        
        # 准备初始状态
        initial_state: TestCaseState = {
            "tara_result": tara_result,
            "threats": [],
            "test_cases": [],
            "coverage": {},
            "optimized_test_cases": [],
            "final_test_suite": {},
            "status": "initialized",
            "current_stage": TestCaseStage.ANALYZE_TARA_RESULTS,
            "history": [],
            "error": None
        }
        
        # 执行分析流程
        try:
            logger.info(f"开始测试用例生成，执行ID: {self.execution_id}")
            result = await self.compiled_graph.ainvoke(initial_state, {"execution_id": self.execution_id})
            logger.info(f"测试用例生成完成，执行ID: {self.execution_id}")
            return result
        except Exception as e:
            logger.error(f"测试用例生成执行失败: {str(e)}")
            return {
                **initial_state,
                "status": "error",
                "current_stage": TestCaseStage.ERROR,
                "error": f"测试用例生成执行失败: {str(e)}"
            }
    
    def get_graph_visualization(self) -> str:
        """获取图的可视化表示（Mermaid格式）"""
        if not self.graph:
            return "图尚未构建"
        return self.graph.get_mermaid(add_dependencies=True)
