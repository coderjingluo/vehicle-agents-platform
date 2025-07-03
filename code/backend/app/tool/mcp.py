from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import ListToolsResult, TextContent

from app.core.logging import logger
from .base import BaseTool, ToolResult
from .tool_collection import ToolCollection


class MCPClientTool(BaseTool):
    """表示可以从客户端在MCP服务器上调用的工具代理"""

    name: str = "mcp_client_tool"
    description: str = "MCP客户端工具"
    session: Optional[ClientSession] = None
    server_id: str = ""  # 添加服务器标识符
    original_name: str = ""

    def __init__(self, server_id: str = "", tool_name: str = "", tool_description: str = "", tool_parameters: Dict = None, **kwargs):
        """初始化MCP客户端工具"""
        data = {
            "name": tool_name or self.name,
            "description": tool_description or self.description,
            "parameters": tool_parameters or {},
        }
        super().__init__(**data)
        self.server_id = server_id
        self.original_name = kwargs.get("original_name", "")
        self.session = kwargs.get("session")

    async def execute(self, **kwargs) -> ToolResult:
        """通过向MCP服务器发出远程调用来执行工具"""
        if not self.session:
            return ToolResult(error="未连接到MCP服务器")

        try:
            logger.info(f"执行工具: {self.original_name}, 参数: {kwargs}")
            result = await self.session.call_tool(self.original_name, kwargs)
            content_str = ", ".join(
                item.text for item in result.content if isinstance(item, TextContent)
            )
            return ToolResult(output=content_str or "没有返回输出。")
        except Exception as e:
            logger.error(f"执行工具失败: {str(e)}")
            return ToolResult(error=f"执行工具错误: {str(e)}")


class MCPClients(ToolCollection):
    """
    连接到多个MCP服务器并通过模型上下文协议管理可用工具的工具集合
    """

    sessions: Dict[str, ClientSession] = {}
    exit_stacks: Dict[str, AsyncExitStack] = {}
    description: str = "用于服务器交互的MCP客户端工具"

    def __init__(self):
        super().__init__()  # 使用空工具列表初始化
        self.name = "mcp"  # 为向后兼容保留名称
        self.tool_map = {}
        self.tools = tuple()

    async def connect_sse(self, server_url: str, server_id: str = "") -> None:
        """使用SSE传输连接到MCP服务器"""
        if not server_url:
            raise ValueError("需要提供服务器URL")

        server_id = server_id or server_url

        # 在新连接之前确保断开旧连接
        if server_id in self.sessions:
            await self.disconnect(server_id)

        exit_stack = AsyncExitStack()
        self.exit_stacks[server_id] = exit_stack

        streams_context = sse_client(url=server_url)
        streams = await exit_stack.enter_async_context(streams_context)
        session = await exit_stack.enter_async_context(ClientSession(*streams))
        self.sessions[server_id] = session

        await self._initialize_and_list_tools(server_id)

    async def connect_stdio(
        self, command: str, args: List[str], server_id: str = ""
    ) -> None:
        """使用stdio传输连接到MCP服务器"""
        if not command:
            raise ValueError("需要提供服务器命令")

        server_id = server_id or command

        # 在新连接之前确保断开旧连接
        if server_id in self.sessions:
            await self.disconnect(server_id)

        exit_stack = AsyncExitStack()
        self.exit_stacks[server_id] = exit_stack

        server_params = StdioServerParameters(command=command, args=args)
        stdio_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(read, write))
        self.sessions[server_id] = session

        await self._initialize_and_list_tools(server_id)

    async def _initialize_and_list_tools(self, server_id: str) -> None:
        """初始化会话并填充工具映射"""
        session = self.sessions.get(server_id)
        if not session:
            raise RuntimeError(f"服务器{server_id}的会话未初始化")

        await session.initialize()
        response = await session.list_tools()

        # 为每个服务器工具创建适当的工具对象
        for tool in response.tools:
            original_name = tool.name
            tool_name = f"mcp_{server_id}_{original_name}"
            tool_name = self._sanitize_tool_name(tool_name)

            server_tool = MCPClientTool(
                name=tool_name,
                description=tool.description,
                parameters=tool.inputSchema,
                session=session,
                server_id=server_id,
                original_name=original_name,
            )
            self.tool_map[tool_name] = server_tool

        # 更新工具元组
        self.tools = tuple(self.tool_map.values())
        logger.info(
            f"连接到服务器 {server_id} 的工具: {[tool.name for tool in response.tools]}"
        )

    def _sanitize_tool_name(self, name: str) -> str:
        """净化工具名称以符合MCPClientTool要求"""
        import re

        # 替换无效字符为下划线
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)

        # 删除连续的下划线
        sanitized = re.sub(r"_+", "_", sanitized)

        # 删除前导/尾随下划线
        sanitized = sanitized.strip("_")

        # 如果需要，截断为64个字符
        if len(sanitized) > 64:
            sanitized = sanitized[:64]

        return sanitized

    async def list_tools(self) -> ListToolsResult:
        """列出所有可用工具"""
        tools_result = ListToolsResult(tools=[])
        for session in self.sessions.values():
            response = await session.list_tools()
            tools_result.tools += response.tools
        return tools_result

    async def disconnect(self, server_id: str = "") -> None:
        """断开与特定MCP服务器的连接，或者如果未提供server_id，则断开所有服务器"""
        if server_id:
            if server_id in self.sessions:
                try:
                    exit_stack = self.exit_stacks.get(server_id)

                    # 关闭退出栈，它将处理会话清理
                    if exit_stack:
                        try:
                            await exit_stack.aclose()
                        except RuntimeError as e:
                            if "cancel scope" in str(e).lower():
                                logger.warning(
                                    f"从{server_id}断开连接期间出现取消范围错误，继续清理: {e}"
                                )
                            else:
                                raise

                    # 清理引用
                    self.sessions.pop(server_id, None)
                    self.exit_stacks.pop(server_id, None)

                    # 移除与此服务器关联的工具
                    self.tool_map = {
                        k: v
                        for k, v in self.tool_map.items()
                        if v.server_id != server_id
                    }

                    # 更新工具元组
                    self.tools = tuple(self.tool_map.values())

                    logger.info(f"已断开与MCP服务器 {server_id} 的连接")
                except Exception as e:
                    logger.error(f"断开与MCP服务器 {server_id} 的连接失败: {str(e)}")
        else:
            # 断开所有连接
            for srv_id in list(self.sessions.keys()):
                try:
                    await self.disconnect(srv_id)
                except Exception as e:
                    logger.error(f"断开与MCP服务器 {srv_id} 的连接失败: {str(e)}")

            # 确保所有引用都被清理
            self.sessions.clear()
            self.exit_stacks.clear()
            self.tool_map.clear()
            self.tools = tuple()


class MCPTool(BaseTool):
    """MCP 工具包装器，提供与MCP服务器交互的能力"""
    
    name: str = "mcp"
    description: str = "与MCP服务器交互，连接和断开连接，以及调用远程工具"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["connect_sse", "connect_stdio", "disconnect", "list_tools", "call_tool"],
                "description": "要执行的MCP操作"
            },
            "server_url": {
                "type": "string",
                "description": "MCP服务器URL，用于SSE连接"
            },
            "server_id": {
                "type": "string",
                "description": "MCP服务器标识符，用于在使用多个服务器时区分它们"
            },
            "command": {
                "type": "string",
                "description": "要执行的命令，用于stdio连接"
            },
            "args": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "命令参数，用于stdio连接"
            },
            "tool_name": {
                "type": "string",
                "description": "要调用的远程工具名称"
            },
            "tool_args": {
                "type": "object",
                "description": "传递给远程工具的参数"
            }
        },
        "required": ["operation"]
    }
    
    # 单例MCP客户端管理器
    _clients = MCPClients()
    
    async def execute(
        self,
        operation: str,
        server_url: Optional[str] = None,
        server_id: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        """执行MCP相关操作
        
        Args:
            operation: 要执行的操作
            server_url: 服务器URL (对于SSE连接)
            server_id: 服务器标识符
            command: 要执行的命令 (对于stdio连接)
            args: 命令参数
            tool_name: 要调用的工具名称
            tool_args: 工具参数
            
        Returns:
            ToolResult: 操作结果
        """
        try:
            if operation == "connect_sse":
                if not server_url:
                    return ToolResult(error="连接SSE需要server_url")
                
                await self._clients.connect_sse(server_url, server_id or "")
                return ToolResult(output=f"已连接到MCP服务器 {server_url}")
                
            elif operation == "connect_stdio":
                if not command:
                    return ToolResult(error="连接stdio需要command")
                    
                await self._clients.connect_stdio(command, args or [], server_id or "")
                return ToolResult(output=f"已连接到MCP命令 {command}")
                
            elif operation == "disconnect":
                await self._clients.disconnect(server_id or "")
                return ToolResult(output=f"已断开与MCP服务器 {server_id or '所有'} 的连接")
                
            elif operation == "list_tools":
                result = await self._clients.list_tools()
                tools_info = [{
                    "name": tool.name,
                    "description": tool.description
                } for tool in result.tools]
                
                return ToolResult(output=tools_info)
                
            elif operation == "call_tool":
                if not tool_name:
                    return ToolResult(error="调用工具需要tool_name")
                
                # 查找工具
                tool = self._clients.get_tool(tool_name)
                if not tool:
                    return ToolResult(error=f"找不到工具: {tool_name}")
                
                # 调用工具
                return await tool.execute(**(tool_args or {}))
            
            else:
                return ToolResult(error=f"未知操作: {operation}")
                
        except Exception as e:
            logger.error(f"执行MCP操作失败: {str(e)}")
            return ToolResult(error=f"执行MCP操作失败: {str(e)}")
    
    @classmethod
    def get_clients(cls) -> MCPClients:
        """获取MCP客户端管理器单例"""
        return cls._clients
