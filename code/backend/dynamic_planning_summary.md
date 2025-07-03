# 动态规划能力增强总结

## 问题背景

在测试过程中发现，系统中的智能体没有实现动态规划能力，无法根据任务需求智能地将任务分解为子任务和步骤。这导致智能体执行任务时缺乏灵活性，无法适应不同场景下的任务需求。

## 解决方案

我们对系统中的智能体架构进行了全面增强，实现了动态规划能力，使智能体能够根据任务特点动态生成执行计划，并将复杂任务智能分解为多层次的子任务和具体步骤。主要改进包括：

### 1. 基础智能体架构增强

- 在 `BaseAgent` 类中添加了动态规划相关的核心功能
- 实现了通用的 `generate_plan` 方法，支持将任务分解为子任务和步骤
- 添加了子任务和步骤的状态跟踪机制
- 实现了计划执行进度更新功能

### 2. 工具调用智能体增强

- 优化了 `ToolCallAgent` 类，使其能够利用基础动态规划能力
- 增强了 `think` 方法，使智能体能够根据当前计划和进度决定下一步行动
- 改进了工具选择机制，使工具选择与计划中的步骤更好地结合

### 3. 专业智能体增强

- 为 `TaraAgent`、`AutomationTestAgent` 等专业智能体增加了特定领域的动态规划能力
- 实现了特定领域的任务分解策略
- 优化了专业智能体对工具的选择和使用方式

### 4. 流程管理系统增强

- 改进了 `DynamicLangGraphFlow` 类，使其更好地支持动态计划生成和执行
- 优化了流程图的构建和执行机制
- 增强了状态管理和执行监控能力

## 关键改进细节

### 动态规划核心功能

```python
async def generate_plan(self, task: str) -> Dict[str, Any]:
    """根据任务动态生成执行计划
    
    将复杂任务分解为多个子任务，并可能进一步分解为更小的步骤
    """
    # 构建提示，引导模型生成规划
    planning_prompt = f"""
    请为以下任务制定详细的执行计划:
    
    # 任务描述
    {task}
    
    # 要求
    1. 将该任务分解为逻辑子任务
    2. 每个子任务可能需要进一步分解为具体步骤
    3. 确定步骤之间的依赖关系
    
    # 规划格式
    请提供JSON格式的执行计划，包含子任务和步骤...
    """
    
    # 使用LLM生成规划
    response = await self.llm.ask(...)
    
    # 解析规划结果
    plan = json.loads(...)
    
    # 保存计划到智能体
    self.current_plan = plan
    self.subtasks = plan.get('subtasks', [])
    
    return plan
```

### 增强的思考过程

```python
async def think(self) -> bool:
    """增强思考过程，整合动态规划"""
    # 检查是否有当前计划和未完成的子任务
    current_subtask = self.get_next_subtask()
    
    if current_subtask and self.dynamic_planning:
        # 获取当前子任务的下一个步骤
        current_step = self.get_next_step(current_subtask.get('id', ''))
        
        if current_step:
            # 更新提示，引导模型执行当前步骤
            subtask_prompt = f"""
            当前正在执行子任务: {current_subtask.get('name')}
            子任务描述: {current_subtask.get('description')}
            
            当前步骤: {current_step.get('description')}
            
            请思考如何最有效地执行这个步骤...
            """
            
            self.update_memory("user", subtask_prompt)
    
    # 调用原始的思考方法
    result = await super().think()
    
    # 如果执行了步骤，更新计划进度
    if result and current_step and self.dynamic_planning:
        # 将当前步骤标记为已完成
        self.completed_steps.append(step_id)
        
        # 更新计划进度
        self._update_plan_progress()
    
    return result
```

## 测试方法

我们创建了专门的测试脚本 `agent_api_test.py`，测试不同类型智能体的动态规划能力：

1. TARA智能体 - 测试威胁分析与风险评估的动态规划能力
2. 测试用例生成智能体 - 测试测试用例生成的动态规划能力
3. 自动化测试智能体 - 测试自动化测试执行的动态规划能力
4. 报告生成智能体 - 测试报告生成的动态规划能力

测试验证智能体能够：
- 将任务动态分解为多个子任务
- 将子任务进一步分解为具体步骤
- 为每个步骤选择合适的工具
- 动态调整执行计划

## 结论

通过以上改进，我们显著增强了智能体的动态规划能力，使其能够更智能地处理复杂任务。智能体现在能够：

1. 根据任务特点动态生成执行计划，而非使用固定步骤
2. 将大型任务智能分解为多个子任务
3. 将子任务进一步分解为具体步骤
4. 在执行过程中跟踪进度并调整计划

这些改进使系统在处理车联网网络安全测试等复杂任务时更加灵活和强大。 