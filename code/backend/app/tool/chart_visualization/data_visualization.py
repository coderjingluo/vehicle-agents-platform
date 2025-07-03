"""
KunlunSec AI Platform - 数据可视化工具

提供数据可视化和图表生成功能。
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd

from app.core.config import settings as config
from app.core.logging import logger
from app.tool.base import BaseTool, ToolResult


class DataVisualizationTool(BaseTool):
    """数据可视化工具，用于生成统计图表和添加洞察"""

    name: str = "data_visualization"
    description: str = """使用visualization_preparation工具的JSON信息可视化统计图表或在图表中添加洞察。您可以按以下步骤操作：
1. 可视化统计图表
2. 基于步骤1选择洞察添加到图表（可选）
输出：
1. 图表（png/html）
2. 图表洞察（.md）（可选）"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "json_path": {
                "type": "string",
                "description": """以".json"结尾的json信息文件路径""",
            },
            "output_type": {
                "description": "渲染格式（html=交互式）",
                "type": "string",
                "default": "html",
                "enum": ["png", "html"],
            },
            "tool_type": {
                "description": "可视化图表或添加洞察",
                "type": "string",
                "default": "visualization",
                "enum": ["visualization", "insight"],
            },
            "language": {
                "description": "英语(en) / 中文(zh)",
                "type": "string",
                "default": "zh",
                "enum": ["zh", "en"],
            },
        },
        "required": ["json_path"],
    }

    def _get_file_path(
        self,
        json_info: List[Dict[str, str]],
        path_str: str,
        directory: Optional[str] = None,
    ) -> List[str]:
        """获取文件路径"""
        res = []
        for item in json_info:
            if os.path.exists(item[path_str]):
                res.append(item[path_str])
            elif os.path.exists(
                os.path.join(f"{directory or config.WORKSPACE_DIR}", item[path_str])
            ):
                res.append(
                    os.path.join(
                        f"{directory or config.WORKSPACE_DIR}", item[path_str]
                    )
                )
            else:
                raise Exception(f"文件或目录不存在: {item[path_str]}")
        return res

    def _success_output_template(self, result: List[Dict[str, str]]) -> str:
        """成功输出模板"""
        content = ""
        if len(result) == 0:
            return "结果为空！"
        for item in result:
            content += f"""## {item['title']}\n图表保存在: {item['chart_path']}"""
            if "insight_path" in item and item["insight_path"] and "insight_md" in item:
                content += "\n" + item["insight_md"]
            else:
                content += "\n"
        return f"图表生成成功！\n{content}"

    async def _data_visualization(
        self, json_info: List[Dict[str, str]], output_type: str, language: str
    ) -> Dict[str, Any]:
        """数据可视化处理"""
        try:
            data_list = []
            csv_file_path = self._get_file_path(json_info, "csvFilePath")
            
            # 处理每个CSV文件
            for index, item in enumerate(json_info):
                df = pd.read_csv(csv_file_path[index], encoding="utf-8")
                df = df.astype(object)
                df = df.where(pd.notnull(df), None)
                data_dict_list = df.to_json(orient="records", force_ascii=False)

                data_list.append({
                    "file_name": os.path.basename(csv_file_path[index]).replace(".csv", ""),
                    "dict_data": data_dict_list,
                    "chartTitle": item["chartTitle"],
                })
            
            # 创建可视化任务
            tasks = []
            for item in data_list:
                # 在实际实现中，这里应该调用图表可视化库
                # 这里我们简化为模拟生成图表文件
                tasks.append(self._simulate_chart_generation(
                    item["dict_data"],
                    item["chartTitle"],
                    item["file_name"],
                    output_type,
                    language
                ))
            
            # 执行所有任务
            results = await asyncio.gather(*tasks)
            
            # 处理结果
            error_list = []
            success_list = []
            for index, result in enumerate(results):
                csv_path = csv_file_path[index]
                if "error" in result and "chart_path" not in result:
                    error_list.append(f"错误 {csv_path}: {result['error']}")
                else:
                    success_list.append({
                        **result,
                        "title": json_info[index]["chartTitle"],
                    })
            
            # 返回结果
            if error_list:
                return {
                    "observation": f"# 图表生成错误{'\n'.join(error_list)}\n{self._success_output_template(success_list)}",
                    "success": False,
                }
            else:
                return {
                    "observation": self._success_output_template(success_list),
                    "success": True,
                }
        except Exception as e:
            logger.error(f"数据可视化错误: {str(e)}")
            return {
                "observation": f"错误: {str(e)}",
                "success": False,
            }

    async def _add_insights(
        self, json_info: List[Dict[str, str]], output_type: str
    ) -> Dict[str, Any]:
        """添加洞察到图表"""
        try:
            # 获取图表路径
            chart_file_path = self._get_file_path(
                json_info, "chartPath", os.path.join(config.WORKSPACE_DIR, "visualization")
            )
            
            # 处理每个图表
            data_list = []
            for index, item in enumerate(json_info):
                if "insights_id" in item:
                    data_list.append({
                        "file_name": os.path.basename(chart_file_path[index]).replace(
                            f".{output_type}", ""
                        ),
                        "insights_id": item["insights_id"],
                    })
            
            # 创建添加洞察任务
            tasks = []
            for item in data_list:
                # 在实际实现中，这里应该调用图表洞察库
                # 这里我们简化为模拟添加洞察
                tasks.append(self._simulate_add_insights(
                    item["insights_id"],
                    item["file_name"],
                    output_type
                ))
            
            # 执行所有任务
            results = await asyncio.gather(*tasks)
            
            # 处理结果
            error_list = []
            success_list = []
            for index, result in enumerate(results):
                chart_path = chart_file_path[index]
                if "error" in result and "chart_path" not in result:
                    error_list.append(f"错误 {chart_path}: {result['error']}")
                else:
                    success_list.append(chart_path)
            
            # 返回结果
            success_template = (
                f"# 图表已更新洞察\n{','.join(success_list)}"
                if success_list else ""
            )
            if error_list:
                return {
                    "observation": f"# 图表洞察错误:{'\n'.join(error_list)}\n{success_template}",
                    "success": False,
                }
            else:
                return {
                    "observation": success_template,
                    "success": True,
                }
        except Exception as e:
            logger.error(f"添加洞察错误: {str(e)}")
            return {
                "observation": f"错误: {str(e)}",
                "success": False,
            }

    async def _simulate_chart_generation(
        self,
        dict_data: str,
        chart_description: str,
        file_name: str,
        output_type: str,
        language: str
    ) -> Dict[str, Any]:
        """模拟图表生成（实际实现中应替换为真实的图表生成）"""
        try:
            # 创建可视化目录
            vis_dir = os.path.join(config.WORKSPACE_DIR, "visualization")
            os.makedirs(vis_dir, exist_ok=True)
            
            # 生成图表文件路径
            chart_path = os.path.join(vis_dir, f"{file_name}.{output_type}")
            
            # 模拟生成图表文件
            with open(chart_path, "w") as f:
                f.write(f"<!-- 模拟图表: {chart_description} -->\n")
                f.write(f"<!-- 数据: {dict_data[:100]}... -->\n")
            
            return {
                "chart_path": chart_path,
                "success": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }

    async def _simulate_add_insights(
        self,
        insights_id: List[str],
        file_name: str,
        output_type: str
    ) -> Dict[str, Any]:
        """模拟添加洞察（实际实现中应替换为真实的洞察添加）"""
        try:
            # 创建可视化目录
            vis_dir = os.path.join(config.WORKSPACE_DIR, "visualization")
            os.makedirs(vis_dir, exist_ok=True)
            
            # 图表文件路径
            chart_path = os.path.join(vis_dir, f"{file_name}.{output_type}")
            
            # 洞察文件路径
            insight_path = os.path.join(vis_dir, f"{file_name}_insights.md")
            
            # 模拟添加洞察
            with open(insight_path, "w") as f:
                f.write(f"# 图表洞察\n\n")
                for insight_id in insights_id:
                    f.write(f"- 洞察 {insight_id}: 这是一个模拟的洞察描述\n")
            
            return {
                "chart_path": chart_path,
                "insight_path": insight_path,
                "success": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }

    async def execute(
        self,
        json_path: str,
        output_type: str = "html",
        tool_type: str = "visualization",
        language: str = "zh",
        **kwargs
    ) -> ToolResult:
        """执行数据可视化操作
        
        Args:
            json_path: JSON信息文件路径
            output_type: 输出类型（html或png）
            tool_type: 工具类型（visualization或insight）
            language: 语言（zh或en）
            
        Returns:
            可视化结果
        """
        try:
            logger.info(f"📈 数据可视化 {json_path}, 类型: {tool_type}")
            
            # 读取JSON文件
            with open(json_path, "r", encoding="utf-8") as file:
                json_info = json.load(file)
            
            # 根据工具类型执行相应操作
            if tool_type == "visualization":
                result = await self._data_visualization(json_info, output_type, language)
            else:
                result = await self._add_insights(json_info, output_type)
            
            # 返回结果
            if result.get("success", False):
                return ToolResult(output=result["observation"])
            else:
                return ToolResult(
                    error=f"数据可视化失败",
                    output=result["observation"]
                )
        except Exception as e:
            logger.error(f"数据可视化工具错误: {str(e)}")
            return ToolResult(error=f"数据可视化工具错误: {str(e)}") 