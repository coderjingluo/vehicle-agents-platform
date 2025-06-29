from typing import Dict, List, Optional, Any, Union

from app.core.config import settings
from app.core.logging import logger
from app.knowledge.vector_db_connector import VectorDBConnector
from app.models.knowledge import KnowledgeBase


class SearchError(Exception):
    """搜索错误"""
    pass


class SearchResult:
    """搜索结果实体模型"""
    
    def __init__(
        self,
        id: str,
        text: str,
        document_id: str,
        similarity: float,
        metadata: Dict[str, Any] = None
    ):
        self.id = id
        self.text = text
        self.document_id = document_id
        self.similarity = similarity
        self.metadata = metadata or {}


class SemanticSearchEngine:
    """语义搜索引擎"""
    
    def __init__(self, vector_db_connector: VectorDBConnector):
        self.vector_db_connector = vector_db_connector
    
    async def search(self, kb_id: str, query: str, top_k: int = 5,
                   filters: Optional[Dict[str, str]] = None,
                   kb_service=None) -> List[SearchResult]:
        """语义搜索知识库"""
        try:
            # 1. 验证知识库ID
            # 如果传入了kb_service则使用它来获取知识库信息
            if kb_service:
                kb = await kb_service.get_knowledge_base(kb_id)
                if not kb:
                    raise ValueError(f"Knowledge base not found: {kb_id}")
            
            # 2. 执行文本查询
            # 这里不需要单独生成嵌入，因为vector_db_connector已经实现了这一功能
            search_results = await self.vector_db_connector.similarity_search(
                kb_id=kb_id,
                query_text=query,
                top_k=top_k,
                filters=filters
            )
            
            # 3. 格式化结果
            formatted_results = []
            for result in search_results:
                formatted_results.append(
                    SearchResult(
                        id=result["id"],
                        text=result["text"],
                        document_id=result["metadata"].get("document_id", ""),
                        similarity=result["score"],
                        metadata=result["metadata"]
                    )
                )
            
            return formatted_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise SearchError(f"Failed to perform semantic search: {e}")


class CrossEncoderReranker:
    """交叉编码器重排器"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """懒加载交叉编码器模型"""
        if self._model is None:
            try:
                from sentence_transformers.cross_encoder import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except ImportError:
                logger.warning("sentence-transformers未安装，无法使用交叉编码器")
                return None
        return self._model
    
    def rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """对搜索结果进行重排序"""
        if not results:
            return []
            
        if not self.model:
            logger.warning("交叉编码器不可用，跳过重排序")
            return results
        
        # 准备文本对
        pairs = [(query, result.text) for result in results]
        
        # 计算相似度得分
        scores = self.model.predict(pairs)
        
        # 更新相似度分数
        for i, result in enumerate(results):
            result.similarity = float(scores[i])
        
        # 根据新的相似度分数排序
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results
