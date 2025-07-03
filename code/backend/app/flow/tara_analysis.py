from typing import Dict, Optional, Any

from app.flow.planning import PlanningFlow
from app.flow.base import FlowStatus
from app.core.logging import logger


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
            1. 首先生成详细的执行计划，包括子任务和步骤
            2. 识别系统资产和边界
            3. 分析潜在威胁
            4. 评估风险等级
            5. 提出缓解措施建议
            6. 检查法规合规性
            
            请注意：必须先生成执行计划，然后按照计划逐步执行，不要跳过计划生成步骤。
            """
            
            logger.info(f"初始化TARA分析流，目标系统: {target_system[:50]}...")
            logger.info("任务描述已设置，明确要求先生成执行计划")
            
            self.context["task"] = task
            
            # 调用基类初始化方法
            result = await super().initialize(task, self.context, **kwargs)
            
            if result:
                logger.info(f"TARA分析流 {self.flow_id} 初始化成功")
            else:
                logger.error(f"TARA分析流 {self.flow_id} 初始化失败: {self.error}")
                
            return result
        except Exception as e:
            self.error = f"初始化TARA分析流失败: {str(e)}"
            self.status = FlowStatus.FAILED
            logger.error(f"初始化TARA分析流失败: {str(e)}")
            return False 