"""
KunlunSec AI Platform - 基础智能体模块

定义智能体基类和核心功能。
"""

import enum
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Tuple
from contextlib import asynccontextmanager
from datetime import datetime
import json
from pydantic import BaseModel, Field, model_validator

from app.core.logging import logger
from app.sandbox.client import SANDBOX_CLIENT

class AgentState(str, enum.Enum):
    """智能体状态枚举"""
    IDLE = "idle"           # 空闲状态
    THINKING = "thinking"   # 思考中
    ACTING = "acting"       # 行动中
    FINISHED = "finished"   # 已完成
    ERROR = "error"         # 错误状态

class Message(BaseModel):
    """消息模型"""
    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    base64_image: Optional[str] = None
    
    @classmethod
    def user_message(cls, content: Optional[str] = None, **kwargs):
        """创建用户消息"""
        return cls(role="user", content=content or "", **kwargs)
    
    @classmethod
    def system_message(cls, content: Optional[str] = None, **kwargs):
        """创建系统消息"""
        return cls(role="system", content=content or "", **kwargs)
    
    @classmethod
    def assistant_message(cls, content: Optional[str] = None, **kwargs):
        """创建助手消息"""
        return cls(role="assistant", content=content or "", **kwargs)
    
    @classmethod
    def tool_message(cls, content: Optional[str] = None, **kwargs):
        """创建工具消息"""
        return cls(role="tool", content=content or "", **kwargs)

class Memory:
    """智能体记忆存储"""
    
    def __init__(self):
        """初始化记忆存储"""
        self.messages = []  # 消息列表
        
    def add_message(self, message):
        """添加消息
        
        Args:
            message: 可以是Message对象或者包含role和content的字典
        """
        if isinstance(message, dict):
            self.messages.append(message)
        else:
            # 假设是Message对象
            self.messages.append({
                "role": message.role,
                "content": message.content,
                **({"tool_call_id": message.tool_call_id} if message.tool_call_id else {}),
                **({"name": message.name} if message.name else {}),
                **({"base64_image": message.base64_image} if message.base64_image else {})
            })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取所有消息"""
        return self.messages
    
    def clear(self) -> None:
        """清除所有消息"""
        self.messages = []
    
    def get_last_message(self) -> Optional[Dict[str, str]]:
        """获取最后一条消息"""
        if not self.messages:
            return None
        return self.messages[-1]

class LLM:
    """语言模型接口"""
    
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, 
                max_tokens: int = 20480, temperature: float = 0.7, 
                api_type: str = "openai", api_version: str = None):
        """初始化LLM
        
        Args:
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
            max_tokens: 最大token数
            temperature: 生成温度
            api_type: API类型(openai, azure, aws等)
            api_version: API版本
        """
        from app.core.config import settings
        
        self.model = model or settings.LLM_MODEL
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_type = api_type or settings.LLM_API_TYPE
        self.api_version = api_version or settings.LLM_API_VERSION
        
        # 设置token计数相关属性
        self.total_input_tokens = 0
        self.total_completion_tokens = 0
        
        # 初始化客户端
        self._init_client()
        
    def _init_client(self):
        """初始化API客户端"""
        try:
            from openai import AsyncOpenAI, AsyncAzureOpenAI
            import tiktoken
            
            # 初始化tokenizer
            try:
                self.tokenizer = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # 如果模型不在tiktoken的预设中，使用cl100k_base作为默认值
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
            # 根据API类型初始化客户端
            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            elif self.api_type == "aws":
                # 暂不支持AWS Bedrock，可根据需要添加
                raise NotImplementedError("AWS Bedrock客户端尚未实现")
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
                
        except ImportError as e:
            from app.core.logging import logger
            logger.error(f"初始化LLM客户端失败: {str(e)}，请安装必要的依赖")
            raise
    
    async def generate(self, prompt: str, messages: List[Dict[str, str]] = None, 
                       system_msgs: List[Dict[str, str]] = None, 
                       tools: List[Dict] = None, tool_choice: Any = None,
                       stream: bool = False, temperature: Optional[float] = None, **kwargs) -> Any:
        """生成文本
        
        Args:
            prompt: 系统提示词
            messages: 对话消息列表
            system_msgs: 系统消息列表
            tools: 工具列表
            tool_choice: 工具选择策略
            stream: 是否流式响应
            temperature: 生成温度
            **kwargs: 其他参数
            
        Returns:
            生成的文本或工具调用响应
        """
        if not messages:
            messages = []
        
        # 添加系统提示词作为系统消息
        if prompt and not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {"role": "system", "content": prompt})
        
        # 如果提供了工具，使用ask_tool方法
        if tools:
            return await self.ask_tool(
                messages=messages, 
                system_msgs=system_msgs,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                **kwargs
            )
        
        # 否则使用标准ask方法
        return await self.ask(
            messages=messages,
            system_msgs=system_msgs,
            stream=stream,
            temperature=temperature,
            **kwargs
        )
    
    def count_tokens(self, text: str) -> int:
        """计算文本中的token数量"""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    async def ask(self, messages: List[Dict[str, str]], 
                 system_msgs: Optional[List[Dict[str, str]]] = None,
                 stream: bool = False, 
                 temperature: Optional[float] = None) -> str:
        """向LLM发送请求
        
        Args:
            messages: 对话消息列表
            system_msgs: 系统消息列表
            stream: 是否流式响应
            temperature: 生成温度
            
        Returns:
            生成的文本
        """
        from app.core.logging import logger
        
        try:
            # 准备消息
            all_messages = []
            if system_msgs:
                all_messages.extend(system_msgs)
            all_messages.extend(messages)
            
            # 创建请求参数
            params = {
                "model": self.model,
                "messages": all_messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "stream": stream
            }
            logger.info(f"[ask]请求参数: {params}")
            # 非流式请求
            if not stream:
                response = await self.client.chat.completions.create(**params)
                
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("LLM响应为空或无效")
                
                # 更新token计数
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_completion_tokens += response.usage.completion_tokens
                
                logger.info(f"[ask]Token使用情况: 输入={response.usage.prompt_tokens}, " 
                           f"输出={response.usage.completion_tokens}, "
                           f"总计={response.usage.prompt_tokens + response.usage.completion_tokens}")
                
                return response.choices[0].message.content
            
            # 流式请求
            response = await self.client.chat.completions.create(**params)
            
            collected_messages = []
            async for chunk in response:
                chunk_message = chunk.choices[0].delta.content or ""
                collected_messages.append(chunk_message)
                # print(chunk_message, end="", flush=True)
            
            # 合并所有收集到的消息片段
            full_response = "".join(collected_messages).strip()
            if not full_response:
                raise ValueError("流式LLM响应为空")
            
            return full_response
            
        except Exception as e:
            logger.error(f"LLM请求失败: {str(e)}")
            raise e
    
    async def ask_tool(self, messages: List[Dict[str, str]],
                      system_msgs: Optional[List[Dict[str, str]]] = None,
                      tools: Optional[List[Dict]] = None,
                      tool_choice: Any = None,
                      temperature: Optional[float] = None,
                      timeout: int = 300,
                      **kwargs) -> Dict[str, Any]:
        """使用工具进行问答
        
        Args:
            messages: 对话消息列表
            system_msgs: 系统消息列表
            tools: 工具列表
            tool_choice: 工具选择策略
            temperature: 生成温度
            timeout: 超时时间(秒)
            **kwargs: 其他参数
            
        Returns:
            带有工具调用的响应
        """
        from app.core.logging import logger
        
        try:
            # 准备消息
            all_messages = []
            if system_msgs:
                all_messages.extend(system_msgs)
            all_messages.extend(messages)
            
            # 创建请求参数
            params = {
                "model": self.model,
                "messages": all_messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "tools": tools,
                "tool_choice": tool_choice,
                "timeout": timeout,
                "stream": False,  # 工具调用始终使用非流式
                **kwargs
            }
            # logger.info(f"[ask_tool]请求参数: {params}")
            # 发送请求
            response = await self.client.chat.completions.create(**params)
            
            # 检查响应是否有效
            if not response.choices or not response.choices[0].message:
                logger.warning("LLM工具响应为空或无效")
                return {}
            
            # 更新token计数
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_completion_tokens += response.usage.completion_tokens
            
            logger.info(f"[ask_tool]Token使用情况: 输入={response.usage.prompt_tokens}, " 
                       f"输出={response.usage.completion_tokens}, "
                       f"总计={response.usage.prompt_tokens + response.usage.completion_tokens}")
            
            logger.info(f"[ask_tool]响应: {response.choices[0].message}")
            
            # 将响应转换为字典
            message = response.choices[0].message
            result = {
                "content": message.content,
                "role": "assistant"
            }
            
            # 添加工具调用(如果有)
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"LLM工具请求失败: {str(e)}")
            raise e

# 定义角色类型
ROLE_TYPE = str

class BaseAgent(BaseModel, ABC):
    """智能体基类"""
    
    # 核心属性
    name: str                               # 智能体名称
    description: Optional[str] = None       # 智能体描述
    
    # 提示语
    system_prompt: Optional[str] = None     # 系统级指令提示
    next_step_prompt: Optional[str] = None  # 下一步行动提示
    
    # 依赖组件
    llm: LLM                                # 语言模型实例
    memory: Memory = Field(default_factory=Memory)  # 智能体记忆存储
    state: AgentState = AgentState.IDLE     # 当前状态
    
    # 执行控制
    max_steps: int = 10                     # 最大执行步骤数
    current_step: int = 0                   # 当前执行步骤
    duplicate_threshold: int = 2            # 重复内容检测阈值
    
    # 动态规划相关
    dynamic_planning: bool = True           # 是否启用动态规划能力
    current_plan: Optional[Dict[str, Any]] = None  # 当前执行计划
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)  # 子任务列表
    steps: List[Dict[str, Any]] = Field(default_factory=list)     # 步骤列表
    completed_subtasks: List[str] = Field(default_factory=list)   # 已完成子任务ID
    completed_steps: List[str] = Field(default_factory=list)      # 已完成步骤ID
    
    # 新增属性
    plan_start_time: Optional[datetime] = None  # 计划开始时间
    error: Optional[str] = None                # 错误信息
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # 允许子类中的额外字段
    
    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """初始化智能体"""
        if self.llm is None:
            raise ValueError("必须提供LLM实例")
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self
    
    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """安全的状态转换上下文管理器"""
        if not isinstance(new_state, AgentState):
            raise ValueError(f"无效的状态: {new_state}")
            
        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # 发生错误时转换到ERROR状态
            raise e
        finally:
            self.state = previous_state  # 恢复到之前的状态
    
    def update_memory(
        self,
        role: ROLE_TYPE,
        content: Optional[str] = None,
        base64_image: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """添加消息到智能体记忆
        
        Args:
            role: 消息角色
            content: 消息内容，可以为None
            base64_image: 可选的base64编码图片
            tool_calls: 可选的工具调用列表
            **kwargs: 其他参数
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }
        
        if role not in message_map:
            raise ValueError(f"不支持的消息角色: {role}")
            
        # 如果是助手消息且有工具调用，添加工具调用信息
        if role == "assistant" and tool_calls:
            # 确保content不为None
            safe_content = content if content is not None else ""
            message_dict = {
                "role": "assistant",
                "content": safe_content,
                "tool_calls": tool_calls
            }
            self.memory.add_message(message_dict)
            logger.info(f"添加带工具调用的助手消息到记忆，包含 {len(tool_calls)} 个工具调用")
        else:
            # 确保content不为None
            safe_content = content if content is not None else ""
            # 创建基本消息
            kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
            message = message_map[role](safe_content, **kwargs)
            # 添加普通消息
            self.memory.add_message(message)
    
    async def run(self, task: str) -> str:
        """执行任务并返回结果
        
        这是智能体的主要执行方法，接收任务描述，执行任务，并返回结果。
        
        Args:
            task: 任务描述
        
        Returns:
            str: 任务执行结果
        """
        # 记录任务开始
        self.task = task
        self.task_start_time = datetime.now()
        logger.info(f"智能体 {self.name} 开始执行任务: {task[:50]}...")
        self.update_memory("system", f"任务开始: {task}")
        
        try:
            # 首先生成执行计划
            if not hasattr(self, 'current_plan') or not self.current_plan:
                logger.info(f"智能体 {self.name} 正在为任务生成执行计划...")
                self.current_plan = await self.generate_plan(task)
                if self.current_plan:
                    logger.info(f"已生成执行计划: {json.dumps(self.current_plan.get('main_task', ''))[:50]}...")
                    logger.info(f"执行计划包含 {len(self.current_plan.get('subtasks', []))} 个子任务")
                    # 将子任务信息添加到内存
                    self.update_memory("system", f"已生成执行计划，包含 {len(self.current_plan.get('subtasks', []))} 个子任务")
                else:
                    logger.warning(f"智能体 {self.name} 未能生成执行计划")
            
            # 执行任务
            result = await self._execute_task(task)
            
            # 记录任务完成
            self.task_end_time = datetime.now()
            duration = (self.task_end_time - self.task_start_time).total_seconds()
            logger.info(f"智能体 {self.name} 完成任务，耗时: {duration:.2f}秒")
            self.update_memory("system", f"任务完成，耗时: {duration:.2f}秒")
            
            return result
        except Exception as e:
            self.task_end_time = datetime.now()
            duration = (self.task_end_time - self.task_start_time).total_seconds()
            logger.error(f"智能体 {self.name} 执行任务时出错: {str(e)}")
            self.update_memory("system", f"任务执行出错: {str(e)}")
            raise
    
    async def _execute_task(self, task: str) -> str:
        """执行具体任务
        
        Args:
            task: 任务描述
            
        Returns:
            str: 任务执行结果
        """
        # 如果有执行计划，使用动态规划执行
        if hasattr(self, 'current_plan') and self.current_plan:
            logger.info(f"智能体 {self.name} 开始执行动态规划任务...")
            
            # 提取子任务和步骤
            subtasks = self.current_plan.get("subtasks", [])
            self.subtasks = subtasks
            
            # 初始化子任务和步骤状态
            self._initialize_task_status()
            
            # 记录子任务详情
            for i, subtask in enumerate(subtasks):
                subtask_id = subtask.get('id', f'subtask-{i+1}')
                subtask_name = subtask.get('name', '未命名子任务')
                steps_count = len(subtask.get('steps', []))
                dependencies = subtask.get('dependencies', [])
                logger.info(f"子任务 {i+1}: ID={subtask_id}, 名称={subtask_name}, 包含 {steps_count} 个步骤, 依赖={dependencies}")
            
            # 执行子任务
            result = await self._execute_subtasks()
            return result
        else:
            # 如果没有执行计划，使用传统方式执行
            logger.info(f"智能体 {self.name} 使用传统方式执行任务...")
            return await self._execute_traditional(task)
    
    def _initialize_task_status(self):
        """初始化子任务和步骤状态"""
        if not hasattr(self, 'subtasks') or not self.subtasks:
            return
            
        logger.info(f"初始化 {len(self.subtasks)} 个子任务的状态")
        
        # 为每个子任务添加状态字段
        for subtask in self.subtasks:
            subtask['status'] = 'pending'  # pending, in_progress, completed, failed
            subtask['start_time'] = None
            subtask['end_time'] = None
            subtask['result'] = None
            
            # 为每个步骤添加状态字段
            for step in subtask.get('steps', []):
                step['status'] = 'pending'  # pending, in_progress, completed, failed
                step['start_time'] = None
                step['end_time'] = None
                step['result'] = None
                step['tool_calls'] = []
    
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
        completed_subtasks = set()
        results = []
        
        # 继续执行直到所有子任务完成或无法继续
        while len(completed_subtasks) < len(self.subtasks):
            progress_made = False
            
            for i, subtask in enumerate(self.subtasks):
                subtask_id = subtask.get('id')
                
                # 跳过已完成的子任务
                if subtask_id in completed_subtasks:
                    continue
                    
                # 检查依赖是否满足
                dependencies = subtask.get('dependencies', [])
                dependencies_met = all(dep in completed_subtasks for dep in dependencies)
                
                if not dependencies_met:
                    logger.debug(f"子任务 {subtask_id} 的依赖尚未满足，稍后执行")
                    continue
                
                # 执行子任务
                logger.info(f"开始执行子任务: {subtask.get('name')} (ID: {subtask_id})")
                subtask['status'] = 'in_progress'
                subtask['start_time'] = datetime.now()
                
                try:
                    # 执行子任务的所有步骤
                    subtask_result = await self._execute_steps(subtask)
                    subtask['result'] = subtask_result
                    subtask['status'] = 'completed'
                    completed_subtasks.add(subtask_id)
                    progress_made = True
                    results.append(subtask_result)
                    
                    logger.info(f"子任务 {subtask_id} 执行完成")
                except Exception as e:
                    subtask['status'] = 'failed'
                    logger.error(f"子任务 {subtask_id} 执行失败: {str(e)}")
                    results.append(f"子任务 {subtask_id} 执行失败: {str(e)}")
                
                subtask['end_time'] = datetime.now()
            
            # 如果本轮没有进展，说明存在循环依赖或所有剩余任务都无法执行
            if not progress_made:
                logger.warning("无法继续执行子任务，可能存在循环依赖或所有剩余任务都无法执行")
                break
        
        # 汇总结果
        final_result = "\n\n".join(results)
        logger.info(f"所有子任务执行完成，共 {len(completed_subtasks)}/{len(self.subtasks)} 个子任务成功执行")
        
        return final_result
    
    async def _execute_steps(self, subtask: Dict[str, Any]) -> str:
        """执行子任务的所有步骤
        
        Args:
            subtask: 子任务定义
            
        Returns:
            str: 子任务执行结果
        """
        steps = subtask.get('steps', [])
        step_results = []
        
        logger.info(f"开始执行子任务 {subtask.get('id')} 的 {len(steps)} 个步骤")
        
        for i, step in enumerate(steps):
            step_id = step.get('id')
            step_desc = step.get('description')
            
            logger.info(f"执行步骤 {i+1}/{len(steps)}: {step_desc} (ID: {step_id})")
            step['status'] = 'in_progress'
            step['start_time'] = datetime.now()
            
            try:
                # 执行步骤，这里需要调用think方法来决定如何执行该步骤
                self._update_current_step(subtask.get('id'), step_id)
                step_result = await self._execute_step(step)
                step['result'] = step_result
                step['status'] = 'completed'
                step_results.append(step_result)
                
                logger.info(f"步骤 {step_id} 执行完成")
            except Exception as e:
                step['status'] = 'failed'
                error_msg = f"步骤 {step_id} 执行失败: {str(e)}"
                logger.error(error_msg)
                step_results.append(error_msg)
            
            step['end_time'] = datetime.now()
        
        # 汇总子任务结果
        subtask_result = "\n".join(step_results)
        return subtask_result
    
    async def _execute_step(self, step: Dict[str, Any]) -> str:
        """执行单个步骤
        
        Args:
            step: 步骤定义
            
        Returns:
            str: 步骤执行结果
        """
        # 这里调用think方法来决定如何执行该步骤
        logger.info(f"思考如何执行步骤: {step.get('description')}")
        
        # 更新内存，添加当前步骤信息
        self.update_memory("system", f"当前执行步骤: {step.get('description')}")
        
        # 检查步骤是否需要工具调用
        needs_tools = len(step.get('tools', [])) > 0
        if needs_tools:
            logger.info(f"步骤需要使用工具: {', '.join(step.get('tools', []))}")
            # 确保在子类的think方法中正确处理工具调用
        
        # 执行思考-行动循环
        continue_execution = True
        result = ""
        
        while continue_execution:
            continue_execution = await self.think()
            if continue_execution:
                action_result = await self.act()
                if action_result:
                    result = action_result
        
        return result
    
    def _update_current_step(self, subtask_id: str, step_id: str):
        """更新当前正在执行的步骤
        
        Args:
            subtask_id: 子任务ID
            step_id: 步骤ID
        """
        if not hasattr(self, 'current_execution'):
            self.current_execution = {}
            
        self.current_execution['current_subtask_id'] = subtask_id
        self.current_execution['current_step_id'] = step_id
        logger.debug(f"当前执行位置更新为: 子任务={subtask_id}, 步骤={step_id}")
    
    def _identify_current_task_and_step(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """识别当前正在执行的子任务和步骤
        
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]: 当前子任务和步骤
        """
        if not hasattr(self, 'current_execution') or not hasattr(self, 'subtasks'):
            return None, None
            
        current_subtask_id = self.current_execution.get('current_subtask_id')
        current_step_id = self.current_execution.get('current_step_id')
        
        if not current_subtask_id or not current_step_id:
            return None, None
            
        # 查找当前子任务
        current_subtask = None
        for subtask in self.subtasks:
            if subtask.get('id') == current_subtask_id:
                current_subtask = subtask
                break
                
        if not current_subtask:
            return None, None
            
        # 查找当前步骤
        current_step = None
        for step in current_subtask.get('steps', []):
            if step.get('id') == current_step_id:
                current_step = step
                break
                
        return current_subtask, current_step
    
    def _update_step_status(self, subtask_id: str, step_id: str, status: str, result: Optional[str] = None):
        """更新步骤状态
        
        Args:
            subtask_id: 子任务ID
            step_id: 步骤ID
            status: 新状态
            result: 步骤结果
        """
        if not hasattr(self, 'subtasks'):
            return
            
        for subtask in self.subtasks:
            if subtask.get('id') == subtask_id:
                for step in subtask.get('steps', []):
                    if step.get('id') == step_id:
                        step['status'] = status
                        if result is not None:
                            step['result'] = result
                        logger.debug(f"步骤 {step_id} 状态更新为 {status}")
                        return
    
    async def _execute_traditional(self, task: str) -> str:
        """使用传统方式执行任务
        
        Args:
            task: 任务描述
            
        Returns:
            str: 任务执行结果
        """
        logger.info("使用传统思考-行动循环执行任务")
        
        continue_execution = True
        result = ""
        
        while continue_execution:
            continue_execution = await self.think()
            if continue_execution:
                action_result = await self.act()
                if action_result:
                    result = action_result
        
        return result
    
    @abstractmethod
    async def step(self) -> str:
        """执行单个步骤(子类必须实现)"""
        pass
    
    def is_stuck(self) -> bool:
        """检测是否陷入循环"""
        if len(self.memory.messages) < 2:
            return False
            
        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False
            
        # 计算相同内容出现的次数
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )
        
        return duplicate_count >= self.duplicate_threshold
    
    def handle_stuck_state(self):
        """处理循环状态"""
        stuck_prompt = "\
        检测到重复响应。考虑新的策略，避免重复已尝试过的无效路径。"
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"智能体检测到循环状态。添加提示: {stuck_prompt}")
    
    @property
    def messages(self) -> List[Message]:
        """获取智能体记忆中的消息列表"""
        return self.memory.messages
    
    @messages.setter
    def messages(self, value: List[Message]):
        """设置智能体记忆中的消息列表"""
        self.memory.messages = value 

    def get_tool_usages(self) -> List[Dict[str, Any]]:
        """获取智能体使用的工具记录
        
        Returns:
            List[Dict[str, Any]]: 工具使用记录列表
        """
        tool_usages = []
        
        # 从记忆中提取工具使用记录
        if hasattr(self, "memory") and hasattr(self.memory, "messages"):
            for msg in self.memory.messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_usages.append({
                            "tool": tool_call.function.name,
                            "args": tool_call.function.arguments,
                            "result": getattr(tool_call, "result", None),
                            "timestamp": getattr(msg, "timestamp", None)
                        })
        
        return tool_usages 

    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """根据任务动态生成执行计划
        
        将复杂任务分解为多个子任务，并可能进一步分解为更小的步骤
        
        Args:
            task: 任务描述
            
        Returns:
            Dict[str, Any]: 生成的执行计划
        """
        # 构建提示，引导模型生成规划
        planning_prompt = f"""
        请为以下任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 要求
        1. 将该任务分解为逻辑子任务
        2. 每个子任务可能需要进一步分解为具体步骤
        3. 确定步骤之间的依赖关系
        
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
                            "tools": ["可能需要使用的工具"],
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
        
        请确保规划逻辑合理，步骤清晰，并针对具体任务特点进行规划。
        """
        
        # 使用LLM生成规划
        from app.core.logging import logger
        logger.info(f"正在为任务生成执行计划: {task[:50]}...")
        
        try:
            # 向LLM发送规划请求
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": "你是一个精通任务分解和规划的专家智能体。"},
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
                    f"已生成任务执行计划，包含 {len(self.subtasks)} 个子任务。"
                )
                
                return plan
            except json.JSONDecodeError as e:
                logger.error(f"解析执行计划失败: {str(e)}")
                # 生成简单计划作为备选
                self.current_plan = {
                    "main_task": task,
                    "subtasks": [{"id": "default-task", "name": "执行任务", "description": task, "steps": [], "dependencies": []}]
                }
                self.subtasks = self.current_plan.get('subtasks', [])
                return self.current_plan
                
        except Exception as e:
            logger.error(f"生成执行计划时出错: {str(e)}")
            # 生成简单计划作为备选
            self.current_plan = {
                "main_task": task,
                "subtasks": [{"id": "default-task", "name": "执行任务", "description": task, "steps": [], "dependencies": []}]
            }
            self.subtasks = self.current_plan.get('subtasks', [])
            return self.current_plan
            
    def _update_plan_progress(self):
        """更新计划执行进度
        
        根据当前执行状态更新子任务和步骤的完成情况
        """
        # 此处实现进度更新逻辑
        # 目前为简单示例，实际应用中需要根据执行情况更新
        
        if not self.current_plan or not self.subtasks:
            return
            
        # 示例: 如果某个子任务的所有步骤都已完成，则标记该子任务为已完成
        for subtask in self.subtasks:
            subtask_id = subtask.get('id')
            if subtask_id in self.completed_subtasks:
                continue
                
            # 获取子任务的所有步骤
            steps = subtask.get('steps', [])
            
            # 检查所有步骤是否已完成
            all_steps_completed = all(
                step.get('id') in self.completed_steps 
                for step in steps if 'id' in step
            )
            
            # 如果子任务没有具体步骤，或者所有步骤已完成，则标记子任务为已完成
            if not steps or all_steps_completed:
                if subtask_id not in self.completed_subtasks:
                    self.completed_subtasks.append(subtask_id)
                    # 更新记忆
                    self.update_memory(
                        "system",
                        f"已完成子任务: {subtask.get('name', subtask_id)}"
                    )
    
    def get_next_subtask(self) -> Optional[Dict[str, Any]]:
        """获取下一个待执行的子任务
        
        根据依赖关系和当前完成情况，确定下一个应该执行的子任务
        
        Returns:
            Optional[Dict[str, Any]]: 下一个子任务，如果没有则返回None
        """
        if not self.subtasks:
            return None
            
        for subtask in self.subtasks:
            subtask_id = subtask.get('id')
            
            # 跳过已完成的子任务
            if subtask_id in self.completed_subtasks:
                continue
                
            # 检查依赖关系
            dependencies = subtask.get('dependencies', [])
            if all(dep in self.completed_subtasks for dep in dependencies):
                # 所有依赖都已满足，可以执行此子任务
                return subtask
                
        return None
    
    def get_next_step(self, subtask_id: str) -> Optional[Dict[str, Any]]:
        """获取指定子任务中下一个待执行的步骤
        
        Args:
            subtask_id: 子任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 下一个步骤，如果没有则返回None
        """
        # 查找指定的子任务
        subtask = next((st for st in self.subtasks if st.get('id') == subtask_id), None)
        if not subtask:
            return None
            
        steps = subtask.get('steps', [])
        if not steps:
            return None
            
        # 返回第一个未完成的步骤
        for step in steps:
            step_id = step.get('id')
            if step_id not in self.completed_steps:
                return step
                
        return None

    async def get_final_answer(self) -> str:
        """获取最终答案
        
        Returns:
            str: 最终答案
        """
        # 如果有执行结果，从结果中构建最终答案
        if hasattr(self, 'subtasks') and self.subtasks:
            # 收集所有子任务的结果
            subtask_results = []
            for subtask in self.subtasks:
                if subtask.get('status') == 'completed' and 'result' in subtask:
                    subtask_name = subtask.get('name', 'Unnamed Subtask')
                    subtask_results.append(f"## {subtask_name}\n{subtask.get('result', '')}")
            
            if subtask_results:
                return "\n\n".join(subtask_results)
        
        # 如果没有执行结果，构建一个基本的回答
        return "任务执行完成，但未生成详细结果。请检查日志了解更多信息。"
    
    def get_final_result(self) -> Dict[str, Any]:
        """获取最终结果
        
        Returns:
            Dict[str, Any]: 最终结果
        """
        # 实现获取最终结果的逻辑
        # 这里需要根据具体的智能体实现来决定如何获取最终结果
        final_result = {
            "success": True,
            "message": "任务执行完成",
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果有收集到的资产、威胁、风险信息，添加到结果中
        if hasattr(self, 'assets'):
            final_result["assets"] = self.assets
        if hasattr(self, 'threats'):
            final_result["threats"] = self.threats
        if hasattr(self, 'risks'):
            final_result["risks"] = self.risks
        if hasattr(self, 'countermeasures'):
            final_result["countermeasures"] = self.countermeasures
        
        return final_result
    
    def get_final_status(self) -> str:
        """获取最终状态
        
        Returns:
            str: 最终状态
        """
        # 实现获取最终状态的逻辑
        # 这里需要根据具体的智能体实现来决定如何获取最终状态
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        return "智能体执行完成"

    def _check_for_completion(self) -> bool:
        """检查是否有完成消息"""
        # 实现检查是否有完成消息的逻辑
        # 这里需要根据具体的智能体实现来决定如何检查是否有完成消息
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        return False

    async def think(self) -> bool:
        """执行思考步骤"""
        # 实现执行思考步骤的逻辑
        # 这里需要根据具体的智能体实现来决定如何执行思考步骤
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        logger.info(f"base.py think...")
        return True

    def get_final_answer(self) -> str:
        """获取最终答案
        
        Returns:
            str: 最终答案
        """
        # 实现获取最终答案的逻辑
        # 这里需要根据具体的智能体实现来决定如何获取最终答案
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        return "智能体执行完成，但未提供最终答案。"
    
    def get_final_result(self) -> Dict[str, Any]:
        """获取最终结果
        
        Returns:
            Dict[str, Any]: 最终结果
        """
        # 实现获取最终结果的逻辑
        # 这里需要根据具体的智能体实现来决定如何获取最终结果
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        return {}
    
    def get_final_status(self) -> str:
        """获取最终状态
        
        Returns:
            str: 最终状态
        """
        # 实现获取最终状态的逻辑
        # 这里需要根据具体的智能体实现来决定如何获取最终状态
        # 这里只是一个示例，实际实现需要根据智能体的具体功能来决定
        return "智能体执行完成" 

    def _update_step_status(self, subtask: Dict[str, Any], step: Dict[str, Any], status: str):
        """更新步骤状态
        
        Args:
            subtask: 子任务
            step: 步骤
            status: 新状态
        """
        step_id = step.get('id', 'unknown')
        step_desc = step.get('description', '未描述步骤')
        
        # 更新步骤状态
        step['status'] = status
        logger.info(f"步骤状态更新: {step_desc} (ID: {step_id}) -> {status}")
        
        # 如果步骤已完成，添加到已完成步骤列表
        if status == "已完成" and step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
            logger.info(f"步骤已完成: {step_desc} (ID: {step_id})")

    def _advance_to_next_step_or_subtask(self, current_subtask: Dict[str, Any], current_step: Dict[str, Any]):
        """前进到下一个步骤或子任务
        
        Args:
            current_subtask: 当前子任务
            current_step: 当前步骤
        """
        if not current_subtask or not current_step:
            return
        
        subtask_id = current_subtask.get('id', 'unknown')
        subtask_name = current_subtask.get('name', '未命名子任务')
        step_id = current_step.get('id', 'unknown')
        
        # 获取当前子任务的所有步骤
        steps = current_subtask.get('steps', [])
        if not steps:
            # 如果没有步骤，标记子任务为已完成
            current_subtask['status'] = "已完成"
            if subtask_id not in self.completed_subtasks:
                self.completed_subtasks.append(subtask_id)
                logger.info(f"子任务已完成: {subtask_name} (ID: {subtask_id})")
            
            # 前进到下一个子任务
            self._advance_to_next_subtask()
            return
        
        # 查找当前步骤的索引
        try:
            current_index = next(i for i, s in enumerate(steps) if s.get('id') == step_id)
        except StopIteration:
            logger.warning(f"无法找到当前步骤: {step_id}")
            return
        
        # 如果有下一个步骤，将其标记为执行中
        if current_index < len(steps) - 1:
            next_step = steps[current_index + 1]
            next_step['status'] = "执行中"
            next_step_id = next_step.get('id', 'unknown')
            next_step_desc = next_step.get('description', '未描述步骤')
            logger.info(f"前进到下一个步骤: {next_step_desc} (ID: {next_step_id})")
        else:
            # 当前子任务的所有步骤已完成，标记子任务为已完成
            current_subtask['status'] = "已完成"
            if subtask_id not in self.completed_subtasks:
                self.completed_subtasks.append(subtask_id)
                logger.info(f"子任务已完成: {subtask_name} (ID: {subtask_id})")
            
            # 前进到下一个子任务
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
            subtask_id = current_subtask.get('id', 'unknown')
            subtask_name = current_subtask.get('name', '未命名子任务')
            
            # 如果有下一个子任务，将其标记为执行中
            if current_index < len(subtasks) - 1:
                next_subtask = subtasks[current_index + 1]
                next_subtask['status'] = "执行中"
                next_subtask_id = next_subtask.get('id', 'unknown')
                next_subtask_name = next_subtask.get('name', '未命名子任务')
                logger.info(f"前进到下一个子任务: {next_subtask_name} (ID: {next_subtask_id})")
                
                # 将下一个子任务的第一个步骤标记为执行中
                next_steps = next_subtask.get('steps', [])
                if next_steps:
                    next_steps[0]['status'] = "执行中"
                    next_step_id = next_steps[0].get('id', 'unknown')
                    next_step_desc = next_steps[0].get('description', '未描述步骤')
                    logger.info(f"开始执行步骤: {next_step_desc} (ID: {next_step_id})")
            else:
                logger.info(f"所有子任务已完成")

    def _identify_current_task_and_step(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """识别当前执行的子任务和步骤
        
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]: 当前子任务和步骤
        """
        if not hasattr(self, 'current_plan') or not self.current_plan:
            return None, None
        
        subtasks = self.current_plan.get('subtasks', [])
        if not subtasks:
            return None, None
        
        for subtask in subtasks:
            if subtask.get('status') == "执行中":
                steps = subtask.get('steps', [])
                for step in steps:
                    if step.get('status') == "执行中":
                        return subtask, step
        
        return None, None 