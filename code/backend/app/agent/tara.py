"""
KunlunSec AI Platform - TARA分析智能体模块

实现威胁分析与风险评估智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, model_validator
from datetime import datetime

from app.agent.toolcall import ToolCallAgent, ToolCollection, ToolCall
from app.tool.base import BaseTool, ToolResult
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.ask_human import AskHumanTool
from app.tool.python_execute import PythonExecuteTool
from app.tool.test_executor import TestExecutorTool
from app.tool.test_case_generator import TestCaseGeneratorTool
from app.tool.code_generator import CodeGeneratorTool
from app.tool.bash import BashTool
from app.tool.str_replace_editor import StrReplaceEditorTool
from app.tool.terminate import TerminateTool
from app.tool.planning import PlanningTool
from app.tool.web_search import WebSearchTool
from app.tool.browser.browser_use import BrowserUseTool
from app.tool.file_operators import FileOperatorTool
from app.tool.tara_analysis import TaraAnalysisTool
from app.tool.rag_query import RAGQueryTool
from app.core.logging import logger
# TARA系统提示
TARA_SYSTEM_PROMPT = """你是一个专门进行威胁分析与风险评估的AI助手。
你的任务是帮助用户识别车联网系统中的安全威胁，评估风险等级，并提出缓解措施。
你可以使用以下工具:
{tools_description}

请基于法规强标进行TARA分析，确保分析结果符合行业标准。
"""

TARA_NEXT_STEP_PROMPT = """请根据当前状态，决定下一步行动。
你可以执行以下操作:
1. 分析威胁
2. 评估风险
3. 生成缓解措施
4. 查询法规标准
5. 使用工具收集更多信息
"""

# 浏览器上下文辅助类
class BrowserContextHelper:
    """浏览器上下文辅助类"""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def format_next_step_prompt(self) -> str:
        """格式化浏览器上下文的下一步提示"""
        return """你正在使用浏览器工具。请根据当前浏览器状态，决定下一步行动:
1. 继续浏览网页获取信息
2. 提取当前页面的关键信息
3. 搜索特定内容
4. 返回到TARA分析任务

请确保收集到足够的信息后再进行TARA分析。
"""

class TaraAgent(ToolCallAgent):
    """威胁分析与风险评估智能体"""
    
    name: str = "TARA"
    description: str = "专门进行威胁分析与风险评估的智能体，基于法规强标进行TARA分析"
    
    # 系统提示不再使用模板字符串，而是在初始化时设置
    system_prompt: str = ""
    next_step_prompt: str = TARA_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletionTool(),
        TerminateTool(),
        PlanningTool(),
        WebSearchTool(),
        BrowserUseTool(),
        CodeGeneratorTool(),
        BashTool(),
        StrReplaceEditorTool(),
        FileOperatorTool(),
        AskHumanTool(),
        PythonExecuteTool(),
        # 专业工具
        TaraAnalysisTool(),
        RAGQueryTool(),
        TestExecutorTool(),
        TestCaseGeneratorTool(),
        
    ))
    
    # TARA特定属性
    regulation_database: Dict[str, str] = Field(default_factory=dict)
    threat_categories: List[str] = Field(default_factory=list)
    browser_context_helper: Optional[BrowserContextHelper] = None
    
    # 初始化方法
    @model_validator(mode="after")
    def initialize_helper(self) -> "TaraAgent":
        """初始化基础组件"""
        from app.core.logging import logger
        
        self.browser_context_helper = BrowserContextHelper(self)
        
        # 设置系统提示，替换工具描述
        tools_description = self._get_tools_description()
        self.system_prompt = TARA_SYSTEM_PROMPT.format(tools_description=tools_description)
        
        logger.info(f"TaraAgent 初始化完成，设置了系统提示，包含工具描述: {len(tools_description)} 字符")
        
        return self
    
    @classmethod
    async def create(cls, **kwargs) -> "TaraAgent":
        """创建并初始化TARA智能体"""
        instance = cls(**kwargs)
        await instance.initialize_regulations()
        return instance
    
    async def get_final_answer(self) -> Dict[str, Any]:
        """获取TARA分析的最终结果
        
        这个方法整合所有分析结果，提供最终的分析答案。
        
        Returns:
            Dict[str, Any]: 包含最终分析结果的字典
        """
        # 提取最后一条有意义的助手消息作为最终答案
        messages = self.memory.get_messages()
        assistant_messages = [m for m in reversed(messages) if m.get("role") == "assistant" and m.get("content")]
        
        final_answer = {
            "result": "未能生成分析结果",
            "analysis": {}
        }
        
        if assistant_messages:
            final_answer["result"] = assistant_messages[0].get("content", "")
            
            # 尝试从内存中提取资产、威胁、风险和缓解措施数据
            assets = self._extract_from_memory("assets")
            threats = self._extract_from_memory("threats")
            risks = self._extract_from_memory("risks")
            countermeasures = self._extract_from_memory("countermeasures")
            
            final_answer["analysis"] = {
                "assets": assets,
                "threats": threats,
                "risks": risks,
                "countermeasures": countermeasures
            }
        
        return final_answer
    
    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """为TARA分析生成详细的执行计划
        
        Args:
            task: TARA分析任务描述
            
        Returns:
            Dict[str, Any]: 生成的TARA执行计划
        """
        from app.core.logging import logger
        
        logger.info(f"TaraAgent 开始为任务生成执行计划: {task[:50]}...")
        
        # 获取可用工具列表
        available_tools = self._get_tools_description()
        logger.info(f"获取到 {len(available_tools.split('- '))-1} 个可用工具")
        
        # 构建TARA专用规划提示
        tara_planning_prompt = f"""
        请为以下车联网安全TARA分析任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 可用工具列表
        以下是你可以在执行计划中使用的工具:
        {available_tools}
        
        # TARA分析需求
        TARA (威胁分析与风险评估) 是车联网安全分析的重要方法论，需要完成以下步骤:
        1. 系统边界识别与定义
        2. 资产识别与梳理
        3. 攻击面分析
        4. 威胁场景建模
        5. 攻击树构建
        6. 风险评估 (基于影响和可能性)
        7. 缓解措施构建
        8. 安全需求与安全目标构建
        9. 验证测试方案建议
        
        # 规划格式
        请提供JSON格式的执行计划，包含以下内容:
        
        ```json
        {{
            "main_task": "TARA分析任务描述",
            "subtasks": [
                {{
                    "id": "subtask-1",
                    "name": "子任务名称 (例如：系统边界识别与定义)",
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
                // 更多子任务...
            ]
        }}
        ```
        
        请确保计划全面、详细，并明确每个步骤使用的工具。
        \\nothink"""
        
        logger.info("已构建TARA专用规划提示")
        
        try:
            # 调用LLM生成执行计划
            logger.info("开始调用LLM生成执行计划...")
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": tara_planning_prompt}
                ],
                temperature=0.7
            )
            logger.info(f"LLM响应完成，响应长度: {len(response) if response else 0}")
            
            # 解析JSON格式的执行计划
            plan = self._parse_plan_from_response(response)
            
            if plan:
                logger.info(f"成功解析执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                
                # 记录计划详情
                main_task = plan.get('main_task', '未命名任务')
                logger.info(f"主任务: {main_task[:100]}...")
                
                for i, subtask in enumerate(plan.get('subtasks', [])):
                    subtask_id = subtask.get('id', f'subtask-{i+1}')
                    subtask_name = subtask.get('name', '未命名子任务')
                    steps_count = len(subtask.get('steps', []))
                    dependencies = subtask.get('dependencies', [])
                    logger.info(f"子任务 {i+1}: ID={subtask_id}, 名称={subtask_name}, 包含 {steps_count} 个步骤, 步骤信息：{subtask.get('steps', [])}, 依赖={dependencies}")
                
                # 保存计划到智能体
                self.current_plan = plan
                self.subtasks = plan.get('subtasks', [])
                
                # 将规划添加到记忆中
                self.update_memory(
                    "system",
                    f"已生成TARA分析执行计划，包含 {len(self.subtasks)} 个子任务。"
                )
                
                return plan
            else:
                logger.error("解析执行计划失败，未能提取有效的JSON")
                # 尝试使用基类的generate_plan方法
                return await super().generate_plan(task)
                
        except Exception as e:
            logger.error(f"生成TARA执行计划时出错: {str(e)}")
            # 尝试使用基类的generate_plan方法
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
    
    def _parse_plan_from_response(self, response: str) -> Dict[str, Any]:
        """从LLM响应中解析执行计划
        
        Args:
            response: LLM响应文本
            
        Returns:
            Dict[str, Any]: 解析后的执行计划，如果解析失败则返回None
        """
        from app.core.logging import logger
        import re
        import json
        
        try:
            # 尝试从响应中提取JSON部分
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.info("从响应中成功提取JSON代码块")
            else:
                # 尝试直接解析整个响应
                json_str = response
                logger.info("未找到JSON代码块，尝试直接解析响应")
            
            # 解析JSON
            plan = json.loads(json_str)
            
            # 验证计划结构
            if "subtasks" not in plan:
                logger.warning("解析的计划中缺少subtasks字段")
                return None
                
            # 验证计划是否包含关键TARA分析步骤
            subtask_names = [st.get('name', '').lower() for st in plan.get('subtasks', [])]
            expected_keywords = ['资产', '威胁', '风险', '缓解']
            
            missing_keywords = [kw for kw in expected_keywords if not any(kw in name for name in subtask_names)]
            if missing_keywords:
                logger.warning(f"生成的TARA计划缺少关键步骤: {', '.join(missing_keywords)}")
                
                # 添加缺失的关键步骤
                self._add_missing_steps(plan, missing_keywords)
            
            return plan
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"解析执行计划时出错: {str(e)}")
            return None
    
    def _add_missing_steps(self, plan: Dict[str, Any], missing_keywords: List[str]) -> None:
        """向计划中添加缺失的关键步骤
        
        Args:
            plan: 执行计划
            missing_keywords: 缺失的关键词列表
        """
        from app.core.logging import logger
        
        for kw in missing_keywords:
            if kw == '资产':
                plan['subtasks'].insert(0, {
                    "id": f"subtask-asset-{len(plan['subtasks'])+1}",
                    "name": "资产识别与梳理",
                    "description": "识别和梳理系统中的关键资产，包括硬件、软件、数据等",
                    "steps": [
                        {
                            "id": f"step-asset-1",
                            "description": "确定系统边界和范围",
                            "tools": ["create_chat_completion", "web_search"],
                            "expected_output": "清晰定义的系统边界文档"
                        },
                        {
                            "id": f"step-asset-2",
                            "description": "识别关键资产列表",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "完整的资产清单，包括重要性评级"
                        }
                    ],
                    "dependencies": []
                })
                logger.info("已添加缺失的资产识别子任务")
            elif kw == '威胁':
                plan['subtasks'].append({
                    "id": f"subtask-threat-{len(plan['subtasks'])+1}",
                    "name": "威胁场景识别",
                    "description": "识别可能的威胁场景和攻击途径",
                    "steps": [
                        {
                            "id": f"step-threat-1",
                            "description": "分析攻击面",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "攻击面分析报告"
                        },
                        {
                            "id": f"step-threat-2",
                            "description": "建立威胁模型",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "威胁模型文档"
                        }
                    ],
                    "dependencies": ["subtask-asset-1"]
                })
                logger.info("已添加缺失的威胁分析子任务")
            elif kw == '风险':
                plan['subtasks'].append({
                    "id": f"subtask-risk-{len(plan['subtasks'])+1}",
                    "name": "风险评估",
                    "description": "基于威胁和资产评估风险等级",
                    "steps": [
                        {
                            "id": f"step-risk-1",
                            "description": "评估威胁影响",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "威胁影响评估表"
                        },
                        {
                            "id": f"step-risk-2",
                            "description": "评估威胁可能性",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "威胁可能性评估表"
                        },
                        {
                            "id": f"step-risk-3",
                            "description": "计算综合风险等级",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "风险等级矩阵"
                        }
                    ],
                    "dependencies": ["subtask-threat-1"]
                })
                logger.info("已添加缺失的风险评估子任务")
            elif kw == '缓解':
                plan['subtasks'].append({
                    "id": f"subtask-mitigation-{len(plan['subtasks'])+1}",
                    "name": "缓解措施制定",
                    "description": "为识别的高风险威胁制定缓解措施",
                    "steps": [
                        {
                            "id": f"step-mitigation-1",
                            "description": "确定缓解措施",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "缓解措施列表"
                        },
                        {
                            "id": f"step-mitigation-2",
                            "description": "评估缓解措施有效性",
                            "tools": ["create_chat_completion", "tara_analysis"],
                            "expected_output": "缓解措施有效性评估"
                        }
                    ],
                    "dependencies": ["subtask-risk-1"]
                })
                logger.info("已添加缺失的缓解措施子任务")
    
    def _extract_tool_calls_from_response(self, response: Any) -> List[ToolCall]:
        """从LLM响应中提取工具调用
        
        Args:
            response: LLM响应
            
        Returns:
            List[ToolCall]: 提取的工具调用列表
        """
        from app.core.logging import logger
        
        try:
            # 使用父类中的_parse_tool_calls方法
            tool_calls = self._parse_tool_calls(response)
            if tool_calls:
                logger.info(f"从响应中提取到 {len(tool_calls)} 个工具调用")
            else:
                logger.info("未从响应中提取到工具调用")
            return tool_calls
        except Exception as e:
            logger.error(f"提取工具调用时出错: {str(e)}")
            return []
    
    def _extract_from_memory(self, key: str) -> Optional[str]:
        """从记忆中提取特定信息
        
        Args:
            key: 信息键名
            
        Returns:
            Optional[str]: 提取的信息，如果不存在则返回None
        """
        for message in reversed(self.memory.get_messages()):
            if message.get("role") == "assistant" and isinstance(message.get("content"), dict):
                if key in message.get("content", {}):
                    return message["content"][key]
        return None
    
    async def initialize_regulations(self):
        """初始化法规数据库"""
        # 示例法规数据
        self.regulation_database = {
            "GB/T 20984-2007": "信息安全技术 信息安全风险评估规范",
            "GB/T 36958-2018": "信息安全技术 汽车电子系统网络安全导则",
            "ISO/SAE 21434": "道路车辆 网络安全工程",
            "UN R155": "联合国法规第155号 网络安全与网络安全管理系统"
        }
        
        # 威胁类别
        self.threat_categories = [
            "欺骗", "篡改", "抵赖", "信息泄露", "拒绝服务", "权限提升"
        ]
    
    async def think(self) -> bool:
        """处理当前状态和决定下一步行动，支持浏览器上下文"""
        logger.info(f"tara.py think...")
        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.get("function", {}).get("name") == BrowserUseTool().name if isinstance(tc, dict) else tc.function.get("name") == BrowserUseTool().name
            for msg in recent_messages
            if "tool_calls" in msg
            for tc in msg.get("tool_calls", [])
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        try:
            result = await super().think()
            # 恢复原始提示
            self.next_step_prompt = original_prompt
            return result
        except AttributeError as e:
            if "'dict' object has no attribute 'function'" in str(e):
                # 处理字典格式的工具调用
                logger.warning(f"处理工具调用时出现错误: {str(e)}，尝试修复...")
                # 如果出现错误，可能是工具调用格式不一致，尝试修复内存中的最后一条消息
                if self.memory.messages:
                    for i in range(len(self.memory.messages) - 1, -1, -1):
                        msg = self.memory.messages[i]
                        if "tool_calls" in msg:
                            fixed_tool_calls = []
                            for tc in msg["tool_calls"]:
                                if isinstance(tc, dict) and "function" not in tc and "name" in tc:
                                    # 修复格式
                                    fixed_tc = {
                                        "id": tc.get("id", f"call_{len(fixed_tool_calls)}"),
                                        "function": {
                                            "name": tc.get("name"),
                                            "arguments": tc.get("arguments", "{}")
                                        }
                                    }
                                    fixed_tool_calls.append(fixed_tc)
                                else:
                                    fixed_tool_calls.append(tc)
                            
                            # 更新消息中的工具调用
                            self.memory.messages[i]["tool_calls"] = fixed_tool_calls
                            break
                    
                    # 重试think操作
                    logger.info("已修复工具调用格式，重试think操作")
                    result = await super().think()
                    # 恢复原始提示
                    self.next_step_prompt = original_prompt
                    return result
                else:
                    logger.error("无法修复工具调用格式，内存中没有消息")
                    # 恢复原始提示
                    self.next_step_prompt = original_prompt
                    return False
            else:
                # 其他类型的错误，重新抛出
                logger.error(f"think方法执行出错: {str(e)}")
                # 恢复原始提示
                self.next_step_prompt = original_prompt
                raise
    
    # TARA特定方法
    async def analyze_threat(self, target_description: str) -> Dict[str, Any]:
        """分析特定目标的威胁"""
        # 使用TARA分析工具
        tara_tool = self.available_tools.get_tool("tara_analysis")
        if not tara_tool:
            return {"error": "TARA分析工具不可用"}
        
        result = await tara_tool.execute(target=target_description)
        return result.output if hasattr(result, "output") else {"error": "执行分析失败"}
    
    async def assess_risk(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估威胁的风险等级"""
        # 实际实现将基于威胁数据进行风险评估
        results = {}
        
        for threat in threat_data.get("threats", []):
            threat_id = threat.get("id")
            likelihood = threat.get("likelihood", "中")
            
            # 根据威胁类型和可能性评估影响
            impact = self._determine_impact(threat)
            
            # 计算风险等级
            risk_level = self._calculate_risk_level(likelihood, impact)
            
            results[threat_id] = {
                "threat": threat,
                "impact": impact,
                "risk_level": risk_level
            }
        
        return results
    
    def _determine_impact(self, threat: Dict[str, Any]) -> str:
        """确定威胁影响"""
        # 简单示例实现
        threat_name = threat.get("name", "").lower()
        
        if "拒绝服务" in threat_name or "安全" in threat_name:
            return "高"
        elif "泄露" in threat_name or "篡改" in threat_name:
            return "中"
        else:
            return "低"
    
    def _calculate_risk_level(self, likelihood: str, impact: str) -> str:
        """计算风险等级"""
        # 风险矩阵
        risk_matrix = {
            ("高", "高"): "严重",
            ("高", "中"): "高",
            ("高", "低"): "中",
            ("中", "高"): "高",
            ("中", "中"): "中",
            ("中", "低"): "低",
            ("低", "高"): "中",
            ("低", "中"): "低",
            ("低", "低"): "可忽略"
        }
        
        return risk_matrix.get((likelihood, impact), "未知")
    
    async def generate_mitigation(self, risk_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成缓解措施"""
        # 实际实现将基于风险数据生成缓解措施
        mitigations = []
        
        for threat_id, risk_info in risk_data.items():
            threat = risk_info.get("threat", {})
            risk_level = risk_info.get("risk_level", "未知")
            
            # 生成针对此威胁的缓解措施
            measures = self._generate_measures_for_threat(threat, risk_level)
            
            mitigations.append({
                "threat_id": threat_id,
                "threat_name": threat.get("name", "未知威胁"),
                "risk_level": risk_level,
                "measures": measures
            })
        
        return mitigations
    
    def _generate_measures_for_threat(self, threat: Dict[str, Any], risk_level: str) -> List[str]:
        """为特定威胁生成缓解措施"""
        # 简单示例实现
        threat_name = threat.get("name", "").lower()
        measures = []
        
        if "未授权访问" in threat_name:
            measures.append("实施强身份认证机制")
            measures.append("定期审查访问权限")
        elif "拒绝服务" in threat_name:
            measures.append("部署DDoS防护系统")
            measures.append("实施流量限制和监控")
        elif "数据泄露" in threat_name:
            measures.append("实施数据加密")
            measures.append("建立数据访问控制")
        else:
            measures.append("实施安全监控")
            measures.append("定期安全评估")
        
        # 根据风险等级调整措施优先级
        if risk_level in ["严重", "高"]:
            measures.append("制定应急响应计划")
        
        return measures
        
    # 添加新的方法以支持TARA分析图
    async def identify_assets(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别并分析系统资产
        
        这个方法动态分解任务，识别系统中的关键资产，并对其进行分类和重要性评估。
        """
        # 更新内存，添加任务上下文
        self.update_memory("system", "开始执行资产识别任务")
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            self.update_memory(role, content)
        
        # 构建提示以引导资产识别
        prompt = """
        请帮我识别系统中的关键资产。资产识别是TARA分析的第一步，需要全面识别系统中的重要组件。
        
        请按照以下步骤进行：
        1. 分析系统架构和功能
        2. 识别关键硬件组件
        3. 识别关键软件组件
        4. 识别关键数据资产
        5. 对资产进行分类和重要性评估
        
        对于每个资产，请提供：
        - 资产ID
        - 资产名称
        - 资产类型（硬件/软件/数据）
        - 重要性级别（高/中/低）
        - 简要描述
        """
        
        # 使用工具进行资产识别
        response = await self.run(prompt)
        
        # 解析响应，提取资产信息
        # 实际实现中应该有更复杂的解析逻辑
        assets = []
        # 简单示例实现，实际应该基于LLM响应解析
        assets = [
            {
                "id": "A001",
                "name": "车载中控系统",
                "type": "硬件",
                "importance": "高",
                "description": "车辆的核心控制系统，管理车辆的关键功能"
            },
            {
                "id": "A002",
                "name": "车联网通信模块",
                "type": "硬件",
                "importance": "高",
                "description": "负责车辆与外部网络的通信"
            },
            {
                "id": "A003",
                "name": "车辆操作系统",
                "type": "软件",
                "importance": "高",
                "description": "车辆的基础操作系统，管理各个子系统"
            },
            {
                "id": "A004",
                "name": "用户个人数据",
                "type": "数据",
                "importance": "高",
                "description": "包括用户账户、位置历史等敏感信息"
            }
        ]
        
        return {"assets": assets}
    
    async def identify_threats(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于资产识别潜在威胁
        
        这个方法动态分析每个资产面临的潜在威胁，并进行分类和评估。
        """
        from app.core.logging import logger
        # 更新内存，添加任务上下文
        self.update_memory("system", "开始执行威胁识别任务")
        logger.info(f"资产信息: {assets}")
        # 构建提示以引导威胁识别
        assets_str = "\n".join([f"- {a['name']} ({a['type']}): {a['description']}" for a in assets])
        output_str = '''
        {
            "threats": [
                {
                    "id": "T001",
                    "name": "威胁名称",
                    "asset_id": "相关资产ID",
                    "type": "威胁类型",
                    "likelihood": "可能性",
                    "description": "威胁描述"
                },
                ...
            ]
        }
        '''
        prompt = f"""
        基于以下已识别的资产，请帮我识别潜在的安全威胁：
        
        {assets_str}
        
        请按照以下步骤进行：
        1. 分析每个资产可能面临的威胁
        2. 考虑STRIDE威胁模型（欺骗、篡改、抵赖、信息泄露、拒绝服务、权限提升）
        3. 评估每个威胁的可能性（高/中/低）
        
        对于每个威胁，请提供：
        - 威胁ID
        - 威胁名称
        - 相关资产ID
        - 威胁类型（STRIDE分类）
        - 可能性评估
        - 简要描述
        
        请以JSON格式返回结果，格式如下：
        ```json
        {output_str}
        ```
        """
        
        # 使用工具进行威胁识别
        try:
            # 不使用父类的run方法，直接使用LLM生成响应
            logger.info("开始生成威胁识别响应...")
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": "你是一个安全威胁分析专家，擅长识别系统中的潜在威胁。"},
                {"role": "user", "content": prompt}
            ]
            
            # 直接使用LLM生成响应
            response = await self.llm.ask(messages=messages)
            logger.info(f"威胁识别响应类型: {type(response)}")
            logger.info(f"响应内容前100个字符: {str(response)}")
        except Exception as e:
            logger.error(f"生成威胁识别响应时出错: {str(e)}")
            # 使用备选方法生成威胁
            return {"threats": self._generate_threats_from_assets(assets)}
        
        # 解析响应，提取威胁信息
        threats = []
        try:
            # 尝试从响应中提取JSON数据
            import re
            import json
            
            # 查找JSON格式的响应
            if isinstance(response, str):
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                    if "threats" in data and isinstance(data["threats"], list):
                        threats = data["threats"]
                
                # 如果没有找到有效的JSON，尝试直接解析整个响应
                if not threats:
                    try:
                        data = json.loads(response)
                        if "threats" in data and isinstance(data["threats"], list):
                            threats = data["threats"]
                    except:
                        pass
                
                # 如果仍然没有提取到威胁，尝试使用正则表达式提取关键信息
                if not threats:
                    # 查找威胁ID模式
                    threat_ids = re.findall(r'T\d{3}', response)
                    asset_ids = [a["id"] for a in assets]
                    threat_types = ["欺骗", "篡改", "抵赖", "信息泄露", "拒绝服务", "权限提升"]
                    likelihood_levels = ["高", "中", "低"]
                    
                    for i, threat_id in enumerate(threat_ids[:10]):  # 限制最多10个威胁
                        # 尝试找到与该ID相关的描述
                        name_match = re.search(rf'{threat_id}[^\n]*?([^\n]+)', response)
                        name = name_match.group(1).strip() if name_match else f"威胁{i+1}"
                        
                        # 为威胁分配资产ID
                        asset_id = asset_ids[i % len(asset_ids)]
                        
                        # 为威胁分配类型
                        type_index = i % len(threat_types)
                        threat_type = threat_types[type_index]
                        
                        # 为威胁分配可能性
                        likelihood_index = i % len(likelihood_levels)
                        likelihood = likelihood_levels[likelihood_index]
                        
                        threats.append({
                            "id": threat_id,
                            "name": name,
                            "asset_id": asset_id,
                            "type": threat_type,
                            "likelihood": likelihood,
                            "description": f"针对{asset_id}的{threat_type}威胁"
                        })
            else:
                logger.error(f"响应不是字符串类型，而是 {type(response)}")
        except Exception as e:
            logger.error(f"解析威胁识别响应失败: {str(e)}")
            
        # 如果没有成功提取威胁，使用基于规则的方法生成
        if not threats:
            logger.warning("未能从LLM响应中提取威胁信息，使用基于规则的方法生成")
            threats = self._generate_threats_from_assets(assets)
            
        return {"threats": threats}
    
    def _generate_threats_from_assets(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于资产类型和重要性生成威胁
        
        当LLM响应解析失败时，使用此方法作为备选
        
        Args:
            assets: 资产列表
            
        Returns:
            生成的威胁列表
        """
        threats = []
        threat_types = {
            "硬件": ["篡改", "拒绝服务", "权限提升"],
            "软件": ["欺骗", "篡改", "抵赖", "权限提升"],
            "数据": ["信息泄露", "篡改", "抵赖"]
        }
        
        threat_templates = {
            "篡改": {
                "硬件": "物理篡改{}，导致功能异常或安全漏洞",
                "软件": "未授权修改{}，导致功能异常或引入后门",
                "数据": "未授权修改{}，导致数据完整性受损"
            },
            "欺骗": {
                "硬件": "伪造{}身份，绕过身份验证",
                "软件": "伪造{}接口，欺骗用户或系统",
                "数据": "伪造{}内容，误导决策或操作"
            },
            "抵赖": {
                "硬件": "{}操作无法追溯，导致责任无法确定",
                "软件": "{}交互无法验证，导致操作可被否认",
                "数据": "{}变更无法审计，导致责任无法追溯"
            },
            "信息泄露": {
                "硬件": "{}配置信息泄露，导致安全机制被绕过",
                "软件": "{}敏感信息泄露，导致系统机密被获取",
                "数据": "{}内容泄露，导致隐私或机密信息被获取"
            },
            "拒绝服务": {
                "硬件": "对{}发起物理干扰，导致服务中断",
                "软件": "对{}发起资源耗尽攻击，导致服务不可用",
                "数据": "对{}存储系统发起攻击，导致数据不可访问"
            },
            "权限提升": {
                "硬件": "利用{}漏洞获取更高权限，执行未授权操作",
                "软件": "利用{}漏洞提升权限，获取系统控制权",
                "数据": "利用{}访问控制缺陷，获取未授权数据"
            }
        }
        
        likelihood_by_importance = {
            "高": "高",
            "中": "中",
            "低": "低"
        }
        
        for i, asset in enumerate(assets):
            asset_id = asset.get("id")
            asset_name = asset.get("name")
            asset_type = asset.get("type")
            asset_importance = asset.get("importance", "中")
            
            # 根据资产类型选择适合的威胁类型
            applicable_threat_types = threat_types.get(asset_type, ["欺骗", "篡改", "信息泄露"])
            
            # 为每个资产生成2-3个威胁
            num_threats = 3 if asset_importance == "高" else (2 if asset_importance == "中" else 1)
            
            for j in range(min(num_threats, len(applicable_threat_types))):
                threat_type = applicable_threat_types[j]
                likelihood = likelihood_by_importance.get(asset_importance, "中")
                
                # 使用模板生成威胁描述
                template = threat_templates.get(threat_type, {}).get(asset_type, "对{}的{}威胁")
                description = template.format(asset_name)
                
                threat_id = f"T{i+1:02d}{j+1}"
                threat_name = f"{threat_type}：{asset_name}"
                
                threats.append({
                    "id": threat_id,
                    "name": threat_name,
                    "asset_id": asset_id,
                    "type": threat_type,
                    "likelihood": likelihood,
                    "description": description
                })
        
        return threats
    
    async def analyze_risks(self, assets: List[Dict[str, Any]], threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析威胁风险
        
        这个方法动态评估每个威胁的风险级别，考虑威胁可能性和潜在影响。
        """
        # 更新内存，添加任务上下文
        self.update_memory("system", "开始执行风险分析任务")
        
        # 构建资产和威胁的映射，便于查找
        assets_map = {a["id"]: a for a in assets}
        
        risks = []
        for threat in threats:
            # 获取相关资产
            asset_id = threat.get("asset_id")
            asset = assets_map.get(asset_id, {})
            asset_importance = asset.get("importance", "中")
            
            # 获取威胁可能性
            likelihood = threat.get("likelihood", "中")
            
            # 基于资产重要性确定影响
            impact_map = {"高": "高", "中": "中", "低": "低"}
            impact = impact_map.get(asset_importance, "中")
            
            # 计算风险级别
            risk_level = self._calculate_risk_level(likelihood, impact)
            
            risks.append({
                "id": f"R{threat['id'][1:]}",
                "threat_id": threat["id"],
                "asset_id": asset_id,
                "likelihood": likelihood,
                "impact": impact,
                "risk_level": risk_level,
                "description": f"风险：{threat.get('name')} 对 {asset.get('name', '未知资产')} 的影响"
            })
        
        return {"risks": risks}
    
    async def develop_countermeasures(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """开发缓解措施
        
        这个方法动态为每个风险制定缓解措施和安全控制。
        """
        # 更新内存，添加任务上下文
        self.update_memory("system", "开始执行缓解措施开发任务")
        
        # 构建提示以引导缓解措施开发
        risks_str = "\n".join([f"- {r['description']} (风险级别: {r['risk_level']})" for r in risks])
        prompt = f"""
        基于以下已识别的风险，请帮我开发相应的缓解措施：
        
        {risks_str}
        
        请按照以下步骤进行：
        1. 分析每个风险的特点
        2. 考虑技术和管理两方面的缓解措施
        3. 确保措施的可行性和有效性
        4. 为高风险项目提供更全面的措施
        
        对于每个缓解措施，请提供：
        - 措施ID
        - 相关风险ID
        - 措施名称
        - 措施类型（技术/管理）
        - 实施优先级（高/中/低）
        - 详细描述
        """
        
        # 使用工具开发缓解措施
        response = await self.run(prompt)
        
        # 解析响应，提取缓解措施信息
        countermeasures = []
        # 简单示例实现，实际应该基于LLM响应解析
        for i, risk in enumerate(risks):
            risk_id = risk.get("id")
            risk_level = risk.get("risk_level")
            
            # 根据风险级别确定措施数量和优先级
            num_measures = 3 if risk_level == "严重" else (2 if risk_level == "高" else 1)
            priority = "高" if risk_level in ["严重", "高"] else "中"
            
            for j in range(num_measures):
                measure_id = f"M{i+1}{j+1}"
                
                if j == 0:
                    measure = {
                        "id": measure_id,
                        "risk_id": risk_id,
                        "name": f"技术控制 {measure_id}",
                        "type": "技术",
                        "priority": priority,
                        "description": f"针对风险 {risk_id} 的技术缓解措施"
                    }
                else:
                    measure = {
                        "id": measure_id,
                        "risk_id": risk_id,
                        "name": f"管理控制 {measure_id}",
                        "type": "管理",
                        "priority": priority,
                        "description": f"针对风险 {risk_id} 的管理缓解措施"
                    }
                
                countermeasures.append(measure)
        
        return {"countermeasures": countermeasures}
    
    async def generate_report(self, assets: List[Dict[str, Any]], threats: List[Dict[str, Any]], 
                            risks: List[Dict[str, Any]], countermeasures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成TARA分析报告
        
        这个方法动态整合所有分析结果，生成完整的TARA分析报告。
        """
        # 更新内存，添加任务上下文
        self.update_memory("system", "开始生成TARA分析报告")
        
        # 构建提示以引导报告生成
        prompt = f"""
        请基于以下TARA分析结果，生成一份完整的威胁分析与风险评估报告：
        
        1. 已识别资产: {len(assets)} 项
        2. 已识别威胁: {len(threats)} 项
        3. 风险评估: {len(risks)} 项
        4. 缓解措施: {len(countermeasures)} 项
        
        报告应包含以下部分：
        1. 执行摘要
        2. 系统概述
        3. 资产清单及分析
        4. 威胁分析
        5. 风险评估
        6. 缓解措施
        7. 结论与建议
        
        请确保报告符合车联网安全标准和法规要求。
        """
        
        # 使用工具生成报告
        response = await self.run(prompt)
        
        # 构建完整报告
        report = {
            "title": "车联网系统威胁分析与风险评估报告",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": "本报告提供了对车联网系统的全面安全评估，包括资产识别、威胁分析、风险评估和缓解措施建议。",
            "assets": assets,
            "threats": threats,
            "risks": risks,
            "countermeasures": countermeasures,
            "conclusion": "基于TARA分析，系统存在多项安全风险，需要实施相应的缓解措施以提高系统安全性。",
            "content": response  # 完整报告内容
        }
        
        return report

# 导入循环依赖
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.terminate import TerminateTool