"""
KunlunSec AI Platform - TARA分析智能体模块

实现威胁分析与风险评估智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, model_validator

from app.agent.toolcall import ToolCallAgent, ToolCollection, Tool

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

# TARA专用工具
class TaraAnalysisTool(Tool):
    """TARA分析工具"""
    name: str = "tara_analysis"
    description: str = "执行威胁分析与风险评估"
    
    async def run(self, target: str, **kwargs) -> Dict[str, Any]:
        """执行TARA分析"""
        # 实际实现将执行完整的TARA分析
        return {
            "target": target,
            "threats": [
                {"id": "T1", "name": "未授权访问", "likelihood": "高"}
            ],
            "risks": [
                {"threat_id": "T1", "impact": "高", "risk_level": "严重"}
            ]
        }

class RagQueryTool(Tool):
    """RAG查询工具"""
    name: str = "rag_query"
    description: str = "查询知识库获取相关信息"
    
    async def run(self, query: str, **kwargs) -> str:
        """执行RAG查询"""
        # 实际实现将查询知识库
        return f"关于'{query}'的查询结果"

class FileOperatorTool(Tool):
    """文件操作工具"""
    name: str = "file_operator"
    description: str = "读写文件"
    
    async def run(self, operation: str, path: str, content: Optional[str] = None, **kwargs) -> str:
        """执行文件操作"""
        if operation == "read":
            # 实际实现将读取文件
            return f"读取文件 {path} 的内容"
        elif operation == "write":
            # 实际实现将写入文件
            return f"写入内容到文件 {path}"
        else:
            return f"不支持的操作: {operation}"

class WebSearchTool(Tool):
    """网络搜索工具"""
    name: str = "web_search"
    description: str = "在网络上搜索信息"
    
    async def run(self, query: str, **kwargs) -> str:
        """执行网络搜索"""
        # 实际实现将执行网络搜索
        return f"关于'{query}'的搜索结果"

class BrowserUseTool(Tool):
    """浏览器使用工具"""
    name: str = "browser_use"
    description: str = "使用浏览器访问网页"
    
    async def run(self, url: str, action: Optional[str] = None, **kwargs) -> str:
        """执行浏览器操作"""
        # 实际实现将控制浏览器
        if not action:
            return f"访问网页 {url} 的内容"
        return f"在网页 {url} 上执行 {action} 操作"

class PlanningTool(Tool):
    """规划工具"""
    name: str = "planning"
    description: str = "制定分析计划"
    
    async def run(self, task: str, **kwargs) -> str:
        """执行规划"""
        # 实际实现将生成计划
        return f"针对任务 '{task}' 的分析计划"

class TaraAgent(ToolCallAgent):
    """威胁分析与风险评估智能体"""
    
    name: str = "TARA"
    description: str = "专门进行威胁分析与风险评估的智能体，基于法规强标进行TARA分析"
    
    system_prompt: str = TARA_SYSTEM_PROMPT
    next_step_prompt: str = TARA_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletion(),
        Terminate(),
        PlanningTool(),
        WebSearchTool(),
        BrowserUseTool(),
        
        # 专业工具
        TaraAnalysisTool(),
        RagQueryTool(),
        FileOperatorTool(),
    ))
    
    # TARA特定属性
    regulation_database: Dict[str, str] = Field(default_factory=dict)
    threat_categories: List[str] = Field(default_factory=list)
    browser_context_helper: Optional[BrowserContextHelper] = None
    
    # 初始化方法
    @model_validator(mode="after")
    def initialize_helper(self) -> "TaraAgent":
        """初始化基础组件"""
        self.browser_context_helper = BrowserContextHelper(self)
        return self
    
    @classmethod
    async def create(cls, **kwargs) -> "TaraAgent":
        """创建并初始化TARA智能体"""
        instance = cls(**kwargs)
        await instance.initialize_regulations()
        return instance
    
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
        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.get("name") == BrowserUseTool().name
            for msg in recent_messages
            if "tool_calls" in msg
            for tc in msg.get("tool_calls", [])
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        result = await super().think()
        
        # 恢复原始提示
        self.next_step_prompt = original_prompt
        
        return result
    
    # TARA特定方法
    async def analyze_threat(self, target_description: str) -> Dict[str, Any]:
        """分析特定目标的威胁"""
        # 使用TARA分析工具
        tara_tool = self.available_tools.get_tool("tara_analysis")
        if not tara_tool:
            return {"error": "TARA分析工具不可用"}
        
        return await tara_tool.run(target=target_description)
    
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
            "高": {"高": "严重", "中": "高", "低": "中"},
            "中": {"高": "高", "中": "中", "低": "低"},
            "低": {"高": "中", "中": "低", "低": "可忽略"}
        }
        
        return risk_matrix.get(likelihood, {}).get(impact, "未知")
    
    async def generate_mitigation(self, risk_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成缓解措施建议"""
        mitigations = []
        
        for threat_id, risk_info in risk_data.items():
            threat = risk_info.get("threat", {})
            risk_level = risk_info.get("risk_level", "未知")
            
            # 根据威胁和风险等级生成缓解措施
            measures = self._generate_measures_for_threat(threat, risk_level)
            
            mitigations.append({
                "threat_id": threat_id,
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
            measures.extend([
                "实施强身份认证",
                "采用最小权限原则",
                "实施网络分段"
            ])
        elif "拒绝服务" in threat_name:
            measures.extend([
                "实施流量监控",
                "部署DDoS防护",
                "增加系统冗余"
            ])
        elif "篡改" in threat_name:
            measures.extend([
                "实施数据完整性校验",
                "使用安全的通信协议",
                "实施变更管理"
            ])
        
        # 根据风险等级添加额外措施
        if risk_level == "严重":
            measures.append("定期进行安全评估和渗透测试")
        
        return measures

# 导入循环依赖
from app.agent.toolcall import CreateChatCompletion, Terminate 