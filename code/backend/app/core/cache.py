"""
Redis缓存策略管理器
提供智能缓存、缓存失效、缓存预热等功能
"""

import json
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import asyncio
from loguru import logger

from app.core.config import settings


class CacheKeyGenerator:
    """缓存键生成器"""
    
    @staticmethod
    def generate_key(prefix: str, **kwargs) -> str:
        """生成缓存键"""
        # 对参数进行排序并序列化
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True, ensure_ascii=False)
        
        # 生成哈希值以避免键过长
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"{prefix}:{params_hash}"
    
    @staticmethod
    def workflow_key(workflow_id: str) -> str:
        """工作流缓存键"""
        return f"workflow:{workflow_id}"
    
    @staticmethod
    def agent_result_key(agent_type: str, input_hash: str) -> str:
        """智能体结果缓存键"""
        return f"agent:{agent_type}:{input_hash}"
    
    @staticmethod
    def knowledge_search_key(query: str, knowledge_base_id: str) -> str:
        """知识库搜索结果缓存键"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"knowledge:search:{knowledge_base_id}:{query_hash}"
    
    @staticmethod
    def model_stats_key(model_id: str) -> str:
        """模型统计缓存键"""
        return f"model:stats:{model_id}"


class CacheStrategy:
    """缓存策略配置"""
    
    # 缓存时间配置（秒）
    CACHE_TTL = {
        "workflow_status": 300,        # 工作流状态: 5分钟
        "agent_result": 3600,          # 智能体结果: 1小时
        "knowledge_search": 1800,      # 知识库搜索: 30分钟
        "model_stats": 900,            # 模型统计: 15分钟
        "system_health": 60,           # 系统健康: 1分钟
        "user_session": 86400,         # 用户会话: 24小时
        "hot_data": 7200,              # 热点数据: 2小时
    }
    
    # 缓存级别配置
    CACHE_LEVELS = {
        "L1": {"ttl": 300, "max_size": 1000},     # 内存缓存
        "L2": {"ttl": 3600, "max_size": 10000},   # Redis缓存
        "L3": {"ttl": 86400, "max_size": 100000}, # 持久化缓存
    }


class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        self.key_generator = CacheKeyGenerator()
    
    async def initialize(self):
        """初始化缓存连接"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis缓存连接成功")
            
        except Exception as e:
            logger.error(f"Redis缓存连接失败: {e}")
            self.redis_client = None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存数据"""
        try:
            # 先检查本地缓存
            if key in self.local_cache:
                cache_entry = self.local_cache[key]
                if self._is_valid_cache_entry(cache_entry):
                    self.cache_stats["hits"] += 1
                    return cache_entry["data"]
                else:
                    del self.local_cache[key]
            
            # 检查Redis缓存
            if self.redis_client:
                data = await self.redis_client.get(key)
                if data is not None:
                    self.cache_stats["hits"] += 1
                    try:
                        return json.loads(data)
                    except json.JSONDecodeError:
                        return data
            
            self.cache_stats["misses"] += 1
            return default
            
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {e}")
            self.cache_stats["misses"] += 1
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        cache_level: str = "L2"
    ) -> bool:
        """设置缓存数据"""
        try:
            if ttl is None:
                ttl = CacheStrategy.CACHE_TTL.get("hot_data", 3600)
            
            # 序列化数据
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            # 设置Redis缓存
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
            
            # 设置本地缓存（如果配置允许）
            if cache_level == "L1":
                self.local_cache[key] = {
                    "data": value,
                    "expires_at": datetime.now() + timedelta(seconds=ttl),
                    "created_at": datetime.now()
                }
                
                # 清理过期的本地缓存
                await self._cleanup_local_cache()
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        try:
            # 删除本地缓存
            if key in self.local_cache:
                del self.local_cache[key]
            
            # 删除Redis缓存
            if self.redis_client:
                await self.redis_client.delete(key)
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        try:
            if not self.redis_client:
                return 0
            
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.cache_stats["deletes"] += deleted
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"模式删除缓存失败 {pattern}: {e}")
            return 0
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable,
        ttl: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """获取缓存或执行函数并缓存结果"""
        # 先尝试获取缓存
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 执行函数获取数据
        if asyncio.iscoroutinefunction(factory):
            value = await factory(*args, **kwargs)
        else:
            value = factory(*args, **kwargs)
        
        # 缓存结果
        await self.set(key, value, ttl)
        return value
    
    async def warm_up_cache(self, warm_up_configs: List[Dict]):
        """缓存预热"""
        logger.info("开始缓存预热...")
        
        for config in warm_up_configs:
            try:
                key = config["key"]
                factory = config["factory"]
                ttl = config.get("ttl")
                args = config.get("args", [])
                kwargs = config.get("kwargs", {})
                
                # 检查是否需要预热
                cached_value = await self.get(key)
                if cached_value is None:
                    if asyncio.iscoroutinefunction(factory):
                        value = await factory(*args, **kwargs)
                    else:
                        value = factory(*args, **kwargs)
                    
                    await self.set(key, value, ttl)
                    logger.debug(f"缓存预热完成: {key}")
                
            except Exception as e:
                logger.error(f"缓存预热失败 {config.get('key', 'unknown')}: {e}")
        
        logger.info("缓存预热完成")
    
    async def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        stats = self.cache_stats.copy()
        
        # 添加命中率
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
        
        # 添加Redis信息
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats["redis_memory"] = redis_info.get("used_memory_human", "N/A")
                stats["redis_connected"] = True
            except:
                stats["redis_connected"] = False
        else:
            stats["redis_connected"] = False
        
        # 添加本地缓存信息
        stats["local_cache_size"] = len(self.local_cache)
        
        return stats
    
    def _is_valid_cache_entry(self, cache_entry: Dict) -> bool:
        """检查本地缓存条目是否有效"""
        return datetime.now() < cache_entry["expires_at"]
    
    async def _cleanup_local_cache(self):
        """清理过期的本地缓存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self.local_cache.items()
            if current_time >= entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
    
    async def close(self):
        """关闭缓存连接"""
        if self.redis_client:
            await self.redis_client.close()


def cache_result(
    key_prefix: str, 
    ttl: Optional[int] = None,
    cache_level: str = "L2"
):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = CacheKeyGenerator.generate_key(
                key_prefix, 
                args=args, 
                kwargs=kwargs
            )
            
            # 获取缓存管理器实例
            cache_manager = SmartCacheManager()
            await cache_manager.initialize()
            
            try:
                # 尝试从缓存获取
                cached_result = await cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 缓存结果
                await cache_manager.set(cache_key, result, ttl, cache_level)
                return result
                
            finally:
                await cache_manager.close()
        
        return wrapper
    return decorator


# 全局缓存管理器实例
cache_manager = SmartCacheManager() 