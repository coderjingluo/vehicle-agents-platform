import logging
import time
from typing import Dict, List, Optional, Any

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ReportGeneratorTool(BaseTool):
    """报告生成工具"""
    
    name: str = "report_generator"
    description: str = "基于测试结果生成分析报告"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["analyze_results", "categorize_issues", "generate_risk_matrix", "generate_report"],
                "description": "要执行的报告操作"
            },
            "test_results": {
                "type": "object",
                "description": "测试结果数据"
            },
            "issues": {
                "type": "array",
                "description": "问题列表，用于分类或生成风险矩阵"
            },
            "analysis_data": {
                "type": "object",
                "description": "分析数据，用于生成最终报告"
            },
            "report_format": {
                "type": "string",
                "enum": ["markdown", "html", "pdf"],
                "description": "报告格式"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, test_results: Optional[dict] = None,
                     issues: Optional[list] = None, analysis_data: Optional[dict] = None,
                     report_format: str = "markdown", **kwargs) -> ToolResult:
        """执行报告相关操作"""
        try:
            if operation == "analyze_results":
                return await self._analyze_results(test_results)
            elif operation == "categorize_issues":
                return await self._categorize_issues(issues)
            elif operation == "generate_risk_matrix":
                return await self._generate_risk_matrix(issues)
            elif operation == "generate_report":
                return await self._generate_report(analysis_data, report_format)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            logger.error(f"报告生成操作失败: {str(e)}")
            return ToolResult(error=f"报告生成操作失败: {str(e)}")
    
    async def _analyze_results(self, test_results: Optional[dict]) -> ToolResult:
        """分析测试结果"""
        if not test_results:
            return ToolResult(error="分析测试结果需要提供test_results")
            
        # 这里是一个简化的实现，实际应该对测试结果进行深入分析
        logger.info("分析测试结果...")
        
        # 提取测试详情
        details = test_results.get("results", {}).get("details", [])
        
        # 分析通过/失败的测试
        passed_tests = [test for test in details if test.get("result") == "passed"]
        failed_tests = [test for test in details if test.get("result") == "failed"]
        
        # 识别问题
        issues = []
        for i, test in enumerate(failed_tests):
            issues.append({
                "id": f"ISSUE-{i+1:03d}",
                "name": f"测试失败: {test.get('name', '未知测试')}",
                "description": test.get("error_message", "测试未通过，未提供错误详情"),
                "severity": "高",
                "category": "功能缺陷"
            })
        
        # 生成分析结果
        analysis = {
            "summary": {
                "total_tests": len(details),
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "pass_rate": len(passed_tests) / len(details) if details else 0,
                "average_duration": sum(test.get("duration", 0) for test in details) / len(details) if details else 0
            },
            "issues": issues,
            "analysis_time": time.time()
        }
        
        return ToolResult(output=analysis)
    
    async def _categorize_issues(self, issues: Optional[list]) -> ToolResult:
        """对问题进行分类"""
        if not issues:
            return ToolResult(error="分类问题需要提供issues")
            
        # 这里是一个简化的实现，实际应该使用更复杂的分类算法
        logger.info("对问题进行分类...")
        
        # 定义分类
        categories = {
            "security": [],  # 安全问题
            "functional": [],  # 功能问题
            "performance": [],  # 性能问题
            "usability": [],  # 可用性问题
            "compatibility": []  # 兼容性问题
        }
        
        # 对问题进行分类
        for issue in issues:
            # 根据问题描述进行简单分类
            description = issue.get("description", "").lower()
            
            if any(kw in description for kw in ["安全", "漏洞", "注入", "越权", "认证"]):
                category = "security"
            elif any(kw in description for kw in ["性能", "速度", "响应时间", "延迟"]):
                category = "performance"
            elif any(kw in description for kw in ["界面", "用户体验", "易用性"]):
                category = "usability"
            elif any(kw in description for kw in ["兼容", "浏览器", "平台"]):
                category = "compatibility"
            else:
                category = "functional"
                
            # 添加分类信息
            issue["category"] = category
            categories[category].append(issue)
        
        # 生成分类结果
        categorized_issues = {
            "categories": {
                "security": {
                    "name": "安全问题",
                    "count": len(categories["security"]),
                    "issues": categories["security"]
                },
                "functional": {
                    "name": "功能问题",
                    "count": len(categories["functional"]),
                    "issues": categories["functional"]
                },
                "performance": {
                    "name": "性能问题",
                    "count": len(categories["performance"]),
                    "issues": categories["performance"]
                },
                "usability": {
                    "name": "可用性问题",
                    "count": len(categories["usability"]),
                    "issues": categories["usability"]
                },
                "compatibility": {
                    "name": "兼容性问题",
                    "count": len(categories["compatibility"]),
                    "issues": categories["compatibility"]
                }
            },
            "all_issues": issues,
            "categorization_time": time.time()
        }
        
        return ToolResult(output=categorized_issues)
    
    async def _generate_risk_matrix(self, issues: Optional[list]) -> ToolResult:
        """生成风险矩阵"""
        if not issues:
            return ToolResult(error="生成风险矩阵需要提供issues")
            
        # 这里是一个简化的实现，实际应该使用更复杂的风险评估算法
        logger.info("生成风险矩阵...")
        
        # 风险矩阵定义
        matrix = {
            "high_impact": {
                "high_likelihood": [],  # 高影响力，高可能性
                "medium_likelihood": [],  # 高影响力，中可能性
                "low_likelihood": []  # 高影响力，低可能性
            },
            "medium_impact": {
                "high_likelihood": [],  # 中影响力，高可能性
                "medium_likelihood": [],  # 中影响力，中可能性
                "low_likelihood": []  # 中影响力，低可能性
            },
            "low_impact": {
                "high_likelihood": [],  # 低影响力，高可能性
                "medium_likelihood": [],  # 低影响力，中可能性
                "low_likelihood": []  # 低影响力，低可能性
            }
        }
        
        # 评估每个问题的影响力和可能性
        for issue in issues:
            # 根据问题严重性评估影响力
            severity = issue.get("severity", "中").lower()
            if severity in ["高", "严重"]:
                impact = "high_impact"
            elif severity in ["中", "一般"]:
                impact = "medium_impact"
            else:
                impact = "low_impact"
                
            # 简单地根据问题类别评估可能性
            category = issue.get("category", "").lower()
            if category in ["security", "functional"]:
                likelihood = "high_likelihood"
            elif category in ["performance"]:
                likelihood = "medium_likelihood"
            else:
                likelihood = "low_likelihood"
                
            # 将问题添加到相应的矩阵单元格
            matrix[impact][likelihood].append(issue)
            
            # 更新问题的风险评估
            issue["impact"] = impact.split("_")[0]
            issue["likelihood"] = likelihood.split("_")[0]
            issue["risk_level"] = self._calculate_risk_level(impact, likelihood)
        
        # 生成风险矩阵结果
        risk_matrix = {
            "matrix": matrix,
            "high_risk_issues": [issue for issue in issues if issue.get("risk_level") == "high"],
            "medium_risk_issues": [issue for issue in issues if issue.get("risk_level") == "medium"],
            "low_risk_issues": [issue for issue in issues if issue.get("risk_level") == "low"],
            "all_issues": issues,
            "generation_time": time.time()
        }
        
        return ToolResult(output=risk_matrix)
    
    def _calculate_risk_level(self, impact: str, likelihood: str) -> str:
        """计算风险等级"""
        # 风险等级矩阵
        risk_matrix = {
            "high_impact": {
                "high_likelihood": "high",
                "medium_likelihood": "high",
                "low_likelihood": "medium"
            },
            "medium_impact": {
                "high_likelihood": "high",
                "medium_likelihood": "medium",
                "low_likelihood": "low"
            },
            "low_impact": {
                "high_likelihood": "medium",
                "medium_likelihood": "low",
                "low_likelihood": "low"
            }
        }
        
        return risk_matrix.get(impact, {}).get(likelihood, "medium")
    
    async def _generate_report(self, analysis_data: Optional[dict], report_format: str) -> ToolResult:
        """生成最终报告"""
        if not analysis_data:
            return ToolResult(error="生成报告需要提供analysis_data")
            
        # 这里是一个简化的实现，实际应该根据分析数据生成格式化报告
        logger.info(f"生成{report_format}格式报告...")
        
        # 根据不同格式生成报告
        if report_format == "markdown":
            report_content = self._generate_markdown_report(analysis_data)
        elif report_format == "html":
            report_content = self._generate_html_report(analysis_data)
        elif report_format == "pdf":
            report_content = "PDF报告生成功能尚未实现"
        else:
            return ToolResult(error=f"不支持的报告格式: {report_format}")
        
        return ToolResult(output={
            "report_format": report_format,
            "report_content": report_content,
            "generation_time": time.time()
        })
    
    def _generate_markdown_report(self, analysis_data: dict) -> str:
        """生成Markdown格式的报告"""
        # 提取报告所需数据
        summary = analysis_data.get("summary", {})
        issues = analysis_data.get("issues", [])
        categorized_issues = analysis_data.get("categories", {})
        risk_matrix = analysis_data.get("matrix", {})
        
        # 生成报告内容
        report = [
            "# 测试报告\n",
            f"## 摘要\n",
            f"- 总测试数: {summary.get('total_tests', 0)}\n",
            f"- 通过测试数: {summary.get('passed_tests', 0)}\n",
            f"- 失败测试数: {summary.get('failed_tests', 0)}\n",
            f"- 通过率: {summary.get('pass_rate', 0):.2%}\n",
            f"- 平均执行时间: {summary.get('average_duration', 0):.2f}秒\n\n",
            
            f"## 问题分类\n"
        ]
        
        # 添加问题分类
        for category_name, category_data in categorized_issues.items():
            report.append(f"### {category_data.get('name', category_name)}\n")
            report.append(f"问题数量: {category_data.get('count', 0)}\n\n")
            
            # 添加该分类下的问题
            for issue in category_data.get("issues", []):
                report.append(f"- **{issue.get('name', '未命名问题')}** (ID: {issue.get('id', 'N/A')}, 严重性: {issue.get('severity', '未知')})\n")
                report.append(f"  {issue.get('description', '无描述')}\n\n")
        
        # 添加风险矩阵
        report.append(f"## 风险矩阵\n\n")
        report.append("| 影响力/可能性 | 高可能性 | 中可能性 | 低可能性 |\n")
        report.append("|------------|--------|--------|--------|\n")
        
        # 高影响力行
        high_impact = risk_matrix.get("high_impact", {})
        report.append("| **高影响力** | ")
        report.append(f"{len(high_impact.get('high_likelihood', []))}个问题 | ")
        report.append(f"{len(high_impact.get('medium_likelihood', []))}个问题 | ")
        report.append(f"{len(high_impact.get('low_likelihood', []))}个问题 |\n")
        
        # 中影响力行
        medium_impact = risk_matrix.get("medium_impact", {})
        report.append("| **中影响力** | ")
        report.append(f"{len(medium_impact.get('high_likelihood', []))}个问题 | ")
        report.append(f"{len(medium_impact.get('medium_likelihood', []))}个问题 | ")
        report.append(f"{len(medium_impact.get('low_likelihood', []))}个问题 |\n")
        
        # 低影响力行
        low_impact = risk_matrix.get("low_impact", {})
        report.append("| **低影响力** | ")
        report.append(f"{len(low_impact.get('high_likelihood', []))}个问题 | ")
        report.append(f"{len(low_impact.get('medium_likelihood', []))}个问题 | ")
        report.append(f"{len(low_impact.get('low_likelihood', []))}个问题 |\n\n")
        
        # 添加详细问题列表
        report.append("## 详细问题列表\n\n")
        for i, issue in enumerate(issues):
            report.append(f"### {i+1}. {issue.get('name', '未命名问题')} (ID: {issue.get('id', 'N/A')})\n\n")
            report.append(f"- **严重性**: {issue.get('severity', '未知')}\n")
            report.append(f"- **分类**: {issue.get('category', '未分类')}\n")
            report.append(f"- **风险等级**: {issue.get('risk_level', '未评估')}\n")
            report.append(f"- **描述**: {issue.get('description', '无描述')}\n\n")
        
        return "".join(report)
    
    def _generate_html_report(self, analysis_data: dict) -> str:
        """生成HTML格式的报告"""
        # 这里应该生成HTML格式的报告
        # 为了简化，返回一个基本的HTML结构
        return "<html><body><h1>测试报告</h1><p>HTML格式报告生成功能尚未完全实现</p></body></html>" 