"""
KunlunSec AI Platform - 图表可视化准备工具

提供图表生成的数据准备功能。
"""

from app.tool.chart_visualization.python_execute import NormalPythonExecuteTool


class VisualizationPrepareTool(NormalPythonExecuteTool):
    """图表生成准备工具"""

    name: str = "visualization_preparation"
    description: str = "使用Python代码生成data_visualization工具的元数据。输出：1) JSON信息。2) 清洗后的CSV数据文件（可选）。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "code_type": {
                "description": "代码类型，visualization: csv -> 图表; insight: 选择洞察添加到图表",
                "type": "string",
                "default": "visualization",
                "enum": ["visualization", "insight"],
            },
            "code": {
                "type": "string",
                "description": """用于data_visualization准备的Python代码。
## 可视化类型
1. 数据加载逻辑
2. CSV数据和图表描述生成
2.1 CSV数据（您想要可视化的数据，从原始数据清洗/转换，保存为.csv）
2.2 CSV数据的图表描述（图表标题或描述应简洁明了。示例："产品销售分布"，"月度收入趋势"。）
3. 将信息保存在json文件中。（格式：{"csvFilePath": string, "chartTitle": string}[]）
## 洞察类型
1. 从data_visualization结果中选择您想要添加到图表的洞察。
2. 将信息保存在json文件中。（格式：{"chartPath": string, "insights_id": number[]}[]）
# 注意
1. 您可以生成一个或多个具有不同可视化需求的csv数据。
2. 使每个图表数据简单、清晰且不同。
3. Json文件以utf-8编码保存，路径打印：print(json_path)
""",
            },
        },
        "required": ["code", "code_type"],
    } 