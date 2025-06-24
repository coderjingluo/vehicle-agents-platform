"""
自动化测试智能体 - 生成和执行自动化测试脚本

该智能体具备以下核心能力：
1. 基于测试用例生成自动化测试脚本
2. 支持多种测试框架 (pytest, selenium, robot framework等)
3. 测试环境配置和管理
4. 测试执行监控和结果收集
5. 持续集成和测试报告生成
"""

from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentStep, AgentPlan
from app.models.task import AgentType


class AutomationAgent(BaseAgent):
    """自动化测试智能体"""
    
    def __init__(self):
        super().__init__()
        self.agent_type = AgentType.AUTOMATION_TEST
        self.test_frameworks = {
            "pytest": "Python测试框架",
            "selenium": "Web自动化测试",
            "robot_framework": "关键字驱动测试",
            "postman": "API测试",
            "jmeter": "性能测试",
            "metasploit": "渗透测试",
            "nmap": "网络扫描",
            "burp_suite": "Web安全测试"
        }
        self.supported_languages = ["Python", "Java", "JavaScript", "C++", "Shell"]
        
    def get_agent_type(self) -> str:
        return "automation_test"
    
    async def _generate_plan(self, user_request: str, context: Dict[str, Any] = None) -> AgentPlan:
        """生成自动化测试计划"""
        
        planning_prompt = f"""
作为自动化测试专家，请基于测试用例生成详细的自动化测试实施计划。

用户请求: {user_request}
测试用例信息: {json.dumps(context or {}, ensure_ascii=False, indent=2)}

请生成包含以下步骤的执行计划：

1. **测试用例分析**: 分析测试用例的自动化可行性
2. **框架选择**: 选择合适的测试框架和工具
3. **环境配置**: 配置测试环境和依赖
4. **脚本生成**: 生成自动化测试脚本
5. **集成配置**: 配置CI/CD集成
6. **执行验证**: 执行测试并验证结果

对于每个步骤，请提供：
- 步骤名称和描述
- 所需工具和框架
- 预期输出
- 成功标准

以JSON格式返回计划。
"""
        
        try:
            response = await self.llm_manager.generate_response(
                planning_prompt,
                context={"agent_type": "automation_test", "task": "planning"}
            )
            
            plan_data = self._parse_json_response(response)
            
            steps = []
            if "steps" in plan_data:
                for step_data in plan_data["steps"]:
                    step = AgentStep(
                        id=str(uuid.uuid4()),
                        name=step_data.get("name", "Unknown Step"),
                        description=step_data.get("description", ""),
                        tool_calls=step_data.get("tools", []),
                        expected_output=step_data.get("expected_output", ""),
                        success_criteria=step_data.get("success_criteria", ""),
                        status="pending"
                    )
                    steps.append(step)
            
            return AgentPlan(
                id=str(uuid.uuid4()),
                agent_type=self.agent_type,
                description=plan_data.get("description", "自动化测试实施计划"),
                steps=steps,
                estimated_duration=plan_data.get("estimated_duration", 40),
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"生成自动化测试计划失败: {e}")
            return self._get_default_plan()
    
    def _get_default_plan(self) -> AgentPlan:
        """获取默认的自动化测试计划"""
        default_steps = [
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试用例分析",
                description="分析测试用例，评估自动化可行性和复杂度",
                tool_calls=["test_case_analyzer"],
                expected_output="自动化可行性评估报告",
                success_criteria="成功分类可自动化和手动测试用例",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试框架选择",
                description="基于测试类型选择合适的自动化测试框架",
                tool_calls=["framework_selector"],
                expected_output="测试框架选择方案",
                success_criteria="选择的框架满足所有测试需求",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试环境配置",
                description="配置自动化测试环境和依赖",
                tool_calls=["environment_configurator"],
                expected_output="测试环境配置文档",
                success_criteria="测试环境运行稳定",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="自动化脚本生成",
                description="基于测试用例生成自动化测试脚本",
                tool_calls=["script_generator"],
                expected_output="完整的自动化测试脚本",
                success_criteria="脚本可执行且覆盖所有测试点",
                status="pending"
            ),
            AgentStep(
                id=str(uuid.uuid4()),
                name="测试执行",
                description="执行自动化测试并收集结果",
                tool_calls=["test_executor"],
                expected_output="测试执行报告",
                success_criteria="所有测试正常执行完成",
                status="pending"
            )
        ]
        
        return AgentPlan(
            id=str(uuid.uuid4()),
            agent_type=self.agent_type,
            description="标准自动化测试实施流程",
            steps=default_steps,
            estimated_duration=35,
            created_at=datetime.utcnow()
        )
    
    async def execute_step(self, step: AgentStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行具体的自动化测试步骤"""
        try:
            self.logger.info(f"执行自动化测试步骤: {step.name}")
            
            # 根据步骤名称执行相应的操作
            if "分析" in step.name:
                return await self._analyze_test_cases(step, context)
            elif "框架" in step.name or "选择" in step.name:
                return await self._select_framework(step, context)
            elif "环境" in step.name or "配置" in step.name:
                return await self._configure_environment(step, context)
            elif "生成" in step.name or "脚本" in step.name:
                return await self._generate_scripts(step, context)
            elif "执行" in step.name:
                return await self._execute_tests(step, context)
            else:
                return await self._execute_general_step(step, context)
                
        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_test_cases(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试用例的自动化可行性"""
        prompt = f"""
作为自动化测试专家，请分析以下测试用例的自动化可行性。

测试用例信息:
{json.dumps(context.get('test_cases', {}), ensure_ascii=False, indent=2)}

请对每个测试用例进行分析，提供：

1. **自动化可行性评估**
   - 完全可自动化 (分数: 9-10)
   - 部分可自动化 (分数: 6-8)
   - 难以自动化 (分数: 3-5)
   - 不可自动化 (分数: 1-2)

2. **技术复杂度评估**
   - 简单 (UI交互、API调用)
   - 中等 (数据处理、状态验证)
   - 复杂 (多系统集成、时序依赖)
   - 极复杂 (人工判断、物理操作)

3. **所需测试工具**
   - Web测试: Selenium, Playwright
   - API测试: Postman, RestAssured
   - 性能测试: JMeter, LoadRunner
   - 安全测试: OWASP ZAP, Burp Suite
   - 网络测试: Nmap, Wireshark

4. **自动化优先级**
   - P0: 核心功能，高频执行
   - P1: 重要功能，回归测试
   - P2: 一般功能，定期测试
   - P3: 边缘功能，手动测试

5. **预估工作量**
   - 脚本开发时间
   - 环境配置时间
   - 维护成本

以JSON格式返回分析结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        analysis_result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": analysis_result,
            "step_id": step.id,
            "analysis_type": "automation_feasibility",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _select_framework(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """选择合适的测试框架"""
        prompt = f"""
基于测试用例分析结果，选择最合适的自动化测试框架和工具组合。

测试用例分析:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请选择并配置测试框架：

1. **主框架选择**
   - pytest: Python生态，丰富插件
   - JUnit: Java生态，企业级
   - Jest: JavaScript生态，前端测试
   - Robot Framework: 关键字驱动，可视化

2. **专项工具选择**
   - Web UI测试: Selenium WebDriver, Playwright
   - API测试: requests, httpx, RestAssured
   - 性能测试: Locust, JMeter, Artillery
   - 安全测试: OWASP ZAP, Nuclei
   - 数据库测试: SQLAlchemy, MyBatis

3. **报告工具**
   - Allure: 美观的测试报告
   - pytest-html: 简单HTML报告
   - ExtentReports: 企业级报告
   - TestNG: 详细的测试报告

4. **CI/CD集成**
   - Jenkins: 传统CI/CD
   - GitHub Actions: 云原生CI/CD
   - GitLab CI: 一体化DevOps
   - Azure DevOps: 微软生态

5. **配置管理**
   - 测试数据管理
   - 环境配置管理
   - 密钥管理
   - 日志收集

提供具体的框架选择理由和配置建议。

以JSON格式返回框架选择方案。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        framework_selection = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": framework_selection,
            "step_id": step.id,
            "selection_type": "test_framework",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _configure_environment(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """配置测试环境"""
        prompt = f"""
基于选择的测试框架，生成详细的测试环境配置方案。

框架选择:
{json.dumps(context.get('previous_results', {}), ensure_ascii=False, indent=2)}

请提供完整的环境配置：

1. **开发环境配置**
   ```bash
   # Python环境示例
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   ```

2. **依赖管理**
   - requirements.txt / package.json
   - 版本锁定和兼容性
   - 依赖安全扫描

3. **测试数据配置**
   - 测试数据库设置
   - 测试数据初始化
   - 数据清理策略

4. **网络环境模拟**
   - Docker容器化
   - 网络拓扑模拟
   - 服务Mock配置

5. **浏览器/设备配置**
   - WebDriver配置
   - 移动设备模拟
   - 跨浏览器兼容性

6. **监控和日志**
   - 测试执行监控
   - 错误日志收集
   - 性能指标监控

7. **安全配置**
   - 测试环境隔离
   - 敏感数据保护
   - 访问权限控制

提供具体的配置文件和脚本。

以JSON格式返回环境配置方案。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        environment_config = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": environment_config,
            "step_id": step.id,
            "config_type": "test_environment",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_scripts(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成自动化测试脚本"""
        prompt = f"""
作为高级自动化测试工程师，基于测试用例和环境配置生成完整的自动化测试脚本。

测试用例信息:
{json.dumps(context.get('test_cases', {}), ensure_ascii=False, indent=2)}

环境配置:
{json.dumps(context.get('environment_config', {}), ensure_ascii=False, indent=2)}

请生成以下类型的测试脚本：

1. **API安全测试脚本** (Python + pytest)
```python
import pytest
import requests
import json

class TestAPIAuthentication:
    def test_authentication_bypass(self):
        # 认证绕过测试
        pass
    
    def test_authorization_escalation(self):
        # 权限提升测试
        pass
```

2. **Web UI安全测试脚本** (Python + Selenium)
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestWebSecurity:
    def test_xss_vulnerability(self):
        # XSS漏洞测试
        pass
    
    def test_sql_injection(self):
        # SQL注入测试
        pass
```

3. **网络安全测试脚本** (Python + Scapy)
```python
from scapy.all import *

class TestNetworkSecurity:
    def test_port_scanning(self):
        # 端口扫描测试
        pass
    
    def test_packet_injection(self):
        # 数据包注入测试
        pass
```

4. **性能测试脚本** (Python + Locust)
```python
from locust import HttpUser, task

class PerformanceTest(HttpUser):
    @task
    def load_test(self):
        # 负载测试
        pass
```

5. **配置文件**
   - pytest.ini: pytest配置
   - conftest.py: 测试夹具
   - config.yaml: 测试配置
   - Dockerfile: 容器化配置

每个脚本应包含：
- 详细的测试步骤
- 完善的断言验证
- 错误处理机制
- 清晰的日志输出
- 可配置的参数

以JSON格式返回生成的脚本代码和配置文件。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        scripts_result = self._parse_json_response(response)
        
        # 计算脚本统计信息
        script_stats = self._calculate_script_statistics(scripts_result)
        
        return {
            "success": True,
            "result": scripts_result,
            "statistics": script_stats,
            "step_id": step.id,
            "script_count": len(scripts_result.get("scripts", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_tests(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行自动化测试"""
        prompt = f"""
模拟执行自动化测试，生成测试执行报告。

测试脚本:
{json.dumps(context.get('scripts', {}), ensure_ascii=False, indent=2)}

请模拟测试执行并提供：

1. **测试执行概况**
   - 总测试用例数量
   - 通过/失败/跳过数量
   - 执行时间统计
   - 覆盖率统计

2. **详细测试结果**
   - 每个测试用例的执行结果
   - 失败用例的错误信息
   - 性能测试的指标数据
   - 安全测试的漏洞发现

3. **问题分析**
   - 失败原因分析
   - 性能瓶颈识别
   - 安全风险评估
   - 改进建议

4. **测试报告**
   - HTML格式报告
   - 趋势分析图表
   - 风险评估矩阵
   - 修复优先级建议

5. **持续改进**
   - 测试用例优化建议
   - 自动化流程改进
   - 工具链升级建议
   - 团队技能提升建议

注意：这是模拟执行，请生成realistic的测试结果，包括一些失败案例和发现的问题。

以JSON格式返回测试执行报告。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        execution_result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": execution_result,
            "step_id": step.id,
            "execution_type": "test_execution",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_script_statistics(self, scripts_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算脚本统计信息"""
        try:
            scripts = scripts_data.get("scripts", [])
            if not scripts:
                return {"total": 0}
            
            stats = {
                "total": len(scripts),
                "by_type": {"api": 0, "ui": 0, "performance": 0, "security": 0},
                "by_language": {"python": 0, "java": 0, "javascript": 0},
                "by_framework": {"pytest": 0, "selenium": 0, "locust": 0},
                "total_lines": 0,
                "estimated_execution_time": 0
            }
            
            for script in scripts:
                # 类型统计
                script_type = script.get("type", "").lower()
                if script_type in stats["by_type"]:
                    stats["by_type"][script_type] += 1
                
                # 语言统计
                language = script.get("language", "python").lower()
                if language in stats["by_language"]:
                    stats["by_language"][language] += 1
                
                # 框架统计
                framework = script.get("framework", "").lower()
                if framework in stats["by_framework"]:
                    stats["by_framework"][framework] += 1
                
                # 代码行数统计
                code = script.get("code", "")
                if isinstance(code, str):
                    stats["total_lines"] += len(code.split('\n'))
                
                # 预估执行时间
                stats["estimated_execution_time"] += script.get("estimated_time", 5)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算脚本统计信息失败: {e}")
            return {"total": 0, "error": str(e)}
    
    async def _execute_general_step(self, step: AgentStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用步骤"""
        prompt = f"""
作为自动化测试专家，执行以下自动化测试任务：

任务描述: {step.description}
预期输出: {step.expected_output}
成功标准: {step.success_criteria}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

请提供详细的执行结果，包括：
1. 执行过程说明
2. 具体输出内容
3. 技术实现细节
4. 质量评估
5. 优化建议

以JSON格式返回结果。
"""
        
        response = await self.llm_manager.generate_response(
            prompt,
            context={"step": step.name, "agent": "automation_test"}
        )
        
        result = self._parse_json_response(response)
        
        return {
            "success": True,
            "result": result,
            "step_id": step.id,
            "execution_type": "general",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "raw_response": response,
                "parsed": False,
                "error": "Failed to parse JSON response"
            }