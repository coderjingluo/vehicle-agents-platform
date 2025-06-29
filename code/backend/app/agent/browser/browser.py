"""
KunlunSec AI Platform - 浏览器智能体模块

实现专门进行网页浏览和交互的智能体。
"""

from typing import Dict, List, Optional, Any
from pydantic import Field, model_validator

from app.agent.toolcall import ToolCallAgent, ToolCollection, AgentState
from app.agent.browser import BrowserContextHelper
from app.core.logging import logger
from app.tool import BrowserUseTool, WebSearchTool, TerminateTool


# 系统提示模板
BROWSER_SYSTEM_PROMPT = """你是一个专业的网页浏览助手，能够高效地浏览和解析网页内容。
你可以导航到特定的URL，在网页上查找信息，与网页元素交互，并根据需求执行各种浏览任务。
你拥有多种工具可以调用:
{tools_description}

请根据用户需求来浏览网页，提取所需信息，并以清晰易懂的方式报告结果。
在浏览过程中，你应该充分利用浏览器功能，包括导航、点击、滚动、提取等操作。
"""

# 下一步提示模板
BROWSER_NEXT_STEP_PROMPT = """请根据当前浏览状态，确定下一步行动:
1. 访问新的网页
2. 导航到相关链接
3. 与页面元素交互
4. 提取特定信息
5. 搜索特定内容
6. 完成当前任务

当前的URL: {current_url}
当前页面标题: {current_title}
"""


class BrowserAgent(ToolCallAgent):
    """浏览器智能体，专门进行网页浏览和交互"""
    
    name: str = "browser"
    description: str = "专门进行网页浏览和交互的智能体"
    
    system_prompt: str = BROWSER_SYSTEM_PROMPT
    next_step_prompt: str = BROWSER_NEXT_STEP_PROMPT
    
    # 工具集合
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            BrowserUseTool(),
            WebSearchTool(),
            TerminateTool()
        )
    )
    
    # 特殊工具名称
    special_tool_names: List[str] = Field(default_factory=lambda: ["terminate"])
    
    # 最大观察长度
    max_observe: int = 10000
    
    # 浏览器上下文辅助类
    browser_context_helper: Optional[BrowserContextHelper] = None
    
    # 当前的浏览器状态
    _current_url: Optional[str] = None
    _current_title: Optional[str] = None
    _current_screenshot: Optional[str] = None
    
    @model_validator(mode="after")
    def initialize_helper(self) -> "BrowserAgent":
        """初始化浏览器上下文辅助类"""
        self.browser_context_helper = BrowserContextHelper(self)
        return self
    
    async def think(self) -> bool:
        """思考下一步行动
        
        根据当前浏览器状态和任务需求决定下一步行动。
        
        Returns:
            是否需要执行行动
        """
        # 更新浏览器状态
        await self._update_browser_state()
        
        # 更新下一步提示
        await self._update_next_step_prompt()
        
        # 调用基类的思考方法
        return await super().think()
    
    async def _update_browser_state(self) -> None:
        """更新浏览器状态"""
        if self.browser_context_helper:
            browser_state = await self.browser_context_helper.get_browser_state()
            if browser_state:
                self._current_url = browser_state.get("current_url")
                self._current_title = browser_state.get("title")
                self._current_screenshot = browser_state.get("screenshot")
    
    async def _update_next_step_prompt(self) -> None:
        """更新下一步提示"""
        if self.browser_context_helper:
            # 使用浏览器上下文辅助类生成提示
            browser_prompt = await self.browser_context_helper.format_next_step_prompt()
            if browser_prompt:
                self.next_step_prompt = browser_prompt
        else:
            # 回退到基本提示
            self.next_step_prompt = BROWSER_NEXT_STEP_PROMPT.format(
                current_url=self._current_url or "未加载任何页面",
                current_title=self._current_title or "未知"
            )
    
    async def run(self, request: Optional[str] = None) -> str:
        """运行浏览器智能体
        
        Args:
            request: 用户请求
            
        Returns:
            执行结果
        """
        # 设置初始请求
        if request:
            self.update_memory("user", request)
            
        try:
            # 设置智能体状态为运行中
            self.state = AgentState.ACTING
            
            while self.current_step < self.max_steps and self.state != AgentState.FINISHED:
                # 执行单个步骤
                result = await self.step()
                
                # 检查是否需要继续
                if self.is_stuck():
                    self.handle_stuck_state()
                    break
                
                self.current_step += 1
                
            # 检查是否达到最大步骤
            if self.current_step >= self.max_steps and self.state != AgentState.FINISHED:
                logger.warning(f"{self.name} 智能体达到最大步骤数 {self.max_steps}")
                self.update_memory(
                    "system",
                    f"已达到最大步骤数 {self.max_steps}。如需继续，请重新启动智能体。"
                )
            
            # 获取最终结果
            messages = self.memory.get_messages()
            final_result = "没有执行结果" if not messages else messages[-1].get("content", "")
            
            # 清理资源
            await self.cleanup()
            
            return final_result
            
        except Exception as e:
            logger.error(f"{self.name} 智能体执行失败: {str(e)}")
            self.state = AgentState.ERROR
            await self.cleanup()
            return f"执行失败: {str(e)}"
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭浏览器
            browser_tool = self.available_tools.get_tool("browser_use")
            if browser_tool:
                await browser_tool.execute(action="close")
                
            # 调用基类的清理方法
            await super().cleanup()
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
            
    def update_memory(
        self,
        role: str,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs
    ):
        """更新记忆
        
        重写以支持图像处理
        
        Args:
            role: 角色
            content: 内容
            base64_image: Base64编码的图像数据
            **kwargs: 其他参数
        """
        # 检查是否有来自浏览器的图像
        if self.browser_context_helper and not base64_image:
            base64_image = self.browser_context_helper.get_current_image()
            
        # 调用基类的方法
        super().update_memory(role, content, base64_image=base64_image, **kwargs) 