import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO, Union

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.knowledge.document_manager import DocumentManager
from app.knowledge.semantic_search import SemanticSearchEngine, SearchResult
from app.knowledge.vector_db_connector import VectorDBConnector
from app.knowledge.knowledge_extractor import KnowledgeExtractor
from app.knowledge.knowledge_integrator import KnowledgeIntegrator
from app.knowledge.learning_trigger import LearningTrigger
from app.models.knowledge import Document, KnowledgeBase, DocumentChunk


class KnowledgeBaseService:
    """知识库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        file_store_path = os.path.join(settings.UPLOAD_DIR, "documents")
        self.vector_db = VectorDBConnector()
        self.document_manager = DocumentManager(self.vector_db, file_store_path)
        self.search_engine = SemanticSearchEngine(self.vector_db)
        self.knowledge_extractor = KnowledgeExtractor(self.vector_db)
        self.knowledge_integrator = KnowledgeIntegrator(self)
        self.learning_trigger = LearningTrigger(self.knowledge_extractor, self.knowledge_integrator)
    
    async def create_knowledge_base(
        self, 
        name: str, 
        description: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "text-embedding-3-small"
    ) -> KnowledgeBase:
        """创建新的知识库"""
        # 检查是否已存在同名知识库
        existing = await self.get_knowledge_base_by_name(name)
        if existing:
            raise ValueError(f"知识库 '{name}' 已存在")
            
        # 创建新的知识库
        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.now(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model
        )
        
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        
        return kb
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """根据ID获取知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalars().first()
    
    async def get_knowledge_base_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """根据名称获取知识库"""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )
        return result.scalars().first()
    
    async def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """列出所有知识库"""
        result = await self.db.execute(select(KnowledgeBase))
        return result.scalars().all()
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        # 获取知识库
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            return False
            
        # 删除向量数据库集合
        await self.vector_db.delete_by_kb_id(kb_id)
        
        # 删除所有相关文档
        documents = await self.list_documents(kb_id)
        for document in documents:
            await self.document_manager.delete_document(self.db, document.id)
            
        # 删除知识库记录
        await self.db.delete(kb)
        await self.db.commit()
        
        return True
    
    async def upload_document(
        self, 
        kb_id: str, 
        file: Union[UploadFile, BinaryIO], 
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Document:
        """上传文档到知识库"""
        # 获取知识库
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_id}")
            
        # 如果是FastAPI的UploadFile，提取文件名和文件对象
        if isinstance(file, UploadFile):
            filename = filename or file.filename
            file_obj = file.file
        else:
            if not filename:
                raise ValueError("必须提供文件名")
            file_obj = file
            
        # 调用文档管理器上传文档
        document = await self.document_manager.upload_document(
            self.db, 
            kb_id, 
            file_obj, 
            filename,
            metadata
        )
        
        # 更新知识库文档计数
        kb.document_count += 1
        kb.last_updated = datetime.now()
        await self.db.commit()
        
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档信息"""
        return await self.document_manager.get_document_info(self.db, document_id)
    
    async def list_documents(self, kb_id: str) -> List[Document]:
        """列出知识库中的所有文档"""
        return await self.document_manager.list_documents(self.db, kb_id)
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        # 获取文档信息
        document = await self.get_document(document_id)
        if not document:
            return False
            
        # 删除文档
        result = await self.document_manager.delete_document(self.db, document_id)
        
        # 更新知识库文档计数
        if result:
            kb = await self.get_knowledge_base(document.kb_id)
            if kb:
                kb.document_count = max(0, kb.document_count - 1)
                kb.last_updated = datetime.now()
                await self.db.commit()
                
        return result
    
    async def semantic_search(
        self, 
        kb_id: str, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, str]] = None,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """语义搜索知识库"""
        # 执行搜索
        results = await self.search_engine.search(
            kb_id=kb_id,
            query=query,
            top_k=top_k,
            filters=filters,
            kb_service=self
        )
        
        # 应用相似度阈值
        if threshold > 0:
            results = [r for r in results if r.similarity >= threshold]
            
        return results
    
    async def add_chunk(self, chunk: DocumentChunk) -> None:
        """添加文档块到知识库"""
        # 保存到数据库
        self.db.add(chunk)
        await self.db.commit()
        
        # 添加到向量数据库
        await self.vector_db.add_chunk(chunk)
        
    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """更新文档块"""
        # 更新数据库记录
        await self.db.merge(chunk)
        await self.db.commit()
        
        # 更新向量数据库
        await self.vector_db.update_chunk(chunk)
        
    async def learn_from_event(self, event_type: str, event_data: Dict[str, Any], kb_id: str) -> bool:
        """从事件中学习知识"""
        return await self.learning_trigger.check_triggers(event_type, event_data, kb_id) 