"""
知识库管理相关数据模型

支持多知识库管理、文档上传、向量化存储、语义搜索等功能
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.core.database import Base


class KnowledgeBaseStatus(str, Enum):
    """知识库状态枚举"""
    ACTIVE = "active"           # 激活状态
    INACTIVE = "inactive"       # 未激活
    INDEXING = "indexing"       # 索引中
    ERROR = "error"             # 错误状态
    ARCHIVED = "archived"       # 已归档


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"
    XML = "xml"


# SQLAlchemy 数据模型
class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=KnowledgeBaseStatus.ACTIVE.value)
    
    # 配置信息
    config = Column(JSON, default={})  # 知识库配置，如向量化参数等
    embedding_model = Column(String(100), default="text-embedding-ada-002")
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # 统计信息
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联文档
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    knowledge_base_id = Column(String, ForeignKey("knowledge_bases.id"), nullable=False)
    
    # 文档基本信息
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)  # 文件大小(bytes)
    file_type = Column(String(20), nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA256哈希，用于去重
    
    # 文档内容
    content = Column(Text, nullable=True)  # 提取的文本内容
    metadata = Column(JSON, default={})   # 文档元数据
    
    # 向量化信息
    is_vectorized = Column(Boolean, default=False)
    vector_ids = Column(JSON, default=[])  # 在向量数据库中的ID列表
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    
    # 处理状态
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, error
    processing_error = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


# Pydantic 模型 - 用于API交互
class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求模型"""
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    embedding_model: str = Field("text-embedding-ada-002", description="嵌入模型")
    chunk_size: int = Field(1000, ge=100, le=4000, description="文档分块大小")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="分块重叠大小")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="知识库配置")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[KnowledgeBaseStatus] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    config: Optional[Dict[str, Any]] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模型"""
    id: str
    name: str
    description: Optional[str]
    status: KnowledgeBaseStatus
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    document_count: int
    total_chunks: int
    total_tokens: int
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """文档上传请求模型"""
    name: str = Field(..., min_length=1, max_length=255, description="文档名称")
    file_type: DocumentType = Field(..., description="文档类型")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="文档元数据")


class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: str
    knowledge_base_id: str
    name: str
    file_path: str
    file_size: int
    file_type: str
    content_hash: Optional[str]
    metadata: Dict[str, Any]
    is_vectorized: bool
    chunk_count: int
    token_count: int
    processing_status: str
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """文档搜索请求模型"""
    query: str = Field(..., min_length=1, description="搜索查询")
    knowledge_base_id: Optional[str] = Field(None, description="指定知识库ID")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")
    include_metadata: bool = Field(True, description="是否包含元数据")


class DocumentSearchResult(BaseModel):
    """文档搜索结果模型"""
    document_id: str
    document_name: str
    knowledge_base_id: str
    knowledge_base_name: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    chunk_index: int


class DocumentSearchResponse(BaseModel):
    """文档搜索响应模型"""
    query: str
    total_results: int
    results: List[DocumentSearchResult]
    execution_time: float


class KnowledgeBaseStats(BaseModel):
    """知识库统计信息模型"""
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    total_tokens: int
    storage_size: int  # 存储大小(bytes)
    
    by_status: Dict[str, int]  # 按状态统计
    by_type: Dict[str, int]    # 按文档类型统计
    recent_activity: List[Dict[str, Any]]  # 最近活动 