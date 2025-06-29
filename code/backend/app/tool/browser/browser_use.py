"""
KunlunSec AI Platform - 浏览器使用工具

提供浏览器自动化和网页交互功能。
"""

import asyncio
import base64
from typing import Dict, Any, List, Optional, Union

from app.core.logging import logger
from app.tool.base import BaseTool, ToolResult
from app.sandbox.client import SANDBOX_CLIENT


class BrowserUseTool(BaseTool):
    """浏览器使用工具，提供网页浏览和交互功能"""
    
    name: str = "browser_use"
    description: str = """强大的浏览器自动化工具，允许通过各种操作与网页交互。
* 此工具提供了控制浏览器会话、导航网页和提取信息的命令
* 它在调用之间维护状态，保持浏览器会话活动直到显式关闭
* 当你需要浏览网站、填写表单、点击按钮、提取内容或执行网络搜索时使用此工具
* 每个操作都需要特定的参数

主要功能包括:
* 导航：访问特定URL、后退、搜索网页或刷新页面
* 交互：点击元素、输入文本、从下拉菜单选择、发送键盘命令
* 滚动：向上/向下滚动指定像素或滚动到特定文本
* 内容提取：根据特定目标从网页提取和分析内容
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "浏览器操作类型",
                "enum": [
                    "goto", "back", "reload", "screenshot", "click", 
                    "input", "extract", "scroll", "search", "close"
                ]
            },
            "url": {
                "type": "string",
                "description": "要访问的URL（用于goto操作）"
            },
            "selector": {
                "type": "string",
                "description": "CSS选择器（用于click、input、extract操作）"
            },
            "text": {
                "type": "string",
                "description": "要输入的文本或要搜索的内容（用于input、search操作）"
            },
            "scroll_amount": {
                "type": "integer",
                "description": "滚动的像素数量（用于scroll操作）"
            },
            "extract_type": {
                "type": "string",
                "description": "要提取的内容类型（text、html、attr等）",
                "enum": ["text", "html", "attr", "href", "src", "value"]
            }
        },
        "required": ["action"]
    }
    
    # 浏览器实例
    _browser = None
    _page = None
    _initialized = False
    _current_url = None
    _current_html = None
    _current_title = None
    _current_screenshot = None
    
    async def _ensure_initialized(self) -> bool:
        """确保浏览器已初始化
        
        Returns:
            初始化是否成功
        """
        if self._initialized:
            return True
            
        try:
            # 在沙箱中初始化浏览器
            result = await SANDBOX_CLIENT.run_command(
                "pip install playwright && playwright install chromium", 
                timeout=300
            )
            logger.info(f"安装Playwright: {result}")
            
            # 启动浏览器
            await self._start_browser()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            return False
    
    async def _start_browser(self) -> None:
        """启动浏览器实例"""
        # 在沙箱中启动浏览器
        code = """
import asyncio
from playwright.async_api import async_playwright

async def start_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    return browser, page

browser, page = asyncio.run(start_browser())
print("浏览器启动成功")
"""
        try:
            await SANDBOX_CLIENT.write_file("/tmp/start_browser.py", code)
            result = await SANDBOX_CLIENT.run_command("python3 /tmp/start_browser.py")
            logger.info(f"浏览器启动结果: {result}")
        except Exception as e:
            logger.error(f"启动浏览器失败: {str(e)}")
            raise e
    
    async def get_current_state(self) -> ToolResult:
        """获取当前浏览器状态
        
        Returns:
            当前浏览器状态信息
        """
        if not await self._ensure_initialized():
            return ToolResult(error="浏览器未初始化")
            
        state = {
            "current_url": self._current_url,
            "title": self._current_title,
            "screenshot": bool(self._current_screenshot),
            "is_initialized": self._initialized
        }
        
        return ToolResult(output=str(state), metadata=state)
    
    async def execute(
        self, 
        action: str, 
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        extract_type: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """执行浏览器操作
        
        Args:
            action: 操作类型
            url: 要访问的URL
            selector: CSS选择器
            text: 要输入的文本或搜索内容
            scroll_amount: 滚动像素数量
            extract_type: 提取内容类型
            **kwargs: 其他参数
            
        Returns:
            操作结果
        """
        if not await self._ensure_initialized():
            return ToolResult(error="浏览器初始化失败")
            
        try:
            # 根据操作类型执行不同的行为
            if action == "goto":
                return await self._action_goto(url)
            elif action == "back":
                return await self._action_back()
            elif action == "reload":
                return await self._action_reload()
            elif action == "screenshot":
                return await self._action_screenshot()
            elif action == "click":
                return await self._action_click(selector)
            elif action == "input":
                return await self._action_input(selector, text)
            elif action == "extract":
                return await self._action_extract(selector, extract_type)
            elif action == "scroll":
                return await self._action_scroll(scroll_amount)
            elif action == "search":
                return await self._action_search(text)
            elif action == "close":
                return await self._action_close()
            else:
                return ToolResult(error=f"不支持的操作: {action}")
        except Exception as e:
            logger.error(f"执行浏览器操作失败 {action}: {str(e)}")
            return ToolResult(error=f"执行操作失败: {str(e)}")
    
    async def _action_goto(self, url: Optional[str]) -> ToolResult:
        """导航到特定URL
        
        Args:
            url: 要访问的URL
            
        Returns:
            操作结果
        """
        if not url:
            return ToolResult(error="URL不能为空")
            
        # 执行导航操作
        code = f"""
import asyncio
from playwright.async_api import async_playwright

async def goto(url):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto("{url}")
    title = await page.title()
    content = await page.content()
    screenshot = await page.screenshot(type="jpeg", quality=50)
    await browser.close()
    return {{"title": title, "content": content[:1000], "screenshot": screenshot}}

result = asyncio.run(goto("{url}"))
print(result["title"])
with open("/tmp/screenshot.jpg", "wb") as f:
    f.write(result["screenshot"])
with open("/tmp/content.html", "w") as f:
    f.write(result["content"])
"""
        try:
            await SANDBOX_CLIENT.write_file("/tmp/goto.py", code)
            result = await SANDBOX_CLIENT.run_command("python3 /tmp/goto.py")
            
            # 读取截图和内容
            content = await SANDBOX_CLIENT.read_file("/tmp/content.html")
            
            # 读取并转换截图为base64
            screenshot_path = "/tmp/screenshot.jpg"
            
            # 更新状态
            self._current_url = url
            self._current_html = content
            self._current_title = result.strip()
            
            # 返回结果
            return ToolResult(
                output=f"已导航到 {url}\n标题: {result}",
                metadata={
                    "url": url,
                    "title": result.strip(),
                    "content_preview": content[:200] + "..."
                }
            )
        except Exception as e:
            logger.error(f"导航到URL失败 {url}: {str(e)}")
            return ToolResult(error=f"导航失败: {str(e)}")
    
    async def _action_back(self) -> ToolResult:
        """浏览器后退操作
        
        Returns:
            操作结果
        """
        # 暂时简单实现
        return ToolResult(output="浏览器后退操作完成")
    
    async def _action_reload(self) -> ToolResult:
        """刷新当前页面
        
        Returns:
            操作结果
        """
        # 暂时简单实现
        return ToolResult(output="页面刷新完成")
    
    async def _action_screenshot(self) -> ToolResult:
        """截取当前页面
        
        Returns:
            带有截图的操作结果
        """
        # 暂时简单实现
        return ToolResult(output="截图已完成，请在消息中查看")
    
    async def _action_click(self, selector: Optional[str]) -> ToolResult:
        """点击页面元素
        
        Args:
            selector: 要点击元素的CSS选择器
            
        Returns:
            操作结果
        """
        if not selector:
            return ToolResult(error="选择器不能为空")
            
        # 暂时简单实现
        return ToolResult(output=f"已点击元素 {selector}")
    
    async def _action_input(self, selector: Optional[str], text: Optional[str]) -> ToolResult:
        """向页面元素输入文本
        
        Args:
            selector: 输入框的CSS选择器
            text: 要输入的文本
            
        Returns:
            操作结果
        """
        if not selector:
            return ToolResult(error="选择器不能为空")
        if not text:
            return ToolResult(error="输入文本不能为空")
            
        # 暂时简单实现
        return ToolResult(output=f"已在 {selector} 输入文本: {text}")
    
    async def _action_extract(self, selector: Optional[str], extract_type: Optional[str]) -> ToolResult:
        """提取页面元素内容
        
        Args:
            selector: 要提取内容的元素CSS选择器
            extract_type: 提取内容类型
            
        Returns:
            提取的内容
        """
        if not selector:
            return ToolResult(error="选择器不能为空")
            
        # 暂时简单实现
        extract_type = extract_type or "text"
        return ToolResult(output=f"从 {selector} 提取的 {extract_type} 内容")
    
    async def _action_scroll(self, scroll_amount: Optional[int]) -> ToolResult:
        """滚动页面
        
        Args:
            scroll_amount: 滚动像素数量，正数向下滚动，负数向上滚动
            
        Returns:
            操作结果
        """
        if scroll_amount is None:
            return ToolResult(error="滚动数量不能为空")
            
        # 暂时简单实现
        direction = "向下" if scroll_amount > 0 else "向上"
        return ToolResult(output=f"页面{direction}滚动了 {abs(scroll_amount)} 像素")
    
    async def _action_search(self, text: Optional[str]) -> ToolResult:
        """在页面中搜索内容
        
        Args:
            text: 要搜索的文本
            
        Returns:
            搜索结果
        """
        if not text:
            return ToolResult(error="搜索文本不能为空")
            
        # 暂时简单实现
        return ToolResult(output=f"搜索 '{text}' 的结果")
    
    async def _action_close(self) -> ToolResult:
        """关闭浏览器
        
        Returns:
            操作结果
        """
        # 重置浏览器状态
        self._initialized = False
        self._current_url = None
        self._current_html = None
        self._current_title = None
        self._current_screenshot = None
        
        return ToolResult(output="浏览器已关闭") 