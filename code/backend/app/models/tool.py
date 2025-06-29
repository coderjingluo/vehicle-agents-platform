"""
KunlunSec AI Platform - 工具模型

定义工具相关的数据库模型和方法。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, 
    ForeignKey, Integer, Enum, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class ToolCategory(str, enum.Enum):
    """工具类别枚举"""
    SYSTEM = "system"              # 系统工具
    AI = "ai"                      # AI工具
    KNOWLEDGE = "knowledge"        # 知识管理工具
    CODE = "code"                  # 代码分析工具
    PLANNING = "planning"          # 规划工具
    BROWSER = "browser"            # 浏览工具
    RESEARCH = "research"          # 研究工具
    MCP = "mcp"                    # MCP工具
    CUSTOM = "custom"              # 自定义工具

class ToolStatus(str, enum.Enum):
    """工具执行状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    TIMEOUT = "timeout"       # 执行超时

class Tool(Base):
    """工具模型"""
    
    __tablename__ = "tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 工具类别和配置
    category = Column(Enum(ToolCategory), nullable=False)
    config = Column(JSON, default={})
    
    # 工具定义
    schema = Column(JSON, default={})  # 工具参数和返回值定义
    
    # 工具状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统预定义工具
    
    # MCP工具特定字段
    is_mcp = Column(Boolean, default=False)
    mcp_endpoint = Column(String(255), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tool {self.name} ({self.category})>"

class ToolExecution(Base):
    """工具执行记录模型"""
    
    __tablename__ = "tool_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联工具
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False)
    tool = relationship("Tool", backref="executions")
    
    # 执行状态
    status = Column(Enum(ToolStatus), default=ToolStatus.PENDING, nullable=False)
    
    # 执行详情
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 执行指标
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    
    # 关联
    agent_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_executions.id"), nullable=True)
    agent_execution = relationship("AgentExecution", backref="tool_executions")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ToolExecution {self.id} ({self.status})>"

class MCPConnection(Base):
    """MCP连接模型"""
    
    __tablename__ = "mcp_connections"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    connection_type = Column(String(50), nullable=False)  # sse, websocket, etc.
    url = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="disconnected")  # connected, disconnected, connecting, error
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    tools = relationship("MCPTool", back_populates="connection", cascade="all, delete-orphan")


class MCPTool(Base):
    """MCP工具模型"""
    
    __tablename__ = "mcp_tools"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    original_name = Column(String(100), nullable=False)  # 原始工具名称
    parameters = Column(JSON, nullable=True)  # 工具参数定义
    connection_id = Column(String(36), ForeignKey("mcp_connections.id"), nullable=False)
    server_id = Column(String(36), nullable=False, index=True)  # 关联的服务器ID
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    connection = relationship("MCPConnection", back_populates="tools")


class MCPServer(Base):
    """MCP服务器模型"""
    
    __tablename__ = "mcp_servers"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    server_type = Column(String(50), nullable=False)  # sse, stdio, etc.
    url = Column(String(255), nullable=True)
    command = Column(String(255), nullable=True)
    auto_connect = Column(Boolean, default=False)
    status = Column(String(50), default="disconnected")  # connected, disconnected, connecting, error
    connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class MCPToolExecution(Base):
    """MCP工具执行历史模型"""
    
    __tablename__ = "mcp_tool_executions"
    
    id = Column(String(36), primary_key=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    server_id = Column(String(36), nullable=False, index=True)
    parameters = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True) 