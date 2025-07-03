"""
KunlunSec AI Platform - LangGraph执行流管理器

管理基于LangGraph的执行流。
"""

import uuid
from typing import Dict, List, Any, Optional, Union
import os

from app.agent.interface import AgentFactory
from app.core.logging import logger


class LangGraphFlowManager:
    """LangGraph执行流管理器"""
    
    def __init__(self, agent_factory=None):
        """
        初始化LangGraph执行流管理器
        
        Args:
            agent_factory: 可选的智能体工厂实例
        """
        self.agent_factory = agent_factory or AgentFactory()
        self.flows = {}  # 流程ID到流程实例的映射
        
    async def create_graph_flow(self, flow_type: str, flow_id: str = None, 
                              name: str = None, description: str = None, 
                              **kwargs) -> str:
        """
        创建图执行流
        
        Args:
            flow_type: 执行流类型
            flow_id: 可选的执行流ID
            name: 可选的执行流名称
            description: 可选的执行流描述
            **kwargs: 其他执行流参数
            
        Returns:
            执行流ID
        """
        # 如果未提供ID，则生成一个
        if not flow_id:
            flow_id = str(uuid.uuid4())
        
        # 根据类型创建图
        try:
            logger.info(f"创建图执行流: {flow_type}")
            # 为每种类型使用特定的图实现
            if flow_type == "tara":
                from app.flow.langgraph.tara_graph import TaraAgentGraph
                flow = TaraAgentGraph(self.agent_factory)
                await flow.initialize(**kwargs)
            elif flow_type in ["testcase", "test_case"]:
                from app.flow.langgraph.testcase_graph import TestCaseAgentGraph
                flow = TestCaseAgentGraph(kwargs.get("config", {}))
                await flow.setup()
            elif flow_type == "automation":
                from app.flow.langgraph.automation_graph import AutomationTestGraph
                flow = AutomationTestGraph(kwargs.get("config", {}))
                await flow.setup()
            elif flow_type == "report":
                from app.flow.langgraph.report_graph import ReportAnalysisGraph
                flow = ReportAnalysisGraph(kwargs.get("config", {}))
                await flow.setup()
            elif flow_type == "dynamic":
                from app.flow.langgraph.dynamic_flow import DynamicLangGraphFlow
                flow = DynamicLangGraphFlow(self.agent_factory, kwargs.get("config", {}))
                await flow.setup()
            else:
                raise ValueError(f"不支持的图执行流类型: {flow_type}")
            
            # 保存流程元数据
            self.flows[flow_id] = {
                "id": flow_id,
                "name": name or flow.name,
                "description": description or flow.description,
                "type": flow_type,
                "instance": flow,
                "status": "created",
                "result": None
            }
            
            return flow_id
        except Exception as e:
            logger.error(f"创建图执行流失败: {str(e)}")
            raise
    
    async def execute_graph_flow(self, flow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行图执行流
        
        Args:
            flow_id: 执行流ID
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        # 确保环境变量中有API密钥
        if not os.environ.get("OPENAI_API_KEY"):
            # 设置一个默认的测试密钥（这里用占位符，实际应用中应从配置中获取）
            os.environ["OPENAI_API_KEY"] = "sk-placeholder-for-testing-only"
            logger.warning("未设置OPENAI_API_KEY环境变量，使用占位符密钥。请在生产环境中正确配置API密钥。")
            
        # 检查流程是否存在
        if flow_id not in self.flows:
            raise ValueError(f"未找到ID为 {flow_id} 的图执行流")
        
        flow_info = self.flows[flow_id]
        flow = flow_info["instance"]
        
        try:
            # 更新状态
            flow_info["status"] = "running"
            
            # 执行流程
            result = await flow.invoke(input_data)
            
            # 更新状态和结果
            flow_info["status"] = result.get("status", "completed")
            flow_info["result"] = result
            
            return result
        except Exception as e:
            logger.error(f"执行图执行流 {flow_id} 失败: {str(e)}")
            flow_info["status"] = "error"
            flow_info["error"] = str(e)
            raise
    
    def get_graph_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        获取图执行流信息
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            执行流信息
        """
        if flow_id not in self.flows:
            raise ValueError(f"未找到ID为 {flow_id} 的图执行流")
        
        flow_info = self.flows[flow_id]
        return {
            "id": flow_info["id"],
            "name": flow_info["name"],
            "description": flow_info["description"],
            "type": flow_info["type"],
            "status": flow_info["status"],
            "result": flow_info.get("result")
        }
    
    def get_flow_visualization(self, flow_id: str) -> str:
        """
        获取图执行流可视化
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            可视化表示（Mermaid格式）
        """
        if flow_id not in self.flows:
            raise ValueError(f"未找到ID为 {flow_id} 的图执行流")
        
        flow = self.flows[flow_id]["instance"]
        return flow.get_graph_visualization()
    
    def list_graph_flows(self, flow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出图执行流
        
        Args:
            flow_type: 可选的执行流类型过滤
            
        Returns:
            执行流列表
        """
        result = []
        for flow_id, flow_info in self.flows.items():
            if flow_type and flow_info["type"] != flow_type:
                continue
                
            result.append({
                "id": flow_info["id"],
                "name": flow_info["name"],
                "description": flow_info["description"],
                "type": flow_info["type"],
                "status": flow_info["status"]
            })
            
        return result 