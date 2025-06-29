"""
KunlunSec AI Platform - DuckDuckGo搜索引擎实现

使用DuckDuckGo API执行网络搜索。
"""

from typing import List
import httpx
import json

from app.core.logging import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class DuckDuckGoSearchEngine(WebSearchEngine):
    """DuckDuckGo搜索引擎实现"""
    
    async def perform_search(
        self, query: str, num_results: int = 10, **kwargs
    ) -> List[SearchItem]:
        """
        执行DuckDuckGo搜索并返回结果。

        Args:
            query: 搜索查询
            num_results: 返回的结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        try:
            # DuckDuckGo不需要API密钥，使用非官方API接口
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # 设置API参数
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "no_redirect": 1,
                "kl": kwargs.get("lang", "cn-zh"),  # 本地化设置
            }
            
            base_url = "https://api.duckduckgo.com"
            
            # 执行API请求
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            # 处理搜索结果
            results = []
            
            # 提取抽象文本结果
            if "AbstractText" in data and data["AbstractText"]:
                results.append(
                    SearchItem(
                        title=data.get("Heading", "DuckDuckGo精选结果"),
                        url=data.get("AbstractURL", ""),
                        description=data.get("AbstractText", ""),
                    )
                )
            
            # 提取相关主题
            if "RelatedTopics" in data:
                for topic in data["RelatedTopics"][:num_results]:
                    if "FirstURL" in topic and "Text" in topic:
                        results.append(
                            SearchItem(
                                title=topic.get("Text", "").split(" - ")[0],
                                url=topic.get("FirstURL", ""),
                                description=topic.get("Text", ""),
                            )
                        )
            
            # 如果还不够，提取即时回答结果
            if "Results" in data and len(results) < num_results:
                for result in data["Results"]:
                    if len(results) >= num_results:
                        break
                    results.append(
                        SearchItem(
                            title=result.get("Text", "DuckDuckGo结果"),
                            url=result.get("FirstURL", ""),
                            description=result.get("Text", ""),
                        )
                    )
            
            return results[:num_results]
                
        except Exception as e:
            logger.error(f"DuckDuckGo搜索失败: {str(e)}")
            return []
