"""
KunlunSec AI Platform - 智能体模型

定义智能体相关的数据库模型和方法。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, 
    ForeignKey, Integer, Enum, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base

class AgentType(str, enum.Enum):
    """智能体类型枚举"""
    TARA = "tara"                    # TARA分析智能体
    TEST_CASE = "test_case"          # 测试用例智能体
    AUTOMATION_TEST = "automation"    # 自动化测试智能体
    REPORT_ANALYSIS = "report"       # 报告分析智能体
    DATA_ANALYSIS = "data_analysis"  # 数据分析智能体
    CUSTOM = "custom"                # 自定义智能体

class AgentStatus(str, enum.Enum):
    """智能体状态枚举"""
    IDLE = "idle"           # 空闲状态
    RUNNING = "running"     # 运行中
    FINISHED = "finished"   # 执行完成
    ERROR = "error"         # 错误状态

class Agent(Base):
    """智能体模型"""
    
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 智能体类型
    agent_type = Column(Enum(AgentType), nullable=False)
    
    # 配置
    config = Column(JSON, default={})
    
    # 关联模型
    model_id = Column(UUID(as_uuid=True), ForeignKey("model_configs.id"), nullable=True)
    model = relationship("ModelConfig", backref="agents")
    
    # 权限和状态
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User", backref="created_agents")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Agent {self.name} ({self.agent_type})>"

class AgentExecution(Base):
    """智能体执行记录模型"""
    
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(Enum(AgentType), nullable=False)
    agent_name = Column(String(255), nullable=False)
    
    # 执行状态
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE, nullable=False)
    
    # 执行详情
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 执行步骤
    steps = Column(JSON, default=[])
    current_step = Column(Integer, default=0)
    
    # 执行指标
    token_usage = Column(JSON, default={})
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    
    # 关联
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    task = relationship("Task", backref="agent_executions")
    
    flow_step_id = Column(UUID(as_uuid=True), ForeignKey("flow_steps.id"), nullable=True)
    flow_step = relationship("FlowStep", backref="agent_execution")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AgentExecution {self.id} ({self.agent_type}, {self.status})>" 