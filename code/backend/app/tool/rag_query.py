from typing import Dict, List, Optional, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.knowledge.vector_db_connector import VectorDBConnector
from app.knowledge.semantic_search import SemanticSearchEngine, CrossEncoderReranker
from app.tool.base import BaseTool, ToolResult


class RAGQueryTool(BaseTool):
    """RAG查询工具"""
    
    name: str = "rag_query"
    description: str = "在知识库中进行语义搜索并检索相关信息"
    parameters: dict = {
        "type": "object",
        "properties": {
            "kb_name": {
                "type": "string",
                "description": "知识库名称"
            },
            "query": {
                "type": "string",
                "description": "查询文本"
            },
            "top_k": {
                "type": "integer",
                "description": "返回的最大结果数量",
                "default": 5
            },
            "filters": {
                "type": "object",
                "description": "过滤条件，如文档类型、创建日期等",
                "default": {}
            },
            "rerank": {
                "type": "boolean",
                "description": "是否对结果进行重排序",
                "default": False
            }
        },
        "required": ["kb_name", "query"]
    }
    
    async def execute(self, kb_name: Optional[str] = None, query: Optional[str] = None, 
                     query_text: Optional[str] = None, top_k: int = 5, 
                     filters: Optional[Dict[str, str]] = None,
                     rerank: bool = False, **kwargs) -> ToolResult:
        """执行RAG查询
        
        Args:
            kb_name: 知识库名称，如果未提供则使用默认知识库
            query: 查询文本
            query_text: 查询文本的别名，用于兼容性
            top_k: 返回的最大结果数量
            filters: 过滤条件
            rerank: 是否重排序结果
            
        Returns:
            ToolResult: 查询结果
        """
        # 参数处理和兼容性
        actual_query = query or query_text or kwargs.get('text') or ""
        actual_kb_name = kb_name or settings.DEFAULT_KB_NAME
        
        if not actual_query:
            return ToolResult(error="未提供查询文本")
        
        # 调用实际的执行方法
        return await self._execute(
            kb_name=actual_kb_name,
            query=actual_query,
            top_k=top_k,
            filters=filters,
            rerank=rerank,
            **kwargs
        )
    
    async def _execute(self, kb_name: str, query: str, top_k: int = 5, 
                     filters: Optional[Dict[str, str]] = None,
                     rerank: bool = False, **kwargs) -> ToolResult:
        """执行RAG查询"""
        try:
            # 获取数据库会话
            async with get_db() as db:
                # 获取知识库ID
                kb_service = await self._get_kb_service(db)
                kb = await kb_service.get_knowledge_base_by_name(kb_name)
                if not kb:
                    return ToolResult(error=f"知识库不存在: {kb_name}")
                
                # 创建向量数据库连接器
                vector_db = VectorDBConnector()
                
                # 创建搜索引擎
                search_engine = SemanticSearchEngine(vector_db)
                
                # 执行搜索
                search_results = await search_engine.search(
                    kb_id=kb.id,
                    query=query,
                    top_k=top_k,
                    filters=filters or {}
                )
                
                # 重排序（如果启用）
                if rerank and len(search_results) > 1:
                    reranker = CrossEncoderReranker()
                    search_results = reranker.rerank(query, search_results)
                
                # 格式化结果
                formatted_results = []
                for i, result in enumerate(search_results):
                    formatted_results.append({
                        "rank": i + 1,
                        "text": result.text,
                        "document": result.metadata.get("filename", ""),
                        "similarity": round(result.similarity, 3),
                        "metadata": {
                            k: v for k, v in result.metadata.items() 
                            if k not in ["filename", "document_id"]
                        }
                    })
                
                return ToolResult(output=formatted_results)
        except Exception as e:
            logger.error(f"RAG查询失败: {str(e)}")
            return ToolResult(error=f"RAG查询失败: {str(e)}")
    
    async def _get_kb_service(self, db: AsyncSession):
        """获取知识库服务"""
        # 这里需要导入KnowledgeBaseService
        # 为避免循环导入，放在方法内部导入
        from app.services.knowledge_service import KnowledgeBaseService
        return KnowledgeBaseService(db)
