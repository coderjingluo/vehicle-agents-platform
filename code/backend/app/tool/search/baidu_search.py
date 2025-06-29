"""
KunlunSec AI Platform - 百度搜索引擎实现

使用百度搜索API执行网络搜索。
"""

from typing import List
import httpx
import json
from bs4 import BeautifulSoup
import re

from app.core.logging import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class BaiduSearchEngine(WebSearchEngine):
    """百度搜索引擎实现"""
    
    async def perform_search(
        self, query: str, num_results: int = 10, **kwargs
    ) -> List[SearchItem]:
        """
        执行百度搜索并返回结果。

        Args:
            query: 搜索查询
            num_results: 返回的结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        try:
            # 百度搜索使用请求网页然后解析结果的方式
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.baidu.com/",
            }
            
            search_url = f"https://www.baidu.com/s?wd={query}&rn={min(num_results*2, 50)}"
            
            # 执行请求
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=headers, follow_redirects=True, timeout=15.0)
                response.raise_for_status()
                html_content = response.text
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # 提取搜索结果
            for result_div in soup.select('.result.c-container')[:num_results]:
                try:
                    # 提取标题
                    title_elem = result_div.select_one('h3 a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                    else:
                        continue
                    
                    # 提取URL（百度使用重定向链接，需要特殊处理）
                    url = ''
                    if title_elem and title_elem.has_attr('href'):
                        url = title_elem['href']
                    
                    # 提取描述
                    desc_elem = result_div.select_one('.content-right_8Zs40')
                    desc = desc_elem.get_text().strip() if desc_elem else ""
                    
                    # 创建搜索结果项
                    if title and url:
                        results.append(
                            SearchItem(
                                title=title,
                                url=url,
                                description=desc
                            )
                        )
                except Exception as inner_e:
                    logger.warning(f"解析百度搜索结果项时出错: {str(inner_e)}")
                    continue
                    
            return results[:num_results]
                
        except Exception as e:
            logger.error(f"百度搜索失败: {str(e)}")
            return []
