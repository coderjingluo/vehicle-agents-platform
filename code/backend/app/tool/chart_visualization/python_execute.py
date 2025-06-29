"""
KunlunSec AI Platform - 图表可视化Python执行工具

提供用于数据分析和报告生成的Python代码执行功能。
"""

from app.core.config import config
from app.tool.python_execute import PythonExecuteTool


class NormalPythonExecuteTool(PythonExecuteTool):
    """用于执行Python代码的工具，带有超时和安全限制"""

    name: str = "normal_python_execute"
    description: str = """执行Python代码进行深入数据分析/数据报告(任务结论)/其他不直接可视化的普通任务。"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "code_type": {
                "description": "代码类型，数据处理/数据报告/其他",
                "type": "string",
                "default": "process",
                "enum": ["process", "report", "others"],
            },
            "code": {
                "type": "string",
                "description": """要执行的Python代码。
# 注意
1. 代码应生成一个全面的基于文本的报告，包含数据集概述、列详情、基本统计信息、派生指标、时间序列比较、异常值和关键见解。
2. 使用print()输出所有内容，以便清晰显示分析结果（包括"数据集概述"或"预处理结果"等部分）并保存。
3. 将任何报告/处理文件/每个分析结果保存在工作空间目录中：{directory}
4. 数据报告需要内容丰富，包括您的整体分析过程和相应的数据可视化。
5. 您可以逐步调用此工具，从摘要到深入进行数据分析，同时保存数据报告""".format(
                    directory=config.workspace_dir
                ),
            },
        },
        "required": ["code"],
    }

    async def execute(self, code: str, code_type: str = None, timeout: int = 5, **kwargs):
        """执行Python代码
        
        Args:
            code: 要执行的Python代码
            code_type: 代码类型
            timeout: 超时时间（秒）
            
        Returns:
            执行结果
        """
        return await super().execute(code=code, timeout=timeout) 