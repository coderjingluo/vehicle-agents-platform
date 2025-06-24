"""
智能体模块初始化

本模块包含车联网安全测试生命周期管理平台的所有智能体：
- TARA智能体: 威胁分析与风险评估
- 测试用例智能体: 基于TARA结果生成测试用例  
- 自动化测试智能体: 生成和执行自动化测试脚本
- 报告分析智能体: 综合分析结果并生成专业报告
- 知识库智能体: 项目知识自动归档和持续学习
"""

from .base_agent import BaseAgent, AgentStep, AgentPlan
from .tara_agent import TARAAgent
from .testcase_agent import TestCaseAgent
from .automation_agent import AutomationAgent
from .report_agent import ReportAgent
from .knowledge_agent import KnowledgeAgent

# 智能体注册表
AGENT_REGISTRY = {
    "tara": TARAAgent,
    "test_case": TestCaseAgent,
    "automation_test": AutomationAgent,
    "report_analysis": ReportAgent,
    "knowledge_base": KnowledgeAgent
}

def get_agent(agent_type: str) -> BaseAgent:
    """
    根据智能体类型获取智能体实例
    
    Args:
        agent_type: 智能体类型 (tara, test_case, automation_test, report_analysis, knowledge_base)
        
    Returns:
        智能体实例
        
    Raises:
        ValueError: 当智能体类型不存在时
    """
    if agent_type not in AGENT_REGISTRY:
        available_types = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(f"未知的智能体类型: {agent_type}. 可用类型: {available_types}")
    
    agent_class = AGENT_REGISTRY[agent_type]
    return agent_class()

def list_available_agents() -> list:
    """
    获取所有可用的智能体类型
    
    Returns:
        智能体类型列表
    """
    return list(AGENT_REGISTRY.keys())

def get_agent_info(agent_type: str) -> dict:
    """
    获取智能体详细信息
    
    Args:
        agent_type: 智能体类型
        
    Returns:
        智能体信息字典
    """
    if agent_type not in AGENT_REGISTRY:
        return {"error": "智能体类型不存在"}
    
    agent_descriptions = {
        "tara": {
            "name": "TARA智能体",
            "description": "威胁分析与风险评估，基于ISO 21434、SAE J3061等标准",
            "capabilities": [
                "威胁识别和分类",
                "风险评估和量化", 
                "缓解措施建议",
                "合规性检查"
            ]
        },
        "test_case": {
            "name": "测试用例智能体", 
            "description": "基于TARA分析结果生成专业测试用例",
            "capabilities": [
                "测试用例设计",
                "测试策略制定",
                "测试覆盖率分析",
                "测试优先级管理"
            ]
        },
        "automation_test": {
            "name": "自动化测试智能体",
            "description": "生成和执行自动化测试脚本",
            "capabilities": [
                "自动化脚本生成",
                "测试框架选择",
                "测试环境配置", 
                "测试执行监控"
            ]
        },
        "report_analysis": {
            "name": "报告分析智能体",
            "description": "综合分析测试结果并生成专业报告",
            "capabilities": [
                "风险评估分析",
                "合规性检查",
                "修复建议生成",
                "专业报告生成"
            ]
        },
        "knowledge_base": {
            "name": "知识库智能体",
            "description": "项目知识自动归档和持续学习优化",
            "capabilities": [
                "知识提取和分类",
                "智能知识检索",
                "知识关联建立",
                "个性化推荐"
            ]
        }
    }
    
    return agent_descriptions.get(agent_type, {"error": "智能体信息不可用"})

__all__ = [
    "BaseAgent", 
    "AgentStep", 
    "AgentPlan",
    "TARAAgent",
    "TestCaseAgent", 
    "AutomationAgent",
    "ReportAgent",
    "KnowledgeAgent",
    "AGENT_REGISTRY",
    "get_agent",
    "list_available_agents", 
    "get_agent_info"
] 