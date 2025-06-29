import os
import uuid
from typing import Dict, List, Optional, Any, Union

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.models.knowledge import DocumentChunk


class VectorDBConnector:
    """向量数据库连接器，负责与Chroma/Qdrant进行交互"""
    
    def __init__(self, persist_directory: str = None, embedding_function_name: str = None):
        """初始化向量数据库连接器"""
        self.persist_directory = persist_directory or os.path.join(settings.UPLOAD_DIR, "vectordb")
        self.embedding_function_name = embedding_function_name or "openai"
        self._client = None
        self._embedding_function = None
        
    @property
    def client(self):
        """获取ChromaDB客户端连接"""
        if self._client is None:
            # 确保存储目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 创建ChromaDB客户端
            self._client = chromadb.Client(
                Settings(
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                )
            )
            
        return self._client
    
    @property
    def embedding_function(self):
        """获取嵌入函数"""
        if self._embedding_function is None:
            if self.embedding_function_name == "openai":
                # 使用OpenAI嵌入函数
                openai_api_key = settings.get("OPENAI_API_KEY", "")
                self._embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=openai_api_key,
                    model_name="text-embedding-3-small"
                )
            else:
                # 默认使用本地嵌入函数
                self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        return self._embedding_function
    
    def _get_collection(self, kb_id: str):
        """获取或创建知识库对应的集合"""
        return self.client.get_or_create_collection(
            name=f"kb_{kb_id}",
            embedding_function=self.embedding_function
        )
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """批量添加文档块到向量数据库"""
        if not chunks:
            return
            
        # 按知识库ID分组
        kb_chunks = {}
        for chunk in chunks:
            if chunk.kb_id not in kb_chunks:
                kb_chunks[chunk.kb_id] = []
            kb_chunks[chunk.kb_id].append(chunk)
        
        # 对每个知识库分别添加
        for kb_id, kb_chunk_list in kb_chunks.items():
            collection = self._get_collection(kb_id)
            
            ids = [chunk.id for chunk in kb_chunk_list]
            documents = [chunk.content for chunk in kb_chunk_list]
            metadatas = [
                {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
                for chunk in kb_chunk_list
            ]
            
            # 添加到集合
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
        logger.info(f"Added {len(chunks)} chunks to vector database")
    
    async def add_chunk(self, chunk: DocumentChunk) -> None:
        """添加单个文档块到向量数据库"""
        await self.add_chunks([chunk])
    
    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """更新向量数据库中的文档块"""
        collection = self._get_collection(chunk.kb_id)
        
        # 使用upsert方法更新文档
        collection.upsert(
            ids=[chunk.id],
            documents=[chunk.content],
            metadatas=[{
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }]
        )
        
        logger.info(f"Updated chunk {chunk.id} in vector database")
    
    async def delete_by_document_id(self, document_id: str) -> None:
        """删除指定文档的所有块"""
        # 首先需要知道文档属于哪个知识库
        # 这里假设有获取文档信息的方法
        # 实际实现可能需要从数据库中查询
        
        # 这里假设我们知道kb_id
        # TODO: 实际实现中通过查询获取kb_id
        kb_id = "unknown"
        
        collection = self._get_collection(kb_id)
        collection.delete(
            where={"document_id": document_id}
        )
        
        logger.info(f"Deleted all chunks for document {document_id}")
    
    async def delete_by_kb_id(self, kb_id: str) -> None:
        """删除整个知识库的向量数据"""
        try:
            self.client.delete_collection(f"kb_{kb_id}")
            logger.info(f"Deleted collection for knowledge base {kb_id}")
        except Exception as e:
            logger.error(f"Failed to delete collection for kb {kb_id}: {e}")
    
    async def similarity_search(
        self, 
        kb_id: str, 
        query_text: str = None,
        query_vector: List[float] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """执行相似度搜索"""
        collection = self._get_collection(kb_id)
        
        # 构建过滤条件
        where_clause = {}
        if filters:
            where_clause.update(filters)
            
        # 执行查询
        if query_text is not None:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
        elif query_vector is not None:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
        else:
            raise ValueError("必须提供query_text或query_vector之一")
            
        # 格式化结果
        formatted_results = []
        
        # 检查结果是否为空
        if not results["ids"] or len(results["ids"][0]) == 0:
            return []
            
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i] if "distances" in results else 0.0
            })
            
        return formatted_results 