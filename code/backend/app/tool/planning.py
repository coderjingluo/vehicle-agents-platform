import logging
import uuid
from typing import Dict, List, Literal, Optional

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class PlanningTool(BaseTool):
    """规划工具，用于创建和管理任务执行计划"""
    
    name: str = "planning"
    description: str = """
    规划工具，允许创建和管理解决复杂任务的计划。
    提供创建计划、更新计划步骤和跟踪进度的功能。
    """
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "要执行的命令。可用命令: create, update, list, get, set_active, mark_step, delete.",
                "enum": [
                    "create",
                    "update",
                    "list",
                    "get",
                    "set_active",
                    "mark_step",
                    "delete",
                ],
                "type": "string",
            },
            "plan_id": {
                "description": "计划的唯一标识符。create、update、set_active和delete命令需要。get和mark_step命令可选(如不指定则使用当前活动计划)。",
                "type": "string",
            },
            "title": {
                "description": "计划标题。create命令必需，update命令可选。",
                "type": "string",
            },
            "steps": {
                "description": "计划步骤列表。create命令必需，update命令可选。",
                "type": "array",
                "items": {"type": "string"},
            },
            "step_index": {
                "description": "要更新的步骤索引(从0开始)。mark_step命令必需。",
                "type": "integer",
            },
            "step_status": {
                "description": "步骤状态。与mark_step命令一起使用。",
                "enum": ["not_started", "in_progress", "completed", "blocked"],
                "type": "string",
            },
            "step_notes": {
                "description": "步骤的附加说明。mark_step命令可选。",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }
    
    # 用于存储计划的字典
    plans: Dict[str, Dict] = {}
    
    # 当前活动计划ID
    _current_plan_id: Optional[str] = None
    
    async def execute(
        self,
        *,
        command: Literal[
            "create", "update", "list", "get", "set_active", "mark_step", "delete"
        ],
        plan_id: Optional[str] = None,
        title: Optional[str] = None,
        steps: Optional[List[str]] = None,
        step_index: Optional[int] = None,
        step_status: Optional[
            Literal["not_started", "in_progress", "completed", "blocked"]
        ] = None,
        step_notes: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """执行规划工具命令"""
        try:
            if command == "create":
                return self._create_plan(plan_id, title, steps)
            elif command == "update":
                return self._update_plan(plan_id, title, steps)
            elif command == "list":
                return self._list_plans()
            elif command == "get":
                return self._get_plan(plan_id)
            elif command == "set_active":
                return self._set_active_plan(plan_id)
            elif command == "mark_step":
                return self._mark_step(plan_id, step_index, step_status, step_notes)
            elif command == "delete":
                return self._delete_plan(plan_id)
            else:
                return ToolResult(error=f"未知命令: {command}")
        except Exception as e:
            logger.error(f"规划操作失败: {str(e)}")
            return ToolResult(error=f"规划操作失败: {str(e)}")
    
    def _create_plan(self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]) -> ToolResult:
        """创建新计划"""
        if not title:
            return ToolResult(error="创建计划需要提供标题")
        if not steps:
            return ToolResult(error="创建计划需要提供步骤")
            
        # 生成唯一ID（如果未提供）
        plan_id = plan_id or f"plan_{uuid.uuid4().hex[:8]}"
        
        # 检查ID是否已存在
        if plan_id in self.plans:
            return ToolResult(error=f"计划ID已存在: {plan_id}")
            
        # 创建计划对象
        plan = {
            "id": plan_id,
            "title": title,
            "steps": [{"description": step, "status": "not_started", "notes": ""} for step in steps],
            "created_at": str(uuid.uuid1()),  # 使用时间戳作为创建时间
        }
        
        # 存储计划
        self.plans[plan_id] = plan
        
        # 如果没有活动计划，将此计划设为活动计划
        if not self._current_plan_id:
            self._current_plan_id = plan_id
            
        return ToolResult(output={"message": f"计划已创建: {title}", "plan_id": plan_id})
    
    def _update_plan(self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]) -> ToolResult:
        """更新现有计划"""
        if not plan_id:
            return ToolResult(error="更新计划需要提供plan_id")
            
        # 检查计划是否存在
        if plan_id not in self.plans:
            return ToolResult(error=f"计划不存在: {plan_id}")
            
        plan = self.plans[plan_id]
        
        # 更新标题（如果提供）
        if title:
            plan["title"] = title
            
        # 更新步骤（如果提供）
        if steps:
            # 保留现有步骤的状态和注释
            existing_steps = {i: step for i, step in enumerate(plan["steps"])}
            
            # 创建新步骤列表
            new_steps = []
            for i, step_desc in enumerate(steps):
                if i < len(existing_steps):
                    # 使用现有步骤的状态和注释
                    existing_step = existing_steps[i]
                    if existing_step["description"] == step_desc:
                        # 如果描述相同，保留所有信息
                        new_steps.append(existing_step)
                    else:
                        # 如果描述不同，保留状态和注释
                        new_steps.append({
                            "description": step_desc,
                            "status": existing_step["status"],
                            "notes": existing_step["notes"]
                        })
                else:
                    # 添加新步骤
                    new_steps.append({
                        "description": step_desc,
                        "status": "not_started",
                        "notes": ""
                    })
                    
            plan["steps"] = new_steps
            
        # 更新计划
        self.plans[plan_id] = plan
        
        return ToolResult(output={"message": f"计划已更新: {plan['title']}", "plan_id": plan_id})
    
    def _list_plans(self) -> ToolResult:
        """列出所有计划"""
        plan_summaries = []
        
        for plan_id, plan in self.plans.items():
            # 计算完成步骤数
            completed_steps = sum(1 for step in plan["steps"] if step["status"] == "completed")
            total_steps = len(plan["steps"])
            
            # 创建计划摘要
            summary = {
                "id": plan_id,
                "title": plan["title"],
                "progress": f"{completed_steps}/{total_steps}",
                "is_active": plan_id == self._current_plan_id,
            }
            
            plan_summaries.append(summary)
            
        return ToolResult(output=plan_summaries)
    
    def _get_plan(self, plan_id: Optional[str]) -> ToolResult:
        """获取特定计划详情"""
        # 如果未提供ID，使用当前活动计划
        plan_id = plan_id or self._current_plan_id
        
        if not plan_id:
            return ToolResult(error="未指定计划ID且没有活动计划")
            
        if plan_id not in self.plans:
            return ToolResult(error=f"计划不存在: {plan_id}")
            
        return ToolResult(output=self.plans[plan_id])
    
    def _set_active_plan(self, plan_id: Optional[str]) -> ToolResult:
        """设置活动计划"""
        if not plan_id:
            return ToolResult(error="设置活动计划需要提供plan_id")
            
        if plan_id not in self.plans:
            return ToolResult(error=f"计划不存在: {plan_id}")
            
        self._current_plan_id = plan_id
        
        return ToolResult(output={"message": f"已设置活动计划: {self.plans[plan_id]['title']}", "plan_id": plan_id})
    
    def _mark_step(self, plan_id: Optional[str], step_index: Optional[int], 
                 step_status: Optional[str], step_notes: Optional[str]) -> ToolResult:
        """更新步骤状态"""
        # 如果未提供ID，使用当前活动计划
        plan_id = plan_id or self._current_plan_id
        
        if not plan_id:
            return ToolResult(error="未指定计划ID且没有活动计划")
            
        if plan_id not in self.plans:
            return ToolResult(error=f"计划不存在: {plan_id}")
            
        if step_index is None:
            return ToolResult(error="更新步骤状态需要提供step_index")
            
        plan = self.plans[plan_id]
        
        # 检查步骤索引是否有效
        if step_index < 0 or step_index >= len(plan["steps"]):
            return ToolResult(error=f"步骤索引无效: {step_index}")
            
        # 更新步骤状态
        if step_status:
            plan["steps"][step_index]["status"] = step_status
            
        # 更新步骤注释
        if step_notes is not None:
            plan["steps"][step_index]["notes"] = step_notes
            
        return ToolResult(output={
            "message": f"已更新步骤状态", 
            "plan_id": plan_id, 
            "step_index": step_index,
            "step": plan["steps"][step_index]
        })
    
    def _delete_plan(self, plan_id: Optional[str]) -> ToolResult:
        """删除计划"""
        if not plan_id:
            return ToolResult(error="删除计划需要提供plan_id")
            
        if plan_id not in self.plans:
            return ToolResult(error=f"计划不存在: {plan_id}")
            
        # 获取计划标题
        plan_title = self.plans[plan_id]["title"]
        
        # 删除计划
        del self.plans[plan_id]
        
        # 如果删除的是当前活动计划，重置活动计划
        if plan_id == self._current_plan_id:
            self._current_plan_id = next(iter(self.plans)) if self.plans else None
            
        return ToolResult(output={"message": f"已删除计划: {plan_title}", "plan_id": plan_id}) 