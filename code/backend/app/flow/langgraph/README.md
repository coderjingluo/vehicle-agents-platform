# LangGraph 流程管理器

## 概述

LangGraph 流程管理器是 KunlunSec AI Platform 的核心组件之一，负责管理和执行基于 LangGraph 的各种执行流程。该组件使用图结构来表示和执行复杂的工作流，支持智能体协作和动态任务分解。

## 设计原则

1. **模块化设计**: 每种类型的执行流程都有专门的图实现
2. **可扩展性**: 支持添加新的图类型和执行流程
3. **灵活性**: 支持动态任务分解和智能体协作
4. **状态管理**: 使用 TypedDict 来管理图状态，确保类型安全
5. **错误处理**: 提供完善的错误处理机制

## 支持的图类型

当前系统支持以下几种图类型：

### 1. TARA 分析图 (TaraAgentGraph)

- **文件**: `tara_graph.py`
- **功能**: 实现威胁分析与风险评估流程
- **步骤**:
  - 资产识别
  - 威胁识别
  - 风险分析
  - 缓解措施开发
  - 报告生成

### 2. 测试用例生成图 (TestCaseAgentGraph)

- **文件**: `testcase_graph.py`
- **功能**: 基于 TARA 分析结果生成测试用例
- **步骤**:
  - TARA 结果分析
  - 测试用例生成
  - 覆盖率验证
  - 测试用例优化
  - 测试套件完成

### 3. 自动化测试图 (AutomationTestGraph)

- **文件**: `automation_graph.py`
- **功能**: 执行自动化测试
- **步骤**:
  - 环境准备
  - 测试脚本生成
  - 测试执行
  - 结果收集
  - 失败分析
  - 失败测试重试
  - 结果完成

### 4. 报告分析图 (ReportAnalysisGraph)

- **文件**: `report_graph.py`
- **功能**: 分析测试结果并生成报告
- **步骤**:
  - 测试结果分析
  - 问题分类
  - 可视化生成
  - 风险矩阵创建
  - 发现总结
  - 报告生成

### 5. 动态流程图 (DynamicLangGraphFlow)

- **文件**: `dynamic_flow.py`
- **功能**: 支持动态任务分解和智能体协作
- **步骤**:
  - 规划
  - 执行
  - 评估
  - 完成

## 流程管理器 (LangGraphFlowManager)

- **文件**: `flow_manager.py`
- **功能**: 
  - 创建和管理不同类型的图执行流
  - 执行图流程
  - 获取执行结果
  - 提供可视化表示

## 使用示例

```python
# 创建流程管理器
flow_manager = LangGraphFlowManager(agent_factory)

# 创建TARA分析流程
tara_flow_id = await flow_manager.create_graph_flow(
    flow_type="tara",
    name="车联网安全TARA分析",
    description="分析车联网系统的安全威胁和风险"
)

# 执行TARA分析流程
result = await flow_manager.execute_graph_flow(
    flow_id=tara_flow_id,
    input_data={"task": "分析车联网系统的安全威胁和风险"}
)

# 获取流程可视化
visualization = flow_manager.get_flow_visualization(tara_flow_id)
```

## 扩展指南

要添加新的图类型，请按照以下步骤操作：

1. 创建新的图实现文件，例如 `new_graph.py`
2. 实现图类，包括必要的状态定义、节点和边
3. 实现 `setup` 或 `initialize` 方法
4. 在 `flow_manager.py` 中的 `create_graph_flow` 方法中添加对新图类型的支持

## 注意事项

- 确保每个图实现都有完善的错误处理机制
- 使用 TypedDict 来管理图状态，确保类型安全
- 使用条件边来处理复杂的状态转换
- 使用 logger 记录关键操作和错误信息 