"""
KunlunSec AI Platform - 浏览器上下文辅助模块

提供浏览器上下文管理和状态跟踪功能。
"""

from typing import TYPE_CHECKING, Optional, Dict, Any

from app.core.logging import logger
from app.agent.browser.browser import BrowserAgent
from app.agent.browser.browser_context_helper import BrowserContextHelper

# 避免循环导入
if TYPE_CHECKING:
    from app.agent.base import BaseAgent

__all__ = ["BrowserContextHelper", "BrowserAgent"]

class BrowserContextHelper:
    """浏览器上下文辅助类
    
    负责跟踪和管理与浏览器相关的上下文信息，并提供在智能体中使用浏览器的辅助功能。
    """
    
    def __init__(self, agent: "BaseAgent"):
        """初始化浏览器上下文辅助类
        
        Args:
            agent: 所属的智能体实例
        """
        self.agent = agent
        self._current_base64_image: Optional[str] = None
        self._current_browser_state: Dict[str, Any] = {}
    
    async def get_browser_state(self) -> Optional[Dict[str, Any]]:
        """获取当前浏览器状态
        
        Returns:
            当前浏览器状态信息，如果浏览器工具不可用则返回None
        """
        # 从可用工具中查找浏览器工具
        browser_tool = None
        if hasattr(self.agent, "available_tools") and hasattr(self.agent.available_tools, "get_tool"):
            browser_tool = self.agent.available_tools.get_tool("browser_use")
        
        if not browser_tool or not hasattr(browser_tool, "get_current_state"):
            logger.warning("浏览器工具不可用或未实现get_current_state方法")
            return None
            
        try:
            result = await browser_tool.get_current_state()
            if hasattr(result, "error") and result.error:
                logger.warning(f"获取浏览器状态失败: {result.error}")
                return None
                
            # 从结果中提取状态信息
            if hasattr(result, "output"):
                # 尝试解析JSON
                try:
                    import json
                    state = json.loads(result.output)
                    self._current_browser_state = state
                    return state
                except Exception as e:
                    logger.error(f"解析浏览器状态失败: {str(e)}")
                    return {"raw_output": result.output}
            
            # 如果输出不是标准格式，返回基本信息
            return self._current_browser_state
                
        except Exception as e:
            logger.error(f"获取浏览器状态时出错: {str(e)}")
            return None
    
    async def format_next_step_prompt(self) -> str:
        """格式化基于浏览器上下文的下一步提示
        
        Returns:
            包含浏览器当前状态信息的提示文本
        """
        # 获取最新的浏览器状态
        browser_state = await self.get_browser_state()
        
        # 根据状态格式化提示
        if not browser_state:
            # 未获取到状态时返回基本提示
            return """你正在使用浏览器工具。请根据当前需求，决定下一步浏览行动:
1. 访问特定网页
2. 搜索相关信息
3. 提取当前页面信息
4. 与网页元素交互
"""
        
        # 构建包含当前状态信息的提示
        current_url = browser_state.get("current_url", "未知URL")
        page_title = browser_state.get("title", "未知标题")
        
        # 检查是否有页面截图
        has_screenshot = bool(browser_state.get("screenshot", False))
        screenshot_text = "\n你可以看到当前页面的截图。" if has_screenshot else ""
        
        return f"""你正在使用浏览器工具。以下是当前浏览器状态:
- 当前URL: {current_url}
- 页面标题: {page_title}{screenshot_text}

请根据上述状态，决定下一步行动:
1. 继续浏览或导航到其他页面
2. 提取当前页面的关键信息
3. 搜索特定内容
4. 与网页元素交互（点击、输入等）
5. 返回之前的任务
"""
    
    def set_current_image(self, base64_image: Optional[str]) -> None:
        """设置当前浏览器截图
        
        Args:
            base64_image: Base64编码的图像数据
        """
        self._current_base64_image = base64_image
    
    def get_current_image(self) -> Optional[str]:
        """获取当前浏览器截图
        
        Returns:
            Base64编码的图像数据
        """
        return self._current_base64_image 