"""
KunlunSec AI Platform - 工具调用智能体模块

实现基于工具调用的智能体。
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, Union, Tuple
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field

from app.agent.react import ReActAgent
from app.agent.base import LLM, Memory, AgentState
from app.core.logging import logger
from app.tool.base import BaseTool as Tool
from app.tool.tool_collection import ToolCollection, get_global_tool_collection

# 工具调用相关类型定义
class ToolChoice(str, Enum):
    """工具选择模式"""
    AUTO = "auto"           # 自动选择工具
    REQUIRED = "required"   # 必须使用工具
    NONE = "none"           # 不使用工具

TOOL_CHOICE_TYPE = Union[ToolChoice, str, Dict[str, Any]]

class ToolCall(BaseModel):
    """工具调用"""
    function: Dict[str, Any]  # 函数信息
    id: Optional[str] = None  # 调用ID

# 系统提示模板
SYSTEM_PROMPT = """你是一个能够使用工具的AI助手。你可以使用以下工具:
{tools_description}

请仔细思考如何解决问题，并在需要时使用适当的工具。
"""

NEXT_STEP_PROMPT = """请根据当前状态，决定下一步行动。你可以选择使用工具或直接回答。"""

class ToolCallAgent(ReActAgent):
    """工具调用智能体"""
    
    name: str = "toolcall"
    description: str = "能够执行工具调用的智能体"
    
    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT
    
    available_tools: Any = None  # 将在initialize中设置
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=lambda: ["terminate"])
    
    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None
    
    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None
    
    # 动态规划增强
    planning_system_prompt: str = """你是一个智能规划专家，擅长将复杂任务分解为子任务和具体步骤。
    请为用户提供的任务创建详细的执行计划，包括子任务分解和工具使用规划。
    确保计划是动态的，且适应于实际需求，而不是固定的步骤。"""
    
    async def initialize(self, **kwargs) -> None:
        """初始化智能体，设置全局工具集合"""
        await super().initialize(**kwargs)
        
        # 使用全局工具集合
        self.available_tools = get_global_tool_collection()
        
        # 添加关于可用工具的系统消息
        tool_names = self.available_tools.get_tool_names()
        tools_info = ", ".join(tool_names)
        
        self.update_memory(
            "system",
            f"可用工具已更新: {tools_info}"
        )
    
    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """增强的计划生成方法，考虑可用工具"""
        # 获取所有可用工具信息
        tools_info = self._get_tools_description()
        
        # 构建规划提示
        planning_prompt = f"""
        请为以下任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 可用工具
        {tools_info}
        
        # 要求
        1. 将该任务分解为多个逻辑子任务
        2. 每个子任务应进一步分解为具体步骤
        3. 为每个步骤指定可能需要使用的工具
        4. 确定步骤之间的依赖关系
        5. 计划必须是动态生成的，不能是固定步骤
        
        # 规划格式
        请提供JSON格式的执行计划，包含以下内容:
        
        ```json
        {{
            "main_task": "任务简要描述",
            "subtasks": [
                {{
                    "id": "subtask-1",
                    "name": "子任务名称",
                    "description": "详细描述",
                    "steps": [
                        {{
                            "id": "step-1.1",
                            "description": "步骤描述",
                            "tools": ["可能需要使用的工具名称"],
                            "expected_output": "期望输出描述"
                        }},
                        // 更多步骤...
                    ],
                    "dependencies": []  // 依赖的其他子任务ID
                }},
                // 更多子任务...
            ]
        }}
        ```
        
        请确保计划逻辑合理，步骤清晰，并针对具体任务特点进行规划。
        """
        
        logger.info(f"正在为任务生成执行计划: {task[:50]}...")
        
        try:
            # 向LLM发送规划请求，使用专门的规划系统提示
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": self.planning_system_prompt},
                    {"role": "user", "content": planning_prompt}
                ]
            )
            
            # 提取JSON部分
            import re
            import json
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response
            
            try:
                # 解析JSON计划
                plan = json.loads(json_str)
                logger.info(f"成功生成执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                
                # 保存计划到智能体
                self.current_plan = plan
                self.subtasks = plan.get('subtasks', [])
                
                # 将规划添加到记忆中
                self.update_memory(
                    "system",
                    f"已生成动态任务执行计划，包含 {len(self.subtasks)} 个子任务。"
                )
                
                return plan
            except json.JSONDecodeError as e:
                logger.error(f"解析执行计划失败: {str(e)}")
                return await super().generate_plan(task)
                
        except Exception as e:
            logger.error(f"生成执行计划时出错: {str(e)}")
            return await super().generate_plan(task)

    def _get_tools_description(self) -> str:
        """获取可用工具的描述列表
        
        Returns:
            str: 格式化的工具描述列表
        """
        tool_descriptions = []
        for tool in self.available_tools.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)

    async def think(self) -> bool:
        """思考并决定下一步行动，支持工具调用
        
        Returns:
            bool: 是否继续执行
        """
        logger.info(f"toolcall.py think...")
        # 检查是否有执行计划
        has_plan = hasattr(self, 'current_plan') and self.current_plan and 'subtasks' in self.current_plan
        
        # 识别当前正在执行的子任务和步骤
        current_subtask, current_step = None, None
        if has_plan:
            current_subtask, current_step = self._identify_current_task_and_step()
            if current_subtask and current_step:
                logger.info(f"当前执行: 子任务={current_subtask.get('name', '未命名')}, 步骤={current_step.get('description', '未描述')}")
        
        # 构建提示消息
        prompt_messages = []
        
        # 添加系统提示
        if self.system_prompt:
            prompt_messages.append({"role": "system", "content": self.system_prompt})
        
        # 添加记忆中的消息
        for message in self.memory.get_messages():
            prompt_messages.append(message)
        
        # 构建下一步提示
        prompt = self.next_step_prompt
        
        # 如果有执行计划，添加计划上下文
        if has_plan and current_subtask and current_step:
            subtask_name = current_subtask.get("name", "未命名子任务")
            step_desc = current_step.get("description", "未描述步骤")
            tools = current_step.get("tools", [])
            
            plan_context = f"""
            ## 当前执行计划状态
            你正在执行的子任务: {subtask_name}
            子任务描述: {current_subtask.get('description', '无描述')}
            当前步骤: {step_desc}
            预期输出: {current_step.get('expected_output', '无预期输出')}
            推荐工具: {', '.join(tools)}
            """
            
            prompt = f"{plan_context}\n\n{prompt}"
            logger.info(f"已将执行计划上下文添加到提示中，推荐工具: {tools}")
        
        # 添加下一步提示
        prompt_messages.append({"role": "user", "content": prompt})
        
        # 获取可用工具
        available_tools = []
        if hasattr(self, 'available_tools') and self.available_tools:
            if hasattr(self.available_tools, 'tools'):
                available_tools = self.available_tools.tools
            elif hasattr(self.available_tools, 'to_params'):
                available_tools = self.available_tools.to_params()
        
        # 确定是否需要使用工具
        needs_tools = (has_plan and current_step and current_step.get('tools')) or available_tools
        
        # 调用LLM获取响应
        try:
            logger.info(f"智能体 {self.name} 正在思考下一步行动...")
            
            if needs_tools:
                # 使用ask_tool方法处理工具调用
                logger.info(f"使用ask_tool方法处理可能的工具调用")
                response = await self.llm.ask_tool(
                    messages=prompt_messages,
                    tools=[tool.to_dict() if hasattr(tool, 'to_dict') else tool for tool in available_tools] if available_tools else None,
                    temperature=0.7
                )
                
                # 检查响应中的工具调用
                tool_calls = response.get('tool_calls', [])
                if tool_calls:
                    logger.info(f"从响应中获取到 {len(tool_calls)} 个工具调用")
                    for i, call in enumerate(tool_calls):
                        function_name = call.get('function', {}).get('name', '未知工具')
                        function_args = call.get('function', {}).get('arguments', '{}')
                        logger.info(f"工具调用 {i+1}: {function_name}, 参数: {function_args}")
                else:
                    logger.info("响应中没有工具调用")
            else:
                # 不需要工具时使用普通ask方法
                logger.info(f"使用普通ask方法获取文本响应")
                response_text = await self.llm.ask(
                    messages=prompt_messages,
                    temperature=0.7
                )
                response = {"content": response_text, "role": "assistant"}
                tool_calls = []
            
            # 处理响应
            content = response.get('content', '')
            logger.info(f"智能体 {self.name} 思考完成，响应长度: {len(content) if content else 0}")
            
            # 如果有工具调用，处理它们
            if 'tool_calls' in response and response['tool_calls']:
                # 如果有执行计划，更新当前步骤状态
                if has_plan and current_subtask and current_step:
                    self._update_step_status(current_subtask, current_step, "执行中")
                    logger.info(f"更新步骤状态: {step_desc} -> 执行中")
                
                # 添加助手消息到内存（包含工具调用）
                self.update_memory("assistant", content, tool_calls=response['tool_calls'])
                
                # 执行工具调用
                logger.info(f"开始执行 {len(response['tool_calls'])} 个工具调用")
                await self._process_tool_calls(response['tool_calls'])
                
                # 如果有执行计划，更新当前步骤状态为完成
                if has_plan and current_subtask and current_step:
                    self._update_step_status(current_subtask, current_step, "已完成")
                    logger.info(f"更新步骤状态: {step_desc} -> 已完成")
                    
                    # 检查是否需要更新到下一个步骤或子任务
                    logger.info("检查是否需要前进到下一个步骤或子任务")
                    self._advance_to_next_step_or_subtask(current_subtask, current_step)
                
                return True
            else:
                # 如果没有工具调用，但有有效响应，添加到内存
                if content and content.strip():
                    logger.info("无工具调用，但有文本响应，添加到内存")
                    self.update_memory("assistant", content)
                    return True
                else:
                    logger.warning("无工具调用且无有效响应")
                    return False
        except Exception as e:
            logger.error(f"思考过程中出错: {str(e)}", exc_info=True)
            self.update_memory("system", f"思考过程中出错: {str(e)}")
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
        
        # 记录当前处理的子任务ID，用于保持一致性
        current_subtask_id = getattr(self, '_current_subtask_id', None)
        
        # 如果有正在跟踪的子任务ID，首先尝试查找该子任务
        if current_subtask_id:
            current_subtask = next((s for s in subtasks if s.get('id') == current_subtask_id), None)
            if current_subtask:
                # 检查子任务状态，如果已完成则不再返回该子任务
                if current_subtask.get('status') in ["已完成", "completed"]:
                    logger.info(f"子任务 {current_subtask_id} 已完成，尝试查找下一个子任务")
                    # 清除当前子任务ID，后面会查找下一个子任务
                    self._current_subtask_id = None
                else:    
                    # 如果子任务仍在执行中，查找当前执行中的步骤
                    steps = current_subtask.get('steps', [])
                    executing_step = next((s for s in steps if s.get('status') in ["执行中", "in_progress"]), None)
                    if executing_step:
                        return current_subtask, executing_step
                    
                    # 如果没有执行中的步骤，查找第一个未完成的步骤
                    pending_step = next((s for s in steps if s.get('status') not in ["已完成", "completed"]), None)
                    if pending_step:
                        return current_subtask, pending_step
                    
                    # 如果子任务所有步骤都已完成，但子任务仍未标记为完成，返回子任务和None
                    logger.info(f"子任务 {current_subtask_id} 的所有步骤已完成，但子任务状态为: {current_subtask.get('status')}")
                    return current_subtask, None
        
        # 如果没有正在跟踪的子任务或已完成，查找状态为"执行中"的子任务
        executing_subtask = next((s for s in subtasks if s.get('status') in ["执行中", "in_progress"]), None)
        if executing_subtask:
            steps = executing_subtask.get('steps', [])
            self._current_subtask_id = executing_subtask.get('id')
            logger.info(f"找到执行中的子任务: {executing_subtask.get('name')} (ID: {self._current_subtask_id})")
            
            # 查找执行中的步骤
            executing_step = next((s for s in steps if s.get('status') in ["执行中", "in_progress"]), None)
            if executing_step:
                return executing_subtask, executing_step
            
            # 如果没有执行中的步骤，查找第一个未完成的步骤
            pending_step = next((s for s in steps if s.get('status') not in ["已完成", "completed"]), None)
            if pending_step:
                return executing_subtask, pending_step
            
            # 如果找不到未完成的步骤，返回子任务和None
            return executing_subtask, None
        
        # 如果没有执行中的子任务，查找第一个未完成的子任务
        pending_subtask = next((s for s in subtasks if s.get('status') not in ["已完成", "completed"]), None)
        if pending_subtask:
            # 将该子任务标记为执行中
            pending_subtask['status'] = "执行中"
            
            # 记录新的当前子任务ID
            self._current_subtask_id = pending_subtask.get('id')
            logger.info(f"开始新子任务: {pending_subtask.get('name')} (ID: {self._current_subtask_id})")
            
            # 查找第一个步骤
            steps = pending_subtask.get('steps', [])
            if steps:
                first_step = steps[0]
                first_step['status'] = "执行中"
                return pending_subtask, first_step
            else:
                return pending_subtask, None
        
        # 所有子任务都已完成
        self._current_subtask_id = None
        logger.info("所有子任务都已完成")
        return None, None
    
    def _update_step_status(self, subtask: Dict[str, Any], step: Dict[str, Any], status: str):
        """更新步骤状态
        
        Args:
            subtask: 子任务
            step: 步骤
            status: 新状态
        """
        if not subtask or not step:
            return
            
        step_id = step.get('id')
        if not step_id:
            return
            
        step['status'] = status
        step['update_time'] = datetime.now().isoformat()
        
        # 如果步骤已完成，检查是否需要更新子任务状态
        if status in ["已完成", "completed"]:
            # 检查子任务的所有步骤是否都已完成
            steps = subtask.get('steps', [])
            all_completed = all(s.get('status') in ["已完成", "completed"] for s in steps)
            
            if all_completed:
                subtask['status'] = "已完成"
                subtask['update_time'] = datetime.now().isoformat()
                logger.info(f"子任务 {subtask.get('name')} 的所有步骤已完成，更新子任务状态为已完成")
    
    def _advance_to_next_step_or_subtask(self, current_subtask: Dict[str, Any], current_step: Dict[str, Any]):
        """前进到下一个步骤或子任务
        
        当前步骤完成后，自动前进到下一个步骤或子任务。
        
        Args:
            current_subtask: 当前子任务
            current_step: 当前步骤
        """
        if not current_subtask or not current_step:
            logger.warning("无法前进到下一步骤：当前子任务或步骤为空")
            return
            
        # 获取当前子任务和步骤的ID用于日志和跟踪
        subtask_id = current_subtask.get('id', 'unknown')
        subtask_name = current_subtask.get('name', '未命名子任务')
        step_id = current_step.get('id', 'unknown')
        step_desc = current_step.get('description', '未描述步骤')
        
        # 标记当前步骤为已完成
        current_step['status'] = "已完成"
        logger.info(f"步骤 {step_id}: {step_desc} 已完成")
        
        # 获取所有步骤
        steps = current_subtask.get('steps', [])
        if not steps:
            # 如果子任务没有步骤，直接标记为已完成并前进到下一个子任务
            current_subtask['status'] = "已完成"
            logger.info(f"子任务 {subtask_name} (ID: {subtask_id}) 已完成(无步骤)")
            self._advance_to_next_subtask()
            return
        
        # 找到当前步骤的索引
        try:
            current_index = next(i for i, s in enumerate(steps) if s.get('id') == step_id)
        except StopIteration:
            logger.warning(f"无法找到当前步骤: {step_id}")
            return
        
        # 检查是否有下一个步骤
        if current_index < len(steps) - 1:
            next_step = steps[current_index + 1]
            next_step_id = next_step.get('id', 'unknown')
            next_step_desc = next_step.get('description', '未描述步骤')
            
            # 检查下一步骤是否已经完成
            if next_step.get('status') in ["已完成", "completed"]:
                logger.info(f"步骤 {next_step_id}: {next_step_desc} 已经完成，查找下一个未完成步骤")
                
                # 寻找下一个未完成的步骤
                next_incomplete_step = None
                for i in range(current_index + 2, len(steps)):
                    if steps[i].get('status') not in ["已完成", "completed"]:
                        next_incomplete_step = steps[i]
                        break
                
                if next_incomplete_step:
                    # 找到了未完成的步骤
                    next_incomplete_step['status'] = "执行中"
                    logger.info(f"前进到步骤: {next_incomplete_step.get('description', '未描述')}")
                else:
                    # 所有步骤都已完成，标记子任务为已完成
                    current_subtask['status'] = "已完成"
                    logger.info(f"子任务 {subtask_name} (ID: {subtask_id}) 已完成(所有步骤已完成)")
                    self._advance_to_next_subtask()
            else:
                # 下一个步骤未完成，将其标记为执行中
                next_step['status'] = "执行中"
                logger.info(f"前进到下一个步骤: {next_step_desc} (ID: {next_step_id})")
        else:
            # 当前是最后一个步骤，所有步骤已完成
            current_subtask['status'] = "已完成"
            logger.info(f"子任务 {subtask_name} (ID: {subtask_id}) 已完成(最后步骤已完成)")
            
            # 前进到下一个子任务
            self._advance_to_next_subtask()
    
    def _advance_to_next_subtask(self):
        """前进到下一个子任务"""
        if not hasattr(self, 'current_plan') or not self.current_plan:
            logger.warning("无法前进到下一子任务：当前计划为空")
            return
        
        subtasks = self.current_plan.get('subtasks', [])
        if not subtasks:
            logger.warning("无法前进到下一子任务：子任务列表为空")
            return
        
        # 获取当前子任务ID
        current_subtask_id = getattr(self, '_current_subtask_id', None)
        if not current_subtask_id:
            logger.warning("无法前进到下一子任务：当前子任务ID未知")
            # 尝试查找第一个未完成的子任务
            pending_subtask = next((s for s in subtasks if s.get('status') not in ["已完成", "completed"]), None)
            if pending_subtask:
                pending_subtask['status'] = "执行中"
                self._current_subtask_id = pending_subtask.get('id')
                logger.info(f"开始子任务: {pending_subtask.get('name')} (ID: {self._current_subtask_id})")
                
                # 将第一个步骤标记为执行中
                steps = pending_subtask.get('steps', [])
                if steps:
                    steps[0]['status'] = "执行中"
            return
        
        # 查找当前子任务
        current_subtask_index = -1
        for i, subtask in enumerate(subtasks):
            if subtask.get('id') == current_subtask_id:
                current_subtask_index = i
                break
        
        if current_subtask_index == -1:
            logger.warning(f"无法找到当前子任务: {current_subtask_id}")
            return
        
        # 查找下一个子任务：检查依赖关系
        next_executable_subtask = None
        for subtask in subtasks:
            # 跳过当前子任务和已完成子任务
            if subtask.get('id') == current_subtask_id or subtask.get('status') in ["已完成", "completed"]:
                continue
                
            # 检查依赖是否满足
            dependencies = subtask.get('dependencies', [])
            dependencies_met = True
            for dep in dependencies:
                dep_subtask = next((s for s in subtasks if s.get('id') == dep), None)
                if not dep_subtask or dep_subtask.get('status') not in ["已完成", "completed"]:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                next_executable_subtask = subtask
                break
        
        # 如果找到了可执行的下一个子任务
        if next_executable_subtask:
            next_subtask_id = next_executable_subtask.get('id')
            next_subtask_name = next_executable_subtask.get('name', '未命名子任务')
            
            # 标记为执行中
            next_executable_subtask['status'] = "执行中"
            
            # 更新当前子任务ID
            self._current_subtask_id = next_subtask_id
            logger.info(f"前进到下一个子任务: {next_subtask_name} (ID: {next_subtask_id})")
            
            # 将第一个步骤标记为执行中
            steps = next_executable_subtask.get('steps', [])
            if steps:
                steps[0]['status'] = "执行中"
                logger.info(f"开始执行步骤: {steps[0].get('description', '未描述步骤')}")
        else:
            # 没有更多可执行的子任务
            self._current_subtask_id = None
            logger.info("所有子任务已完成或无法执行下一个子任务(依赖未满足)")
    
    def _update_step_status(self, subtask: Dict[str, Any], step: Dict[str, Any], status: str):
        """更新步骤状态
        
        Args:
            subtask: 子任务
            step: 步骤
            status: 新状态
        """
        if not subtask or not step:
            return
            
        step_id = step.get('id')
        if not step_id:
            return
            
        step['status'] = status
        step['update_time'] = datetime.now().isoformat()
        
        # 如果步骤已完成，检查是否需要更新子任务状态
        if status in ["已完成", "completed"]:
            # 检查子任务的所有步骤是否都已完成
            steps = subtask.get('steps', [])
            all_completed = all(s.get('status') in ["已完成", "completed"] for s in steps)
            
            if all_completed:
                subtask['status'] = "已完成"
                subtask['update_time'] = datetime.now().isoformat()
                logger.info(f"子任务 {subtask.get('name')} 的所有步骤已完成，更新子任务状态为已完成")
    
    async def act(self) -> str:
        """执行动作，使用工具调用"""
        if not self.tool_calls:
            logger.info(f"🤔 {self.name} 没有选择使用工具")
            return ""
        
        results = []
        
        for call in self.tool_calls:
            try:
                # 检查call是否为ToolCall对象或标准dict格式
                tool_call_id = None
                name = None
                arguments = None
                
                if isinstance(call, ToolCall):
                    # ToolCall类型
                    tool_call_id = getattr(call, 'id', None)
                    if hasattr(call, 'function') and call.function:
                        name = call.function.get("name", "")
                        arguments = call.function.get("arguments", "{}")
                    else:
                        logger.error(f"ToolCall对象缺少function字段: {call}")
                        results.append(f"错误: 工具调用缺少function字段")
                        continue
                elif isinstance(call, dict):
                    # dict类型，检查格式
                    tool_call_id = call.get("id")
                    
                    if "function" in call:
                        # 标准格式
                        function = call["function"]
                        if isinstance(function, dict):
                            name = function.get("name", "")
                            arguments = function.get("arguments", "{}")
                        else:
                            logger.error(f"function字段不是字典: {function}")
                            results.append(f"错误: function字段格式无效")
                            continue
                    else:
                        # 尝试直接获取name和arguments
                        name = call.get("name", "")
                        arguments = call.get("arguments", "{}")
                        if not name:
                            logger.error(f"工具调用缺少name字段: {call}")
                            results.append(f"错误: 工具调用缺少name字段")
                            continue
                else:
                    logger.error(f"无效的工具调用类型: {type(call)}")
                    results.append(f"错误: 无效的工具调用格式")
                    continue
                
                # 确保name不为空
                if not name:
                    logger.error("工具名称为空")
                    results.append("错误: 工具名称为空")
                    continue
                
                # 解析参数
                if isinstance(arguments, str):
                    try:
                        args = json.loads(arguments)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析参数JSON: {arguments}，使用文本参数")
                        args = {"text": arguments}  # 回退到使用原始字符串
                else:
                    args = arguments
                
                # 参数名称映射，处理不同的参数命名约定
                function_args = {}
                
                # 特定工具的参数名称映射
                param_mappings = {
                    "web_search": {
                        "search_query": "query",
                        "engine": "search_engine"
                    },
                    "create_chat_completion": {
                        "prompt": "messages"
                    }
                }
                
                # 应用参数映射
                if name in param_mappings and isinstance(args, dict):
                    mapping = param_mappings[name]
                    for old_name, new_name in mapping.items():
                        if old_name in args:
                            function_args[new_name] = args[old_name]
                            logger.info(f"参数映射: {old_name} -> {new_name} = {args[old_name]}")
                
                # 添加所有其他参数
                if isinstance(args, dict):
                    for key, value in args.items():
                        if key not in function_args:  # 避免覆盖已映射的参数
                            function_args[key] = value
                    
                logger.info(f"🔧 执行工具 {name} 参数: {function_args}")
                
                # 执行工具调用
                if isinstance(call, ToolCall):
                    # 更新参数
                    if hasattr(call, "function") and hasattr(call.function, "arguments"):
                        call.function.arguments = json.dumps(function_args)
                    result = await self.execute_tool(call)
                else:
                    # 创建临时ToolCall对象
                    temp_call = {
                        "id": tool_call_id,
                        "function": {"name": name, "arguments": json.dumps(function_args)}
                    }
                    result = await self.execute_tool(temp_call)
                
                # 检查结果是否是协程对象，如果是则等待其完成
                if asyncio.iscoroutine(result):
                    logger.info(f"工具 {name} 返回了协程对象，等待其完成...")
                    result = await result
                
                # 检查是否需要处理特殊工具
                if self._is_special_tool(name):
                    await self._handle_special_tool(name, result, **args)
                    
                # 更新工具使用记录
                self.update_memory(
                    "tool", 
                    result if isinstance(result, str) else json.dumps(result, ensure_ascii=False),
                    tool_call_id=tool_call_id,
                    name=name
                )
                
                # 将结果添加到列表
                results.append(result)
                
                # 如果在执行计划中，更新当前步骤状态
                if hasattr(self, 'current_plan') and self.current_plan:
                    # 获取当前子任务和步骤
                    current_subtask, current_step = self._identify_current_task_and_step()
                    if current_subtask and current_step:
                        logger.info(f"更新当前步骤 {current_step.get('id')} 的状态")
                        if name in current_step.get('tools', []):
                            # 更新步骤状态
                            self._update_step_status(current_subtask, current_step, "已完成")
                            logger.info(f"步骤 {current_step.get('id')} 使用了工具 {name}，标记为已完成")
                            # 前进到下一个步骤
                            self._advance_to_next_step_or_subtask(current_subtask, current_step)
                
            except Exception as e:
                error_msg = f"工具 {name if name else '未知'} 执行出错: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.update_memory("tool", error_msg, tool_call_id=tool_call_id, name=name)
                results.append(error_msg)
                
        # 清理工具调用列表，避免重复执行
        self.tool_calls = []
                
        # 返回结果
        return "\n".join(str(r) for r in results)

    def get_final_answer(self) -> str:
        """获取最终执行结果"""
        # 检查计划执行情况
        if self.dynamic_planning and self.current_plan:
            total_subtasks = len(self.subtasks)
            completed_subtasks = len(self.completed_subtasks)
            
            # 计算完成度
            completion_percentage = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
            
            # 整合执行情况
            execution_summary = f"任务执行完成度: {completion_percentage:.1f}% ({completed_subtasks}/{total_subtasks} 子任务)"
            
            # 获取最后一条助手消息
            messages = self.memory.get_messages()
            assistant_messages = [m for m in reversed(messages) 
                                if m.get("role") == "assistant" and m.get("content")]
            
            final_message = assistant_messages[0]["content"] if assistant_messages else "无最终结果"
            
            return f"{final_message}\n\n{execution_summary}"
        
        # 如果没有启用动态规划，使用原始方法
        messages = self.memory.get_messages()
        assistant_messages = [m for m in reversed(messages) 
                            if m.get("role") == "assistant" and m.get("content")]
        
        if assistant_messages:
            return assistant_messages[0]["content"]
        else:
            return "智能体未生成最终答案"

    def get_tool_usages(self) -> List[Dict[str, Any]]:
        """获取工具使用记录"""
        tool_usages = []
        
        # 遍历记忆中的消息，寻找工具调用和工具响应
        messages = self.memory.get_messages()
        
        for i, message in enumerate(messages):
            if message.get("role") == "assistant" and "tool_calls" in message:
                for tool_call in message.get("tool_calls", []):
                    # 基本信息
                    usage = {
                        "tool_id": tool_call.get("id"),
                        "tool_name": tool_call.get("function", {}).get("name"),
                        "arguments": tool_call.get("function", {}).get("arguments"),
                        "response": None,  # 将在下面设置
                    }
                    
                    # 查找对应的工具响应
                    for j in range(i+1, len(messages)):
                        if (messages[j].get("role") == "tool" and 
                            messages[j].get("tool_call_id") == tool_call.get("id")):
                            usage["response"] = messages[j].get("content")
                            break
                    
                    tool_usages.append(usage)
        
        # 如果有动态规划，添加工具与计划的关联
        if self.dynamic_planning and self.current_plan:
            for usage in tool_usages:
                # 尝试找到使用该工具的步骤
                for subtask in self.subtasks:
                    for step in subtask.get('steps', []):
                        if usage["tool_name"] in step.get('tools', []):
                            usage["related_step"] = {
                                "subtask_id": subtask.get('id'),
                                "subtask_name": subtask.get('name'),
                                "step_id": step.get('id'),
                                "step_description": step.get('description')
                            }
                            break
        
        return tool_usages
    
    async def execute_tool(self, command: Union[ToolCall, Dict[str, Any]]) -> str:
        """执行单个工具调用并进行错误处理"""
        # 确保command是标准格式
        try:
            # 初始化变量
            tool_call_id = ""
            function_name = ""
            function_args = {}
            
            # 处理不同格式的工具调用
            if isinstance(command, dict):
                tool_call_id = command.get("id", "")
                
                if "function" in command:
                    # 标准格式
                    function = command["function"]
                    if isinstance(function, dict):
                        function_name = function.get("name", "")
                        function_args_str = function.get("arguments", "{}")
                    else:
                        return f"错误: function字段格式无效: {function}"
                elif "name" in command:
                    # 非标准格式1
                    function_name = command.get("name", "")
                    function_args_str = command.get("arguments", "{}")
                elif "tool" in command:
                    # 非标准格式2
                    function_name = command.get("tool", "")
                    function_args_str = command.get("tool_input", "{}")
                else:
                    return "错误: 工具调用缺少必要字段"
                
                # 解析参数
                if isinstance(function_args_str, str):
                    try:
                        import json
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError:
                        function_args = {"input": function_args_str}
                else:
                    function_args = function_args_str
            elif hasattr(command, "function") and command.function:
                # ToolCall对象
                tool_call_id = getattr(command, "id", "")
                
                if isinstance(command.function, dict):
                    function_name = command.function.get("name", "")
                    function_args_str = command.function.get("arguments", "{}")
                else:
                    function_name = getattr(command.function, "name", "")
                    function_args_str = getattr(command.function, "arguments", "{}")
                
                # 解析参数
                if isinstance(function_args_str, str):
                    try:
                        import json
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError:
                        function_args = {"input": function_args_str}
                else:
                    function_args = function_args_str
            else:
                # 尝试从其他属性获取信息
                if hasattr(command, "name"):
                    function_name = getattr(command, "name")
                elif hasattr(command, "function_name"):
                    function_name = getattr(command, "function_name")
                elif hasattr(command, "tool"):
                    function_name = getattr(command, "tool")
                else:
                    return "错误: 无法确定工具名称"
                
                if hasattr(command, "arguments"):
                    function_args_str = getattr(command, "arguments")
                elif hasattr(command, "tool_input"):
                    function_args_str = getattr(command, "tool_input")
                elif hasattr(command, "params"):
                    function_args_str = getattr(command, "params")
                elif hasattr(command, "args"):
                    function_args_str = getattr(command, "args")
                else:
                    function_args_str = "{}"
                
                # 解析参数
                if isinstance(function_args_str, str):
                    try:
                        import json
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError:
                        function_args = {"input": function_args_str}
                else:
                    function_args = function_args_str
            
            # 验证function_name是否存在
            if not function_name:
                return "错误: 无法确定工具名称"
            
            # 检查工具是否存在
            tool = None
            if hasattr(self, 'available_tools'):
                if hasattr(self.available_tools, 'get_tool'):
                    tool = self.available_tools.get_tool(function_name)
                elif hasattr(self.available_tools, 'tools'):
                    tool = next((t for t in self.available_tools.tools if getattr(t, 'name', '') == function_name), None)
            
            if not tool:
                return f"错误: 未知工具 '{function_name}'"
            
            # 参数名称映射，处理不同的参数命名约定
            mapped_args = {}
            
            # 特定工具的参数名称映射
            param_mappings = {
                "web_search": {
                    "search_query": "query",
                    "engine": "search_engine"
                },
                "create_chat_completion": {
                    "prompt": "messages"
                }
            }
            
            # 应用参数映射
            if function_name in param_mappings and isinstance(function_args, dict):
                mapping = param_mappings[function_name]
                for old_name, new_name in mapping.items():
                    if old_name in function_args:
                        mapped_args[new_name] = function_args[old_name]
                        logger.info(f"参数映射: {old_name} -> {new_name} = {function_args[old_name]}")
            
            # 添加所有其他参数
            if isinstance(function_args, dict):
                for key, value in function_args.items():
                    if key not in mapped_args:  # 避免覆盖已映射的参数
                        mapped_args[key] = value
            
            # 使用映射后的参数
            function_args = mapped_args
            
            # 执行工具
            logger.info(f"🔧 激活工具: '{function_name}'，参数: {function_args}")
            
            # 直接调用工具的execute方法，绕过ToolCollection包装器
            try:
                result = await tool.execute(**function_args) if asyncio.iscoroutinefunction(tool.execute) else tool.execute(**function_args)
                
                # 检查结果是否是协程对象，如果是则等待其完成
                if asyncio.iscoroutine(result):
                    logger.info(f"工具 {function_name} 返回了协程对象，等待其完成...")
                    result = await result
                    
            except TypeError as e:
                # 如果有参数类型错误，进行更灵活的参数处理
                logger.warning(f"工具参数不匹配，尝试调整参数: {str(e)}")
                
                if name == "tara_analysis" and "target" in args:
                    # TaraAnalysis工具特殊处理
                    result = await tool.execute(
                        operation="analyze_threat",
                        target_description=args["target"]
                    )
                elif name == "planning" and "task" in args:
                    # Planning工具特殊处理
                    result = await tool.execute(
                        command="create",
                        title=f"计划: {args['task']}",
                        steps=[f"执行任务: {args['task']}"]
                    )
                elif name == "web_search" and "query" in args:
                    # WebSearch工具特殊处理
                    result = await tool.execute(search_query=args["query"])
                elif name == "rag_query" and "query" in args:
                    # RAG查询工具特殊处理
                    result = await tool.execute(query_text=args["query"])
                elif name == "browser_use" and "url" in args:
                    # 浏览器工具特殊处理
                    result = await tool.execute(
                        url=args["url"],
                        action=args.get("action")
                    )
                else:
                    # 尝试调用可能的替代方法
                    if callable(tool):
                        result = await tool(**function_args) if asyncio.iscoroutinefunction(tool) else tool(**function_args)
                    elif hasattr(tool, 'run') and callable(tool.run):
                        result = await tool.run(**function_args) if asyncio.iscoroutinefunction(tool.run) else tool.run(**function_args)
                    elif hasattr(tool, '__call__') and callable(tool.__call__):
                        result = await tool(**function_args) if asyncio.iscoroutinefunction(tool.__call__) else tool(**function_args)
                    else:
                        # 如果没有特殊处理，则抛出原始异常
                        raise
                
                # 检查结果是否是协程对象，如果是则等待其完成
                if asyncio.iscoroutine(result):
                    logger.info(f"工具 {function_name} 返回了协程对象，等待其完成...")
                    result = await result
            
            # 检查是否为特殊工具
            if self._is_special_tool(function_name):
                await self._handle_special_tool(function_name, result, **function_args)
            
            # 提取结果
            final_result = None
            if hasattr(result, "output") and result.output is not None:
                final_result = result.output
            elif hasattr(result, "error") and result.error:
                final_result = f"错误: {result.error}"
            elif hasattr(result, "base64_image") and result.base64_image:
                self._current_base64_image = result.base64_image
                final_result = "图像已生成"
            else:
                final_result = str(result)
                
            # 如果结果是字典类型，则转换为字符串以避免pydantic验证错误
            if isinstance(final_result, dict):
                final_result_str = json.dumps(final_result, ensure_ascii=False, indent=2)
                return final_result_str
            else:
                return final_result
                
        except Exception as e:
            logger.error(f"执行工具调用时出错: {str(e)}", exc_info=True)
            return f"错误: 执行工具调用时出错: {str(e)}"
    
    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """处理特殊工具执行后的状态变更"""
        # 检查结果是否是协程对象，如果是则等待其完成
        if asyncio.iscoroutine(result):
            logger.info(f"特殊工具 {name} 返回了协程对象，等待其完成...")
            result = await result
            
        if name.lower() == "terminate":
            self.state = AgentState.FINISHED
        
        # 处理图像结果
        if hasattr(result, "base64_image") and result.base64_image:
            self._current_base64_image = result.base64_image
            
        return result
    
    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """确定是否应该结束执行"""
        return False
    
    def _is_special_tool(self, name: str) -> bool:
        """检查是否为特殊工具"""
        return name.lower() in [t.lower() for t in self.special_tool_names]
    
    def _parse_tool_calls(self, response: Any) -> List[ToolCall]:
        """解析响应中的工具调用"""
        tool_calls = []
        
        # 处理字典响应
        if isinstance(response, dict):
            # 检查OpenAI格式
            if "tool_calls" in response:
                for call in response.get("tool_calls", []):
                    if "function" in call:
                        tool_calls.append(ToolCall(
                            function=call["function"],
                            id=call.get("id")
                        ))
            # 检查Anthropic格式
            elif "tool_use" in response:
                tool_use = response["tool_use"]
                if isinstance(tool_use, dict) and "name" in tool_use:
                    tool_calls.append(ToolCall(
                        function={
                            "name": tool_use["name"],
                            "arguments": tool_use.get("parameters", {})
                        },
                        id=tool_use.get("id")
                    ))
            # 检查自定义格式
            elif "name" in response and "arguments" in response:
                tool_calls.append(ToolCall(
                    function={
                        "name": response["name"],
                        "arguments": response["arguments"]
                    }
                ))
        
        return tool_calls
    
    async def cleanup(self):
        """清理资源"""
        # 这里可以添加清理代码
        pass
    
    async def run(self, request: Optional[str] = None) -> str:
        """运行智能体"""
        if request:
            self.update_memory("user", request)
        
        self.state = AgentState.IDLE
        self.current_step = 0
        
        try:
            while self.state != AgentState.FINISHED and self.current_step < self.max_steps:
                self.current_step += 1
                
                # 思考
                should_continue = await self.think()
                logger.info(f"should_continue: {should_continue}")
                if not should_continue:
                    break
                
                logger.info(f"执行智能体")
                logger.info(f"self.current_step: {self.current_step}")
                logger.info(f"self.state: {self.__class__.__name__}")
                # 执行
                await self.act()
            
            # 获取最终回答
            final_answer = self.get_final_answer()
            
            # 清理
            await self.cleanup()
            
            return final_answer
        except Exception as e:
            logger.error(f"运行智能体时出错: {str(e)}")
            self.state = AgentState.ERROR
            await self.cleanup() 
            return f"错误: {str(e)}" 

    async def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """处理工具调用
        
        执行工具调用并将结果添加到智能体记忆
        
        Args:
            tool_calls: 工具调用列表
        """
        if not tool_calls:
            return
            
        logger.info(f"开始处理 {len(tool_calls)} 个工具调用")
        
        for tool_call in tool_calls:
            try:
                # 初始化变量
                tool_call_id = ""
                function_name = ""
                function_args_str = "{}"
                
                # 检查工具调用的类型和结构
                if isinstance(tool_call, dict):
                    # 字典类型工具调用
                    tool_call_id = tool_call.get("id", "")
                    
                    if "function" in tool_call:
                        # 标准格式
                        function = tool_call["function"]
                        if isinstance(function, dict):
                            function_name = function.get("name", "")
                            function_args_str = function.get("arguments", "{}")
                        else:
                            logger.error(f"无效的function字段格式: {function}")
                            self.update_memory("system", f"工具调用的function字段格式无效: {str(function)}")
                            continue
                    elif "name" in tool_call:
                        # 非标准格式1: {name: "tool_name", arguments: {...}}
                        function_name = tool_call.get("name", "")
                        function_args_str = tool_call.get("arguments", "{}")
                        
                        # 创建标准格式的工具调用，以便后续处理
                        logger.info(f"转换非标准工具调用格式: name={function_name}")
                        tool_call = {
                            "id": tool_call_id or f"call_{function_name}_{datetime.now().timestamp()}",
                            "function": {
                                "name": function_name,
                                "arguments": function_args_str
                            }
                        }
                    elif "tool" in tool_call:
                        # 非标准格式2: {tool: "tool_name", tool_input: {...}}
                        function_name = tool_call.get("tool", "")
                        function_args_str = tool_call.get("tool_input", "{}")
                        
                        # 创建标准格式的工具调用，以便后续处理
                        logger.info(f"转换非标准工具调用格式: tool={function_name}")
                        tool_call = {
                            "id": tool_call_id or f"call_{function_name}_{datetime.now().timestamp()}",
                            "function": {
                                "name": function_name,
                                "arguments": function_args_str
                            }
                        }
                    else:
                        # 尝试查找任何可能包含工具名称的字段
                        for key, value in tool_call.items():
                            if key in ["name", "tool", "function_name", "tool_name"]:
                                function_name = str(value)
                                break
                        
                        # 尝试查找任何可能包含参数的字段
                        for key, value in tool_call.items():
                            if key in ["arguments", "tool_input", "params", "parameters", "args"]:
                                function_args_str = value
                                break
                        
                        if not function_name:
                            logger.error(f"工具调用缺少name字段: {tool_call}")
                            self.update_memory("system", f"无效的工具调用格式: {tool_call}")
                            continue
                            
                        # 创建标准格式的工具调用，以便后续处理
                        logger.info(f"转换未知格式的工具调用: {function_name}")
                        tool_call = {
                            "id": tool_call_id or f"call_{function_name}_{datetime.now().timestamp()}",
                            "function": {
                                "name": function_name,
                                "arguments": function_args_str
                            }
                        }
                elif hasattr(tool_call, "function") and tool_call.function:
                    # ToolCall类型
                    tool_call_id = getattr(tool_call, "id", "")
                    
                    # 检查function是字典还是对象
                    if isinstance(tool_call.function, dict):
                        function_name = tool_call.function.get("name", "")
                        function_args_str = tool_call.function.get("arguments", "{}")
                    else:
                        # function可能是一个对象，尝试获取属性
                        function_name = getattr(tool_call.function, "name", "")
                        function_args_str = getattr(tool_call.function, "arguments", "{}")
                else:
                    # 处理其他可能的格式
                    tool_call_id = getattr(tool_call, "id", "") if hasattr(tool_call, "id") else ""
                    
                    # 尝试以多种方式获取function_name和function_args_str
                    if hasattr(tool_call, "name"):
                        function_name = getattr(tool_call, "name")
                    elif hasattr(tool_call, "function_name"):
                        function_name = getattr(tool_call, "function_name")
                    elif hasattr(tool_call, "tool"):
                        function_name = getattr(tool_call, "tool")
                    
                    if hasattr(tool_call, "arguments"):
                        function_args_str = getattr(tool_call, "arguments")
                    elif hasattr(tool_call, "tool_input"):
                        function_args_str = getattr(tool_call, "tool_input")
                    elif hasattr(tool_call, "params"):
                        function_args_str = getattr(tool_call, "params")
                    elif hasattr(tool_call, "args"):
                        function_args_str = getattr(tool_call, "args")
                    
                    if not function_name:
                        logger.error(f"无效的工具调用类型或格式: {type(tool_call)}")
                        self.update_memory("system", f"无效的工具调用格式: {tool_call}")
                        continue
                        
                    # 创建标准格式的工具调用，以便后续处理
                    logger.info(f"转换对象格式的工具调用: {function_name}")
                    tool_call = {
                        "id": tool_call_id or f"call_{function_name}_{datetime.now().timestamp()}",
                        "function": {
                            "name": function_name,
                            "arguments": function_args_str
                        }
                    }
                
                logger.info(f"处理工具调用: {function_name}，ID: {tool_call_id}")
                
                # 尝试解析参数
                try:
                    import json
                    if isinstance(function_args_str, dict):
                        # 如果已经是字典，直接使用
                        function_args = function_args_str
                    else:
                        function_args = json.loads(function_args_str)
                    logger.info(f"工具调用参数: {function_args}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"无法解析工具调用参数: {function_args_str}, 错误: {str(e)}")
                    # 回退到直接使用字符串或空字典
                    if isinstance(function_args_str, str):
                        function_args = {"text": function_args_str}
                    else:
                        function_args = {}
                
                # 查找对应的工具
                tool = None
                if hasattr(self, 'available_tools'):
                    if hasattr(self.available_tools, 'get_tool'):
                        tool = self.available_tools.get_tool(function_name)
                    elif hasattr(self.available_tools, 'tools'):
                        tool = next((t for t in self.available_tools.tools if getattr(t, 'name', '') == function_name), None)
                
                if not tool:
                    error_msg = f"找不到工具: {function_name}"
                    logger.error(error_msg)
                    self.update_memory("tool", error_msg, tool_call_id=tool_call_id)
                    continue
                
                # 执行工具
                logger.info(f"执行工具 {function_name} 开始")
                start_time = datetime.now()
                
                try:
                    # 检查工具是否有__call__或run方法
                    if callable(tool):
                        tool_result = await tool(**function_args) if asyncio.iscoroutinefunction(tool) else tool(**function_args)
                    elif hasattr(tool, 'run') and callable(tool.run):
                        tool_result = await tool.run(**function_args) if asyncio.iscoroutinefunction(tool.run) else tool.run(**function_args)
                    elif hasattr(tool, '__call__') and callable(tool.__call__):
                        tool_result = await tool(**function_args) if asyncio.iscoroutinefunction(tool.__call__) else tool(**function_args)
                    else:
                        raise ValueError(f"工具 {function_name} 没有可调用的方法")
                    
                    # 检查结果是否是协程对象，如果是则等待其完成
                    if asyncio.iscoroutine(tool_result):
                        logger.info(f"工具 {function_name} 返回了协程对象，等待其完成...")
                        tool_result = await tool_result
                    
                    # 确保结果是字符串
                    if not isinstance(tool_result, str):
                        tool_result = str(tool_result)
                    
                    # 记录成功结果
                    logger.info(f"工具 {function_name} 执行成功，结果长度: {len(tool_result)}, 结果: {tool_result}")
                    self.update_memory("tool", tool_result, tool_call_id=tool_call_id)
                except Exception as e:
                    # 记录错误
                    error_msg = f"工具 {function_name} 执行失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self.update_memory("tool", error_msg, tool_call_id=tool_call_id)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"工具 {function_name} 执行完成，耗时: {duration:.2f}秒")
                
            except Exception as e:
                logger.error(f"处理工具调用时出错: {str(e)}", exc_info=True)
                # 尝试添加错误消息到记忆
                try:
                    error_msg = f"处理工具调用时出错: {str(e)}"
                    if 'tool_call_id' in locals() and tool_call_id:
                        self.update_memory("tool", error_msg, tool_call_id=tool_call_id)
                    else:
                        self.update_memory("system", error_msg)
                except Exception:
                    pass
        
        logger.info(f"所有工具调用处理完成")

    async def _execute_subtasks(self) -> str:
        """执行所有子任务
        
        按照依赖关系顺序执行子任务，处理子任务间的依赖关系。
        
        Returns:
            str: 所有子任务执行的汇总结果
        """
        if not hasattr(self, 'subtasks') or not self.subtasks:
            return "没有可执行的子任务"
            
        logger.info(f"开始执行子任务序列，共 {len(self.subtasks)} 个子任务")
        
        # 跟踪已完成的子任务
        if not hasattr(self, 'completed_subtasks'):
            self.completed_subtasks = set()
        else:
            self.completed_subtasks = set(self.completed_subtasks)
            
        results = []
        
        # 创建子任务状态映射
        subtask_status = {}
        for subtask in self.subtasks:
            subtask_id = subtask.get('id')
            if not subtask_id:
                continue
            if subtask_id in self.completed_subtasks:
                subtask_status[subtask_id] = 'completed'
                subtask['status'] = 'completed'
            else:
                subtask_status[subtask_id] = 'pending'
                subtask['status'] = 'pending'
        
        # 继续执行直到所有子任务完成或无法继续
        max_iterations = 2 * len(self.subtasks)  # 防止无限循环
        iterations = 0
        
        while len(self.completed_subtasks) < len(self.subtasks) and iterations < max_iterations:
            iterations += 1
            progress_made = False
            
            # 找出所有可执行的子任务（依赖已满足）
            executable_subtasks = []
            for subtask in self.subtasks:
                subtask_id = subtask.get('id')
                
                # 跳过已完成的子任务
                if subtask_id in self.completed_subtasks:
                    continue
                
                # 检查依赖是否满足
                dependencies = subtask.get('dependencies', [])
                dependencies_met = all(dep in self.completed_subtasks for dep in dependencies)
                
                if dependencies_met:
                    executable_subtasks.append(subtask)
            
            # 如果没有可执行的子任务，但仍有未完成的子任务，可能存在循环依赖
            if not executable_subtasks and len(self.completed_subtasks) < len(self.subtasks):
                logger.warning("检测到可能的循环依赖，无法继续执行子任务")
                break
            
            # 执行可执行的子任务
            for subtask in executable_subtasks:
                subtask_id = subtask.get('id')
                logger.info(f"开始执行子任务: {subtask.get('name')} (ID: {subtask_id})")
                
                subtask['status'] = 'in_progress'
                subtask_status[subtask_id] = 'in_progress'
                subtask['start_time'] = datetime.now()
                
                # 记录当前正在执行的子任务ID，用于保持一致性
                self._current_subtask_id = subtask_id
                
                try:
                    # 执行子任务的所有步骤
                    subtask_result = await self._execute_steps(subtask)
                    subtask['result'] = subtask_result
                    subtask['status'] = 'completed'
                    subtask_status[subtask_id] = 'completed'
                    self.completed_subtasks.add(subtask_id)
                    progress_made = True
                    results.append(subtask_result)
                    
                    logger.info(f"子任务 {subtask_id} 执行完成")
                except Exception as e:
                    subtask['status'] = 'failed'
                    subtask_status[subtask_id] = 'failed'
                    logger.error(f"子任务 {subtask_id} 执行失败: {str(e)}")
                    results.append(f"子任务 {subtask_id} 执行失败: {str(e)}")
                
                subtask['end_time'] = datetime.now()
            
            # 如果本轮没有进展，说明存在循环依赖或所有剩余任务都无法执行
            if not progress_made:
                logger.warning("无法继续执行子任务，可能存在循环依赖或所有剩余任务都无法执行")
                break
        
        # 汇总结果
        final_result = "\n\n".join(results)
        logger.info(f"所有子任务执行完成，共 {len(self.completed_subtasks)}/{len(self.subtasks)} 个子任务成功执行")
        
        return final_result 