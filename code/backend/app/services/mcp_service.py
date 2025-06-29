"""
MCP服务

提供MCP连接和工具管理的服务
"""

import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.core.logging import logger
from app.models.tool import MCPConnection, MCPTool, MCPServer, MCPToolExecution
from app.tool.mcp import MCPClients, MCPClientTool


class MCPService:
    """MCP服务类，提供MCP连接和工具管理功能"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mcp_clients = MCPClients()  # MCP客户端实例
        self._running_servers = {}  # 存储正在运行的服务器会话
    
    # MCP连接管理
    
    async def create_connection(
        self, 
        name: str, 
        connection_type: str, 
        url: str, 
        description: str = ""
    ) -> MCPConnection:
        """创建新的MCP连接"""
        # 检查是否已存在同名连接
        result = await self.db.execute(
            select(MCPConnection).where(MCPConnection.name == name)
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError(f"已存在名为 '{name}' 的MCP连接")
        
        # 创建新连接
        connection = MCPConnection(
            id=str(uuid.uuid4()),
            name=name,
            connection_type=connection_type,
            url=url,
            description=description,
            status="connecting",
            created_at=datetime.now()
        )
        
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        
        # 尝试建立连接（异步）
        # 这里应该实现实际的连接逻辑，可能需要使用后台任务
        # 简化处理，直接返回
        
        return connection
    
    async def list_connections(self) -> List[MCPConnection]:
        """获取所有MCP连接列表"""
        result = await self.db.execute(select(MCPConnection))
        return result.scalars().all()
    
    async def get_connection(self, conn_id: str) -> Optional[MCPConnection]:
        """根据ID获取MCP连接"""
        result = await self.db.execute(
            select(MCPConnection).where(MCPConnection.id == conn_id)
        )
        return result.scalars().first()
    
    async def delete_connection(self, conn_id: str) -> bool:
        """删除MCP连接"""
        # 获取连接
        connection = await self.get_connection(conn_id)
        if not connection:
            return False
        
        # 删除关联的工具
        await self.db.execute(
            delete(MCPTool).where(MCPTool.connection_id == conn_id)
        )
        
        # 删除连接
        await self.db.delete(connection)
        await self.db.commit()
        
        return True
    
    async def get_tool_count(self, conn_id: str) -> int:
        """获取连接的工具数量"""
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.connection_id == conn_id)
        )
        tools = result.scalars().all()
        return len(tools)
    
    async def list_tools(self, conn_id: str) -> List[MCPTool]:
        """获取连接的工具列表"""
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.connection_id == conn_id)
        )
        return result.scalars().all()
    
    # MCP服务器管理
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """获取所有MCP服务器列表"""
        result = await self.db.execute(select(MCPServer))
        servers = result.scalars().all()
        
        server_list = []
        for server in servers:
            server_dict = {
                "id": server.id,
                "name": server.name,
                "type": server.server_type,
                "status": server.status
            }
            
            if server.url:
                server_dict["url"] = server.url
            if server.command:
                server_dict["command"] = server.command
            if server.connected_at:
                server_dict["connected_at"] = server.connected_at
            if server.status == "disconnected" and server.last_error:
                server_dict["last_error"] = server.last_error
                
            # 获取工具数量
            result = await self.db.execute(
                select(MCPTool).where(MCPTool.server_id == server.id)
            )
            tools = result.scalars().all()
            server_dict["tools_count"] = len(tools)
            
            server_list.append(server_dict)
            
        return server_list
    
    async def get_server(self, server_id: str) -> Optional[MCPServer]:
        """根据ID获取MCP服务器"""
        result = await self.db.execute(
            select(MCPServer).where(MCPServer.id == server_id)
        )
        return result.scalars().first()
    
    async def connect_server(self, server_id: str) -> Dict[str, Any]:
        """连接到MCP服务器"""
        server = await self.get_server(server_id)
        if not server:
            raise ValueError(f"MCP服务器不存在: {server_id}")
        
        # 实现实际的连接逻辑
        try:
            if server.server_type == "sse":
                if not server.url:
                    raise ValueError("SSE服务器需要URL")
                await self.mcp_clients.connect_sse(server_url=server.url, server_id=server_id)
            elif server.server_type == "stdio":
                if not server.command:
                    raise ValueError("stdio服务器需要命令")
                # 分割命令和参数
                parts = server.command.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                await self.mcp_clients.connect_stdio(command=command, args=args, server_id=server_id)
            else:
                raise ValueError(f"不支持的服务器类型: {server.server_type}")
                
            # 存储会话和同步数据库中的工具
            self._running_servers[server_id] = self.mcp_clients.sessions[server_id]
            await self._sync_server_tools(server_id)
            
            # 更新服务器状态
            now = datetime.now()
            server.status = "connected"
            server.connected_at = now
            server.last_error = None
            
            await self.db.commit()
            await self.db.refresh(server)
            
            return {
                "status": "connected",
                "connected_at": now
            }
        
        except Exception as e:
            # 连接失败，更新错误状态
            server.status = "error"
            server.last_error = str(e)
            await self.db.commit()
            
            logger.error(f"连接到MCP服务器失败: {e}")
            raise ValueError(f"连接失败: {str(e)}")
    
    async def disconnect_server(self, server_id: str) -> Dict[str, Any]:
        """断开MCP服务器连接"""
        server = await self.get_server(server_id)
        if not server:
            raise ValueError(f"MCP服务器不存在: {server_id}")
        
        # 实现断开连接逻辑
        try:
            await self.mcp_clients.disconnect(server_id)
            self._running_servers.pop(server_id, None)
            
            # 更新服务器状态
            now = datetime.now()
            server.status = "disconnected"
            
            await self.db.commit()
            await self.db.refresh(server)
            
            return {
                "status": "disconnected",
                "disconnected_at": now
            }
        except Exception as e:
            logger.error(f"断开MCP服务器连接失败: {e}")
            server.last_error = str(e)
            await self.db.commit()
            raise
    
    async def _sync_server_tools(self, server_id: str) -> None:
        """同步服务器工具到数据库"""
        # 先删除现有的工具记录
        await self.db.execute(
            delete(MCPTool).where(MCPTool.server_id == server_id)
        )
        
        # 获取所有工具
        server_tools = [t for t in self.mcp_clients.tools if getattr(t, 'server_id', '') == server_id]
        
        # 创建新的工具记录
        for tool in server_tools:
            if isinstance(tool, MCPClientTool):
                mcp_tool = MCPTool(
                    id=f"{server_id}_{tool.original_name}",
                    name=tool.name,
                    description=tool.description,
                    original_name=tool.original_name,
                    parameters=tool.parameters,
                    server_id=server_id,
                    connection_id=server_id,  # 可以使用相同的ID作为连接ID
                    created_at=datetime.now()
                )
                self.db.add(mcp_tool)
        
        await self.db.commit()
        
    async def add_server_config(
        self,
        server_id: str,
        name: str,
        server_type: str,
        url: Optional[str] = None,
        command: Optional[str] = None,
        auto_connect: bool = False
    ) -> Dict[str, Any]:
        """添加新的MCP服务器配置"""
        # 检查是否已存在同ID服务器
        existing = await self.get_server(server_id)
        if existing:
            raise ValueError(f"已存在ID为 '{server_id}' 的MCP服务器")
        
        # 创建新服务器配置
        server = MCPServer(
            id=server_id,
            name=name,
            server_type=server_type,
            url=url,
            command=command,
            auto_connect=auto_connect,
            status="disconnected",
            created_at=datetime.now()
        )
        
        self.db.add(server)
        await self.db.commit()
        await self.db.refresh(server)
        
        # 如果设置了自动连接，尝试连接
        if auto_connect:
            await self.connect_server(server_id)
        
        return {
            "id": server.id,
            "name": server.name,
            "type": server.server_type,
            "url": server.url,
            "command": server.command,
            "auto_connect": server.auto_connect,
            "created_at": server.created_at
        }
    
    async def delete_server_config(self, server_id: str) -> bool:
        """删除MCP服务器配置"""
        server = await self.get_server(server_id)
        if not server:
            return False
        
        # 如果服务器已连接，先断开连接
        if server.status == "connected":
            await self.disconnect_server(server_id)
        
        # 删除关联的工具
        await self.db.execute(
            delete(MCPTool).where(MCPTool.server_id == server_id)
        )
        
        # 删除服务器配置
        await self.db.delete(server)
        await self.db.commit()
        
        return True
    
    # MCP工具管理
    
    async def list_all_tools(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有可用工具列表"""
        if server_id:
            result = await self.db.execute(
                select(MCPTool).where(MCPTool.server_id == server_id)
            )
        else:
            result = await self.db.execute(select(MCPTool))
            
        tools = result.scalars().all()
        
        tool_list = []
        for tool in tools:
            tool_list.append({
                "name": tool.name,
                "description": tool.description,
                "server_id": tool.server_id,
                "original_name": tool.original_name,
                "parameters": tool.parameters
            })
            
        return tool_list
    
    async def execute_tool(
        self,
        tool_name: str,
        server_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行MCP工具"""
        # 检查服务器是否存在且已连接
        server = await self.get_server(server_id)
        if not server:
            raise ValueError(f"MCP服务器不存在: {server_id}")
            
        if server.status != "connected":
            raise ValueError(f"MCP服务器未连接: {server_id}")
        
        # 检查工具是否存在
        result = await self.db.execute(
            select(MCPTool).where(
                MCPTool.name == tool_name,
                MCPTool.server_id == server_id
            )
        )
        tool = result.scalars().first()
        
        if not tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 创建执行记录
        execution_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
        execution = MCPToolExecution(
            id=execution_id,
            tool_name=tool_name,
            server_id=server_id,
            parameters=parameters,
            status="running",
            start_time=datetime.now()
        )
        
        self.db.add(execution)
        await self.db.commit()
        
        try:
            # 实际执行工具
            tool_instance = next((t for t in self.mcp_clients.tools 
                                 if t.name == tool_name and getattr(t, 'server_id', '') == server_id), None)
            
            if not tool_instance:
                raise ValueError(f"找不到工具实例: {tool_name}")
            
            # 执行工具
            tool_result = await tool_instance.execute(**parameters)
            
            if hasattr(tool_result, 'error') and tool_result.error:
                # 执行出错
                result = {
                    "status": "failed",
                    "error": tool_result.error
                }
                execution.status = "failed"
                execution.error = tool_result.error
            else:
                # 执行成功
                result = {
                    "status": "completed",
                    "output": tool_result.output
                }
                execution.status = "completed"
                execution.result = result
            
            # 更新执行记录
            execution.end_time = datetime.now()
            execution.duration_ms = int((execution.end_time - execution.start_time).total_seconds() * 1000)
            
            await self.db.commit()
            
            return {
                "execution_id": execution_id,
                "result": result
            }
            
        except Exception as e:
            # 更新执行记录为失败
            execution.status = "failed"
            execution.end_time = datetime.now()
            execution.error = str(e)
            execution.duration_ms = int((execution.end_time - execution.start_time).total_seconds() * 1000)
            
            await self.db.commit()
            
            # 重新抛出异常
            raise
    
    async def get_tool_execution_history(
        self,
        tool_name: Optional[str] = None,
        server_id: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取工具执行历史记录"""
        # 构建查询
        query = select(MCPToolExecution)
        
        if tool_name:
            query = query.where(MCPToolExecution.tool_name == tool_name)
        
        if server_id:
            query = query.where(MCPToolExecution.server_id == server_id)
        
        # 获取总数
        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())
        
        # 应用分页
        query = query.order_by(MCPToolExecution.start_time.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        # 执行查询
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        # 格式化结果
        history = []
        for execution in executions:
            history_item = {
                "execution_id": execution.id,
                "tool_name": execution.tool_name,
                "server_id": execution.server_id,
                "parameters": execution.parameters,
                "status": execution.status,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "duration_ms": execution.duration_ms
            }
            
            if execution.result:
                history_item["result"] = execution.result
                
            if execution.error:
                history_item["error"] = execution.error
                
            history.append(history_item)
            
        return history, total 