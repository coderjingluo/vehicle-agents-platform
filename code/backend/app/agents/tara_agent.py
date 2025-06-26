"""
TARA智能体
威胁分析和风险评估智能体，使用LangGraph工作流
"""

from typing import Any, Dict, List, Optional
import json
import uuid
from datetime import datetime

from .base_agent import BaseAgent, AgentStep, AgentPlan
from app.core.llm_client import LLMClientManager
from app.core.tool_registry import ToolRegistry
from loguru import logger


class TARAAgent(BaseAgent):
    """威胁分析和风险评估智能体"""
    
    def __init__(
        self,
        llm_manager: Optional[LLMClientManager] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        super().__init__(
            agent_id="tara_001",
            name="TARA智能体",
            description="专业的威胁分析和风险评估智能体，基于车联网安全标准进行分析",
            llm_manager=llm_manager,
            tool_registry=tool_registry
        )
        self.logger = logger
    
    def get_agent_type(self) -> str:
        """获取智能体类型"""
        return "tara"
    
    async def _generate_plan(self, user_request: str, context: Dict[str, Any] = None) -> AgentPlan:
        """生成TARA分析计划"""
        default_steps = [
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="资产识别",
                description="识别需要保护的关键资产",
                tool_name="asset_analyzer",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="威胁分析",
                description="分析可能的威胁和攻击向量",
                tool_name="threat_analyzer",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="风险评估",
                description="评估每个威胁的风险等级",
                tool_name="risk_analyzer",
                parameters={},
                dependencies=[]
            ),
            AgentStep(
                step_id=str(uuid.uuid4()),
                name="缓解建议",
                description="生成缓解措施建议",
                tool_name="mitigation_recommender",
                parameters={},
                dependencies=[]
            )
        ]
        
        return AgentPlan(
            plan_id=str(uuid.uuid4()),
            description="TARA分析计划",
            steps=default_steps
        )
    
    async def execute_step(self, step: AgentStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行TARA分析步骤"""
        try:
            self.logger.info(f"执行TARA分析步骤: {step.name}")
            
            # 执行相应的步骤
            if "资产" in step.name:
                return await self._analyze_assets(context)
            elif "威胁" in step.name:
                return await self._analyze_threats(context)
            elif "风险" in step.name:
                return await self._analyze_risks(context)
            elif "缓解" in step.name:
                return await self._generate_mitigations(context)
            else:
                return {"success": False, "error": f"未知步骤: {step.name}"}
                
        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.step_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_assets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析系统资产"""
        system_prompt = self._build_tara_system_prompt()
        user_prompt = f"""
请识别以下系统的关键资产:

系统描述: {context.get('user_request', '车联网系统')}
详细信息: {json.dumps(context.get('context', {}), ensure_ascii=False, indent=2)}

请提供:
1. 资产列表
2. 资产分类
3. 资产重要性评级
4. 保护需求

以JSON格式返回结果。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_manager.generate_response(messages)
        assets_result = self._parse_tara_response(response)
        
        return {
            "success": True,
            "result": assets_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_threats(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析威胁"""
        assets = context.get('previous_results', {}).get('资产识别', {})
        
        system_prompt = self._build_tara_system_prompt()
        user_prompt = f"""
基于以下资产信息，分析可能的威胁:

资产信息: {json.dumps(assets, ensure_ascii=False, indent=2)}
系统描述: {context.get('user_request', '车联网系统')}

请使用STRIDE方法分析威胁:
- Spoofing (欺骗)
- Tampering (篡改)
- Repudiation (抵赖)
- Information Disclosure (信息泄露)
- Denial of Service (拒绝服务)
- Elevation of Privilege (权限提升)

对每个威胁，提供:
1. 威胁ID和名称
2. 威胁类别(STRIDE)
3. 详细描述
4. 可能的攻击向量
5. 受影响资产

以JSON格式返回结果。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_manager.generate_response(messages)
        threats_result = self._parse_tara_response(response)
        
        return {
            "success": True,
            "result": threats_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_risks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险等级"""
        previous_results = context.get('previous_results', {})
        threats = previous_results.get('威胁分析', {})
        
        system_prompt = self._build_tara_system_prompt()
        user_prompt = f"""
基于以下威胁信息，评估风险等级:

威胁信息: {json.dumps(threats, ensure_ascii=False, indent=2)}

对每个威胁，提供风险评估:
1. 风险等级(1-10)
2. 影响评估(安全、隐私、财务、操作)
3. 可能性评估
4. 风险评估理由

风险等级标准:
- 极高(9-10): 严重安全或隐私风险，可能导致生命危险或重大损失
- 高(7-8): 重要安全或业务功能受损，可能造成显著损失
- 中(4-6): 影响系统功能，但不会造成严重损失
- 低(1-3): 轻微影响，容易修复或规避

以JSON格式返回结果。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_manager.generate_response(messages)
        risks_result = self._parse_tara_response(response)
        
        return {
            "success": True,
            "result": risks_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_mitigations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成缓解措施建议"""
        previous_results = context.get('previous_results', {})
        threats = previous_results.get('威胁分析', {})
        risks = previous_results.get('风险评估', {})
        
        system_prompt = self._build_tara_system_prompt()
        user_prompt = f"""
基于以下威胁和风险信息，提供缓解措施建议:

威胁信息: {json.dumps(threats, ensure_ascii=False, indent=2)}
风险评估: {json.dumps(risks, ensure_ascii=False, indent=2)}

请提供:
1. 针对高风险威胁的优先缓解措施
2. 每个措施的实施难度和预期效果
3. 符合行业标准的安全控制建议
4. 测试和验证方法

以JSON格式返回结果。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm_manager.generate_response(messages)
        mitigations_result = self._parse_tara_response(response)
        
        return {
            "success": True,
            "result": mitigations_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def execute(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        plan_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行TARA分析"""
        
        try:
            # 构建TARA分析提示词
            system_prompt = self._build_tara_system_prompt()
            
            # 分析用户请求
            analysis_prompt = self._build_analysis_prompt(user_request, context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]
            
            # 调用LLM进行分析
            response = await self.llm_manager.generate_response(
                messages=messages,
                temperature=0.3,  # 使用较低温度确保一致性
                max_tokens=2000
            )
            
            # 解析分析结果
            tara_result = self._parse_tara_response(response)
            
            # 添加元数据
            tara_result.update({
                "agent_id": self.agent_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "context": context or {},
                "confidence_score": self._calculate_confidence_score(tara_result)
            })
            
            return tara_result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "agent_id": self.agent_id,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    def _build_tara_system_prompt(self) -> str:
        """构建TARA分析系统提示词"""
        return """
你是一个专业的车联网安全威胁分析和风险评估（TARA）专家。你需要根据以下标准和方法进行分析：

## 分析框架
1. **ISO 21434** - 道路车辆网络安全工程生命周期
2. **SAE J3061** - 车辆系统网络安全指南
3. **UNECE WP.29** - 车辆网络安全和软件更新法规

## 威胁分析方法
1. **资产识别** - 识别需要保护的关键资产
2. **威胁建模** - 使用STRIDE方法分析威胁
3. **攻击路径分析** - 分析可能的攻击向量
4. **影响评估** - 评估安全、隐私、财务和操作影响

## 风险评估标准
- **风险等级**: 极高(9-10) / 高(7-8) / 中(4-6) / 低(1-3)
- **影响维度**: 安全性、隐私性、财务损失、声誉影响
- **可能性评估**: 几乎确定 / 很可能 / 可能 / 不太可能 / 几乎不可能

## 输出格式
请以JSON格式返回分析结果，包含以下结构：
{
    "summary": "分析概要",
    "assets": [
        {
            "name": "资产名称",
            "type": "资产类型",
            "criticality": "关键程度",
            "description": "资产描述"
        }
    ],
    "threats": [
        {
            "id": "威胁ID",
            "name": "威胁名称",
            "category": "STRIDE分类",
            "description": "威胁描述",
            "attack_vectors": ["攻击向量列表"],
            "affected_assets": ["受影响的资产"],
            "likelihood": "可能性评估",
            "impact": {
                "safety": "安全影响",
                "privacy": "隐私影响", 
                "financial": "财务影响",
                "operational": "操作影响"
            }
        }
    ],
    "risks": [
        {
            "threat_id": "关联威胁ID",
            "risk_level": "风险等级",
            "risk_score": "风险分数(1-10)",
            "justification": "风险评估理由"
        }
    ],
    "recommendations": [
        {
            "priority": "优先级",
            "category": "建议类别",
            "description": "具体建议",
            "implementation_effort": "实施难度",
            "expected_impact": "预期效果"
        }
    ],
    "compliance_notes": "合规性说明"
}
"""
    
    def _build_analysis_prompt(self, user_request: str, context: Optional[Dict[str, Any]]) -> str:
        """构建分析提示词"""
        prompt = f"""
请对以下车联网系统进行威胁分析和风险评估（TARA）：

**分析目标**: {user_request}

**系统信息**:
"""
        
        if context:
            if context.get("system_description"):
                prompt += f"- 系统描述: {context['system_description']}\n"
            if context.get("components"):
                prompt += f"- 主要组件: {', '.join(context['components'])}\n"
            if context.get("interfaces"):
                prompt += f"- 外部接口: {', '.join(context['interfaces'])}\n"
            if context.get("data_types"):
                prompt += f"- 数据类型: {', '.join(context['data_types'])}\n"
            if context.get("security_requirements"):
                prompt += f"- 安全要求: {context['security_requirements']}\n"
        
        prompt += """
请按照车联网安全标准进行全面的TARA分析，重点关注：
1. 车辆控制系统的安全威胁
2. 车联网通信的隐私风险
3. 远程攻击的可能性
4. 数据泄露的影响
5. 监管合规要求

请确保分析结果具有可操作性，并提供具体的缓解建议。
"""
        
        return prompt
    
    def _calculate_confidence_score(self, tara_result: Dict[str, Any]) -> float:
        """计算分析结果的置信度分数"""
        score = 0.0
        
        # 基于结果完整性计算
        if "summary" in tara_result and tara_result["summary"]:
            score += 0.2
        
        if "assets" in tara_result and len(tara_result["assets"]) > 0:
            score += 0.2
        
        if "threats" in tara_result and len(tara_result["threats"]) > 0:
            score += 0.2
        
        if "risks" in tara_result and len(tara_result["risks"]) > 0:
            score += 0.2
        
        if "recommendations" in tara_result and len(tara_result["recommendations"]) > 0:
            score += 0.2
        
        # 上限为1.0
        return min(score, 1.0)
    
    def _parse_tara_response(self, response: str) -> Dict[str, Any]:
        """解析TARA分析响应"""
        try:
            # 尝试解析JSON响应
            result = json.loads(response.strip())
            
            # 验证必要字段
            required_fields = ["summary", "assets", "threats", "risks", "recommendations"]
            for field in required_fields:
                if field not in result:
                    result[field] = []
            
            return result
        except json.JSONDecodeError:
            # 如果无法解析为JSON，尝试提取信息
            return self._extract_tara_info(response)
    
    def _extract_tara_info(self, response: str) -> Dict[str, Any]:
        """从非JSON响应中提取TARA信息"""
        import re
        
        # 默认结果
        result = {
            "summary": "",
            "assets": [],
            "threats": [],
            "risks": [],
            "recommendations": [],
            "compliance_notes": "",
            "raw_response": response  # 保存原始响应
        }
        
        # 尝试提取概要信息
        summary_match = re.search(r'#*\s*概要|总结|Summary(.*?)(?=#|\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            result["summary"] = summary_match.group(1).strip()
        
        # 尝试提取资产信息
        assets_section = re.search(r'#*\s*资产|Assets(.*?)(?=#|\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if assets_section:
            assets_text = assets_section.group(1)
            asset_items = re.findall(r'[-*]\s*(.*?)(?=[-*]|\n\n|$)', assets_text, re.DOTALL)
            for item in asset_items:
                if item.strip():
                    result["assets"].append({
                        "name": item.strip(),
                        "description": item.strip()
                    })
        
        # 尝试提取威胁信息
        threats_section = re.search(r'#*\s*威胁|Threats(.*?)(?=#|\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if threats_section:
            threats_text = threats_section.group(1)
            threat_items = re.findall(r'[-*]\s*(.*?)(?=[-*]|\n\n|$)', threats_text, re.DOTALL)
            for i, item in enumerate(threat_items):
                if item.strip():
                    result["threats"].append({
                        "id": f"T{i+1}",
                        "name": item.strip(),
                        "description": item.strip()
                    })
        
        # 尝试提取建议信息
        recom_section = re.search(r'#*\s*建议|推荐|Recommendations(.*?)(?=#|\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if recom_section:
            recom_text = recom_section.group(1)
            recom_items = re.findall(r'[-*]\s*(.*?)(?=[-*]|\n\n|$)', recom_text, re.DOTALL)
            for item in recom_items:
                if item.strip():
                    result["recommendations"].append({
                        "description": item.strip(),
                        "priority": "中"
                    })
        
        # 如果没有提取到内容，设置一个基本概要
        if not result["summary"] and not result["assets"] and not result["threats"]:
            result["summary"] = "无法解析TARA分析结果为结构化数据，请参考原始响应。"
        
        return result
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的工具列表"""
        return {
            "asset_analyzer": {
                "description": "分析系统资产",
                "parameters": {}
            },
            "threat_analyzer": {
                "description": "识别和分析威胁",
                "parameters": {}
            },
            "risk_calculator": {
                "description": "计算风险等级",
                "parameters": {}
            },
            "mitigation_recommender": {
                "description": "推荐缓解措施",
                "parameters": {}
            }
        } 