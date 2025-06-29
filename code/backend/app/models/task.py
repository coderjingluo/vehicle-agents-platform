"""
KunlunSec AI Platform - 任务模型

定义任务数据库模型和相关方法。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, String, DateTime, Text, 
    ForeignKey, Integer, Enum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    PAUSED = "paused"         # 已暂停
    CANCELLED = "cancelled"   # 已取消

class TaskType(str, enum.Enum):
    """任务类型枚举"""
    TARA = "tara"                    # TARA分析任务
    TEST_CASE = "test_case"          # 测试用例生成任务
    AUTOMATION = "automation"        # 自动化测试任务
    REPORT = "report"                # 报告生成任务
    KNOWLEDGE = "knowledge"          # 知识库管理任务
    CUSTOM = "custom"                # 自定义任务

class Task(Base):
    """任务模型"""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 任务类型和状态
    type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # 任务详情
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="tasks")
    
    # 关联执行流
    flow_execution_id = Column(UUID(as_uuid=True), ForeignKey("flow_executions.id"), nullable=True)
    flow_execution = relationship("FlowExecution", backref="task")
    
    # 任务进度
    progress = Column(Integer, default=0)  # 0-100
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Task {self.name} ({self.type}, {self.status})>" 