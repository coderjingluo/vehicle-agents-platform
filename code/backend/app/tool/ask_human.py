"""
KunlunSec AI Platform - 询问人类工具

提供向人类用户询问问题的功能。
"""

from app.core.logging import logger
from .base import BaseTool, ToolResult


class AskHumanTool(BaseTool):
    """询问人类工具，用于向人类用户询问问题并获取回答"""
    
    name: str = "ask_human"
    description: str = "使用此工具向人类用户询问问题并获取回答。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "要向人类用户询问的问题。"
            }
        },
        "required": ["question"]
    }
    
    async def execute(self, question: str, **kwargs) -> ToolResult:
        """执行询问人类操作
        
        Args:
            question: 要询问的问题
            
        Returns:
            人类用户的回答
        """
        try:
            logger.info(f"询问人类: {question}")
            
            # 在实际实现中，这里应该通过某种机制（如WebSocket）将问题发送给前端，
            # 然后等待用户的回答。这里我们简化为直接返回一个提示信息。
            
            # 注意：这个实现是不完整的，需要与前端交互系统集成
            return ToolResult(
                output="[系统消息] 已向用户发送问题，等待回答...",
                metadata={
                    "question": question,
                    "waiting_for_human": True
                }
            )
        except Exception as e:
            logger.error(f"询问人类工具错误: {str(e)}")
            return ToolResult(error=f"询问人类失败: {str(e)}") 