"""
KunlunSec AI Platform - 模型配置模型

定义模型配置相关的数据库模型和方法。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, 
    ForeignKey, Integer, Enum, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class ModelProvider(str, enum.Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"

class ModelConfig(Base):
    """模型配置模型"""
    
    __tablename__ = "model_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 模型信息
    provider = Column(Enum(ModelProvider), nullable=False)
    model_id = Column(String(255), nullable=False)  # 如gpt-4, claude-3-opus等
    
    # API配置
    api_key = Column(Text, nullable=True)  # 加密存储
    api_base = Column(String(255), nullable=True)
    api_version = Column(String(50), nullable=True)
    
    # 请求参数
    default_parameters = Column(JSON, default={})  # 如temperature, max_tokens等
    
    # 能力标志
    supports_vision = Column(Boolean, default=False)
    supports_streaming = Column(Boolean, default=True)
    supports_function_calling = Column(Boolean, default=False)
    
    # 统计信息
    usage_count = Column(Integer, default=0)
    average_latency = Column(Float, nullable=True)  # 平均响应时间（秒）
    
    # 权限和状态
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User", backref="created_models")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    def update_usage_stats(self, latency: float) -> None:
        """
        更新使用统计信息
        
        参数:
            latency: 请求延迟（秒）
        """
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        
        if self.average_latency is None:
            self.average_latency = latency
        else:
            # 使用移动平均
            self.average_latency = (self.average_latency * 0.9) + (latency * 0.1)
    
    def get_config_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        获取配置字典
        
        参数:
            include_secrets: 是否包含敏感信息（API密钥等）
            
        返回:
            Dict[str, Any]: 配置字典
        """
        config = {
            "id": str(self.id),
            "name": self.name,
            "provider": self.provider,
            "model_id": self.model_id,
            "api_base": self.api_base,
            "api_version": self.api_version,
            "default_parameters": self.default_parameters,
            "supports_vision": self.supports_vision,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "is_default": self.is_default
        }
        
        if include_secrets and self.api_key:
            config["api_key"] = self.api_key
            
        return config
    
    def __repr__(self):
        return f"<ModelConfig {self.name} ({self.provider}/{self.model_id})>" 