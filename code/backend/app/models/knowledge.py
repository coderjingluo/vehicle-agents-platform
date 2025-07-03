"""
KunlunSec AI Platform - 知识库模型

定义知识库相关的数据库模型和方法。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, List, Dict, Union

from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, 
    ForeignKey, Integer, Enum, JSON, Float, Table
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base

class DocumentType(str, enum.Enum):
    """文档类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    HTML = "html"
    URL = "url"
    CODE = "code"
    CUSTOM = "custom"

class DocumentStatus(str, enum.Enum):
    """文档处理状态枚举"""
    PENDING = "pending"       # 等待处理
    PROCESSING = "processing" # 正在处理
    COMPLETED = "completed"   # 处理完成
    FAILED = "failed"         # 处理失败

class DocumentFormat(str, enum.Enum):
    """支持的文档格式枚举"""
    TXT = "txt"
    MD = "md"
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    PY = "py"
    JS = "js"
    HTML = "html"
    CSS = "css"
    JAVA = "java"
    CPP = "cpp"
    C = "c"

class KnowledgeDocument(Base):
    """知识文档模型"""
    
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 文档类型和内容
    document_type = Column(Enum(DocumentType), nullable=False)
    content = Column(Text, nullable=True)  # 原始内容或文件路径
    file_path = Column(String(255), nullable=True)  # 文件存储路径
    url = Column(String(512), nullable=True)  # 如果是URL类型
    
    # 文档元数据
    doc_metadata = Column(JSON, default={})
    tags = Column(ARRAY(String), default=[])
    
    # 向量数据库ID
    vector_id = Column(String(255), nullable=True)  # Chroma中的ID
    
    # 文档状态
    is_indexed = Column(Boolean, default=False)  # 是否已被索引
    is_active = Column(Boolean, default=True)    # 是否可用
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="documents")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<KnowledgeDocument {self.title} ({self.document_type})>"

class KnowledgeChunk(Base):
    """知识块模型 - 用于跟踪文档分块"""
    
    __tablename__ = "knowledge_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), nullable=False)
    document = relationship("KnowledgeDocument", backref="chunks")
    
    # 块内容和元数据
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON, default={})
    
    # 向量数据库ID和位置信息
    vector_id = Column(String(255), nullable=True)  # Chroma中的ID
    chunk_index = Column(Integer, nullable=False)   # 块在文档中的索引
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<KnowledgeChunk {self.id} (Doc: {self.document_id}, Index: {self.chunk_index})>"

class Document(Base):
    """文档数据库模型"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, nullable=True)
    status = Column(String(10), default=DocumentStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    doc_metadata = Column(JSON, default={})
    chunk_count = Column(Integer, default=0)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeBase(Base):
    """知识库数据库模型"""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, nullable=True)
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    embedding_model = Column(String(100), nullable=False)
    document_count = Column(Integer, default=0)

    # Relationships
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="knowledge_base", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """文档分块数据库模型"""
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    doc_metadata = Column(JSON, default={})
    
    # 注意: 向量嵌入通常存储在向量数据库中，而非SQL数据库
    # embedding 字段不存储在此

    # Relationships
    document = relationship("Document", back_populates="chunks")
    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")