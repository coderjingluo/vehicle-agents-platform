"""
向量存储服务

负责向量数据库的管理、文档向量化和语义搜索功能
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import chromadb
from chromadb.config import Settings
import numpy as np

# 可选导入 sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False

from app.core.config import get_settings
from app.core.llm_client import LLMClientManager
from loguru import logger


class VectorService:
    """向量存储服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_manager = LLMClientManager()
        
        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.PersistentClient(
            path=self.settings.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化本地嵌入模型（作为备用）
        self.local_embedding_model = None
        self._load_local_embedding_model()
    
    def _load_local_embedding_model(self):
        """加载本地嵌入模型"""
        try:
            if not HAS_SENTENCE_TRANSFORMERS:
                logger.warning("sentence_transformers 未安装，将使用模拟嵌入向量")
                return
                
            # 使用中文友好的嵌入模型
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            self.local_embedding_model = SentenceTransformer(model_name)
            logger.info(f"成功加载本地嵌入模型: {model_name}")
        except Exception as e:
            logger.warning(f"加载本地嵌入模型失败: {e}")
            self.local_embedding_model = None
    
    async def create_collection(
        self,
        collection_name: str,
        embedding_model: str = "text-embedding-ada-002",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建向量集合"""
        try:
            # 检查集合是否已存在
            try:
                existing_collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"集合已存在: {collection_name}")
                return True
            except ValueError:
                # 集合不存在，创建新集合
                pass
            
            # 创建集合
            collection_metadata = {
                "embedding_model": embedding_model,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata=collection_metadata,
                embedding_function=None  # 我们手动管理嵌入
            )
            
            logger.info(f"成功创建向量集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建向量集合失败 {collection_name}: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> bool:
        """删除向量集合"""
        try:
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"成功删除向量集合: {collection_name}")
            return True
            
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return False
        except Exception as e:
            logger.error(f"删除向量集合失败 {collection_name}: {e}")
            raise
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadata: Dict[str, Any],
        embedding_model: str = "text-embedding-ada-002"
    ) -> List[str]:
        """添加文档到向量集合"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 生成向量
            embeddings = await self._generate_embeddings(documents, embedding_model)
            
            # 生成文档ID
            document_ids = [f"{metadata['document_id']}_{i}" for i in range(len(documents))]
            
            # 准备元数据
            metadatas = []
            for i, doc in enumerate(documents):
                doc_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "chunk_text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "embedding_model": embedding_model,
                    "created_at": datetime.utcnow().isoformat()
                }
                metadatas.append(doc_metadata)
            
            # 添加到集合
            collection.add(
                ids=document_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"成功添加 {len(documents)} 个文档块到集合 {collection_name}")
            return document_ids
            
        except Exception as e:
            logger.error(f"添加文档失败 {collection_name}: {e}")
            raise
    
    async def _generate_embeddings(
        self,
        texts: List[str],
        embedding_model: str
    ) -> List[List[float]]:
        """生成文本嵌入向量"""
        try:
            # 尝试使用API生成嵌入
            if embedding_model.startswith("text-embedding"):
                try:
                    embeddings = await self._generate_openai_embeddings(texts, embedding_model)
                    return embeddings
                except Exception as e:
                    logger.warning(f"API嵌入生成失败，使用本地模型: {e}")
            
            # 使用本地模型生成嵌入
            if self.local_embedding_model:
                embeddings = self.local_embedding_model.encode(texts)
                return embeddings.tolist()
            else:
                # 如果没有可用的嵌入模型，使用简单的向量模拟
                logger.warning("使用模拟嵌入向量（开发环境）")
                return self._generate_mock_embeddings(texts)
                
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    async def _generate_openai_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """使用OpenAI API生成嵌入"""
        try:
            # 分批处理，避免超过API限制
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # 这里应该调用实际的OpenAI嵌入API
                # 暂时使用模拟实现
                batch_embeddings = await self._mock_openai_embeddings(batch_texts, model)
                all_embeddings.extend(batch_embeddings)
                
                # 避免频率限制
                if len(texts) > batch_size:
                    await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI嵌入生成失败: {e}")
            raise
    
    async def _mock_openai_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """模拟OpenAI嵌入（用于开发测试）"""
        # 在实际项目中，这里应该调用真实的OpenAI API
        # 这里使用本地模型生成嵌入作为替代
        if self.local_embedding_model:
            embeddings = self.local_embedding_model.encode(texts)
            return embeddings.tolist()
        else:
            return self._generate_mock_embeddings(texts)
    
    def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成模拟嵌入向量（用于测试和开发环境）"""
        # 生成基于文本内容的简单嵌入向量
        dimension = 384  # paraphrase-multilingual-MiniLM-L12-v2的维度
        embeddings = []
        
        for text in texts:
            # 基于文本内容生成稳定的向量（而不是随机向量）
            # 这样相同的文本总是产生相同的向量
            np.random.seed(hash(text) % (2**32))
            embedding = np.random.random(dimension).tolist()
            embeddings.append(embedding)
        
        return embeddings
    
    async def search_documents(
        self,
        collection_names: List[str],
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        try:
            all_results = []
            
            for collection_name in collection_names:
                try:
                    collection = self.chroma_client.get_collection(collection_name)
                    
                    # 获取集合的嵌入模型信息
                    collection_metadata = collection.metadata or {}
                    embedding_model = collection_metadata.get("embedding_model", "text-embedding-ada-002")
                    
                    # 生成查询向量
                    query_embedding = await self._generate_embeddings([query], embedding_model)
                    
                    # 执行搜索
                    results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=limit,
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # 处理结果
                    for i in range(len(results["ids"][0])):
                        distance = results["distances"][0][i]
                        similarity_score = 1 - distance  # 转换为相似度分数
                        
                        if similarity_score >= similarity_threshold:
                            result = {
                                "id": results["ids"][0][i],
                                "content": results["documents"][0][i],
                                "metadata": results["metadatas"][0][i],
                                "similarity_score": similarity_score,
                                "collection_name": collection_name
                            }
                            all_results.append(result)
                            
                except ValueError:
                    logger.warning(f"集合不存在: {collection_name}")
                    continue
                except Exception as e:
                    logger.error(f"搜索集合失败 {collection_name}: {e}")
                    continue
            
            # 按相似度排序并限制结果数量
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            raise
    
    async def delete_documents(
        self,
        collection_name: str,
        document_ids: List[str]
    ) -> bool:
        """从集合中删除文档"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 检查哪些ID实际存在
            existing_results = collection.get(ids=document_ids, include=[])
            existing_ids = existing_results["ids"]
            
            if existing_ids:
                collection.delete(ids=existing_ids)
                logger.info(f"成功删除 {len(existing_ids)} 个文档块从集合 {collection_name}")
            else:
                logger.warning(f"没有找到要删除的文档ID: {document_ids}")
            
            return True
            
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return False
        except Exception as e:
            logger.error(f"删除文档失败 {collection_name}: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """获取集合统计信息"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 获取集合中的文档数量
            count_result = collection.count()
            
            # 获取集合元数据
            metadata = collection.metadata or {}
            
            return {
                "collection_name": collection_name,
                "document_count": count_result,
                "embedding_model": metadata.get("embedding_model", "unknown"),
                "created_at": metadata.get("created_at", "unknown"),
                "metadata": metadata
            }
            
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return None
        except Exception as e:
            logger.error(f"获取集合统计失败 {collection_name}: {e}")
            raise
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """列出所有集合"""
        try:
            collections = self.chroma_client.list_collections()
            
            collection_info = []
            for collection in collections:
                stats = await self.get_collection_stats(collection.name)
                if stats:
                    collection_info.append(stats)
            
            return collection_info
            
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            raise
    
    async def update_document_metadata(
        self,
        collection_name: str,
        document_ids: List[str],
        metadata: Dict[str, Any]
    ) -> bool:
        """更新文档元数据"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 获取现有元数据
            existing_data = collection.get(ids=document_ids, include=["metadatas"])
            
            if not existing_data["ids"]:
                logger.warning(f"没有找到要更新的文档: {document_ids}")
                return False
            
            # 更新元数据
            updated_metadatas = []
            for existing_metadata in existing_data["metadatas"]:
                updated_metadata = {**existing_metadata, **metadata}
                updated_metadata["updated_at"] = datetime.utcnow().isoformat()
                updated_metadatas.append(updated_metadata)
            
            # 应用更新
            collection.update(
                ids=existing_data["ids"],
                metadatas=updated_metadatas
            )
            
            logger.info(f"成功更新 {len(existing_data['ids'])} 个文档的元数据")
            return True
            
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return False
        except Exception as e:
            logger.error(f"更新文档元数据失败 {collection_name}: {e}")
            raise
    
    async def similarity_search_with_score(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """带分数的相似度搜索"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 获取嵌入模型信息
            collection_metadata = collection.metadata or {}
            embedding_model = collection_metadata.get("embedding_model", "text-embedding-ada-002")
            
            # 生成查询向量
            query_embedding = await self._generate_embeddings([query], embedding_model)
            
            # 构建查询参数
            query_params = {
                "query_embeddings": query_embedding,
                "n_results": limit,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # 添加元数据过滤
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            # 执行搜索
            results = collection.query(**query_params)
            
            # 处理结果
            search_results = []
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                similarity_score = 1 - distance
                
                search_results.append((
                    results["documents"][0][i],
                    similarity_score,
                    results["metadatas"][0][i]
                ))
            
            return search_results
            
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return []
        except Exception as e:
            logger.error(f"相似度搜索失败 {collection_name}: {e}")
            raise
    
    async def get_document_by_id(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取文档"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            results = collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"]:
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            else:
                return None
                
        except ValueError:
            logger.warning(f"集合不存在: {collection_name}")
            return None
        except Exception as e:
            logger.error(f"获取文档失败 {collection_name}: {e}")
            raise
    
    async def backup_collection(
        self,
        collection_name: str,
        backup_path: str
    ) -> bool:
        """备份集合"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 获取所有数据
            all_data = collection.get(include=["documents", "metadatas", "embeddings"])
            
            # 添加集合元数据
            backup_data = {
                "collection_name": collection_name,
                "collection_metadata": collection.metadata,
                "data": all_data,
                "backup_timestamp": datetime.utcnow().isoformat()
            }
            
            # 保存到文件
            import json
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功备份集合 {collection_name} 到 {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"备份集合失败 {collection_name}: {e}")
            raise
    
    async def restore_collection(
        self,
        backup_path: str,
        new_collection_name: Optional[str] = None
    ) -> bool:
        """从备份恢复集合"""
        try:
            # 读取备份数据
            import json
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            collection_name = new_collection_name or backup_data["collection_name"]
            
            # 创建集合
            await self.create_collection(
                collection_name,
                metadata=backup_data.get("collection_metadata", {})
            )
            
            collection = self.chroma_client.get_collection(collection_name)
            
            # 恢复数据
            data = backup_data["data"]
            if data["ids"]:
                collection.add(
                    ids=data["ids"],
                    documents=data["documents"],
                    metadatas=data["metadatas"],
                    embeddings=data["embeddings"]
                )
            
            logger.info(f"成功恢复集合 {collection_name} 从 {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"恢复集合失败: {e}")
            raise 