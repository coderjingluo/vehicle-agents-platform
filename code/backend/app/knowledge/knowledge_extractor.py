import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.core.logging import logger
from app.knowledge.vector_db_connector import VectorDBConnector
from app.models.knowledge import DocumentChunk
class KnowledgeExtractor:
    """知识提取器，从智能体执行过程中提取知识"""
    
    def __init__(self, vector_db_connector: VectorDBConnector, embedding_model: str = "text-embedding-3-small"):
        self.vector_db_connector = vector_db_connector
        self.embedding_model = embedding_model
        self.extraction_strategies = {
            "task_execution": self._extract_from_task_execution,
            "agent_conversation": self._extract_from_conversation,
            "tool_usage": self._extract_from_tool_usage,
            "error_handling": self._extract_from_error_handling
        }
    async def extract_knowledge(self, source_type: str, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从不同类型的源数据中提取知识"""
        if source_type not in self.extraction_strategies:
            raise ValueError(f"不支持的知识源类型: {source_type}")
            
        extraction_func = self.extraction_strategies[source_type]
        knowledge_items = await extraction_func(source_data)
        
        # 过滤无价值的知识项
        filtered_items = await self._filter_knowledge_items(knowledge_items)
        
        return filtered_items
    async def _extract_from_task_execution(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从任务执行记录中提取知识"""
        knowledge_items = []
        
        # 提取任务目标和结果之间的关系
        if "goal" in task_data and "result" in task_data:
            knowledge_items.append({
                "type": "task_pattern",
                "goal": task_data["goal"],
                "successful_approach": task_data.get("successful_steps", []),
                "result": task_data["result"],
                "metadata": {
                    "task_id": task_data.get("id"),
                    "execution_time": task_data.get("execution_time"),
                    "confidence": self._calculate_confidence(task_data)
                }
            })
        
        # 提取有价值的中间结果
        if "intermediate_results" in task_data:
            for step, result in task_data["intermediate_results"].items():
                if self._is_valuable_result(result):
                    knowledge_items.append({
                        "type": "intermediate_insight",
                        "step": step,
                        "insight": result,
                        "metadata": {
                            "task_id": task_data.get("id"),
                            "confidence": 0.7  # 中间结果的默认置信度
                        }
                    })
        
        return knowledge_items
    def _calculate_confidence(self, task_data: Dict[str, Any]) -> float:
        """计算知识项的置信度"""
        # 根据任务完成状态、验证结果等计算置信度
        # 这里使用简单的启发式方法
        confidence = 0.5  # 默认置信度
        
        # 如果任务成功完成，增加置信度
        if task_data.get("status") == "completed":
            confidence += 0.3
            
        # 如果有验证结果且通过，增加置信度
        if task_data.get("validation", {}).get("passed", False):
            confidence += 0.2
            
        # 如果有错误，降低置信度
        if task_data.get("errors"):
            confidence -= 0.2 * len(task_data.get("errors", []))
            
        # 确保置信度在[0, 1]范围内
        return max(0.1, min(confidence, 1.0))
    
    def _is_valuable_result(self, result: Any) -> bool:
        """判断中间结果是否有价值"""
        # 如果结果为空，无价值
        if not result:
            return False
            
        # 字符串结果，长度需要足够
        if isinstance(result, str):
            return len(result) > 20
            
        # 字典或列表结果，需要有内容
        if isinstance(result, (dict, list)):
            return bool(result)
            
        # 其他类型暂不认为有价值
        return False
    
    async def _extract_from_conversation(self, conversation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从智能体对话中提取知识"""
        knowledge_items = []
        
        # 提取问题和回答
        if "messages" in conversation_data:
            messages = conversation_data["messages"]
            for i in range(len(messages) - 1):
                # 寻找用户问题和智能体回答对
                if messages[i].get("role") == "user" and messages[i+1].get("role") == "assistant":
                    question = messages[i].get("content", "")
                    answer = messages[i+1].get("content", "")
                    
                    # 过滤短问答
                    if len(question) > 10 and len(answer) > 30:
                        knowledge_items.append({
                            "type": "qa_pair",
                            "question": question,
                            "answer": answer,
                            "metadata": {
                                "conversation_id": conversation_data.get("id"),
                                "timestamp": messages[i+1].get("timestamp", datetime.now().isoformat()),
                                "confidence": 0.6  # QA对的默认置信度
                            }
                        })
                        
        return knowledge_items
    
    async def _extract_from_tool_usage(self, tool_usage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从工具使用记录中提取知识"""
        knowledge_items = []
        
        # 提取工具使用模式
        if "tool_name" in tool_usage_data and "input_params" in tool_usage_data and "result" in tool_usage_data:
            # 只关注成功的工具调用
            if tool_usage_data.get("status") == "success":
                knowledge_items.append({
                    "type": "tool_usage_pattern",
                    "tool_name": tool_usage_data["tool_name"],
                    "parameters": tool_usage_data["input_params"],
                    "result": tool_usage_data["result"],
                    "metadata": {
                        "task_id": tool_usage_data.get("task_id"),
                        "timestamp": tool_usage_data.get("timestamp", datetime.now().isoformat()),
                        "execution_time": tool_usage_data.get("execution_time"),
                        "confidence": 0.75  # 工具使用模式的默认置信度
                    }
                })
                
        return knowledge_items
    
    async def _extract_from_error_handling(self, error_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从错误处理记录中提取知识"""
        knowledge_items = []
        
        # 提取错误和解决方案
        if "error" in error_data and "resolution" in error_data:
            knowledge_items.append({
                "type": "error_resolution",
                "error_type": error_data.get("error_type", "unknown"),
                "error_message": error_data["error"],
                "resolution": error_data["resolution"],
                "context": error_data.get("context", {}),
                "metadata": {
                    "task_id": error_data.get("task_id"),
                    "timestamp": error_data.get("timestamp", datetime.now().isoformat()),
                    "confidence": 0.8 if error_data.get("resolution_successful", False) else 0.4
                }
            })
                
        return knowledge_items
    
    async def _filter_knowledge_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤低价值的知识项"""
        if not items:
            return []
            
        # 计算每个知识项的价值分数
        scored_items = []
        for item in items:
            value_score = await self._calculate_knowledge_value(item)
            if value_score > 0.5:  # 只保留价值分数大于0.5的项
                item["value_score"] = value_score
                scored_items.append(item)
        
        return scored_items
    
    async def _calculate_knowledge_value(self, item: Dict[str, Any]) -> float:
        """计算知识项的价值"""
        # 基础分值，根据类型不同有不同的初始值
        type_scores = {
            "task_pattern": 0.7,
            "intermediate_insight": 0.5,
            "qa_pair": 0.6,
            "tool_usage_pattern": 0.65,
            "error_resolution": 0.8
        }
        
        base_score = type_scores.get(item["type"], 0.5)
        
        # 根据元数据中的置信度调整
        confidence = item.get("metadata", {}).get("confidence", 0.5)
        
        # 根据内容复杂度调整
        complexity_factor = self._calculate_complexity(item)
        
        # 最终分值
        final_score = base_score * 0.4 + confidence * 0.4 + complexity_factor * 0.2
        
        return final_score
    
    def _calculate_complexity(self, item: Dict[str, Any]) -> float:
        """计算知识项的复杂度"""
        # 简单启发式方法，根据内容长度和结构评估复杂度
        complexity = 0.5  # 默认中等复杂度
        
        # 转换为字符串计算内容长度
        content_str = json.dumps(item, ensure_ascii=False)
        
        # 根据长度调整
        if len(content_str) > 1000:
            complexity = 0.8  # 长内容视为复杂
        elif len(content_str) < 100:
            complexity = 0.3  # 短内容视为简单
            
        return complexity
    