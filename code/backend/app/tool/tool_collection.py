"""
KunlunSec AI Platform - 工具集合模块

管理多个工具的集合，提供统一的接口。
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel

from app.core.logging import logger
from app.tool.base import BaseTool, ToolResult


class ToolCollection(BaseModel):
    """工具集合，管理多个工具并提供统一的接口"""
    
    name: str = "tool_collection"
    description: str = "工具集合"
    tools: Tuple[BaseTool, ...] = ()
    tool_map: Dict[str, BaseTool] = {}
    mcp_clients: Any = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, *tools: BaseTool, **kwargs):
        """初始化工具集合"""
        super().__init__(**kwargs)
        self.tool_map = {tool.name: tool for tool in tools}
        self.tools = tuple(tools)
    
    def add_tool(self, tool: BaseTool) -> None:
        """添加工具到集合"""
        if tool.name in self.tool_map:
            logger.warning(f"工具 '{tool.name}' 已存在，将被覆盖")
        
        self.tool_map[tool.name] = tool
        self.tools = tuple(self.tool_map.values())
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """批量添加工具到集合"""
        for tool in tools:
            self.add_tool(tool)
    
    def remove_tool(self, tool_name: str) -> None:
        """从集合中移除工具"""
        if tool_name in self.tool_map:
            del self.tool_map[tool_name]
            self.tools = tuple(self.tool_map.values())
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取指定名称的工具"""
        return self.tool_map.get(tool_name)
    
    def get_tools(self) -> List[BaseTool]:
        """获取所有工具列表"""
        return list(self.tools)
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tool_map.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的模式定义"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """执行指定的工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(error=f"工具 '{tool_name}' 不存在")
        
        try:
            # 直接将参数传递给工具的execute方法
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"执行工具 '{tool_name}' 时出错: {str(e)}")
            return ToolResult(error=f"执行工具 '{tool_name}' 时出错: {str(e)}")


# 全局工具集合实例
_global_tool_collection = None


def get_global_tool_collection() -> ToolCollection:
    """获取全局工具集合实例"""
    global _global_tool_collection
    
    if _global_tool_collection is None:
        _global_tool_collection = ToolCollection()
        
        # 初始化基本工具
        from app.tool.bash import Bash
        from app.tool.file_operators import FileOperatorTool
        from app.tool.python_execute import PythonExecuteTool
        from app.tool.create_chat_completion import CreateChatCompletionTool
        from app.tool.terminate import TerminateTool
        
        _global_tool_collection.add_tools([
            Bash(),
            FileOperatorTool(),
            PythonExecuteTool(),
            CreateChatCompletionTool(),
            TerminateTool()
        ])
        
        # 尝试初始化MCP工具
        try:
            from app.tool.mcp import MCPClients
            _global_tool_collection.mcp_clients = MCPClients()
        except ImportError:
            logger.warning("无法导入MCP客户端，MCP工具将不可用")
    
    return _global_tool_collection


async def register_mcp_tool(command: str, args: List[str] = None, server_id: str = "") -> bool:
    """注册MCP工具到全局工具集合
    
    Args:
        command: MCP服务器命令
        args: 命令参数
        server_id: 服务器标识符
        
    Returns:
        bool: 是否成功注册
    """
    tool_collection = get_global_tool_collection()
    
    if not hasattr(tool_collection, "mcp_clients"):
        logger.error("MCP客户端未初始化")
        return False
    
    try:
        # 连接到MCP服务器
        await tool_collection.mcp_clients.connect_stdio(
            command=command,
            args=args or [],
            server_id=server_id
        )
        
        # 将MCP工具添加到全局工具集合
        for tool_name, tool in tool_collection.mcp_clients.tool_map.items():
            tool_collection.add_tool(tool)
        
        logger.info(f"已注册MCP工具: {tool_collection.mcp_clients.get_tool_names()}")
        return True
    except Exception as e:
        logger.error(f"注册MCP工具时出错: {str(e)}")
        return False


async def register_mcp_tool_sse(server_url: str, server_id: str = "") -> bool:
    """通过SSE注册MCP工具到全局工具集合
    
    Args:
        server_url: MCP服务器URL
        server_id: 服务器标识符
        
    Returns:
        bool: 是否成功注册
    """
    tool_collection = get_global_tool_collection()
    
    if not hasattr(tool_collection, "mcp_clients"):
        logger.error("MCP客户端未初始化")
        return False
    
    try:
        # 连接到MCP服务器
        await tool_collection.mcp_clients.connect_sse(
            server_url=server_url,
            server_id=server_id
        )
        
        # 将MCP工具添加到全局工具集合
        for tool_name, tool in tool_collection.mcp_clients.tool_map.items():
            tool_collection.add_tool(tool)
        
        logger.info(f"已注册MCP工具: {tool_collection.mcp_clients.get_tool_names()}")
        return True
    except Exception as e:
        logger.error(f"注册MCP工具时出错: {str(e)}")
        return False 