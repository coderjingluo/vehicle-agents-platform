"""
KunlunSec AI Platform - 沙箱模块

提供安全的命令执行环境。
"""

from app.sandbox.client import SandboxClient

# 全局沙箱客户端实例
SANDBOX_CLIENT = SandboxClient()
