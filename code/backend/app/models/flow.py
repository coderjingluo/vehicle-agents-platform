"""
KunlunSec AI Platform - 执行流模型

定义执行流相关的数据库模型和方法。
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

class FlowStatus(str, enum.Enum):
    """执行流状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    PAUSED = "paused"         # 已暂停
    CANCELLED = "cancelled"   # 已取消

class FlowType(str, enum.Enum):
    """执行流类型枚举"""
    PLANNING = "planning"              # 规划执行流
    TARA = "tara"                      # TARA分析流
    TEST_CASE = "test_case"            # 测试用例生成流
    AUTOMATION = "automation"          # 自动化测试流
    REPORT = "report"                  # 报告生成流
    CUSTOM = "custom"                  # 自定义流

class Flow(Base):
    """执行流模板模型"""
    
    __tablename__ = "flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 流类型和配置
    type = Column(Enum(FlowType), nullable=False)
    config = Column(JSON, default={})
    
    # 流定义
    definition = Column(JSON, default={})
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="flows")
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统预定义流
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Flow {self.name} ({self.type})>"

class FlowExecution(Base):
    """执行流执行实例模型"""
    
    __tablename__ = "flow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联流模板
    flow_id = Column(UUID(as_uuid=True), ForeignKey("flows.id"), nullable=False)
    flow = relationship("Flow", backref="executions")
    
    # 执行状态
    status = Column(Enum(FlowStatus), default=FlowStatus.PENDING, nullable=False)
    
    # 执行详情
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    context = Column(JSON, default={})  # 执行上下文
    
    # 执行进度
    progress = Column(Integer, default=0)  # 0-100
    
    # 执行指标
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="flow_executions")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<FlowExecution {self.id} ({self.status})>"

class FlowStep(Base):
    """执行流步骤模型"""
    
    __tablename__ = "flow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_id = Column(String(255), nullable=False)  # 步骤标识符
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 关联执行流实例
    flow_execution_id = Column(UUID(as_uuid=True), ForeignKey("flow_executions.id"), nullable=False)
    flow_execution = relationship("FlowExecution", backref="steps")
    
    # 步骤配置
    executor = Column(String(255), nullable=True)  # 执行者（智能体类型）
    dependencies = Column(ARRAY(String), default=[])  # 依赖的步骤ID
    
    # 步骤状态
    status = Column(Enum(FlowStatus), default=FlowStatus.PENDING, nullable=False)
    
    # 步骤详情
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<FlowStep {self.step_id} ({self.name}, {self.status})>" 