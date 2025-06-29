from typing import Any, Dict, List, Optional

import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolFailure(ToolResult):
    """工具执行失败结果"""
    pass


class ToolError(Exception):
    """工具执行错误"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ToolCollection:
    """工具集合"""
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, *tools: BaseTool):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
    
    def __iter__(self):
        """迭代器方法"""
        return iter(self.tools)
    
    def to_params(self) -> List[Dict[str, Any]]:
        """转换所有工具为参数列表"""
        return [tool.to_param() for tool in self.tools]
    
    async def execute(self, *, name: str, tool_input: Dict[str, Any] = None) -> ToolResult:
        """执行指定的工具"""
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            result = await tool(**(tool_input or {}))
            return result
        except ToolError as e:
            return ToolFailure(error=e.message)
    
    def add_tool(self, tool: BaseTool):
        """添加单个工具到集合"""
        if tool.name in self.tool_map:
            logger.warning(f"Tool {tool.name} already exists in collection, skipping")
            return self
        
        self.tools += (tool,)
        self.tool_map[tool.name] = tool
        return self
    
    def add_tools(self, *tools: BaseTool):
        """添加多个工具到集合"""
        for tool in tools:
            self.add_tool(tool)
        return self 