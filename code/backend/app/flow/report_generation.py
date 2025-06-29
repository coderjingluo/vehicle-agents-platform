import json
from typing import Dict, Optional, Any

from app.flow.planning import PlanningFlow
from app.flow.base import FlowStatus


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