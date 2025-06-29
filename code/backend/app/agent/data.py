"""
KunlunSec AI Platform - 数据分析智能体模块

实现专门处理数据分析和可视化的智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from app.agent.base import BaseAgent, AgentState, LLM, Memory

# 数据分析系统提示
DATA_ANALYSIS_SYSTEM_PROMPT = """你是一个专门进行数据分析和可视化的AI助手。
你的任务是分析车联网安全测试数据，提取有价值的信息，并生成可视化结果。
你可以使用以下工具:
{tools_description}

请确保分析结果准确、直观，并提供有价值的见解。
"""

class PythonExecute:
    """Python代码执行工具"""
    name: str = "python_execute"
    description: str = "执行Python代码"
    
    async def run(self, code: str, **kwargs) -> Dict[str, Any]:
        """执行Python代码"""
        # 实际实现将在安全环境中执行代码
        return {
            "result": f"执行代码的结果: {code[:50]}...",
            "output": "代码执行输出",
            "error": None
        }

class DataVisualizationTool:
    """数据可视化工具"""
    name: str = "data_visualization"
    description: str = "生成数据可视化"
    
    async def run(self, data: Dict[str, Any], chart_type: str = "bar", **kwargs) -> Dict[str, Any]:
        """生成可视化"""
        # 实际实现将生成可视化图表
        return {
            "chart_type": chart_type,
            "data": data,
            "image_base64": "模拟的Base64图像数据",
            "description": f"生成的{chart_type}图表"
        }

class FileOperatorTool:
    """文件操作工具"""
    name: str = "file_operator"
    description: str = "读写文件"
    
    async def run(self, operation: str, path: str, content: Optional[str] = None, **kwargs) -> str:
        """执行文件操作"""
        if operation == "read":
            # 实际实现将读取文件
            return f"读取文件 {path} 的内容"
        elif operation == "write":
            # 实际实现将写入文件
            return f"写入内容到文件 {path}"
        else:
            return f"不支持的操作: {operation}"

class ToolCollection:
    """工具集合"""
    
    def __init__(self, *tools):
        self.tools = list(tools)
    
    def add_tool(self, tool):
        """添加工具"""
        self.tools.append(tool)
    
    def get_tool(self, name: str):
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

class DataAnalysisAgent(BaseAgent):
    """专门处理数据分析的智能体"""
    
    name: str = "DataAnalysis"
    description: str = "专门处理数据分析和可视化的智能体"
    
    system_prompt: str = DATA_ANALYSIS_SYSTEM_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        PythonExecute(),
        DataVisualizationTool(),
        FileOperatorTool(),
    ))
    
    # 数据分析特定方法
    async def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据并生成结果"""
        # 准备分析代码
        analysis_code = self._prepare_analysis_code(data)
        
        # 执行分析
        python_tool = self.available_tools.get_tool("python_execute")
        if not python_tool:
            return {"error": "Python执行工具不可用"}
        
        result = await python_tool.run(code=analysis_code)
        
        # 处理结果
        if result.get("error"):
            return {"error": result["error"]}
        
        # 解析和整理结果
        analysis_result = self._parse_analysis_result(result.get("result", ""))
        
        return analysis_result
    
    def _prepare_analysis_code(self, data: Dict[str, Any]) -> str:
        """准备数据分析代码"""
        # 根据数据类型生成适当的分析代码
        code = """
import pandas as pd
import numpy as np
from io import StringIO
import json

# 解析输入数据
data = json.loads('''
%s
''')

# 转换为DataFrame
df = pd.DataFrame(data)

# 基本统计分析
stats = df.describe().to_dict()

# 检查缺失值
missing = df.isnull().sum().to_dict()

# 相关性分析
correlations = {}
if df.select_dtypes(include=[np.number]).shape[1] > 1:
    correlations = df.corr().to_dict()

# 返回结果
result = {
    "stats": stats,
    "missing": missing,
    "correlations": correlations,
    "columns": list(df.columns),
    "shape": df.shape
}

print(json.dumps(result))
""" % (str(data).replace("'", '"'))
        
        return code
    
    def _parse_analysis_result(self, result_str: str) -> Dict[str, Any]:
        """解析分析结果"""
        # 实际实现将解析JSON结果
        # 这里简化处理
        return {
            "summary": "数据分析结果摘要",
            "details": result_str,
            "insights": ["见解1", "见解2"]
        }
    
    async def visualize_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成数据可视化"""
        # 获取可视化工具
        viz_tool = self.available_tools.get_tool("data_visualization")
        if not viz_tool:
            return {"error": "数据可视化工具不可用"}
        
        # 确定合适的图表类型
        chart_type = self._determine_chart_type(analysis_result)
        
        # 准备可视化数据
        viz_data = self._prepare_visualization_data(analysis_result, chart_type)
        
        # 生成可视化
        visualization = await viz_tool.run(
            data=viz_data,
            chart_type=chart_type
        )
        
        return visualization
    
    def _determine_chart_type(self, analysis_result: Dict[str, Any]) -> str:
        """确定合适的图表类型"""
        # 根据数据特性选择图表类型
        # 简化实现
        return "bar"
    
    def _prepare_visualization_data(self, analysis_result: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """准备可视化数据"""
        # 根据图表类型准备数据
        # 简化实现
        return {
            "labels": ["A", "B", "C"],
            "values": [1, 2, 3],
            "title": "数据分析可视化"
        }
    
    async def step(self) -> str:
        """执行数据分析步骤"""
        # 获取当前任务
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        user_message = next((m for m in recent_messages if m.get("role") == "user"), None)
        
        if not user_message:
            return "没有待处理的用户请求"
        
        # 解析用户请求
        request = user_message.get("content", "")
        
        # 根据请求类型执行不同操作
        if "分析" in request or "analyze" in request.lower():
            # 提取数据
            data = self._extract_data_from_request(request)
            
            # 分析数据
            analysis_result = await self.analyze_data(data)
            
            # 更新记忆
            self.update_memory("assistant", f"数据分析完成，结果: {str(analysis_result)[:100]}...")
            
            return f"数据分析完成，发现 {len(analysis_result.get('insights', []))} 个见解"
            
        elif "可视化" in request or "visualize" in request.lower():
            # 获取最近的分析结果
            analysis_result = self._get_recent_analysis_result()
            
            if not analysis_result:
                self.update_memory("assistant", "未找到可用的分析结果进行可视化")
                return "请先进行数据分析"
            
            # 生成可视化
            visualization = await self.visualize_data(analysis_result)
            
            # 更新记忆
            self.update_memory("assistant", f"数据可视化完成，类型: {visualization.get('chart_type')}")
            
            return f"生成了 {visualization.get('chart_type')} 类型的可视化图表"
        else:
            # 默认行为
            self.update_memory("assistant", "无法理解请求，请指定是要进行数据分析还是数据可视化")
            return "请指定是要进行数据分析还是数据可视化"
    
    def _extract_data_from_request(self, request: str) -> Dict[str, Any]:
        """从请求中提取数据"""
        # 实际实现将解析请求中的数据
        # 简化实现
        return {
            "column1": [1, 2, 3],
            "column2": [4, 5, 6]
        }
    
    def _get_recent_analysis_result(self) -> Optional[Dict[str, Any]]:
        """获取最近的分析结果"""
        # 从记忆中查找分析结果
        for message in reversed(self.memory.messages):
            if message.get("role") == "assistant" and "数据分析完成" in message.get("content", ""):
                # 实际实现将解析消息内容
                return {
                    "summary": "示例分析结果",
                    "data": {
                        "column1": [1, 2, 3],
                        "column2": [4, 5, 6]
                    }
                }
        return None 