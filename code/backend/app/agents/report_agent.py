"""
报告分析智能体 - 综合分析测试结果并生成专业报告

该智能体具备以下核心能力：
1. 综合分析TARA、测试用例、自动化测试结果
2. 生成专业的安全测试报告
3. 风险评估和优先级排序
4. 修复建议和缓解措施
5. 合规性评估和认证支持
"""

from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentStep, AgentPlan
from app.models.task import AgentType


class ReportAgent(BaseAgent):
    """报告分析智能体"""
    
    def __init__(self):
        agent_id = str(uuid.uuid4())
        super().__init__(
            agent_id=agent_id,
            name="报告分析智能体",
            description="综合分析测试结果并生成专业报告"
        )
        self.agent_type = AgentType.REPORT_ANALYSIS
        self.report_standards = {
            "ISO_21434": "道路车辆网络安全工程报告",
            "SAE_J3061": "车联网安全评估报告",
            "UNECE_WP29": "车辆网络安全合规报告",
            "NIST_CSF": "网络安全框架评估报告",
            "ISO_27001": "信息安全管理体系审计报告"
        }
        self.risk_levels = {
            "critical": {"score": 9-10, "color": "red", "action": "立即修复"},
            "high": {"score": 7-8, "color": "orange", "action": "优先修复"},
            "medium": {"score": 4-6, "color": "yellow", "action": "计划修复"},
            "low": {"score": 1-3, "color": "green", "action": "监控观察"}
        }
        
    def get_agent_type(self) -> str:
        return "report_analysis"
    
    async def _generate_plan(self, user_request: str, context: Dict[str, Any] = None) -> AgentPlan:
        """生成报告分析计划"""
        default_steps = [
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="数据收集整理",
                description="收集并整理TARA分析、测试用例、自动化测试等所有相关数据",
                tool_name="data_collector",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="风险评估分析",
                description="基于测试结果进行综合风险评估和优先级排序",
                tool_name="risk_analyzer",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="合规性检查",
                description="检查测试结果是否符合相关标准和法规要求",
                tool_name="compliance_checker",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="修复建议生成",
                description="基于发现的问题生成具体的修复建议和缓解措施",
                tool_name="fix_recommender",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="报告生成",
                description="生成完整的专业安全测试报告",
                tool_name="report_generator",
                parameters={},
                dependencies=[]
            )
        ]
        
        return AgentPlan(
            plan_id=str(uuid.uuid4()),
            description="安全测试报告生成流程",
            steps=default_steps
        )
    
    async def execute_step(self, step: AgentStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行报告分析步骤"""
        try:
            self.logger.info(f"执行报告分析步骤: {step.name}")
            
            if "收集" in step.name or "数据" in step.name:
                return await self._collect_data(step, context)
            elif "风险" in step.name or "评估" in step.name:
                return await self._analyze_risks(step, context)
            elif "合规" in step.name:
                return await self._check_compliance(step, context)
            elif "修复" in step.name or "建议" in step.name:
                return await self._generate_recommendations(step, context)
            elif "报告" in step.name:
                return await self._generate_report(step, context)
            else:
                return await self._execute_general_step(step, context)
                
        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.step_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _collect_data(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """收集和整理测试数据"""
        prompt = f"""
作为安全分析专家，请收集并整理所有相关的测试数据。

可用数据源:
{json.dumps(context, ensure_ascii=False, indent=2)}

请整理以下数据：

1. **TARA分析结果**
   - 识别的威胁列表
   - 风险评估结果
   - 缓解措施建议

2. **测试用例执行结果**
   - 测试用例总数和执行状态
   - 通过/失败的测试用例
   - 覆盖率统计

3. **自动化测试结果**
   - 自动化脚本执行结果
   - 发现的漏洞和问题
   - 性能测试指标

4. **系统信息**
   - 测试目标系统描述
   - 测试环境配置
   - 测试时间和范围

5. **数据质量检查**
   - 数据完整性验证
   - 数据一致性检查
   - 缺失数据识别

以JSON格式返回整理后的数据集合。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        data_collection = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": data_collection,
            "step_id": step.step_id,
            "data_sources": list(context.keys()) if context else [],
            "collection_type": "comprehensive_data",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_risks(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险和威胁"""
        prompt = f"""
作为资深安全专家，基于收集的测试数据进行综合风险分析。

测试数据:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请进行全面的风险分析：

1. **威胁识别和分类**
   - 高危威胁 (风险分数: 8-10)
   - 中危威胁 (风险分数: 5-7)
   - 低危威胁 (风险分数: 1-4)

2. **风险评估矩阵**
   ```
   影响程度 vs 发生概率
   高影响-高概率: 关键风险
   高影响-低概率: 重要风险
   低影响-高概率: 一般风险
   低影响-低概率: 可接受风险
   ```

3. **业务影响评估**
   - 数据泄露风险
   - 服务中断风险
   - 合规性风险
   - 声誉损害风险

4. **技术风险分析**
   - 认证和授权风险
   - 数据传输风险
   - 存储安全风险
   - 接口安全风险

5. **风险优先级排序**
   - 修复优先级 (P0-P3)
   - 预计修复时间
   - 所需资源评估

6. **残留风险评估**
   - 当前缓解措施效果
   - 剩余风险水平
   - 可接受风险阈值

以JSON格式返回风险分析结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        risk_analysis = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": risk_analysis,
            "step_id": step.step_id,
            "analysis_type": "comprehensive_risk_assessment",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_compliance(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """检查合规性"""
        prompt = f"""
作为合规性专家，检查测试结果是否符合相关标准和法规要求。

风险分析结果:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请进行合规性评估：

1. **ISO 21434 合规性检查**
   - 网络安全工程生命周期要求
   - 风险评估和管理要求
   - 事件响应计划要求
   - 供应链安全要求

2. **SAE J3061 合规性检查**
   - 车联网安全指导原则
   - 安全架构设计要求
   - 威胁建模要求
   - 安全验证要求

3. **UNECE WP.29 合规性检查**
   - 车辆网络安全管理系统
   - 风险评估程序
   - 监控和响应程序
   - 型式认证要求

4. **NIST网络安全框架**
   - 识别(Identify)功能
   - 保护(Protect)功能
   - 检测(Detect)功能
   - 响应(Respond)功能
   - 恢复(Recover)功能

5. **合规性差距分析**
   - 不符合项识别
   - 差距严重程度评估
   - 合规性改进建议
   - 认证准备建议

6. **法规要求映射**
   - 强制性要求vs推荐性要求
   - 适用地区和市场
   - 合规时间要求

以JSON格式返回合规性评估报告。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        compliance_check = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": compliance_check,
            "step_id": step.step_id,
            "standards_checked": ["ISO_21434", "SAE_J3061", "UNECE_WP29", "NIST_CSF"],
            "check_type": "multi_standard_compliance",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_recommendations(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成修复建议"""
        prompt = f"""
作为安全咨询专家，基于风险分析和合规性检查结果，生成具体的修复建议。

合规性检查结果:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请提供详细的修复建议：

1. **关键问题修复建议**
   - 问题描述和影响
   - 具体修复步骤
   - 实施时间估算
   - 所需技术资源

2. **安全控制措施**
   - 技术控制措施
   - 管理控制措施
   - 物理控制措施
   - 人员控制措施

3. **实施优先级**
   - P0: 立即修复 (1周内)
   - P1: 高优先级 (1月内)
   - P2: 中优先级 (3月内)
   - P3: 低优先级 (6月内)

4. **缓解措施建议**
   - 临时缓解措施
   - 永久性解决方案
   - 补偿性控制
   - 监控和检测

5. **成本效益分析**
   - 修复成本估算
   - 风险降低收益
   - ROI评估
   - 投资建议

6. **实施路线图**
   - 短期目标 (1-3月)
   - 中期目标 (3-12月)
   - 长期目标 (1-3年)
   - 里程碑设置

7. **验证和测试计划**
   - 修复效果验证
   - 回归测试计划
   - 持续监控方案

以JSON格式返回修复建议和实施计划。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        recommendations = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": recommendations,
            "step_id": step.step_id,
            "recommendation_type": "comprehensive_remediation",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_report(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终报告"""
        prompt = f"""
作为报告撰写专家，基于所有分析结果生成完整的专业安全测试报告。

修复建议:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请生成结构化的安全测试报告：

## 1. 执行摘要
- 测试概述和目标
- 主要发现和结论
- 关键风险和建议
- 管理层决策建议

## 2. 测试范围和方法
- 测试目标系统
- 测试方法和工具
- 测试时间和范围
- 限制条件说明

## 3. 威胁和风险分析
- TARA分析结果
- 威胁建模发现
- 风险评估矩阵
- 业务影响分析

## 4. 测试结果详述
- 测试用例执行结果
- 自动化测试发现
- 漏洞详细描述
- 安全控制评估

## 5. 合规性评估
- 标准符合性检查
- 差距分析
- 认证准备状态
- 法规要求映射

## 6. 修复建议
- 优先级修复计划
- 具体实施步骤
- 资源需求评估
- 时间线规划

## 7. 风险缓解策略
- 短期缓解措施
- 长期解决方案
- 监控和检测
- 事件响应计划

## 8. 附录
- 技术详细信息
- 测试数据统计
- 工具和方法说明
- 参考标准和法规

报告应该：
- 内容准确、客观
- 结构清晰、逻辑性强
- 语言专业、易懂
- 图表丰富、可视化好
- 结论明确、建议可行

以JSON格式返回完整的结构化报告。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        final_report = self._parse_json_response(response)
        
        # 添加报告元数据
        report_metadata = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "security_assessment",
            "standards_compliance": ["ISO_21434", "SAE_J3061", "UNECE_WP29"],
            "report_version": "1.0",
            "confidentiality": "Confidential"
        }
        
        return {
            "success": True,
            "result": final_report,
            "metadata": report_metadata,
            "step_id": step.step_id,
            "report_sections": 8,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_general_step(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用步骤"""
        prompt = f"""
作为安全报告分析专家，执行以下任务：

任务描述: {step.description}
预期输出: {step.expected_output}
成功标准: {step.success_criteria}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

以JSON格式返回结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "report_analysis"}
        )
        
        result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": result,
            "step_id": step.step_id,
            "execution_type": "general",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "raw_response": response,
                "parsed": False,
                "error": "Failed to parse JSON response"
            } 