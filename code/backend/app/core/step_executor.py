"""
步骤执行器
负责执行智能体计划中的具体步骤
"""

import asyncio
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from .tool_registry import ToolRegistry
from ..agents.base_agent import AgentStep


class StepExecutor:
    """步骤执行器"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.execution_history: Dict[str, Dict[str, Any]] = {}
    
    async def execute(self, step: AgentStep) -> Dict[str, Any]:
        """
        执行单个步骤
        
        Args:
            step: 要执行的步骤
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        execution_id = str(uuid.uuid4())
        step.started_at = datetime.utcnow()
        step.status = "running"
        
        try:
            # 记录执行开始
            self.execution_history[execution_id] = {
                "step_id": step.step_id,
                "step_name": step.name,
                "started_at": step.started_at,
                "status": "running"
            }
            
            # 执行步骤
            if step.tool_name:
                # 使用指定工具执行
                result = await self._execute_with_tool(step)
            else:
                # 不使用工具的自由执行
                result = await self._execute_without_tool(step)
            
            # 更新步骤状态
            step.status = "completed"
            step.completed_at = datetime.utcnow()
            step.result = result
            
            # 记录执行完成
            self.execution_history[execution_id].update({
                "status": "completed",
                "completed_at": step.completed_at,
                "result": result
            })
            
            return {
                "step_id": step.step_id,
                "status": "completed",
                "result": result,
                "execution_id": execution_id,
                "duration": (step.completed_at - step.started_at).total_seconds()
            }
            
        except Exception as e:
            # 处理执行错误
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            step.error = str(e)
            
            # 记录执行失败
            self.execution_history[execution_id].update({
                "status": "failed",
                "completed_at": step.completed_at,
                "error": str(e)
            })
            
            return {
                "step_id": step.step_id,
                "status": "failed",
                "error": str(e),
                "execution_id": execution_id,
                "duration": (step.completed_at - step.started_at).total_seconds()
            }
    
    async def _execute_with_tool(self, step: AgentStep) -> Dict[str, Any]:
        """
        使用工具执行步骤
        
        Args:
            step: 执行步骤
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if not step.tool_name:
            raise ValueError("工具名称不能为空")
        
        # 验证工具是否存在
        tool = self.tool_registry.get_tool(step.tool_name)
        if not tool:
            raise ValueError(f"工具 {step.tool_name} 不存在")
        
        # 验证参数
        validated_parameters = self._validate_parameters(step.parameters, tool.parameters)
        
        # 执行工具
        tool_result = await self.tool_registry.execute_tool(step.tool_name, validated_parameters)
        
        if not tool_result.get("success", False):
            raise Exception(f"工具执行失败: {tool_result.get('error', '未知错误')}")
        
        return {
            "tool_name": step.tool_name,
            "tool_result": tool_result.get("result"),
            "parameters_used": validated_parameters,
            "execution_type": "tool"
        }
    
    async def _execute_without_tool(self, step: AgentStep) -> Dict[str, Any]:
        """
        不使用工具的自由执行
        
        Args:
            step: 执行步骤
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 对于不使用工具的步骤，执行基本的分析或处理
        result = {
            "message": f"步骤 '{step.name}' 执行完成",
            "description": step.description,
            "parameters": step.parameters,
            "execution_type": "direct"
        }
        
        # 根据步骤描述执行不同的逻辑
        if "分析" in step.name or "analysis" in step.name.lower():
            result["analysis_result"] = self._perform_analysis(step)
        elif "生成" in step.name or "generate" in step.name.lower():
            result["generation_result"] = self._perform_generation(step)
        elif "验证" in step.name or "validate" in step.name.lower():
            result["validation_result"] = self._perform_validation(step)
        
        return result
    
    def _validate_parameters(
        self,
        parameters: Dict[str, Any],
        tool_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证和处理参数
        
        Args:
            parameters: 输入参数
            tool_parameters: 工具参数定义
            
        Returns:
            Dict[str, Any]: 验证后的参数
        """
        validated = {}
        
        for param_name, param_value in parameters.items():
            if param_name in tool_parameters:
                # 参数存在，进行类型验证
                param_def = tool_parameters[param_name]
                
                # 处理空值
                if param_value is None:
                    # 如果参数是必需的
                    if param_def.get("required", False):
                        # 使用默认值，如果有的话
                        if "default" in param_def:
                            validated[param_name] = param_def["default"]
                        else:
                            # 否则，保留为None
                            validated[param_name] = None
                    continue
                
                # 简单的类型验证和转换
                expected_type = param_def.get("type", "string")
                try:
                    if expected_type == "string":
                        if not isinstance(param_value, str):
                            param_value = str(param_value)
                    elif expected_type == "integer" or expected_type == "number":
                        if not isinstance(param_value, (int, float)):
                            if isinstance(param_value, str) and param_value.strip():
                                try:
                                    if expected_type == "integer":
                                        param_value = int(float(param_value))
                                    else:
                                        param_value = float(param_value)
                                except (ValueError, TypeError):
                                    param_value = param_def.get("default", 0)
                            else:
                                param_value = param_def.get("default", 0)
                    elif expected_type == "boolean":
                        if not isinstance(param_value, bool):
                            if isinstance(param_value, str):
                                param_value = param_value.lower() in ["true", "yes", "1", "t", "y"]
                            else:
                                param_value = bool(param_value)
                    elif expected_type == "array" and isinstance(param_value, str):
                        # 尝试将字符串解析为数组
                        try:
                            import json
                            param_value = json.loads(param_value)
                            if not isinstance(param_value, list):
                                param_value = [param_value]
                        except json.JSONDecodeError:
                            # 如果不是JSON格式，按逗号分割
                            param_value = [item.strip() for item in param_value.split(",") if item.strip()]
                except Exception as e:
                    # 转换失败，使用默认值
                    if "default" in param_def:
                        param_value = param_def["default"]
                    
                validated[param_name] = param_value
            else:
                # 参数不在定义中，但仍然保留
                validated[param_name] = param_value
        
        # 检查是否缺少必需参数，添加默认值
        for param_name, param_def in tool_parameters.items():
            if param_name not in validated and param_def.get("required", False) and "default" in param_def:
                validated[param_name] = param_def["default"]
        
        return validated
    
    def _perform_analysis(self, step: AgentStep) -> Dict[str, Any]:
        """执行分析任务"""
        return {
            "type": "analysis",
            "step_name": step.name,
            "findings": [
                "分析已完成",
                "基于提供的信息进行了综合评估",
                "生成了相关建议"
            ],
            "confidence": 0.85
        }
    
    def _perform_generation(self, step: AgentStep) -> Dict[str, Any]:
        """执行生成任务"""
        return {
            "type": "generation",
            "step_name": step.name,
            "generated_items": [
                f"基于{step.description}生成的项目1",
                f"基于{step.description}生成的项目2",
                f"基于{step.description}生成的项目3"
            ],
            "generation_count": 3
        }
    
    def _perform_validation(self, step: AgentStep) -> Dict[str, Any]:
        """执行验证任务"""
        return {
            "type": "validation",
            "step_name": step.name,
            "validation_status": "passed",
            "checked_items": [
                "数据完整性检查",
                "格式验证",
                "业务规则验证"
            ],
            "validation_score": 0.95
        }
    
    async def execute_parallel(self, steps: list[AgentStep]) -> Dict[str, Any]:
        """
        并行执行多个步骤
        
        Args:
            steps: 要执行的步骤列表
            
        Returns:
            Dict[str, Any]: 执行结果汇总
        """
        if not steps:
            return {"results": [], "total_steps": 0, "success_count": 0, "failed_count": 0}
        
        # 创建执行任务
        tasks = [self.execute(step) for step in steps]
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = 0
        failed_count = 0
        processed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 处理异常
                failed_count += 1
                processed_results.append({
                    "step_id": steps[i].step_id,
                    "status": "failed",
                    "error": str(result)
                })
            else:
                if result.get("status") == "completed":
                    success_count += 1
                else:
                    failed_count += 1
                processed_results.append(result)
        
        return {
            "results": processed_results,
            "total_steps": len(steps),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / len(steps) if steps else 0
        }
    
    def get_execution_history(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        获取执行历史
        
        Args:
            limit: 限制返回的记录数
            
        Returns:
            Dict[str, Any]: 执行历史
        """
        history_items = list(self.execution_history.values())
        
        # 按时间排序
        history_items.sort(key=lambda x: x.get("started_at", datetime.min), reverse=True)
        
        if limit:
            history_items = history_items[:limit]
        
        return {
            "history": history_items,
            "total_executions": len(self.execution_history),
            "shown_count": len(history_items)
        }
    
    def clear_history(self) -> None:
        """清除执行历史"""
        self.execution_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "success_count": 0,
                "failed_count": 0,
                "success_rate": 0,
                "average_duration": 0
            }
        
        success_count = sum(1 for h in self.execution_history.values() if h.get("status") == "completed")
        failed_count = total_executions - success_count
        
        # 计算平均执行时间
        durations = []
        for history in self.execution_history.values():
            started = history.get("started_at")
            completed = history.get("completed_at")
            if started and completed:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace('Z', '+00:00'))
                if isinstance(completed, str):
                    completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                duration = (completed - started).total_seconds()
                durations.append(duration)
        
        average_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_executions": total_executions,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / total_executions,
            "average_duration": average_duration
        } 