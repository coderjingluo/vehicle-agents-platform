"""
测试用例智能体 - 基于TARA分析结果生成测试用例

该智能体具备以下核心能力：
1. 基于TARA分析结果智能生成测试用例
2. 支持确认测试(Confirmation Test)和验证测试(Validation Test)
3. 测试覆盖率分析和优化
4. 测试用例分类和优先级管理
5. 支持多种测试标准和框架
"""

from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentStep, AgentPlan
from app.models.task import AgentType


class TestCaseAgent(BaseAgent):
    """测试用例智能体"""
    
    def __init__(self):
        super().__init__()
        self.agent_type = AgentType.TEST_CASE
        self.test_standards = {
            "ISO_21434": "道路车辆网络安全工程",
            "SAE_J3061": "车联网安全指南",
            "UNECE_WP29": "车辆网络安全法规",
            "ISO_26262": "道路车辆功能安全",
            "GB_T_40857": "汽车网络安全技术要求"
        }
        
    def get_agent_type(self) -> str:
        return "test_case"
    
    async def _generate_plan(self, user_request: str, context: Dict[str, Any] = None) -> AgentPlan:
        """基于TARA结果生成测试用例计划"""
        
        planning_prompt = f"""
作为车联网安全测试用例专家，请基于用户请求和TARA分析结果，生成详细的测试用例开发计划。

用户请求: {user_request}
上下文信息: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

请生成包含以下步骤的执行计划：

1. **TARA结果分析**: 分析威胁和风险评估结果
2. **测试策略制定**: 确定测试类型和覆盖范围
3. **测试用例设计**: 设计具体的测试用例
4. **测试数据准备**: 准备测试所需的数据和环境
5. **测试执行计划**: 制定测试执行顺序和时间安排
6. **验证标准确认**: 确认测试通过标准和验收条件

对于每个步骤，请提供：
- 步骤名称和描述
- 所需工具
- 预期输出
- 成功标准

以JSON格式返回计划。
"""
        
        try:
            response = await self.llm_manager.generate_response(
                planning_prompt,
                context={"agent_type": "test_case", "task": "planning"}
            )
            
            plan_data = self._parse_json_response(response)
            
            steps = []
            if "steps" in plan_data:
                for step_data in plan_data["steps"]:
                    step = AgentStep(
                        id=str(uuid.uuid4()),
                        name=step_data.get("name", "Unknown Step"),
                        description=step_data.get("description", ""),
                        tool_calls=step_data.get("tools", []),
                        expected_output=step_data.get("expected_output", ""),
                        success_criteria=step_data.get("success_criteria", ""),
                        status="pending"
                    )
                    steps.append(step)
            
            return AgentPlan(
                id=str(uuid.uuid4()),
                agent_type=self.agent_type,
                description=plan_data.get("description", "测试用例生成计划"),
                steps=steps,
                estimated_duration=plan_data.get("estimated_duration", 30),
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"生成测试用例计划失败: {e}")
            # 返回默认计划
            return self._get_default_plan()
    
    def _get_default_plan(self) -> AgentPlan:
        """获取默认的测试用例生成计划"""
        default_steps = [
            AgentStep(
                id=str(uuid.uuid4()),
                name="TARA结果分析",
                description="分析威胁和风险评估结果，识别需要测试的安全威胁",
                tool_calls=["tara_analyzer"],
                expected_output="威胁清单和风险等级分析",
                success_criteria="成功识别所有高危威胁",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试策略制定",
                description="基于威胁分析结果制定测试策略和方法",
                tool_calls=["test_strategy_generator"],
                expected_output="测试策略文档",
                success_criteria="覆盖所有识别的威胁",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试用例设计",
                description="设计具体的测试用例，包括确认测试和验证测试",
                tool_calls=["test_case_designer"],
                expected_output="详细的测试用例文档",
                success_criteria="测试用例完整且可执行",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试覆盖率验证",
                description="验证测试用例的覆盖率是否满足要求",
                tool_calls=["coverage_analyzer"],
                expected_output="测试覆盖率报告",
                success_criteria="覆盖率达到90%以上",
                status="pending"
            )
        ]
        
        return AgentPlan(
            id=str(uuid.uuid4()),
            agent_type=self.agent_type,
            description="标准测试用例生成流程",
            steps=default_steps,
            estimated_duration=25,
            created_at=datetime.utcnow()
        )
    
    async def execute_step(self, step: AgentStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行具体的测试用例生成步骤"""
        try:
            self.logger.info(f"执行测试用例生成步骤: {step.name}")
            
            # 根据步骤名称执行相应的操作
            if "TARA" in step.name or "威胁" in step.name:
                return await self._analyze_tara_results(step, context)
            elif "策略" in step.name:
                return await self._generate_test_strategy(step, context)
            elif "设计" in step.name or "用例" in step.name:
                return await self._design_test_cases(step, context)
            elif "覆盖率" in step.name:
                return await self._analyze_coverage(step, context)
            else:
                return await self._execute_general_step(step, context)
                
        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_tara_results(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析TARA结果"""
        prompt = f"""
作为安全测试专家，请分析以下TARA结果，提取需要进行测试验证的威胁和风险点。

TARA分析结果:
{json.dumps(context.get('tara_result', {}), ensure_ascii=False, indent=2)}

请提供：
1. 高危威胁清单 (风险等级 >= 7)
2. 中危威胁清单 (风险等级 4-6)
3. 每个威胁的具体测试需求
4. 推荐的测试类型 (确认测试/验证测试)
5. 测试优先级排序

以JSON格式返回分析结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "test_case"}
        )
        
        analysis_result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": analysis_result,
            "step_id": step.id,
            "analysis_type": "tara_analysis",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_test_strategy(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试策略"""
        prompt = f"""
基于威胁分析结果，制定comprehensive的安全测试策略。

威胁分析结果:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请制定包含以下内容的测试策略：

1. **测试目标和范围**
   - 明确测试边界和目标
   - 定义测试的系统组件

2. **测试方法分类**
   - 静态安全测试 (SAST)
   - 动态安全测试 (DAST)
   - 交互式安全测试 (IAST)
   - 渗透测试
   - 模糊测试 (Fuzzing)

3. **测试环境要求**
   - 测试环境配置
   - 工具和设备需求
   - 网络环境模拟

4. **测试数据准备**
   - 正常数据集
   - 异常数据集
   - 恶意输入数据

5. **测试执行计划**
   - 测试顺序和依赖关系
   - 时间安排和里程碑
   - 资源分配

符合以下标准：
- ISO 21434 (网络安全工程)
- SAE J3061 (车联网安全)
- ISO 26262 (功能安全)

以JSON格式返回测试策略。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "test_case"}
        )
        
        strategy_result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": strategy_result,
            "step_id": step.id,
            "strategy_type": "comprehensive_security_testing",
            "standards_compliance": ["ISO_21434", "SAE_J3061", "ISO_26262"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _design_test_cases(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """设计具体的测试用例"""
        prompt = f"""
作为资深安全测试工程师，基于测试策略设计详细的测试用例。

测试策略:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

为每个威胁设计测试用例，包含：

1. **确认测试 (Confirmation Tests)**
   - 测试用例ID和名称
   - 测试目的和描述
   - 前置条件
   - 测试步骤 (详细的操作步骤)
   - 预期结果
   - 通过/失败标准
   - 风险等级

2. **验证测试 (Validation Tests)**
   - 功能验证测试
   - 性能验证测试
   - 安全控制验证
   - 边界条件测试

3. **专项安全测试**
   - 认证绕过测试
   - 授权提升测试
   - 数据泄露测试
   - 注入攻击测试
   - 拒绝服务测试

4. **测试用例分类**
   - 优先级 (P0-P3)
   - 测试类型 (功能/安全/性能)
   - 自动化可行性
   - 执行频率

每个测试用例应该：
- 可独立执行
- 结果可验证
- 支持自动化
- 符合标准要求

以JSON格式返回测试用例设计。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "test_case"}
        )
        
        test_cases = self._parse_json_response(response)
        
        # 添加测试用例统计信息
        statistics = self._calculate_test_statistics(test_cases)
        
        return {
            "success": True,
            "result": test_cases,
            "statistics": statistics,
            "step_id": step.id,
            "test_case_count": len(test_cases.get("test_cases", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_coverage(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试覆盖率"""
        prompt = f"""
分析当前测试用例的覆盖率，确保满足安全测试要求。

测试用例设计:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请分析以下覆盖率维度：

1. **威胁覆盖率**
   - 已覆盖的威胁数量/总威胁数量
   - 未覆盖威胁的风险评估
   - 覆盖率缺口分析

2. **功能覆盖率**
   - 系统组件覆盖率
   - 接口覆盖率
   - 数据流覆盖率

3. **测试方法覆盖率**
   - 静态测试覆盖率
   - 动态测试覆盖率
   - 渗透测试覆盖率

4. **合规性覆盖率**
   - ISO 21434 要求覆盖率
   - SAE J3061 要求覆盖率
   - 其他标准覆盖率

5. **风险等级覆盖率**
   - 高危风险覆盖率 (目标: 100%)
   - 中危风险覆盖率 (目标: 90%)
   - 低危风险覆盖率 (目标: 70%)

提供：
- 当前覆盖率状态
- 覆盖率缺口
- 改进建议
- 补充测试用例建议

以JSON格式返回覆盖率分析。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "test_case"}
        )
        
        coverage_analysis = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": coverage_analysis,
            "step_id": step.id,
            "analysis_type": "coverage_analysis",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_test_statistics(self, test_cases: Dict[str, Any]) -> Dict[str, Any]:
        """计算测试用例统计信息"""
        try:
            cases = test_cases.get("test_cases", [])
            if not cases:
                return {"total": 0}
            
            # 统计不同类型的测试用例
            stats = {
                "total": len(cases),
                "by_priority": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
                "by_type": {"confirmation": 0, "validation": 0, "security": 0},
                "by_automation": {"automated": 0, "manual": 0},
                "by_risk_level": {"high": 0, "medium": 0, "low": 0}
            }
            
            for case in cases:
                # 优先级统计
                priority = case.get("priority", "P2")
                if priority in stats["by_priority"]:
                    stats["by_priority"][priority] += 1
                
                # 类型统计
                test_type = case.get("type", "").lower()
                if "confirmation" in test_type:
                    stats["by_type"]["confirmation"] += 1
                elif "validation" in test_type:
                    stats["by_type"]["validation"] += 1
                elif "security" in test_type:
                    stats["by_type"]["security"] += 1
                
                # 自动化统计
                automation = case.get("automation_feasible", False)
                if automation:
                    stats["by_automation"]["automated"] += 1
                else:
                    stats["by_automation"]["manual"] += 1
                
                # 风险等级统计
                risk_level = case.get("risk_level", "medium").lower()
                if risk_level in stats["by_risk_level"]:
                    stats["by_risk_level"][risk_level] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算测试统计信息失败: {e}")
            return {"total": 0, "error": str(e)}
    
    async def _execute_general_step(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用步骤"""
        prompt = f"""
作为车联网安全测试专家，执行以下测试用例生成任务：

任务描述: {step.description}
预期输出: {step.expected_output}
成功标准: {step.success_criteria}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

请提供详细的执行结果，包括：
1. 执行过程说明
2. 具体输出内容
3. 质量评估
4. 改进建议

以JSON格式返回结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "test_case"}
        )
        
        result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": result,
            "step_id": step.id,
            "execution_type": "general",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            # 如果JSON解析失败，返回包含原始响应的结构
            return {
                "raw_response": response,
                "parsed": False,
                "error": "Failed to parse JSON response"
            } 