"""
KunlunSec AI Platform - 工具模块

提供各种AI工具的实现。
"""

from .base import BaseTool, ToolResult
from .bash import BashTool
from .create_chat_completion import CreateChatCompletionTool
from .file_operators import FileOperatorTool
from .mcp import MCPClientTool
from .planning import PlanningTool
from .python_execute import PythonExecuteTool
from .rag_query import RAGQueryTool
from .report_generator import ReportGeneratorTool
from .tara_analysis import TaraAnalysisTool
from .terminate import TerminateTool
from .test_case_generator import TestCaseGeneratorTool
from .test_executor import TestExecutorTool
from .tool_collection import ToolCollection
from .web_search import WebSearchTool
from .str_replace_editor import StrReplaceEditorTool
from .ask_human import AskHumanTool
from .browser.browser_use import BrowserUseTool

# 导出所有工具类
__all__ = [
    "BaseTool",
    "ToolResult",
    "BashTool",
    "BrowserUseTool",
    "CreateChatCompletionTool",
    "FileOperatorTool",
    "MCPClientTool",
    "PlanningTool",
    "PythonExecuteTool",
    "RAGQueryTool",
    "ReportGeneratorTool",
    "TaraAnalysisTool",
    "TerminateTool",
    "TestCaseGeneratorTool",
    "TestExecutorTool",
    "ToolCollection",
    "WebSearchTool",
    "StrReplaceEditorTool",
    "AskHumanTool",
]

# 默认工具集合
DEFAULT_TOOLS = [
    BashTool,
    BrowserUseTool,
    CreateChatCompletionTool,
    FileOperatorTool,
    PlanningTool,
    PythonExecuteTool,
    RAGQueryTool,
    ReportGeneratorTool,
    TaraAnalysisTool,
    TerminateTool,
    TestCaseGeneratorTool,
    TestExecutorTool,
    WebSearchTool,
    StrReplaceEditorTool,
    AskHumanTool,
] 