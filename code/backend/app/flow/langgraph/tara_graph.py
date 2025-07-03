"""
KunlunSec AI Platform - TARA分析图执行流

使用LangGraph实现TARA分析流程。
"""

from typing import Dict, List, Any, Optional, Callable, TypedDict, Annotated, Literal, Union, cast
from enum import Enum
import uuid
import json
import os
import copy
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.agent.tara import TaraAgent
from app.agent.base import BaseAgent
from app.core.logging import logger


# 定义步骤枚举
class TaraStep(str, Enum):
    """TARA分析步骤"""
    IDENTIFY_ASSETS = "identify_assets"
    IDENTIFY_THREATS = "identify_threats"
    ANALYZE_RISKS = "analyze_risks"
    DEVELOP_COUNTERMEASURES = "develop_countermeasures"
    GENERATE_REPORT = "generate_report"
    COMPLETE = "complete"
    ERROR = "error"


# 定义状态类型 - 使用独立的字段而不是嵌套结构
class TaraState(TypedDict, total=False):
    """TARA分析图状态"""
    # 基本状态信息
    current_step: Annotated[str, "The current step in the TARA process"]
    status: str
    error: Optional[str]
    
    # 消息和步骤跟踪
    input_messages: List[Dict[str, Any]]
    completed_steps: List[str]
    
    # 分析结果
    assets: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    countermeasures: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]


class TaraAgentGraph:
    """TARA分析图执行流"""
    
    def __init__(self, agent_factory=None):
        """
        初始化TARA分析图执行流
        
        Args:
            agent_factory: 智能体工厂
        """
        self.agent_factory = agent_factory
        self.tara_agent = None
        self.graph = None
        self.graph_id = None
        self.name = "TARA分析"
        self.description = "基于威胁分析与风险评估的安全分析流程"
        
        # 设置OpenAI API密钥环境变量，如果尚未设置
        self._setup_openai_env()
        
    def _setup_openai_env(self):
        """设置OpenAI API环境变量"""
        # 如果环境变量未设置，则使用默认值
        if not os.environ.get("OPENAI_API_KEY"):
            # 使用一个默认的测试密钥（这里用占位符，实际应用中应从配置中获取）
            os.environ["OPENAI_API_KEY"] = "sk-placeholder-for-testing-only"
            logger.warning("未设置OPENAI_API_KEY环境变量，使用占位符密钥。请在生产环境中正确配置API密钥。")
        
    async def initialize(self, **kwargs) -> None:
        """
        初始化图执行流
        
        Args:
            **kwargs: 初始化参数
        """
        # 创建TARA智能体
        if self.agent_factory:
            self.tara_agent = await self.agent_factory.get_agent("tara")
        else:
            self.tara_agent = await TaraAgent.create()
        
        # 构建图
        self._build_graph()
        
        # 生成图ID
        self.graph_id = str(uuid.uuid4())
        
    def _build_graph(self) -> None:
        """构建TARA分析图"""
        # 创建状态图
        builder = StateGraph(TaraState)
        
        # 添加节点
        builder.add_node(TaraStep.IDENTIFY_ASSETS, self._identify_assets)
        builder.add_node(TaraStep.IDENTIFY_THREATS, self._identify_threats)
        builder.add_node(TaraStep.ANALYZE_RISKS, self._analyze_risks)
        builder.add_node(TaraStep.DEVELOP_COUNTERMEASURES, self._develop_countermeasures)
        builder.add_node(TaraStep.GENERATE_REPORT, self._generate_report)
        builder.add_node(TaraStep.ERROR, self._handle_error)
        
        # 设置入口点
        builder.set_entry_point(TaraStep.IDENTIFY_ASSETS)
        
        # 添加边 - 使用条件边来处理状态转换
        builder.add_conditional_edges(
            TaraStep.IDENTIFY_ASSETS,
            self._route_next_step,
            {
                TaraStep.IDENTIFY_THREATS: TaraStep.IDENTIFY_THREATS,
                TaraStep.ERROR: TaraStep.ERROR
            }
        )
        
        builder.add_conditional_edges(
            TaraStep.IDENTIFY_THREATS,
            self._route_next_step,
            {
                TaraStep.ANALYZE_RISKS: TaraStep.ANALYZE_RISKS,
                TaraStep.ERROR: TaraStep.ERROR
            }
        )
        
        builder.add_conditional_edges(
            TaraStep.ANALYZE_RISKS,
            self._route_next_step,
            {
                TaraStep.DEVELOP_COUNTERMEASURES: TaraStep.DEVELOP_COUNTERMEASURES,
                TaraStep.ERROR: TaraStep.ERROR
            }
        )
        
        builder.add_conditional_edges(
            TaraStep.DEVELOP_COUNTERMEASURES,
            self._route_next_step,
            {
                TaraStep.GENERATE_REPORT: TaraStep.GENERATE_REPORT,
                TaraStep.ERROR: TaraStep.ERROR
            }
        )
        
        builder.add_edge(TaraStep.GENERATE_REPORT, END)
        builder.add_edge(TaraStep.ERROR, END)
        
        # 编译图
        self.graph = builder.compile()
    
    def _route_next_step(self, state: TaraState) -> str:
        """路由到下一个步骤"""
        if state.get("error"):
            return TaraStep.ERROR
            
        current_step = state.get("current_step", "")
        
        # 根据当前步骤确定下一步
        if current_step == TaraStep.IDENTIFY_ASSETS:
            return TaraStep.IDENTIFY_THREATS
        elif current_step == TaraStep.IDENTIFY_THREATS:
            return TaraStep.ANALYZE_RISKS
        elif current_step == TaraStep.ANALYZE_RISKS:
            return TaraStep.DEVELOP_COUNTERMEASURES
        elif current_step == TaraStep.DEVELOP_COUNTERMEASURES:
            return TaraStep.GENERATE_REPORT
        else:
            return TaraStep.ERROR
    
    async def _identify_assets(self, state: TaraState) -> TaraState:
        """识别资产节点"""
        try:
            # 创建新状态而不是修改现有状态
            new_state = copy.deepcopy(state)
            new_state["current_step"] = TaraStep.IDENTIFY_ASSETS
            
            logger.info("执行识别资产步骤")
            
            # 使用智能体的执行计划流程执行此步骤，而不是直接调用identify_assets方法
            if hasattr(self.tara_agent, 'current_plan') and self.tara_agent.current_plan:
                # 查找与资产识别相关的子任务
                asset_subtask = None
                for subtask in self.tara_agent.subtasks:
                    if '资产' in subtask.get('name', '').lower():
                        asset_subtask = subtask
                        break
                
                if asset_subtask:
                    logger.info(f"找到资产识别子任务: {asset_subtask.get('name')}")
                    # 构建执行提示
                    prompt = f"""
                    请执行TARA分析的资产识别步骤，识别并分析系统中的关键资产。
                    
                    子任务: {asset_subtask.get('name')}
                    描述: {asset_subtask.get('description')}
                    
                    请确保返回格式化的资产列表，包含:
                    - 资产ID
                    - 资产名称
                    - 资产类型
                    - 重要性级别
                    - 简要描述
                    """
                    
                    # 使用智能体执行这个步骤
                    result = await self.tara_agent.run(prompt)
                    
                    # 尝试从结果中提取资产信息
                    assets = self._extract_assets_from_response(result)
                else:
                    logger.warning("未找到资产识别相关子任务，使用默认方法")
                    # 如果没有找到相关子任务，则使用默认方式
                    input_messages = new_state.get("input_messages", [])
                    # 使用识别资产方法，但通过run方法调用，而不是直接调用
                    prompt = "请识别并分析系统中的关键资产，包括硬件、软件和数据资产。"
                    result = await self.tara_agent.run(prompt)
                    assets = self._extract_assets_from_response(result)
            else:
                logger.warning("智能体没有执行计划，使用默认方法识别资产")
                # 如果没有执行计划，使用默认方式
                input_messages = new_state.get("input_messages", [])
                result = await self.tara_agent.run("请识别并分析系统中的关键资产，包括硬件、软件和数据资产。")
                assets = self._extract_assets_from_response(result)
            
            # 更新状态
            new_state["assets"] = assets
            
            # 更新已完成步骤
            completed_steps = new_state.get("completed_steps", [])
            if TaraStep.IDENTIFY_ASSETS not in completed_steps:
                new_state["completed_steps"] = completed_steps + [TaraStep.IDENTIFY_ASSETS]
            
            return new_state
        except Exception as e:
            logger.error(f"识别资产失败: {str(e)}")
            return {**copy.deepcopy(state), "error": f"识别资产失败: {str(e)}"}
        
    def _extract_assets_from_response(self, response: str) -> List[Dict[str, Any]]:
        """从智能体响应中提取资产列表
        
        Args:
            response: 智能体响应
            
        Returns:
            List[Dict[str, Any]]: 提取的资产列表
        """
        import re
        import json
        
        try:
            # 尝试从响应中提取JSON格式的资产列表
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                if isinstance(data, dict) and "assets" in data:
                    return data["assets"]
                elif isinstance(data, list):
                    return data
            
            # 如果没有找到JSON格式，则尝试从文本中提取资产信息
            assets = []
            # 使用正则表达式匹配可能的资产ID格式，如A001或Asset-1
            asset_ids = re.findall(r'(A\d{3}|Asset[-_]?\d+)', response)
            
            for i, asset_id in enumerate(asset_ids[:10]):  # 限制最多10个资产
                # 尝试找到与该ID相关的名称和描述
                name_match = re.search(rf'{asset_id}[^\n]*?([^\n]+)', response)
                name = name_match.group(1).strip() if name_match else f"资产{i+1}"
                
                # 尝试确定资产类型
                type_indicators = {
                    "硬件": ["设备", "硬件", "装置", "组件", "模块"],
                    "软件": ["软件", "应用", "程序", "系统", "固件"],
                    "数据": ["数据", "信息", "记录", "配置", "密钥"]
                }
                
                asset_type = "未知"
                for t, indicators in type_indicators.items():
                    if any(ind in name.lower() for ind in indicators):
                        asset_type = t
                        break
                
                # 简单估计重要性
                importance_indicators = {
                    "高": ["关键", "核心", "重要", "主要", "敏感"],
                    "中": ["次要", "支持", "辅助"],
                    "低": ["可选", "非关键", "辅助"]
                }
                
                importance = "中"  # 默认中等重要性
                for level, indicators in importance_indicators.items():
                    if any(ind in response.lower() for ind in indicators):
                        importance = level
                        break
                
                # 创建资产条目
                assets.append({
                    "id": asset_id,
                    "name": name,
                    "type": asset_type,
                    "importance": importance,
                    "description": f"从分析中识别的{asset_type}资产"
                })
            
            # 如果未能提取到任何资产，则创建一些默认资产
            if not assets:
                assets = [
                    {
                        "id": "A001",
                        "name": "车载中控系统",
                        "type": "硬件",
                        "importance": "高",
                        "description": "车辆的核心控制系统，管理车辆的关键功能"
                    },
                    {
                        "id": "A002",
                        "name": "车联网通信模块",
                        "type": "硬件",
                        "importance": "高",
                        "description": "负责车辆与外部网络的通信"
                    },
                    {
                        "id": "A003",
                        "name": "车辆操作系统",
                        "type": "软件",
                        "importance": "高",
                        "description": "车辆的基础操作系统，管理各个子系统"
                    }
                ]
                logger.warning("未能从响应中提取资产，使用默认资产列表")
                
            return assets
        except Exception as e:
            logger.error(f"提取资产信息失败: {str(e)}")
            # 返回默认资产列表
            return [
                {
                    "id": "A001",
                    "name": "车载中控系统",
                    "type": "硬件",
                    "importance": "高",
                    "description": "车辆的核心控制系统，管理车辆的关键功能"
                }
            ]
    
    async def _identify_threats(self, state: TaraState) -> TaraState:
        """识别威胁节点"""
        try:
            # 创建新状态而不是修改现有状态
            new_state = copy.deepcopy(state)
            new_state["current_step"] = TaraStep.IDENTIFY_THREATS
            
            logger.info("执行识别威胁步骤")
            
            # 使用智能体的执行计划流程执行此步骤，而不是直接调用identify_threats方法
            assets = new_state.get("assets", [])
            
            if hasattr(self.tara_agent, 'current_plan') and self.tara_agent.current_plan:
                # 查找与威胁识别相关的子任务
                threat_subtask = None
                for subtask in self.tara_agent.subtasks:
                    if '威胁' in subtask.get('name', '').lower():
                        threat_subtask = subtask
                        break
                
                if threat_subtask:
                    logger.info(f"找到威胁识别子任务: {threat_subtask.get('name')}")
                    # 格式化资产信息
                    assets_str = "\n".join([
                        f"- {a.get('id', 'Unknown')}: {a.get('name', 'Unknown')} ({a.get('type', 'Unknown')}) - 重要性: {a.get('importance', '中')}"
                        for a in assets
                    ])
                    
                    # 构建执行提示
                    prompt = f"""
                    请执行TARA分析的威胁识别步骤，基于以下资产识别潜在威胁:
                    
                    子任务: {threat_subtask.get('name')}
                    描述: {threat_subtask.get('description')}
                    
                    已识别的资产:
                    {assets_str}
                    
                    请考虑STRIDE威胁模型（欺骗、篡改、抵赖、信息泄露、拒绝服务、权限提升），
                    并为每个威胁提供以下信息:
                    - 威胁ID
                    - 威胁名称
                    - 相关资产ID
                    - 威胁类型
                    - 可能性评估
                    - 简要描述
                    
                    请以JSON格式返回威胁列表。
                    """
                    
                    # 使用智能体执行这个步骤
                    result = await self.tara_agent.run(prompt)
                    
                    # 尝试从结果中提取威胁信息
                    threats = self._extract_threats_from_response(result, assets)
                else:
                    logger.warning("未找到威胁识别相关子任务，使用默认方法")
                    # 格式化资产信息
                    assets_str = "\n".join([
                        f"- {a.get('id', 'Unknown')}: {a.get('name', 'Unknown')}"
                        for a in assets[:5]  # 限制显示数量
                    ])
                    
                    # 构建提示
                    prompt = f"""
                    请基于以下已识别的资产，识别潜在的安全威胁:
                    
                    {assets_str}
                    
                    请考虑STRIDE威胁模型，并为每个威胁提供详细信息。
                    """
                    
                    # 使用智能体执行
                    result = await self.tara_agent.run(prompt)
                    threats = self._extract_threats_from_response(result, assets)
            else:
                logger.warning("智能体没有执行计划，使用默认方法识别威胁")
                # 如果没有执行计划，使用默认方式
                # 格式化资产信息
                assets_str = "\n".join([
                    f"- {a.get('id', 'Unknown')}: {a.get('name', 'Unknown')}"
                    for a in assets[:5]  # 限制显示数量
                ])
                
                # 构建提示
                prompt = f"""
                请基于以下已识别的资产，识别潜在的安全威胁:
                
                {assets_str}
                
                请考虑STRIDE威胁模型，并为每个威胁提供详细信息。
                """
                
                # 使用智能体执行
                result = await self.tara_agent.run(prompt)
                threats = self._extract_threats_from_response(result, assets)
            
            # 更新状态
            new_state["threats"] = threats
            
            # 更新已完成步骤
            completed_steps = new_state.get("completed_steps", [])
            if TaraStep.IDENTIFY_THREATS not in completed_steps:
                new_state["completed_steps"] = completed_steps + [TaraStep.IDENTIFY_THREATS]
            
            return new_state
        except Exception as e:
            logger.error(f"识别威胁失败: {str(e)}")
            return {**copy.deepcopy(state), "error": f"识别威胁失败: {str(e)}"}
        
    def _extract_threats_from_response(self, response: str, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从智能体响应中提取威胁列表
        
        Args:
            response: 智能体响应
            assets: 已识别的资产列表
            
        Returns:
            List[Dict[str, Any]]: 提取的威胁列表
        """
        import re
        import json
        
        try:
            # 尝试从响应中提取JSON格式的威胁列表
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                if isinstance(data, dict) and "threats" in data:
                    return data["threats"]
                elif isinstance(data, list):
                    return data
            
            # 如果没有找到JSON格式，则尝试从文本中提取威胁信息
            threats = []
            # 使用正则表达式匹配可能的威胁ID格式，如T001或Threat-1
            threat_ids = re.findall(r'(T\d{3}|Threat[-_]?\d+)', response)
            
            # 获取所有资产ID
            asset_ids = [a.get("id") for a in assets if "id" in a]
            if not asset_ids:
                asset_ids = ["A001", "A002", "A003"]
            
            # STRIDE威胁类型
            threat_types = ["欺骗", "篡改", "抵赖", "信息泄露", "拒绝服务", "权限提升"]
            
            # 可能性级别
            likelihood_levels = ["高", "中", "低"]
            
            for i, threat_id in enumerate(threat_ids[:15]):  # 限制最多15个威胁
                # 尝试找到与该ID相关的名称和描述
                name_match = re.search(rf'{threat_id}[^\n]*?([^\n]+)', response)
                name = name_match.group(1).strip() if name_match else f"威胁{i+1}"
                
                # 尝试找到描述
                desc_match = re.search(rf'{threat_id}.*?\n.*?描述[：:]\s*([^\n]+)', response, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else f"针对系统的潜在威胁"
                
                # 尝试找到相关资产ID
                asset_match = re.search(rf'{threat_id}.*?资产.*?(A\d+|Asset[-_]?\d+)', response, re.DOTALL)
                asset_id = asset_match.group(1) if asset_match else asset_ids[i % len(asset_ids)]
                
                # 尝试找到威胁类型
                type_match = re.search(rf'{threat_id}.*?类型[：:]\s*([^\n]+)', response, re.DOTALL)
                threat_type = type_match.group(1).strip() if type_match else threat_types[i % len(threat_types)]
                
                # 尝试找到可能性
                likelihood_match = re.search(rf'{threat_id}.*?可能性[：:]\s*([^\n]+)', response, re.DOTALL)
                likelihood = likelihood_match.group(1).strip() if likelihood_match else likelihood_levels[i % len(likelihood_levels)]
                
                # 创建威胁条目
                threats.append({
                    "id": threat_id,
                    "name": name,
                    "asset_id": asset_id,
                    "type": threat_type,
                    "likelihood": likelihood,
                    "description": description
                })
            
            # 如果未能提取到任何威胁，则创建一些默认威胁
            if not threats:
                # 为每个资产创建至少一个威胁
                for i, asset in enumerate(assets[:5]):  # 限制为前5个资产
                    asset_id = asset.get("id", f"A{i+1:03d}")
                    asset_type = asset.get("type", "未知")
                    asset_name = asset.get("name", f"资产{i+1}")
                    
                    # 根据资产类型选择适合的威胁类型
                    if asset_type == "硬件":
                        threat_type = threat_types[1]  # 篡改
                    elif asset_type == "软件":
                        threat_type = threat_types[5]  # 权限提升
                    else:
                        threat_type = threat_types[3]  # 信息泄露
                    
                    threats.append({
                        "id": f"T{i+1:03d}",
                        "name": f"{threat_type}: {asset_name}",
                        "asset_id": asset_id,
                        "type": threat_type,
                        "likelihood": "中",
                        "description": f"针对{asset_name}的{threat_type}威胁"
                    })
                
                logger.warning("未能从响应中提取威胁，使用默认威胁列表")
            
            return threats
        except Exception as e:
            logger.error(f"提取威胁信息失败: {str(e)}")
            # 返回默认威胁列表
            if assets:
                asset_id = assets[0].get("id", "A001")
                asset_name = assets[0].get("name", "未知资产")
            else:
                asset_id = "A001"
                asset_name = "车载系统"
            
            return [
                {
                    "id": "T001",
                    "name": f"未授权访问: {asset_name}",
                    "asset_id": asset_id,
                    "type": "权限提升",
                    "likelihood": "中",
                    "description": f"攻击者尝试获取对{asset_name}的未授权访问"
                }
            ]
    
    async def _analyze_risks(self, state: TaraState) -> TaraState:
        """分析风险节点"""
        try:
            # 创建新状态而不是修改现有状态
            new_state = copy.deepcopy(state)
            new_state["current_step"] = TaraStep.ANALYZE_RISKS
            
            logger.info("执行风险分析步骤")
            
            # 获取资产和威胁
            assets = new_state.get("assets", [])
            threats = new_state.get("threats", [])
            
            # 使用智能体的执行计划流程执行此步骤，而不是直接调用analyze_risks方法
            if hasattr(self.tara_agent, 'current_plan') and self.tara_agent.current_plan:
                # 查找与风险分析相关的子任务
                risk_subtask = None
                for subtask in self.tara_agent.subtasks:
                    if '风险' in subtask.get('name', '').lower():
                        risk_subtask = subtask
                        break
                
                if risk_subtask:
                    logger.info(f"找到风险分析子任务: {risk_subtask.get('name')}")
                    
                    # 格式化资产和威胁信息
                    assets_str = "\n".join([
                        f"- {a.get('id', 'Unknown')}: {a.get('name', 'Unknown')} ({a.get('type', 'Unknown')}) - 重要性: {a.get('importance', '中')}"
                        for a in assets[:5]  # 限制显示数量
                    ])
                    
                    threats_str = "\n".join([
                        f"- {t.get('id', 'Unknown')}: {t.get('name', 'Unknown')} (资产: {t.get('asset_id', 'Unknown')}) - 类型: {t.get('type', 'Unknown')}, 可能性: {t.get('likelihood', '中')}"
                        for t in threats[:5]  # 限制显示数量
                    ])
                    
                    # 构建执行提示
                    prompt = f"""
                    请执行TARA分析的风险评估步骤，基于以下资产和威胁评估风险等级:
                    
                    子任务: {risk_subtask.get('name')}
                    描述: {risk_subtask.get('description')}
                    
                    已识别的资产:
                    {assets_str}
                    
                    已识别的威胁:
                    {threats_str}
                    
                    请为每个威胁评估风险等级，考虑以下因素:
                    1. 威胁可能性
                    2. 资产重要性
                    3. 潜在影响
                    
                    风险等级矩阵:
                    - 高可能性 + 高影响 = 严重风险
                    - 高可能性 + 中影响 = 高风险
                    - 高可能性 + 低影响 = 中风险
                    - 中可能性 + 高影响 = 高风险
                    - 中可能性 + 中影响 = 中风险
                    - 中可能性 + 低影响 = 低风险
                    - 低可能性 + 高影响 = 中风险
                    - 低可能性 + 中影响 = 低风险
                    - 低可能性 + 低影响 = 可忽略风险
                    
                    请以JSON格式返回风险评估结果。
                    """
                    
                    # 使用智能体执行这个步骤
                    result = await self.tara_agent.run(prompt)
                    
                    # 尝试从结果中提取风险信息
                    risks = self._extract_risks_from_response(result, threats, assets)
                else:
                    logger.warning("未找到风险分析相关子任务，使用默认方法")
                    # 使用默认方法
                    prompt = f"""
                    请基于已识别的威胁和资产，评估系统的风险等级。
                    为每个威胁分配风险等级（严重/高/中/低/可忽略）。
                    """
                    
                    # 使用智能体执行
                    result = await self.tara_agent.run(prompt)
                    risks = self._extract_risks_from_response(result, threats, assets)
            else:
                logger.warning("智能体没有执行计划，使用默认方法分析风险")
                # 使用默认方法
                prompt = "请基于已识别的威胁和资产，评估系统的风险等级。"
                result = await self.tara_agent.run(prompt)
                risks = self._extract_risks_from_response(result, threats, assets)
            
            # 更新状态
            new_state["risks"] = risks
            
            # 更新已完成步骤
            completed_steps = new_state.get("completed_steps", [])
            if TaraStep.ANALYZE_RISKS not in completed_steps:
                new_state["completed_steps"] = completed_steps + [TaraStep.ANALYZE_RISKS]
            
            return new_state
        except Exception as e:
            logger.error(f"分析风险失败: {str(e)}")
            return {**copy.deepcopy(state), "error": f"分析风险失败: {str(e)}"}
        
    def _extract_risks_from_response(self, response: str, threats: List[Dict[str, Any]], assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从智能体响应中提取风险评估结果
        
        Args:
            response: 智能体响应
            threats: 已识别的威胁列表
            assets: 已识别的资产列表
            
        Returns:
            List[Dict[str, Any]]: 提取的风险列表
        """
        import re
        import json
        
        try:
            # 尝试从响应中提取JSON格式的风险列表
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                if isinstance(data, dict) and "risks" in data:
                    return data["risks"]
                elif isinstance(data, list):
                    return data
            
            # 如果没有找到JSON格式，则尝试从文本中提取风险信息
            risks = []
            # 使用威胁ID作为基础，创建对应的风险
            for i, threat in enumerate(threats):
                threat_id = threat.get("id", f"T{i+1:03d}")
                asset_id = threat.get("asset_id", "A001")
                
                # 查找资产重要性
                asset_importance = "中"  # 默认中等重要性
                for asset in assets:
                    if asset.get("id") == asset_id:
                        asset_importance = asset.get("importance", "中")
                        break
                
                # 获取威胁可能性
                likelihood = threat.get("likelihood", "中")
                
                # 确定影响级别
                impact_map = {"高": "高", "中": "中", "低": "低"}
                impact = impact_map.get(asset_importance, "中")
                
                # 尝试从响应中查找相应威胁的风险级别
                risk_match = re.search(rf'{threat_id}.*?风险[等级]*[：:]\s*([^\n.,]+)', response, re.DOTALL)
                
                # 使用风险矩阵确定风险级别
                risk_matrix = {
                    ("高", "高"): "严重",
                    ("高", "中"): "高",
                    ("高", "低"): "中",
                    ("中", "高"): "高",
                    ("中", "中"): "中",
                    ("中", "低"): "低",
                    ("低", "高"): "中",
                    ("低", "中"): "低",
                    ("低", "低"): "可忽略"
                }
                
                # 如果从响应中找到风险级别，优先使用它
                if risk_match:
                    risk_level = risk_match.group(1).strip()
                    # 检查风险级别是否有效
                    valid_levels = ["严重", "高", "中", "低", "可忽略"]
                    if risk_level not in valid_levels:
                        risk_level = risk_matrix.get((likelihood, impact), "中")
                else:
                    risk_level = risk_matrix.get((likelihood, impact), "中")
                
                # 创建风险条目
                risks.append({
                    "id": f"R{threat_id[1:]}",
                    "threat_id": threat_id,
                    "asset_id": asset_id,
                    "likelihood": likelihood,
                    "impact": impact,
                    "risk_level": risk_level,
                    "description": f"风险：{threat.get('name', '未知威胁')} 对资产的影响"
                })
            
            return risks
        except Exception as e:
            logger.error(f"提取风险信息失败: {str(e)}")
            # 返回默认风险列表
            if threats:
                threat = threats[0]
                return [
                    {
                        "id": f"R{threat.get('id', 'T001')[1:]}",
                        "threat_id": threat.get("id", "T001"),
                        "asset_id": threat.get("asset_id", "A001"),
                        "likelihood": threat.get("likelihood", "中"),
                        "impact": "中",
                        "risk_level": "中",
                        "description": f"风险：{threat.get('name', '未知威胁')} 的潜在影响"
                    }
                ]
            else:
                return [
                    {
                        "id": "R001",
                        "threat_id": "T001",
                        "asset_id": "A001",
                        "likelihood": "中",
                        "impact": "中",
                        "risk_level": "中",
                        "description": "未知威胁的潜在风险"
                    }
                ]
    
    async def _develop_countermeasures(self, state: TaraState) -> TaraState:
        """制定缓解措施节点"""
        try:
            # 创建新状态而不是修改现有状态
            new_state = copy.deepcopy(state)
            new_state["current_step"] = TaraStep.DEVELOP_COUNTERMEASURES
            
            # 获取风险信息
            risks = new_state.get("risks", [])
            
            # 使用子任务执行而不是直接调用generate_mitigation方法
            result = await self.tara_agent.run(f"为识别到的{len(risks)}个风险提出缓解措施")
            
            # 从响应中提取缓解措施
            countermeasures = self._extract_countermeasures_from_response(result, risks)
            
            # 更新状态
            new_state["countermeasures"] = countermeasures
            
            # 更新已完成步骤
            completed_steps = new_state.get("completed_steps", [])
            if TaraStep.DEVELOP_COUNTERMEASURES not in completed_steps:
                new_state["completed_steps"] = completed_steps + [TaraStep.DEVELOP_COUNTERMEASURES]
            
            return new_state
        except Exception as e:
            logger.error(f"制定缓解措施失败: {str(e)}")
            return {**copy.deepcopy(state), "error": f"制定缓解措施失败: {str(e)}"}
        
    def _extract_countermeasures_from_response(self, response: str, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从智能体响应中提取缓解措施
        
        Args:
            response: 智能体响应
            risks: 已识别的风险列表
            
        Returns:
            List[Dict[str, Any]]: 提取的缓解措施列表
        """
        import re
        import json
        
        try:
            # 尝试从响应中提取JSON格式的缓解措施列表
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                if isinstance(data, dict) and "countermeasures" in data:
                    return data["countermeasures"]
                elif isinstance(data, list):
                    return data
            
            # 如果没有找到JSON格式，则尝试从文本中提取缓解措施信息
            countermeasures = []
            
            # 使用风险ID作为基础，为每个风险创建缓解措施
            measure_id_counter = 1
            for risk in risks:
                risk_id = risk.get("id", f"R{measure_id_counter:03d}")
                risk_level = risk.get("risk_level", "中")
                
                # 根据风险级别确定措施数量
                num_measures = 3 if risk_level in ["严重", "高"] else (2 if risk_level == "中" else 1)
                
                # 为风险提取相关措施
                measure_match = re.search(rf'{risk_id}.*?措施[：:](.*?)(?=(?:R\d{{3}}|$))', response, re.DOTALL)
                measures_text = measure_match.group(1) if measure_match else ""
                
                # 尝试从文本中提取单独的措施
                individual_measures = re.findall(r'(?:^|\n)\s*(?:•|-|[0-9]+\.)\s*(.*?)(?=$|\n\s*(?:•|-|[0-9]+\.))', measures_text, re.DOTALL)
                
                if individual_measures:
                    # 使用提取到的具体措施
                    for i, measure_desc in enumerate(individual_measures[:num_measures]):
                        measure_type = "技术" if i == 0 else ("管理" if i == 1 else "监控")
                        countermeasures.append({
                            "id": f"M{measure_id_counter:03d}",
                            "risk_id": risk_id,
                            "name": f"{measure_type}措施: {measure_desc[:20]}...",
                            "type": measure_type,
                            "priority": "高" if risk_level in ["严重", "高"] else "中",
                            "description": measure_desc.strip()
                        })
                        measure_id_counter += 1
                else:
                    # 如果没有提取到具体措施，创建默认措施
                    measure_types = ["技术", "管理", "监控"]
                    for i in range(num_measures):
                        measure_type = measure_types[i % len(measure_types)]
                        
                        # 根据风险级别和措施类型生成描述
                        if measure_type == "技术":
                            if risk_level in ["严重", "高"]:
                                description = "实施强技术控制措施，包括加密、访问控制和安全监控"
                            else:
                                description = "实施基本技术控制措施，如基本认证和日志记录"
                        elif measure_type == "管理":
                            if risk_level in ["严重", "高"]:
                                description = "制定详细的安全策略和流程，定期审计和合规检查"
                            else:
                                description = "制定安全指南和基本流程文档"
                        else:  # 监控
                            if risk_level in ["严重", "高"]:
                                description = "实施全面的实时监控和报警系统，定期安全评估"
                            else:
                                description = "基本的日志监控和定期检查"
                        
                        countermeasures.append({
                            "id": f"M{measure_id_counter:03d}",
                            "risk_id": risk_id,
                            "name": f"{measure_type}措施 {measure_id_counter}",
                            "type": measure_type,
                            "priority": "高" if risk_level in ["严重", "高"] else "中",
                            "description": description
                        })
                        measure_id_counter += 1
            
            return countermeasures
        except Exception as e:
            logger.error(f"提取缓解措施失败: {str(e)}")
            # 返回默认缓解措施
            if risks:
                risk = risks[0]
                return [
                    {
                        "id": "M001",
                        "risk_id": risk.get("id", "R001"),
                        "name": "技术控制措施",
                        "type": "技术",
                        "priority": "高" if risk.get("risk_level") in ["严重", "高"] else "中",
                        "description": "实施技术控制措施以缓解风险"
                    },
                    {
                        "id": "M002",
                        "risk_id": risk.get("id", "R001"),
                        "name": "管理控制措施",
                        "type": "管理",
                        "priority": "中",
                        "description": "实施管理控制措施以缓解风险"
                    }
                ]
            else:
                return [
                    {
                        "id": "M001",
                        "risk_id": "R001",
                        "name": "默认技术控制措施",
                        "type": "技术",
                        "priority": "中",
                        "description": "实施默认技术控制措施"
                    }
                ]
    
    async def _generate_report(self, state: TaraState) -> TaraState:
        """生成报告节点"""
        try:
            # 创建新状态而不是修改现有状态
            new_state = copy.deepcopy(state)
            new_state["current_step"] = TaraStep.GENERATE_REPORT
            
            logger.info("执行生成TARA分析报告步骤")
            
            # 获取资产、威胁、风险和缓解措施
            assets = new_state.get("assets", [])
            threats = new_state.get("threats", [])
            risks = new_state.get("risks", [])
            countermeasures = new_state.get("countermeasures", [])
            
            # 构建提示，而不是直接调用generate_report方法
            prompt = f"""
            请基于以下TARA分析结果，生成一份完整的威胁分析与风险评估报告：
            
            1. 已识别资产: {len(assets)} 项
            2. 已识别威胁: {len(threats)} 项
            3. 风险评估: {len(risks)} 项
            4. 缓解措施: {len(countermeasures)} 项
            
            报告应包含以下部分：
            1. 执行摘要
            2. 系统概述
            3. 资产清单及分析
            4. 威胁分析
            5. 风险评估
            6. 缓解措施
            7. 结论与建议
            
            请确保报告符合车联网安全标准和法规要求。
            """
            
            # 使用智能体执行这个步骤
            result = await self.tara_agent.run(prompt)
            
            # 构建最终报告
            report = {
                "title": "车联网系统威胁分析与风险评估报告",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": "本报告提供了对车联网系统的全面安全评估，包括资产识别、威胁分析、风险评估和缓解措施建议。",
                "assets": assets,
                "threats": threats,
                "risks": risks,
                "countermeasures": countermeasures,
                "conclusion": "基于TARA分析，系统存在多项安全风险，需要实施相应的缓解措施以提高系统安全性。",
                "content": result  # 完整报告内容
            }
            
            # 更新状态
            new_state["analysis_result"] = report
            
            # 更新已完成步骤
            completed_steps = new_state.get("completed_steps", [])
            if TaraStep.GENERATE_REPORT not in completed_steps:
                new_state["completed_steps"] = completed_steps + [TaraStep.GENERATE_REPORT]
            
            new_state["status"] = "completed"
            
            return new_state
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return {**copy.deepcopy(state), "error": f"生成报告失败: {str(e)}"}
    
    async def _handle_error(self, state: TaraState) -> TaraState:
        """错误处理节点"""
        # 创建新状态而不是修改现有状态
        new_state = copy.deepcopy(state)
        new_state["status"] = "error"
        
        return new_state
    
    async def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行TARA分析图
        
        Args:
            input_data: 输入数据，包含消息和任务信息
            
        Returns:
            执行结果
        """
        try:
            # 准备初始消息
            messages = []
            
            # 将输入数据转换为消息
            if "system" in input_data:
                messages.append({"role": "system", "content": input_data["system"]})
            
            if "task" in input_data:
                messages.append({"role": "user", "content": input_data["task"]})
                
            if "detailed_description" in input_data:
                messages.append({"role": "user", "content": input_data["detailed_description"]})
            
            # 如果input_data中有messages字段，优先使用它
            if "messages" in input_data and isinstance(input_data["messages"], list):
                messages = input_data["messages"]
            
            # 准备初始状态
            initial_state = {
                "input_messages": messages,
                "current_step": "",
                "assets": [],
                "threats": [],
                "risks": [],
                "countermeasures": [],
                "analysis_result": {},
                "completed_steps": [],
                "status": "running",
                "error": None
            }
            
            # 首先生成执行计划
            logger.info("开始执行TARA分析流程")
            logger.info("第一步：生成TARA分析执行计划")
            
            # 从消息中提取任务描述
            task_description = ""
            for msg in messages:
                if msg.get("role") == "user":
                    task_description = msg.get("content", "")
                    break
            
            if not task_description:
                task_description = "对车联网系统进行TARA分析，识别威胁并评估风险"
            
            # 调用智能体的generate_plan方法生成计划
            try:
                logger.info(f"为任务生成执行计划: {task_description[:50]}...")
                plan = await self.tara_agent.generate_plan(task_description)
                
                if plan:
                    logger.info(f"成功生成执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                    # 保存计划到智能体
                    self.tara_agent.current_plan = plan
                    self.tara_agent.subtasks = plan.get('subtasks', [])
                else:
                    logger.warning("未能生成有效的执行计划，将使用默认流程")
            except Exception as e:
                logger.error(f"生成执行计划时出错: {str(e)}")
                return {
                    "success": False,
                    "error": f"生成执行计划失败: {str(e)}",
                    "status": "error"
                }
            
            # 模拟执行流程
            try:
                # 识别资产
                assets_state = await self._identify_assets(initial_state)
                if assets_state.get("error"):
                    return {
                        "success": False,
                        "error": assets_state.get("error"),
                        "status": "error"
                    }
                
                # 识别威胁
                threats_state = await self._identify_threats(assets_state)
                if threats_state.get("error"):
                    return {
                        "success": False,
                        "error": threats_state.get("error"),
                        "status": "error"
                    }
                
                # 分析风险
                risks_state = await self._analyze_risks(threats_state)
                if risks_state.get("error"):
                    return {
                        "success": False,
                        "error": risks_state.get("error"),
                        "status": "error"
                    }
                
                # 制定对策
                countermeasures_state = await self._develop_countermeasures(risks_state)
                if countermeasures_state.get("error"):
                    return {
                        "success": False,
                        "error": countermeasures_state.get("error"),
                        "status": "error"
                    }
                
                # 生成报告
                final_state = await self._generate_report(countermeasures_state)
                if final_state.get("error"):
                    return {
                        "success": False,
                        "error": final_state.get("error"),
                        "status": "error"
                    }
                
                # 处理结果
                return {
                    "success": True,
                    "result": final_state.get("analysis_result", {}),
                    "assets": final_state.get("assets", []),
                    "threats": final_state.get("threats", []),
                    "risks": final_state.get("risks", []),
                    "countermeasures": final_state.get("countermeasures", [])
                }
            
            except Exception as e:
                logger.error(f"模拟执行TARA分析流程失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"执行TARA分析流程失败: {str(e)}",
                    "status": "error"
                }
        except Exception as e:
            logger.error(f"执行TARA分析图失败: {str(e)}")
            return {
                "success": False,
                "error": f"执行TARA分析图失败: {str(e)}",
                "status": "error"
            }
    
    def get_graph_visualization(self) -> str:
        """获取图可视化表示（Mermaid格式）"""
        mermaid = """
        graph TD
            A[识别资产] --> B[识别威胁]
            B --> C[分析风险]
            C --> D[制定对策]
            D --> E[生成报告]
            E --> F[完成]
            
            A --> G[错误处理]
            B --> G
            C --> G
            D --> G
            E --> G
            G --> F
        """
        return mermaid.strip()

async def format_final_result(state):
    """格式化最终结果，整合TARA分析各阶段的输出
    
    Args:
        state: 当前状态
    
    Returns:
        Dict: 最终结果，包含TARA分析报告
    """
    agent = state["agent"]
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    # 获取最终报告内容
    try:
        final_answer = await agent.get_final_answer()
    except Exception as e:
        logger.error(f"获取最终答案时出错: {str(e)}")
        final_answer = "生成最终报告时出错，请查看日志了解详情。"
    
    # 构建报告
    report = {
        "title": "车联网系统威胁分析与风险评估报告",
        "date": date_str,
        "summary": "本报告提供了对车联网系统的全面安全评估，包括资产识别、威胁分析、风险评估和缓解措施建议。",
        "assets": getattr(agent, 'assets', []) or [
            {
                "id": "A001",
                "name": "车载中控系统",
                "type": "硬件",
                "importance": "高",
                "description": "车辆的核心控制系统，管理车辆的关键功能"
            }
        ],
        "threats": getattr(agent, 'threats', []) or [
            {
                "id": "T001",
                "name": "未授权访问: 车载中控系统",
                "asset_id": "A001",
                "type": "权限提升",
                "likelihood": "中",
                "description": "攻击者尝试获取对车载中控系统的未授权访问"
            }
        ],
        "risks": getattr(agent, 'risks', []) or [
            {
                "id": "R001",
                "threat_id": "T001",
                "asset_id": "A001",
                "likelihood": "中",
                "impact": "中",
                "risk_level": "中",
                "description": "风险：未授权访问: 车载中控系统 的潜在影响"
            }
        ],
        "countermeasures": getattr(agent, 'countermeasures', []) or [
            {
                "id": "M001",
                "risk_id": "R001",
                "name": "技术控制措施",
                "type": "技术",
                "priority": "中",
                "description": "实施技术控制措施以缓解风险"
            },
            {
                "id": "M002",
                "risk_id": "R001",
                "name": "管理控制措施",
                "type": "管理",
                "priority": "中",
                "description": "实施管理控制措施以缓解风险"
            }
        ],
        "conclusion": "基于TARA分析，系统存在多项安全风险，需要实施相应的缓解措施以提高系统安全性。",
        "content": final_answer
    }
    
    result = {
        "success": True,
        "result": report,
        "assets": report["assets"],
        "threats": report["threats"],
        "risks": report["risks"],
        "countermeasures": report["countermeasures"]
    }
    
    return result

def create_tara_flow(use_dynamic=True):
    """创建TARA分析流程
    
    Returns:
        TaraAnalysisGraph: TARA分析流程
    """
    # 如果使用动态规划流程，应该包含更多子任务和状态
    tara_flow = Graph()
    
    tara_flow.add_node("generate_plan", generate_tara_plan)
    tara_flow.add_node("identify_assets", identify_assets)
    tara_flow.add_node("identify_threats", identify_threats)
    tara_flow.add_node("analyze_risks", analyze_risks)
    tara_flow.add_node("suggest_mitigations", suggest_mitigations)
    tara_flow.add_node("generate_report", generate_report)
    
    # 添加状态转换
    tara_flow.add_edge("generate_plan", "identify_assets")
    tara_flow.add_edge("identify_assets", "identify_threats")
    tara_flow.add_edge("identify_threats", "analyze_risks")
    tara_flow.add_edge("analyze_risks", "suggest_mitigations")
    tara_flow.add_edge("suggest_mitigations", "generate_report")
    
    # 设置流程入口和出口
    tara_flow.set_entry_point("generate_plan")
    tara_flow.set_finish_point("generate_report")
    
    # 编译流程
    app = tara_flow.compile()
    
    class TaraAnalysisGraph:
        @classmethod
        async def ainvoke(cls, inputs: Dict) -> Dict:
            """执行TARA分析流程
            
            Args:
                inputs: 输入参数，包含task和agent等
            
            Returns:
                Dict: 结果字典
            """
            # 提取智能体和任务
            task = inputs.get("task", "对车联网系统进行TARA分析")
            agent = inputs.get("agent")
            
            # 初始化状态
            state = {
                "task": task,
                "agent": agent,
                "assets": [],
                "threats": [],
                "risks": [],
                "countermeasures": []
            }
            
            # 执行流程
            try:
                logger.info("开始执行TARA分析流程")
                logger.info("第一步：生成TARA分析执行计划")
                flow_result = await app.ainvoke(state)
                
                # 后处理：格式化结果
                final_result = await format_final_result(flow_result)
                
                logger.info("flow_result: %s", final_result)
                logger.info("flow_result: %s", type(final_result))
                logger.info("flow_result: %s", dir(final_result))
                
                logger.info("任务 %s 执行完成", inputs.get("task_id", "unknown"))
                return final_result
            except Exception as e:
                logger.error("TARA分析流程执行出错: %s", str(e), exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "assets": [],
                    "threats": [],
                    "risks": [],
                    "countermeasures": []
                }
    
    return TaraAnalysisGraph
