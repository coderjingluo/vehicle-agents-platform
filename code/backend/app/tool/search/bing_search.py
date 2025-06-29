"""
KunlunSec AI Platform - Bing搜索引擎实现

使用Bing搜索API执行网络搜索。
"""

import httpx
from typing import List
from pydantic import Field

from app.core.config import settings
from app.core.logging import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class BingSearchEngine(WebSearchEngine):
    """Bing搜索引擎实现"""

    api_key: str = Field(default=None)
    base_url: str = Field(default="https://api.bing.microsoft.com/v7.0/search")
    
    async def perform_search(
        self, query: str, num_results: int = 10, search_type: str = "web", **kwargs
    ) -> List[SearchItem]:
        """
        执行Bing搜索并返回结果。

        Args:
            query: 搜索查询
            num_results: 返回的结果数量
            search_type: 搜索类型（web、news、images）
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        # 检查API密钥
        api_key = self.api_key or settings.BING_SEARCH_API_KEY
        
        if not api_key:
            logger.error("未配置Bing搜索API密钥")
            return []

        # 设置请求头
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
        }
        
        # 准备API请求参数
        params = {
            "q": query,
            "count": min(num_results, 50),  # Bing API限制
            "setLang": kwargs.get("lang", "zh-CN"),
            "textDecorations": "true",
            "textFormat": "HTML"
        }
        
        # 根据搜索类型设置参数
        if search_type == "news":
            self.base_url = "https://api.bing.microsoft.com/v7.0/news/search"
        elif search_type == "images":
            self.base_url = "https://api.bing.microsoft.com/v7.0/images/search"
        
        try:
            # 执行API请求
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=20.0
                )
                response.raise_for_status()
                data = response.json()
            
            # 处理搜索结果
            results = []
            
            if search_type == "web" and "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:num_results]:
                    results.append(
                        SearchItem(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            description=item.get("snippet", ""),
                        )
                    )
            
            elif search_type == "news" and "value" in data:
                for item in data["value"][:num_results]:
                    results.append(
                        SearchItem(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            description=item.get("description", ""),
                        )
                    )
                    
            elif search_type == "images" and "value" in data:
                for item in data["value"][:num_results]:
                    results.append(
                        SearchItem(
                            title=item.get("name", ""),
                            url=item.get("contentUrl", ""),
                            description=item.get("name", ""),
                        )
                    )
                    
            return results
            
        except Exception as e:
            logger.error(f"Bing搜索失败: {str(e)}")
            return []
