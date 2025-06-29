from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseTool(ABC, BaseModel):
    """工具基类"""
    
    name: str                         # 工具名称
    description: str                  # 工具描述
    parameters: Optional[dict] = None  # 工具参数定义
    
    class Config:
        arbitrary_types_allowed = True
    
    async def __call__(self, **kwargs) -> Any:
        """执行工具调用"""
        return await self.execute(**kwargs)
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具操作（子类必须实现）"""
    
    def to_param(self) -> Dict:
        """转换为函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolResult(BaseModel):
    """工具执行结果"""
    
    output: Any = Field(default=None)           # 输出结果
    error: Optional[str] = Field(default=None)  # 错误信息
    base64_image: Optional[str] = Field(default=None)  # 图像数据（如有）
    system: Optional[str] = Field(default=None)  # 系统消息
    
    class Config:
        arbitrary_types_allowed = True
    
    def __bool__(self):
        """用于布尔上下文的评估"""
        return any(getattr(self, field) for field in self.__fields__)
    
    def __str__(self):
        """字符串表示"""
        return f"Error: {self.error}" if self.error else str(self.output)
    
    def replace(self, **kwargs):
        """返回带有替换字段的新ToolResult"""
        return type(self)(**{**self.dict(), **kwargs}) 