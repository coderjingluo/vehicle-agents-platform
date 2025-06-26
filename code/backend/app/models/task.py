"""
任务和智能体执行相关的数据模型

定义任务状态、智能体执行请求/响应、状态监控等模型
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, ConfigDict
import uuid

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
    TARA = "tara"                       # TARA智能体
    TEST_CASE = "test_case"             # 测试用例智能体
    AUTOMATION_TEST = "automation_test" # 自动化测试智能体
    REPORT_ANALYSIS = "report_analysis" # 报告分析智能体
    KNOWLEDGE_BASE = "knowledge_base"   # 知识库智能体


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
    task_metadata = Column(JSON, comment="任务元数据")
    
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
            "metadata": self.task_metadata,
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


# 基础任务模型
class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务元数据")


class TaskCreate(TaskBase):
    """创建任务请求模型"""
    agent_type: AgentType = Field(..., description="执行智能体类型")
    user_request: str = Field(..., description="用户请求内容")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")
    timeout: Optional[int] = Field(300, description="超时时间(秒)")


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    title: Optional[str] = Field(None, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: Optional[TaskPriority] = Field(None, description="优先级")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="任务元数据")


class TaskResponse(TaskBase):
    """任务响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="任务ID")
    agent_type: AgentType = Field(..., description="执行智能体类型")
    status: TaskStatus = Field(..., description="任务状态")
    user_request: str = Field(..., description="用户请求内容")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    plan: Optional[Dict[str, Any]] = Field(None, description="执行计划")
    progress: float = Field(0.0, description="执行进度(0-100)")
    timeout: int = Field(300, description="超时时间(秒)")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始执行时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 执行信息
    agent_instance_id: Optional[str] = Field(None, description="智能体实例ID")
    execution_duration: Optional[float] = Field(None, description="执行耗时(秒)")


# 智能体执行相关模型
class AgentExecutionRequest(BaseModel):
    """智能体执行请求"""
    user_request: str = Field(..., description="用户请求内容")
    context: Optional[Dict[str, Any]] = Field(default=None, description="执行上下文")
    timeout: Optional[int] = Field(default=300, description="超时时间(秒)")
    priority: Optional[str] = Field(default="normal", description="优先级")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="请求元数据")
    
    # 新增：智能规划相关参数
    enable_planning: Optional[bool] = Field(default=False, description="启用智能步骤分配")
    step_by_step: Optional[bool] = Field(default=False, description="启用步骤化执行")
    chat_mode: Optional[bool] = Field(default=False, description="启用聊天模式")
    stream: Optional[bool] = Field(default=False, description="启用流式响应")
    
    # 新增：智能体特定配置
    agent_config: Optional[Dict[str, Any]] = Field(default=None, description="智能体特定配置")
    
class PlanStep(BaseModel):
    """执行步骤"""
    step_id: str
    title: str
    description: str
    tools: Optional[List[str]] = None
    status: str = "pending"  # pending, running, completed, failed
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    
class ExecutionPlan(BaseModel):
    """执行计划"""
    plan_id: str
    description: str
    steps: List[PlanStep]
    total_steps: int
    completed_steps: int = 0
    
class StreamEvent(BaseModel):
    """流式事件"""
    event_type: str  # planning, step_start, step_progress, step_completed, result, error
    timestamp: str
    data: Dict[str, Any]
    
class ChatMessage(BaseModel):
    """聊天消息"""
    message_id: str
    type: str  # user, agent, system
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class AgentExecutionResponse(BaseModel):
    """智能体执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    task_id: str = Field(..., description="任务ID")
    agent_type: str = Field(..., description="智能体类型")
    agent_instance_id: str = Field(..., description="智能体实例ID")
    plan: Optional[Dict[str, Any]] = Field(None, description="执行计划")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    status: TaskStatus = Field(..., description="任务状态")
    error: Optional[str] = Field(None, description="错误信息")
    execution_duration: Optional[float] = Field(None, description="执行耗时(秒)")
    timestamp: datetime = Field(..., description="响应时间")


# 智能体状态监控模型
class AgentStatus(BaseModel):
    """智能体状态模型"""
    agent_type: str = Field(..., description="智能体类型")
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    instance_status: str = Field(..., description="实例状态 (active/inactive)")
    instance_id: Optional[str] = Field(None, description="实例ID")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    task_stats: Dict[str, int] = Field(default_factory=dict, description="任务统计")
    timestamp: datetime = Field(..., description="状态时间")


class AgentMetrics(BaseModel):
    """智能体性能指标模型"""
    agent_type: str = Field(..., description="智能体类型")
    period_days: int = Field(..., description="统计周期(天)")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    average_execution_time: float = Field(..., description="平均执行时间(秒)")
    success_rate: float = Field(..., description="成功率(%)")
    avg_response_time: float = Field(..., description="平均响应时间(秒)")
    error_rate: float = Field(..., description="错误率(%)")
    resource_usage: Dict[str, float] = Field(default_factory=dict, description="资源使用情况")
    timestamp: datetime = Field(..., description="指标时间")


# 批量执行模型
class BatchExecutionRequest(BaseModel):
    """批量执行请求模型"""
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表")
    max_concurrent: int = Field(5, description="最大并发数")
    timeout: int = Field(600, description="批次超时时间(秒)")
    fail_fast: bool = Field(False, description="遇到错误是否快速失败")


class BatchExecutionResponse(BaseModel):
    """批量执行响应模型"""
    success: bool = Field(..., description="批次是否成功")
    batch_id: str = Field(..., description="批次ID")
    task_ids: List[str] = Field(..., description="任务ID列表")
    total_tasks: int = Field(..., description="总任务数")
    submitted_tasks: int = Field(..., description="已提交任务数")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(..., description="响应时间")


class BatchStatus(BaseModel):
    """批次状态模型"""
    batch_id: str = Field(..., description="批次ID")
    total_tasks: int = Field(..., description="总任务数")
    status_stats: Dict[str, int] = Field(default_factory=dict, description="状态统计")
    progress: float = Field(..., description="进度百分比")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="任务列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    timestamp: datetime = Field(..., description="状态时间")


# 工作流相关模型
class WorkflowStatus(str, PyEnum):
    """工作流状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowExecution(BaseModel):
    """工作流执行模型"""
    workflow_id: str = Field(..., description="工作流ID")
    user_request: str = Field(..., description="用户请求")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    status: WorkflowStatus = Field(..., description="工作流状态")
    current_step: Optional[str] = Field(None, description="当前步骤")
    steps_completed: int = Field(0, description="已完成步骤数")
    total_steps: int = Field(0, description="总步骤数")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求模型"""
    user_request: str = Field(..., description="用户请求内容")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")
    max_iterations: int = Field(10, description="最大迭代次数")
    max_retries: int = Field(3, description="最大重试次数")
    timeout: int = Field(600, description="总超时时间(秒)")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    workflow_id: str = Field(..., description="工作流ID")
    status: WorkflowStatus = Field(..., description="工作流状态")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    steps_executed: int = Field(..., description="已执行步骤数")
    execution_duration: Optional[float] = Field(None, description="执行耗时(秒)")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(..., description="响应时间")


# 实时监控模型
class TaskProgressUpdate(BaseModel):
    """任务进度更新模型"""
    task_id: str = Field(..., description="任务ID")
    agent_type: str = Field(..., description="智能体类型")
    progress: float = Field(..., description="进度百分比")
    current_step: str = Field(..., description="当前步骤")
    message: Optional[str] = Field(None, description="进度消息")
    timestamp: datetime = Field(..., description="更新时间")


class SystemStatus(BaseModel):
    """系统状态模型"""
    status: str = Field(..., description="系统状态")
    uptime: float = Field(..., description="运行时间(秒)")
    active_agents: int = Field(..., description="活跃智能体数")
    active_tasks: int = Field(..., description="活跃任务数")
    total_requests: int = Field(..., description="总请求数")
    memory_usage: float = Field(..., description="内存使用率(%)")
    cpu_usage: float = Field(..., description="CPU使用率(%)")
    timestamp: datetime = Field(..., description="状态时间")


# 错误处理模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(..., description="错误时间")
    request_id: Optional[str] = Field(None, description="请求ID")


# 工具调用模型
class ToolExecutionRequest(BaseModel):
    """工具执行请求模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文")
    timeout: int = Field(60, description="超时时间(秒)")


class ToolExecutionResponse(BaseModel):
    """工具执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    tool_name: str = Field(..., description="工具名称")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间(秒)")
    timestamp: datetime = Field(..., description="响应时间")


# 配置模型
class APIConfiguration(BaseModel):
    """API配置模型"""
    max_concurrent_tasks: int = Field(50, description="最大并发任务数")
    default_timeout: int = Field(300, description="默认超时时间(秒)")
    enable_streaming: bool = Field(True, description="启用流式响应")
    enable_caching: bool = Field(True, description="启用缓存")
    log_level: str = Field("INFO", description="日志级别")
    rate_limit: Dict[str, int] = Field(default_factory=dict, description="速率限制配置")


# 导出所有模型
__all__ = [
    # 枚举
    "TaskStatus",
    "TaskPriority", 
    "AgentType",
    "WorkflowStatus",
    
    # 任务相关
    "TaskBase",
    "TaskCreate",
    "TaskUpdate", 
    "TaskResponse",
    
    # 智能体执行
    "AgentExecutionRequest",
    "AgentExecutionResponse",
    "AgentStatus",
    "AgentMetrics",
    
    # 批量执行
    "BatchExecutionRequest",
    "BatchExecutionResponse",
    "BatchStatus",
    
    # 工作流
    "WorkflowExecution",
    "WorkflowExecutionRequest",
    "WorkflowExecutionResponse",
    
    # 监控
    "TaskProgressUpdate",
    "SystemStatus",
    
    # 工具
    "ToolExecutionRequest",
    "ToolExecutionResponse",
    
    # 错误处理
    "ErrorResponse",
    
    # 配置
    "APIConfiguration"
]