"""
KunlunSec AI Platform - 执行流管理

管理执行流的创建、运行和监控。
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
import os

from app.agent.interface import AgentFactory
from app.flow.flow_factory import FlowFactory, FlowType
from app.flow.base import BaseFlow
from app.flow.langgraph.flow_manager import LangGraphFlowManager
from app.core.logging import logger


class FlowManager:
    """执行流管理器"""
    
    def __init__(self, agent_factory=None):
        """
        初始化执行流管理器
        
        Args:
            agent_factory: 可选的智能体工厂实例
        """
        self.agent_factory = agent_factory or AgentFactory()
        self.flow_factory = FlowFactory(self.agent_factory)
        self.flows = {}  # 传统的执行流
        self.langgraph_manager = LangGraphFlowManager(self.agent_factory)  # LangGraph执行流管理器
        
    async def create_flow(self, flow_type: str, name: Optional[str] = None, 
                         description: Optional[str] = None, use_langgraph: bool = True,
                         **kwargs) -> str:
        """
        创建执行流
        
        Args:
            flow_type: 执行流类型
            name: 可选的执行流名称
            description: 可选的执行流描述
            use_langgraph: 是否使用LangGraph实现 (True使用LangGraph, False使用传统实现)
            **kwargs: 其他执行流参数
            
        Returns:
            执行流ID
        """
        flow_id = str(uuid.uuid4())
        
        try:
            if use_langgraph and flow_type in ["tara", "testcase", "automation", "report", "dynamic"]:
                # 使用LangGraph实现
                return await self.langgraph_manager.create_graph_flow(
                    flow_type=flow_type,
                    flow_id=flow_id,
                    name=name,
                    description=description,
                    **kwargs
                )
            else:
                # 使用传统实现
                flow = self.flow_factory.create_flow(
                    flow_type=flow_type,
                    flow_id=flow_id,
                    name=name,
                    description=description,
                    **kwargs
                )
                
                if not flow:
                    raise ValueError(f"无法创建类型为 {flow_type} 的执行流")
                
                # 初始化执行流
                await flow.initialize(**kwargs)
                
                # 保存执行流
                self.flows[flow_id] = flow
                
                return flow_id
        except Exception as e:
            logger.error(f"创建执行流失败: {str(e)}")
            raise
    
    async def execute_flow(self, flow_id: str, **kwargs) -> Union[bool, Dict[str, Any]]:
        """
        执行执行流
        
        Args:
            flow_id: 执行流ID
            **kwargs: 执行参数
            
        Returns:
            执行是否成功或执行结果
        """
        try:
            # 确保环境变量中有API密钥
            if not os.environ.get("OPENAI_API_KEY"):
                # 设置一个默认的测试密钥（这里用占位符，实际应用中应从配置中获取）
                os.environ["OPENAI_API_KEY"] = "sk-placeholder-for-testing-only"
                logger.warning("未设置OPENAI_API_KEY环境变量，使用占位符密钥。请在生产环境中正确配置API密钥。")
            
            # 先检查是否为LangGraph流程
            try:
                # 尝试从LangGraph管理器获取流程
                self.langgraph_manager.get_graph_flow(flow_id)
                # 如果成功，则使用LangGraph执行
                return await self.langgraph_manager.execute_graph_flow(flow_id, kwargs)
            except ValueError:
                # 如果不是LangGraph流程，则查找传统流程
                if flow_id not in self.flows:
                    raise ValueError(f"未找到ID为 {flow_id} 的执行流")
                
                # 使用传统执行流执行
                flow = self.flows[flow_id]
                result = await flow.execute()
                return result
        except Exception as e:
            logger.error(f"执行流 {flow_id} 执行失败: {str(e)}")
            raise

    async def _handle_task_execution(self, flow_id: str, task: str, task_type: str = None, **params):
        """处理任务执行
        
        Args:
            flow_id: 流程ID
            task: 任务内容
            task_type: 任务类型，可选，如果提供则优先使用
            **params: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 获取流程
        flow = self.flows.get(flow_id)
        if not flow:
            raise ValueError(f"找不到流程: {flow_id}")
        
        # 获取流程类型
        flow_type = flow.get("type")
        
        # 确定任务类型
        if not task_type:
            # 尝试从任务内容自动识别任务类型
            if isinstance(task, dict) and "type" in task:
                task_type = task["type"].upper() if isinstance(task["type"], str) else None
            
            # 如果依然没有识别出任务类型，根据流程类型设置默认任务类型
            if not task_type:
                if flow_type == "tara":
                    task_type = "TARA"
                elif flow_type == "testcase":
                    task_type = "TEST_CASE"
                elif flow_type == "automation":
                    task_type = "AUTOMATION"
                elif flow_type == "report":
                    task_type = "REPORT"
                else:
                    # 动态流程默认使用通用任务类型
                    task_type = "GENERAL"
        
        logger.info(f"【flow_manager】执行流程 {flow_id}, 任务类型: {task_type}, 流程类型: {flow_type}")
        
        # 确保流程已初始化
        flow_instance = flow.get("instance")
        if not flow_instance:
            raise ValueError(f"流程 {flow_id} 未初始化")
        
        # 准备执行参数
        execution_params = {"task": task}
        execution_params.update(params)
        
        # 保存当前流程信息
        self._current_flow_id = flow_id
        self._current_task_type = task_type
        
        # 记录任务开始时间
        flow["start_time"] = datetime.now().isoformat()
        flow["status"] = "running"
        
        try:
            # 执行流程
            if flow_type == "dynamic":
                # 为动态流程添加任务类型信息
                execution_params["task_type"] = task_type
                
                # 使用LangGraph执行
                lg_flow_manager = self.langgraph_flow_managers.get(flow_id)
                if not lg_flow_manager:
                    raise ValueError(f"找不到LangGraph流程管理器: {flow_id}")
                
                # 执行任务
                result = await lg_flow_manager.execute_task(execution_params)
                
            else:
                # 调用流程实例的执行方法
                # 注意：不同流程的执行方法可能不同，这里需要根据实际情况调整
                if hasattr(flow_instance, 'execute'):
                    result = await flow_instance.execute(**execution_params)
                elif hasattr(flow_instance, 'run'):
                    result = await flow_instance.run(**execution_params)
                else:
                    raise ValueError(f"流程 {flow_id} 没有可执行的方法")
            
            # 更新流程状态
            flow["status"] = "completed"
            flow["end_time"] = datetime.now().isoformat()
            flow["result"] = result
            
            return result
            
        except Exception as e:
            # 更新流程状态为错误
            flow["status"] = "error"
            flow["end_time"] = datetime.now().isoformat()
            flow["error"] = str(e)
            
            # 记录错误
            logger.error(f"执行流程 {flow_id} 失败: {str(e)}", exc_info=True)
            
            # 返回错误信息
            return {"error": str(e), "status": "failed"}

    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        获取执行流状态
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            执行流状态
        """
        try:
            # 先检查是否为LangGraph流程
            try:
                return self.langgraph_manager.get_graph_flow(flow_id)
            except ValueError as e:
                logger.debug(f"在LangGraph管理器中未找到流程 {flow_id}: {str(e)}")
                
                # 如果不是LangGraph流程，则查找传统流程
                if flow_id not in self.flows:
                    # 尝试从数据库中获取执行流状态
                    try:
                        from sqlalchemy import create_engine, text
                        from app.db.session import get_db_url
                        
                        # 创建同步引擎
                        sync_engine = create_engine(get_db_url())
                        
                        # 使用同步方式查询数据库
                        with sync_engine.connect() as connection:
                            query = text(
                                "SELECT id, status, progress, error_message, output_data "
                                "FROM flow_executions WHERE id = :flow_id"
                            )
                            result = connection.execute(query, {"flow_id": flow_id})
                            row = result.fetchone()
                            
                            if row:
                                return {
                                    "id": str(row[0]),
                                    "status": str(row[1]),
                                    "progress": row[2],
                                    "error": row[3],
                                    "result": row[4]
                                }
                    except Exception as db_error:
                        logger.error(f"从数据库获取流程状态失败: {str(db_error)}")
                    
                    # 如果数据库中也没有，则抛出异常
                    raise ValueError(f"未找到ID为 {flow_id} 的执行流")
                
                return self.flows[flow_id].get_status()
        except Exception as e:
            logger.error(f"获取执行流 {flow_id} 状态失败: {str(e)}")
            raise
    
    def get_flow_result(self, flow_id: str) -> Dict[str, Any]:
        """
        获取执行流结果
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            执行流结果
        """
        try:
            # 先检查是否为LangGraph流程
            try:
                flow_info = self.langgraph_manager.get_graph_flow(flow_id)
                if flow_info["status"] != "completed":
                    raise ValueError(f"执行流 {flow_id} 尚未完成")
                return flow_info["result"] or {}
            except ValueError:
                # 如果不是LangGraph流程，则查找传统流程
                if flow_id not in self.flows:
                    raise ValueError(f"未找到ID为 {flow_id} 的执行流")
                
                flow = self.flows[flow_id]
                return flow.get_result()
        except Exception as e:
            logger.error(f"获取执行流 {flow_id} 结果失败: {str(e)}")
            raise
    
    async def pause_flow(self, flow_id: str) -> bool:
        """
        暂停执行流
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            是否成功暂停
        """
        # LangGraph执行流不支持暂停
        if flow_id not in self.flows:
            raise ValueError(f"未找到ID为 {flow_id} 的执行流，或该流程不支持暂停")
        
        flow = self.flows[flow_id]
        return await flow.pause()
    
    async def resume_flow(self, flow_id: str) -> bool:
        """
        恢复执行流
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            是否成功恢复
        """
        # LangGraph执行流不支持恢复
        if flow_id not in self.flows:
            raise ValueError(f"未找到ID为 {flow_id} 的执行流，或该流程不支持恢复")
        
        flow = self.flows[flow_id]
        return await flow.resume()
    
    def list_flows(self, flow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出执行流
        
        Args:
            flow_type: 可选的执行流类型过滤
            
        Returns:
            执行流列表
        """
        # 获取传统执行流
        traditional_flows = []
        for flow_id, flow in self.flows.items():
            if flow_type and flow.__class__.__name__.lower() != flow_type.lower():
                continue
                
            traditional_flows.append({
                "id": flow_id,
                "name": getattr(flow, "name", "未命名"),
                "description": getattr(flow, "description", ""),
                "type": flow.__class__.__name__,
                "status": flow.status,
                "is_graph_based": False
            })
        
        # 获取LangGraph执行流
        try:
            graph_flows = self.langgraph_manager.list_graph_flows(flow_type)
            for flow in graph_flows:
                flow["is_graph_based"] = True
        except:
            graph_flows = []
            
        # 合并并返回结果
        return traditional_flows + graph_flows
    
    def get_flow_visualization(self, flow_id: str) -> str:
        """
        获取执行流可视化
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            可视化表示（Mermaid格式）
        """
        # 先检查是否为LangGraph流程
        try:
            return self.langgraph_manager.get_flow_visualization(flow_id)
        except ValueError:
            # 如果不是LangGraph流程，则返回不支持信息
            return "传统执行流不支持Mermaid可视化"
    
    def delete_flow(self, flow_id: str) -> bool:
        """
        删除执行流
        
        Args:
            flow_id: 执行流ID
            
        Returns:
            是否成功删除
        """
        # 先检查是否为LangGraph流程
        try:
            return self.langgraph_manager.delete_graph_flow(flow_id)
        except ValueError:
            # 如果不是LangGraph流程，检查传统流程
            if flow_id not in self.flows:
                raise ValueError(f"未找到ID为 {flow_id} 的执行流")
                
            del self.flows[flow_id]
            return True
