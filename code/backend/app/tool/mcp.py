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
                    self.tools = tuple(self.tool_map.values())
                    logger.info(f"已断开与MCP服务器{server_id}的连接")
                except Exception as e:
                    logger.error(f"断开与服务器{server_id}的连接时出错: {e}")
        else:
            # 按确定的顺序断开所有服务器
            for sid in sorted(list(self.sessions.keys())):
                await self.disconnect(sid)
            self.tool_map = {}
            self.tools = tuple()
            logger.info("已断开与所有MCP服务器的连接")
