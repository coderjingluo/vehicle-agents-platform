"""
KunlunSec AI Platform - 测试用例智能体模块

实现基于TARA分析结果生成测试用例的智能体。
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import Field

from app.agent.toolcall import ToolCallAgent, ToolCollection
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.terminate import TerminateTool
from app.tool.planning import PlanningTool
from app.tool.rag_query import RAGQueryTool
from app.tool.file_operators import FileOperatorTool
from app.tool.test_case_generator import TestCaseGeneratorTool
from app.core.logging import logger
from app.agent.base import AgentState

# 测试用例系统提示
TEST_CASE_SYSTEM_PROMPT = """你是一个专门生成车联网安全测试用例的AI助手。
你的任务是基于TARA分析结果，为识别出的威胁生成详细的测试用例。
你可以使用以下工具:
{tools_description}

请确保测试用例覆盖所有关键威胁，并符合行业测试标准。
"""

TEST_CASE_NEXT_STEP_PROMPT = """请根据当前状态，决定下一步行动。
你可以执行以下操作:
1. 分析TARA结果
2. 生成测试用例
3. 评估测试覆盖率
4. 查询测试模板
5. 使用工具收集更多信息
"""

class TestCaseAgent(ToolCallAgent):
    """测试用例生成智能体"""
    
    name: str = "TestCase"
    description: str = "基于TARA分析结果生成测试用例的专业智能体"
    
    system_prompt: str = TEST_CASE_SYSTEM_PROMPT
    next_step_prompt: str = TEST_CASE_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletionTool(),
        TerminateTool(),
        PlanningTool(),
        
        # 专业工具
        TestCaseGeneratorTool(),
        RAGQueryTool(),
        FileOperatorTool(),
    ))
    
    # 测试用例特定属性
    test_templates: Dict[str, str] = Field(default_factory=dict)
    coverage_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # 任务计划和执行相关属性
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    current_plan: Optional[Dict[str, Any]] = Field(default=None)
    completed_subtasks: List[str] = Field(default_factory=list)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "TestCaseAgent":
        """创建并初始化测试用例智能体"""
        instance = cls(**kwargs)
        await instance.initialize_templates()
        return instance
        
    async def run(self, request: Optional[str] = None) -> str:
        """运行测试用例生成智能体
        
        按照计划分解任务并按顺序执行
        
        Args:
            request: 请求内容
            
        Returns:
            str: 执行结果
        """
        if request:
            self.update_memory("user", request)
        
        try:
            # 1. 生成测试用例执行计划
            logger.info("开始生成测试用例执行计划...")
            plan = await self.generate_plan(request or "生成测试用例")
            
            # 2. 设置计划
            self.current_plan = plan
            self.subtasks = plan.get('subtasks', [])
            
            logger.info(f"测试用例执行计划已生成，包含 {len(self.subtasks)} 个子任务")
            
            # 3. 执行子任务 - 使用ToolCallAgent的think-act循环
            self.state = AgentState.IDLE
            self.current_step = 0
            
            while self.state != AgentState.FINISHED and self.current_step < self.max_steps:
                self.current_step += 1
                
                # 思考
                should_continue = await super().think()  # 调用父类的think方法
                if not should_continue:
                    break
                
                # 执行
                await self.act()
            
            # 4. 返回结果
            return self.get_final_answer()
            
        except Exception as e:
            logger.error(f"运行测试用例生成智能体出错: {str(e)}")
            return f"错误: {str(e)}"
    
    async def initialize_templates(self):
        """初始化测试模板库"""
        # 示例测试模板
        self.test_templates = {
            "未授权访问": """
测试用例: {test_id}
名称: 未授权访问测试
描述: 验证系统是否能够防止未授权访问
前置条件: 系统正常运行
步骤:
1. 尝试使用无效凭证访问系统
2. 尝试绕过认证机制
3. 尝试提升权限访问受限资源
预期结果: 所有未授权访问尝试均被系统拒绝并记录
            """,
            
            "拒绝服务": """
测试用例: {test_id}
名称: 拒绝服务攻击测试
描述: 验证系统在面对DoS攻击时的韧性
前置条件: 系统正常运行，监控系统就绪
步骤:
1. 在受控环境中模拟高流量请求
2. 监控系统响应时间和资源使用情况
3. 验证系统恢复机制
预期结果: 系统能够检测异常流量并采取措施，保持核心功能可用
            """,
            
            "数据篡改": """
测试用例: {test_id}
名称: 数据完整性测试
描述: 验证系统是否能够防止数据被篡改
前置条件: 系统正常运行，测试数据已准备
步骤:
1. 尝试在传输过程中修改数据
2. 尝试绕过完整性检查机制
3. 验证系统对篡改数据的响应
预期结果: 系统能够检测数据篡改并拒绝处理被篡改的数据
            """
        }
    
    # 测试用例特定方法
    async def generate_test_cases(self, tara_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于TARA结果生成测试用例"""
        all_test_cases = []
        
        # 获取威胁列表
        threats = tara_result.get("threats", [])
        
        for threat in threats:
            # 使用测试用例生成工具
            test_case_generator = self.available_tools.get_tool("test_case_generator")
            if not test_case_generator:
                continue
                
            # 生成测试用例
            result = await test_case_generator.execute(
                threat_data=threat,
                format="detailed"
            )
            
            if hasattr(result, "output") and "test_cases" in result.output:
                test_case_result = {
                    "threat_id": threat.get("id"),
                    "threat_name": threat.get("name"),
                    "test_cases": result.output["test_cases"]
                }
            
            # 使用模板丰富测试用例
            enriched_cases = await self._enrich_with_templates(test_case_result)
            all_test_cases.extend(enriched_cases)
        
        return all_test_cases
    
    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """为测试用例生成任务创建详细的执行计划
        
        Args:
            task: 测试用例生成任务描述
            
        Returns:
            Dict[str, Any]: 生成的执行计划
        """
        from app.core.logging import logger
        
        # 获取可用工具列表
        available_tools = self._get_tools_description()
        
        # 构建测试用例生成专用规划提示
        testcase_planning_prompt = f"""
        请为以下车联网安全测试用例生成任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 可用工具列表
        以下是你可以在执行计划中使用的工具:
        {available_tools}
        
        # 测试用例生成需求
        测试用例生成是车联网安全验证的重要环节，需要完成以下步骤:
        1. 分析测试目标系统
        2. 提取/获取威胁信息
        3. 设计测试用例框架
        4. 生成功能测试用例
        5. 生成安全测试用例
        6. 生成边界测试用例
        7. 生成异常测试用例
        8. 生成渗透测试用例
        9. 优化测试覆盖率
        10. 生成测试报告模板
        
        # 规划格式
        请提供JSON格式的执行计划，包含以下内容:
        
        ```json
        {{
            "main_task": "测试用例生成任务描述",
            "subtasks": [
                {{
                    "id": "subtask-1",
                    "name": "子任务名称 (例如：测试目标系统分析)",
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
                // 所有测试用例生成必要的子任务...
            ]
        }}
        ```
        
        请确保规划涵盖完整的测试用例生成流程，每个子任务和步骤都清晰可执行，且符合车联网安全测试的专业要求。
        重要：每个步骤中指定的工具必须从上面提供的"可用工具列表"中选择，不要使用列表之外的工具。
        """
        
        logger.info(f"正在为测试用例生成任务制定执行计划: {task[:50]}...")
        
        try:
            # 向LLM发送规划请求
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": "你是车联网安全测试专家，擅长设计结构化的测试用例生成计划。"},
                    {"role": "user", "content": testcase_planning_prompt}
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
                logger.info(f"成功生成测试用例执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                
                # 验证计划是否包含关键测试用例生成步骤
                subtask_names = [st.get('name', '').lower() for st in plan.get('subtasks', [])]
                expected_keywords = ['分析', '威胁', '测试用例', '覆盖率', '报告']
                
                missing_keywords = [kw for kw in expected_keywords if not any(kw in name for name in subtask_names)]
                if missing_keywords:
                    logger.warning(f"生成的测试用例计划缺少关键步骤: {', '.join(missing_keywords)}")
                    
                    # 添加缺失的关键步骤
                    for kw in missing_keywords:
                        # 生成一个新的子任务
                        new_subtask = {
                            "id": f"subtask-{str(uuid.uuid4())[:8]}",
                            "name": f"补充步骤: {kw}相关任务",
                            "description": f"确保测试用例生成过程中包含{kw}相关的必要步骤",
                            "steps": [
                                {
                                    "id": f"step-{str(uuid.uuid4())[:8]}",
                                    "description": f"执行{kw}相关的必要分析和操作",
                                    "tools": ["create_chat_completion", "rag_query"],
                                    "expected_output": f"{kw}相关的分析结果和操作输出"
                                }
                            ],
                            "dependencies": []  # 可能需要根据步骤类型设置依赖
                        }
                        plan['subtasks'].append(new_subtask)
                
                # 确保计划有正确的ID和依赖
                for i, subtask in enumerate(plan.get('subtasks', [])):
                    if 'id' not in subtask or not subtask['id']:
                        subtask['id'] = f"subtask-{i+1}"
                    
                    # 确保每个子任务都有依赖字段
                    if 'dependencies' not in subtask:
                        subtask['dependencies'] = []
                    
                    # 确保每个步骤都有ID
                    for j, step in enumerate(subtask.get('steps', [])):
                        if 'id' not in step or not step['id']:
                            step['id'] = f"step-{i+1}.{j+1}"
                        
                        # 确保每个步骤都有工具字段
                        if 'tools' not in step:
                            step['tools'] = ["create_chat_completion"]
                            
                        # 初始化步骤状态
                        step['status'] = '待执行'
                
                # 初始化子任务状态
                for subtask in plan.get('subtasks', []):
                    subtask['status'] = '待执行'
                
                return plan
                
            except json.JSONDecodeError as e:
                logger.error(f"无法解析测试用例执行计划JSON: {e}")
                # 创建一个基本的默认计划
                return self._create_default_plan(task)
                
        except Exception as e:
            logger.error(f"生成测试用例执行计划时出错: {e}")
            # 创建一个基本的默认计划
            return self._create_default_plan(task)

    def _create_default_plan(self, task: str) -> Dict[str, Any]:
        """创建默认的测试用例生成计划
        
        当自动计划生成失败时使用。
        
        Args:
            task: 任务描述
            
        Returns:
            Dict[str, Any]: 默认的执行计划
        """
        logger.info("创建默认的测试用例生成计划")
        
        # 基本的测试用例生成步骤
        plan = {
            "main_task": f"测试用例生成: {task[:50]}...",
            "subtasks": [
                {
                    "id": "subtask-1",
                    "name": "需求分析",
                    "description": "分析测试需求和目标系统",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-1.1",
                            "description": "分析测试需求",
                            "tools": ["create_chat_completion"],
                            "expected_output": "测试需求分析结果",
                            "status": "待执行"
                        },
                        {
                            "id": "step-1.2",
                            "description": "分析目标系统",
                            "tools": ["create_chat_completion", "rag_query"],
                            "expected_output": "目标系统分析结果",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": []
                },
                {
                    "id": "subtask-2",
                    "name": "威胁识别和分析",
                    "description": "识别和分析相关威胁",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-2.1",
                            "description": "识别相关威胁",
                            "tools": ["create_chat_completion", "rag_query"],
                            "expected_output": "相关威胁列表",
                            "status": "待执行"
                        },
                        {
                            "id": "step-2.2",
                            "description": "分析威胁特性",
                            "tools": ["create_chat_completion"],
                            "expected_output": "威胁特性分析结果",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": ["subtask-1"]
                },
                {
                    "id": "subtask-3",
                    "name": "测试用例设计",
                    "description": "设计测试用例框架和结构",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-3.1",
                            "description": "设计测试用例框架",
                            "tools": ["create_chat_completion"],
                            "expected_output": "测试用例框架",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": ["subtask-2"]
                },
                {
                    "id": "subtask-4",
                    "name": "生成测试用例",
                    "description": "生成详细的测试用例",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-4.1",
                            "description": "生成功能测试用例",
                            "tools": ["test_case_generator", "create_chat_completion"],
                            "expected_output": "功能测试用例",
                            "status": "待执行"
                        },
                        {
                            "id": "step-4.2",
                            "description": "生成安全测试用例",
                            "tools": ["test_case_generator", "create_chat_completion"],
                            "expected_output": "安全测试用例",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": ["subtask-3"]
                },
                {
                    "id": "subtask-5",
                    "name": "测试覆盖率评估",
                    "description": "评估测试用例覆盖率",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-5.1",
                            "description": "评估测试覆盖率",
                            "tools": ["create_chat_completion"],
                            "expected_output": "测试覆盖率评估结果",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": ["subtask-4"]
                },
                {
                    "id": "subtask-6",
                    "name": "生成测试报告",
                    "description": "生成测试报告模板",
                    "status": "待执行",
                    "steps": [
                        {
                            "id": "step-6.1",
                            "description": "生成测试报告模板",
                            "tools": ["create_chat_completion", "file_operator"],
                            "expected_output": "测试报告模板",
                            "status": "待执行"
                        }
                    ],
                    "dependencies": ["subtask-5"]
                }
            ]
        }
        
        return plan
    
    def _get_tools_description(self) -> str:
        """获取可用工具的描述列表
        
        Returns:
            str: 格式化的工具描述列表
        """
        tool_descriptions = []
        for tool in self.available_tools.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    async def _enrich_with_templates(self, test_case_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用模板丰富测试用例
        
        Args:
            test_case_result: 基础测试用例结果
            
        Returns:
            List[Dict[str, Any]]: 丰富后的测试用例列表
        """
        enriched_cases = []
        threat_name = test_case_result.get("threat_name", "").lower()
        test_cases = test_case_result.get("test_cases", [])
        
        for test_case in test_cases:
            # 查找匹配的模板
            template = None
            for key, tmpl in self.test_templates.items():
                if key.lower() in threat_name:
                    template = tmpl
                    break
            
            # 如果找到匹配的模板，使用模板丰富测试用例
            if template:
                test_case["template"] = template.format(test_id=test_case.get("id", "unknown"))
            
            enriched_cases.append(test_case)
        
        return enriched_cases
    
    
    
    async def analyze_coverage(self, test_cases: List[Dict[str, Any]], threats: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析测试用例覆盖率
        
        Args:
            test_cases: 测试用例列表
            threats: 威胁列表
            
        Returns:
            Dict[str, float]: 覆盖率指标
        """
        # 计算威胁覆盖率
        threat_ids = set(t.get("id") for t in threats)
        covered_threats = set()
        
        for test_case in test_cases:
            threat_id = test_case.get("threat_id")
            if threat_id and threat_id in threat_ids:
                covered_threats.add(threat_id)
        
        threat_coverage = len(covered_threats) / len(threat_ids) if threat_ids else 0
        
        # 分析测试类型覆盖率
        test_types = ["功能测试", "安全测试", "边界测试", "异常测试", "渗透测试"]
        covered_types = {test_type: 0 for test_type in test_types}
        
        for test_case in test_cases:
            content = test_case.get("content", "")
            for test_type in test_types:
                if test_type in content:
                    covered_types[test_type] += 1
        
        type_coverage = sum(1 for count in covered_types.values() if count > 0) / len(test_types)
        
        # 更新覆盖率指标
        self.coverage_metrics = {
            "threat_coverage": threat_coverage,
            "type_coverage": type_coverage,
            "overall_coverage": (threat_coverage + type_coverage) / 2
        }
        
        return self.coverage_metrics

    async def _execute_subtasks(self) -> str:
        """执行所有子任务
        
        按照依赖关系顺序执行子任务，处理子任务间的依赖关系。
        
        Returns:
            str: 所有子任务执行的汇总结果
        """
        if not hasattr(self, 'subtasks') or not self.subtasks:
            return "没有可执行的子任务"
            
        logger.info(f"开始执行子任务序列，共 {len(self.subtasks)} 个子任务")
        
        # 初始化已完成的子任务集合
        if not hasattr(self, 'completed_subtasks'):
            self.completed_subtasks = set()
        else:
            self.completed_subtasks = set(self.completed_subtasks)
        
        results = []
        
        # 创建子任务状态映射
        subtask_status = {}
        for subtask in self.subtasks:
            subtask_id = subtask.get('id')
            if not subtask_id:
                continue
                
            if subtask_id in self.completed_subtasks:
                subtask_status[subtask_id] = 'completed'
                subtask['status'] = 'completed'
            else:
                subtask_status[subtask_id] = 'pending'
                subtask['status'] = 'pending'
        
        # 继续执行直到所有子任务完成或无法继续
        max_iterations = 2 * len(self.subtasks)  # 防止无限循环
        iterations = 0
        
        while len(self.completed_subtasks) < len(self.subtasks) and iterations < max_iterations:
            iterations += 1
            progress_made = False
            
            # 找出所有可执行的子任务（依赖已满足）
            executable_subtasks = []
            for subtask in self.subtasks:
                subtask_id = subtask.get('id')
                
                # 跳过已完成的子任务
                if subtask_id in self.completed_subtasks:
                    continue
                
                # 检查依赖是否满足
                dependencies = subtask.get('dependencies', [])
                dependencies_met = all(dep in self.completed_subtasks for dep in dependencies)
                
                if dependencies_met:
                    executable_subtasks.append(subtask)
            
            # 如果没有可执行的子任务，但仍有未完成的子任务，可能存在循环依赖
            if not executable_subtasks and len(self.completed_subtasks) < len(self.subtasks):
                logger.warning("检测到可能的循环依赖，无法继续执行子任务")
                break
            
            # 执行可执行的子任务
            for subtask in executable_subtasks:
                subtask_id = subtask.get('id')
                logger.info(f"开始执行子任务: {subtask.get('name')} (ID: {subtask_id})")
                
                subtask['status'] = 'in_progress'
                subtask_status[subtask_id] = 'in_progress'
                subtask['start_time'] = datetime.now().isoformat()
                
                # 记录当前正在执行的子任务ID，用于保持一致性
                self._current_subtask_id = subtask_id
                
                try:
                    # 执行子任务的所有步骤
                    subtask_result = await self._execute_steps(subtask)
                    subtask['result'] = subtask_result
                    subtask['status'] = 'completed'
                    subtask_status[subtask_id] = 'completed'
                    self.completed_subtasks.add(subtask_id)
                    progress_made = True
                    results.append(subtask_result)
                    
                    logger.info(f"子任务 {subtask_id} 执行完成")
                except Exception as e:
                    subtask['status'] = 'failed'
                    subtask_status[subtask_id] = 'failed'
                    logger.error(f"子任务 {subtask_id} 执行失败: {str(e)}")
                    results.append(f"子任务 {subtask_id} 执行失败: {str(e)}")
                
                subtask['end_time'] = datetime.now().isoformat()
            
            # 如果本轮没有进展，说明存在循环依赖或所有剩余任务都无法执行
            if not progress_made:
                logger.warning("无法继续执行子任务，可能存在循环依赖或所有剩余任务都无法执行")
                break
        
        # 汇总结果
        final_result = "\n\n".join(results)
        logger.info(f"所有子任务执行完成，共 {len(self.completed_subtasks)}/{len(self.subtasks)} 个子任务成功执行")
        
        return final_result
    
    async def _execute_steps(self, subtask: Dict[str, Any]) -> str:
        """执行子任务的所有步骤
        
        Args:
            subtask: 子任务信息
            
        Returns:
            str: 子任务执行结果
        """
        steps = subtask.get('steps', [])
        if not steps:
            return f"子任务 {subtask.get('name')} 没有定义步骤"
            
        results = []
        
        for step in steps:
            step_id = step.get('id')
            description = step.get('description', '未描述')
            
            logger.info(f"执行步骤: {description} (ID: {step_id})")
            
            # 标记步骤为执行中
            step['status'] = 'in_progress'
            step['start_time'] = datetime.now().isoformat()
            
            try:
                # 获取步骤指定的工具
                tools = step.get('tools', [])
                
                if not tools:
                    # 如果没有指定工具，使用create_chat_completion
                    tools = ["create_chat_completion"]
                
                # 构建执行步骤的提示
                prompt = self._build_step_execution_prompt(subtask, step)
                
                # 执行步骤
                response = await self.llm.ask(
                    messages=[
                        {"role": "system", "content": "你是车联网安全测试专家，正在执行测试用例生成流程中的特定步骤。"},
                        {"role": "user", "content": prompt}
                    ],
                    tools=self._prepare_tools_for_llm(tools),
                    tool_choice="auto"
                )
                
                # 处理执行结果
                step_result = ""
                if isinstance(response, str):
                    # 文本结果
                    step_result = response
                elif isinstance(response, dict):
                    # 可能包含工具调用或内容
                    if "content" in response and response["content"]:
                        step_result = response.get("content", "")
                    elif "tool_calls" in response:
                        # 处理工具调用
                        await self._process_tool_calls(response["tool_calls"])
                        # 添加工具调用结果
                        tool_result_msgs = [m for m in self.memory.get_messages() if m.get("role") == "tool"]
                        if tool_result_msgs:
                            step_result = "工具调用结果: " + ", ".join([m.get("content", "") for m in tool_result_msgs[-len(response["tool_calls"]):]])
                        else:
                            step_result = "执行了工具调用，但没有结果"
                else:
                    # 其他格式，转换为字符串
                    step_result = str(response)
                
                # 记录步骤结果
                step['result'] = step_result
                step['status'] = 'completed'
                results.append(f"步骤 {step_id}: {description}\n结果: {step_result}")
                
            except Exception as e:
                logger.error(f"执行步骤 {step_id} 时出错: {str(e)}")
                step['status'] = 'failed'
                step['error'] = str(e)
                results.append(f"步骤 {step_id}: {description} 执行失败: {str(e)}")
                # 继续执行其他步骤，而不是中断
            
            step['end_time'] = datetime.now().isoformat()
            
        # 返回所有步骤的结果
        return "\n\n".join(results)
    
    def _build_step_execution_prompt(self, subtask: Dict[str, Any], step: Dict[str, Any]) -> str:
        """构建执行步骤的提示
        
        Args:
            subtask: 子任务信息
            step: 步骤信息
            
        Returns:
            str: 提示内容
        """
        # 获取已完成步骤的结果，作为上下文
        context = []
        subtask_steps = subtask.get('steps', [])
        for prev_step in subtask_steps:
            if prev_step.get('id') == step.get('id'):
                # 当前步骤，跳过
                break
                
            if prev_step.get('status') in ['completed', '已完成']:
                # 添加已完成步骤的结果
                prev_result = prev_step.get('result', '无结果')
                context.append(f"步骤 {prev_step.get('id')}: {prev_step.get('description')}\n结果: {prev_result}")
        
        # 如果有依赖子任务，也添加其结果作为上下文
        dependencies = subtask.get('dependencies', [])
        dependency_results = []
        if dependencies and self.subtasks:
            for dep_id in dependencies:
                dep_task = next((t for t in self.subtasks if t.get('id') == dep_id), None)
                if dep_task and dep_task.get('status') in ['completed', '已完成'] and 'result' in dep_task:
                    dependency_results.append(f"依赖任务 {dep_task.get('name')} 的结果:\n{dep_task.get('result')}")
        
        # 构建提示
        prompt = f"""
        # 当前执行步骤
        {step.get('description')}
        
        # 子任务信息
        {subtask.get('name')}: {subtask.get('description')}
        
        # 预期输出
        {step.get('expected_output', '未指定')}
        
        # 可用工具
        {', '.join(step.get('tools', ['create_chat_completion']))}
        """
        
        # 添加上下文（如果有）
        if context:
            prompt += f"\n\n# 先前步骤的结果\n" + "\n\n".join(context)
            
        if dependency_results:
            prompt += f"\n\n# 依赖任务的结果\n" + "\n\n".join(dependency_results)
            
        # 添加执行指导
        prompt += """
        
        # 执行说明
        请根据上述信息执行当前步骤，并确保输出符合预期。如果需要使用工具，请直接调用工具而不要描述调用过程。
        输出应该是结构化的、清晰的，并符合测试用例生成的专业要求。
        """
        
        return prompt
        
    def _prepare_tools_for_llm(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """准备用于LLM的工具列表
        
        Args:
            tool_names: 工具名称列表
            
        Returns:
            List[Dict[str, Any]]: 工具定义列表
        """
        tools = []
        for name in tool_names:
            tool = self.available_tools.get_tool(name)
            if tool and hasattr(tool, 'to_llm_tool'):
                tools.append(tool.to_llm_tool())
        
        return tools