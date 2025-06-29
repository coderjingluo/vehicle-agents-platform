"""
KunlunSec AI Platform - 网络搜索工具

提供网络搜索功能，支持多种搜索引擎。
"""

import json
import asyncio
from typing import Dict, List, Optional, Any

from app.core.logging import logger
from app.core.config import settings
from .base import BaseTool, ToolResult
from .search import (
    BaiduSearchEngine,
    BingSearchEngine,
    DuckDuckGoSearchEngine,
    GoogleSearchEngine,
    SearchItem,
    WebSearchEngine
)


class WebSearch(BaseTool):
    """网络搜索工具"""
    
    name: str = "web_search"
    description: str = """执行网络搜索并返回结果。
可以搜索最新信息、新闻、定义、事实等。
提供查询以获取相关搜索结果。
支持多种搜索引擎，包括Google、Bing、DuckDuckGo和百度。
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询"
            },
            "num_results": {
                "type": "integer",
                "description": "返回的结果数量（默认为5）"
            },
            "search_engine": {
                "type": "string",
                "description": "使用的搜索引擎（google、bing、duckduckgo、baidu）",
                "enum": ["google", "bing", "duckduckgo", "baidu", "auto"]
            },
            "search_type": {
                "type": "string",
                "description": "搜索类型（web、news、images）",
                "enum": ["web", "news", "images"]
            }
        },
        "required": ["query"]
    }
    
    # 搜索引擎实例
    _search_engines: Dict[str, WebSearchEngine] = {
        "google": GoogleSearchEngine(),
        "bing": BingSearchEngine(),
        "duckduckgo": DuckDuckGoSearchEngine(),
        "baidu": BaiduSearchEngine(),
    }
    
    async def execute(self, query: str, num_results: int = 5, 
                     search_engine: str = "auto", search_type: str = "web", 
                     **kwargs) -> ToolResult:
        """执行网络搜索
        
        Args:
            query: 搜索查询
            num_results: 返回的结果数量
            search_engine: 使用的搜索引擎
            search_type: 搜索类型
            
        Returns:
            搜索结果
        """
        try:
            # 限制结果数量
            num_results = min(max(1, num_results), 10)
            
            # 选择搜索引擎
            if search_engine == "auto":
                # 自动选择搜索引擎，按优先级尝试
                search_results = await self._try_all_engines(query, num_results, search_type)
            else:
                # 使用指定的搜索引擎
                if search_engine not in self._search_engines:
                    return ToolResult(error=f"不支持的搜索引擎: {search_engine}")
                
                engine = self._search_engines[search_engine]
                search_results = await engine.perform_search(
                    query=query,
                    num_results=num_results,
                    search_type=search_type
                )
            
            # 格式化结果
            formatted_results = self._format_results(query, search_results, search_type)
            
            return ToolResult(output=formatted_results)
        except Exception as e:
            logger.error(f"执行网络搜索失败: {str(e)}")
            return ToolResult(error=f"搜索失败: {str(e)}")
    
    async def _try_all_engines(
        self, query: str, num_results: int, search_type: str
    ) -> List[SearchItem]:
        """尝试所有搜索引擎，按优先级返回第一个成功的结果"""
        # 确定优先级顺序
        engine_order = self._get_engine_order()
        
        for engine_name in engine_order:
            try:
                logger.info(f"正在尝试使用 {engine_name} 引擎进行搜索")
                engine = self._search_engines[engine_name]
                results = await engine.perform_search(
                    query=query, 
                    num_results=num_results,
                    search_type=search_type
                )
                
                if results:
                    logger.info(f"{engine_name} 搜索成功，找到 {len(results)} 个结果")
                    return results
                    
            except Exception as e:
                logger.warning(f"{engine_name} 搜索失败: {str(e)}")
                continue
                
        # 如果所有搜索引擎都失败，返回空列表
        logger.warning("所有搜索引擎都失败了")
        return []
    
    def _get_engine_order(self) -> List[str]:
        """获取搜索引擎优先级顺序"""
        # 首先检查是否配置了特定的API密钥
        engine_order = []
        
        # 如果配置了Google API密钥，优先使用Google
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_CX:
            engine_order.append("google")
            
        # 如果配置了Bing API密钥，其次使用Bing
        if settings.BING_SEARCH_API_KEY:
            engine_order.append("bing")
        
        # DuckDuckGo不需要API密钥，可以直接使用
        engine_order.append("duckduckgo")
        
        # 百度作为最后的备选
        engine_order.append("baidu")
        
        # 确保不返回重复的引擎
        return list(dict.fromkeys(engine_order))
    
    def _format_results(self, query: str, results: List[SearchItem], search_type: str) -> str:
        """格式化搜索结果"""
        if not results:
            return "未找到搜索结果。"
        
        output = []
        
        # 添加搜索结果标题
        output.append(f"### 搜索结果: {query}\n")
        
        # 格式化每个结果
        for i, result in enumerate(results, 1):
            # 添加标题和链接
            title = result.title or "无标题"
            url = result.url or ""
            output.append(f"{i}. **{title}**")
            output.append(f"   链接: {url}")
            
            # 添加摘要
            description = result.description or ""
            if description:
                # 清理描述文本
                description = description.replace("\n", " ")
                if len(description) > 200:
                    description = description[:200] + "..."
                output.append(f"   摘要: {description}")
            
            # 添加分隔符
            output.append("")
        
        return "\n".join(output) 