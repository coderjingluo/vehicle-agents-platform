"""
MCP相关的模式定义
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MCPConnectionCreate(BaseModel):
    """创建MCP连接请求模式"""
    name: str = Field(..., description="连接名称")
    type: str = Field(..., description="连接类型")
    url: str = Field(..., description="连接URL")
    description: Optional[str] = Field(None, description="连接描述")


class MCPConnectionResponse(BaseModel):
    """MCP连接响应模式"""
    id: str
    name: str
    type: str
    url: str
    description: Optional[str]
    status: str
    last_heartbeat: Optional[datetime]
    tool_count: int = 0
    
    class Config:
        orm_mode = True


class MCPToolResponse(BaseModel):
    """MCP工具响应模式"""
    name: str
    description: Optional[str]
    parameters: Dict[str, Any]
    
    class Config:
        orm_mode = True


class MCPConnectionDetailResponse(BaseModel):
    """MCP连接详情响应模式"""
    id: str
    name: str
    type: str
    url: str
    description: Optional[str]
    status: str
    last_heartbeat: Optional[datetime]
    tools: List[MCPToolResponse]
    
    class Config:
        orm_mode = True


class MCPServerResponse(BaseModel):
    """MCP服务器响应模式"""
    id: str
    name: str
    type: str
    url: Optional[str]
    command: Optional[str]
    status: str
    connected_at: Optional[datetime]
    tools_count: int = 0
    last_error: Optional[str]
    
    class Config:
        orm_mode = True


class MCPServerCreate(BaseModel):
    """创建MCP服务器请求模式"""
    id: str = Field(..., description="服务器ID")
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器类型")
    url: Optional[str] = Field(None, description="服务器URL")
    command: Optional[str] = Field(None, description="服务器命令")
    auto_connect: bool = Field(False, description="是否自动连接")


class MCPToolExecutionResponse(BaseModel):
    """MCP工具执行响应模式"""
    execution_id: str
    tool_name: str
    server_id: str
    parameters: Dict[str, Any]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    
    class Config:
        orm_mode = True


class MCPToolExecuteRequest(BaseModel):
    """执行MCP工具请求模式"""
    tool_name: str = Field(..., description="工具名称")
    server_id: str = Field(..., description="服务器ID")
    parameters: Dict[str, Any] = Field(..., description="工具参数")


class MCPToolExecutionListResponse(BaseModel):
    """MCP工具执行历史列表响应模式"""
    history: List[MCPToolExecutionResponse]
    pagination: Dict[str, Any]
