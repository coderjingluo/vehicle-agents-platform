"""
任务分解器
负责基于大模型将用户请求分解为可执行的步骤
"""

import json
import uuid
from typing import Any, Dict, List
from datetime import datetime

from .llm_client import LLMClientManager
from ..agents.base_agent import AgentPlan, AgentStep


class TaskDecomposer:
    """任务分解器"""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.llm_manager = llm_manager
    
    async def decompose(
        self,
        llm_response: str,
        available_tools: Dict[str, Dict[str, Any]]
    ) -> AgentPlan:
        """
        分解LLM响应为执行计划
        
        Args:
            llm_response: LLM的响应
            available_tools: 可用工具列表
            
        Returns:
            AgentPlan: 执行计划
        """
        try:
            # 尝试解析JSON响应
            plan_data = json.loads(llm_response.strip())
            
            # 验证计划结构
            self._validate_plan_structure(plan_data)
            
            # 创建执行步骤
            steps = []
            for step_data in plan_data.get("steps", []):
                step = self._create_step(step_data, available_tools)
                steps.append(step)
            
            # 创建执行计划
            plan = AgentPlan(
                plan_id=plan_data.get("plan_id", str(uuid.uuid4())),
                description=plan_data.get("description", "执行计划"),
                steps=steps
            )
            
            return plan
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试智能解析
            return await self._parse_natural_language_plan(llm_response, available_tools)
        except Exception as e:
            # 创建默认计划
            return self._create_fallback_plan(str(e), available_tools)
    
    def _validate_plan_structure(self, plan_data: Dict[str, Any]) -> None:
        """验证计划结构"""
        if not isinstance(plan_data, dict):
            raise ValueError("计划必须是字典格式")
        
        if "steps" not in plan_data:
            raise ValueError("计划必须包含steps字段")
        
        if not isinstance(plan_data["steps"], list):
            raise ValueError("steps必须是列表格式")
        
        # 验证每个步骤
        for i, step in enumerate(plan_data["steps"]):
            if not isinstance(step, dict):
                raise ValueError(f"步骤{i}必须是字典格式")
            
            required_fields = ["step_id", "name", "description"]
            for field in required_fields:
                if field not in step:
                    raise ValueError(f"步骤{i}缺少必需字段: {field}")
    
    def _create_step(
        self,
        step_data: Dict[str, Any],
        available_tools: Dict[str, Dict[str, Any]]
    ) -> AgentStep:
        """创建执行步骤"""
        
        step_id = step_data["step_id"]
        name = step_data["name"]
        description = step_data["description"]
        tool_name = step_data.get("tool_name")
        parameters = step_data.get("parameters", {})
        dependencies = step_data.get("dependencies", [])
        
        # 验证工具名称
        if tool_name and tool_name not in available_tools:
            # 尝试找到相似的工具
            similar_tool = self._find_similar_tool(tool_name, available_tools)
            if similar_tool:
                tool_name = similar_tool
            else:
                tool_name = None  # 工具不存在，设为None
        
        # 验证参数
        if tool_name and tool_name in available_tools:
            tool_info = available_tools[tool_name]
            parameters = self._validate_parameters(parameters, tool_info)
        
        return AgentStep(
            step_id=step_id,
            name=name,
            description=description,
            tool_name=tool_name,
            parameters=parameters,
            dependencies=dependencies
        )
    
    def _find_similar_tool(
        self,
        tool_name: str,
        available_tools: Dict[str, Dict[str, Any]]
    ) -> str:
        """查找相似的工具名称"""
        tool_name_lower = tool_name.lower()
        
        # 精确匹配
        for available_tool in available_tools:
            if available_tool.lower() == tool_name_lower:
                return available_tool
        
        # 包含匹配
        for available_tool in available_tools:
            if tool_name_lower in available_tool.lower() or available_tool.lower() in tool_name_lower:
                return available_tool
        
        return None
    
    def _validate_parameters(
        self,
        parameters: Dict[str, Any],
        tool_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证和修正参数"""
        if "parameters" not in tool_info:
            return parameters
        
        tool_params = tool_info["parameters"]
        validated_params = {}
        
        for param_name, param_value in parameters.items():
            if param_name in tool_params:
                validated_params[param_name] = param_value
            else:
                # 尝试找到相似的参数名
                similar_param = self._find_similar_parameter(param_name, tool_params)
                if similar_param:
                    validated_params[similar_param] = param_value
        
        return validated_params
    
    def _find_similar_parameter(
        self,
        param_name: str,
        tool_params: Dict[str, Any]
    ) -> str:
        """查找相似的参数名"""
        param_name_lower = param_name.lower()
        
        for tool_param in tool_params:
            if tool_param.lower() == param_name_lower:
                return tool_param
            
            if param_name_lower in tool_param.lower() or tool_param.lower() in param_name_lower:
                return tool_param
        
        return None
    
    async def _parse_natural_language_plan(
        self,
        response: str,
        available_tools: Dict[str, Dict[str, Any]]
    ) -> AgentPlan:
        """解析自然语言计划"""
        
        # 构建解析提示词
        system_prompt = f"""
你需要将以下自然语言描述转换为JSON格式的执行计划。

可用工具:
{json.dumps(available_tools, ensure_ascii=False, indent=2)}

请返回标准的JSON计划格式：
{{
    "plan_id": "唯一ID",
    "description": "计划描述",
    "steps": [
        {{
            "step_id": "步骤ID",
            "name": "步骤名称",
            "description": "步骤描述",
            "tool_name": "工具名称",
            "parameters": {{}},
            "dependencies": []
        }}
    ]
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请将以下内容转换为执行计划：\n{response}"}
        ]
        
        try:
            llm_response = await self.llm_manager.generate_response(messages)
            plan_data = json.loads(llm_response.strip())
            
            # 递归调用自己处理JSON
            return await self.decompose(json.dumps(plan_data), available_tools)
            
        except Exception as e:
            # 如果还是失败，返回默认计划
            return self._create_fallback_plan(f"解析失败: {str(e)}", available_tools)
    
    def _create_fallback_plan(
        self,
        error_message: str,
        available_tools: Dict[str, Dict[str, Any]]
    ) -> AgentPlan:
        """创建默认的回退计划"""
        
        plan_id = str(uuid.uuid4())
        description = f"默认执行计划 (原因: {error_message})"
        
        # 创建一个简单的分析步骤
        steps = [
            AgentStep(
                step_id="fallback_step_1",
                name="问题分析",
                description="分析用户请求并生成基础响应",
                tool_name=None,  # 不使用特定工具
                parameters={},
                dependencies=[]
            )
        ]
        
        return AgentPlan(
            plan_id=plan_id,
            description=description,
            steps=steps
        )
    
    async def refine_plan(
        self,
        plan: AgentPlan,
        feedback: str,
        available_tools: Dict[str, Dict[str, Any]]
    ) -> AgentPlan:
        """
        基于反馈优化计划
        
        Args:
            plan: 原始计划
            feedback: 反馈信息
            available_tools: 可用工具
            
        Returns:
            AgentPlan: 优化后的计划
        """
        
        system_prompt = f"""
你需要基于反馈信息优化执行计划。

原始计划：
{json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)}

可用工具：
{json.dumps(available_tools, ensure_ascii=False, indent=2)}

请根据反馈优化计划，返回新的JSON格式计划。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"反馈信息：{feedback}"}
        ]
        
        try:
            response = await self.llm_manager.generate_response(messages)
            return await self.decompose(response, available_tools)
        except Exception:
            # 如果优化失败，返回原计划
            return plan 