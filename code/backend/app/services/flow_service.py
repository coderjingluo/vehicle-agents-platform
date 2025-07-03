"""
KunlunSec AI Platform - 执行流服务

提供执行流管理器的依赖注入。
"""

from app.flow.flow_manager import FlowManager
from app.agent.interface import AgentFactory


# 全局执行流管理器实例
_flow_manager = None
# 全局智能体工厂实例
_agent_factory = None


def get_agent_factory() -> AgentFactory:
    """
    获取智能体工厂实例（依赖注入）
    
    Returns:
        AgentFactory: 智能体工厂实例
    """
    global _agent_factory
    
    if _agent_factory is None:
        _agent_factory = AgentFactory()
        
    return _agent_factory


def get_flow_manager() -> FlowManager:
    """
    获取执行流管理器实例（依赖注入）
    
    Returns:
        FlowManager: 执行流管理器实例
    """
    global _flow_manager, _agent_factory
    
    if _flow_manager is None:
        agent_factory = get_agent_factory()
        _flow_manager = FlowManager(agent_factory)
        
    return _flow_manager 