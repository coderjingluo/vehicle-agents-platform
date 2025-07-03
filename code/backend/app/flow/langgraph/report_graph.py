"""
KunlunSec AI Platform - LangGraph 报告分析流程

使用LangGraph实现的报告分析与生成流程。
"""

import uuid
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Union
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from langchain_core.runnables import Runnable, RunnableLambda

from app.core.logging import logger
from app.agent.report import ReportAnalysisAgent
from app.agent.adapter import LangGraphAgentAdapter


# 报告分析阶段
class ReportStage(str, Enum):
    INIT = "init"
    ANALYZE_TEST_RESULTS = "analyze_test_results"
    CATEGORIZE_ISSUES = "categorize_issues"
    GENERATE_VISUALIZATIONS = "generate_visualizations"
    CREATE_RISK_MATRIX = "create_risk_matrix"
    SUMMARIZE_FINDINGS = "summarize_findings"
    GENERATE_REPORT = "generate_report"
    COMPLETE = "complete"
    ERROR = "error"


# 报告分析状态
class ReportState(TypedDict):
    """报告分析状态"""
    test_results: Dict[str, Dict[str, Any]]     # 测试结果
    issues: List[Dict[str, Any]]                # 识别的问题
    categories: Dict[str, List[Dict[str, Any]]] # 问题分类
    visualizations: Dict[str, Any]              # 生成的可视化
    risk_matrix: Dict[str, Any]                 # 风险矩阵
    summary: Dict[str, Any]                     # 发现总结
    report: Optional[str]                       # 最终报告
    report_format: str                          # 报告格式
    current_stage: ReportStage                  # 当前阶段
    status: str                                 # 当前状态
    history: List[Dict[str, Any]]               # 执行历史
    error: Optional[str]                        # 错误信息(如果有)


class ReportAnalysisGraph:
    """基于LangGraph实现的报告分析智能体图"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化报告分析图
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.report_agent = None
        self.agent_adapter = None
        self.tools_map = {}
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver()
        self.execution_id = None
        
    async def setup(self):
        """设置智能体和工具"""
        # 初始化报告分析智能体
        self.report_agent = await ReportAnalysisAgent.create()
        
        # 创建适配器
        self.agent_adapter = LangGraphAgentAdapter(self.report_agent)
        
        # 配置工具
        self.tools_map = {
            "report_generator": self.agent_adapter.get_tool_as_runnable("report_generator"),
            "data_visualization": self.agent_adapter.get_tool_as_runnable("data_visualization"),
            "file_operator": self.agent_adapter.get_tool_as_runnable("file_operator"),
            "rag_query": self.agent_adapter.get_tool_as_runnable("rag_query"),
        }
        
        # 构建工作流图
        self._build_graph()
        
        return self
        
    def _build_graph(self):
        """构建报告分析工作流图"""
        # 创建状态图
        self.graph = StateGraph(ReportState)
        
        # 添加节点
        self.graph.add_node(ReportStage.ANALYZE_TEST_RESULTS, self._analyze_test_results)
        self.graph.add_node(ReportStage.CATEGORIZE_ISSUES, self._categorize_issues)
        self.graph.add_node(ReportStage.GENERATE_VISUALIZATIONS, self._generate_visualizations)
        self.graph.add_node(ReportStage.CREATE_RISK_MATRIX, self._create_risk_matrix)
        self.graph.add_node(ReportStage.SUMMARIZE_FINDINGS, self._summarize_findings)
        self.graph.add_node(ReportStage.GENERATE_REPORT, self._generate_report)
        
        # 添加边：定义标准执行流程
        self.graph.add_edge(ReportStage.ANALYZE_TEST_RESULTS, ReportStage.CATEGORIZE_ISSUES)
        self.graph.add_edge(ReportStage.CATEGORIZE_ISSUES, ReportStage.GENERATE_VISUALIZATIONS)
        self.graph.add_edge(ReportStage.GENERATE_VISUALIZATIONS, ReportStage.CREATE_RISK_MATRIX)
        self.graph.add_edge(ReportStage.CREATE_RISK_MATRIX, ReportStage.SUMMARIZE_FINDINGS)
        self.graph.add_edge(ReportStage.SUMMARIZE_FINDINGS, ReportStage.GENERATE_REPORT)
        
        # 添加条件边：从最终报告生成到完成
        self.graph.add_conditional_edges(
            ReportStage.GENERATE_REPORT,
            self._check_report_condition,
            {
                "complete": END,
                "needs_revision": ReportStage.ANALYZE_TEST_RESULTS,  # 如需修改分析，返回开始
            }
        )
        
        # 设置入口节点
        self.graph.set_entry_point(ReportStage.ANALYZE_TEST_RESULTS)
        
        # 编译图
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    async def _analyze_test_results(self, state: ReportState) -> ReportState:
        """分析测试结果"""
        logger.info("执行测试结果分析阶段")
        try:
            test_results = state["test_results"]
            
            # 准备提示
            prompt = f"""
            请分析以下测试结果，识别所有安全问题：

            测试结果数量: {len(test_results)}

            请提供以下信息：
            1. 失败测试的列表
            2. 每个失败测试的详细描述
            3. 初步问题分类
            4. 问题严重程度评估
            """
            
            # 执行智能体
            response = await self.report_agent.run(prompt)
            
            # 使用智能体专用方法分析测试结果
            analysis_result = await self.report_agent.analyze_test_results(test_results)
            issues = analysis_result.get("issues", [])
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.ANALYZE_TEST_RESULTS,
                "input": {"test_results_count": len(test_results)},
                "output": response,
                "issues": issues
            }
            
            # 更新状态
            return {
                **state,
                "issues": issues,
                "current_stage": ReportStage.CATEGORIZE_ISSUES,
                "status": "results_analyzed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"测试结果分析失败: {str(e)}")
            return {
                **state,
                "error": f"测试结果分析失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _categorize_issues(self, state: ReportState) -> ReportState:
        """将问题进行分类"""
        logger.info("执行问题分类阶段")
        try:
            issues = state["issues"]
            
            # 准备提示
            issues_str = "\n".join([
                f"- {issue.get('id', 'N/A')}: {issue.get('name', '未命名问题')} ({issue.get('severity', '未知')})" 
                for issue in issues[:5]  # 限制显示数量
            ])
            
            prompt = f"""
            请对以下识别出的安全问题进行分类:

            问题：
            {issues_str}

            将问题分为以下类别：
            1. 认证问题
            2. 授权问题 
            3. 数据安全问题
            4. 网络安全问题
            5. 代码安全问题
            """
            
            # 执行智能体
            response = await self.report_agent.run(prompt)
            
            # 使用智能体专用方法对问题进行分类
            categories = await self.report_agent.categorize_issues(issues)
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.CATEGORIZE_ISSUES,
                "input": {"issues_count": len(issues)},
                "output": response,
                "categories": categories
            }
            
            # 更新状态
            return {
                **state,
                "categories": categories,
                "current_stage": ReportStage.GENERATE_VISUALIZATIONS,
                "status": "issues_categorized",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"问题分类失败: {str(e)}")
            return {
                **state,
                "error": f"问题分类失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _generate_visualizations(self, state: ReportState) -> ReportState:
        """生成数据可视化"""
        logger.info("执行数据可视化阶段")
        try:
            categories = state["categories"]
            issues = state["issues"]
            
            # 准备可视化数据
            visualization_data = {
                "categories": {
                    "labels": list(categories.keys()),
                    "values": [len(cat) for cat in categories.values()]
                },
                "severity": {
                    "labels": ["高", "中", "低"],
                    "values": [
                        sum(1 for i in issues if i.get("severity") == "高"),
                        sum(1 for i in issues if i.get("severity") == "中"),
                        sum(1 for i in issues if i.get("severity") == "低")
                    ]
                }
            }
            
            # 准备提示
            prompt = """
            请为以下测试结果数据生成可视化：

            1. 按问题分类的饼图
            2. 按严重程度的柱状图
            """
            
            # 执行智能体
            response = await self.report_agent.run(prompt)
            
            # 获取可视化工具
            data_viz_tool = self.tools_map.get("data_visualization")
            
            # 生成可视化
            visualizations = {
                "categories_chart": await data_viz_tool(
                    data=visualization_data["categories"], 
                    chart_type="pie"
                ),
                "severity_chart": await data_viz_tool(
                    data=visualization_data["severity"],
                    chart_type="bar"
                )
            }
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.GENERATE_VISUALIZATIONS,
                "input": visualization_data,
                "output": response,
                "visualizations": {k: "图表已生成" for k in visualizations}
            }
            
            # 更新状态
            return {
                **state,
                "visualizations": visualizations,
                "current_stage": ReportStage.CREATE_RISK_MATRIX,
                "status": "visualizations_generated",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"数据可视化生成失败: {str(e)}")
            return {
                **state,
                "error": f"数据可视化生成失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _create_risk_matrix(self, state: ReportState) -> ReportState:
        """创建风险矩阵"""
        logger.info("执行风险矩阵生成阶段")
        try:
            categories = state["categories"]
            
            # 准备提示
            prompt = """
            请基于分析结果生成风险矩阵，将每个问题映射到以下矩阵中：

            - 高影响 x 高可能性: 高风险
            - 高影响 x 中可能性: 高风险
            - 高影响 x 低可能性: 中风险
            - 中影响 x 高可能性: 高风险
            - 中影响 x 中可能性: 中风险
            - 中影响 x 低可能性: 低风险
            - 低影响 x 高可能性: 中风险
            - 低影响 x 中可能性: 低风险
            - 低影响 x 低可能性: 低风险
            """
            
            # 执行智能体
            response = await self.report_agent.run(prompt)
            
            # 使用智能体专用方法生成风险矩阵
            risk_matrix = await self.report_agent.generate_risk_matrix(categories)
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.CREATE_RISK_MATRIX,
                "input": {"categories": list(categories.keys())},
                "output": response,
                "risk_matrix": risk_matrix
            }
            
            # 更新状态
            return {
                **state,
                "risk_matrix": risk_matrix,
                "current_stage": ReportStage.SUMMARIZE_FINDINGS,
                "status": "risk_matrix_created",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"风险矩阵生成失败: {str(e)}")
            return {
                **state,
                "error": f"风险矩阵生成失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _summarize_findings(self, state: ReportState) -> ReportState:
        """总结发现"""
        logger.info("执行发现总结阶段")
        try:
            issues = state["issues"]
            risk_matrix = state["risk_matrix"]
            
            # 计算风险得分
            risk_score = await self._calculate_risk_score(risk_matrix)
            
            # 汇总信息
            summary = {
                "total_issues": len(issues),
                "severity_counts": {
                    "high": sum(1 for i in issues if i.get("severity") == "高"),
                    "medium": sum(1 for i in issues if i.get("severity") == "中"),
                    "low": sum(1 for i in issues if i.get("severity") == "低")
                },
                "risk_score": risk_score,
                "risk_level": self._determine_risk_level(risk_score)
            }
            
            # 准备提示
            prompt = f"""
            请总结测试发现，包括：

            1. 总体安全状况评估
            2. 主要问题概述
            3. 最严重的问题
            4. 优先修复建议
            
            总问题数: {summary['total_issues']}
            高严重性问题: {summary['severity_counts']['high']}
            中严重性问题: {summary['severity_counts']['medium']}
            低严重性问题: {summary['severity_counts']['low']}
            总体风险等级: {summary['risk_level']}
            """
            
            # 执行智能体
            response = await self.report_agent.run(prompt)
            
            # 更新摘要
            summary["overview"] = response
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.SUMMARIZE_FINDINGS,
                "input": {"issues_count": len(issues), "risk_matrix": "风险矩阵"},
                "output": response,
                "summary": summary
            }
            
            # 更新状态
            return {
                **state,
                "summary": summary,
                "current_stage": ReportStage.GENERATE_REPORT,
                "status": "findings_summarized",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"发现总结失败: {str(e)}")
            return {
                **state,
                "error": f"发现总结失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _generate_report(self, state: ReportState) -> ReportState:
        """生成最终报告"""
        logger.info("执行报告生成阶段")
        try:
            issues = state["issues"]
            categories = state["categories"]
            risk_matrix = state["risk_matrix"]
            summary = state["summary"]
            report_format = state.get("report_format", "markdown")
            
            # 准备分析数据
            analysis_data = {
                "issues": issues,
                "categories": categories,
                "matrix": risk_matrix,
                "summary": summary,
                "project_name": "车联网安全测试项目",
                "test_date": "2023-01-01",  # 应从实际状态中获取
            }
            
            # 使用智能体生成报告
            report = await self.report_agent.generate_report(analysis_data)
            
            # 记录历史
            history_entry = {
                "stage": ReportStage.GENERATE_REPORT,
                "input": analysis_data,
                "output": "生成的报告内容",
                "report_format": report_format
            }
            
            # 更新状态
            return {
                **state,
                "report": report,
                "current_stage": ReportStage.COMPLETE,
                "status": "completed",
                "history": state.get("history", []) + [history_entry]
            }
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            return {
                **state,
                "error": f"报告生成失败: {str(e)}",
                "current_stage": ReportStage.ERROR,
                "status": "error"
            }
    
    async def _calculate_risk_score(self, risk_matrix: Dict[str, Dict[str, Any]]) -> float:
        """计算风险得分"""
        # 风险权重
        weights = {
            "high": {"high": 9, "medium": 6, "low": 3},
            "medium": {"high": 6, "medium": 4, "low": 2},
            "low": {"high": 3, "medium": 2, "low": 1}
        }
        
        # 计算加权总分
        score = 0
        count = 0
        
        for impact, severities in risk_matrix.items():
            for severity, issues in severities.items():
                num = len(issues)
                score += weights[impact][severity] * num
                count += num
        
        # 返回平均风险分数
        return score / max(count, 1)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """根据风险得分确定风险等级"""
        if risk_score >= 6:
            return "高"
        elif risk_score >= 3:
            return "中"
        else:
            return "低"
    
    def _check_report_condition(self, state: ReportState) -> Literal["complete", "needs_revision"]:
        """检查报告条件"""
        # 检查报告是否已生成
        if state.get("report") and state.get("current_stage") == ReportStage.COMPLETE:
            return "complete"
        return "needs_revision"
    
    async def generate_report(self, test_results: Dict[str, Any], report_format: str = "markdown") -> Dict[str, Any]:
        """运行完整报告分析"""
        # 生成执行ID
        self.execution_id = str(uuid.uuid4())
        
        # 准备初始状态
        initial_state: ReportState = {
            "test_results": test_results,
            "issues": [],
            "categories": {},
            "visualizations": {},
            "risk_matrix": {},
            "summary": {},
            "report": None,
            "report_format": report_format,
            "status": "initialized",
            "current_stage": ReportStage.ANALYZE_TEST_RESULTS,
            "history": [],
            "error": None
        }
        
        # 执行分析流程
        try:
            logger.info(f"开始报告分析，执行ID: {self.execution_id}")
            result = await self.compiled_graph.ainvoke(initial_state, {"execution_id": self.execution_id})
            logger.info(f"报告分析完成，执行ID: {self.execution_id}")
            return result
        except Exception as e:
            logger.error(f"报告分析执行失败: {str(e)}")
            return {
                **initial_state,
                "status": "error",
                "current_stage": ReportStage.ERROR,
                "error": f"报告分析执行失败: {str(e)}"
            }
    
    def get_graph_visualization(self) -> str:
        """获取图的可视化表示（Mermaid格式）"""
        if not self.graph:
            return "图尚未构建"
        return self.graph.get_mermaid(add_dependencies=True)
