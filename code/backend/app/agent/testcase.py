"""
KunlunSec AI Platform - 测试用例智能体模块

实现基于TARA分析结果生成测试用例的智能体。
"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent, ToolCollection, Tool
from app.agent.toolcall import CreateChatCompletion, Terminate

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

# 测试用例专用工具
class TestCaseGeneratorTool(Tool):
    """测试用例生成工具"""
    name: str = "test_case_generator"
    description: str = "生成安全测试用例"
    
    async def run(self, threat: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成测试用例"""
        # 实际实现将基于威胁生成测试用例
        threat_name = threat.get("name", "未知威胁")
        
        return {
            "threat_id": threat.get("id", "unknown"),
            "threat_name": threat_name,
            "test_cases": [
                {
                    "id": f"TC_{threat.get('id', 'unknown')}_1",
                    "name": f"{threat_name}测试1",
                    "description": f"验证系统对{threat_name}的防御能力",
                    "steps": [
                        "步骤1: 准备测试环境",
                        "步骤2: 执行测试操作",
                        "步骤3: 验证结果"
                    ],
                    "expected_result": "系统应当能够抵御攻击并保持正常运行"
                }
            ]
        }

class TestCaseAgent(ToolCallAgent):
    """测试用例生成智能体"""
    
    name: str = "TestCase"
    description: str = "基于TARA分析结果生成测试用例的专业智能体"
    
    system_prompt: str = TEST_CASE_SYSTEM_PROMPT
    next_step_prompt: str = TEST_CASE_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletion(),
        Terminate(),
        PlanningTool(),
        
        # 专业工具
        TestCaseGeneratorTool(),
        RagQueryTool(),
        FileOperatorTool(),
    ))
    
    # 测试用例特定属性
    test_templates: Dict[str, str] = Field(default_factory=dict)
    coverage_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "TestCaseAgent":
        """创建并初始化测试用例智能体"""
        instance = cls(**kwargs)
        await instance.initialize_templates()
        return instance
    
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
            test_case_tool = self.available_tools.get_tool("test_case_generator")
            if not test_case_tool:
                continue
                
            # 生成测试用例
            test_case_result = await test_case_tool.run(threat=threat)
            
            # 使用模板丰富测试用例
            enriched_cases = await self._enrich_with_templates(test_case_result)
            
            all_test_cases.extend(enriched_cases)
        
        return all_test_cases
    
    async def _enrich_with_templates(self, test_case_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用模板丰富测试用例"""
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
        """分析测试用例对威胁的覆盖率"""
        # 初始化覆盖率指标
        coverage = {
            "overall": 0.0,
            "by_threat": {},
            "by_category": {}
        }
        
        # 计算威胁覆盖率
        threat_ids = {threat.get("id"): threat for threat in threats}
        covered_threats = set()
        
        for test_case in test_cases:
            threat_id = test_case.get("threat_id")
            if threat_id in threat_ids:
                covered_threats.add(threat_id)
        
        if threat_ids:
            coverage["overall"] = len(covered_threats) / len(threat_ids) * 100
        
        # 按威胁计算覆盖率
        for threat_id, threat in threat_ids.items():
            threat_test_cases = [tc for tc in test_cases if tc.get("threat_id") == threat_id]
            coverage["by_threat"][threat_id] = len(threat_test_cases) > 0
        
        # 更新覆盖率指标
        self.coverage_metrics = coverage
        
        return coverage

# 导入循环依赖
from app.agent.tara import PlanningTool, RagQueryTool, FileOperatorTool 