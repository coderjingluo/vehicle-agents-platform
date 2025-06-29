"""
KunlunSec AI Platform - 工具调用智能体模块

实现能够调用各种工具的智能体。
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field

from app.agent.react import ReActAgent
from app.agent.base import LLM, Memory, AgentState
from app.core.logging import logger

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

class Tool(BaseModel):
    """工具基类"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    async def run(self, **kwargs) -> Any:
        """执行工具"""
        raise NotImplementedError("Tool.run must be implemented by subclasses")

class ToolCollection:
    """工具集合"""
    
    def __init__(self, *tools: Tool):
        self.tools = list(tools)
        self.tool_map = {tool.name: tool for tool in tools}
    
    def add_tool(self, tool: Tool):
        """添加工具"""
        self.tools.append(tool)
        self.tool_map[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        return self.tool_map.get(name)
    
    def to_dict(self) -> Dict[str, Tool]:
        """转换为字典形式"""
        return self.tool_map
    
    def to_params(self) -> List[Dict[str, Any]]:
        """转换为参数形式"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    async def execute(self, name: str, tool_input: Dict[str, Any]) -> Any:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"未找到工具: {name}")
        return await tool.run(**tool_input)

# 创建基本工具
class CreateChatCompletion(Tool):
    """创建聊天回复工具"""
    name: str = "create_chat_completion"
    description: str = "创建聊天回复"
    
    async def run(self, prompt: str, **kwargs) -> str:
        """执行工具"""
        # 实际实现将连接到LLM服务
        return f"这是对'{prompt}'的回复"

class Terminate(Tool):
    """终止执行工具"""
    name: str = "terminate"
    description: str = "终止当前执行"
    
    async def run(self, **kwargs) -> str:
        """执行工具"""
        return "执行已终止"

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
    
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        CreateChatCompletion(), Terminate()
    ))
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=lambda: ["terminate"])
    
    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None
    
    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None
    
    async def think(self) -> bool:
        """处理当前状态并决定使用工具"""
        if self.next_step_prompt:
            self.update_memory("user", self.next_step_prompt)
        
        try:
            # 准备提示
            formatted_system_prompt = self.system_prompt.format(
                tools_description="\n".join(
                    f"- {tool.name}: {tool.description}" for tool in self.available_tools.tools
                )
            )
            
            # 调用LLM，获取带有工具选择的回应
            response = await self.llm.generate(
                formatted_system_prompt, 
                messages=self.memory.get_messages(),
                tools=self.available_tools.to_params(),
                tool_choice=self.tool_choices
            )
            
            # 解析响应中的工具调用
            self.tool_calls = self._parse_tool_calls(response)
            content = response.get("content", "") if isinstance(response, dict) else response
            
            # 记录响应信息
            logger.info(f"✨ {self.name}的思考: {content}")
            logger.info(f"🛠️ {self.name}选择了 {len(self.tool_calls) if self.tool_calls else 0} 个工具使用")
            
            if self.tool_calls:
                logger.info(f"🧰 准备使用的工具: {[call.function.get('name') for call in self.tool_calls]}")
                logger.info(f"🔧 工具参数: {self.tool_calls[0].function.get('arguments')}")
            
            # 处理不同的工具选择模式
            if self.tool_choices == ToolChoice.NONE:
                if self.tool_calls:
                    logger.warning(f"🤔 嗯，{self.name}尝试使用工具，但工具不可用！")
                if content:
                    self.update_memory("assistant", content)
                    return True
                return False
            
            # 创建并添加助手消息
            if self.tool_calls:
                self.update_memory("assistant", content, tool_calls=self.tool_calls)
            else:
                self.update_memory("assistant", content)
            
            if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
                return True  # 将在act()中处理
            
            # 对于'auto'模式，如果没有工具调用但有内容，则继续
            if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
                return bool(content)
            
            return bool(self.tool_calls)
        except Exception as e:
            logger.error(f"🚨 哎呀！{self.name}的思考过程遇到了问题: {e}")
            self.update_memory("assistant", f"处理时遇到错误: {str(e)}")
            return False
    
    async def act(self) -> str:
        """执行工具调用并处理结果"""
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                error_msg = "需要工具调用但未提供"
                self.update_memory("system", error_msg)
                return error_msg
            
            # 如果没有工具调用，返回最后一条消息内容
            messages = self.memory.get_messages()
            return messages[-1].get("content", "") if messages else "没有内容或命令要执行"
        
        results = []
        for command in self.tool_calls:
            # 每个工具调用重置base64_image
            self._current_base64_image = None
            
            result = await self.execute_tool(command)
            
            if self.max_observe:
                if isinstance(self.max_observe, int):
                    result = result[:self.max_observe]
            
            logger.info(f"🎯 工具 '{command.function.get('name')}' 完成了任务！结果: {result}")
            
            # 添加工具响应到记忆
            self.update_memory(
                "tool", 
                result,
                tool_name=command.function.get("name"),
                tool_call_id=command.id,
                base64_image=self._current_base64_image
            )
            results.append(result)
        
        return "\n\n".join(results)
    
    async def execute_tool(self, command: ToolCall) -> str:
        """执行单个工具调用并进行错误处理"""
        if not command or not command.function or "name" not in command.function:
            return "错误: 无效的命令格式"
        
        name = command.function.get("name")
        if name not in self.available_tools.tool_map:
            return f"错误: 未知工具 '{name}'"
        
        try:
            # 解析参数
            arguments = command.function.get("arguments", "{}")
            if isinstance(arguments, str):
                try:
                    args = json.loads(arguments)
                except json.JSONDecodeError:
                    args = {"input": arguments}
            else:
                args = arguments
            
            # 执行工具
            logger.info(f"🔧 激活工具: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)
            
            # 处理特殊工具
            await self._handle_special_tool(name=name, result=result)
            
            # 检查结果是否有base64_image
            if hasattr(result, "base64_image") and result.base64_image:
                self._current_base64_image = result.base64_image
            
            # 格式化结果显示
            observation = (
                f"执行命令 `{name}` 的观察结果:\n{str(result)}"
                if result
                else f"命令 `{name}` 完成，没有输出"
            )
            
            return observation
        except json.JSONDecodeError:
            error_msg = f"解析 {name} 的参数时出错: 无效的JSON格式"
            logger.error(f"📝 哎呀！'{name}'的参数无法理解 - 无效的JSON，参数:{command.function.get('arguments')}")
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"⚠️ 工具 '{name}' 遇到问题: {str(e)}"
            logger.exception(error_msg)
            return f"错误: {error_msg}"
    
    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """处理特殊工具执行和状态变更"""
        if not self._is_special_tool(name):
            return
        
        if self._should_finish_execution(name=name, result=result, **kwargs):
            # 将智能体状态设置为完成
            logger.info(f"🏁 特殊工具 '{name}' 已完成任务！")
            self.state = AgentState.FINISHED
    
    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """确定工具执行是否应该结束智能体"""
        return True
    
    def _is_special_tool(self, name: str) -> bool:
        """检查工具名称是否在特殊工具列表中"""
        return name.lower() in [n.lower() for n in self.special_tool_names]
    
    def _parse_tool_calls(self, response: Any) -> List[ToolCall]:
        """从LLM响应中解析工具调用"""
        # 检查是否是新的LLM实现返回的字典格式
        if isinstance(response, dict) and "tool_calls" in response:
            return [ToolCall(**tc) for tc in response["tool_calls"]]
        
        # 检查OpenAI格式的直接工具调用
        if hasattr(response, "tool_calls") and response.tool_calls:
            return [
                ToolCall(
                    id=tc.id, 
                    function={
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                ) 
                for tc in response.tool_calls
            ]
        
        # 简单的正则表达式匹配工具调用(用于文本回复中包含工具调用的情况)
        import re
        import json
        tool_calls = []
        
        if isinstance(response, str):
            # 匹配格式: tool(toolname({"arg": "value"}))
            pattern = r'tool\((\w+)\((.*?)\)\)'
            matches = re.findall(pattern, response)
            
            for i, (name, args_str) in enumerate(matches):
                try:
                    args = json.loads(args_str) if args_str else {}
                except:
                    args = {"input": args_str}
                
                tool_calls.append(ToolCall(
                    id=f"call_{i}",
                    function={"name": name, "arguments": args}
                ))
        
        return tool_calls
    
    async def cleanup(self):
        """清理智能体使用的资源"""
        logger.info(f"🧹 清理智能体 '{self.name}' 的资源...")
        for tool_name, tool_instance in self.available_tools.tool_map.items():
            if hasattr(tool_instance, "cleanup") and asyncio.iscoroutinefunction(
                tool_instance.cleanup
            ):
                try:
                    logger.debug(f"🧼 清理工具: {tool_name}")
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(
                        f"🚨 清理工具 '{tool_name}' 时出错: {e}", exc_info=True
                    )
        logger.info(f"✨ 智能体 '{self.name}' 的清理完成。")
    
    async def run(self, request: Optional[str] = None) -> str:
        """运行智能体并在完成时进行清理"""
        try:
            return await super().run(request)
        finally:
            await self.cleanup() 