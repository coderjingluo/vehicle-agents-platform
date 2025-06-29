import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.core.logging import logger
from app.knowledge.vector_db_connector import VectorDBConnector
from app.models.knowledge import DocumentChunk

class KnowledgeIntegrator:
    """知识整合器，将提取的知识整合到知识库中"""
    
    def __init__(self, kb_service, conflict_resolution_strategy: str = "confidence_based"):
        self.kb_service = kb_service
        self.conflict_strategy = conflict_resolution_strategy
        
    async def integrate_knowledge(self, kb_id: str, knowledge_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将知识项整合到指定的知识库中"""
        if not knowledge_items:
            return {"integrated": 0, "conflicts": 0, "errors": 0}
        
        stats = {"integrated": 0, "conflicts": 0, "errors": 0}
        
        for item in knowledge_items:
            try:
                # 1. 检查是否与现有知识冲突
                conflicts = await self._check_conflicts(kb_id, item)
                
                if conflicts:
                    # 2. 解决冲突
                    resolution = await self._resolve_conflicts(conflicts, item)
                    if resolution["action"] == "update":
                        await self._update_existing_knowledge(kb_id, resolution["target_id"], item)
                        stats["integrated"] += 1
                        stats["conflicts"] += 1
                    elif resolution["action"] == "ignore":
                        stats["conflicts"] += 1
                        continue
                else:
                    # 3. 添加新知识
                    await self._add_new_knowledge(kb_id, item)
                    stats["integrated"] += 1
            
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"知识整合错误: {str(e)}")
        
        return stats
    
    async def _check_conflicts(self, kb_id: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查知识项是否与现有知识冲突"""
        # 1. 提取关键内容
        key_content = self._extract_key_content(item)
        
        # 2. 语义搜索相似内容
        search_results = await self.kb_service.semantic_search(
            kb_id=kb_id,
            query=key_content,
            top_k=5,
            threshold=0.85  # 高相似度阈值
        )
        
        # 3. 分析冲突
        conflicts = []
        for result in search_results:
            conflict_type = self._analyze_conflict_type(item, result)
            if conflict_type:
                conflicts.append({
                    "existing_item": result,
                    "conflict_type": conflict_type,
                    "similarity": result.similarity
                })
        
        return conflicts
    
    def _extract_key_content(self, item: Dict[str, Any]) -> str:
        """提取知识项的关键内容用于相似度搜索"""
        if item["type"] == "task_pattern":
            return f"{item['goal']} {item['result']}"
        elif item["type"] == "intermediate_insight":
            return item["insight"]
        elif item["type"] == "qa_pair":
            return f"{item['question']} {item['answer']}"
        elif item["type"] == "tool_usage_pattern":
            return f"{item['tool_name']} {json.dumps(item['parameters'])} {item['result']}"
        elif item["type"] == "error_resolution":
            return f"{item['error_type']} {item['error_message']} {item['resolution']}"
        # 其他类型的处理...
        return json.dumps(item)
    
    def _analyze_conflict_type(self, new_item: Dict[str, Any], existing_item: Dict[str, Any]) -> Optional[str]:
        """分析冲突类型"""
        # 从文本内容中尝试解析现有项的类型和内容
        try:
            existing_text = existing_item.text
            if "type" in existing_text:
                # 可能是相同类型的知识项
                if new_item["type"] in existing_text:
                    return "duplicate"
            
            # 如果类型不同但内容高度相似
            if new_item["type"] == "task_pattern" and ("goal" in existing_text or "result" in existing_text):
                return "overlapping"
            elif new_item["type"] == "qa_pair" and ("question" in existing_text or "answer" in existing_text):
                return "overlapping"
            elif new_item["type"] == "error_resolution" and ("error" in existing_text or "resolution" in existing_text):
                return "overlapping"
        except:
            # 解析失败，保守地返回None
            pass
            
        return None
    
    async def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], new_item: Dict[str, Any]) -> Dict[str, Any]:
        """解决知识冲突"""
        if self.conflict_strategy == "confidence_based":
            # 基于置信度的冲突解决
            highest_confidence_conflict = max(conflicts, key=lambda c: c["existing_item"].metadata.get("confidence", 0))
            existing_confidence = highest_confidence_conflict["existing_item"].metadata.get("confidence", 0)
            new_confidence = new_item.get("metadata", {}).get("confidence", 0)
            
            if new_confidence > existing_confidence:
                return {
                    "action": "update",
                    "target_id": highest_confidence_conflict["existing_item"].id
                }
            else:
                return {"action": "ignore"}
                
        elif self.conflict_strategy == "recency_based":
            # 基于时间的冲突解决，总是使用最新的
            return {
                "action": "update",
                "target_id": conflicts[0]["existing_item"].id
            }
            
        elif self.conflict_strategy == "merge":
            # 合并冲突的知识
            # 实现合并逻辑
            # 这里简化处理，相当于replace
            return {
                "action": "update",
                "target_id": conflicts[0]["existing_item"].id
            }
            
        return {"action": "ignore"}
    
    async def _add_new_knowledge(self, kb_id: str, item: Dict[str, Any]) -> None:
        """添加新知识到知识库"""
        # 1. 格式化为文档块
        chunk = self._format_as_document_chunk(kb_id, item)
        
        # 2. 添加到向量数据库
        await self.kb_service.add_chunk(chunk)
    
    async def _update_existing_knowledge(self, kb_id: str, chunk_id: str, new_item: Dict[str, Any]) -> None:
        """更新现有知识"""
        # 1. 格式化为文档块
        updated_chunk = self._format_as_document_chunk(kb_id, new_item, chunk_id)
        
        # 2. 更新向量数据库中的条目
        await self.kb_service.update_chunk(updated_chunk)
        
    def _format_as_document_chunk(self, kb_id: str, item: Dict[str, Any], chunk_id: str = None) -> DocumentChunk:
        """将知识项格式化为文档块"""
        # 生成内容
        content = self._generate_chunk_content(item)
        
        # 创建文档块
        chunk = DocumentChunk(
            id=chunk_id or str(uuid.uuid4()),
            document_id=f"auto_generated_{uuid.uuid4().hex[:8]}",
            kb_id=kb_id,
            content=content,
            chunk_index=0,
            metadata={
                "source_type": "auto_extracted",
                "knowledge_type": item["type"],
                "extraction_time": datetime.now().isoformat(),
                "confidence": item.get("metadata", {}).get("confidence", 0.7),
                **item.get("metadata", {})
            }
        )
        
        return chunk
    
    def _generate_chunk_content(self, item: Dict[str, Any]) -> str:
        """根据知识项类型生成结构化内容"""
        if item["type"] == "task_pattern":
            return f"""目标: {item['goal']}
成功方法: {json.dumps(item['successful_approach'], ensure_ascii=False)}
结果: {item['result']}"""
            
        elif item["type"] == "intermediate_insight":
            return f"""步骤: {item['step']}
见解: {item['insight']}"""
            
        elif item["type"] == "qa_pair":
            return f"""问题: {item['question']}
回答: {item['answer']}"""
            
        elif item["type"] == "tool_usage_pattern":
            return f"""工具: {item['tool_name']}
参数: {json.dumps(item['parameters'], ensure_ascii=False)}
结果: {item['result']}"""
            
        elif item["type"] == "error_resolution":
            return f"""错误类型: {item['error_type']}
错误信息: {item['error_message']}
解决方案: {item['resolution']}
上下文: {json.dumps(item['context'], ensure_ascii=False)}"""
            
        # 其他类型的处理...
        return json.dumps(item, ensure_ascii=False)