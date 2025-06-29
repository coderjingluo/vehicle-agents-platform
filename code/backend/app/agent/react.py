"""
KunlunSec AI Platform - ReAct智能体模块

实现基于Reasoning and Acting模式的智能体。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from pydantic import Field

from app.agent.base import BaseAgent, AgentState, LLM, Memory

class ReActAgent(BaseAgent, ABC):
    """ReAct模式智能体"""
    
    name: str
    description: Optional[str] = None
    
    system_prompt: Optional[str] = None
    next_step_prompt: Optional[str] = None
    
    llm: Optional[LLM] = Field(default_factory=LLM)
    memory: Memory = Field(default_factory=Memory)
    state: AgentState = AgentState.IDLE
    
    max_steps: int = 10
    current_step: int = 0
    
    @abstractmethod
    async def think(self) -> bool:
        """处理当前状态并决定下一步行动"""
        pass
    
    @abstractmethod
    async def act(self) -> str:
        """执行决定的行动"""
        pass
    
    async def step(self) -> str:
        """执行单个步骤: 思考和行动"""
        should_act = await self.think()
        if not should_act:
            return "思考完成 - 无需行动"
        return await self.act() 