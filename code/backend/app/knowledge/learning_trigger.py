from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.knowledge.knowledge_extractor import KnowledgeExtractor
from app.knowledge.knowledge_integrator import KnowledgeIntegrator


class LearningTrigger:
    """学习触发器，决定何时启动知识提取和整合流程"""
    
    def __init__(self, knowledge_extractor: KnowledgeExtractor, knowledge_integrator: KnowledgeIntegrator):
        self.extractor = knowledge_extractor
        self.integrator = knowledge_integrator
        self.trigger_conditions = {
            "task_completion": self._check_task_completion,
            "error_occurrence": self._check_error_occurrence,
            "new_pattern_detected": self._check_new_pattern,
            "scheduled": self._check_scheduled
        }
        self.last_learning_time = {}  # 记录每个知识库上次学习时间
    
    async def check_triggers(self, event_type: str, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查是否触发学习过程"""
        if event_type not in self.trigger_conditions:
            return False
            
        # 检查触发条件
        should_trigger = await self.trigger_conditions[event_type](event_data, kb_id)
        
        if should_trigger:
            # 执行知识提取和整合
            await self._execute_learning_cycle(event_type, event_data, kb_id)
            return True
            
        return False
    
    async def _execute_learning_cycle(self, source_type: str, source_data: Dict[str, Any], kb_id: str) -> None:
        """执行完整的学习周期"""
        try:
            # 1. 提取知识
            knowledge_items = await self.extractor.extract_knowledge(source_type, source_data)
            
            if not knowledge_items:
                logger.info(f"未从{source_type}提取到有价值的知识")
                return
                
            # 2. 整合知识
            stats = await self.integrator.integrate_knowledge(kb_id, knowledge_items)
            
            # 3. 更新学习时间
            self.last_learning_time[kb_id] = datetime.now()
            
            logger.info(f"知识学习周期完成: {stats}")
            
        except Exception as e:
            logger.error(f"学习周期执行失败: {str(e)}")
    
    async def _check_task_completion(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查任务完成触发条件"""
        # 实现任务完成触发逻辑
        return event_data.get("status") == "completed"
    
    async def _check_error_occurrence(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查错误发生触发条件"""
        # 实现错误触发逻辑
        return "error" in event_data and event_data["error"].get("should_learn", False)
    
    async def _check_new_pattern(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查新模式检测触发条件"""
        # 实现新模式检测逻辑
        return False
    
    async def _check_scheduled(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查定时触发条件"""
        # 检查上次学习时间，确保不会过于频繁
        last_time = self.last_learning_time.get(kb_id)
        if not last_time:
            return True
            
        # 至少间隔1小时
        min_interval = timedelta(hours=1)
        return datetime.now() - last_time > min_interval
