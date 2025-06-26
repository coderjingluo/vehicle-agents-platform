"""
LLM客户端
统一的大语言模型客户端，支持多种AI模型提供商
兼容最新版本的LangChain和LangGraph
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from enum import Enum
import json
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from .config import settings


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """生成响应"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    def __init__(self, api_key: str, api_base: str = "http://172.31.15.200:9997/v1"):
        self.api_key = api_key
        self.api_base = api_base
        self.client = ChatOpenAI(
            api_key=api_key,
            base_url=api_base,
            model="qwen3",
            temperature=0.7
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """转换消息格式"""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))
        
        return converted
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """生成响应"""
        # 更新客户端配置
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            # 使用新版本的调用方式
            response = await self.client.ainvoke(converted_messages)
            return response.content
            
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            async for chunk in self.client.astream(converted_messages):
                yield chunk.content
                
        except Exception as e:
            yield f"流式响应错误: {str(e)}"


class DeepSeekClient(BaseLLMClient):
    """DeepSeek客户端"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.api_base = api_base
        self.client = ChatOpenAI(
            api_key=api_key,
            base_url=api_base,
            model="deepseek-chat",
            temperature=0.7
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """转换消息格式"""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))
        
        return converted
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """生成响应"""
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            response = await self.client.ainvoke(converted_messages)
            return response.content
            
        except Exception as e:
            raise Exception(f"DeepSeek API调用失败: {str(e)}")
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            async for chunk in self.client.astream(converted_messages):
                yield chunk.content
                
        except Exception as e:
            yield f"流式响应错误: {str(e)}"


class AnthropicClient(BaseLLMClient):
    """Anthropic客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = ChatAnthropic(
            api_key=api_key,
            model="claude-3-sonnet-20240229",
            temperature=0.7
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """转换消息格式"""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))
        
        return converted
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """生成响应"""
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            response = await self.client.ainvoke(converted_messages)
            return response.content
            
        except Exception as e:
            raise Exception(f"Anthropic API调用失败: {str(e)}")
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        if model:
            self.client.model_name = model
        
        self.client.temperature = temperature
        if max_tokens:
            self.client.max_tokens = max_tokens
        
        converted_messages = self._convert_messages(messages)
        
        try:
            async for chunk in self.client.astream(converted_messages):
                yield chunk.content
                
        except Exception as e:
            yield f"流式响应错误: {str(e)}"


class LLMClientManager:
    """LLM客户端管理器"""
    
    def __init__(self):
        self._clients: Dict[LLMProvider, BaseLLMClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化所有可用的客户端"""
        # OpenAI客户端
        if settings.openai_api_key:
            self._clients[LLMProvider.OPENAI] = OpenAIClient(
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base
            )
        
        # DeepSeek客户端
        if settings.deepseek_api_key:
            self._clients[LLMProvider.DEEPSEEK] = DeepSeekClient(
                api_key=settings.deepseek_api_key,
                api_base=settings.deepseek_api_base
            )
        
        # Anthropic客户端
        if settings.anthropic_api_key:
            self._clients[LLMProvider.ANTHROPIC] = AnthropicClient(
                api_key=settings.anthropic_api_key
            )
    
    def get_client(self, provider: Optional[LLMProvider] = None) -> BaseLLMClient:
        """获取LLM客户端"""
        if provider is None:
            provider = LLMProvider(settings.default_llm_provider)
        
        if provider not in self._clients:
            raise ValueError(f"LLM provider {provider.value} not configured")
        
        return self._clients[provider]
    
    def list_available_providers(self) -> List[LLMProvider]:
        """列出可用的提供商"""
        return list(self._clients.keys())
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """生成响应"""
        client = self.get_client(provider)
        return await client.generate_response(messages, model=model, **kwargs)
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        client = self.get_client(provider)
        async for chunk in client.generate_stream(messages, model=model, **kwargs):
            yield chunk


# 全局LLM客户端管理器实例
llm_manager = LLMClientManager()


def get_llm_manager() -> LLMClientManager:
    """获取LLM客户端管理器"""
    return llm_manager 