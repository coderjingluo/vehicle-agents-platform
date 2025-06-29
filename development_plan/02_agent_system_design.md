# 智能体系统详细设计

## 1. 智能体架构

参考OpenManus项目的智能体设计，我们将采用多层次的智能体架构，每个智能体都具有特定的专业领域和能力。智能体系统的设计将遵循以下原则：

- **模块化**: 每个智能体都是独立的模块，可以单独使用或与其他智能体协作
- **可扩展性**: 便于添加新的专业化智能体
- **高内聚低耦合**: 智能体内部功能高度内聚，智能体之间通过标准化接口交互
- **状态管理**: 明确的状态转换和错误处理

### 1.1 智能体类层次结构

```
BaseAgent (基础智能体)
  ├── ReActAgent (思考-行动-观察型智能体)
  │     └── ToolCallAgent (工具调用智能体)
  │           ├── TaraAgent (TARA分析智能体)
  │           ├── TestCaseAgent (测试用例智能体)
  │           ├── AutomationTestAgent (自动化测试智能体)
  │           └── ReportAnalysisAgent (报告分析智能体)
  └── DataAnalysisAgent (数据分析智能体)
```

### 1.2 智能体状态模型

借鉴OpenManus的智能体状态模型，我们定义以下状态：

```python
class AgentState(str, Enum):
    """智能体执行状态"""
    IDLE = "IDLE"           # 空闲状态
    RUNNING = "RUNNING"     # 运行中
    FINISHED = "FINISHED"   # 执行完成
    ERROR = "ERROR"         # 错误状态
```

## 2. 基础智能体设计 (BaseAgent)

### 2.1 核心属性

```python
class BaseAgent(BaseModel, ABC):
    """智能体基类"""
    
    # 核心属性
    name: str                               # 智能体名称
    description: Optional[str] = None       # 智能体描述
    
    # 提示语
    system_prompt: Optional[str] = None     # 系统级指令提示
    next_step_prompt: Optional[str] = None  # 下一步行动提示
    
    # 依赖组件
    llm: LLM                                # 语言模型实例
    memory: Memory                          # 智能体记忆存储
    state: AgentState = AgentState.IDLE     # 当前状态
    
    # 执行控制
    max_steps: int = 10                     # 最大执行步骤数
    current_step: int = 0                   # 当前执行步骤
    duplicate_threshold: int = 2            # 重复内容检测阈值
```

### 2.2 核心方法

```python
class BaseAgent(BaseModel, ABC):
    # 初始化方法
    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """初始化智能体"""
    
    # 状态上下文管理
    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """安全的状态转换上下文管理器"""
    
    # 记忆更新方法
    def update_memory(self, role: ROLE_TYPE, content: str, **kwargs):
        """添加消息到智能体记忆"""
    
    # 主执行循环
    async def run(self, request: Optional[str] = None) -> str:
        """执行智能体主循环"""
    
    # 单步执行方法(抽象)
    @abstractmethod
    async def step(self) -> str:
        """执行单个步骤(子类必须实现)"""
    
    # 循环检测与处理
    def is_stuck(self) -> bool:
        """检测是否陷入循环"""
    
    def handle_stuck_state(self):
        """处理循环状态"""
```

## 3. ReAct智能体设计 (ReActAgent)

ReAct模式是"Reasoning and Acting"的缩写，是一种让语言模型通过思考-行动-观察循环来解决问题的方法。

```python
class ReActAgent(BaseAgent, ABC):
    """ReAct模式智能体"""
    
    name: str
    description: Optional[str] = None
    
    system_prompt: Optional[str] = None
    next_step_prompt: Optional[str] = None
    
    llm: Optional[LLM] = Field(default_factory=LLM)
    memory: Memory = Field(default_factory=Memory)
    state: AgentState = AgentState.IDLE
    
    max_steps: int = 10
    current_step: int = 0
    
    @abstractmethod
    async def think(self) -> bool:
        """处理当前状态并决定下一步行动"""
    
    @abstractmethod
    async def act(self) -> str:
        """执行决定的行动"""
    
    async def step(self) -> str:
        """执行单个步骤: 思考和行动"""
        should_act = await self.think()
        if not should_act:
            return "思考完成 - 无需行动"
        return await self.act()
```

## 4. 工具调用智能体设计 (ToolCallAgent)

工具调用智能体是实际应用最广泛的智能体类型，能够调用各种工具来解决问题。

```python
class ToolCallAgent(ReActAgent):
    """工具调用智能体"""
    
    name: str = "toolcall"
    description: str = "能够执行工具调用的智能体"
    
    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT
    
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        CreateChatCompletion(), Terminate()
    ))
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])
    
    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None
    
    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None
    
    async def think(self) -> bool:
        """处理当前状态并决定使用工具"""
        # 调用LLM，获取带有工具选择的回应
        # 处理不同的工具选择模式
        # 将助手消息添加到记忆
        # 返回是否需要行动
    
    async def act(self) -> str:
        """执行工具调用并处理结果"""
        # 如果没有工具调用，根据模式返回
        # 执行每个工具调用
        # 将工具响应添加到记忆
        # 返回结果
    
    async def execute_tool(self, command: ToolCall) -> str:
        """执行单个工具调用并进行错误处理"""
        # 验证命令格式
        # 解析参数并执行工具
        # 处理特殊工具
        # 格式化结果
    
    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """处理特殊工具执行和状态变更"""
    
    def _is_special_tool(self, name: str) -> bool:
        """检查工具名称是否在特殊工具列表中"""
    
    async def cleanup(self):
        """清理智能体使用的资源"""
```

## 5. 专业智能体设计

### 5.1 TARA分析智能体 (TaraAgent)

```python
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
    
    async def think(self) -> bool:
        """处理当前状态和决定下一步行动，支持浏览器上下文"""
        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
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
    
    async def assess_risk(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估威胁的风险等级"""
    
    async def generate_mitigation(self, risk_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成缓解措施建议"""
```

### 5.2 测试用例智能体 (TestCaseAgent)

```python
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
    
    # 测试用例特定方法
    async def generate_test_cases(self, tara_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于TARA结果生成测试用例"""
    
    async def analyze_coverage(self, test_cases: List[Dict[str, Any]], threats: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析测试用例对威胁的覆盖率"""
```

### 5.3 自动化测试智能体 (AutomationTestAgent)

```python
class AutomationTestAgent(ToolCallAgent):
    """自动化测试执行智能体"""
    
    name: str = "AutomationTest"
    description: str = "基于测试用例执行自动化测试的专业智能体"
    
    system_prompt: str = AUTOMATION_TEST_SYSTEM_PROMPT
    next_step_prompt: str = AUTOMATION_TEST_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletion(),
        Terminate(),
        PlanningTool(),
        
        # 专业工具
        TestExecutorTool(),
        TestEnvironmentTool(),
        CodeGeneratorTool(),
        FileOperatorTool(),
    ))
    
    # MCP客户端
    mcp_clients: MCPClients = Field(default_factory=MCPClients)
    
    # 自动化测试特定属性
    test_environments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    test_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # 添加沙盒管理器
    sandbox_manager: SandboxManager = Field(default_factory=SandboxManager)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "AutomationTestAgent":
        """创建并初始化自动化测试智能体"""
        instance = cls(**kwargs)
        await instance.initialize_environments()
        await instance.initialize_mcp_connections()
        return instance
    
    async def initialize_environments(self):
        """初始化测试环境配置"""
    
    async def initialize_mcp_connections(self):
        """初始化MCP工具连接"""
    
    # 自动化测试特定方法
    async def prepare_test_environment(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备测试环境"""
    
    async def generate_test_scripts(self, test_cases: List[Dict[str, Any]]) -> Dict[str, str]:
        """生成测试脚本"""
    
    async def execute_tests(self, test_scripts: Dict[str, str], environment: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """执行测试脚本并收集结果"""
    
    async def execute_test_in_sandbox(self, test_script: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """在沙盒中执行测试"""
        return await self.sandbox_manager.run_test_in_sandbox(test_script, environment)
```

### 5.4 报告分析智能体 (ReportAnalysisAgent)

```python
class ReportAnalysisAgent(ToolCallAgent):
    """测试报告分析智能体"""
    
    name: str = "ReportAnalysis"
    description: str = "基于测试结果生成分析报告的专业智能体"
    
    system_prompt: str = REPORT_ANALYSIS_SYSTEM_PROMPT
    next_step_prompt: str = REPORT_ANALYSIS_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletion(),
        Terminate(),
        PlanningTool(),
        
        # 专业工具
        ReportGeneratorTool(),
        DataVisualizationTool(),
        FileOperatorTool(),
        RagQueryTool(),
    ))
    
    # 报告分析特定属性
    report_templates: Dict[str, str] = Field(default_factory=dict)
    issue_categories: Dict[str, List[str]] = Field(default_factory=dict)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "ReportAnalysisAgent":
        """创建并初始化报告分析智能体"""
        instance = cls(**kwargs)
        await instance.initialize_templates()
        await instance.initialize_categories()
        return instance
    
    async def initialize_templates(self):
        """初始化报告模板"""
    
    async def initialize_categories(self):
        """初始化问题分类"""
    
    # 报告分析特定方法
    async def analyze_test_results(self, test_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果，识别问题"""
    
    async def categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """对问题进行分类"""
    
    async def generate_risk_matrix(self, issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成风险矩阵"""
    
    async def generate_report(self, analysis_data: Dict[str, Any]) -> str:
        """生成综合分析报告"""
```

### 5.5 数据分析智能体 (DataAnalysisAgent)

```python
class DataAnalysisAgent(BaseAgent):
    """专门处理数据分析的智能体"""
    
    name: str = "DataAnalysis"
    description: str = "专门处理数据分析和可视化的智能体"
    
    system_prompt: str = DATA_ANALYSIS_SYSTEM_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        PythonExecute(),
        DataVisualizationTool(),
        FileOperatorTool(),
    ))
    
    # 数据分析特定方法
    async def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据并生成结果"""
    
    async def visualize_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成数据可视化"""
    
    async def step(self) -> str:
        """执行数据分析步骤"""
```

## 6. 多智能体协作

### 6.1 智能体协作模式

参考OpenManus的Flow系统设计，我们将通过以下方式实现智能体协作：

1. **流程控制**: 通过Flow系统控制多个智能体的执行顺序
2. **数据共享**: 通过标准化的数据结构在智能体间传递数据
3. **状态监控**: 集中跟踪各智能体的执行状态
4. **事件通知**: 使用事件系统进行智能体间通信

### 6.2 智能体交互接口

```python
class AgentInterface:
    """智能体交互接口"""
    
    @staticmethod
    async def handoff(from_agent: BaseAgent, to_agent: BaseAgent, context: Dict[str, Any]) -> None:
        """将控制权从一个智能体交接给另一个智能体"""
    
    @staticmethod
    async def get_agent_status(agent: BaseAgent) -> AgentState:
        """获取智能体状态"""
    
    @staticmethod
    async def share_memory(source_agent: BaseAgent, target_agent: BaseAgent, 
                          start_index: int = 0, count: Optional[int] = None) -> None:
        """在智能体之间共享记忆"""
``` 

### 6.3 高级协作模式

为了支持更复杂的车联网安全测试场景，我们设计了以下高级协作模式：

#### 6.3.1 专家委员会模式

当面对复杂决策时，多个专业智能体组成委员会，各自提供专业意见，然后通过投票或共识机制做出最终决策。

```python
class ExpertCommittee:
    """专家委员会协作模式"""
    
    def __init__(self, coordinator_agent: BaseAgent, expert_agents: List[BaseAgent]):
        self.coordinator = coordinator_agent
        self.experts = expert_agents
        self.voting_strategy = "majority"  # 默认采用多数投票
    
    async def deliberate(self, problem: str) -> Dict[str, Any]:
        """委员会讨论并解决问题"""
        # 1. 协调者分解问题
        sub_problems = await self.coordinator.decompose_problem(problem)
        
        # 2. 分发给专家
        expert_opinions = {}
        for expert in self.experts:
            expertise = expert.expertise_areas
            relevant_problems = [p for p in sub_problems if self._is_relevant(p, expertise)]
            if relevant_problems:
                opinions = await expert.analyze(relevant_problems)
                expert_opinions[expert.name] = opinions
        
        # 3. 收集并整合意见
        consensus = await self.coordinator.build_consensus(expert_opinions, self.voting_strategy)
        
        # 4. 形成最终决策
        final_decision = await self.coordinator.make_decision(consensus)
        
        return {
            "decision": final_decision,
            "consensus": consensus,
            "expert_opinions": expert_opinions
        }
    
    def _is_relevant(self, problem: Dict[str, Any], expertise: List[str]) -> bool:
        """判断问题是否属于专家的专业领域"""
        problem_tags = problem.get("tags", [])
        return any(tag in expertise for tag in problem_tags)
```

#### 6.3.2 分层任务分解模式

针对复杂的车联网安全测试任务，采用分层任务分解模式，将大型任务分解为多层次的子任务网络。

```python
class HierarchicalTaskDecomposition:
    """分层任务分解协作模式"""
    
    def __init__(self, planner_agent: BaseAgent, executor_agents: Dict[str, BaseAgent]):
        self.planner = planner_agent
        self.executors = executor_agents
        self.task_graph = nx.DiGraph()  # 使用有向图表示任务依赖关系
    
    async def execute_complex_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行复杂任务"""
        # 1. 规划者分解任务为层次化子任务
        task_hierarchy = await self.planner.decompose_hierarchical(task)
        
        # 2. 构建任务依赖图
        self._build_task_graph(task_hierarchy)
        
        # 3. 按照拓扑排序执行任务
        results = {}
        for task_id in nx.topological_sort(self.task_graph):
            task_info = self.task_graph.nodes[task_id]["info"]
            
            # 获取依赖任务的结果
            dependencies_results = {}
            for dep_id in self.task_graph.predecessors(task_id):
                dependencies_results[dep_id] = results[dep_id]
            
            # 选择合适的执行者
            executor_type = task_info.get("executor_type", "default")
            executor = self.executors.get(executor_type)
            if not executor:
                raise ValueError(f"未找到类型为 {executor_type} 的执行者")
            
            # 执行任务并存储结果
            task_result = await executor.execute_task(task_info, dependencies_results)
            results[task_id] = task_result
            
            # 更新任务状态
            self.task_graph.nodes[task_id]["status"] = "completed"
            self.task_graph.nodes[task_id]["result"] = task_result
        
        # 4. 整合最终结果
        return await self.planner.integrate_results(results, self.task_graph)
    
    def _build_task_graph(self, task_hierarchy: Dict[str, Any]) -> None:
        """构建任务依赖图"""
        # 实现任务图构建逻辑
```

#### 6.3.3 自适应协作模式

根据任务执行过程中的反馈和环境变化，动态调整智能体协作策略。

```python
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
            evaluation = await self.monitor.evaluate_execution(result, metrics)
            
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
    
    async def _adapt_strategy(self, evaluation: Dict[str, Any], task: Dict[str, Any]) -> str:
        """基于执行评估调整协作策略"""
        # 实现策略调整逻辑
        
    async def _adapt_agents(self, evaluation: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, BaseAgent]:
        """基于执行评估调整参与智能体"""
        # 实现智能体调整逻辑
```

## 7. 沙盒执行环境集成

参考OpenManus的沙盒执行环境设计，我们将实现一个安全的代码执行环境，以保证车联网安全测试代码能够在隔离环境中安全执行。

### 7.1 沙盒管理器

```python
class SandboxManager:
    """沙盒管理器，负责创建和维护执行沙盒"""
    
    async def create_sandbox(self, config: Optional[SandboxSettings] = None) -> DockerSandbox:
        """创建执行沙盒"""
        try:
            # 创建沙盒实例
            sandbox = DockerSandbox(config)
            await sandbox.create()
            return sandbox
        except Exception as e:
            logger.error(f"创建沙盒失败: {str(e)}")
            raise SandboxError(f"创建沙盒失败: {str(e)}")
    
    async def run_test_in_sandbox(self, test_script: str, environment: Dict[str, str]) -> Dict[str, Any]:
        """在沙盒中执行测试脚本"""
        sandbox = await self.create_sandbox()
        try:
            # 写入测试脚本
            await sandbox.write_file("/tmp/test_script.py", test_script)
            
            # 设置环境变量
            env_vars = " ".join(f"{k}='{v}'" for k, v in environment.items())
            
            # 执行测试
            result = await sandbox.run_command(f"{env_vars} python /tmp/test_script.py")
            
            return {"output": result, "status": "success"}
        except Exception as e:
            return {"output": str(e), "status": "failed"}
        finally:
            # 清理资源
            await sandbox.cleanup()
```

### 7.2 Docker沙盒实现

```python
class DockerSandbox:
    """Docker沙盒环境"""
    
    def __init__(self, config: Optional[SandboxSettings] = None, 
                volume_bindings: Optional[Dict[str, str]] = None):
        """初始化沙盒实例"""
        self.config = config or SandboxSettings()
        self.volume_bindings = volume_bindings or {}
        self.client = docker.from_env()
        self.container = None
        self.terminal = None
    
    async def create(self) -> "DockerSandbox":
        """创建并启动沙盒容器"""
        try:
            # 准备容器配置
            host_config = self.client.api.create_host_config(
                mem_limit=self.config.memory_limit,
                cpu_period=100000,
                cpu_quota=int(100000 * self.config.cpu_limit),
                network_mode="none" if not self.config.network_enabled else "bridge",
                binds=self._prepare_volume_bindings(),
            )
            
            # 生成唯一容器名
            container_name = f"sandbox_{uuid.uuid4().hex[:8]}"
            
            # 创建容器
            container = await asyncio.to_thread(
                self.client.api.create_container,
                image=self.config.image,
                command="tail -f /dev/null",
                hostname="sandbox",
                working_dir=self.config.work_dir,
                host_config=host_config,
                name=container_name,
                tty=True,
                detach=True,
            )
            
            self.container = self.client.containers.get(container["Id"])
            
            # 启动容器
            await asyncio.to_thread(self.container.start)
            
            # 初始化终端
            self.terminal = AsyncDockerizedTerminal(
                container["Id"], 
                self.config.work_dir,
                env_vars={"PYTHONUNBUFFERED": "1"}
            )
            await self.terminal.init()
            
            return self
        except Exception as e:
            await self.cleanup()  # 确保资源被清理
            raise RuntimeError(f"创建沙盒失败: {e}")
    
    async def run_command(self, cmd: str, timeout: Optional[int] = None) -> str:
        """在沙盒中运行命令"""
        if not self.terminal:
            raise RuntimeError("沙盒未初始化")
            
        try:
            return await self.terminal.run_command(
                cmd, timeout=timeout or self.config.timeout
            )
        except TimeoutError:
            raise SandboxTimeoutError(
                f"命令执行超时，超过{timeout or self.config.timeout}秒"
            )
    
    async def read_file(self, path: str) -> str:
        """读取容器中的文件内容"""
        # 实现文件读取逻辑
    
    async def write_file(self, path: str, content: str) -> None:
        """写入内容到容器中的文件"""
        # 实现文件写入逻辑
    
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        if self.container:
            try:
                await asyncio.to_thread(self.container.stop)
                await asyncio.to_thread(self.container.remove)
            except Exception as e:
                logger.error(f"清理沙盒资源失败: {e}")
```

### 7.3 沙盒设置模型

```python
class SandboxSettings(BaseModel):
    """沙盒配置"""
    
    use_sandbox: bool = Field(False, description="是否使用沙盒")
    image: str = Field("python:3.12-slim", description="基础镜像")
    work_dir: str = Field("/workspace", description="容器工作目录")
    memory_limit: str = Field("512m", description="内存限制")
    cpu_limit: float = Field(1.0, description="CPU限制")
    timeout: int = Field(300, description="默认命令超时时间（秒）")
    network_enabled: bool = Field(False, description="是否允许网络访问")
```

### 7.4 智能体与沙盒集成

```python
class AutomationTestAgent(ToolCallAgent):
    # 添加沙盒管理器
    sandbox_manager: SandboxManager = Field(default_factory=SandboxManager)
    
    async def execute_test_in_sandbox(self, test_script: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """在沙盒中执行测试"""
        return await self.sandbox_manager.run_test_in_sandbox(test_script, environment)
``` 

## 8. 智能体框架集成

基于对项目需求的分析和对现有智能体框架的评估，我们推荐使用LangGraph作为智能体协作的核心框架，同时结合LangChain组件库的丰富功能。

### 8.1 LangGraph集成方案

LangGraph是基于LangChain构建的高级工作流框架，专门为复杂的多步骤、多智能体协作设计，非常适合我们的车联网安全测试场景。

```python
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

class TaraAgentGraph:
    """基于LangGraph实现的TARA分析智能体图"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tara_agent = None
        self.tools_map = {}
        self.graph = None
        self.checkpointer = MemorySaver()
        
    async def setup(self):
        """设置智能体和工具"""
        # 初始化TARA智能体
        self.tara_agent = await TaraAgent.create()
        
        # 配置工具
        self.tools_map = {
            "tara_analysis": self.tara_agent.analyze_threat,
            "risk_assessment": self.tara_agent.assess_risk,
            "mitigation": self.tara_agent.generate_mitigation,
        }
        
        # 构建工作流图
        self._build_graph()
        
    def _build_graph(self):
        """构建TARA分析工作流图"""
        from typing import TypedDict, List, Dict, Any
        
        class TaraState(TypedDict):
            """TARA分析状态"""
            target_system: str
            assets: List[Dict[str, Any]]
            threats: Dict[str, Dict[str, Any]]
            risks: Dict[str, Dict[str, Any]]
            mitigations: Dict[str, List[Dict[str, Any]]]
            status: str
            current_stage: str
            error: Optional[str]
        
        # 创建状态图
        self.graph = StateGraph(TaraState)
        
        # 添加节点
        self.graph.add_node("identify_assets", self._identify_assets)
        self.graph.add_node("analyze_threats", self._analyze_threats)
        self.graph.add_node("assess_risks", self._assess_risks)
        self.graph.add_node("generate_mitigations", self._generate_mitigations)
        self.graph.add_node("check_compliance", self._check_compliance)
        self.graph.add_node("finalize_report", self._finalize_report)
        
        # 添加边
        self.graph.add_edge("identify_assets", "analyze_threats")
        self.graph.add_edge("analyze_threats", "assess_risks")
        self.graph.add_edge("assess_risks", "generate_mitigations")
        self.graph.add_edge("generate_mitigations", "check_compliance")
        self.graph.add_edge("check_compliance", "finalize_report")
        
        # 添加条件边
        self.graph.add_conditional_edges(
            "finalize_report",
            self._check_completion_condition,
            {
                "complete": END,
                "incomplete": "identify_assets"  # 如需重新分析
            }
        )
        
        # 设置入口节点
        self.graph.set_entry_point("identify_assets")
        
        # 编译图
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    async def _identify_assets(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """识别系统资产"""
        try:
            target_system = state["target_system"]
            # 使用智能体分析资产
            response = await self.tara_agent.run(
                f"识别以下车联网系统的关键资产和边界：\n\n{target_system}"
            )
            # 解析资产列表
            assets = self._parse_assets_from_response(response)
            
            return {**state, "assets": assets, "current_stage": "assets_identified"}
        except Exception as e:
            return {**state, "error": f"资产识别失败: {str(e)}"}
    
    # 其他节点处理方法...
    
    def _check_completion_condition(self, state: Dict[str, Any]) -> str:
        """检查TARA分析是否完成"""
        if state.get("error"):
            return "incomplete"
        return "complete"
    
    async def run_analysis(self, target_system: str) -> Dict[str, Any]:
        """运行完整TARA分析"""
        # 准备初始状态
        initial_state = {
            "target_system": target_system,
            "assets": [],
            "threats": {},
            "risks": {},
            "mitigations": {},
            "status": "initialized",
            "current_stage": "start",
            "error": None
        }
        
        # 执行分析流程
        try:
            result = await self.compiled_graph.invoke(initial_state)
            return result
        except Exception as e:
            return {
                **initial_state,
                "status": "error",
                "error": f"TARA分析执行失败: {str(e)}"
            }
    
    def get_analysis_visualization(self) -> str:
        """获取分析流程的可视化表示"""
        if not self.graph:
            return "图尚未构建"
        return self.graph.get_graph().draw_mermaid()
```

### 8.2 智能体适配器模式

为了便于将我们现有的智能体模型集成到LangGraph中，我们设计了智能体适配器模式：

```python
class LangGraphAgentAdapter:
    """将现有智能体适配到LangGraph框架"""
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self._setup_tools()
        
    def _setup_tools(self):
        """设置智能体工具"""
        if hasattr(self.agent, 'available_tools'):
            self.tools = self.agent.available_tools.to_dict()
        else:
            self.tools = {}
            
    def as_runnable(self) -> Runnable:
        """将智能体转换为可运行对象"""
        from langchain_core.runnables import RunnableLambda
        
        async def _run_agent(input_data):
            """包装智能体运行方法"""
            if isinstance(input_data, str):
                return await self.agent.run(input_data)
            elif isinstance(input_data, dict):
                if "query" in input_data:
                    return await self.agent.run(input_data["query"])
                elif "input" in input_data:
                    return await self.agent.run(input_data["input"])
            return await self.agent.run(str(input_data))
        
        return RunnableLambda(_run_agent)
    
    def get_tool_as_runnable(self, tool_name: str) -> Optional[Runnable]:
        """将指定工具转换为可运行对象"""
        if tool_name not in self.tools:
            return None
            
        from langchain_core.runnables import RunnableLambda
        
        tool = self.tools[tool_name]
        
        async def _run_tool(input_data):
            """包装工具运行方法"""
            if isinstance(input_data, dict):
                return await tool.run(**input_data)
            return await tool.run(input_data)
        
        return RunnableLambda(_run_tool)
```

### 8.3 框架集成到执行流系统

我们将LangGraph框架集成到执行流系统中，实现高级的流程控制和可视化：

```python
class LangGraphFlowManager(FlowManager):
    """基于LangGraph的执行流管理器"""
    
    def __init__(self, agent_factory=None):
        super().__init__(agent_factory)
        self.graph_flows = {}
        self.checkpointer = MemorySaver()  # 可替换为持久化存储
    
    async def create_graph_flow(self, flow_type: str, flow_id: str = None, 
                              name: str = None, description: str = None, 
                              **kwargs) -> str:
        """创建基于图的执行流"""
        flow_id = flow_id or str(uuid.uuid4())
        
        # 检查ID是否已存在
        if flow_id in self.flows or flow_id in self.graph_flows:
            raise ValueError(f"Flow with ID {flow_id} already exists")
        
        # 创建基于图的执行流
        if flow_type == "tara":
            graph_flow = TaraAgentGraph()
            await graph_flow.setup()
        elif flow_type == "testcase":
            graph_flow = TestCaseGenerationGraph()
            await graph_flow.setup()
        elif flow_type == "automation":
            graph_flow = AutomationTestGraph()
            await graph_flow.setup()
        else:
            raise ValueError(f"Unsupported graph flow type: {flow_type}")
        
        # 保存流程
        self.graph_flows[flow_id] = {
            "id": flow_id,
            "name": name or f"{flow_type} graph flow",
            "description": description,
            "type": flow_type,
            "graph": graph_flow,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
        return flow_id
    
    async def execute_graph_flow(self, flow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行基于图的执行流"""
        if flow_id not in self.graph_flows:
            raise ValueError(f"Graph flow with ID {flow_id} not found")
        
        flow_info = self.graph_flows[flow_id]
        graph_flow = flow_info["graph"]
        
        # 更新状态
        self.graph_flows[flow_id]["status"] = "running"
        self.graph_flows[flow_id]["started_at"] = datetime.now().isoformat()
        
        try:
            # 执行图
            if flow_info["type"] == "tara":
                result = await graph_flow.run_analysis(input_data.get("target_system", ""))
            elif flow_info["type"] == "testcase":
                result = await graph_flow.generate_test_cases(input_data.get("tara_result", {}))
            elif flow_info["type"] == "automation":
                result = await graph_flow.run_tests(input_data.get("test_cases", []))
            else:
                raise ValueError(f"Unsupported graph flow type: {flow_info['type']}")
            
            # 更新状态
            self.graph_flows[flow_id]["status"] = "completed" 
            self.graph_flows[flow_id]["completed_at"] = datetime.now().isoformat()
            self.graph_flows[flow_id]["result"] = result
            
            return result
        except Exception as e:
            # 更新状态
            self.graph_flows[flow_id]["status"] = "failed"
            self.graph_flows[flow_id]["error"] = str(e)
            self.graph_flows[flow_id]["failed_at"] = datetime.now().isoformat()
            
            raise
    
    def get_graph_flow_visualization(self, flow_id: str) -> str:
        """获取基于图的执行流的可视化表示"""
        if flow_id not in self.graph_flows:
            raise ValueError(f"Graph flow with ID {flow_id} not found")
            
        graph_flow = self.graph_flows[flow_id]["graph"]
        return graph_flow.get_analysis_visualization()
    
    def list_all_flows(self) -> List[Dict[str, Any]]:
        """列出所有执行流及其状态"""
        # 列出传统执行流
        traditional_flows = self.list_flows()
        
        # 列出基于图的执行流
        graph_flows = [
            {
                "id": flow_id,
                "name": flow_info["name"],
                "description": flow_info["description"],
                "type": flow_info["type"],
                "status": flow_info["status"],
                "is_graph_based": True
            }
            for flow_id, flow_info in self.graph_flows.items()
        ]
        
        return traditional_flows + graph_flows
``` 