"""
知识库API端点

提供知识库管理、文档管理和搜索功能的API接口
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.knowledge import KnowledgeBase, Document
from app.services.knowledge_service import KnowledgeBaseService
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseDetailResponse,
    DocumentResponse,
    DocumentListResponse,
    SearchRequest,
    SearchResponse
)
from app.schemas.common import ResponseModel, PaginationParams

router = APIRouter()


@router.post(
    "/knowledge-bases",
    status_code=status.HTTP_201_CREATED,
    summary="创建知识库"
)
async def create_knowledge_base(
    kb_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的知识库
    """
    try:
        kb_service = KnowledgeBaseService(db)
        kb = await kb_service.create_knowledge_base(
            name=kb_data["name"],
            description=kb_data.get("description"),
            chunk_size=kb_data.get("chunk_size", 500),
            chunk_overlap=kb_data.get("chunk_overlap", 50),
            embedding_model=kb_data.get("embedding_model", "text-embedding-3-small")
        )
        
        return {
            "success": True,
            "data": {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "created_at": kb.created_at,
                "chunk_size": kb.chunk_size,
                "chunk_overlap": kb.chunk_overlap,
                "embedding_model": kb.embedding_model,
                "document_count": kb.document_count
            },
            "message": "知识库创建成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/knowledge-bases",
    summary="获取知识库列表"
)
async def get_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有知识库列表
    """
    kb_service = KnowledgeBaseService(db)
    kb_list = await kb_service.list_knowledge_bases()
    
    knowledge_bases = []
    for kb in kb_list:
        knowledge_bases.append({
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "created_at": kb.created_at,
            "document_count": kb.document_count
        })
    
    return {
        "success": True,
        "data": {
            "knowledge_bases": knowledge_bases
        },
        "message": "获取知识库列表成功"
    }


@router.get(
    "/knowledge-bases/{kb_id}",
    summary="获取知识库详情"
)
async def get_knowledge_base_detail(
    kb_id: str = Path(..., description="知识库ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取知识库详细信息，包括文档列表
    """
    kb_service = KnowledgeBaseService(db)
    kb = await kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 获取知识库中的文档
    documents = await kb_service.list_documents(kb_id)
    
    # 计算总块数
    total_chunks = sum(doc.chunk_count or 0 for doc in documents)
    
    # 构建文档列表
    doc_list = []
    for doc in documents:
        doc_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_format": doc.file_format,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at,
            "status": doc.status,
            "chunk_count": doc.chunk_count
        })
    
    # 构建响应
    response_data = {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "created_at": kb.created_at,
        "last_updated": kb.last_updated,
        "chunk_size": kb.chunk_size,
        "chunk_overlap": kb.chunk_overlap,
        "embedding_model": kb.embedding_model,
        "document_count": kb.document_count,
        "total_chunks": total_chunks,
        "documents": doc_list
    }
    
    return {
        "success": True,
        "data": response_data,
        "message": "获取知识库详情成功"
    }


@router.delete(
    "/knowledge-bases/{kb_id}",
    summary="删除知识库"
)
async def delete_knowledge_base(
    kb_id: str = Path(..., description="知识库ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定的知识库及其所有文档
    """
    kb_service = KnowledgeBaseService(db)
    result = await kb_service.delete_knowledge_base(kb_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    return {
        "success": True,
        "data": None,
        "message": "知识库删除成功"
    }


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    status_code=status.HTTP_201_CREATED,
    summary="上传文档"
)
async def upload_document(
    kb_id: str = Path(..., description="知识库ID"),
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传文档到指定知识库
    """
    kb_service = KnowledgeBaseService(db)
    
    # 解析元数据
    meta_dict = {}
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="元数据格式错误，必须是有效的JSON"
            )
    
    try:
        document = await kb_service.upload_document(
            kb_id=kb_id,
            file=file,
            metadata=meta_dict
        )
        
        return {
            "success": True,
            "data": {
                "id": document.id,
                "filename": document.filename,
                "kb_id": document.kb_id,
                "file_format": document.file_format,
                "file_size": document.file_size,
                "uploaded_at": document.uploaded_at,
                "status": document.status,
                "metadata": document.doc_metadata
            },
            "message": "文档上传成功，正在处理"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    summary="获取文档列表"
)
async def get_documents(
    kb_id: str = Path(..., description="知识库ID"),
    status: Optional[str] = Query(None, description="文档状态筛选"),
    format: Optional[str] = Query(None, description="文件格式筛选"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取知识库中的文档列表
    """
    kb_service = KnowledgeBaseService(db)
    
    # 检查知识库是否存在
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 获取文档列表
    documents = await kb_service.list_documents(kb_id)
    
    # 应用筛选
    if status:
        documents = [doc for doc in documents if doc.status == status]
    
    if format:
        documents = [doc for doc in documents if doc.file_format == format]
    
    # 应用分页
    total = len(documents)
    pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated_docs = documents[start:end]
    
    # 构建响应
    doc_list = []
    for doc in paginated_docs:
        doc_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_format": doc.file_format,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at,
            "status": doc.status,
            "chunk_count": doc.chunk_count
        })
    
    return {
        "success": True,
        "data": {
            "documents": doc_list,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages
            }
        },
        "message": "获取文档列表成功"
    }


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}",
    summary="删除文档"
)
async def delete_document(
    kb_id: str = Path(..., description="知识库ID"),
    doc_id: str = Path(..., description="文档ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    从知识库中删除指定文档
    """
    kb_service = KnowledgeBaseService(db)
    
    # 检查文档是否存在
    document = await kb_service.get_document(doc_id)
    if not document or document.kb_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在或不属于指定知识库"
        )
    
    # 删除文档
    result = await kb_service.delete_document(doc_id)
    
    return {
        "success": True,
        "data": None,
        "message": "文档删除成功"
    }


@router.post(
    "/knowledge-bases/{kb_id}/search",
    summary="语义搜索"
)
async def semantic_search(
    search_request: dict,
    kb_id: str = Path(..., description="知识库ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    在知识库中进行语义搜索
    """
    kb_service = KnowledgeBaseService(db)
    
    # 检查知识库是否存在
    kb = await kb_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 执行搜索
    search_results = await kb_service.semantic_search(
        kb_id=kb_id,
        query=search_request["query"],
        top_k=search_request.get("top_k", 5),
        threshold=search_request.get("similarity_threshold", 0.0)
    )
    
    # 格式化结果
    formatted_results = []
    for result in search_results:
        formatted_results.append({
            "id": result.id,
            "content": result.text,
            "document_id": result.document_id,
            "document_name": result.metadata.get("filename", ""),
            "similarity": result.similarity,
            "metadata": result.metadata
        })
    
    return {
        "success": True,
        "data": {
            "results": formatted_results
        },
        "message": "搜索成功"
    } 