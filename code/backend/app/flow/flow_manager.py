import uuid
from typing import Dict, List, Any, Optional

from app.flow.base import BaseFlow, FlowStatus
from app.flow.flow_factory import FlowFactory


class FlowManager:
    """执行流管理器"""
    
    def __init__(self, agent_factory=None):
        self.flows: Dict[str, BaseFlow] = {}
        self.flow_factory = FlowFactory(agent_factory)
    
    async def create_flow(self, flow_type: str, flow_id: str = None, name: str = None, 
                        description: str = None, **kwargs) -> str:
        """创建新的执行流"""
        flow_id = flow_id or str(uuid.uuid4())
        
        # 检查ID是否已存在
        if flow_id in self.flows:
            raise ValueError(f"Flow with ID {flow_id} already exists")
        
        # 创建执行流
        flow = self.flow_factory.create_flow(flow_type, flow_id, name, description)
        
        # 初始化执行流
        await flow.initialize(**kwargs)
        
        # 保存执行流
        self.flows[flow_id] = flow
        
        return flow_id
    
    async def execute_flow(self, flow_id: str) -> Dict[str, Any]:
        """执行指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        flow = self.flows[flow_id]
        success = await flow.execute()
        
        return {
            "success": success,
            "status": flow.status,
            "error": flow.error
        }
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """获取指定执行流的状态"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        return self.flows[flow_id].get_status()
    
    def get_flow_result(self, flow_id: str) -> Dict[str, Any]:
        """获取指定执行流的结果"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        flow = self.flows[flow_id]
        if flow.status != FlowStatus.COMPLETED:
            raise ValueError(f"Flow {flow_id} is not completed yet, current status: {flow.status}")
        
        return flow.get_result()
    
    async def pause_flow(self, flow_id: str) -> bool:
        """暂停指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        return await self.flows[flow_id].pause()
    
    async def resume_flow(self, flow_id: str) -> Dict[str, Any]:
        """恢复指定的执行流"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow with ID {flow_id} not found")
        
        success = await self.flows[flow_id].resume()
        
        flow = self.flows[flow_id]
        return {
            "success": success,
            "status": flow.status,
            "error": flow.error
        }
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """列出所有执行流及其状态"""
        return [
            {
                "id": flow_id,
                "name": flow.name,
                "description": flow.description,
                "status": flow.status,
                "type": flow.__class__.__name__
            }
            for flow_id, flow in self.flows.items()
        ]
