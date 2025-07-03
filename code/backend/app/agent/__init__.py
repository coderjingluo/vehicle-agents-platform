"""
KunlunSec AI Platform - 智能体模块

提供不同类型的智能体实现。
"""

from app.agent.base import BaseAgent, Memory, AgentState, LLM
from app.agent.browser import BrowserAgent
# 移除对不存在的 CollaborationAgent 的导入
# from app.agent.collaboration import CollaborationAgent
from app.agent.data import DataAnalysisAgent
from app.agent.interface import AgentInterface
from app.agent.mcp import MCPAgent
from app.agent.react import ReActAgent
from app.agent.report import ReportAnalysisAgent
from app.agent.tara import TaraAgent
from app.agent.testcase import TestCaseAgent
from app.agent.toolcall import ToolCallAgent

# 导出所有智能体类
__all__ = [
    "BaseAgent", 
    "BrowserAgent",
    # "CollaborationAgent", 
    "DataAnalysisAgent", 
    "AgentInterface", 
    "LLM",
    "MCPAgent", 
    "Memory", 
    "ReActAgent", 
    "ReportAnalysisAgent", 
    "TaraAgent", 
    "TestCaseAgent",
    "ToolCallAgent", 
    "AgentState"
] 