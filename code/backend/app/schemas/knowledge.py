"""
知识库相关的模式定义
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求模式"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    chunk_size: int = Field(500, description="文本分块大小")
    chunk_overlap: int = Field(50, description="文本分块重叠大小")
    embedding_model: str = Field("text-embedding-3-small", description="嵌入模型名称")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模式"""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    document_count: int = 0
    
    class Config:
        orm_mode = True


class DocumentResponse(BaseModel):
    """文档响应模式"""
    id: str
    filename: str
    file_format: str
    file_size: int
    uploaded_at: datetime
    status: str
    chunk_count: Optional[int] = None
    
    class Config:
        orm_mode = True


class PaginationInfo(BaseModel):
    """分页信息"""
    total: int
    page: int
    limit: int
    pages: int


class DocumentListResponse(BaseModel):
    """文档列表响应模式"""
    documents: List[DocumentResponse]
    pagination: PaginationInfo


class KnowledgeBaseDetailResponse(BaseModel):
    """知识库详情响应模式"""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    last_updated: Optional[datetime]
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    document_count: int
    total_chunks: int
    documents: List[DocumentResponse]
    
    class Config:
        orm_mode = True


class SearchRequest(BaseModel):
    """搜索请求模式"""
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(5, description="返回结果数量")
    similarity_threshold: float = Field(0.0, description="相似度阈值")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: str
    content: str
    document_id: str
    document_name: str
    similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """搜索响应模式"""
    results: List[SearchResultItem]
