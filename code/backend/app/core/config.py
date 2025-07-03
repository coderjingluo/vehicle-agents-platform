"""
KunlunSec AI Platform - 配置管理

这个模块处理应用程序的配置设置，从环境变量加载配置。
"""

import os
import secrets
from typing import List, Optional, Union, Dict, Any
from pydantic import (
    PostgresDsn, 
    RedisDsn, 
    HttpUrl, 
    validator, 
    Field,
    AnyHttpUrl
)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用程序设置"""
    
    # 应用基础配置
    APP_NAME: str = "车联网安全测试生命周期管理平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: PostgresDsn
    
    # Redis配置
    REDIS_URL: RedisDsn
    
    # Chroma向量数据库配置
    CHROMA_URL: str
    
    # JWT配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    REFRESH_TOKEN_SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(default_factory=list)
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # AI模型配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 默认模型配置
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    
    # LLM详细配置
    LLM_MODEL: str = Field(default="gpt-4-turbo")
    LLM_MAX_TOKENS: int = Field(default=4096)
    LLM_TEMPERATURE: float = Field(default=0.7)
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_API_TYPE: str = Field(default="openai")  # openai, azure, aws等
    LLM_API_VERSION: Optional[str] = None
    
    # 多模态模型配置
    MULTIMODAL_MODELS: List[str] = Field(default_factory=lambda: [
        "gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini",
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    ])
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "./uploads"
    WORKSPACE_DIR: str = "./workspace"
    
    # WebSocket配置
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Celery配置
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # 监控配置
    ENABLE_PROMETHEUS: bool = False
    PROMETHEUS_PORT: int = 8001
    
    # 知识库配置
    KNOWLEDGE_BASE_COLLECTION_NAME: str = "automotive_knowledge"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    DEFAULT_KB_NAME: str = "default_knowledge_base"
    
    # MCP工具配置
    MCP_TIMEOUT: int = 30
    MCP_MAX_RETRIES: int = 3
    
    # 搜索API配置
    GOOGLE_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_CX: Optional[str] = None
    BING_SEARCH_API_KEY: Optional[str] = None
    
    # MCP配置
    MCP_DEFAULT_SERVER_TYPE: str = "stdio"
    MCP_DEFAULT_COMMAND: str = "python -m mcp.server"
    
    # 沙箱配置
    SANDBOX_IMAGE: str = "ubuntu:latest"
    SANDBOX_WORKSPACE: str = "/workspace"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 将默认模型配置应用到LLM配置
        if not self.LLM_API_KEY:
            if self.LLM_API_TYPE == "openai" and self.OPENAI_API_KEY:
                self.LLM_API_KEY = self.OPENAI_API_KEY
            elif self.LLM_API_TYPE == "anthropic" and self.ANTHROPIC_API_KEY:
                self.LLM_API_KEY = self.ANTHROPIC_API_KEY
        
        if not self.LLM_BASE_URL:
            if self.LLM_API_TYPE == "openai" and self.OPENAI_API_BASE:
                self.LLM_BASE_URL = self.OPENAI_API_BASE
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局设置对象
settings = Settings() 