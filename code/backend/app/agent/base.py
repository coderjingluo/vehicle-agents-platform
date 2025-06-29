"""
KunlunSec AI Platform - 基础智能体模块

定义智能体基类和核心功能。
"""

import enum
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field, model_validator

from app.core.logging import logger
from app.sandbox.client import SANDBOX_CLIENT

class AgentState(str, enum.Enum):
    """智能体状态枚举"""
    IDLE = "idle"           # 空闲状态
    THINKING = "thinking"   # 思考中
    ACTING = "acting"       # 行动中
    FINISHED = "finished"   # 已完成
    ERROR = "error"         # 错误状态

class Message(BaseModel):
    """消息模型"""
    role: str
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    base64_image: Optional[str] = None
    
    @classmethod
    def user_message(cls, content: str, **kwargs):
        """创建用户消息"""
        return cls(role="user", content=content, **kwargs)
    
    @classmethod
    def system_message(cls, content: str, **kwargs):
        """创建系统消息"""
        return cls(role="system", content=content, **kwargs)
    
    @classmethod
    def assistant_message(cls, content: str, **kwargs):
        """创建助手消息"""
        return cls(role="assistant", content=content, **kwargs)
    
    @classmethod
    def tool_message(cls, content: str, **kwargs):
        """创建工具消息"""
        return cls(role="tool", content=content, **kwargs)

class Memory:
    """智能体记忆存储"""
    
    def __init__(self):
        """初始化记忆存储"""
        self.messages = []  # 消息列表
        
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取所有消息"""
        return self.messages
    
    def clear(self) -> None:
        """清除所有消息"""
        self.messages = []
    
    def get_last_message(self) -> Optional[Dict[str, str]]:
        """获取最后一条消息"""
        if not self.messages:
            return None
        return self.messages[-1]

class LLM:
    """语言模型接口"""
    
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, 
                max_tokens: int = 2048, temperature: float = 0.7, 
                api_type: str = "openai", api_version: str = None):
        """初始化LLM
        
        Args:
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
            max_tokens: 最大token数
            temperature: 生成温度
            api_type: API类型(openai, azure, aws等)
            api_version: API版本
        """
        from app.core.config import settings
        
        self.model = model or settings.LLM_MODEL
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_type = api_type or settings.LLM_API_TYPE
        self.api_version = api_version or settings.LLM_API_VERSION
        
        # 设置token计数相关属性
        self.total_input_tokens = 0
        self.total_completion_tokens = 0
        
        # 初始化客户端
        self._init_client()
        
    def _init_client(self):
        """初始化API客户端"""
        try:
            from openai import AsyncOpenAI, AsyncAzureOpenAI
            import tiktoken
            
            # 初始化tokenizer
            try:
                self.tokenizer = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # 如果模型不在tiktoken的预设中，使用cl100k_base作为默认值
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
            # 根据API类型初始化客户端
            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            elif self.api_type == "aws":
                # 暂不支持AWS Bedrock，可根据需要添加
                raise NotImplementedError("AWS Bedrock客户端尚未实现")
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
                
        except ImportError as e:
            from app.core.logging import logger
            logger.error(f"初始化LLM客户端失败: {str(e)}，请安装必要的依赖")
            raise
    
    async def generate(self, prompt: str, messages: List[Dict[str, str]] = None, 
                       system_msgs: List[Dict[str, str]] = None, 
                       tools: List[Dict] = None, tool_choice: Any = None,
                       stream: bool = False, temperature: Optional[float] = None, **kwargs) -> Any:
        """生成文本
        
        Args:
            prompt: 系统提示词
            messages: 对话消息列表
            system_msgs: 系统消息列表
            tools: 工具列表
            tool_choice: 工具选择策略
            stream: 是否流式响应
            temperature: 生成温度
            **kwargs: 其他参数
            
        Returns:
            生成的文本或工具调用响应
        """
        if not messages:
            messages = []
        
        # 添加系统提示词作为系统消息
        if prompt and not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {"role": "system", "content": prompt})
        
        # 如果提供了工具，使用ask_tool方法
        if tools:
            return await self.ask_tool(
                messages=messages, 
                system_msgs=system_msgs,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                **kwargs
            )
        
        # 否则使用标准ask方法
        return await self.ask(
            messages=messages,
            system_msgs=system_msgs,
            stream=stream,
            temperature=temperature,
            **kwargs
        )
    
    def count_tokens(self, text: str) -> int:
        """计算文本中的token数量"""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    async def ask(self, messages: List[Dict[str, str]], 
                 system_msgs: Optional[List[Dict[str, str]]] = None,
                 stream: bool = False, 
                 temperature: Optional[float] = None) -> str:
        """向LLM发送请求
        
        Args:
            messages: 对话消息列表
            system_msgs: 系统消息列表
            stream: 是否流式响应
            temperature: 生成温度
            
        Returns:
            生成的文本
        """
        from app.core.logging import logger
        
        try:
            # 准备消息
            all_messages = []
            if system_msgs:
                all_messages.extend(system_msgs)
            all_messages.extend(messages)
            
            # 创建请求参数
            params = {
                "model": self.model,
                "messages": all_messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "stream": stream
            }
            
            # 非流式请求
            if not stream:
                response = await self.client.chat.completions.create(**params)
                
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("LLM响应为空或无效")
                
                # 更新token计数
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_completion_tokens += response.usage.completion_tokens
                
                logger.info(f"Token使用情况: 输入={response.usage.prompt_tokens}, " 
                           f"输出={response.usage.completion_tokens}, "
                           f"总计={response.usage.prompt_tokens + response.usage.completion_tokens}")
                
                return response.choices[0].message.content
            
            # 流式请求
            response = await self.client.chat.completions.create(**params)
            
            collected_messages = []
            async for chunk in response:
                chunk_message = chunk.choices[0].delta.content or ""
                collected_messages.append(chunk_message)
                # print(chunk_message, end="", flush=True)
            
            # 合并所有收集到的消息片段
            full_response = "".join(collected_messages).strip()
            if not full_response:
                raise ValueError("流式LLM响应为空")
            
            return full_response
            
        except Exception as e:
            logger.error(f"LLM请求失败: {str(e)}")
            raise e
    
    async def ask_tool(self, messages: List[Dict[str, str]],
                      system_msgs: Optional[List[Dict[str, str]]] = None,
                      tools: Optional[List[Dict]] = None,
                      tool_choice: Any = None,
                      temperature: Optional[float] = None,
                      timeout: int = 300,
                      **kwargs) -> Dict[str, Any]:
        """使用工具进行问答
        
        Args:
            messages: 对话消息列表
            system_msgs: 系统消息列表
            tools: 工具列表
            tool_choice: 工具选择策略
            temperature: 生成温度
            timeout: 超时时间(秒)
            **kwargs: 其他参数
            
        Returns:
            带有工具调用的响应
        """
        from app.core.logging import logger
        
        try:
            # 准备消息
            all_messages = []
            if system_msgs:
                all_messages.extend(system_msgs)
            all_messages.extend(messages)
            
            # 创建请求参数
            params = {
                "model": self.model,
                "messages": all_messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "tools": tools,
                "tool_choice": tool_choice,
                "timeout": timeout,
                "stream": False,  # 工具调用始终使用非流式
                **kwargs
            }
            
            # 发送请求
            response = await self.client.chat.completions.create(**params)
            
            # 检查响应是否有效
            if not response.choices or not response.choices[0].message:
                logger.warning("LLM工具响应为空或无效")
                return {}
            
            # 更新token计数
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_completion_tokens += response.usage.completion_tokens
            
            logger.info(f"Token使用情况: 输入={response.usage.prompt_tokens}, " 
                       f"输出={response.usage.completion_tokens}, "
                       f"总计={response.usage.prompt_tokens + response.usage.completion_tokens}")
            
            # 将响应转换为字典
            message = response.choices[0].message
            result = {
                "content": message.content,
                "role": "assistant"
            }
            
            # 添加工具调用(如果有)
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"LLM工具请求失败: {str(e)}")
            raise e

# 定义角色类型
ROLE_TYPE = str

class BaseAgent(BaseModel, ABC):
    """智能体基类"""
    
    # 核心属性
    name: str                               # 智能体名称
    description: Optional[str] = None       # 智能体描述
    
    # 提示语
    system_prompt: Optional[str] = None     # 系统级指令提示
    next_step_prompt: Optional[str] = None  # 下一步行动提示
    
    # 依赖组件
    llm: LLM                                # 语言模型实例
    memory: Memory = Field(default_factory=Memory)  # 智能体记忆存储
    state: AgentState = AgentState.IDLE     # 当前状态
    
    # 执行控制
    max_steps: int = 10                     # 最大执行步骤数
    current_step: int = 0                   # 当前执行步骤
    duplicate_threshold: int = 2            # 重复内容检测阈值
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # 允许子类中的额外字段
    
    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """初始化智能体"""
        if self.llm is None:
            raise ValueError("必须提供LLM实例")
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self
    
    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """安全的状态转换上下文管理器"""
        if not isinstance(new_state, AgentState):
            raise ValueError(f"无效的状态: {new_state}")
            
        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # 发生错误时转换到ERROR状态
            raise e
        finally:
            self.state = previous_state  # 恢复到之前的状态
    
    def update_memory(
        self,
        role: ROLE_TYPE,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs
    ):
        """添加消息到智能体记忆"""
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }
        
        if role not in message_map:
            raise ValueError(f"不支持的消息角色: {role}")
            
        # 根据角色创建消息并添加适当的参数
        kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
        self.memory.add_message(message_map[role](content, **kwargs))
    
    async def run(self, request: Optional[str] = None) -> str:
        """执行智能体主循环"""
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"无法从状态 {self.state} 运行智能体")
            
        if request:
            self.update_memory("user", request)
        
        results = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"执行步骤 {self.current_step}/{self.max_steps}")
                step_result = await self.step()
                
                # 检查是否陷入循环
                if self.is_stuck():
                    self.handle_stuck_state()
                    
                results.append(f"步骤 {self.current_step}: {step_result}")
                
            if self.current_step >= self.max_steps:
                self.current_step = 0
                self.state = AgentState.IDLE
                results.append(f"终止: 达到最大步骤数 ({self.max_steps})")
        
        await SANDBOX_CLIENT.cleanup()
        return "\n".join(results) if results else "没有执行任何步骤"
    
    @abstractmethod
    async def step(self) -> str:
        """执行单个步骤(子类必须实现)"""
        pass
    
    def is_stuck(self) -> bool:
        """检测是否陷入循环"""
        if len(self.memory.messages) < 2:
            return False
            
        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False
            
        # 计算相同内容出现的次数
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )
        
        return duplicate_count >= self.duplicate_threshold
    
    def handle_stuck_state(self):
        """处理循环状态"""
        stuck_prompt = "\
        检测到重复响应。考虑新的策略，避免重复已尝试过的无效路径。"
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"智能体检测到循环状态。添加提示: {stuck_prompt}")
    
    @property
    def messages(self) -> List[Message]:
        """获取智能体记忆中的消息列表"""
        return self.memory.messages
    
    @messages.setter
    def messages(self, value: List[Message]):
        """设置智能体记忆中的消息列表"""
        self.memory.messages = value 