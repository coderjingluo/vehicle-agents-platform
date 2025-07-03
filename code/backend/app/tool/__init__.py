"""
KunlunSec AI Platform - 工具模块

提供各种工具的集合。
"""

from app.tool.base import BaseTool, ToolResult
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.terminate import TerminateTool
from app.tool.planning import PlanningTool
from app.tool.bash import BashTool
from app.tool.web_search import WebSearchTool
from app.tool.file_operators import FileOperatorTool
from app.tool.rag_query import RAGQueryTool
from app.tool.tara_analysis import TaraAnalysisTool
from app.tool.code_generator import CodeGeneratorTool
from app.tool.test_executor import TestExecutorTool
from app.tool.test_case_generator import TestCaseGeneratorTool
from app.tool.report_generator import ReportGeneratorTool
from app.tool.str_replace_editor import StrReplaceEditorTool
from app.tool.python_execute import PythonExecuteTool
from app.tool.mcp import MCPTool
from app.tool.ask_human import AskHumanTool

# 浏览器相关工具
from app.tool.browser import BrowserUseTool

# 搜索相关工具
# from app.tool.search import BaiduSearchTool, GoogleSearchTool, DuckDuckGoSearchTool

# 图表可视化工具
# from app.tool.chart_visualization import ChartVisualizationTool, ChartPrepareTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "CreateChatCompletionTool",
    "TerminateTool",
    "PlanningTool",
    "BashTool",
    "WebSearchTool",
    "FileOperatorTool",
    "RAGQueryTool",
    "TaraAnalysisTool",
    "CodeGeneratorTool",
    "TestExecutorTool",
    "TestCaseGeneratorTool",
    "ReportGeneratorTool",
    "StrReplaceEditorTool",
    "PythonExecuteTool",
    "MCPTool",
    "AskHumanTool",
    "BrowserUseTool"
]

# 默认工具集合
DEFAULT_TOOLS = [
    BashTool,
    FileOperatorTool,
    PythonExecuteTool,
    WebSearchTool,
    CreateChatCompletionTool,
    StrReplaceEditorTool,
    RAGQueryTool,
    ReportGeneratorTool,
    TestCaseGeneratorTool,
    TestExecutorTool,
    TerminateTool,
    TaraAnalysisTool,
    PlanningTool,
    MCPTool,
    BrowserUseTool,
    CodeGeneratorTool,
    AskHumanTool,
] 