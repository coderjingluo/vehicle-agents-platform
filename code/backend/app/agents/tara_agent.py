"""
TARA智能体
威胁分析和风险评估智能体，使用LangGraph工作流
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from .base_agent import BaseAgent
from app.core.llm_client import LLMClientManager
from app.core.tool_registry import ToolRegistry


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
    
    def get_agent_type(self) -> str:
        """获取智能体类型"""
        return "tara"
    
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
            
            # 确保每个威胁都有ID
            for i, threat in enumerate(result.get("threats", [])):
                if "id" not in threat:
                    threat["id"] = f"T{i+1:03d}"
            
            # 确保每个风险都关联威胁
            for risk in result.get("risks", []):
                if "threat_id" not in risk and result.get("threats"):
                    risk["threat_id"] = result["threats"][0].get("id", "T001")
            
            return result
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试提取关键信息
            return self._extract_tara_info(response)
    
    def _extract_tara_info(self, response: str) -> Dict[str, Any]:
        """从非JSON响应中提取TARA信息"""
        lines = response.split('\n')
        
        result = {
            "summary": "TARA分析完成",
            "assets": [],
            "threats": [],
            "risks": [],
            "recommendations": [],
            "raw_response": response
        }
        
        # 简单的关键词提取
        threat_keywords = ["威胁", "threat", "攻击", "attack", "漏洞", "vulnerability"]
        risk_keywords = ["风险", "risk", "危险", "danger"]
        recommendation_keywords = ["建议", "recommendation", "措施", "measure", "防护", "protection"]
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in threat_keywords):
                result["threats"].append({
                    "id": f"T{len(result['threats'])+1:03d}",
                    "name": line,
                    "category": "未分类",
                    "description": line
                })
            elif any(keyword in line.lower() for keyword in risk_keywords):
                result["risks"].append({
                    "threat_id": f"T{len(result['risks'])+1:03d}",
                    "risk_level": "中",
                    "risk_score": 5,
                    "justification": line
                })
            elif any(keyword in line.lower() for keyword in recommendation_keywords):
                result["recommendations"].append({
                    "priority": "中",
                    "category": "一般建议",
                    "description": line,
                    "implementation_effort": "中等",
                    "expected_impact": "中等"
                })
        
        return result
    
    def _calculate_confidence_score(self, tara_result: Dict[str, Any]) -> float:
        """计算分析置信度分数"""
        score = 0.0
        
        # 基于结果完整性计算置信度
        if tara_result.get("summary"):
            score += 0.2
        if tara_result.get("assets"):
            score += 0.2
        if tara_result.get("threats"):
            score += 0.3
        if tara_result.get("risks"):
            score += 0.2
        if tara_result.get("recommendations"):
            score += 0.1
        
        # 基于结果详细程度调整
        threat_count = len(tara_result.get("threats", []))
        if threat_count >= 5:
            score += 0.1
        elif threat_count >= 3:
            score += 0.05
        
        risk_count = len(tara_result.get("risks", []))
        if risk_count >= 3:
            score += 0.1
        elif risk_count >= 1:
            score += 0.05
        
        return min(score, 1.0)
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取TARA专用工具"""
        tools = super().get_available_tools()
        
        # 过滤出TARA相关的工具
        tara_tools = {}
        for tool_name, tool_info in tools.items():
            if any(keyword in tool_name.lower() for keyword in 
                   ["tara", "threat", "risk", "security", "analysis"]):
                tara_tools[tool_name] = tool_info
        
        return tara_tools 