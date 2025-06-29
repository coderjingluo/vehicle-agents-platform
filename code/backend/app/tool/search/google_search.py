"""
KunlunSec AI Platform - Google搜索引擎实现

使用Google API执行网络搜索。
"""

import httpx
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class GoogleSearchEngine(WebSearchEngine):
    """Google搜索引擎实现"""

    async def perform_search(
        self, query: str, num_results: int = 10, search_type: str = "web", **kwargs
    ) -> List[SearchItem]:
        """
        执行Google搜索并返回结果。

        Args:
            query: 搜索查询
            num_results: 返回的结果数量
            search_type: 搜索类型（web、news、images）
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        # 检查API密钥
        api_key = settings.GOOGLE_SEARCH_API_KEY
        cx = settings.GOOGLE_SEARCH_CX
        
        if not api_key or not cx:
            logger.error("未配置Google搜索API密钥或搜索引擎ID")
            return []
        
        # 准备API请求
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num_results, 10),  # Google API限制最多10个结果
        }
        
        # 根据搜索类型设置参数
        if search_type == "news":
            params["sort"] = "date"
        elif search_type == "images":
            params["searchType"] = "image"
        
        try:
            # 执行API请求
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 处理搜索结果
            results = []
            if "items" in data:
                for item in data["items"]:
                    result = SearchItem(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        description=item.get("snippet", ""),
                    )
                    results.append(result)
                    
            return results
        
        except Exception as e:
            logger.error(f"Google搜索失败: {str(e)}")
            return []
