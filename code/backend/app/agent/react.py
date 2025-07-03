"""
KunlunSec AI Platform - ReAct智能体模块

实现基于Reasoning and Acting模式的智能体。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from pydantic import Field
from app.core.logging import logger

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
    
    # 动态规划相关属性
    completed_steps: List[str] = Field(default_factory=list)
    completed_subtasks: List[str] = Field(default_factory=list)
    
    async def think(self) -> bool:
        """思考并决定下一步行动
        
        Returns:
            bool: 是否继续执行
        """
        logger.info(f"react.py think...")
        # 检查是否有执行计划
        has_plan = hasattr(self, 'current_plan') and self.current_plan and 'subtasks' in self.current_plan
        
        if has_plan:
            # 识别当前正在执行的子任务和步骤
            current_subtask, current_step = self._identify_current_task_and_step()
            
            if current_subtask:
                subtask_name = current_subtask.get("name", "未命名子任务")
                subtask_id = current_subtask.get("id", "unknown")
                logger.info(f"执行子任务: {subtask_name} (ID: {subtask_id})")
                
                if current_step:
                    step_desc = current_step.get("description", "未描述步骤")
                    step_id = current_step.get("id", "unknown")
                    logger.info(f"执行步骤: {step_desc} (ID: {step_id})")
                    
                    # 更新步骤状态
                    self._update_step_status(subtask_id, step_id, "in_progress")
        
        # 构建提示消息
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # 添加记忆中的消息
        for message in self.memory.get_messages():
            messages.append(message)
        
        # 构建下一步提示
        if self.next_step_prompt:
            messages.append({"role": "user", "content": self.next_step_prompt})
        
        # 调用LLM获取响应
        try:
            logger.info(f"智能体 {self.name} 正在思考下一步行动...")
            response = await self.llm.ask(messages)
            logger.info(f"智能体 {self.name} 思考完成，响应长度: {len(response)}")
            
            # 将助手消息添加到记忆
            self.update_memory("assistant", response)
            
            # 检查是否有完成消息
            if self._check_for_completion(response):
                logger.info(f"智能体 {self.name} 检测到完成消息，停止执行")
                
                # 更新子任务和步骤状态
                if has_plan and current_subtask and current_step:
                    self._update_step_status(subtask_id, step_id, "completed", response)
                    
                    # 检查是否所有步骤都已完成
                    all_steps_completed = all(
                        step.get("status") == "completed" 
                        for step in current_subtask.get("steps", [])
                    )
                    
                    if all_steps_completed:
                        logger.info(f"子任务 {subtask_id} 的所有步骤已完成")
                        
                        # 更新子任务状态
                        for subtask in self.subtasks:
                            if subtask.get("id") == subtask_id:
                                subtask["status"] = "completed"
                                subtask["end_time"] = datetime.now()
                                break
                
                return False
            
            return True
        except Exception as e:
            logger.error(f"思考过程中出错: {str(e)}")
            
            # 更新步骤状态为失败
            if has_plan and current_subtask and current_step:
                self._update_step_status(subtask_id, step_id, "failed", str(e))
            
            raise

    async def _react_with_prompt(self, prompt: str) -> bool:
        """使用提供的提示执行ReAct思考过程
        
        Args:
            prompt: 提示文本
            
        Returns:
            bool: 是否继续执行
        """
        # 构建提示消息
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            # 格式化系统提示，添加工具描述
            formatted_system_prompt = self.system_prompt.format(
                tools_description=self._get_tools_description()
            )
            messages.append({"role": "system", "content": formatted_system_prompt})
        
        # 添加历史消息
        for msg in self.memory.messages:
            messages.append(msg)
        
        # 添加当前思考提示
        messages.append({"role": "user", "content": prompt})
        
        try:
            # 发送请求给LLM
            response = await self.llm.ask(
                messages=messages,
                format="json_object",
                max_tokens=1024,
                temperature=0.7
            )
            
            # 解析JSON响应
            parsed_response = self._parse_response(response)
            
            # 更新内存
            if parsed_response:
                self.update_memory("assistant", parsed_response)
            
            # 如果有工具调用，处理它们
            tool_calls = self._extract_tool_calls(parsed_response)
            if tool_calls:
                # 调用工具并处理结果
                await self._process_tool_calls(tool_calls)
                
                # 如果动态规划已启用，更新任务进度
                if hasattr(self, 'current_plan') and self.current_plan:
                    self._update_step_progress()
                
                return True
            elif "answer" in parsed_response or "final_answer" in parsed_response:
                # 如果回答包含终结答案，标记为完成
                logger.info("智能体生成了最终答案，任务完成")
                self.state = AgentState.FINISHED
                
                # 如果动态规划已启用，更新任务进度
                if hasattr(self, 'current_plan') and self.current_plan:
                    self._complete_current_subtask()
                
                return False
            else:
                # 没有工具调用，也没有终结答案，继续执行
                return True
        except Exception as e:
            logger.error(f"思考过程中出错: {str(e)}")
            self.update_memory("system", f"思考错误: {str(e)}")
            return False
    
    def _identify_current_task_and_step(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """识别当前正在执行的子任务和步骤
        
        通过分析内存中的消息和任务状态，确定当前正在执行的子任务和步骤。
        
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]: 当前子任务和步骤
        """
        if not hasattr(self, 'current_plan') or not self.current_plan:
            return None, None
        
        subtasks = self.current_plan.get('subtasks', [])
        if not subtasks:
            return None, None
        
        # 检查子任务状态
        for subtask in subtasks:
            # 如果子任务有状态且为"执行中"，则为当前子任务
            if subtask.get('status') == "执行中":
                # 查找当前步骤
                steps = subtask.get('steps', [])
                for step in steps:
                    if step.get('status') == "执行中":
                        return subtask, step
                
                # 如果没有执行中的步骤，查找第一个未完成的步骤
                for step in steps:
                    if step.get('status') != "已完成":
                        return subtask, step
                
                # 所有步骤已完成，但子任务仍在执行中
                return subtask, None
        
        # 如果没有找到执行中的子任务，查找第一个未完成的子任务
        for subtask in subtasks:
            if subtask.get('status') != "已完成":
                # 将该子任务标记为执行中
                subtask['status'] = "执行中"
                
                # 查找第一个步骤
                steps = subtask.get('steps', [])
                if steps:
                    steps[0]['status'] = "执行中"
                    return subtask, steps[0]
                else:
                    return subtask, None
        
        # 所有子任务都已完成
        return None, None
    
    def _update_step_status(self, subtask_id: str, step_id: str, status: str, response: str = ""):
        """更新步骤状态
        
        Args:
            subtask_id: 子任务ID
            step_id: 步骤ID
            status: 新状态
            response: 响应文本
        """
        # 更新步骤状态
        for subtask in self.current_plan.get('subtasks', []):
            if subtask.get('id') == subtask_id:
                for step in subtask.get('steps', []):
                    if step.get('id') == step_id:
                        step['status'] = status
                        step['response'] = response
                        break
                break
        
        # 如果步骤已完成，检查是否所有步骤都已完成
        if status == "已完成":
            all_steps_completed = all(s.get('status') == "已完成" for s in self.current_plan.get('subtasks', []) if s.get('id') == subtask_id)
            if all_steps_completed:
                for subtask in self.current_plan.get('subtasks', []):
                    if subtask.get('id') == subtask_id:
                        subtask['status'] = "已完成"
                        subtask['end_time'] = datetime.now()
                        break
            
            # 将子任务ID添加到已完成子任务列表中
            if subtask_id not in self.completed_subtasks:
                self.completed_subtasks.append(subtask_id)
            
            # 将步骤ID添加到已完成步骤列表中
            if step_id not in self.completed_steps:
                self.completed_steps.append(step_id)
    
    def _advance_to_next_step_or_subtask(self, current_subtask: Dict[str, Any], current_step: Dict[str, Any]):
        """前进到下一个步骤或子任务
        
        当前步骤完成后，自动前进到下一个步骤或子任务。
        
        Args:
            current_subtask: 当前子任务
            current_step: 当前步骤
        """
        # 获取所有步骤
        steps = current_subtask.get('steps', [])
        if not steps:
            return
        
        # 找到当前步骤的索引
        try:
            current_index = steps.index(current_step)
        except ValueError:
            return
        
        # 如果有下一个步骤，将其标记为执行中
        if current_index < len(steps) - 1:
            next_step = steps[current_index + 1]
            next_step['status'] = "执行中"
        else:
            # 当前子任务的所有步骤已完成，查找下一个子任务
            self._advance_to_next_subtask()
    
    def _advance_to_next_subtask(self):
        """前进到下一个子任务"""
        if not hasattr(self, 'current_plan') or not self.current_plan:
            return
        
        subtasks = self.current_plan.get('subtasks', [])
        if not subtasks:
            return
        
        # 找到当前执行中的子任务
        current_subtask = None
        current_index = -1
        
        for i, subtask in enumerate(subtasks):
            if subtask.get('status') == "执行中":
                current_subtask = subtask
                current_index = i
                break
        
        if current_subtask and current_index >= 0:
            # 将当前子任务标记为已完成
            current_subtask['status'] = "已完成"
            
            # 如果有下一个子任务，将其标记为执行中
            if current_index < len(subtasks) - 1:
                next_subtask = subtasks[current_index + 1]
                next_subtask['status'] = "执行中"
                
                # 将下一个子任务的第一个步骤标记为执行中
                next_steps = next_subtask.get('steps', [])
                if next_steps:
                    next_steps[0]['status'] = "执行中"
    
    def _get_next_step(self, subtask: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取子任务的下一个未完成步骤"""
        if not subtask or "steps" not in subtask:
            return None
            
        for step in subtask.get("steps", []):
            if step.get('status') != "已完成":
                return step
                
        return None
    
    def _get_next_subtask(self) -> Optional[Dict[str, Any]]:
        """获取下一个未完成的子任务"""
        if not hasattr(self, 'current_plan') or not self.current_plan:
            return None
        
        subtasks = self.current_plan.get('subtasks', [])
        if not subtasks:
            return None
        
        for subtask in subtasks:
            if subtask.get('status') != "已完成":
                return subtask
        
        return None
            
    def _update_step_progress(self):
        """更新当前步骤的进度"""
        current_subtask, current_step = self._identify_current_task_and_step()
        if current_subtask and current_step:
            self._update_step_status(current_subtask.get('id'), current_step.get('id'), "已完成")
            self._advance_to_next_step_or_subtask(current_subtask, current_step)
    
    def _complete_current_subtask(self):
        """完成当前子任务"""
        current_subtask, _ = self._identify_current_task_and_step()
        if current_subtask:
            current_subtask['status'] = "已完成"
            
            # 将所有该子任务的步骤标记为已完成
            for step in current_subtask.get("steps", []):
                step['status'] = "已完成"
                
                # 将步骤ID添加到已完成步骤列表中
                step_id = step.get("id")
                if step_id and step_id not in self.completed_steps:
                    self.completed_steps.append(step_id)
            
            # 将子任务ID添加到已完成子任务列表中
            subtask_id = current_subtask.get("id")
            if subtask_id and subtask_id not in self.completed_subtasks:
                self.completed_subtasks.append(subtask_id)
            
            # 前进到下一个子任务
            self._advance_to_next_subtask()
    
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