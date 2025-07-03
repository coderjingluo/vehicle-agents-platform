# 工具调用参数处理和协程处理问题修复

## 问题描述

在车联网安全平台的工具调用系统中，发现了两个主要问题：

1. **参数名称不匹配问题**：某些工具调用（如`web_search`和`create_chat_completion`）使用的参数名称与工具实现中期望的参数名称不匹配。例如，LLM可能返回`search_query`参数，但`WebSearchTool.execute()`方法期望的是`query`参数。

2. **协程处理问题**：工具调用返回的协程对象没有被正确地等待完成，导致错误：
   - `WebSearchTool.execute() missing 1 required positional argument: 'query'`
   - `CreateChatCompletionTool.execute() missing 1 required positional argument: 'messages'`

## 修复方法

### 1. 参数名称映射

在`toolcall.py`中添加了参数名称映射机制，将LLM返回的参数名称映射到工具实际期望的参数名称：

```python
# 特定工具的参数名称映射
param_mappings = {
    "web_search": {
        "search_query": "query",
        "engine": "search_engine"
    },
    "create_chat_completion": {
        "prompt": "messages"
    }
}

# 应用参数映射
if function_name in param_mappings and isinstance(function_args, dict):
    mapping = param_mappings[function_name]
    for old_name, new_name in mapping.items():
        if old_name in function_args:
            mapped_args[new_name] = function_args[old_name]
```

这个映射机制在两个位置实现：
- `_process_tool_calls`方法中，处理初始工具调用
- `execute_tool`方法中，执行具体工具前再次检查参数

### 2. 协程处理增强

在所有可能返回协程对象的地方添加了检查和等待机制：

```python
# 检查结果是否是协程对象，如果是则等待其完成
if asyncio.iscoroutine(result):
    logger.info(f"工具 {function_name} 返回了协程对象，等待其完成...")
    result = await result
```

这个检查在以下位置实现：
- `act`方法中
- `execute_tool`方法中
- `_process_tool_calls`方法中
- `_handle_special_tool`方法中

### 3. 特殊工具处理返回值

修改了`_handle_special_tool`方法，确保它正确返回处理后的结果：

```python
async def _handle_special_tool(self, name: str, result: Any, **kwargs):
    # 处理逻辑...
    return result  # 确保返回处理后的结果
```

## 参考实现

这些修复参考了OpenManus项目中的工具调用实现，特别是其参数处理和协程处理机制。OpenManus使用了类似的参数映射和协程等待机制，确保工具调用能够正确执行。

## 测试验证

修复后，之前出现错误的工具调用现在能够正常工作：
- `web_search`工具能够正确接收`query`参数
- `create_chat_completion`工具能够正确接收`messages`参数
- 所有返回协程对象的工具调用都能被正确等待和处理 