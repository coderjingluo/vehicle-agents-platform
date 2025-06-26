"""
应用配置模块
管理所有的配置项和环境变量
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 应用基础配置
    app_name: str = Field(default="车联网安全测试生命周期管理平台", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql://admin:admin123@localhost:5432/automotive_security",
        description="数据库连接URL"
    )
    
    # Redis配置
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis连接URL"
    )
    
    # Chroma向量数据库配置
    chroma_url: str = Field(
        default="http://localhost:8000",
        description="Chroma数据库连接URL"
    )
    
    # JWT配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    
    # CORS配置
    # 指定为所有源
    allowed_origins: str = Field(
        default="*",
        description="允许的跨域源(逗号分隔)"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """获取CORS源列表"""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return self.allowed_origins
    
    # AI模型配置
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API密钥")
    openai_api_base: str = Field(default="https://api.openai.com/v1", description="OpenAI API基础URL")
    
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API密钥")
    deepseek_api_base: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API基础URL")
    
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API密钥")
    
    # 默认模型配置
    default_llm_provider: str = Field(default="openai", description="默认LLM提供商")
    default_llm_model: str = Field(default="gpt-3.5-turbo", description="默认LLM模型")
    
    # 文件上传配置
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小(字节)")  # 10MB
    upload_dir: str = Field(default="./uploads", description="文件上传目录")
    
    # WebSocket配置
    websocket_heartbeat_interval: int = Field(default=30, description="WebSocket心跳间隔(秒)")
    
    # Celery配置
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery消息代理URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery结果后端URL"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="./logs/app.log", description="日志文件路径")
    
    # 监控配置
    enable_prometheus: bool = Field(default=True, description="启用Prometheus监控")
    prometheus_port: int = Field(default=8001, description="Prometheus端口")
    
    # 知识库配置
    knowledge_base_collection_name: str = Field(
        default="automotive_knowledge",
        description="知识库集合名称"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="嵌入模型名称"
    )
    chunk_size: int = Field(default=1000, description="文档分块大小")
    chunk_overlap: int = Field(default=200, description="文档分块重叠大小")
    
    # MCP工具配置
    mcp_timeout: int = Field(default=30, description="MCP工具调用超时时间(秒)")
    mcp_max_retries: int = Field(default=3, description="MCP工具最大重试次数")
    
    # Phase 4: 扩展配置
    # 文档处理配置
    UPLOAD_DIR: str = Field(default="./uploads", description="文件上传目录")
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="最大文件大小(50MB)")
    SUPPORTED_FILE_TYPES: List[str] = Field(
        default=["pdf", "docx", "txt", "md", "html", "json", "xml"],
        description="支持的文件类型"
    )
    
    # 向量数据库配置
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./chroma_db", description="Chroma持久化目录")
    CHROMA_HOST: str = Field(default="localhost", description="Chroma主机")
    CHROMA_PORT: int = Field(default=8001, description="Chroma端口")
    
    # 模型配置加密
    ENCRYPTION_KEY: str = Field(
        default="your-encryption-key-here-32-chars-long",
        description="API密钥加密密钥(32字符)"
    )
    
    # 批处理配置
    BATCH_SIZE: int = Field(default=100, description="批处理大小")
    MAX_CONCURRENT_TASKS: int = Field(default=10, description="最大并发任务数")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存过期时间(秒)")
    ENABLE_CACHE: bool = Field(default=True, description="启用缓存")


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings 