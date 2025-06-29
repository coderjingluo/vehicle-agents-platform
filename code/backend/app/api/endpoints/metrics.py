"""
KunlunSec AI Platform - 监控指标端点

提供Prometheus监控指标的端点。
"""

from fastapi import APIRouter
from starlette.responses import Response
import prometheus_client

# 创建路由器
metrics_router = APIRouter()

@metrics_router.get("/metrics", tags=["监控"])
async def metrics():
    """
    获取Prometheus监控指标
    
    返回所有已注册的Prometheus指标，格式为Prometheus文本格式。
    """
    return Response(
        prometheus_client.generate_latest(),
        media_type="text/plain"
    ) 