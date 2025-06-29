import os
import uuid
import aiofiles
from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import logger
from app.db.session import get_db
from app.knowledge.vector_db_connector import VectorDBConnector
from app.models.knowledge import Document, DocumentChunk, DocumentStatus, DocumentFormat, KnowledgeBase


class DocumentUploadError(Exception):
    """文档上传错误"""
    pass


class UnsupportedFormatError(Exception):
    """不支持的文件格式错误"""
    pass


class DocumentDeletionError(Exception):
    """文档删除错误"""
    pass


class TextSplitterFactory:
    """文本分割器工厂"""
    
    @staticmethod
    def get_splitter(document_format: DocumentFormat, chunk_size: int, chunk_overlap: int):
        """根据文档格式获取适当的文本分割器"""
        from langchain.text_splitter import (
            RecursiveCharacterTextSplitter,
            MarkdownTextSplitter,
            PythonCodeTextSplitter,
        )
        
        # 默认文本分割器映射
        splitter_map = {
            DocumentFormat.TXT: RecursiveCharacterTextSplitter,
            DocumentFormat.MD: MarkdownTextSplitter,
            DocumentFormat.PDF: RecursiveCharacterTextSplitter,
            DocumentFormat.DOCX: RecursiveCharacterTextSplitter,
            DocumentFormat.DOC: RecursiveCharacterTextSplitter,
            DocumentFormat.PY: PythonCodeTextSplitter,
        }
        
        # 对于未明确定义的格式，使用RecursiveCharacterTextSplitter
        splitter_cls = splitter_map.get(document_format, RecursiveCharacterTextSplitter)
        
        return splitter_cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )


class DocumentManager:
    """文档管理器"""
    
    def __init__(self, vector_db_connector: VectorDBConnector, file_store_path: str):
        self.vector_db_connector = vector_db_connector
        self.file_store_path = file_store_path
    
    async def upload_document(self, db: AsyncSession, kb_id: str, file: BinaryIO, filename: str,
                             metadata: Optional[Dict[str, str]] = None) -> Document:
        """上传文档到知识库"""
        try:
            # 1. 保存文件
            document_id = str(uuid.uuid4())
            file_path = await self._save_file(file, document_id, filename)
            
            # 2. 确定文件格式和大小
            file_format = self._get_file_format(filename)
            file_size = os.path.getsize(file_path)
            
            # 3. 创建文档记录
            document = Document(
                id=document_id,
                kb_id=kb_id,
                filename=filename,
                file_format=file_format.value,
                file_size=file_size,
                content_type=self._get_content_type(file_format),
                uploaded_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # 4. 保存文档记录到数据库
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # 5. 触发异步处理任务
            # 注意：实际环境中应该使用Celery或其他异步任务队列
            # 这里为了简化，直接调用处理方法
            await self._process_document_async(db, document)
            
            return document
        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            raise DocumentUploadError(f"Failed to upload document: {str(e)}")
    
    async def _save_file(self, file: BinaryIO, document_id: str, filename: str) -> str:
        """保存上传的文件"""
        # 确保目录存在
        doc_dir = os.path.join(self.file_store_path, document_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        # 保存文件路径
        file_path = os.path.join(doc_dir, filename)
        
        # 保存文件
        contents = file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)
            
        return file_path
    
    def _get_file_format(self, filename: str) -> DocumentFormat:
        """从文件名确定文件格式"""
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        
        # 尝试将扩展名映射到枚举
        try:
            return DocumentFormat(ext)
        except ValueError:
            # 不支持的文件格式，默认为TXT
            logger.warning(f"Unsupported file format: {ext}, treating as TXT")
            return DocumentFormat.TXT
    
    def _get_content_type(self, file_format: DocumentFormat) -> str:
        """获取文件内容类型"""
        content_type_map = {
            DocumentFormat.TXT: "text/plain",
            DocumentFormat.MD: "text/markdown",
            DocumentFormat.PDF: "application/pdf",
            DocumentFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            DocumentFormat.DOC: "application/msword",
            DocumentFormat.PY: "text/x-python",
            DocumentFormat.JS: "application/javascript",
            DocumentFormat.HTML: "text/html",
            DocumentFormat.CSS: "text/css",
            DocumentFormat.JAVA: "text/x-java",
            DocumentFormat.CPP: "text/x-c++",
            DocumentFormat.C: "text/x-c",
        }
        
        return content_type_map.get(file_format, "text/plain")
    
    async def _process_document_async(self, db: AsyncSession, document: Document) -> None:
        """异步处理文档（分块和向量化）"""
        try:
            # 更新状态为处理中
            document.status = DocumentStatus.PROCESSING.value
            await db.commit()
            
            # 1. 读取文档内容
            content = await self._read_document_content(document)
            
            # 2. 获取知识库配置
            kb = await self._get_knowledge_base(db, document.kb_id)
            
            # 3. 分块处理
            chunks = await self._split_document(content, document, kb.chunk_size, kb.chunk_overlap)
            
            # 4. 向量化和存储
            await self._vectorize_and_store(chunks, kb.embedding_model)
            
            # 5. 更新文档状态
            document.status = DocumentStatus.COMPLETED.value
            document.chunk_count = len(chunks)
            document.last_updated = datetime.now()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {str(e)}")
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(e)
            await db.commit()
    
    async def _get_knowledge_base(self, db: AsyncSession, kb_id: str) -> KnowledgeBase:
        """获取知识库信息"""
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalars().first()
        
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")
            
        return kb
    
    async def _read_document_content(self, document: Document) -> str:
        """根据文档格式读取内容"""
        file_path = self._get_document_path(document.id, document.filename)
        
        # 获取文档格式
        file_format = DocumentFormat(document.file_format)
        
        if file_format in [DocumentFormat.TXT, DocumentFormat.MD, 
                          DocumentFormat.PY, DocumentFormat.JS,
                          DocumentFormat.HTML, DocumentFormat.CSS,
                          DocumentFormat.JAVA, DocumentFormat.CPP,
                          DocumentFormat.C]:
            # 直接读取文本文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
                
        elif file_format == DocumentFormat.PDF:
            # 使用PyPDF2读取PDF
            return await self._read_pdf(file_path)
            
        elif file_format in [DocumentFormat.DOCX, DocumentFormat.DOC]:
            # 使用python-docx读取Word文档
            return await self._read_docx(file_path)
            
        else:
            raise UnsupportedFormatError(f"Unsupported file format: {file_format}")
    
    def _get_document_path(self, document_id: str, filename: str) -> str:
        """获取文档文件路径"""
        return os.path.join(self.file_store_path, document_id, filename)
    
    async def _read_pdf(self, file_path: str) -> str:
        """读取PDF文件内容"""
        try:
            import PyPDF2
            
            text_content = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text_content += reader.pages[page_num].extract_text()
                    
            return text_content
        except ImportError:
            logger.error("PyPDF2 not installed. Cannot process PDF files.")
            raise UnsupportedFormatError("PDF processing requires PyPDF2")
    
    async def _read_docx(self, file_path: str) -> str:
        """读取Word文档内容"""
        try:
            import docx
            
            doc = docx.Document(file_path)
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            return text_content
        except ImportError:
            logger.error("python-docx not installed. Cannot process DOCX files.")
            raise UnsupportedFormatError("DOCX processing requires python-docx")
    
    async def _split_document(self, content: str, document: Document, 
                            chunk_size: int, chunk_overlap: int) -> List[DocumentChunk]:
        """将文档内容分块"""
        # 使用文本分割器进行分块
        file_format = DocumentFormat(document.file_format)
        text_splitter = TextSplitterFactory.get_splitter(file_format, chunk_size, chunk_overlap)
        texts = text_splitter.split_text(content)
        
        chunks = []
        for i, text in enumerate(texts):
            chunk = DocumentChunk(
                id=f"{document.id}_chunk_{i}",
                document_id=document.id,
                kb_id=document.kb_id,
                content=text,
                chunk_index=i,
                metadata={
                    "filename": document.filename,
                    "format": document.file_format,
                    "chunk": f"{i+1}/{len(texts)}"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _vectorize_and_store(self, chunks: List[DocumentChunk], embedding_model: str) -> None:
        """向量化分块内容并存储"""
        # 存储到向量数据库
        await self.vector_db_connector.add_chunks(chunks)
    
    async def delete_document(self, db: AsyncSession, document_id: str) -> bool:
        """从知识库中删除文档"""
        try:
            # 1. 获取文档记录
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalars().first()
            
            if not document:
                return False
            
            # 2. 删除向量数据库中的分块
            await self.vector_db_connector.delete_by_document_id(document_id)
            
            # 3. 删除文件系统中的文档
            file_path = self._get_document_path(document.id, document.filename)
            doc_dir = os.path.dirname(file_path)
            
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # 删除文档目录
            if os.path.exists(doc_dir):
                import shutil
                shutil.rmtree(doc_dir)
            
            # 4. 删除文档记录
            await db.delete(document)
            await db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise DocumentDeletionError(f"Failed to delete document: {str(e)}")
    
    async def get_document_info(self, db: AsyncSession, document_id: str) -> Optional[Document]:
        """获取文档信息"""
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalars().first()
    
    async def list_documents(self, db: AsyncSession, kb_id: str) -> List[Document]:
        """列出知识库中的所有文档"""
        result = await db.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        return result.scalars().all() 