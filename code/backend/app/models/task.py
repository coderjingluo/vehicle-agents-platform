"""
任务数据模型
包含任务的基础信息、状态管理和执行计划
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class TaskStatus(PyEnum):
    """任务状态枚举"""
    PENDING = "pending"         # 待处理
    PLANNING = "planning"       # 计划生成中
    RUNNING = "running"         # 执行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"     # 已取消


class TaskPriority(PyEnum):
    """任务优先级枚举"""
    LOW = "low"         # 低优先级
    MEDIUM = "medium"   # 中优先级
    HIGH = "high"       # 高优先级
    URGENT = "urgent"   # 紧急


class AgentType(PyEnum):
    """智能体类型枚举"""
    TARA = "tara"               # TARA智能体
    TESTCASE = "testcase"       # 测试用例智能体
    AUTOTEST = "autotest"       # 自动化测试智能体
    REPORT = "report"           # 报告分析智能体


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    # 基础信息
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    title = Column(String(255), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    agent_type = Column(Enum(AgentType), nullable=False, comment="智能体类型")
    
    # 状态管理
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, comment="任务优先级")
    progress = Column(Integer, default=0, comment="任务进度(0-100)")
    
    # 数据
    input_data = Column(JSON, comment="输入数据")
    output_data = Column(JSON, comment="输出数据")
    plan = Column(JSON, comment="执行计划")
    metadata = Column(JSON, comment="元数据")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    started_at = Column(DateTime(timezone=True), comment="开始时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_details = Column(JSON, comment="错误详情")
    
    # 用户信息
    user_id = Column(String(255), comment="用户ID")
    
    # 配置
    config = Column(JSON, comment="任务配置")
    is_template = Column(Boolean, default=False, comment="是否为模板")
    template_name = Column(String(255), comment="模板名称")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_running(self) -> bool:
        """判断任务是否正在运行"""
        return self.status in [TaskStatus.PLANNING, TaskStatus.RUNNING]
    
    @property
    def is_completed(self) -> bool:
        """判断任务是否已完成"""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """判断任务是否失败"""
        return self.status == TaskStatus.FAILED
    
    @property
    def duration(self) -> Optional[float]:
        """计算任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "progress": self.progress,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "plan": self.plan,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "user_id": self.user_id,
            "config": self.config,
            "is_template": self.is_template,
            "template_name": self.template_name,
            "duration": self.duration
        } 