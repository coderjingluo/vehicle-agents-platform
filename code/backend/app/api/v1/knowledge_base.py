"""
知识库管理API路由

提供知识库CRUD、文档管理、语义搜索等功能的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json

from app.core.database import get_db_session
from app.models.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseStatus,
    DocumentUpload,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentType,
    KnowledgeBaseStats
)
from app.services.knowledge_base_service import KnowledgeBaseService
from loguru import logger

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-base"])


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """创建知识库"""
    try:
        service = KnowledgeBaseService()
        knowledge_base = await service.create_knowledge_base(kb_data, db)
        return KnowledgeBaseResponse.model_validate(knowledge_base)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建知识库API错误: {e}")
        raise HTTPException(status_code=500, detail="创建知识库失败")


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    status: Optional[KnowledgeBaseStatus] = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库列表"""
    try:
        service = KnowledgeBaseService()
        knowledge_bases, total = await service.list_knowledge_bases(
            db, status=status, limit=limit, offset=offset
        )
        
        response_data = [
            KnowledgeBaseResponse.model_validate(kb) for kb in knowledge_bases
        ]
        
        return JSONResponse(
            content=[kb.model_dump() for kb in response_data],
            headers={"X-Total-Count": str(total)}
        )
    except Exception as e:
        logger.error(f"获取知识库列表API错误: {e}")
        raise HTTPException(status_code=500, detail="获取知识库列表失败")


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    include_documents: bool = Query(False, description="是否包含文档列表"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库详情"""
    try:
        service = KnowledgeBaseService()
        knowledge_base = await service.get_knowledge_base(
            kb_id, db, include_documents=include_documents
        )
        
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return KnowledgeBaseResponse.model_validate(knowledge_base)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库API错误: {e}")
        raise HTTPException(status_code=500, detail="获取知识库失败")


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """更新知识库"""
    try:
        service = KnowledgeBaseService()
        knowledge_base = await service.update_knowledge_base(kb_id, kb_data, db)
        
        if not knowledge_base:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return KnowledgeBaseResponse.model_validate(knowledge_base)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新知识库API错误: {e}")
        raise HTTPException(status_code=500, detail="更新知识库失败")


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """删除知识库"""
    try:
        service = KnowledgeBaseService()
        success = await service.delete_knowledge_base(kb_id, db)
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return {"message": "知识库删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库API错误: {e}")
        raise HTTPException(status_code=500, detail="删除知识库失败")


@router.post("/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(..., description="上传的文档文件"),
    name: str = Form(..., description="文档名称"),
    file_type: DocumentType = Form(..., description="文档类型"),
    metadata: str = Form("{}", description="文档元数据(JSON格式)"),
    db: AsyncSession = Depends(get_db_session)
):
    """上传文档到知识库"""
    try:
        # 解析元数据
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="元数据格式错误，应为JSON格式")
        
        # 验证文件类型
        if file.content_type:
            allowed_types = {
                DocumentType.PDF: ["application/pdf"],
                DocumentType.DOCX: [
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ],
                DocumentType.TXT: ["text/plain"],
                DocumentType.MD: ["text/markdown", "text/x-markdown"],
                DocumentType.HTML: ["text/html"],
                DocumentType.JSON: ["application/json"],
                DocumentType.XML: ["application/xml", "text/xml"]
            }
            
            if file.content_type not in allowed_types.get(file_type, []):
                logger.warning(f"文件类型不匹配: {file.content_type} vs {file_type}")
        
        # 读取文件内容
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="文件为空")
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB限制
            raise HTTPException(status_code=400, detail="文件大小超过限制(50MB)")
        
        # 创建文档上传对象
        doc_upload = DocumentUpload(
            name=name,
            file_type=file_type,
            metadata=metadata_dict
        )
        
        # 上传文档
        service = KnowledgeBaseService()
        document = await service.upload_document(kb_id, file_content, doc_upload, db)
        
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上传文档API错误: {e}")
        raise HTTPException(status_code=500, detail="上传文档失败")


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    processing_status: Optional[str] = Query(None, description="处理状态筛选"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库中的文档列表"""
    try:
        # 验证知识库是否存在
        service = KnowledgeBaseService()
        kb = await service.get_knowledge_base(kb_id, db)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 这里可以添加获取文档列表的逻辑
        # 简化实现，直接返回知识库的文档
        kb_with_docs = await service.get_knowledge_base(kb_id, db, include_documents=True)
        documents = kb_with_docs.documents if kb_with_docs else []
        
        # 应用筛选和分页
        if processing_status:
            documents = [doc for doc in documents if doc.processing_status == processing_status]
        
        documents = documents[offset:offset + limit]
        
        return [DocumentResponse.model_validate(doc) for doc in documents]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表API错误: {e}")
        raise HTTPException(status_code=500, detail="获取文档列表失败")


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """删除文档"""
    try:
        service = KnowledgeBaseService()
        success = await service.delete_document(doc_id, db)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {"message": "文档删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档API错误: {e}")
        raise HTTPException(status_code=500, detail="删除文档失败")


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """搜索文档"""
    try:
        service = KnowledgeBaseService()
        search_response = await service.search_documents(search_request, db)
        return search_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"搜索文档API错误: {e}")
        raise HTTPException(status_code=500, detail="搜索文档失败")


@router.get("/stats/overview", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库统计信息"""
    try:
        service = KnowledgeBaseService()
        stats = await service.get_knowledge_base_stats(db)
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息API错误: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# 演示API
@router.post("/demo/upload-and-search")
async def demo_upload_and_search(
    kb_id: str,
    file: UploadFile = File(...),
    search_query: str = Form(..., description="搜索查询"),
    db: AsyncSession = Depends(get_db_session)
):
    """演示：上传文档并立即搜索"""
    try:
        # 自动检测文件类型
        file_type = DocumentType.TXT
        if file.filename:
            if file.filename.endswith('.pdf'):
                file_type = DocumentType.PDF
            elif file.filename.endswith('.docx'):
                file_type = DocumentType.DOCX
            elif file.filename.endswith('.md'):
                file_type = DocumentType.MD
            elif file.filename.endswith('.html'):
                file_type = DocumentType.HTML
            elif file.filename.endswith('.json'):
                file_type = DocumentType.JSON
            elif file.filename.endswith('.xml'):
                file_type = DocumentType.XML
        
        # 上传文档
        file_content = await file.read()
        doc_upload = DocumentUpload(
            name=file.filename or "unknown",
            file_type=file_type,
            metadata={"demo": True}
        )
        
        service = KnowledgeBaseService()
        document = await service.upload_document(kb_id, file_content, doc_upload, db)
        
        # 等待文档处理完成（简化实现）
        import asyncio
        await asyncio.sleep(2)
        
        # 执行搜索
        search_request = DocumentSearchRequest(
            query=search_query,
            knowledge_base_id=kb_id,
            limit=5
        )
        search_response = await service.search_documents(search_request, db)
        
        return {
            "uploaded_document": DocumentResponse.model_validate(document),
            "search_results": search_response
        }
        
    except Exception as e:
        logger.error(f"演示API错误: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


@router.get("/demo/sample-data")
async def create_demo_knowledge_base(
    db: AsyncSession = Depends(get_db_session)
):
    """创建演示知识库和示例数据"""
    try:
        service = KnowledgeBaseService()
        
        # 创建演示知识库
        kb_data = KnowledgeBaseCreate(
            name="车联网安全测试演示知识库",
            description="包含车联网安全测试相关文档和最佳实践",
            embedding_model="text-embedding-ada-002",
            chunk_size=1000,
            chunk_overlap=200
        )
        
        knowledge_base = await service.create_knowledge_base(kb_data, db)
        
        # 创建示例文档内容
        sample_documents = [
            {
                "name": "ISO 21434 车辆网络安全标准",
                "content": """
ISO 21434是车辆网络安全工程的国际标准。该标准定义了车辆网络安全管理系统的要求，
包括组织层面的网络安全治理、项目层面的网络安全活动、持续的网络安全活动等。

主要内容包括：
1. 网络安全治理和风险管理
2. 项目相关的网络安全活动
3. 持续的网络安全活动
4. 威胁分析和风险评估(TARA)
5. 网络安全概念设计
6. 产品开发中的网络安全
7. 网络安全验证和确认
8. 网络安全监控和响应

TARA（Threat Analysis and Risk Assessment）是标准的核心组成部分，
要求对车辆系统进行系统性的威胁识别和风险评估。
                """,
                "type": DocumentType.TXT
            },
            {
                "name": "车联网安全测试最佳实践",
                "content": """
车联网安全测试最佳实践指南

1. 渗透测试
   - 网络接口安全测试
   - 无线通信安全测试
   - 固件安全分析
   - 硬件安全测试

2. 协议安全测试
   - CAN总线安全测试
   - V2X通信安全测试
   - OTA更新安全测试
   - 认证和授权测试

3. 数据保护测试
   - 个人数据保护测试
   - 数据传输加密测试
   - 数据存储安全测试
   - 隐私保护测试

4. 业务逻辑安全测试
   - 访问控制测试
   - 权限提升测试
   - 业务流程安全测试
   - 异常处理测试

5. 移动应用安全测试
   - 应用程序接口安全
   - 客户端安全测试
   - 后端服务安全测试
   - 第三方组件安全测试
                """,
                "type": DocumentType.TXT
            }
        ]
        
        # 添加示例文档
        for doc_data in sample_documents:
            doc_upload = DocumentUpload(
                name=doc_data["name"],
                file_type=doc_data["type"],
                metadata={"category": "demo", "source": "system"}
            )
            
            # 直接处理文本内容（跳过文件保存步骤）
            await service.upload_document(
                knowledge_base.id,
                doc_data["content"].encode('utf-8'),
                doc_upload,
                db
            )
        
        return {
            "message": "演示知识库创建成功",
            "knowledge_base_id": knowledge_base.id,
            "knowledge_base": KnowledgeBaseResponse.model_validate(knowledge_base)
        }
        
    except Exception as e:
        logger.error(f"创建演示数据API错误: {e}")
        raise HTTPException(status_code=500, detail=f"创建演示数据失败: {str(e)}") 