# 知识库系统详细设计

## 1. 知识库系统概述

知识库系统是KunlunSec AI平台的核心组件之一，提供车联网安全知识的存储、检索和管理能力。该系统基于向量数据库技术，实现高效的语义搜索和RAG（检索增强生成）功能，帮助智能体访问专业知识，提高决策质量。

### 1.1 知识库系统架构

```
┌────────────────────┐      ┌────────────────────┐
│                    │      │                    │
│     前端界面       │◄────►│    API服务层       │
│                    │      │                    │
└────────────────────┘      └─────────┬──────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│                 知识库系统                       │
│                                                 │
│  ┌──────────────────┐     ┌───────────────────┐ │
│  │                  │     │                   │ │
│  │   文档管理器     │     │   语义搜索引擎    │ │
│  │                  │     │                   │ │
│  └──────────────────┘     └───────────────────┘ │
│                                                 │
│  ┌──────────────────┐     ┌───────────────────┐ │
│  │                  │     │                   │ │
│  │ 向量数据库连接器 │     │    知识提取器     │ │
│  │                  │     │                   │ │
│  └──────────────────┘     └───────────────────┘ │
│                                                 │
└─────────────────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│               存储层                            │
│  ┌────────────────────┐  ┌──────────────────┐   │
│  │                    │  │                  │   │
│  │   向量数据库       │  │  文档存储        │   │
│  │   (Chroma/Qdrant)  │  │                  │   │
│  └────────────────────┘  └──────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 1.2 知识库设计原则

- **模块化**: 清晰的组件分离，便于维护和扩展
- **高性能**: 优化的索引和检索机制，支持快速响应
- **可伸缩性**: 能够处理不断增长的文档集合
- **多格式支持**: 支持多种格式的文档处理
- **自动化维护**: 支持自动更新和知识提取

## 2. 知识库模型设计

### 2.1 知识库实体模型

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """文档处理状态枚举"""
    PENDING = "pending"       # 等待处理
    PROCESSING = "processing" # 正在处理
    COMPLETED = "completed"   # 处理完成
    FAILED = "failed"         # 处理失败


class DocumentFormat(str, Enum):
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


class Document(BaseModel):
    """文档实体模型"""
    id: str = Field(description="文档唯一标识符")
    kb_id: str = Field(description="所属知识库ID")
    filename: str = Field(description="文件名")
    file_format: DocumentFormat = Field(description="文件格式")
    file_size: int = Field(description="文件大小(字节)")
    content_type: str = Field(description="内容类型")
    uploaded_at: datetime = Field(description="上传时间")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="处理状态")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    metadata: Dict[str, str] = Field(default_factory=dict, description="文档元数据")
    chunk_count: int = Field(default=0, description="分块数量")


class KnowledgeBase(BaseModel):
    """知识库实体模型"""
    id: str = Field(description="知识库唯一标识符")
    name: str = Field(description="知识库名称")
    description: Optional[str] = Field(default=None, description="知识库描述")
    created_at: datetime = Field(description="创建时间")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    chunk_size: int = Field(default=500, description="分块大小")
    chunk_overlap: int = Field(default=50, description="分块重叠大小")
    embedding_model: str = Field(description="使用的嵌入模型")
    document_count: int = Field(default=0, description="文档数量")


class DocumentChunk(BaseModel):
    """文档分块实体模型"""
    id: str = Field(description="分块唯一标识符")
    document_id: str = Field(description="所属文档ID")
    kb_id: str = Field(description="所属知识库ID")
    content: str = Field(description="分块内容")
    chunk_index: int = Field(description="分块索引")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入")
    metadata: Dict[str, str] = Field(default_factory=dict, description="分块元数据")


class SearchResult(BaseModel):
    """搜索结果实体模型"""
    id: str = Field(description="分块ID")
    text: str = Field(description="文本内容")
    document_id: str = Field(description="文档ID")
    similarity: float = Field(description="相似度分数")
    metadata: Dict[str, str] = Field(default_factory=dict, description="元数据")
```

## 3. 文档管理器设计

文档管理器负责文档的上传、更新、删除和分块处理。

```python
from typing import BinaryIO, Dict, List, Optional, Union

class DocumentManager:
    """文档管理器"""
    
    def __init__(self, vector_db_connector, file_store_path: str):
        self.vector_db_connector = vector_db_connector
        self.file_store_path = file_store_path
    
    async def upload_document(self, kb_id: str, file: BinaryIO, filename: str,
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
                file_format=file_format,
                file_size=file_size,
                content_type=self._get_content_type(file_format),
                uploaded_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # 4. 保存文档记录到数据库
            await self._save_document_record(document)
            
            # 5. 触发异步处理任务
            await self._process_document_async(document)
            
            return document
        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            raise DocumentUploadError(f"Failed to upload document: {str(e)}")
    
    async def _process_document_async(self, document: Document) -> None:
        """异步处理文档（分块和向量化）"""
        try:
            # 更新状态为处理中
            document.status = DocumentStatus.PROCESSING
            await self._update_document_status(document.id, DocumentStatus.PROCESSING)
            
            # 1. 读取文档内容
            content = await self._read_document_content(document)
            
            # 2. 获取知识库配置
            kb = await self._get_knowledge_base(document.kb_id)
            
            # 3. 分块处理
            chunks = await self._split_document(content, document, kb.chunk_size, kb.chunk_overlap)
            
            # 4. 向量化和存储
            await self._vectorize_and_store(chunks, kb.embedding_model)
            
            # 5. 更新文档状态
            document.status = DocumentStatus.COMPLETED
            document.chunk_count = len(chunks)
            document.last_updated = datetime.now()
            await self._update_document_record(document)
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {str(e)}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await self._update_document_record(document)
    
    async def _read_document_content(self, document: Document) -> str:
        """根据文档格式读取内容"""
        file_path = self._get_document_path(document.id, document.filename)
        
        if document.file_format in [DocumentFormat.TXT, DocumentFormat.MD, 
                                  DocumentFormat.PY, DocumentFormat.JS,
                                  DocumentFormat.HTML, DocumentFormat.CSS,
                                  DocumentFormat.JAVA, DocumentFormat.CPP,
                                  DocumentFormat.C]:
            # 直接读取文本文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
                
        elif document.file_format == DocumentFormat.PDF:
            # 使用PyPDF2读取PDF
            return await self._read_pdf(file_path)
            
        elif document.file_format in [DocumentFormat.DOCX, DocumentFormat.DOC]:
            # 使用python-docx读取Word文档
            return await self._read_docx(file_path)
            
        else:
            raise UnsupportedFormatError(f"Unsupported file format: {document.file_format}")
    
    async def _split_document(self, content: str, document: Document, 
                            chunk_size: int, chunk_overlap: int) -> List[DocumentChunk]:
        """将文档内容分块"""
        # 使用文本分割器进行分块
        text_splitter = self._get_text_splitter(document.file_format, chunk_size, chunk_overlap)
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
                    "format": document.file_format.value,
                    "chunk": f"{i+1}/{len(texts)}"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _vectorize_and_store(self, chunks: List[DocumentChunk], embedding_model: str) -> None:
        """向量化分块内容并存储"""
        # 获取嵌入模型
        embedding_function = self._get_embedding_function(embedding_model)
        
        # 批量创建嵌入
        texts = [chunk.content for chunk in chunks]
        embeddings = await self._create_embeddings(texts, embedding_function)
        
        # 更新分块的嵌入
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]
        
        # 存储到向量数据库
        await self.vector_db_connector.add_chunks(chunks)
    
    async def delete_document(self, document_id: str) -> bool:
        """从知识库中删除文档"""
        try:
            # 1. 获取文档记录
            document = await self._get_document(document_id)
            if not document:
                return False
            
            # 2. 删除向量数据库中的分块
            await self.vector_db_connector.delete_by_document_id(document_id)
            
            # 3. 删除文件系统中的文档
            file_path = self._get_document_path(document.id, document.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 4. 删除文档记录
            await self._delete_document_record(document_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise DocumentDeletionError(f"Failed to delete document: {str(e)}")
    
    async def get_document_info(self, document_id: str) -> Optional[Document]:
        """获取文档信息"""
        return await self._get_document(document_id)
    
    async def list_documents(self, kb_id: str) -> List[Document]:
        """列出知识库中的所有文档"""
        return await self._list_documents_by_kb(kb_id)
```

### 3.1 文本分割器

```python
from typing import Dict, Type

class TextSplitterFactory:
    """文本分割器工厂"""
    
    @staticmethod
    def get_splitter(document_format: DocumentFormat, chunk_size: int, chunk_overlap: int):
        """根据文档格式获取适当的文本分割器"""
        format_to_splitter: Dict[DocumentFormat, Type[TextSplitter]] = {
            DocumentFormat.TXT: RecursiveCharacterTextSplitter,
            DocumentFormat.MD: MarkdownTextSplitter,
            DocumentFormat.PDF: RecursiveCharacterTextSplitter,
            DocumentFormat.DOCX: RecursiveCharacterTextSplitter,
            DocumentFormat.DOC: RecursiveCharacterTextSplitter,
            DocumentFormat.PY: PythonCodeTextSplitter,
            DocumentFormat.JS: JavaScriptTextSplitter,
            DocumentFormat.HTML: HTMLTextSplitter,
            DocumentFormat.CSS: RecursiveCharacterTextSplitter,
            DocumentFormat.JAVA: JavaTextSplitter,
            DocumentFormat.CPP: CPPTextSplitter,
            DocumentFormat.C: CTextSplitter
        }
        
        splitter_cls = format_to_splitter.get(
            document_format, 
            RecursiveCharacterTextSplitter
        )
        
        return splitter_cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
```

## 4. 语义搜索引擎设计

语义搜索引擎是知识库系统的核心，负责根据语义相似度检索与查询最相关的内容。

```python
class SemanticSearchEngine:
    """语义搜索引擎"""
    
    def __init__(self, vector_db_connector):
        self.vector_db_connector = vector_db_connector
    
    async def search(self, kb_id: str, query: str, top_k: int = 5,
                   filters: Optional[Dict[str, str]] = None) -> List[SearchResult]:
        """语义搜索知识库"""
        try:
            # 1. 验证知识库ID
            kb = await self._get_knowledge_base(kb_id)
            if not kb:
                raise ValueError(f"Knowledge base not found: {kb_id}")
            
            # 2. 获取嵌入模型
            embedding_model = self._get_embedding_model(kb.embedding_model)
            
            # 3. 生成查询嵌入
            query_embedding = await self._generate_embedding(query, embedding_model)
            
            # 4. 执行向量搜索
            search_results = await self.vector_db_connector.similarity_search(
                kb_id=kb_id,
                query_vector=query_embedding,
                top_k=top_k,
                filters=filters
            )
            
            # 5. 格式化结果
            formatted_results = []
            for result in search_results:
                formatted_results.append(
                    SearchResult(
                        id=result["id"],
                        text=result["text"],
                        document_id=result["metadata"]["document_id"],
                        similarity=result["score"],
                        metadata=result["metadata"]
                    )
                )
            
            return formatted_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise SearchError(f"Failed to perform semantic search: {e}")
    
    async def _generate_embedding(self, text: str, model: str) -> List[float]:
        """使用指定模型生成嵌入向量"""
        # 实现嵌入生成
```

### 4.1 RAG查询工具 (RagQueryTool)

参考OpenManus中工具实现的经验，设计RAG查询工具，使智能体能够直接查询知识库获取信息。

```python
class RagQueryTool(BaseTool):
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
                "default": false
            }
        },
        "required": ["kb_name", "query"]
    }
    
    async def execute(self, kb_name: str, query: str, top_k: int = 5, 
                     filters: Optional[Dict[str, str]] = None,
                     rerank: bool = False, **kwargs) -> ToolResult:
        """执行RAG查询"""
        try:
            # 获取知识库ID
            kb_service = KnowledgeBaseService()
            kb = await kb_service.get_knowledge_base_by_name(kb_name)
            if not kb:
                return ToolResult(error=f"知识库不存在: {kb_name}")
            
            # 创建搜索引擎
            search_engine = SemanticSearchEngine(kb_service.vector_db)
            
            # 执行搜索
            search_results = await search_engine.search(
                kb_id=kb.id,
                query=query,
                top_k=top_k,
                filters=filters or {}
            )
            
            # 重排序（如果启用）
            if rerank and len(search_results) > 1:
                search_results = await self._rerank_results(query, search_results)
            
            # 格式化结果
            formatted_results = []
            for i, result in enumerate(search_results):
                formatted_results.append({
                    "rank": i + 1,
                    "text": result.text,
                    "document": result.metadata.get("document_name", ""),
                    "similarity": round(result.similarity, 3),
                    "metadata": {
                        k: v for k, v in result.metadata.items() 
                        if k not in ["document_name", "document_id"]
                    }
                })
            
            return ToolResult(output=formatted_results)
        except Exception as e:
            return ToolResult(error=f"RAG查询失败: {str(e)}")
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """使用交叉编码器对结果进行重排序"""
        try:
            # 获取交叉编码器模型
            reranker = self._get_reranker_model()
            
            # 准备文本对
            pairs = [(query, result.text) for result in results]
            
            # 计算相似度得分
            scores = reranker.predict(pairs)
            
            # 更新相似度分数
            for i, result in enumerate(results):
                result.similarity = float(scores[i])
            
            # 根据新的相似度分数排序
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            return results
        except Exception as e:
            logger.warning(f"重排序失败，使用原始排序: {e}")
            return results
    
    def _get_reranker_model(self):
        """获取交叉编码器模型"""
        # 使用sentence-transformers中的交叉编码器
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
            return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except ImportError:
            logger.warning("sentence-transformers未安装，无法使用交叉编码器")
            return None
```

## 5. 主动学习系统

知识库系统的一个关键优势是能够从实际操作中不断学习和改进。主动学习系统负责从智能体的执行过程中提取有价值的知识，并将其整合到知识库中。

### 5.1 知识提取器

```python
class KnowledgeExtractor:
    """知识提取器，从智能体执行过程中提取知识"""
    
    def __init__(self, vector_db_connector, embedding_model: str = "text-embedding-3-small"):
        self.vector_db_connector = vector_db_connector
        self.embedding_model = embedding_model
        self.extraction_strategies = {
            "task_execution": self._extract_from_task_execution,
            "agent_conversation": self._extract_from_conversation,
            "tool_usage": self._extract_from_tool_usage,
            "error_handling": self._extract_from_error_handling
        }
    
    async def extract_knowledge(self, source_type: str, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从不同类型的源数据中提取知识"""
        if source_type not in self.extraction_strategies:
            raise ValueError(f"不支持的知识源类型: {source_type}")
            
        extraction_func = self.extraction_strategies[source_type]
        knowledge_items = await extraction_func(source_data)
        
        # 过滤无价值的知识项
        filtered_items = await self._filter_knowledge_items(knowledge_items)
        
        return filtered_items
    
    async def _extract_from_task_execution(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从任务执行记录中提取知识"""
        knowledge_items = []
        
        # 提取任务目标和结果之间的关系
        if "goal" in task_data and "result" in task_data:
            knowledge_items.append({
                "type": "task_pattern",
                "goal": task_data["goal"],
                "successful_approach": task_data.get("successful_steps", []),
                "result": task_data["result"],
                "metadata": {
                    "task_id": task_data.get("id"),
                    "execution_time": task_data.get("execution_time"),
                    "confidence": self._calculate_confidence(task_data)
                }
            })
        
        # 提取有价值的中间结果
        if "intermediate_results" in task_data:
            for step, result in task_data["intermediate_results"].items():
                if self._is_valuable_result(result):
                    knowledge_items.append({
                        "type": "intermediate_insight",
                        "step": step,
                        "insight": result,
                        "metadata": {
                            "task_id": task_data.get("id"),
                            "confidence": 0.7  # 中间结果的默认置信度
                        }
                    })
        
        return knowledge_items
    
    async def _extract_from_conversation(self, conversation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从智能体对话中提取知识"""
        # 实现从对话中提取知识的逻辑
        pass
    
    async def _extract_from_tool_usage(self, tool_usage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从工具使用记录中提取知识"""
        # 实现从工具使用中提取知识的逻辑
        pass
    
    async def _extract_from_error_handling(self, error_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从错误处理记录中提取知识"""
        # 实现从错误处理中提取知识的逻辑
        pass
    
    async def _filter_knowledge_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤低价值的知识项"""
        if not items:
            return []
            
        # 计算每个知识项的价值分数
        scored_items = []
        for item in items:
            value_score = await self._calculate_knowledge_value(item)
            if value_score > 0.5:  # 只保留价值分数大于0.5的项
                item["value_score"] = value_score
                scored_items.append(item)
        
        return scored_items
    
    async def _calculate_knowledge_value(self, item: Dict[str, Any]) -> float:
        """计算知识项的价值"""
        # 实现知识价值计算逻辑
        # 可考虑：新颖性、适用性、准确性等因素
        return 0.7  # 示例默认值
```

### 5.2 知识整合器

```python
class KnowledgeIntegrator:
    """知识整合器，将提取的知识整合到知识库中"""
    
    def __init__(self, knowledge_base_service, conflict_resolution_strategy: str = "confidence_based"):
        self.kb_service = knowledge_base_service
        self.conflict_strategy = conflict_resolution_strategy
    
    async def integrate_knowledge(self, kb_id: str, knowledge_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将知识项整合到指定的知识库中"""
        if not knowledge_items:
            return {"integrated": 0, "conflicts": 0, "errors": 0}
        
        stats = {"integrated": 0, "conflicts": 0, "errors": 0}
        
        for item in knowledge_items:
            try:
                # 1. 检查是否与现有知识冲突
                conflicts = await self._check_conflicts(kb_id, item)
                
                if conflicts:
                    # 2. 解决冲突
                    resolution = await self._resolve_conflicts(conflicts, item)
                    if resolution["action"] == "update":
                        await self._update_existing_knowledge(kb_id, resolution["target_id"], item)
                        stats["integrated"] += 1
                        stats["conflicts"] += 1
                    elif resolution["action"] == "ignore":
                        stats["conflicts"] += 1
                        continue
                else:
                    # 3. 添加新知识
                    await self._add_new_knowledge(kb_id, item)
                    stats["integrated"] += 1
            
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"知识整合错误: {str(e)}")
        
        return stats
    
    async def _check_conflicts(self, kb_id: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查知识项是否与现有知识冲突"""
        # 1. 提取关键内容
        key_content = self._extract_key_content(item)
        
        # 2. 语义搜索相似内容
        search_results = await self.kb_service.semantic_search(
            kb_id=kb_id,
            query=key_content,
            top_k=5,
            threshold=0.85  # 高相似度阈值
        )
        
        # 3. 分析冲突
        conflicts = []
        for result in search_results:
            conflict_type = self._analyze_conflict_type(item, result)
            if conflict_type:
                conflicts.append({
                    "existing_item": result,
                    "conflict_type": conflict_type,
                    "similarity": result.similarity
                })
        
        return conflicts
    
    def _extract_key_content(self, item: Dict[str, Any]) -> str:
        """提取知识项的关键内容用于相似度搜索"""
        if item["type"] == "task_pattern":
            return f"{item['goal']} {item['result']}"
        elif item["type"] == "intermediate_insight":
            return item["insight"]
        # 其他类型的处理...
        return json.dumps(item)
    
    def _analyze_conflict_type(self, new_item: Dict[str, Any], existing_item: Dict[str, Any]) -> Optional[str]:
        """分析冲突类型"""
        # 实现冲突类型分析逻辑
        pass
    
    async def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], new_item: Dict[str, Any]) -> Dict[str, Any]:
        """解决知识冲突"""
        if self.conflict_strategy == "confidence_based":
            # 基于置信度的冲突解决
            highest_confidence_conflict = max(conflicts, key=lambda c: c["existing_item"].metadata.get("confidence", 0))
            existing_confidence = highest_confidence_conflict["existing_item"].metadata.get("confidence", 0)
            new_confidence = new_item.get("metadata", {}).get("confidence", 0)
            
            if new_confidence > existing_confidence:
                return {
                    "action": "update",
                    "target_id": highest_confidence_conflict["existing_item"].id
                }
            else:
                return {"action": "ignore"}
                
        elif self.conflict_strategy == "recency_based":
            # 基于时间的冲突解决，总是使用最新的
            return {
                "action": "update",
                "target_id": conflicts[0]["existing_item"].id
            }
            
        elif self.conflict_strategy == "merge":
            # 合并冲突的知识
            # 实现合并逻辑
            pass
            
        return {"action": "ignore"}
    
    async def _add_new_knowledge(self, kb_id: str, item: Dict[str, Any]) -> None:
        """添加新知识到知识库"""
        # 1. 格式化为文档块
        chunk = self._format_as_document_chunk(kb_id, item)
        
        # 2. 添加到向量数据库
        await self.kb_service.add_chunk(chunk)
    
    async def _update_existing_knowledge(self, kb_id: str, chunk_id: str, new_item: Dict[str, Any]) -> None:
        """更新现有知识"""
        # 1. 格式化为文档块
        updated_chunk = self._format_as_document_chunk(kb_id, new_item, chunk_id)
        
        # 2. 更新向量数据库中的条目
        await self.kb_service.update_chunk(updated_chunk)
    
    def _format_as_document_chunk(self, kb_id: str, item: Dict[str, Any], chunk_id: str = None) -> DocumentChunk:
        """将知识项格式化为文档块"""
        # 生成内容
        content = self._generate_chunk_content(item)
        
        # 创建文档块
        chunk = DocumentChunk(
            id=chunk_id or str(uuid.uuid4()),
            document_id=f"auto_generated_{uuid.uuid4().hex[:8]}",
            kb_id=kb_id,
            content=content,
            chunk_index=0,
            metadata={
                "source_type": "auto_extracted",
                "knowledge_type": item["type"],
                "extraction_time": datetime.now().isoformat(),
                "confidence": item.get("metadata", {}).get("confidence", 0.7),
                **item.get("metadata", {})
            }
        )
        
        return chunk
    
    def _generate_chunk_content(self, item: Dict[str, Any]) -> str:
        """根据知识项类型生成结构化内容"""
        if item["type"] == "task_pattern":
            return f"""目标: {item['goal']}
成功方法: {json.dumps(item['successful_approach'], ensure_ascii=False)}
结果: {item['result']}"""
            
        elif item["type"] == "intermediate_insight":
            return f"""步骤: {item['step']}
见解: {item['insight']}"""
            
        # 其他类型的处理...
        return json.dumps(item, ensure_ascii=False)
```

### 5.3 学习触发器

```python
class LearningTrigger:
    """学习触发器，决定何时启动知识提取和整合流程"""
    
    def __init__(self, knowledge_extractor: KnowledgeExtractor, knowledge_integrator: KnowledgeIntegrator):
        self.extractor = knowledge_extractor
        self.integrator = knowledge_integrator
        self.trigger_conditions = {
            "task_completion": self._check_task_completion,
            "error_occurrence": self._check_error_occurrence,
            "new_pattern_detected": self._check_new_pattern,
            "scheduled": self._check_scheduled
        }
        self.last_learning_time = {}  # 记录每个知识库上次学习时间
    
    async def check_triggers(self, event_type: str, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查是否触发学习过程"""
        if event_type not in self.trigger_conditions:
            return False
            
        # 检查触发条件
        should_trigger = await self.trigger_conditions[event_type](event_data, kb_id)
        
        if should_trigger:
            # 执行知识提取和整合
            await self._execute_learning_cycle(event_type, event_data, kb_id)
            return True
            
        return False
    
    async def _execute_learning_cycle(self, source_type: str, source_data: Dict[str, Any], kb_id: str) -> None:
        """执行完整的学习周期"""
        try:
            # 1. 提取知识
            knowledge_items = await self.extractor.extract_knowledge(source_type, source_data)
            
            if not knowledge_items:
                logger.info(f"未从{source_type}提取到有价值的知识")
                return
                
            # 2. 整合知识
            stats = await self.integrator.integrate_knowledge(kb_id, knowledge_items)
            
            # 3. 更新学习时间
            self.last_learning_time[kb_id] = datetime.now()
            
            logger.info(f"知识学习周期完成: {stats}")
            
        except Exception as e:
            logger.error(f"学习周期执行失败: {str(e)}")
    
    async def _check_task_completion(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查任务完成触发条件"""
        # 实现任务完成触发逻辑
        return event_data.get("status") == "completed"
    
    async def _check_error_occurrence(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查错误发生触发条件"""
        # 实现错误触发逻辑
        return "error" in event_data and event_data["error"].get("should_learn", False)
    
    async def _check_new_pattern(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查新模式检测触发条件"""
        # 实现新模式检测逻辑
        return False
    
    async def _check_scheduled(self, event_data: Dict[str, Any], kb_id: str) -> bool:
        """检查定时触发条件"""
        # 检查上次学习时间，确保不会过于频繁
        last_time = self.last_learning_time.get(kb_id)
        if not last_time:
            return True
            
        # 至少间隔1小时
        min_interval = timedelta(hours=1)
        return datetime.now() - last_time > min_interval
```
