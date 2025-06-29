from enum import Enum
from typing import Optional

from app.flow.planning import PlanningFlow
from app.flow.tara_analysis import TaraAnalysisFlow
from app.flow.test_case_generation import TestCaseGenerationFlow
from app.flow.automation_test import AutomationTestFlow
from app.flow.report_generation import ReportGenerationFlow


class FlowType(str, Enum):
    """执行流类型枚举"""
    PLANNING = "planning"
    TARA = "tara"
    TESTCASE = "testcase"
    AUTOMATION = "automation"
    REPORT = "report"


class FlowFactory:
    """执行流工厂"""
    
    def __init__(self, agent_factory=None):
        self.agent_factory = agent_factory
    
    def create_flow(self, flow_type: str, flow_id: str, name: str = None, description: str = None, **kwargs):
        """创建执行流"""
        if flow_type == FlowType.PLANNING:
            return PlanningFlow(flow_id, name or "规划执行", description, agent_factory=self.agent_factory)
        elif flow_type == FlowType.TARA:
            return TaraAnalysisFlow(flow_id, name or "TARA分析", description, agent_factory=self.agent_factory)
        elif flow_type == FlowType.TESTCASE:
            return TestCaseGenerationFlow(flow_id, name or "测试用例生成", description, agent_factory=self.agent_factory)
        elif flow_type == FlowType.AUTOMATION:
            return AutomationTestFlow(flow_id, name or "自动化测试执行", description, agent_factory=self.agent_factory)
        elif flow_type == FlowType.REPORT:
            return ReportGenerationFlow(flow_id, name or "报告生成", description, agent_factory=self.agent_factory)
        else:
            raise ValueError(f"Unsupported flow type: {flow_type}") 