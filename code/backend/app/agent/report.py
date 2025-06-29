"""
KunlunSec AI Platform - 报告分析智能体模块

实现基于测试结果生成分析报告的智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent, ToolCollection, Tool
from app.agent.toolcall import CreateChatCompletion, Terminate

# 报告分析系统提示
REPORT_ANALYSIS_SYSTEM_PROMPT = """你是一个专门分析车联网安全测试结果并生成报告的AI助手。
你的任务是分析测试结果，识别问题，分类风险，并生成综合分析报告。
你可以使用以下工具:
{tools_description}

请确保报告内容全面、准确，并提供有价值的安全建议。
"""

REPORT_ANALYSIS_NEXT_STEP_PROMPT = """请根据当前状态，决定下一步行动。
你可以执行以下操作:
1. 分析测试结果
2. 识别和分类问题
3. 生成风险矩阵
4. 生成综合报告
5. 使用工具辅助分析
"""

# 报告分析专用工具
class ReportGeneratorTool(Tool):
    """报告生成工具"""
    name: str = "report_generator"
    description: str = "生成分析报告"
    
    async def run(self, analysis_data: Dict[str, Any], template: str = "standard", **kwargs) -> str:
        """生成报告"""
        # 实际实现将基于分析数据生成报告
        issues = analysis_data.get("issues", [])
        issue_count = len(issues)
        
        report = f"""
# 车联网安全测试分析报告

## 摘要
- 测试项目: {analysis_data.get('project_name', '未指定项目')}
- 测试日期: {analysis_data.get('test_date', '未指定日期')}
- 测试结果: 发现 {issue_count} 个安全问题

## 问题分析
"""
        
        if issues:
            for i, issue in enumerate(issues):
                report += f"""
### 问题 {i+1}: {issue.get('name', '未命名问题')}
- 严重程度: {issue.get('severity', '未知')}
- 描述: {issue.get('description', '无描述')}
- 影响: {issue.get('impact', '未知影响')}
- 建议修复措施: {issue.get('remediation', '无建议')}
"""
        else:
            report += "未发现安全问题。\n"
            
        report += """
## 风险评估
(风险矩阵数据将在此显示)

## 结论与建议
(基于分析结果的结论和建议将在此显示)
"""
        
        return report

class DataVisualizationTool(Tool):
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

class ReportAnalysisAgent(ToolCallAgent):
    """测试报告分析智能体"""
    
    name: str = "ReportAnalysis"
    description: str = "基于测试结果生成分析报告的专业智能体"
    
    system_prompt: str = REPORT_ANALYSIS_SYSTEM_PROMPT
    next_step_prompt: str = REPORT_ANALYSIS_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletion(),
        Terminate(),
        PlanningTool(),
        
        # 专业工具
        ReportGeneratorTool(),
        DataVisualizationTool(),
        FileOperatorTool(),
        RagQueryTool(),
    ))
    
    # 报告分析特定属性
    report_templates: Dict[str, str] = Field(default_factory=dict)
    issue_categories: Dict[str, List[str]] = Field(default_factory=dict)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "ReportAnalysisAgent":
        """创建并初始化报告分析智能体"""
        instance = cls(**kwargs)
        await instance.initialize_templates()
        await instance.initialize_categories()
        return instance
    
    async def initialize_templates(self):
        """初始化报告模板"""
        # 示例报告模板
        self.report_templates = {
            "standard": """
# 车联网安全测试分析报告

## 摘要
- 测试项目: {project_name}
- 测试日期: {test_date}
- 测试结果: 发现 {issue_count} 个安全问题

## 问题分析
{issues_analysis}

## 风险评估
{risk_matrix}

## 结论与建议
{conclusions}
            """,
            
            "executive": """
# 车联网安全测试分析报告 - 管理层摘要

## 关键发现
{key_findings}

## 风险概览
{risk_overview}

## 建议行动
{recommended_actions}

## 时间线
{timeline}
            """,
            
            "detailed": """
# 车联网安全测试详细分析报告

## 摘要
- 测试项目: {project_name}
- 测试日期: {test_date}
- 测试环境: {test_environment}
- 测试结果: 发现 {issue_count} 个安全问题

## 测试范围
{test_scope}

## 方法论
{methodology}

## 详细问题分析
{detailed_issues}

## 风险评估
{risk_matrix}

## 技术建议
{technical_recommendations}

## 附录
{appendix}
            """
        }
    
    async def initialize_categories(self):
        """初始化问题分类"""
        # 示例问题分类
        self.issue_categories = {
            "authentication": [
                "弱密码",
                "缺少多因素认证",
                "会话固定",
                "凭证泄露"
            ],
            "authorization": [
                "权限提升",
                "未授权访问",
                "越权操作",
                "访问控制不当"
            ],
            "data_security": [
                "敏感数据泄露",
                "数据加密不足",
                "不安全的数据传输",
                "不安全的数据存储"
            ],
            "network_security": [
                "开放端口",
                "不安全的网络协议",
                "中间人攻击",
                "网络嗅探"
            ],
            "code_security": [
                "注入漏洞",
                "跨站脚本",
                "不安全的反序列化",
                "逻辑漏洞"
            ]
        }
    
    # 报告分析特定方法
    async def analyze_test_results(self, test_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果，识别问题"""
        issues = []
        
        for test_id, result in test_results.items():
            # 检查测试是否通过
            if result.get("status") == "failed" or not result.get("passed", False):
                # 提取测试输出
                output = result.get("output", "")
                
                # 分析输出识别问题
                issue = self._identify_issue_from_output(test_id, output)
                if issue:
                    issues.append(issue)
        
        # 整理分析结果
        analysis = {
            "total_tests": len(test_results),
            "passed_tests": sum(1 for r in test_results.values() if r.get("passed", False)),
            "failed_tests": sum(1 for r in test_results.values() if not r.get("passed", False)),
            "issues": issues
        }
        
        return analysis
    
    def _identify_issue_from_output(self, test_id: str, output: str) -> Optional[Dict[str, Any]]:
        """从测试输出中识别问题"""
        # 实际实现将使用更复杂的分析逻辑
        if not output:
            return None
            
        # 简单示例实现
        if "error" in output.lower():
            return {
                "id": f"ISSUE_{test_id}",
                "name": "测试失败",
                "description": f"测试 {test_id} 执行失败",
                "severity": "中",
                "output": output
            }
        elif "warning" in output.lower():
            return {
                "id": f"ISSUE_{test_id}",
                "name": "测试警告",
                "description": f"测试 {test_id} 产生警告",
                "severity": "低",
                "output": output
            }
        elif "vulnerability" in output.lower() or "漏洞" in output:
            return {
                "id": f"ISSUE_{test_id}",
                "name": "安全漏洞",
                "description": f"测试 {test_id} 发现安全漏洞",
                "severity": "高",
                "output": output
            }
            
        return None
    
    async def categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """对问题进行分类"""
        categorized = {category: [] for category in self.issue_categories.keys()}
        uncategorized = []
        
        for issue in issues:
            # 获取问题描述
            description = issue.get("description", "").lower()
            
            # 尝试分类
            categorized_flag = False
            for category, keywords in self.issue_categories.items():
                for keyword in keywords:
                    if keyword.lower() in description:
                        categorized[category].append(issue)
                        categorized_flag = True
                        break
                if categorized_flag:
                    break
            
            # 如果无法分类，放入未分类列表
            if not categorized_flag:
                uncategorized.append(issue)
        
        # 添加未分类的问题
        if uncategorized:
            categorized["uncategorized"] = uncategorized
        
        return categorized
    
    async def generate_risk_matrix(self, issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成风险矩阵"""
        # 初始化风险矩阵
        risk_matrix = {
            "high": {"high": 0, "medium": 0, "low": 0},
            "medium": {"high": 0, "medium": 0, "low": 0},
            "low": {"high": 0, "medium": 0, "low": 0}
        }
        
        # 严重程度映射
        severity_map = {
            "高": "high",
            "中": "medium",
            "低": "low"
        }
        
        # 计算风险分布
        for category, category_issues in issues.items():
            for issue in category_issues:
                # 获取严重程度
                severity = issue.get("severity", "中")
                severity_en = severity_map.get(severity, "medium")
                
                # 根据问题类别确定影响
                impact = self._determine_impact(category)
                
                # 更新风险矩阵
                risk_matrix[impact][severity_en] += 1
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(risk_matrix)
        
        return {
            "matrix": risk_matrix,
            "score": risk_score,
            "categories": list(issues.keys())
        }
    
    def _determine_impact(self, category: str) -> str:
        """根据问题类别确定影响"""
        # 高影响类别
        if category in ["authentication", "data_security"]:
            return "high"
        # 中等影响类别
        elif category in ["authorization", "network_security"]:
            return "medium"
        # 低影响类别
        else:
            return "low"
    
    def _calculate_risk_score(self, risk_matrix: Dict[str, Dict[str, int]]) -> float:
        """计算风险分数"""
        # 风险权重
        weights = {
            "high": {"high": 9, "medium": 6, "low": 3},
            "medium": {"high": 6, "medium": 4, "low": 2},
            "low": {"high": 3, "medium": 2, "low": 1}
        }
        
        # 计算加权总分
        score = 0
        count = 0
        
        for impact, severities in risk_matrix.items():
            for severity, num in severities.items():
                score += weights[impact][severity] * num
                count += num
        
        # 返回平均风险分数
        return score / max(count, 1)
    
    async def generate_report(self, analysis_data: Dict[str, Any]) -> str:
        """生成综合分析报告"""
        # 使用报告生成工具
        report_tool = self.available_tools.get_tool("report_generator")
        if not report_tool:
            return "报告生成工具不可用"
        
        # 选择合适的模板
        template = "standard"
        if analysis_data.get("detailed", False):
            template = "detailed"
        elif analysis_data.get("executive", False):
            template = "executive"
        
        # 生成报告
        report = await report_tool.run(
            analysis_data=analysis_data,
            template=template
        )
        
        return report

# 导入循环依赖
from app.agent.tara import PlanningTool, RagQueryTool, FileOperatorTool 