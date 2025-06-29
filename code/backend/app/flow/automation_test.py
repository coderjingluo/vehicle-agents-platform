import json
from typing import Dict, Optional, Any, List

from app.flow.planning import PlanningFlow
from app.flow.base import FlowStatus


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