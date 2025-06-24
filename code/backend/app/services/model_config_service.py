"""
模型配置管理服务

负责多模型配置、API密钥管理、连接测试、使用统计等功能
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from openai import AsyncOpenAI
import anthropic
import httpx

from app.models.model_config import (
    ModelConfig,
    ModelProvider,
    ModelType,
    ModelStatus,
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelTestRequest,
    ModelTestResponse,
    ModelUsageStats,
    ModelProviderInfo,
    ModelConfigList
)
from app.core.config import get_settings
from app.core.llm_client import LLMClientManager
from loguru import logger


class ModelConfigService:
    """模型配置管理服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cipher_suite = Fernet(self.settings.ENCRYPTION_KEY.encode())
        self.llm_manager = LLMClientManager()
        
        # 模型提供商信息
        self.provider_info = {
            ModelProvider.OPENAI: ModelProviderInfo(
                provider=ModelProvider.OPENAI,
                display_name="OpenAI",
                description="OpenAI GPT系列模型，包括GPT-4、GPT-3.5等",
                supported_types=[ModelType.CHAT, ModelType.EMBEDDING, ModelType.VISION],
                available_models=[
                    {"name": "gpt-4-turbo", "type": "chat", "context_length": 128000},
                    {"name": "gpt-4", "type": "chat", "context_length": 8192},
                    {"name": "gpt-3.5-turbo", "type": "chat", "context_length": 16385},
                    {"name": "text-embedding-ada-002", "type": "embedding", "dimensions": 1536},
                    {"name": "gpt-4-vision-preview", "type": "vision", "context_length": 128000},
                ],
                default_config={
                    "api_base": "https://api.openai.com/v1",
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                pricing_info={
                    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                    "gpt-4": {"input": 0.03, "output": 0.06},
                    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
                },
                documentation_url="https://platform.openai.com/docs"
            ),
            ModelProvider.ANTHROPIC: ModelProviderInfo(
                provider=ModelProvider.ANTHROPIC,
                display_name="Anthropic",
                description="Anthropic Claude系列模型，擅长推理和安全性",
                supported_types=[ModelType.CHAT],
                available_models=[
                    {"name": "claude-3-opus-20240229", "type": "chat", "context_length": 200000},
                    {"name": "claude-3-sonnet-20240229", "type": "chat", "context_length": 200000},
                    {"name": "claude-3-haiku-20240307", "type": "chat", "context_length": 200000},
                ],
                default_config={
                    "api_base": "https://api.anthropic.com",
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                pricing_info={
                    "claude-3-opus": {"input": 0.015, "output": 0.075},
                    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
                    "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
                },
                documentation_url="https://docs.anthropic.com"
            ),
            ModelProvider.DEEPSEEK: ModelProviderInfo(
                provider=ModelProvider.DEEPSEEK,
                display_name="DeepSeek",
                description="DeepSeek智能体和推理模型",
                supported_types=[ModelType.CHAT],
                available_models=[
                    {"name": "deepseek-chat", "type": "chat", "context_length": 32768},
                    {"name": "deepseek-coder", "type": "chat", "context_length": 16384},
                ],
                default_config={
                    "api_base": "https://api.deepseek.com/v1",
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                pricing_info={
                    "deepseek-chat": {"input": 0.0014, "output": 0.002},
                    "deepseek-coder": {"input": 0.0014, "output": 0.002}
                },
                documentation_url="https://platform.deepseek.com/api-docs"
            )
        }
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
    
    async def create_model_config(
        self,
        config_data: ModelConfigCreate,
        db: AsyncSession
    ) -> ModelConfig:
        """创建模型配置"""
        try:
            # 检查名称是否已存在
            existing_config = await db.execute(
                select(ModelConfig).where(ModelConfig.name == config_data.name)
            )
            if existing_config.scalar_one_or_none():
                raise ValueError(f"模型配置名称 '{config_data.name}' 已存在")
            
            # 加密API密钥
            encrypted_key = self._encrypt_api_key(config_data.api_key.get_secret_value())
            
            # 创建配置
            config = ModelConfig(
                name=config_data.name,
                display_name=config_data.display_name,
                description=config_data.description,
                provider=config_data.provider.value,
                model_type=config_data.model_type.value,
                model_name=config_data.model_name,
                version=config_data.version,
                api_base=config_data.api_base,
                api_key=encrypted_key,
                api_version=config_data.api_version,
                organization=config_data.organization,
                max_tokens=config_data.max_tokens,
                temperature=config_data.temperature,
                top_p=config_data.top_p,
                frequency_penalty=config_data.frequency_penalty,
                presence_penalty=config_data.presence_penalty,
                config=config_data.config,
                headers=config_data.headers,
                rate_limit_rpm=config_data.rate_limit_rpm,
                rate_limit_tpm=config_data.rate_limit_tpm,
                daily_quota=config_data.daily_quota,
                monthly_quota=config_data.monthly_quota,
                is_default=config_data.is_default,
                priority=config_data.priority,
                status=ModelStatus.INACTIVE.value
            )
            
            db.add(config)
            
            # 如果设置为默认模型，需要取消其他默认模型
            if config_data.is_default:
                await self._unset_other_defaults(
                    config_data.model_type, config.id, db
                )
            
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"成功创建模型配置: {config.name}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建模型配置失败: {e}")
            raise
    
    async def _unset_other_defaults(
        self,
        model_type: ModelType,
        exclude_id: str,
        db: AsyncSession
    ):
        """取消其他默认模型设置"""
        await db.execute(
            select(ModelConfig).where(
                and_(
                    ModelConfig.model_type == model_type.value,
                    ModelConfig.id != exclude_id,
                    ModelConfig.is_default == True
                )
            ).update({"is_default": False})
        )
    
    async def get_model_config(
        self,
        config_id: str,
        db: AsyncSession,
        decrypt_key: bool = False
    ) -> Optional[ModelConfig]:
        """获取模型配置"""
        try:
            result = await db.execute(
                select(ModelConfig).where(ModelConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            
            if config and decrypt_key:
                # 临时解密API密钥（仅在需要时）
                config._decrypted_key = self._decrypt_api_key(config.api_key)
            
            return config
            
        except Exception as e:
            logger.error(f"获取模型配置失败: {e}")
            raise
    
    async def list_model_configs(
        self,
        db: AsyncSession,
        provider: Optional[ModelProvider] = None,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> ModelConfigList:
        """获取模型配置列表"""
        try:
            # 构建查询条件
            conditions = []
            if provider:
                conditions.append(ModelConfig.provider == provider.value)
            if model_type:
                conditions.append(ModelConfig.model_type == model_type.value)
            if status:
                conditions.append(ModelConfig.status == status.value)
            
            # 获取总数
            count_query = select(func.count(ModelConfig.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 获取列表
            list_query = select(ModelConfig).order_by(
                desc(ModelConfig.priority),
                desc(ModelConfig.created_at)
            )
            if conditions:
                list_query = list_query.where(and_(*conditions))
            
            list_query = list_query.offset(offset).limit(limit)
            
            result = await db.execute(list_query)
            configs = result.scalars().all()
            
            # 获取统计信息
            stats_query = select(
                ModelConfig.status,
                func.count(ModelConfig.id),
                func.avg(ModelConfig.avg_response_time),
                func.sum(ModelConfig.total_requests),
                func.sum(ModelConfig.total_tokens)
            ).group_by(ModelConfig.status)
            
            stats_result = await db.execute(stats_query)
            stats = {
                "by_status": {},
                "total_requests": 0,
                "total_tokens": 0,
                "avg_response_time": 0.0
            }
            
            for row in stats_result.all():
                stats["by_status"][row[0]] = {
                    "count": row[1],
                    "avg_response_time": row[2] or 0.0
                }
                stats["total_requests"] += row[3] or 0
                stats["total_tokens"] += row[4] or 0
            
            return ModelConfigList(
                total=total,
                models=configs,
                providers=list(self.provider_info.values()),
                stats=stats
            )
            
        except Exception as e:
            logger.error(f"获取模型配置列表失败: {e}")
            raise
    
    async def update_model_config(
        self,
        config_id: str,
        update_data: ModelConfigUpdate,
        db: AsyncSession
    ) -> Optional[ModelConfig]:
        """更新模型配置"""
        try:
            config = await self.get_model_config(config_id, db)
            if not config:
                return None
            
            # 更新字段
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # 处理API密钥加密
            if "api_key" in update_dict:
                update_dict["api_key"] = self._encrypt_api_key(
                    update_dict["api_key"].get_secret_value()
                )
            
            # 处理默认模型设置
            if update_dict.get("is_default"):
                await self._unset_other_defaults(
                    ModelType(config.model_type), config.id, db
                )
            
            for field, value in update_dict.items():
                setattr(config, field, value)
            
            config.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"成功更新模型配置: {config.name}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新模型配置失败: {e}")
            raise
    
    async def delete_model_config(
        self,
        config_id: str,
        db: AsyncSession
    ) -> bool:
        """删除模型配置"""
        try:
            config = await self.get_model_config(config_id, db)
            if not config:
                return False
            
            await db.delete(config)
            await db.commit()
            
            logger.info(f"成功删除模型配置: {config.name}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除模型配置失败: {e}")
            raise
    
    async def test_model_connection(
        self,
        config_id: str,
        test_request: ModelTestRequest,
        db: AsyncSession
    ) -> ModelTestResponse:
        """测试模型连接"""
        start_time = datetime.utcnow()
        
        try:
            config = await self.get_model_config(config_id, db, decrypt_key=True)
            if not config:
                raise ValueError(f"模型配置不存在: {config_id}")
            
            # 更新测试状态
            config.status = ModelStatus.TESTING.value
            config.last_test_at = start_time
            await db.commit()
            
            # 执行测试
            response = None
            error = None
            token_count = None
            
            try:
                # 根据提供商执行不同的测试
                if config.provider == ModelProvider.OPENAI.value:
                    response = await self._test_openai_model(config, test_request)
                elif config.provider == ModelProvider.ANTHROPIC.value:
                    response = await self._test_anthropic_model(config, test_request)
                elif config.provider == ModelProvider.DEEPSEEK.value:
                    response = await self._test_deepseek_model(config, test_request)
                else:
                    raise ValueError(f"不支持的模型提供商: {config.provider}")
                
                # 估算token数量
                token_count = len(response.split()) * 1.3 if response else None
                
                # 更新成功状态
                config.status = ModelStatus.ACTIVE.value
                config.last_test_status = "success"
                config.last_test_error = None
                
            except Exception as e:
                error = str(e)
                config.status = ModelStatus.ERROR.value
                config.last_test_status = "failed"
                config.last_test_error = error
                logger.error(f"模型测试失败 {config.name}: {e}")
            
            # 计算响应时间
            response_time = (datetime.utcnow() - start_time).total_seconds()
            config.avg_response_time = (
                (config.avg_response_time * config.total_requests + response_time) /
                (config.total_requests + 1)
            ) if config.total_requests > 0 else response_time
            
            # 更新统计
            config.total_requests += 1
            if token_count:
                config.total_tokens += int(token_count)
            
            await db.commit()
            
            return ModelTestResponse(
                model_id=config.id,
                success=error is None,
                response=response,
                error=error,
                response_time=response_time,
                token_count=int(token_count) if token_count else None,
                test_timestamp=start_time
            )
            
        except Exception as e:
            logger.error(f"测试模型连接失败: {e}")
            raise
    
    async def _test_openai_model(
        self,
        config: ModelConfig,
        test_request: ModelTestRequest
    ) -> str:
        """测试OpenAI模型"""
        client = AsyncOpenAI(
            api_key=config._decrypted_key,
            base_url=config.api_base,
            organization=config.organization,
            timeout=test_request.timeout
        )
        
        if config.model_type == ModelType.CHAT.value:
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": test_request.test_message}],
                max_tokens=min(config.max_tokens, 100),
                temperature=config.temperature
            )
            return response.choices[0].message.content
        
        elif config.model_type == ModelType.EMBEDDING.value:
            response = await client.embeddings.create(
                model=config.model_name,
                input=test_request.test_message
            )
            return f"Embedding generated with {len(response.data[0].embedding)} dimensions"
        
        else:
            raise ValueError(f"不支持的模型类型: {config.model_type}")
    
    async def _test_anthropic_model(
        self,
        config: ModelConfig,
        test_request: ModelTestRequest
    ) -> str:
        """测试Anthropic模型"""
        client = anthropic.AsyncAnthropic(
            api_key=config._decrypted_key,
            base_url=config.api_base,
            timeout=test_request.timeout
        )
        
        response = await client.messages.create(
            model=config.model_name,
            max_tokens=min(config.max_tokens, 100),
            temperature=config.temperature,
            messages=[{"role": "user", "content": test_request.test_message}]
        )
        
        return response.content[0].text
    
    async def _test_deepseek_model(
        self,
        config: ModelConfig,
        test_request: ModelTestRequest
    ) -> str:
        """测试DeepSeek模型"""
        headers = {
            "Authorization": f"Bearer {config._decrypted_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config.model_name,
            "messages": [{"role": "user", "content": test_request.test_message}],
            "max_tokens": min(config.max_tokens, 100),
            "temperature": config.temperature
        }
        
        async with httpx.AsyncClient(timeout=test_request.timeout) as client:
            response = await client.post(
                f"{config.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def get_model_usage_stats(
        self,
        config_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Optional[ModelUsageStats]:
        """获取模型使用统计"""
        try:
            config = await self.get_model_config(config_id, db)
            if not config:
                return None
            
            # 这里简化实现，实际项目中可能需要更复杂的统计逻辑
            # 可以从日志或单独的统计表中获取数据
            
            now = datetime.utcnow()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # 模拟统计数据（实际实现中应从数据库或日志中获取）
            daily_factor = min(config.total_requests / 30, 1000)
            weekly_factor = daily_factor * 7
            monthly_factor = daily_factor * 30
            
            return ModelUsageStats(
                model_id=config.id,
                model_name=config.display_name,
                daily_requests=int(daily_factor),
                daily_tokens=int(daily_factor * 100),
                daily_cost=round(daily_factor * 0.01, 4),
                weekly_requests=int(weekly_factor),
                weekly_tokens=int(weekly_factor * 100),
                weekly_cost=round(weekly_factor * 0.01, 4),
                monthly_requests=int(monthly_factor),
                monthly_tokens=int(monthly_factor * 100),
                monthly_cost=round(monthly_factor * 0.01, 4),
                avg_response_time=config.avg_response_time,
                success_rate=0.95,  # 模拟成功率
                error_rate=0.05,    # 模拟错误率
                usage_trend=[
                    {"date": str((now - timedelta(days=i)).date()), "requests": max(0, int(daily_factor * (1 + 0.1 * (i % 3))))}
                    for i in range(days)
                ][::-1]
            )
            
        except Exception as e:
            logger.error(f"获取模型统计失败: {e}")
            raise
    
    async def get_provider_info(self, provider: ModelProvider) -> Optional[ModelProviderInfo]:
        """获取模型提供商信息"""
        return self.provider_info.get(provider)
    
    async def get_default_model(
        self,
        model_type: ModelType,
        db: AsyncSession
    ) -> Optional[ModelConfig]:
        """获取默认模型配置"""
        try:
            result = await db.execute(
                select(ModelConfig).where(
                    and_(
                        ModelConfig.model_type == model_type.value,
                        ModelConfig.is_default == True,
                        ModelConfig.status == ModelStatus.ACTIVE.value
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取默认模型失败: {e}")
            raise 