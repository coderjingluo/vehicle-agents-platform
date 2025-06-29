"""
通用模式定义
"""

from typing import Dict, List, Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


T = TypeVar('T')


class ResponseModel(GenericModel, Generic[T]):
    """通用响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: str = "操作成功"


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: ErrorDetail


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(10, ge=1, le=100, description="每页数量")
    sort: Optional[str] = Field(None, description="排序字段")
    order: Optional[str] = Field("desc", description="排序方向")
