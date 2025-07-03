"""
KunlunSec AI Platform - 自动化测试智能体模块

实现基于测试用例执行自动化测试的智能体。
"""

import uuid
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import Field
from datetime import datetime
import json
import re

from app.agent.toolcall import ToolCallAgent, ToolCollection
from app.tool.base import BaseTool, ToolResult
from app.tool.create_chat_completion import CreateChatCompletionTool
from app.tool.terminate import TerminateTool
from app.tool.planning import PlanningTool
from app.tool.bash import BashTool
from app.tool.test_executor import TestExecutorTool
from app.tool.file_operators import FileOperatorTool
from app.tool.code_generator import CodeGeneratorTool
from app.core.logging import logger
from app.tool.mcp import MCPTool
from app.agent.base import AgentState

# 自动化测试系统提示
AUTOMATION_SYSTEM_PROMPT = """你是一个专业的自动化测试智能体，负责生成和执行测试脚本。
你可以使用以下工具:
{tools_description}

请基于测试用例设计合适的自动化测试，并执行这些测试，最后收集和分析测试结果。
"""

AUTOMATION_NEXT_STEP_PROMPT = """请根据当前状态，决定下一步行动。
你可以执行以下操作:
1. 准备测试环境
2. 生成测试脚本
3. 执行测试
4. 分析测试结果
5. 优化测试解决方案
"""

# 沙盒相关类
class SandboxSettings:
    """沙盒配置"""
    
    def __init__(self):
        self.use_sandbox = False
        self.image = "python:3.12-slim"
        self.work_dir = "/workspace"
        self.memory_limit = "512m"
        self.cpu_limit = 1.0
        self.timeout = 300
        self.network_enabled = False

class SandboxError(Exception):
    """沙盒错误"""
    pass

class SandboxTimeoutError(SandboxError):
    """沙盒超时错误"""
    pass

class AsyncDockerizedTerminal:
    """异步Docker终端"""
    
    def __init__(self, container_id: str, work_dir: str, env_vars: Dict[str, str] = None):
        self.container_id = container_id
        self.work_dir = work_dir
        self.env_vars = env_vars or {}
    
    async def init(self):
        """初始化终端"""
        # 实际实现将初始化Docker终端
        pass
    
    async def run_command(self, cmd: str, timeout: int = 300) -> str:
        """运行命令"""
        # 实际实现将在Docker中执行命令
        return f"执行命令 {cmd} 的结果"

class SandboxManager:
    """沙盒管理器，负责创建和维护执行沙盒"""
    
    async def create_sandbox(self, config: Optional[SandboxSettings] = None) -> "DockerSandbox":
        """创建执行沙盒"""
        try:
            # 创建沙盒实例
            sandbox = DockerSandbox(config)
            await sandbox.create()
            return sandbox
        except Exception as e:
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

class DockerSandbox:
    """Docker沙盒环境"""
    
    def __init__(self, config: Optional[SandboxSettings] = None, 
                volume_bindings: Optional[Dict[str, str]] = None):
        """初始化沙盒实例"""
        self.config = config or SandboxSettings()
        self.volume_bindings = volume_bindings or {}
        self.container = None
        self.terminal = None
    
    async def create(self) -> "DockerSandbox":
        """创建并启动沙盒容器"""
        try:
            # 注意：这里只是模拟实现，实际需要使用Docker API
            print(f"创建Docker容器，使用镜像: {self.config.image}")
            
            # 初始化终端
            self.terminal = AsyncDockerizedTerminal(
                "mock_container_id", 
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
        # 模拟实现
        return f"读取文件 {path} 的内容"
    
    async def write_file(self, path: str, content: str) -> None:
        """写入内容到容器中的文件"""
        # 模拟实现
        print(f"写入内容到文件 {path}")
    
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        # 模拟实现
        print("清理沙盒资源")

# MCP客户端
class MCPClients:
    """MCP客户端集合"""
    
    def __init__(self):
        self.clients = {}
    
    def add_client(self, name: str, client: Any):
        """添加MCP客户端"""
        self.clients[name] = client
    
    def get_client(self, name: str) -> Any:
        """获取MCP客户端"""
        return self.clients.get(name)

class AutomationTestAgent(ToolCallAgent):
    """自动化测试智能体"""
    
    name: str = "automation"
    description: str = "专门设计和执行自动化测试的智能体"
    
    system_prompt: str = AUTOMATION_SYSTEM_PROMPT
    next_step_prompt: str = AUTOMATION_NEXT_STEP_PROMPT
    
    # 专业工具
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection(
        # 通用工具
        CreateChatCompletionTool(),
        TerminateTool(),
        PlanningTool(),
        BashTool(),
        
        # 专业工具
        TestExecutorTool(),
        FileOperatorTool(),
        CodeGeneratorTool(),
    ))
    
    # 增强的动态规划系统提示
    planning_system_prompt: str = """你是一个专业的自动化测试规划专家，擅长将测试任务分解为具体的测试子任务和步骤。
    你的职责是分析测试需求，设计完整的测试流程，并确保测试覆盖全面。
    请记住，测试计划必须是动态生成的，根据当前任务的具体需求来定制，而不是固定的步骤列表。"""
    
    # 自动化测试特定属性
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    test_scripts: Dict[str, str] = Field(default_factory=dict)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    failed_tests: List[str] = Field(default_factory=list)
    
    # 任务计划和执行相关属性
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    current_plan: Optional[Dict[str, Any]] = Field(default=None)
    completed_subtasks: List[str] = Field(default_factory=list)
    
    # MCP客户端
    mcp_tool: MCPTool = Field(default_factory=MCPTool)
    
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
        
    async def run(self, request: Optional[str] = None) -> str:
        """运行自动化测试智能体
        
        按照计划分解任务并按顺序执行
        
        Args:
            request: 请求内容
            
        Returns:
            str: 执行结果
        """
        if request:
            self.update_memory("user", request)
        
        try:
            # 1. 初始化环境
            await self.initialize_environments()
            await self.initialize_mcp_connections()
            
            # 2. 生成自动化测试执行计划
            logger.info("开始生成自动化测试执行计划...")
            plan = await self.generate_plan(request or "执行自动化测试")
            
            # 3. 设置计划
            self.current_plan = plan
            self.subtasks = plan.get('subtasks', [])
            
            logger.info(f"自动化测试执行计划已生成，包含 {len(self.subtasks)} 个子任务")
            
            # 4. 执行子任务 - 使用ToolCallAgent的think-act循环
            self.state = AgentState.IDLE
            self.current_step = 0
            
            while self.state != AgentState.FINISHED and self.current_step < self.max_steps:
                self.current_step += 1
                
                # 思考
                should_continue = await super().think()  # 调用父类的think方法
                if not should_continue:
                    break
                
                # 执行
                await self.act()
            
            # 5. 返回结果
            return self.get_final_answer()
            
        except Exception as e:
            logger.error(f"运行自动化测试智能体出错: {str(e)}")
            return f"错误: {str(e)}"
    
    async def initialize_environments(self):
        """初始化测试环境"""
        # 设置常用测试环境配置
        self.environment_configs = {
            "default": {
                "os": "Linux",
                "python": "3.10",
                "packages": ["pytest", "selenium", "requests"]
            },
            "web": {
                "os": "Linux",
                "python": "3.10",
                "packages": ["pytest", "selenium", "webdriver-manager"],
                "browsers": ["chrome", "firefox"]
            },
            "api": {
                "os": "Linux",
                "python": "3.10",
                "packages": ["pytest", "requests", "pydantic"]
            }
        }
        
        # 添加环境配置到内存
        self.update_memory(
            "system", 
            f"已初始化 {len(self.environment_configs)} 个测试环境配置。"
        )
    
    async def initialize_mcp_connections(self):
        """初始化MCP连接"""
        # 在实际应用中，这里会初始化与MCP服务的连接
        try:
            # 可以根据配置或环境变量来连接不同的MCP服务
            # 例如连接到本地MCP服务
            await self.mcp_tool.execute(
                operation="connect_sse",
                server_url="http://localhost:8000/mcp",
                server_id="local"
            )
            
            # 记录到内存
            self.update_memory(
                "system",
                "已初始化与MCP服务的连接"
            )
        except Exception as e:
            logger.error(f"初始化MCP连接失败: {str(e)}")
            self.update_memory(
                "system",
                f"初始化MCP连接失败: {str(e)}"
            )
    
    async def generate_plan(self, task: str) -> Dict[str, Any]:
        """为自动化测试执行任务创建详细的执行计划
        
        Args:
            task: 自动化测试任务描述
            
        Returns:
            Dict[str, Any]: 生成的执行计划
        """
        # 获取可用工具列表
        available_tools = self._get_tools_description()
        
        # 构建自动化测试专用规划提示
        automation_planning_prompt = f"""
        请为以下车联网安全自动化测试任务制定详细的执行计划:
        
        # 任务描述
        {task}
        
        # 可用工具列表
        以下是你可以在执行计划中使用的工具:
        {available_tools}
        
        # 自动化测试执行需求
        自动化测试是车联网安全验证的关键环节，需要完成以下步骤:
        1. 配置与准备测试环境
        2. 分析测试用例需求
        3. 生成测试脚本
        4. 验证测试脚本
        5. 执行测试
        6. 收集测试结果
        7. 分析失败测试
        8. 重试关键失败测试
        9. 生成测试报告
        10. 资源清理
        
        # 规划格式
        请提供JSON格式的执行计划，包含以下内容:

        ```json
        {{
            "main_task": "自动化测试执行任务描述",
            "subtasks": [
                {{
                    "id": "subtask-1",
                    "name": "子任务名称 (例如：测试环境配置)",
                    "description": "详细描述",
                    "steps": [
                        {{
                            "id": "step-1.1",
                            "description": "步骤描述",
                            "tools": ["可能需要使用的工具名称"],
                            "expected_output": "期望输出描述"
                        }},
                        // 更多步骤...
                    ],
                    "dependencies": []  // 依赖的其他子任务ID
                }},
                // 所有自动化测试执行必要的子任务...
            ]
        }}
        ```
        
        请确保规划涵盖完整的自动化测试执行流程，每个子任务和步骤都清晰可执行，且符合车联网安全测试的专业要求。
        重要：每个步骤中指定的工具必须从上面提供的"可用工具列表"中选择，不要使用列表之外的工具。
        """
        
        logger.info(f"正在为自动化测试任务制定执行计划: {task[:50]}...")
        
        try:
            # 向LLM发送规划请求
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": "你是车联网安全自动化测试专家，擅长设计结构化的测试执行计划。"},
                    {"role": "user", "content": automation_planning_prompt}
                ],
                temperature=0.2  # 使用较低的温度以获得更确定性的规划
            )
            
            # 提取JSON部分
            import re
            import json
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response
            
            try:
                # 解析JSON计划
                plan = json.loads(json_str)
                logger.info(f"成功生成自动化测试执行计划，包含 {len(plan.get('subtasks', []))} 个子任务")
                
                # 验证计划是否包含关键自动化测试执行步骤
                subtask_names = [st.get('name', '').lower() for st in plan.get('subtasks', [])]
                expected_keywords = ['环境', '测试脚本', '执行', '结果', '分析', '报告']
                
                missing_keywords = [kw for kw in expected_keywords if not any(kw in name for name in subtask_names)]
                if missing_keywords:
                    logger.warning(f"生成的自动化测试执行计划缺少关键步骤: {', '.join(missing_keywords)}")
                    
                    # 添加缺失的关键步骤
                    for kw in missing_keywords:
                        if kw == '环境':
                            plan['subtasks'].insert(0, {
                                "id": f"subtask-env-{len(plan['subtasks'])+1}",
                                "name": "测试环境配置与准备",
                                "description": "配置和准备自动化测试所需的环境",
                                "steps": [
                                    {
                                        "id": f"step-env-1",
                                        "description": "检查系统要求",
                                        "tools": ["create_chat_completion", "bash"],
                                        "expected_output": "系统环境检查报告"
                                    },
                                    {
                                        "id": f"step-env-2",
                                        "description": "配置测试依赖",
                                        "tools": ["bash", "test_executor"],
                                        "expected_output": "环境配置完成确认"
                                    }
                                ],
                                "dependencies": []
                            })
                        elif kw == '测试脚本':
                            plan['subtasks'].append({
                                "id": f"subtask-script-{len(plan['subtasks'])+1}",
                                "name": "测试脚本生成",
                                "description": "根据测试用例生成自动化测试脚本",
                                "steps": [
                                    {
                                        "id": f"step-script-1",
                                        "description": "分析测试用例",
                                        "tools": ["create_chat_completion", "file_operator"],
                                        "expected_output": "测试用例分析结果"
                                    },
                                    {
                                        "id": f"step-script-2",
                                        "description": "生成测试脚本",
                                        "tools": ["create_chat_completion", "code_generator"],
                                        "expected_output": "自动化测试脚本"
                                    }
                                ],
                                "dependencies": ["subtask-env-1"]
                            })
                        elif kw == '执行':
                            plan['subtasks'].append({
                                "id": f"subtask-exec-{len(plan['subtasks'])+1}",
                                "name": "测试执行",
                                "description": "执行自动化测试脚本",
                                "steps": [
                                    {
                                        "id": f"step-exec-1",
                                        "description": "运行测试脚本",
                                        "tools": ["test_executor", "bash"],
                                        "expected_output": "测试执行过程输出"
                                    },
                                    {
                                        "id": f"step-exec-2",
                                        "description": "监控测试执行",
                                        "tools": ["create_chat_completion", "test_executor"],
                                        "expected_output": "测试执行状态"
                                    }
                                ],
                                "dependencies": ["subtask-script-1"]
                            })
                        elif kw == '结果':
                            plan['subtasks'].append({
                                "id": f"subtask-result-{len(plan['subtasks'])+1}",
                                "name": "结果收集",
                                "description": "收集和整理测试执行结果",
                                "steps": [
                                    {
                                        "id": f"step-result-1",
                                        "description": "收集测试日志",
                                        "tools": ["test_executor", "file_operator"],
                                        "expected_output": "测试日志文件"
                                    },
                                    {
                                        "id": f"step-result-2",
                                        "description": "提取测试结果",
                                        "tools": ["create_chat_completion", "file_operator"],
                                        "expected_output": "结构化测试结果"
                                    }
                                ],
                                "dependencies": ["subtask-exec-1"]
                            })
                        elif kw == '分析':
                            plan['subtasks'].append({
                                "id": f"subtask-analysis-{len(plan['subtasks'])+1}",
                                "name": "失败测试分析",
                                "description": "分析测试失败原因",
                                "steps": [
                                    {
                                        "id": f"step-analysis-1",
                                        "description": "识别失败测试",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "失败测试清单"
                                    },
                                    {
                                        "id": f"step-analysis-2",
                                        "description": "分析失败原因",
                                        "tools": ["create_chat_completion"],
                                        "expected_output": "失败原因分析"
                                    },
                                    {
                                        "id": f"step-analysis-3",
                                        "description": "重试关键失败测试",
                                        "tools": ["test_executor"],
                                        "expected_output": "重试测试结果"
                                    }
                                ],
                                "dependencies": ["subtask-result-1"]
                            })
                        elif kw == '报告':
                            plan['subtasks'].append({
                                "id": f"subtask-report-{len(plan['subtasks'])+1}",
                                "name": "测试报告生成",
                                "description": "生成自动化测试报告",
                                "steps": [
                                    {
                                        "id": f"step-report-1",
                                        "description": "汇总测试结果",
                                        "tools": ["create_chat_completion", "file_operator"],
                                        "expected_output": "测试结果汇总"
                                    },
                                    {
                                        "id": f"step-report-2",
                                        "description": "生成测试报告",
                                        "tools": ["create_chat_completion", "file_operator"],
                                        "expected_output": "完整测试报告"
                                    }
                                ],
                                "dependencies": ["subtask-analysis-1"]
                            })
                
                # 保存计划到智能体
                self.current_plan = plan
                self.subtasks = plan.get('subtasks', [])
                
                # 将规划添加到记忆中
                self.update_memory(
                    "system",
                    f"已生成自动化测试执行计划，包含 {len(self.subtasks)} 个子任务。"
                )
                
                return plan
            except json.JSONDecodeError as e:
                logger.error(f"解析自动化测试执行计划失败: {str(e)}")
                return await super().generate_plan(task)
                
        except Exception as e:
            logger.error(f"生成自动化测试执行计划时出错: {str(e)}")
            return await super().generate_plan(task)
    
    def _get_tools_description(self) -> str:
        """获取可用工具的描述列表
        
        Returns:
            str: 格式化的工具描述列表
        """
        tool_descriptions = []
        for tool in self.available_tools.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    def _extract_test_requirements(self, task: str) -> str:
        """从任务描述中提取测试需求
        
        Args:
            task: 测试任务描述
            
        Returns:
            str: 提取的测试需求
        """
        # 简单版本: 将整个任务作为需求返回
        # 实际应用中可以使用更复杂的NLP技术提取关键需求
        return task
    
    async def think(self) -> bool:
        """增强思考过程，整合动态测试规划"""
        # 检查是否有当前测试计划和未完成的子任务
        current_subtask = self.get_next_subtask()
        
        if current_subtask and self.dynamic_planning:
            # 获取当前子任务的下一个步骤
            current_step = self.get_next_step(current_subtask.get('id', ''))
            
            if current_step:
                # 更新提示，引导模型执行当前测试步骤
                category = current_subtask.get('category', '测试')
                subtask_prompt = f"""
                当前正在执行{category}子任务: {current_subtask.get('name')}
                子任务描述: {current_subtask.get('description')}
                
                当前步骤: {current_step.get('description')}
                期望输出: {current_step.get('expected_output', '成功完成当前步骤')}
                
                请思考如何最有效地执行这个测试步骤。可以考虑使用以下工具:
                {', '.join(current_step.get('tools', []))}
                
                请执行这个具体的测试步骤，确保达到期望的输出结果。
                """
                
                self.update_memory("user", subtask_prompt)
        
        # 调用原始的思考方法
        result = await super().think()
        
        # 如果执行了步骤，更新计划进度
        if result and current_step and self.dynamic_planning:
            # 将当前步骤标记为已完成
            step_id = current_step.get('id')
            if step_id and step_id not in self.completed_steps:
                self.completed_steps.append(step_id)
            
            # 更新计划进度
            self._update_plan_progress()
        
        return result
    
    # 自动化测试特定方法
    async def prepare_environment(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备测试环境"""
        # 保存测试用例
        self.test_cases = test_cases
        
        # 使用规划工具创建准备环境的计划
        planning_tool = self.available_tools.get_tool("planning")
        if planning_tool:
            # 创建环境准备计划
            steps = [
                "检查系统要求",
                "安装必要依赖",
                "配置测试数据",
                "设置环境变量"
            ]
            
            # 根据测试用例调整步骤
            if test_cases and len(test_cases) > 0:
                test_types = set()
                for tc in test_cases:
                    if "type" in tc:
                        test_types.add(tc["type"])
                
                # 根据测试类型添加特定步骤
                for test_type in test_types:
                    steps.append(f"准备{test_type}测试环境")
            
            result = await planning_tool.execute(
                command="create",
                title="测试环境准备计划",
                steps=steps
            )
            
            return result.output
        
        return {"message": "未能创建环境准备计划"}
    
    async def generate_test_script(self, test_case: Dict[str, Any]) -> Dict[str, str]:
        """为指定测试用例生成测试脚本
        
        Args:
            test_case: 测试用例信息
            
        Returns:
            Dict[str, str]: 生成的测试脚本(脚本名:脚本内容)
        """
        # 使用代码生成工具生成测试脚本
        code_generator = self.available_tools.get_tool("code_generator")
        if not code_generator:
            return {"error": "代码生成工具不可用"}
        
        # 提取测试用例信息
        test_id = test_case.get("id", "unknown")
        title = test_case.get("title", "未命名测试")
        description = test_case.get("description", "")
        test_type = test_case.get("type", "functional")
        requirements = test_case.get("requirements", [])
        
        # 构建提示
        prompt = f"""
        请为以下测试用例生成自动化测试脚本:
        
        测试ID: {test_id}
        标题: {title}
        描述: {description}
        类型: {test_type}
        需求:
        {', '.join(requirements)}
        
        请生成Python pytest格式的测试脚本，包含必要的setup和teardown操作。
        """
        
        # 生成测试脚本
        result = await code_generator.execute(
            language="python",
            prompt=prompt,
            filename=f"test_{test_id}.py",
            framework="pytest",
            test_case=test_case
        )
        
        if hasattr(result, "output") and "code" in result.output:
            script = result.output["code"]
            self.test_scripts[test_id] = script
            return {test_id: script}
        
        return {"error": "生成测试脚本失败"}
    
    async def execute_test(self, test_id: str, script: str = None) -> Dict[str, Any]:
        """执行指定测试
        
        Args:
            test_id: 测试ID
            script: 测试脚本内容(可选，如果不提供则使用之前生成的脚本)
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        # 获取测试脚本
        if not script:
            script = self.test_scripts.get(test_id)
            if not script:
                return {"error": f"找不到测试脚本: {test_id}"}
        
        # 使用测试执行工具
        test_executor = self.available_tools.get_tool("test_executor")
        if not test_executor:
            return {"error": "测试执行工具不可用"}
        
        # 准备测试环境配置
        environment = {}
        
        # 执行测试
        result = await test_executor.execute(
            operation="execute",
            test_script=script,
            environment=environment
        )
        
        # 保存测试结果
        if hasattr(result, "output"):
            # 获取测试ID
            exec_test_id = result.output.get("test_id")
            
            # 获取测试结果
            if result.output.get("status") == "completed":
                results_response = await test_executor.execute(
                    operation="get_results",
                    test_id=exec_test_id
                )
                
                if hasattr(results_response, "output"):
                    test_result = results_response.output
                    self.test_results[test_id] = test_result
                    
                    # 检查测试是否失败
                    if test_result.get("status") != "passed" and test_id not in self.failed_tests:
                        self.failed_tests.append(test_id)
                        
                    return test_result
            
            # 返回初始执行结果
            return result.output
        
        return {"error": "执行测试失败，无结果"}
    
    async def analyze_results(self) -> Dict[str, Any]:
        """分析所有测试结果
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 计算测试统计信息
        total_tests = len(self.test_results)
        if total_tests == 0:
            return {"error": "没有可分析的测试结果"}
            
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result.get("status") == "passed")
        failed_tests = len(self.failed_tests)
        
        # 提取失败测试的详细信息
        failure_details = {}
        for test_id in self.failed_tests:
            result = self.test_results.get(test_id, {})
            failure_details[test_id] = {
                "error": result.get("error", "未知错误"),
                "traceback": result.get("traceback", "")
            }
        
        # 生成分析报告
        analysis = {
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{(passed_tests / total_tests * 100):.2f}%" if total_tests > 0 else "0%"
            },
            "failures": failure_details,
            "recommendations": []
        }
        
        # 添加改进建议
        if failed_tests > 0:
            analysis["recommendations"].append("修复失败的测试")
            
            # 使用LLM分析失败原因并提供建议
            failure_prompt = f"""
            分析以下测试失败，并提供修复建议:
            
            失败测试数: {failed_tests}
            失败详情:
            {json.dumps(failure_details, indent=2)}
            
            请提供具体的修复建议。
            """
            
            response = await self.llm.ask(
                messages=[
                    {"role": "system", "content": "你是一个专业的测试分析师，擅长分析测试失败并提供修复建议。"},
                    {"role": "user", "content": failure_prompt}
                ]
            )
            
            analysis["recommendations"].append(response)
        
        return analysis
    
    def get_final_answer(self) -> str:
        """获取最终执行结果，包含测试执行统计"""
        # 检查计划执行情况
        if self.dynamic_planning and self.current_plan:
            # 使用增强的父类方法获取基本结果
            base_result = super().get_final_answer()
            
            # 添加测试特定统计
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() 
                              if result.get("status") == "passed")
            
            test_stats = f"""
            测试执行统计:
            - 总测试数: {total_tests}
            - 通过测试: {passed_tests}
            - 失败测试: {len(self.failed_tests)}
            - 通过率: {(passed_tests / total_tests * 100):.2f}% 如果total_tests > 0 else "N/A"
            """
            
            return f"{base_result}\n\n{test_stats}"
        
        # 如果没有动态规划或测试结果，返回默认结果
        return super().get_final_answer()
        
    def summarize_execution(self) -> Dict[str, Any]:
        """总结整个测试执行过程
        
        Returns:
            Dict[str, Any]: 测试执行总结
        """
        return {
            "test_cases": len(self.test_cases),
            "test_scripts_generated": len(self.test_scripts),
            "tests_executed": len(self.test_results),
            "tests_passed": sum(1 for result in self.test_results.values() 
                             if result.get("status") == "passed"),
            "tests_failed": len(self.failed_tests),
            "dynamic_plan": self.current_plan,
            "completed_subtasks": self.completed_subtasks
        }

    async def _execute_subtasks(self) -> str:
        """执行所有子任务
        
        按照依赖关系顺序执行子任务，处理子任务间的依赖关系。
        
        Returns:
            str: 所有子任务执行的汇总结果
        """
        if not hasattr(self, 'subtasks') or not self.subtasks:
            return "没有可执行的子任务"
            
        logger.info(f"开始执行子任务序列，共 {len(self.subtasks)} 个子任务")
        
        # 初始化已完成的子任务集合
        if not hasattr(self, 'completed_subtasks'):
            self.completed_subtasks = set()
        else:
            self.completed_subtasks = set(self.completed_subtasks)
        
        results = []
        
        # 创建子任务状态映射
        subtask_status = {}
        for subtask in self.subtasks:
            subtask_id = subtask.get('id')
            if not subtask_id:
                continue
                
            if subtask_id in self.completed_subtasks:
                subtask_status[subtask_id] = 'completed'
                subtask['status'] = 'completed'
            else:
                subtask_status[subtask_id] = 'pending'
                subtask['status'] = 'pending'
        
        # 继续执行直到所有子任务完成或无法继续
        max_iterations = 2 * len(self.subtasks)  # 防止无限循环
        iterations = 0
        
        while len(self.completed_subtasks) < len(self.subtasks) and iterations < max_iterations:
            iterations += 1
            progress_made = False
            
            # 找出所有可执行的子任务（依赖已满足）
            executable_subtasks = []
            for subtask in self.subtasks:
                subtask_id = subtask.get('id')
                
                # 跳过已完成的子任务
                if subtask_id in self.completed_subtasks:
                    continue
                
                # 检查依赖是否满足
                dependencies = subtask.get('dependencies', [])
                dependencies_met = all(dep in self.completed_subtasks for dep in dependencies)
                
                if dependencies_met:
                    executable_subtasks.append(subtask)
            
            # 如果没有可执行的子任务，但仍有未完成的子任务，可能存在循环依赖
            if not executable_subtasks and len(self.completed_subtasks) < len(self.subtasks):
                logger.warning("检测到可能的循环依赖，无法继续执行子任务")
                break
            
            # 执行可执行的子任务
            for subtask in executable_subtasks:
                subtask_id = subtask.get('id')
                logger.info(f"开始执行子任务: {subtask.get('name')} (ID: {subtask_id})")
                
                subtask['status'] = 'in_progress'
                subtask_status[subtask_id] = 'in_progress'
                subtask['start_time'] = datetime.now().isoformat()
                
                # 记录当前正在执行的子任务ID，用于保持一致性
                self._current_subtask_id = subtask_id
                
                try:
                    # 执行子任务的所有步骤
                    subtask_result = await self._execute_steps(subtask)
                    subtask['result'] = subtask_result
                    subtask['status'] = 'completed'
                    subtask_status[subtask_id] = 'completed'
                    self.completed_subtasks.add(subtask_id)
                    progress_made = True
                    results.append(subtask_result)
                    
                    logger.info(f"子任务 {subtask_id} 执行完成")
                except Exception as e:
                    subtask['status'] = 'failed'
                    subtask_status[subtask_id] = 'failed'
                    logger.error(f"子任务 {subtask_id} 执行失败: {str(e)}")
                    results.append(f"子任务 {subtask_id} 执行失败: {str(e)}")
                
                subtask['end_time'] = datetime.now().isoformat()
            
            # 如果本轮没有进展，说明存在循环依赖或所有剩余任务都无法执行
            if not progress_made:
                logger.warning("无法继续执行子任务，可能存在循环依赖或所有剩余任务都无法执行")
                break
        
        # 汇总结果
        final_result = "\n\n".join(results)
        logger.info(f"所有子任务执行完成，共 {len(self.completed_subtasks)}/{len(self.subtasks)} 个子任务成功执行")
        
        return final_result
    
    async def _execute_steps(self, subtask: Dict[str, Any]) -> str:
        """执行子任务的所有步骤
        
        Args:
            subtask: 子任务信息
            
        Returns:
            str: 子任务执行结果
        """
        steps = subtask.get('steps', [])
        if not steps:
            return f"子任务 {subtask.get('name')} 没有定义步骤"
            
        results = []
        
        for step in steps:
            step_id = step.get('id')
            description = step.get('description', '未描述')
            
            logger.info(f"执行步骤: {description} (ID: {step_id})")
            
            # 标记步骤为执行中
            step['status'] = 'in_progress'
            step['start_time'] = datetime.now().isoformat()
            
            try:
                # 获取步骤指定的工具
                tools = step.get('tools', [])
                
                if not tools:
                    # 如果没有指定工具，使用create_chat_completion
                    tools = ["create_chat_completion"]
                
                # 构建执行步骤的提示
                prompt = self._build_step_execution_prompt(subtask, step)
                
                # 执行步骤
                response = await self.llm.ask(
                    messages=[
                        {"role": "system", "content": "你是自动化测试专家，正在执行测试流程中的特定步骤。"},
                        {"role": "user", "content": prompt}
                    ],
                    tools=self._prepare_tools_for_llm(tools),
                    tool_choice="auto"
                )
                
                # 处理执行结果
                step_result = ""
                if isinstance(response, str):
                    # 文本结果
                    step_result = response
                elif isinstance(response, dict):
                    # 可能包含工具调用或内容
                    if "content" in response and response["content"]:
                        step_result = response.get("content", "")
                    elif "tool_calls" in response:
                        # 处理工具调用
                        await self._process_tool_calls(response["tool_calls"])
                        # 添加工具调用结果
                        tool_result_msgs = [m for m in self.memory.get_messages() if m.get("role") == "tool"]
                        if tool_result_msgs:
                            step_result = "工具调用结果: " + ", ".join([m.get("content", "") for m in tool_result_msgs[-len(response["tool_calls"]):]])
                        else:
                            step_result = "执行了工具调用，但没有结果"
                else:
                    # 其他格式，转换为字符串
                    step_result = str(response)
                
                # 记录步骤结果
                step['result'] = step_result
                step['status'] = 'completed'
                results.append(f"步骤 {step_id}: {description}\n结果: {step_result}")
                
            except Exception as e:
                logger.error(f"执行步骤 {step_id} 时出错: {str(e)}")
                step['status'] = 'failed'
                step['error'] = str(e)
                results.append(f"步骤 {step_id}: {description} 执行失败: {str(e)}")
                # 继续执行其他步骤，而不是中断
            
            step['end_time'] = datetime.now().isoformat()
            
        # 返回所有步骤的结果
        return "\n\n".join(results)
    
    def _build_step_execution_prompt(self, subtask: Dict[str, Any], step: Dict[str, Any]) -> str:
        """构建执行步骤的提示
        
        Args:
            subtask: 子任务信息
            step: 步骤信息
            
        Returns:
            str: 提示内容
        """
        # 获取已完成步骤的结果，作为上下文
        context = []
        subtask_steps = subtask.get('steps', [])
        for prev_step in subtask_steps:
            if prev_step.get('id') == step.get('id'):
                # 当前步骤，跳过
                break
                
            if prev_step.get('status') in ['completed', '已完成']:
                # 添加已完成步骤的结果
                prev_result = prev_step.get('result', '无结果')
                context.append(f"步骤 {prev_step.get('id')}: {prev_step.get('description')}\n结果: {prev_result}")
        
        # 如果有依赖子任务，也添加其结果作为上下文
        dependencies = subtask.get('dependencies', [])
        dependency_results = []
        if dependencies and self.subtasks:
            for dep_id in dependencies:
                dep_task = next((t for t in self.subtasks if t.get('id') == dep_id), None)
                if dep_task and dep_task.get('status') in ['completed', '已完成'] and 'result' in dep_task:
                    dependency_results.append(f"依赖任务 {dep_task.get('name')} 的结果:\n{dep_task.get('result')}")
        
        # 构建提示
        prompt = f"""
        # 当前执行步骤
        {step.get('description')}
        
        # 子任务信息
        {subtask.get('name')}: {subtask.get('description')}
        
        # 预期输出
        {step.get('expected_output', '未指定')}
        
        # 可用工具
        {', '.join(step.get('tools', ['create_chat_completion']))}
        """
        
        # 添加上下文（如果有）
        if context:
            prompt += f"\n\n# 先前步骤的结果\n" + "\n\n".join(context)
            
        if dependency_results:
            prompt += f"\n\n# 依赖任务的结果\n" + "\n\n".join(dependency_results)
            
        # 添加执行指导
        prompt += """
        
        # 执行说明
        请根据上述信息执行当前步骤，并确保输出符合预期。如果需要使用工具，请直接调用工具而不要描述调用过程。
        输出应该是结构化的、清晰的，并符合自动化测试的专业要求。
        """
        
        return prompt
        
    def _prepare_tools_for_llm(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """准备用于LLM的工具列表
        
        Args:
            tool_names: 工具名称列表
            
        Returns:
            List[Dict[str, Any]]: 工具定义列表
        """
        tools = []
        for name in tool_names:
            tool = self.available_tools.get_tool(name)
            if tool and hasattr(tool, 'to_llm_tool'):
                tools.append(tool.to_llm_tool())
        
        return tools

# 导入循环依赖
from app.tool.planning import PlanningTool
from app.tool.file_operators import FileOperatorTool 
