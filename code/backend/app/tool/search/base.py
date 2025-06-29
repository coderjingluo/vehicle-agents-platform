"""
KunlunSec AI Platform - 搜索引擎基类

定义搜索引擎基类和搜索结果项模型。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    """表示单个搜索结果项"""

    title: str = Field(description="搜索结果的标题")
    url: str = Field(description="搜索结果的URL")
    description: Optional[str] = Field(
        default=None, description="搜索结果的描述或摘要"
    )

    def __str__(self) -> str:
        """搜索结果项的字符串表示"""
        return f"{self.title} - {self.url}"


class WebSearchEngine(BaseModel):
    """网络搜索引擎基类"""

    model_config = {"arbitrary_types_allowed": True}

    async def perform_search(
        self, query: str, num_results: int = 10, **kwargs
    ) -> List[SearchItem]:
        """
        执行网络搜索并返回搜索结果项列表。

        Args:
            query (str): 提交给搜索引擎的搜索查询。
            num_results (int, optional): 要返回的搜索结果数量。默认为10。
            **kwargs: 附加关键字参数。

        Returns:
            List[SearchItem]: 匹配搜索查询的SearchItem对象列表。
        """
        raise NotImplementedError("搜索引擎必须实现perform_search方法")