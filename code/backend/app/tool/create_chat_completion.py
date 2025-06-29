import logging
from typing import Dict, List, Optional

from pydantic import BaseModel

from .base import BaseTool, ToolResult
from app.agent.base import LLM

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """聊天消息"""
    role: str
    content: str


class CreateChatCompletionTool(BaseTool):
    """创建聊天完成工具"""
    
    name: str = "create_chat_completion"
    description: str = "使用指定的大型语言模型（LLM）生成聊天回应"
    parameters: dict = {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["system", "user", "assistant"]
                        },
                        "content": {
                            "type": "string"
                        }
                    },
                    "required": ["role", "content"]
                },
                "description": "聊天消息历史"
            },
            "model_name": {
                "type": "string",
                "description": "要使用的模型名称，如不指定则使用默认模型"
            },
            "temperature": {
                "type": "number",
                "description": "生成的随机性(0-1)"
            }
        },
        "required": ["messages"]
    }
    
    _llm: Optional[LLM] = None
    
    def __init__(self, **data):
        """初始化创建聊天完成工具"""
        super().__init__(**data)
        self._llm = LLM()
    
    async def execute(self, messages: List[Dict[str, str]], model_name: Optional[str] = None,
                     temperature: Optional[float] = None, **kwargs) -> ToolResult:
        """执行聊天完成"""
        try:
            # 转换消息格式
            converted_messages = [Message(**msg) for msg in messages]
            
            # 使用模型生成回应
            response = await self._llm.ask(
                messages=messages,  # 直接使用原始消息格式，新的LLM实现可以处理
                temperature=temperature,
            )
            
            return ToolResult(output=response)
        except Exception as e:
            logger.error(f"创建聊天完成失败: {str(e)}")
            return ToolResult(error=f"创建聊天完成失败: {str(e)}") 