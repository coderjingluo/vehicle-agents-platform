from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FlowStatus(str, Enum):
    """执行流状态枚举"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 执行完成
    FAILED = "failed"         # 执行失败
    PAUSED = "paused"         # 已暂停


class FlowStep(BaseModel):
    """执行流步骤定义"""
    id: str                               # 步骤ID
    name: str                             # 步骤名称
    description: Optional[str] = None     # 步骤描述
    status: FlowStatus = FlowStatus.PENDING  # 当前状态
    input: Dict[str, Any] = {}            # 输入参数
    output: Optional[Dict[str, Any]] = None  # 输出结果
    error: Optional[str] = None           # 错误信息
    executor: Optional[str] = None        # 执行器（如智能体名称）
    dependencies: List[str] = []          # 依赖的步骤ID
    retry_count: int = 0                  # 已重试次数
    max_retries: int = 3                  # 最大重试次数


class BaseFlow(ABC):
    """执行流基类"""
    
    def __init__(self, flow_id: str, name: str, description: Optional[str] = None):
        self.id = flow_id                            # 流程ID
        self.name = name                             # 流程名称
        self.description = description               # 流程描述
        self.status = FlowStatus.PENDING             # 当前状态
        self.steps: Dict[str, FlowStep] = {}         # 步骤字典
        self.current_step_id: Optional[str] = None   # 当前执行的步骤ID
        self.context: Dict[str, Any] = {}            # 上下文数据
        self.error: Optional[str] = None             # 错误信息
    
    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """初始化执行流，创建步骤和设置初始参数"""
        pass
    
    @abstractmethod
    async def execute_step(self, step: FlowStep) -> FlowStep:
        """执行单个步骤"""
        pass
    
    async def execute(self) -> bool:
        """执行整个流程"""
        if self.status == FlowStatus.RUNNING:
            raise RuntimeError("Flow is already running")
        
        try:
            # 更新状态为运行中
            self.status = FlowStatus.RUNNING
            
            # 获取未执行或失败的步骤
            pending_steps = self._get_executable_steps()
            
            # 循环执行步骤直到所有步骤完成
            while pending_steps:
                # 获取下一个可执行步骤
                step_id = next(iter(pending_steps))
                step = self.steps[step_id]
                
                # 更新当前步骤
                self.current_step_id = step_id
                
                # 执行步骤
                try:
                    self.steps[step_id] = await self.execute_step(step)
                except Exception as e:
                    # 步骤执行失败
                    self.steps[step_id].status = FlowStatus.FAILED
                    self.steps[step_id].error = str(e)
                    
                    # 检查是否需要重试
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        self.steps[step_id].status = FlowStatus.PENDING
                    else:
                        # 超过最大重试次数，整个流程失败
                        self.status = FlowStatus.FAILED
                        self.error = f"Step {step_id} failed: {str(e)}"
                        return False
                
                # 更新可执行步骤列表
                pending_steps = self._get_executable_steps()
            
            # 所有步骤执行完成
            self.status = FlowStatus.COMPLETED
            return True
        except Exception as e:
            # 流程执行异常
            self.status = FlowStatus.FAILED
            self.error = str(e)
            return False
    
    def _get_executable_steps(self) -> Dict[str, FlowStep]:
        """获取当前可执行的步骤"""
        executable = {}
        
        for step_id, step in self.steps.items():
            # 跳过已完成的步骤
            if step.status == FlowStatus.COMPLETED:
                continue
            
            # 检查是否状态为未执行
            if step.status != FlowStatus.PENDING:
                continue
            
            # 检查依赖是否满足
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_step = self.steps.get(dep_id)
                if not dep_step or dep_step.status != FlowStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                executable[step_id] = step
        
        return executable
    
    async def pause(self) -> bool:
        """暂停执行流"""
        if self.status != FlowStatus.RUNNING:
            return False
        
        self.status = FlowStatus.PAUSED
        return True
    
    async def resume(self) -> bool:
        """恢复执行流"""
        if self.status != FlowStatus.PAUSED:
            return False
        
        self.status = FlowStatus.RUNNING
        return await self.execute()
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态和进度"""
        total_steps = len(self.steps)
        completed_steps = sum(1 for step in self.steps.values() if step.status == FlowStatus.COMPLETED)
        failed_steps = sum(1 for step in self.steps.values() if step.status == FlowStatus.FAILED)
        
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "progress": {
                "total": total_steps,
                "completed": completed_steps,
                "failed": failed_steps,
                "pending": total_steps - completed_steps - failed_steps,
                "percentage": int(completed_steps / total_steps * 100) if total_steps > 0 else 0
            },
            "current_step": self.current_step_id,
            "error": self.error
        }
    
    def get_result(self) -> Dict[str, Any]:
        """获取执行流的结果"""
        if self.status != FlowStatus.COMPLETED:
            raise ValueError(f"Flow is not completed yet, current status: {self.status}")
        
        results = {}
        for step_id, step in self.steps.items():
            if step.output:
                results[step_id] = step.output
        
        return {
            "flow_id": self.id,
            "results": results,
            "context": self.context
        } 