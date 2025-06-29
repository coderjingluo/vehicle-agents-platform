import json
from typing import Dict, Optional, Any

from app.flow.planning import PlanningFlow
from app.flow.base import FlowStatus


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