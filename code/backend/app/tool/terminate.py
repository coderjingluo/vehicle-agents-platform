import logging
import sys
from typing import Optional

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class TerminateTool(BaseTool):
    """终止工具，用于结束智能体执行"""
    
    name: str = "terminate"
    description: str = "终止当前智能体执行流程，可选择性地提供退出消息。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "终止时显示的消息"
            },
            "exit_code": {
                "type": "integer",
                "description": "退出代码，默认为0（成功退出）"
            }
        },
        "required": []
    }
    
    async def execute(self, message: Optional[str] = None, exit_code: int = 0, **kwargs) -> ToolResult:
        """执行终止操作"""
        try:
            # 记录终止消息
            if message:
                logger.info(f"智能体终止: {message}")
            else:
                logger.info("智能体执行已终止")
                
            # 返回终止结果
            # 注意：实际终止应该由调用方处理，这里只返回一个信号
            return ToolResult(
                output={"terminated": True, "message": message or "执行已终止", "exit_code": exit_code},
                system="TERMINATE"
            )
        except Exception as e:
            logger.error(f"终止操作失败: {str(e)}")
            return ToolResult(error=f"终止操作失败: {str(e)}") 