"""
模型配置管理相关数据模型

支持多模型配置、API密钥管理、连接测试、使用统计等功能
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, SecretStr

from app.core.database import Base


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ModelType(str, Enum):
    """模型类型枚举"""
    CHAT = "chat"                    # 对话模型
    EMBEDDING = "embedding"          # 嵌入模型
    COMPLETION = "completion"        # 文本补全模型
    IMAGE = "image"                  # 图像生成模型
    VISION = "vision"                # 视觉理解模型
    AUDIO = "audio"                  # 音频处理模型


class ModelStatus(str, Enum):
    """模型状态枚举"""
    ACTIVE = "active"               # 活跃状态
    INACTIVE = "inactive"           # 未激活
    TESTING = "testing"             # 测试中
    ERROR = "error"                 # 错误状态
    RATE_LIMITED = "rate_limited"   # 频率限制
    QUOTA_EXCEEDED = "quota_exceeded"  # 配额超限


# SQLAlchemy 数据模型
class ModelConfig(Base):
    """模型配置模型"""
    __tablename__ = "model_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 模型基本信息
    provider = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    model_name = Column(String(255), nullable=False)  # 实际的模型名称，如 gpt-4-turbo
    version = Column(String(50), nullable=True)
    
    # 连接配置
    api_base = Column(String(500), nullable=True)  # API基础URL
    api_key = Column(Text, nullable=False)  # 加密存储的API密钥
    api_version = Column(String(50), nullable=True)  # API版本
    organization = Column(String(255), nullable=True)  # 组织ID
    
    # 模型参数
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    
    # 配置选项
    config = Column(JSON, default={})  # 额外配置参数
    headers = Column(JSON, default={})  # 自定义请求头
    
    # 限制和配额
    rate_limit_rpm = Column(Integer, default=0)  # 每分钟请求数限制
    rate_limit_tpm = Column(Integer, default=0)  # 每分钟令牌数限制
    daily_quota = Column(Integer, default=0)     # 每日配额
    monthly_quota = Column(Integer, default=0)   # 每月配额
    
    # 状态和统计
    status = Column(String(50), default=ModelStatus.INACTIVE.value)
    is_default = Column(Boolean, default=False)  # 是否为默认模型
    priority = Column(Integer, default=0)        # 优先级，数字越大优先级越高
    
    # 使用统计
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    last_used_at = Column(DateTime, nullable=True)
    
    # 连接测试
    last_test_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(50), nullable=True)  # success, failed
    last_test_error = Column(Text, nullable=True)
    avg_response_time = Column(Float, default=0.0)  # 平均响应时间(秒)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic 模型 - 用于API交互
class ModelConfigCreate(BaseModel):
    """创建模型配置请求模型"""
    name: str = Field(..., min_length=1, max_length=255, description="模型配置名称")
    display_name: str = Field(..., min_length=1, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="模型描述")
    
    provider: ModelProvider = Field(..., description="模型提供商")
    model_type: ModelType = Field(..., description="模型类型")
    model_name: str = Field(..., min_length=1, max_length=255, description="模型名称")
    version: Optional[str] = Field(None, description="模型版本")
    
    api_base: Optional[str] = Field(None, description="API基础URL")
    api_key: SecretStr = Field(..., description="API密钥")
    api_version: Optional[str] = Field(None, description="API版本")
    organization: Optional[str] = Field(None, description="组织ID")
    
    max_tokens: int = Field(4096, ge=1, le=128000, description="最大令牌数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外配置")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="自定义请求头")
    
    rate_limit_rpm: int = Field(0, ge=0, description="每分钟请求数限制")
    rate_limit_tpm: int = Field(0, ge=0, description="每分钟令牌数限制")
    daily_quota: int = Field(0, ge=0, description="每日配额")
    monthly_quota: int = Field(0, ge=0, description="每月配额")
    
    is_default: bool = Field(False, description="是否为默认模型")
    priority: int = Field(0, description="优先级")


class ModelConfigUpdate(BaseModel):
    """更新模型配置请求模型"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    api_base: Optional[str] = None
    api_key: Optional[SecretStr] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    
    config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    
    rate_limit_rpm: Optional[int] = Field(None, ge=0)
    rate_limit_tpm: Optional[int] = Field(None, ge=0)
    daily_quota: Optional[int] = Field(None, ge=0)
    monthly_quota: Optional[int] = Field(None, ge=0)
    
    status: Optional[ModelStatus] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None


class ModelConfigResponse(BaseModel):
    """模型配置响应模型"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    
    provider: ModelProvider
    model_type: ModelType
    model_name: str
    version: Optional[str]
    
    api_base: Optional[str]
    api_version: Optional[str]
    organization: Optional[str]
    # 注意：不返回API密钥
    
    max_tokens: int
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    
    config: Dict[str, Any]
    headers: Dict[str, str]
    
    rate_limit_rpm: int
    rate_limit_tpm: int
    daily_quota: int
    monthly_quota: int
    
    status: ModelStatus
    is_default: bool
    priority: int
    
    total_requests: int
    total_tokens: int
    total_cost: float
    last_used_at: Optional[datetime]
    
    last_test_at: Optional[datetime]
    last_test_status: Optional[str]
    avg_response_time: float
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModelTestRequest(BaseModel):
    """模型测试请求模型"""
    test_message: str = Field("Hello, this is a test message.", description="测试消息")
    timeout: int = Field(30, ge=5, le=120, description="超时时间(秒)")


class ModelTestResponse(BaseModel):
    """模型测试响应模型"""
    model_id: str
    success: bool
    response: Optional[str]
    error: Optional[str]
    response_time: float  # 响应时间(秒)
    token_count: Optional[int]
    test_timestamp: datetime


class ModelUsageStats(BaseModel):
    """模型使用统计模型"""
    model_id: str
    model_name: str
    
    # 时间范围统计
    daily_requests: int
    daily_tokens: int
    daily_cost: float
    
    weekly_requests: int
    weekly_tokens: int
    weekly_cost: float
    
    monthly_requests: int
    monthly_tokens: int
    monthly_cost: float
    
    # 性能统计
    avg_response_time: float
    success_rate: float
    error_rate: float
    
    # 趋势数据
    usage_trend: List[Dict[str, Any]]  # 使用趋势图数据


class ModelProviderInfo(BaseModel):
    """模型提供商信息模型"""
    provider: ModelProvider
    display_name: str
    description: str
    supported_types: List[ModelType]
    available_models: List[Dict[str, Any]]
    default_config: Dict[str, Any]
    pricing_info: Optional[Dict[str, Any]]
    documentation_url: Optional[str]


class ModelConfigList(BaseModel):
    """模型配置列表响应模型"""
    total: int
    models: List[ModelConfigResponse]
    providers: List[ModelProviderInfo]
    stats: Dict[str, Any]  # 整体统计信息 