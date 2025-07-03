"""
KunlunSec AI Platform - 报告分析智能体模块

实现基于测试结果生成分析报告的智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent, ToolCollection
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.terminate import TerminateTool
from app.tool.planning import PlanningTool
from app.tool.file_operators import FileOperatorTool
from app.tool.rag_query import RAGQueryTool
from app.tool.report_generator import ReportGeneratorTool
from app.tool.chart_visualization import DataVisualizationTool

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

class ReportAnalysisAgent(ToolCallAgent):
    """测试报告分析智能体"""
    
    name: str = "ReportAnalysis"
    description: str = "基于测试结果生成分析报告的专业智能体"
    
    system_prompt: str = REPORT_ANALYSIS_SYSTEM_PROMPT
    next_step_prompt: str = REPORT_ANALYSIS_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletionTool(),
        TerminateTool(),
        PlanningTool(),
        
        # 专业工具
        ReportGeneratorTool(),
        DataVisualizationTool(),
        FileOperatorTool(),
        RAGQueryTool(),
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
    
    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """为报告分析任务创建详细的执行计划
        
        Args:
            task: 报告分析任务描述
            
        Returns:
            Dict[str, Any]: 生成的执行计划
        """
        from app.core.logging import logger
        
        # 获取可用工具列表
        available_tools = self._get_tools_description()
        
        # 构建报告分析专用规划提示
        report_planning_prompt = f"""
        请为以下车联网安全报告分析任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 可用工具列表
        以下是你可以在执行计划中使用的工具:
        {available_tools}
        
        # 报告分析需求
        报告分析是车联网安全评估的总结环节，需要完成以下步骤:
        1. 收集测试结果和数据
        2. 数据清洗与整理
        3. 数据分析与统计
        4. 安全漏洞分类与评级
        5. 生成数据可视化图表
        6. 撰写发现总结
        7. 提出安全建议
        8. 生成最终报告
        
        # 规划格式
        请提供JSON格式的执行计划，包含以下内容:
        
        ```json
        {{
            "main_task": "报告分析任务描述",
            "subtasks": [
                {{
                    "id": "subtask-1",
                    "name": "子任务名称 (例如：测试结果收集)",
                    "description": "详细描述",
                    "steps": [
                        {{
                            "id": "step-1.1",
                            "description": "步骤描述",
                            "tools": ["可能需要使用的工具名称"],
                            "expected_output": "期望输出描述"
                        }},
                        // 更多步骤...
                    ],
                    "dependencies": []  // 依赖的其他子任务ID
                }},
                // 所有报告分析必要的子任务...
            ]
        }}
        ```
        
        请确保规划涵盖完整的报告分析流程，每个子任务和步骤都清晰可执行，且符合车联网安全报告的专业要求。
        重要：每个步骤中指定的工具必须从上面提供的"可用工具列表"中选择，不要使用列表之外的工具。
        """
        
        logger.info(f"正在为报告分析任务制定执行计划: {task[:50]}...")
        
        try:
            # 向LLM发送规划请求
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": "你是车联网安全报告分析专家，擅长设计结构化的分析报告计划。"},
                    {"role": "user", "content": report_planning_prompt}
                ],
                temperature=0.2  # 使用较低的温度以获得更确定性的规划
            )
            
            # 提取JSON部分
            import re
            import json
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response
            
            try:
                # 解析JSON计划
                plan = json.loads(json_str)
                logger.info(f"成功生成报告分析执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                
                # 验证计划是否包含关键报告分析步骤
                subtask_names = [st.get('name', '').lower() for st in plan.get('subtasks', [])]
                expected_keywords = ['测试结果', '分类', '风险', '可视化', '报告']
                
                missing_keywords = [kw for kw in expected_keywords if not any(kw in name for name in subtask_names)]
                if missing_keywords:
                    logger.warning(f"生成的报告分析计划缺少关键步骤: {', '.join(missing_keywords)}")
                    
                    # 添加缺失的关键步骤
                    for kw in missing_keywords:
                        if kw == '测试结果':
                            plan['subtasks'].insert(0, {
                                "id": f"subtask-results-{len(plan['subtasks'])+1}",
                                "name": "测试结果分析",
                                "description": "分析测试结果数据，提取关键信息",
                                "steps": [
                                    {
                                        "id": f"step-results-1",
                                        "description": "读取测试结果数据",
                                        "tools": ["create_chat_completion", "file_operator"],
                                        "expected_output": "结构化测试结果数据"
                                    },
                                    {
                                        "id": f"step-results-2",
                                        "description": "提取测试统计信息",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "测试统计摘要"
                                    }
                                ],
                                "dependencies": []
                            })
                        elif kw == '分类':
                            plan['subtasks'].append({
                                "id": f"subtask-category-{len(plan['subtasks'])+1}",
                                "name": "问题分类与评估",
                                "description": "识别并分类安全问题，评估严重程度",
                                "steps": [
                                    {
                                        "id": f"step-category-1",
                                        "description": "识别安全问题",
                                        "tools": ["create_chat_completion", "rag_query"],
                                        "expected_output": "安全问题列表"
                                    },
                                    {
                                        "id": f"step-category-2",
                                        "description": "分类安全问题",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "问题分类结果"
                                    },
                                    {
                                        "id": f"step-category-3",
                                        "description": "评估问题严重程度",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "问题严重程度评估"
                                    }
                                ],
                                "dependencies": ["subtask-results-1"]
                            })
                        elif kw == '风险':
                            plan['subtasks'].append({
                                "id": f"subtask-risk-{len(plan['subtasks'])+1}",
                                "name": "风险分析",
                                "description": "生成风险矩阵与风险评分",
                                "steps": [
                                    {
                                        "id": f"step-risk-1",
                                        "description": "构建风险矩阵",
                                        "tools": ["create_chat_completion", "report_generator"],
                                        "expected_output": "风险矩阵"
                                    },
                                    {
                                        "id": f"step-risk-2",
                                        "description": "计算风险评分",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "风险评分"
                                    },
                                    {
                                        "id": f"step-risk-3",
                                        "description": "提出风险缓解建议",
                                        "tools": ["create_chat_completion", "rag_query"],
                                        "expected_output": "风险缓解建议"
                                    }
                                ],
                                "dependencies": ["subtask-category-1"]
                            })
                        elif kw == '可视化':
                            plan['subtasks'].append({
                                "id": f"subtask-visual-{len(plan['subtasks'])+1}",
                                "name": "数据可视化",
                                "description": "创建报告数据可视化",
                                "steps": [
                                    {
                                        "id": f"step-visual-1",
                                        "description": "准备可视化数据",
                                        "tools": ["create_chat_completion", "data_visualization"],
                                        "expected_output": "格式化可视化数据"
                                    },
                                    {
                                        "id": f"step-visual-2",
                                        "description": "生成图表",
                                        "tools": ["data_visualization"],
                                        "expected_output": "报告图表"
                                    }
                                ],
                                "dependencies": ["subtask-risk-1"]
                            })
                        elif kw == '报告':
                            plan['subtasks'].append({
                                "id": f"subtask-report-{len(plan['subtasks'])+1}",
                                "name": "综合报告生成",
                                "description": "生成最终安全分析报告",
                                "steps": [
                                    {
                                        "id": f"step-report-1",
                                        "description": "整合分析结果",
                                        "tools": ["create_chat_completion", "report_generator"],
                                        "expected_output": "整合分析数据"
                                    },
                                    {
                                        "id": f"step-report-2",
                                        "description": "生成报告草稿",
                                        "tools": ["report_generator"],
                                        "expected_output": "报告草稿"
                                    },
                                    {
                                        "id": f"step-report-3",
                                        "description": "审核并优化报告",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "最终报告"
                                    }
                                ],
                                "dependencies": ["subtask-visual-1", "subtask-risk-1"]
                            })
                
                # 保存计划到智能体
                self.current_plan = plan
                self.subtasks = plan.get('subtasks', [])
                
                # 将规划添加到记忆中
                self.update_memory(
                    "system",
                    f"已生成报告分析执行计划，包含 {len(self.subtasks)} 个子任务。"
                )
                
                return plan
            except json.JSONDecodeError as e:
                logger.error(f"解析报告分析执行计划失败: {str(e)}")
                return await super().generate_plan(task)
                
        except Exception as e:
            logger.error(f"生成报告分析执行计划时出错: {str(e)}")
            return await super().generate_plan(task)
    
    def _get_tools_description(self) -> str:
        """获取可用工具的描述列表
        
        Returns:
            str: 格式化的工具描述列表
        """
        tool_descriptions = []
        for tool in self.available_tools.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
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
        """基于分析数据生成报告
        
        Args:
            analysis_data: 分析数据，包括问题、风险矩阵等
            
        Returns:
            str: 生成的报告内容
        """
        # 使用报告生成工具
        report_generator = self.available_tools.get_tool("report_generator")
        if not report_generator:
            return "报告生成工具不可用"
        
        # 默认使用标准模板
        template = "standard"
        if "detailed" in analysis_data.get("options", {}):
            template = "detailed"
        elif "executive" in analysis_data.get("options", {}):
            template = "executive"
        
        # 生成报告
        result = await report_generator.execute(
            analysis_data=analysis_data,
            template=template
        )
        
        if hasattr(result, "output"):
            return result.output
        
        return "报告生成失败"
    
    async def visualize_data(self, data: Dict[str, Any], chart_type: str = "bar") -> Dict[str, Any]:
        """生成数据可视化
        
        Args:
            data: 要可视化的数据
            chart_type: 图表类型（bar, pie, line等）
            
        Returns:
            Dict[str, Any]: 可视化结果
        """
        # 使用数据可视化工具
        data_vis_tool = self.available_tools.get_tool("chart_visualization")
        if not data_vis_tool:
            return {"error": "数据可视化工具不可用"}
        
        # 生成可视化
        result = await data_vis_tool.execute(
            data=data,
            chart_type=chart_type
        )
        
        if hasattr(result, "output"):
            return result.output
        
        return {"error": "数据可视化失败"}

