"""
KunlunSec AI Platform - 智能体交互接口模块

实现智能体之间的交互和协作功能。
"""

from typing import Dict, Any, List, Optional
from app.agent.base import BaseAgent, AgentState

class AgentInterface:
    """智能体交互接口"""
    
    @staticmethod
    async def handoff(from_agent: BaseAgent, to_agent: BaseAgent, context: Dict[str, Any]) -> None:
        """将控制权从一个智能体交接给另一个智能体"""
        # 记录交接事件
        from_agent.update_memory("system", f"交接控制权给 {to_agent.name} 智能体")
        
        # 准备上下文信息
        handoff_message = f"从 {from_agent.name} 接收任务，上下文信息如下:\n"
        for key, value in context.items():
            handoff_message += f"- {key}: {str(value)[:100]}...\n"
        
        # 将上下文传递给目标智能体
        to_agent.update_memory("system", handoff_message)
        
        # 共享最近的记忆
        await AgentInterface.share_memory(from_agent, to_agent, count=3)
    
    @staticmethod
    async def get_agent_status(agent: BaseAgent) -> AgentState:
        """获取智能体状态"""
        return agent.state
    
    @staticmethod
    async def share_memory(source_agent: BaseAgent, target_agent: BaseAgent, 
                          start_index: int = 0, count: Optional[int] = None) -> None:
        """在智能体之间共享记忆"""
        # 获取源智能体的记忆
        source_messages = source_agent.memory.messages
        
        # 确定要共享的消息范围
        if count is None:
            # 共享全部消息
            messages_to_share = source_messages[start_index:]
        else:
            # 共享指定数量的消息
            end_index = min(start_index + count, len(source_messages))
            messages_to_share = source_messages[start_index:end_index]
        
        # 将消息添加到目标智能体的记忆中
        for message in messages_to_share:
            role = message.get("role", "system")
            content = message.get("content", "")
            
            # 复制其他元数据
            metadata = {k: v for k, v in message.items() if k not in ["role", "content"]}
            
            # 添加到目标智能体的记忆
            target_agent.update_memory(role, content, **metadata)

class ExpertCommittee:
    """专家委员会协作模式"""
    
    def __init__(self, coordinator_agent: BaseAgent, expert_agents: List[BaseAgent]):
        self.coordinator = coordinator_agent
        self.experts = expert_agents
        self.voting_strategy = "majority"  # 默认采用多数投票
    
    async def deliberate(self, problem: str) -> Dict[str, Any]:
        """委员会讨论并解决问题"""
        # 1. 协调者分解问题
        sub_problems = await self._decompose_problem(problem)
        
        # 2. 分发给专家
        expert_opinions = {}
        for expert in self.experts:
            expertise = getattr(expert, "expertise_areas", [])
            relevant_problems = [p for p in sub_problems if self._is_relevant(p, expertise)]
            if relevant_problems:
                opinions = await self._get_expert_opinion(expert, relevant_problems)
                expert_opinions[expert.name] = opinions
        
        # 3. 收集并整合意见
        consensus = await self._build_consensus(expert_opinions, self.voting_strategy)
        
        # 4. 形成最终决策
        final_decision = await self._make_decision(consensus)
        
        return {
            "decision": final_decision,
            "consensus": consensus,
            "expert_opinions": expert_opinions
        }
    
    async def _decompose_problem(self, problem: str) -> List[Dict[str, Any]]:
        """分解问题"""
        # 使用协调者智能体分解问题
        # 这里简化实现
        sub_problems = [
            {"id": "SP1", "description": f"子问题1: {problem}的安全性分析", "tags": ["security"]},
            {"id": "SP2", "description": f"子问题2: {problem}的性能分析", "tags": ["performance"]},
            {"id": "SP3", "description": f"子问题3: {problem}的合规性分析", "tags": ["compliance"]}
        ]
        return sub_problems
    
    def _is_relevant(self, problem: Dict[str, Any], expertise: List[str]) -> bool:
        """判断问题是否属于专家的专业领域"""
        problem_tags = problem.get("tags", [])
        return any(tag in expertise for tag in problem_tags)
    
    async def _get_expert_opinion(self, expert: BaseAgent, problems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取专家意见"""
        # 构建请求
        problem_descriptions = "\n".join([p.get("description", "") for p in problems])
        request = f"请针对以下问题提供专业意见:\n{problem_descriptions}"
        
        # 获取专家意见
        response = await expert.run(request)
        
        # 整理结果
        opinions = {
            "expert": expert.name,
            "problems": [p.get("id") for p in problems],
            "opinion": response
        }
        
        return opinions
    
    async def _build_consensus(self, expert_opinions: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """构建共识"""
        # 实际实现将根据策略整合专家意见
        # 这里简化实现
        consensus = {
            "strategy": strategy,
            "summary": "基于专家意见的共识",
            "details": expert_opinions
        }
        return consensus
    
    async def _make_decision(self, consensus: Dict[str, Any]) -> str:
        """做出最终决策"""
        # 使用协调者智能体做出决策
        # 这里简化实现
        return "基于专家共识的最终决策"

class HierarchicalTaskDecomposition:
    """分层任务分解协作模式"""
    
    def __init__(self, planner_agent: BaseAgent, executor_agents: Dict[str, BaseAgent]):
        self.planner = planner_agent
        self.executors = executor_agents
        self.task_graph = {}  # 使用字典表示任务依赖关系
    
    async def execute_complex_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行复杂任务"""
        # 1. 规划者分解任务为层次化子任务
        task_hierarchy = await self._decompose_hierarchical(task)
        
        # 2. 构建任务依赖图
        self._build_task_graph(task_hierarchy)
        
        # 3. 按照拓扑排序执行任务
        results = await self._execute_tasks()
        
        # 4. 整合最终结果
        final_result = await self._integrate_results(results)
        
        return final_result
    
    async def _decompose_hierarchical(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分层分解任务"""
        # 使用规划者智能体分解任务
        # 这里简化实现
        return {
            "root": {
                "id": "T0",
                "name": "根任务",
                "description": task.get("description", ""),
                "children": ["T1", "T2"]
            },
            "tasks": {
                "T1": {
                    "id": "T1",
                    "name": "子任务1",
                    "description": "子任务1描述",
                    "executor_type": "tara",
                    "children": ["T3"]
                },
                "T2": {
                    "id": "T2",
                    "name": "子任务2",
                    "description": "子任务2描述",
                    "executor_type": "testcase",
                    "children": []
                },
                "T3": {
                    "id": "T3",
                    "name": "子任务3",
                    "description": "子任务3描述",
                    "executor_type": "automation",
                    "children": []
                }
            }
        }
    
    def _build_task_graph(self, task_hierarchy: Dict[str, Any]) -> None:
        """构建任务依赖图"""
        # 初始化任务图
        self.task_graph = {
            "nodes": {},
            "edges": [],
            "execution_order": []
        }
        
        # 添加节点
        tasks = task_hierarchy.get("tasks", {})
        for task_id, task_info in tasks.items():
            self.task_graph["nodes"][task_id] = {
                "info": task_info,
                "status": "pending",
                "result": None
            }
        
        # 添加边（依赖关系）
        for task_id, task_info in tasks.items():
            for child_id in task_info.get("children", []):
                self.task_graph["edges"].append((task_id, child_id))
        
        # 计算拓扑排序
        self.task_graph["execution_order"] = self._topological_sort()
    
    def _topological_sort(self) -> List[str]:
        """计算拓扑排序"""
        # 简化实现
        # 实际实现需要处理循环依赖等情况
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node_id):
            if node_id in temp_visited:
                # 检测到循环依赖
                return
            if node_id in visited:
                return
            
            temp_visited.add(node_id)
            
            # 访问所有依赖节点
            for src, dst in self.task_graph["edges"]:
                if src == node_id:
                    visit(dst)
            
            temp_visited.remove(node_id)
            visited.add(node_id)
            result.append(node_id)
        
        # 访问所有节点
        for node_id in self.task_graph["nodes"]:
            if node_id not in visited:
                visit(node_id)
        
        return result
    
    async def _execute_tasks(self) -> Dict[str, Any]:
        """执行任务"""
        results = {}
        
        # 按照拓扑排序执行任务
        for task_id in self.task_graph["execution_order"]:
            task_info = self.task_graph["nodes"][task_id]["info"]
            
            # 获取依赖任务的结果
            dependencies_results = {}
            for src, dst in self.task_graph["edges"]:
                if dst == task_id and src in results:
                    dependencies_results[src] = results[src]
            
            # 选择合适的执行者
            executor_type = task_info.get("executor_type", "default")
            executor = self.executors.get(executor_type)
            if not executor:
                self.task_graph["nodes"][task_id]["status"] = "failed"
                self.task_graph["nodes"][task_id]["result"] = {"error": f"未找到类型为 {executor_type} 的执行者"}
                continue
            
            # 执行任务
            try:
                task_result = await self._execute_single_task(executor, task_info, dependencies_results)
                results[task_id] = task_result
                
                # 更新任务状态
                self.task_graph["nodes"][task_id]["status"] = "completed"
                self.task_graph["nodes"][task_id]["result"] = task_result
            except Exception as e:
                self.task_graph["nodes"][task_id]["status"] = "failed"
                self.task_graph["nodes"][task_id]["result"] = {"error": str(e)}
        
        return results
    
    async def _execute_single_task(self, executor: BaseAgent, task_info: Dict[str, Any], 
                                 dependencies_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个任务"""
        # 构建任务请求
        request = f"执行任务: {task_info.get('name')}\n"
        request += f"描述: {task_info.get('description')}\n"
        
        if dependencies_results:
            request += "依赖任务结果:\n"
            for dep_id, dep_result in dependencies_results.items():
                request += f"- 任务 {dep_id}: {str(dep_result)[:100]}...\n"
        
        # 执行任务
        response = await executor.run(request)
        
        # 解析结果
        # 实际实现需要更复杂的结果解析
        return {
            "task_id": task_info.get("id"),
            "result": response
        }
    
    async def _integrate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """整合最终结果"""
        # 使用规划者智能体整合结果
        # 这里简化实现
        return {
            "summary": "任务执行完成",
            "results": results,
            "task_graph": self.task_graph
        }

class AdaptiveCollaboration:
    """自适应协作模式"""
    
    def __init__(self, agents_pool: Dict[str, BaseAgent], monitor_agent: BaseAgent):
        self.agents_pool = agents_pool
        self.monitor = monitor_agent
        self.active_agents = {}
        self.collaboration_strategy = "sequential"  # 默认协作策略
        self.performance_metrics = {}
    
    async def execute_with_adaptation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务并自适应调整协作策略"""
        # 1. 初始策略选择
        self.collaboration_strategy = await self._select_initial_strategy(task)
        
        # 2. 初始智能体分配
        self.active_agents = await self._allocate_initial_agents(task)
        
        # 3. 开始执行任务
        result = None
        task_completed = False
        adaptation_count = 0
        max_adaptations = 5  # 最大调整次数
        
        while not task_completed and adaptation_count < max_adaptations:
            # 执行当前策略
            execution_context = {
                "strategy": self.collaboration_strategy,
                "active_agents": self.active_agents
            }
            
            # 执行并监控
            result, metrics = await self._execute_and_monitor(task, execution_context)
            self.performance_metrics[adaptation_count] = metrics
            
            # 评估执行效果
            evaluation = await self._evaluate_execution(result, metrics)
            
            if evaluation["success"]:
                task_completed = True
            else:
                # 需要调整策略
                adaptation_count += 1
                new_strategy = await self._adapt_strategy(evaluation, task)
                new_agents = await self._adapt_agents(evaluation, task)
                
                self.collaboration_strategy = new_strategy
                self.active_agents = new_agents
        
        # 4. 返回最终结果和适应性指标
        return {
            "result": result,
            "adaptations": adaptation_count,
            "final_strategy": self.collaboration_strategy,
            "performance_metrics": self.performance_metrics
        }
    
    async def _select_initial_strategy(self, task: Dict[str, Any]) -> str:
        """选择初始协作策略"""
        # 基于任务特性选择策略
        task_complexity = task.get("complexity", "medium")
        task_type = task.get("type", "general")
        
        if task_complexity == "high" and task_type == "security_analysis":
            return "expert_committee"
        elif task_complexity == "high":
            return "hierarchical"
        else:
            return "sequential"
    
    async def _allocate_initial_agents(self, task: Dict[str, Any]) -> Dict[str, BaseAgent]:
        """初始智能体分配"""
        # 根据任务类型和策略分配智能体
        strategy = self.collaboration_strategy
        task_type = task.get("type", "general")
        
        allocated_agents = {}
        
        if strategy == "expert_committee":
            # 分配专家委员会成员
            if "security" in task_type:
                allocated_agents["coordinator"] = self.agents_pool.get("tara")
                allocated_agents["experts"] = [
                    self.agents_pool.get("testcase"),
                    self.agents_pool.get("automation")
                ]
        elif strategy == "hierarchical":
            # 分配层次任务执行者
            allocated_agents["planner"] = self.agents_pool.get("tara")
            allocated_agents["executors"] = {
                "tara": self.agents_pool.get("tara"),
                "testcase": self.agents_pool.get("testcase"),
                "automation": self.agents_pool.get("automation")
            }
        else:  # sequential
            # 分配顺序执行者
            allocated_agents["executor"] = self.agents_pool.get("tara")
        
        return allocated_agents
    
    async def _execute_and_monitor(self, task: Dict[str, Any], 
                                 execution_context: Dict[str, Any]) -> tuple:
        """执行并监控任务"""
        strategy = execution_context["strategy"]
        active_agents = execution_context["active_agents"]
        
        # 根据策略执行任务
        result = None
        if strategy == "expert_committee":
            # 执行专家委员会策略
            committee = ExpertCommittee(
                active_agents["coordinator"],
                active_agents.get("experts", [])
            )
            result = await committee.deliberate(task.get("description", ""))
        elif strategy == "hierarchical":
            # 执行层次任务分解策略
            htd = HierarchicalTaskDecomposition(
                active_agents["planner"],
                active_agents.get("executors", {})
            )
            result = await htd.execute_complex_task(task)
        else:  # sequential
            # 执行顺序策略
            executor = active_agents.get("executor")
            if executor:
                result = await executor.run(task.get("description", ""))
        
        # 收集性能指标
        metrics = await self._collect_metrics(active_agents)
        
        return result, metrics
    
    async def _collect_metrics(self, active_agents: Dict[str, Any]) -> Dict[str, Any]:
        """收集性能指标"""
        # 实际实现将收集更多指标
        metrics = {
            "execution_time": 10.5,  # 示例执行时间
            "memory_usage": 256.0,   # 示例内存使用
            "agent_states": {}
        }
        
        # 收集智能体状态
        for role, agent in active_agents.items():
            if isinstance(agent, list):
                # 处理智能体列表
                metrics["agent_states"][role] = [
                    await AgentInterface.get_agent_status(a) for a in agent
                ]
            elif isinstance(agent, dict):
                # 处理智能体字典
                metrics["agent_states"][role] = {
                    k: await AgentInterface.get_agent_status(a) 
                    for k, a in agent.items()
                }
            elif hasattr(agent, "state"):
                # 处理单个智能体
                metrics["agent_states"][role] = await AgentInterface.get_agent_status(agent)
        
        return metrics
    
    async def _evaluate_execution(self, result: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, bool]:
        """评估执行效果"""
        # 使用监控智能体评估执行效果
        # 这里简化实现
        success = True
        
        # 检查是否有失败的智能体
        for role, states in metrics.get("agent_states", {}).items():
            if isinstance(states, list):
                if any(state == AgentState.ERROR for state in states):
                    success = False
            elif isinstance(states, dict):
                if any(state == AgentState.ERROR for state in states.values()):
                    success = False
            elif states == AgentState.ERROR:
                success = False
        
        return {
            "success": success,
            "metrics": metrics
        }
    
    async def _adapt_strategy(self, evaluation: Dict[str, Any], task: Dict[str, Any]) -> str:
        """基于执行评估调整协作策略"""
        current_strategy = self.collaboration_strategy
        
        # 根据评估结果调整策略
        if not evaluation["success"]:
            if current_strategy == "sequential":
                # 从顺序策略升级到层次策略
                return "hierarchical"
            elif current_strategy == "hierarchical":
                # 从层次策略升级到专家委员会策略
                return "expert_committee"
        
        # 如果当前策略成功或已经是最高级策略，则保持不变
        return current_strategy
    
    async def _adapt_agents(self, evaluation: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, BaseAgent]:
        """基于执行评估调整参与智能体"""
        new_strategy = await self._adapt_strategy(evaluation, task)
        
        # 如果策略改变，重新分配智能体
        if new_strategy != self.collaboration_strategy:
            return await self._allocate_initial_agents({**task, "type": task.get("type", "general")})
        
        # 如果策略未改变，但有智能体失败，替换失败的智能体
        current_agents = self.active_agents
        metrics = evaluation.get("metrics", {})
        agent_states = metrics.get("agent_states", {})
        
        for role, states in agent_states.items():
            if isinstance(states, list):
                # 处理智能体列表
                for i, state in enumerate(states):
                    if state == AgentState.ERROR and i < len(current_agents.get(role, [])):
                        # 替换失败的智能体
                        agent_type = current_agents[role][i].__class__.__name__.lower()
                        replacement = self._find_replacement(agent_type)
                        if replacement:
                            current_agents[role][i] = replacement
            elif isinstance(states, dict):
                # 处理智能体字典
                for agent_type, state in states.items():
                    if state == AgentState.ERROR:
                        # 替换失败的智能体
                        replacement = self._find_replacement(agent_type)
                        if replacement and role in current_agents:
                            current_agents[role][agent_type] = replacement
            elif states == AgentState.ERROR:
                # 处理单个智能体
                agent_type = current_agents.get(role).__class__.__name__.lower()
                replacement = self._find_replacement(agent_type)
                if replacement:
                    current_agents[role] = replacement
        
        return current_agents
    
    def _find_replacement(self, agent_type: str) -> Optional[BaseAgent]:
        """查找替代智能体"""
        # 在智能体池中查找同类型的替代智能体
        for name, agent in self.agents_pool.items():
            if agent_type in name.lower() and agent not in self.active_agents.values():
                return agent
        return None 

class AgentFactory:
    """智能体工厂，负责创建和管理不同类型的智能体"""
    
    def __init__(self):
        """初始化智能体工厂"""
        self.agents_cache = {}  # 缓存已创建的智能体
        
    async def get_agent(self, agent_type: str) -> BaseAgent:
        """
        获取指定类型的智能体
        
        Args:
            agent_type: 智能体类型，例如 'tara', 'testcase', 'automation', 'report', 'toolcall'
            
        Returns:
            对应类型的智能体实例
        """
        # 规范化智能体类型
        agent_type = agent_type.lower()
        
        # 检查缓存
        if agent_type in self.agents_cache:
            return self.agents_cache[agent_type]
        
        # 根据类型创建智能体
        agent = None
        if agent_type == "tara":
            from app.agent.tara import TaraAgent
            agent = await TaraAgent.create()
        elif agent_type == "testcase":
            from app.agent.testcase import TestCaseAgent
            agent = await TestCaseAgent.create()
        elif agent_type == "automation" or agent_type == "automationtest":
            from app.agent.automation import AutomationTestAgent
            agent = await AutomationTestAgent.create()
        elif agent_type == "report" or agent_type == "reportanalysis":
            from app.agent.report import ReportAnalysisAgent
            agent = await ReportAnalysisAgent.create()
        elif agent_type == "toolcall":
            from app.agent.toolcall import ToolCallAgent
            agent = await ToolCallAgent.create()
        elif agent_type == "react":
            from app.agent.react import ReactAgent
            agent = await ReactAgent.create()
        elif agent_type == "mcp":
            from app.agent.mcp import MCPAgent
            agent = await MCPAgent.create()
        elif agent_type == "browser":
            from app.agent.browser.browser import BrowserAgent
            agent = await BrowserAgent.create()
        elif agent_type == "collaboration":
            from app.agent.collaboration import CollaborationAgent
            agent = await CollaborationAgent.create()
        elif agent_type == "data":
            from app.agent.data import DataAnalysisAgent
            agent = await DataAnalysisAgent.create()
        else:
            # 默认使用ToolCallAgent
            from app.agent.toolcall import ToolCallAgent
            agent = await ToolCallAgent.create()
            
        # 缓存智能体
        self.agents_cache[agent_type] = agent
        
        return agent
    
    async def create_agent(self, agent_type: str, **kwargs) -> BaseAgent:
        """
        创建指定类型的智能体（不使用缓存）
        
        Args:
            agent_type: 智能体类型
            **kwargs: 智能体初始化参数
            
        Returns:
            新创建的智能体实例
        """
        # 规范化智能体类型
        agent_type = agent_type.lower()
        
        # 根据类型创建智能体
        if agent_type == "tara":
            from app.agent.tara import TaraAgent
            return await TaraAgent.create(**kwargs)
        elif agent_type == "testcase":
            from app.agent.testcase import TestCaseAgent
            return await TestCaseAgent.create(**kwargs)
        elif agent_type == "automation" or agent_type == "automationtest":
            from app.agent.automation import AutomationTestAgent
            return await AutomationTestAgent.create(**kwargs)
        elif agent_type == "report" or agent_type == "reportanalysis":
            from app.agent.report import ReportAnalysisAgent
            return await ReportAnalysisAgent.create(**kwargs)
        elif agent_type == "toolcall":
            from app.agent.toolcall import ToolCallAgent
            return await ToolCallAgent.create(**kwargs)
        elif agent_type == "react":
            from app.agent.react import ReactAgent
            return await ReactAgent.create(**kwargs)
        elif agent_type == "mcp":
            from app.agent.mcp import MCPAgent
            return await MCPAgent.create(**kwargs)
        elif agent_type == "browser":
            from app.agent.browser.browser import BrowserAgent
            return await BrowserAgent.create(**kwargs)
        elif agent_type == "collaboration":
            from app.agent.collaboration import CollaborationAgent
            return await CollaborationAgent.create(**kwargs)
        elif agent_type == "data":
            from app.agent.data import DataAnalysisAgent
            return await DataAnalysisAgent.create(**kwargs)
        else:
            # 默认使用ToolCallAgent
            from app.agent.toolcall import ToolCallAgent
            return await ToolCallAgent.create(**kwargs)
    
    def clear_cache(self):
        """清除智能体缓存"""
        self.agents_cache = {} 