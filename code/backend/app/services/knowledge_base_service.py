"""
知识库管理服务

负责知识库的创建、管理、文档处理和语义搜索功能
"""

import os
import hashlib
import aiofiles
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import (
    KnowledgeBase,
    Document,
    KnowledgeBaseStatus,
    DocumentType,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    DocumentUpload,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentSearchResponse,
    KnowledgeBaseStats
)
from app.core.database import get_db_session
from app.services.document_processor import DocumentProcessor
from app.services.vector_service import VectorService
from app.core.config import get_settings
from loguru import logger


class KnowledgeBaseService:
    """知识库管理服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.document_processor = DocumentProcessor()
        self.vector_service = VectorService()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def create_knowledge_base(
        self,
        kb_data: KnowledgeBaseCreate,
        db: AsyncSession
    ) -> KnowledgeBase:
        """创建新的知识库"""
        try:
            # 检查名称是否已存在
            existing_kb = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.name == kb_data.name)
            )
            if existing_kb.scalar_one_or_none():
                raise ValueError(f"知识库名称 '{kb_data.name}' 已存在")
            
            # 创建知识库
            kb = KnowledgeBase(
                name=kb_data.name,
                description=kb_data.description,
                embedding_model=kb_data.embedding_model,
                chunk_size=kb_data.chunk_size,
                chunk_overlap=kb_data.chunk_overlap,
                config=kb_data.config,
                status=KnowledgeBaseStatus.ACTIVE.value
            )
            
            db.add(kb)
            await db.commit()
            await db.refresh(kb)
            
            # 在向量数据库中创建集合
            await self.vector_service.create_collection(
                collection_name=kb.id,
                embedding_model=kb.embedding_model
            )
            
            logger.info(f"成功创建知识库: {kb.name} (ID: {kb.id})")
            return kb
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建知识库失败: {e}")
            raise
    
    async def get_knowledge_base(
        self,
        kb_id: str,
        db: AsyncSession,
        include_documents: bool = False
    ) -> Optional[KnowledgeBase]:
        """获取知识库信息"""
        try:
            query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            
            if include_documents:
                query = query.options(selectinload(KnowledgeBase.documents))
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取知识库失败: {e}")
            raise
    
    async def list_knowledge_bases(
        self,
        db: AsyncSession,
        status: Optional[KnowledgeBaseStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[KnowledgeBase], int]:
        """获取知识库列表"""
        try:
            # 构建查询条件
            conditions = []
            if status:
                conditions.append(KnowledgeBase.status == status.value)
            
            # 获取总数
            count_query = select(func.count(KnowledgeBase.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 获取列表
            list_query = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
            if conditions:
                list_query = list_query.where(and_(*conditions))
            
            list_query = list_query.offset(offset).limit(limit)
            
            result = await db.execute(list_query)
            knowledge_bases = result.scalars().all()
            
            return knowledge_bases, total
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            raise
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        kb_data: KnowledgeBaseUpdate,
        db: AsyncSession
    ) -> Optional[KnowledgeBase]:
        """更新知识库"""
        try:
            kb = await self.get_knowledge_base(kb_id, db)
            if not kb:
                return None
            
            # 更新字段
            update_data = kb_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(kb, field, value)
            
            kb.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(kb)
            
            logger.info(f"成功更新知识库: {kb.name}")
            return kb
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新知识库失败: {e}")
            raise
    
    async def delete_knowledge_base(
        self,
        kb_id: str,
        db: AsyncSession
    ) -> bool:
        """删除知识库"""
        try:
            kb = await self.get_knowledge_base(kb_id, db, include_documents=True)
            if not kb:
                return False
            
            # 删除向量数据库中的集合
            await self.vector_service.delete_collection(kb.id)
            
            # 删除文档文件
            for doc in kb.documents:
                try:
                    file_path = Path(doc.file_path)
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    logger.warning(f"删除文档文件失败 {doc.file_path}: {e}")
            
            # 删除数据库记录
            await db.delete(kb)
            await db.commit()
            
            logger.info(f"成功删除知识库: {kb.name}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除知识库失败: {e}")
            raise
    
    async def upload_document(
        self,
        kb_id: str,
        file_content: bytes,
        doc_info: DocumentUpload,
        db: AsyncSession
    ) -> Document:
        """上传文档到知识库"""
        try:
            # 检查知识库是否存在
            kb = await self.get_knowledge_base(kb_id, db)
            if not kb:
                raise ValueError(f"知识库不存在: {kb_id}")
            
            if kb.status != KnowledgeBaseStatus.ACTIVE.value:
                raise ValueError(f"知识库状态不可用: {kb.status}")
            
            # 计算文件哈希
            content_hash = hashlib.sha256(file_content).hexdigest()
            
            # 检查是否已存在相同文件
            existing_doc = await db.execute(
                select(Document).where(
                    and_(
                        Document.knowledge_base_id == kb_id,
                        Document.content_hash == content_hash
                    )
                )
            )
            if existing_doc.scalar_one_or_none():
                raise ValueError("文档已存在（文件内容相同）")
            
            # 保存文件
            file_extension = doc_info.file_type.value
            file_name = f"{content_hash}.{file_extension}"
            file_path = self.upload_dir / kb_id / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # 创建文档记录
            document = Document(
                knowledge_base_id=kb_id,
                name=doc_info.name,
                file_path=str(file_path),
                file_size=len(file_content),
                file_type=doc_info.file_type.value,
                content_hash=content_hash,
                metadata=doc_info.metadata,
                processing_status="pending"
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # 异步处理文档（提取文本、向量化）
            await self._process_document_async(document, kb, db)
            
            logger.info(f"成功上传文档: {document.name} 到知识库 {kb.name}")
            return document
            
        except Exception as e:
            await db.rollback()
            logger.error(f"上传文档失败: {e}")
            raise
    
    async def _process_document_async(
        self,
        document: Document,
        knowledge_base: KnowledgeBase,
        db: AsyncSession
    ):
        """异步处理文档（提取文本和向量化）"""
        try:
            # 更新处理状态
            document.processing_status = "processing"
            await db.commit()
            
            # 提取文本内容
            content = await self.document_processor.extract_text(
                document.file_path,
                DocumentType(document.file_type)
            )
            
            if not content.strip():
                raise ValueError("无法提取文档内容或内容为空")
            
            # 文档分块
            chunks = await self.document_processor.chunk_text(
                content,
                chunk_size=knowledge_base.chunk_size,
                chunk_overlap=knowledge_base.chunk_overlap
            )
            
            # 向量化并存储
            vector_ids = await self.vector_service.add_documents(
                collection_name=knowledge_base.id,
                documents=chunks,
                metadata={
                    "document_id": document.id,
                    "document_name": document.name,
                    "knowledge_base_id": knowledge_base.id,
                    **document.metadata
                }
            )
            
            # 计算token数量（估算）
            token_count = len(content.split()) * 1.3  # 粗略估算
            
            # 更新文档信息
            document.content = content
            document.is_vectorized = True
            document.vector_ids = vector_ids
            document.chunk_count = len(chunks)
            document.token_count = int(token_count)
            document.processing_status = "completed"
            document.processing_error = None
            
            # 更新知识库统计
            knowledge_base.document_count += 1
            knowledge_base.total_chunks += len(chunks)
            knowledge_base.total_tokens += int(token_count)
            knowledge_base.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"文档处理完成: {document.name}, 生成 {len(chunks)} 个块")
            
        except Exception as e:
            # 更新错误状态
            document.processing_status = "error"
            document.processing_error = str(e)
            await db.commit()
            
            logger.error(f"文档处理失败 {document.name}: {e}")
            raise
    
    async def search_documents(
        self,
        search_request: DocumentSearchRequest,
        db: AsyncSession
    ) -> DocumentSearchResponse:
        """搜索文档"""
        start_time = datetime.utcnow()
        
        try:
            # 确定搜索范围
            collection_names = []
            kb_info = {}
            
            if search_request.knowledge_base_id:
                # 搜索指定知识库
                kb = await self.get_knowledge_base(search_request.knowledge_base_id, db)
                if not kb:
                    raise ValueError(f"知识库不存在: {search_request.knowledge_base_id}")
                collection_names.append(kb.id)
                kb_info[kb.id] = {"name": kb.name}
            else:
                # 搜索所有知识库
                kbs, _ = await self.list_knowledge_bases(
                    db, status=KnowledgeBaseStatus.ACTIVE
                )
                collection_names = [kb.id for kb in kbs]
                kb_info = {kb.id: {"name": kb.name} for kb in kbs}
            
            if not collection_names:
                return DocumentSearchResponse(
                    query=search_request.query,
                    total_results=0,
                    results=[],
                    execution_time=0.0
                )
            
            # 向量搜索
            search_results = await self.vector_service.search_documents(
                collection_names=collection_names,
                query=search_request.query,
                limit=search_request.limit,
                similarity_threshold=search_request.similarity_threshold
            )
            
            # 获取文档信息并构建结果
            document_ids = [result["metadata"]["document_id"] for result in search_results]
            documents_query = select(Document).where(Document.id.in_(document_ids))
            doc_result = await db.execute(documents_query)
            documents = {doc.id: doc for doc in doc_result.scalars().all()}
            
            # 构建搜索结果
            results = []
            for result in search_results:
                doc_id = result["metadata"]["document_id"]
                document = documents.get(doc_id)
                
                if document:
                    search_result = DocumentSearchResult(
                        document_id=doc_id,
                        document_name=document.name,
                        knowledge_base_id=document.knowledge_base_id,
                        knowledge_base_name=kb_info.get(document.knowledge_base_id, {}).get("name", ""),
                        content=result["content"],
                        similarity_score=result["similarity_score"],
                        metadata=result["metadata"] if search_request.include_metadata else {},
                        chunk_index=result.get("chunk_index", 0)
                    )
                    results.append(search_result)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return DocumentSearchResponse(
                query=search_request.query,
                total_results=len(results),
                results=results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            raise
    
    async def get_knowledge_base_stats(self, db: AsyncSession) -> KnowledgeBaseStats:
        """获取知识库统计信息"""
        try:
            # 基础统计
            total_kb_result = await db.execute(select(func.count(KnowledgeBase.id)))
            total_kb = total_kb_result.scalar() or 0
            
            total_doc_result = await db.execute(select(func.count(Document.id)))
            total_doc = total_doc_result.scalar() or 0
            
            chunks_sum_result = await db.execute(select(func.sum(KnowledgeBase.total_chunks)))
            total_chunks = chunks_sum_result.scalar() or 0
            
            tokens_sum_result = await db.execute(select(func.sum(KnowledgeBase.total_tokens)))
            total_tokens = tokens_sum_result.scalar() or 0
            
            # 计算存储大小
            size_sum_result = await db.execute(select(func.sum(Document.file_size)))
            storage_size = size_sum_result.scalar() or 0
            
            # 按状态统计
            status_query = select(
                KnowledgeBase.status,
                func.count(KnowledgeBase.id)
            ).group_by(KnowledgeBase.status)
            status_result = await db.execute(status_query)
            by_status = {row[0]: row[1] for row in status_result.all()}
            
            # 按文档类型统计
            type_query = select(
                Document.file_type,
                func.count(Document.id)
            ).group_by(Document.file_type)
            type_result = await db.execute(type_query)
            by_type = {row[0]: row[1] for row in type_result.all()}
            
            # 最近活动（最近7天的文档上传）
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_query = select(
                func.date(Document.created_at).label('date'),
                func.count(Document.id).label('count')
            ).where(
                Document.created_at >= week_ago
            ).group_by(
                func.date(Document.created_at)
            ).order_by(func.date(Document.created_at))
            
            recent_result = await db.execute(recent_query)
            recent_activity = [
                {"date": str(row[0]), "count": row[1]}
                for row in recent_result.all()
            ]
            
            return KnowledgeBaseStats(
                total_knowledge_bases=total_kb,
                total_documents=total_doc,
                total_chunks=total_chunks,
                total_tokens=total_tokens,
                storage_size=storage_size,
                by_status=by_status,
                by_type=by_type,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
    
    async def delete_document(
        self,
        doc_id: str,
        db: AsyncSession
    ) -> bool:
        """删除文档"""
        try:
            document = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = document.scalar_one_or_none()
            
            if not doc:
                return False
            
            # 从向量数据库中删除
            if doc.is_vectorized and doc.vector_ids:
                await self.vector_service.delete_documents(
                    collection_name=doc.knowledge_base_id,
                    document_ids=doc.vector_ids
                )
            
            # 删除文件
            try:
                file_path = Path(doc.file_path)
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"删除文档文件失败 {doc.file_path}: {e}")
            
            # 更新知识库统计
            kb = await self.get_knowledge_base(doc.knowledge_base_id, db)
            if kb:
                kb.document_count = max(0, kb.document_count - 1)
                kb.total_chunks = max(0, kb.total_chunks - doc.chunk_count)
                kb.total_tokens = max(0, kb.total_tokens - doc.token_count)
                kb.updated_at = datetime.utcnow()
            
            # 删除数据库记录
            await db.delete(doc)
            await db.commit()
            
            logger.info(f"成功删除文档: {doc.name}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除文档失败: {e}")
            raise 