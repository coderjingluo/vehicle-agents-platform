# 工具系统详细设计

## 1. 工具系统概述

参考OpenManus项目的工具系统设计，我们将构建一个可扩展的工具架构，使智能体能够与外部系统交互并执行各种任务。工具系统设计遵循以下原则：

- **统一接口**：所有工具遵循相同的接口规范
- **独立性**：每个工具都是独立的，可以单独测试和部署
- **可组合性**：工具可以组合使用，形成复杂的功能
- **错误处理**：标准化的错误处理和报告机制
- **可扩展性**：便于添加新工具

### 1.1 工具系统架构

```
┌──────────────────┐      ┌──────────────────┐
│                  │      │                  │
│    智能体系统     │◄────►│    工具系统      │
│                  │      │                  │
└──────────────────┘      └────────┬─────────┘
                                  │
            ┌───────────────────┬─┴────────────────┐
            │                   │                  │
┌───────────▼────────┐ ┌────────▼─────────┐ ┌──────▼───────────┐
│                    │ │                  │ │                  │
│   基础工具集       │ │  专业工具集       │ │   MCP工具集      │
│                    │ │                  │ │                  │
└────────────────────┘ └──────────────────┘ └──────────────────┘
```

## 2. 基础工具设计

### 2.1 工具基类 (BaseTool)

参考OpenManus的BaseTool设计，我们定义以下基础工具类：

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseTool(ABC, BaseModel):
    """工具基类"""
    
    name: str                         # 工具名称
    description: str                  # 工具描述
    parameters: Optional[dict] = None  # 工具参数定义
    
    class Config:
        arbitrary_types_allowed = True
    
    async def __call__(self, **kwargs) -> Any:
        """执行工具调用"""
        return await self.execute(**kwargs)
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具操作（子类必须实现）"""
    
    def to_param(self) -> Dict:
        """转换为函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
```

### 2.2 工具结果类 (ToolResult)

```python
class ToolResult(BaseModel):
    """工具执行结果"""
    
    output: Any = Field(default=None)           # 输出结果
    error: Optional[str] = Field(default=None)  # 错误信息
    base64_image: Optional[str] = Field(default=None)  # 图像数据（如有）
    system: Optional[str] = Field(default=None)  # 系统消息
    
    class Config:
        arbitrary_types_allowed = True
    
    def __bool__(self):
        """用于布尔上下文的评估"""
        return any(getattr(self, field) for field in self.__fields__)
    
    def __str__(self):
        """字符串表示"""
        return f"Error: {self.error}" if self.error else str(self.output)
    
    def replace(self, **kwargs):
        """返回带有替换字段的新ToolResult"""
        return type(self)(**{**self.dict(), **kwargs})
```

### 2.3 工具集合类 (ToolCollection)

```python
class ToolCollection:
    """工具集合"""
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, *tools: BaseTool):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
    
    def __iter__(self):
        """迭代器方法"""
        return iter(self.tools)
    
    def to_params(self) -> List[Dict[str, Any]]:
        """转换所有工具为参数列表"""
        return [tool.to_param() for tool in self.tools]
    
    async def execute(self, *, name: str, tool_input: Dict[str, Any] = None) -> ToolResult:
        """执行指定的工具"""
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            result = await tool(**tool_input)
            return result
        except ToolError as e:
            return ToolFailure(error=e.message)
    
    def add_tool(self, tool: BaseTool):
        """添加单个工具到集合"""
        if tool.name in self.tool_map:
            logger.warning(f"Tool {tool.name} already exists in collection, skipping")
            return self
        
        self.tools += (tool,)
        self.tool_map[tool.name] = tool
        return self
    
    def add_tools(self, *tools: BaseTool):
        """添加多个工具到集合"""
        for tool in tools:
            self.add_tool(tool)
        return self
```

## 3. 系统工具

### 3.1 Bash命令工具 (BashTool)

```python
class BashTool(BaseTool):
    """Bash命令执行工具"""
    
    name: str = "bash"
    description: str = "执行Bash命令并返回结果。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的Bash命令"
            },
            "cwd": {
                "type": "string",
                "description": "执行命令的工作目录"
            },
            "timeout": {
                "type": "integer",
                "description": "命令执行超时时间（秒）"
            }
        },
        "required": ["command"]
    }
    
    async def execute(self, command: str, cwd: Optional[str] = None, 
                     timeout: Optional[int] = None, **kwargs) -> ToolResult:
        """执行Bash命令"""
        try:
            # 使用沙箱环境执行命令
            result = await SANDBOX_CLIENT.run_command(
                command, 
                cwd=cwd, 
                timeout=timeout or 60
            )
            return ToolResult(output=result.stdout, error=result.stderr or None)
        except Exception as e:
            return ToolResult(error=f"执行命令失败: {str(e)}")
```

### 3.2 文件操作工具 (FileOperatorTool)

```python
class FileOperatorTool(BaseTool):
    """文件操作工具"""
    
    name: str = "file_operator"
    description: str = "执行文件操作，如读取、写入、列出文件等"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "list", "delete", "exists", "mkdir"],
                "description": "要执行的文件操作"
            },
            "path": {
                "type": "string",
                "description": "文件或目录路径"
            },
            "content": {
                "type": "string",
                "description": "写入文件的内容"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码",
                "default": "utf-8"
            }
        },
        "required": ["operation", "path"]
    }
    
    async def execute(self, operation: str, path: str, content: Optional[str] = None,
                     encoding: str = "utf-8", **kwargs) -> ToolResult:
        """执行文件操作"""
        try:
            # 标准化路径
            path = self._normalize_path(path)
            
            if operation == "read":
                return await self._read_file(path, encoding)
            elif operation == "write":
                return await self._write_file(path, content, encoding)
            elif operation == "list":
                return await self._list_dir(path)
            elif operation == "delete":
                return await self._delete_file(path)
            elif operation == "exists":
                return await self._file_exists(path)
            elif operation == "mkdir":
                return await self._make_directory(path)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"文件操作失败: {str(e)}")
    
    def _normalize_path(self, path: str) -> str:
        """标准化文件路径"""
        # 安全相关的路径处理
        return os.path.abspath(os.path.expanduser(path))
    
    async def _read_file(self, path: str, encoding: str) -> ToolResult:
        """读取文件内容"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"文件不存在: {path}")
            if os.path.isdir(path):
                return ToolResult(error=f"路径是目录而非文件: {path}")
            
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(error=f"读取文件失败: {str(e)}")
    
    async def _write_file(self, path: str, content: str, encoding: str) -> ToolResult:
        """写入文件内容"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            async with aiofiles.open(path, 'w', encoding=encoding) as f:
                await f.write(content)
            return ToolResult(output=f"文件写入成功: {path}")
        except Exception as e:
            return ToolResult(error=f"写入文件失败: {str(e)}")
    
    async def _list_dir(self, path: str) -> ToolResult:
        """列出目录内容"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"路径不存在: {path}")
            if not os.path.isdir(path):
                return ToolResult(error=f"路径是文件而非目录: {path}")
            
            files = []
            directories = []
            
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    directories.append(f"{item}/")
                else:
                    files.append(item)
            
            # 按字母顺序排序
            directories.sort()
            files.sort()
            
            result = {
                "directories": directories,
                "files": files,
                "path": path
            }
            
            return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=f"列出目录失败: {str(e)}")
```

## 4. AI工具

### 4.1 创建聊天完成工具 (CreateChatCompletionTool)

```python
class CreateChatCompletionTool(BaseTool):
    """创建聊天完成工具"""
    
    name: str = "create_chat_completion"
    description: str = "使用指定的大型语言模型（LLM）生成聊天回应"
    parameters: dict = {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["system", "user", "assistant"]
                        },
                        "content": {
                            "type": "string"
                        }
                    },
                    "required": ["role", "content"]
                },
                "description": "聊天消息历史"
            },
            "model_name": {
                "type": "string",
                "description": "要使用的模型名称，如不指定则使用默认模型"
            },
            "temperature": {
                "type": "number",
                "description": "生成的随机性(0-1)"
            }
        },
        "required": ["messages"]
    }
    
    _llm: Optional[LLM] = None
    
    def __init__(self, **data):
        """初始化创建聊天完成工具"""
        super().__init__(**data)
        self._llm = LLM()
    
    async def execute(self, messages: List[Dict[str, str]], model_name: Optional[str] = None,
                     temperature: Optional[float] = None, **kwargs) -> ToolResult:
        """执行聊天完成"""
        try:
            # 转换消息格式
            converted_messages = [Message(**msg) for msg in messages]
            
            # 使用模型生成回应
            response = await self._llm.ask(
                messages=converted_messages,
                temperature=temperature,
            )
            
            return ToolResult(output=response)
        except Exception as e:
            return ToolResult(error=f"创建聊天完成失败: {str(e)}")
```

## 5. 知识库工具

### 5.1 知识库管理工具 (KnowledgeManagerTool)

```python
class KnowledgeManagerTool(BaseTool):
    """知识库管理工具"""
    
    name: str = "knowledge_manager"
    description: str = "管理知识库，包括创建、更新、删除、列出知识库等"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["create", "update", "delete", "list", "upload", "remove_document"],
                "description": "要执行的知识库操作"
            },
            "kb_name": {
                "type": "string",
                "description": "知识库名称"
            },
            "kb_description": {
                "type": "string",
                "description": "知识库描述"
            },
            "document_path": {
                "type": "string",
                "description": "文档路径，用于上传或删除文档"
            },
            "document_id": {
                "type": "string",
                "description": "文档ID，用于删除特定文档"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, kb_name: Optional[str] = None,
                     kb_description: Optional[str] = None, document_path: Optional[str] = None,
                     document_id: Optional[str] = None, **kwargs) -> ToolResult:
        """执行知识库管理操作"""
        try:
            if operation == "create":
                return await self._create_kb(kb_name, kb_description)
            elif operation == "update":
                return await self._update_kb(kb_name, kb_description)
            elif operation == "delete":
                return await self._delete_kb(kb_name)
            elif operation == "list":
                return await self._list_kb()
            elif operation == "upload":
                return await self._upload_document(kb_name, document_path)
            elif operation == "remove_document":
                return await self._remove_document(kb_name, document_id)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"知识库操作失败: {str(e)}")
    
    async def _create_kb(self, kb_name: str, kb_description: Optional[str]) -> ToolResult:
        """创建知识库"""
        try:
            # 验证知识库名称
            if not kb_name:
                return ToolResult(error="知识库名称不能为空")
                
            # 检查是否已存在
            kb_service = KnowledgeBaseService()
            existing_kb = await kb_service.get_knowledge_base(kb_name)
            if existing_kb:
                return ToolResult(error=f"知识库已存在: {kb_name}")
            
            # 创建新知识库
            new_kb = await kb_service.create_knowledge_base(
                name=kb_name,
                description=kb_description or f"知识库: {kb_name}"
            )
            
            return ToolResult(output=f"知识库创建成功: {kb_name}")
        except Exception as e:
            return ToolResult(error=f"创建知识库失败: {str(e)}")
    
    async def _list_kb(self) -> ToolResult:
        """列出所有知识库"""
        try:
            kb_service = KnowledgeBaseService()
            knowledge_bases = await kb_service.list_knowledge_bases()
            
            formatted_kbs = []
            for kb in knowledge_bases:
                formatted_kbs.append({
                    "name": kb.name,
                    "description": kb.description,
                    "document_count": await kb_service.get_document_count(kb.name),
                    "created_at": kb.created_at.isoformat() if hasattr(kb, "created_at") else None
                })
            
            return ToolResult(output=formatted_kbs)
        except Exception as e:
            return ToolResult(error=f"列出知识库失败: {str(e)}")
            
    async def _upload_document(self, kb_name: str, document_path: str) -> ToolResult:
        """上传文档到知识库"""
        try:
            if not kb_name:
                return ToolResult(error="知识库名称不能为空")
            if not document_path:
                return ToolResult(error="文档路径不能为空")
                
            # 验证文件存在
            document_path = os.path.abspath(os.path.expanduser(document_path))
            if not os.path.exists(document_path):
                return ToolResult(error=f"文件不存在: {document_path}")
                
            # 获取知识库
            kb_service = KnowledgeBaseService()
            kb = await kb_service.get_knowledge_base(kb_name)
            if not kb:
                return ToolResult(error=f"知识库不存在: {kb_name}")
            
            # 上传文档
            document_id = await kb_service.add_document(kb_name, document_path)
            
            return ToolResult(output={
                "message": f"文档上传成功: {os.path.basename(document_path)}",
                "document_id": document_id
            })
        except Exception as e:
            return ToolResult(error=f"上传文档失败: {str(e)}")
```

### 5.2 RAG查询工具 (RagQueryTool)

```python
class RagQueryTool(BaseTool):
    """检索增强生成（RAG）查询工具"""
    
    name: str = "rag_query"
    description: str = "在知识库中执行语义搜索并获取相关内容"
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询"
            },
            "kb_name": {
                "type": "string",
                "description": "要搜索的知识库名称"
            },
            "top_k": {
                "type": "integer",
                "description": "返回的最大结果数",
                "default": 5
            },
            "similarity_threshold": {
                "type": "number",
                "description": "相似度阈值(0-1)",
                "default": 0.7
            }
        },
        "required": ["query", "kb_name"]
    }
    
    async def execute(self, query: str, kb_name: str, top_k: int = 5,
                     similarity_threshold: float = 0.7, **kwargs) -> ToolResult:
        """执行RAG查询"""
        try:
            # 获取知识库
            kb_service = KnowledgeBaseService()
            kb = await kb_service.get_knowledge_base(kb_name)
            if not kb:
                return ToolResult(error=f"未找到知识库: {kb_name}")
            
            # 执行语义搜索
            results = await kb_service.search(
                kb_name=kb_name,
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            if not results:
                return ToolResult(output="未找到匹配结果")
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.text,
                    "metadata": result.metadata,
                    "similarity": round(result.similarity, 4) if hasattr(result, "similarity") else None,
                    "document_id": result.document_id if hasattr(result, "document_id") else None,
                })
            
            return ToolResult(output=formatted_results)
        except Exception as e:
            return ToolResult(error=f"RAG查询失败: {str(e)}")
```

## 6. 专业工具

### 6.1 TARA分析工具 (TaraAnalysisTool)

```python
class TaraAnalysisTool(BaseTool):
    """威胁分析与风险评估工具"""
    
    name: str = "tara_analysis"
    description: str = "执行威胁分析与风险评估（TARA），识别威胁并评估风险"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["analyze_threat", "assess_risk", "generate_mitigation", "check_compliance"],
                "description": "要执行的TARA操作"
            },
            "target_description": {
                "type": "string",
                "description": "目标系统描述"
            },
            "threat_data": {
                "type": "object",
                "description": "威胁数据，用于风险评估"
            },
            "risk_data": {
                "type": "object",
                "description": "风险数据，用于生成缓解措施"
            },
            "regulation": {
                "type": "string",
                "description": "要检查合规性的法规名称"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, target_description: Optional[str] = None,
                     threat_data: Optional[dict] = None, risk_data: Optional[dict] = None,
                     regulation: Optional[str] = None, **kwargs) -> ToolResult:
        """执行TARA相关操作"""
        try:
            if operation == "analyze_threat":
                return await self._analyze_threat(target_description)
            elif operation == "assess_risk":
                return await self._assess_risk(threat_data)
            elif operation == "generate_mitigation":
                return await self._generate_mitigation(risk_data)
            elif operation == "check_compliance":
                return await self._check_compliance(target_description, regulation)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"TARA操作失败: {str(e)}")
```

### 6.2 测试用例生成工具 (TestCaseGeneratorTool)

```python
class TestCaseGeneratorTool(BaseTool):
    """测试用例生成工具"""
    
    name: str = "test_case_generator"
    description: str = "基于威胁分析结果生成测试用例"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["generate", "update", "analyze_coverage"],
                "description": "要执行的测试用例操作"
            },
            "tara_result": {
                "type": "object",
                "description": "TARA分析结果"
            },
            "test_type": {
                "type": "string",
                "enum": ["confirmation", "validation", "all"],
                "description": "生成的测试类型"
            },
            "test_cases": {
                "type": "array",
                "description": "现有测试用例，用于更新或分析覆盖率"
            },
            "threats": {
                "type": "array",
                "description": "威胁列表，用于分析覆盖率"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, tara_result: Optional[dict] = None,
                     test_type: str = "all", test_cases: Optional[list] = None,
                     threats: Optional[list] = None, **kwargs) -> ToolResult:
        """执行测试用例相关操作"""
        try:
            if operation == "generate":
                return await self._generate_test_cases(tara_result, test_type)
            elif operation == "update":
                return await self._update_test_cases(test_cases, tara_result)
            elif operation == "analyze_coverage":
                return await self._analyze_coverage(test_cases, threats)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"测试用例操作失败: {str(e)}")
```

### 6.3 测试执行工具 (TestExecutorTool)

```python
class TestExecutorTool(BaseTool):
    """测试执行工具"""
    
    name: str = "test_executor"
    description: str = "执行自动化测试并收集结果"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["execute", "get_status", "get_results", "abort"],
                "description": "要执行的测试操作"
            },
            "test_script": {
                "type": "string",
                "description": "测试脚本内容"
            },
            "test_id": {
                "type": "string",
                "description": "测试ID，用于获取状态或结果"
            },
            "environment": {
                "type": "object",
                "description": "测试环境配置"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, test_script: Optional[str] = None,
                     test_id: Optional[str] = None, environment: Optional[dict] = None,
                     **kwargs) -> ToolResult:
        """执行测试相关操作"""
        try:
            if operation == "execute":
                return await self._execute_test(test_script, environment)
            elif operation == "get_status":
                return await self._get_test_status(test_id)
            elif operation == "get_results":
                return await self._get_test_results(test_id)
            elif operation == "abort":
                return await self._abort_test(test_id)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"测试执行操作失败: {str(e)}")
```

### 6.4 报告生成工具 (ReportGeneratorTool)

```python
class ReportGeneratorTool(BaseTool):
    """报告生成工具"""
    
    name: str = "report_generator"
    description: str = "基于测试结果生成分析报告"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["analyze_results", "categorize_issues", "generate_risk_matrix", "generate_report"],
                "description": "要执行的报告操作"
            },
            "test_results": {
                "type": "object",
                "description": "测试结果数据"
            },
            "issues": {
                "type": "array",
                "description": "问题列表，用于分类或生成风险矩阵"
            },
            "analysis_data": {
                "type": "object",
                "description": "分析数据，用于生成最终报告"
            },
            "report_format": {
                "type": "string",
                "enum": ["markdown", "html", "pdf"],
                "description": "报告格式"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(self, operation: str, test_results: Optional[dict] = None,
                     issues: Optional[list] = None, analysis_data: Optional[dict] = None,
                     report_format: str = "markdown", **kwargs) -> ToolResult:
        """执行报告相关操作"""
        try:
            if operation == "analyze_results":
                return await self._analyze_results(test_results)
            elif operation == "categorize_issues":
                return await self._categorize_issues(issues)
            elif operation == "generate_risk_matrix":
                return await self._generate_risk_matrix(issues)
            elif operation == "generate_report":
                return await self._generate_report(analysis_data, report_format)
            else:
                return ToolResult(error=f"未知操作: {operation}")
        except Exception as e:
            return ToolResult(error=f"报告生成操作失败: {str(e)}")
```

## 7. MCP工具系统

参考OpenManus的MCP工具实现，我们将设计以下MCP相关组件：

### 7.1 MCP客户端工具 (MCPClientTool)

```python
class MCPClientTool(BaseTool):
    """MCP客户端工具基类"""
    
    name: str = "mcp_client"
    description: str = "与MCP服务器通信的客户端工具"
    server_id: str = ""
    tool_info: Optional[Dict[str, Any]] = None
    
    def __init__(self, server_id: str, tool_info: Dict[str, Any], **kwargs):
        """初始化MCP客户端工具"""
        super().__init__(**kwargs)
        self.server_id = server_id
        self.tool_info = tool_info
        self.name = tool_info.get("name") or f"mcp_{server_id}"
        self.description = tool_info.get("description") or f"MCP工具: {self.name}"
        self.parameters = tool_info.get("parameters") or {}
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行MCP工具调用"""
        try:
            # 获取MCP客户端实例
            client = self._get_mcp_client()
            if not client:
                return ToolResult(error=f"未找到MCP客户端: {self.server_id}")
            
            # 调用MCP工具
            result = await client.call_tool(
                self.name,
                kwargs
            )
            
            return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=f"MCP工具调用失败: {str(e)}")
```

### 7.2 MCP客户端集合 (MCPClients)

```python
class MCPClients:
    """MCP客户端集合"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.tools: List[MCPClientTool] = []
    
    async def connect_sse(self, server_url: str, server_id: str = "") -> None:
        """连接到SSE类型的MCP服务器"""
        client_id = server_id or server_url
        if client_id in self.clients:
            logger.warning(f"MCP client {client_id} already exists")
            return
        
        # 创建新的SSE客户端
        client = MCPSSEClient(server_url, client_id)
        await client.connect()
        
        # 添加到客户端字典
        self.clients[client_id] = client
        
        # 为每个工具创建MCPClientTool并添加到工具列表
        server_tools = await client.get_tools()
        for tool_info in server_tools:
            tool = MCPClientTool(
                server_id=client_id,
                tool_info=tool_info,
            )
            self.tools.append(tool)
    
    async def connect_stdio(self, command: str, args: List[str], server_id: str = "") -> None:
        """连接到STDIO类型的MCP服务器"""
        client_id = server_id or command
        if client_id in self.clients:
            logger.warning(f"MCP client {client_id} already exists")
            return
        
        # 创建新的STDIO客户端
        client = MCPStdioClient(command, args, client_id)
        await client.connect()
        
        # 添加到客户端字典
        self.clients[client_id] = client
        
        # 为每个工具创建MCPClientTool并添加到工具列表
        server_tools = await client.get_tools()
        for tool_info in server_tools:
            tool = MCPClientTool(
                server_id=client_id,
                tool_info=tool_info,
            )
            self.tools.append(tool)
    
    async def disconnect(self, server_id: str = "") -> None:
        """断开与MCP服务器的连接"""
        if not server_id:
            # 断开所有连接
            for client_id, client in list(self.clients.items()):
                await client.disconnect()
                del self.clients[client_id]
            # 清空工具列表
            self.tools.clear()
        elif server_id in self.clients:
            # 断开特定连接
            await self.clients[server_id].disconnect()
            del self.clients[server_id]
            # 移除相关工具
            self.tools = [tool for tool in self.tools if tool.server_id != server_id]
    
    def get_client(self, server_id: str) -> Optional[MCPClient]:
        """获取特定的MCP客户端"""
        return self.clients.get(server_id)
```

### 7.3 MCP工具工厂 (MCPToolFactory)

```python
class MCPToolFactory:
    """MCP工具工厂，用于创建与注册MCP工具"""
    
    @staticmethod
    async def create_tools_from_connection(connection_config: Dict[str, Any]) -> List[MCPClientTool]:
        """从连接配置创建MCP工具"""
        tools = []
        try:
            connection_type = connection_config.get("type")
            server_id = connection_config.get("id")
            
            if connection_type == "sse":
                url = connection_config.get("url")
                if not url:
                    logger.error("SSE连接需要URL")
                    return []
                
                # 创建连接并获取工具
                clients = MCPClients()
                await clients.connect_sse(url, server_id)
                tools = clients.tools
                
            elif connection_type == "stdio":
                command = connection_config.get("command")
                args = connection_config.get("args", [])
                if not command:
                    logger.error("STDIO连接需要命令")
                    return []
                
                # 创建连接并获取工具
                clients = MCPClients()
                await clients.connect_stdio(command, args, server_id)
                tools = clients.tools
                
            else:
                logger.error(f"不支持的连接类型: {connection_type}")
            
            return tools
        except Exception as e:
            logger.error(f"创建MCP工具失败: {e}")
            return []
    
    @staticmethod
    def register_tools(tools: List[MCPClientTool], tool_collection: ToolCollection) -> None:
        """注册MCP工具到工具集合"""
        for tool in tools:
            tool_collection.add_tool(tool)
```

## 8. 规划工具

参考OpenManus的PlanningTool实现，设计一个规划工具来帮助智能体管理复杂任务的执行计划：

### 8.1 规划工具 (PlanningTool)

```python
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
    plans: dict = {}
    
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
            return ToolResult(error=f"规划操作失败: {str(e)}")
```

## 9. MCP工具管理系统

参考OpenManus的MCP系统实现，我们设计一个灵活的外部工具集成框架，使智能体能够与外部工具进行交互。

### 9.1 MCP管理器

```python
class MCPManager:
    """MCP管理器，负责连接和管理MCP服务器"""
    
    def __init__(self):
        self.mcp_clients = MCPClients()
        self.connected_servers: Dict[str, Dict[str, Any]] = {}
    
    async def connect_mcp_server(self, server_config: MCPServerConfig) -> bool:
        """连接到MCP服务器"""
        try:
            if server_config.type == "sse":
                # SSE连接
                await self.mcp_clients.connect_sse(
                    server_url=server_config.url, 
                    server_id=server_config.id
                )
                self.connected_servers[server_config.id] = {
                    "url": server_config.url,
                    "type": "sse",
                    "status": "connected"
                }
            elif server_config.type == "stdio":
                # 标准I/O连接
                await self.mcp_clients.connect_stdio(
                    command=server_config.command,
                    args=server_config.args or [],
                    server_id=server_config.id
                )
                self.connected_servers[server_config.id] = {
                    "command": server_config.command,
                    "type": "stdio",
                    "status": "connected"
                }
            else:
                logger.error(f"不支持的连接类型: {server_config.type}")
                return False
                
            # 更新可用工具
            await self._refresh_tools(server_config.id)
            logger.info(f"成功连接到MCP服务器: {server_config.id}")
            return True
        except Exception as e:
            logger.error(f"连接MCP服务器失败: {str(e)}")
            return False
    
    async def disconnect_mcp_server(self, server_id: str) -> bool:
        """断开与MCP服务器的连接"""
        try:
            await self.mcp_clients.disconnect(server_id)
            if server_id in self.connected_servers:
                self.connected_servers.pop(server_id)
            logger.info(f"已断开与MCP服务器的连接: {server_id}")
            return True
        except Exception as e:
            logger.error(f"断开MCP服务器连接失败: {str(e)}")
            return False
    
    async def _refresh_tools(self, server_id: str = "") -> Tuple[List[str], List[str]]:
        """刷新可用工具列表"""
        if not self.mcp_clients.sessions:
            return [], []
            
        # 获取当前工具的schema
        response = await self.mcp_clients.list_tools()
        current_tools = {tool.name: tool.inputSchema for tool in response.tools}
        
        # 确定新增、移除和更改的工具
        current_names = set(current_tools.keys())
        previous_names = set(self.mcp_clients.tool_schemas.keys()) if hasattr(self.mcp_clients, "tool_schemas") else set()
        
        added_tools = list(current_names - previous_names)
        removed_tools = list(previous_names - current_names)
        
        # 检查现有工具的schema变化
        changed_tools = []
        for name in current_names.intersection(previous_names):
            if current_tools[name] != getattr(self.mcp_clients, "tool_schemas", {}).get(name):
                changed_tools.append(name)
        
        # 更新存储的schemas
        if hasattr(self.mcp_clients, "tool_schemas"):
            self.mcp_clients.tool_schemas = current_tools
        
        # 记录变化
        if added_tools:
            logger.info(f"新增MCP工具: {added_tools}")
        if removed_tools:
            logger.info(f"移除MCP工具: {removed_tools}")
        if changed_tools:
            logger.info(f"变更MCP工具: {changed_tools}")
        
        return added_tools, removed_tools
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用的MCP工具"""
        tools = []
        for tool in self.mcp_clients.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "server_id": tool.server_id,
                "original_name": tool.original_name if hasattr(tool, "original_name") else tool.name
            })
        return tools
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务器的状态"""
        return self.connected_servers
```

### 9.2 MCP客户端工具

```python
class MCPClientTool(BaseTool):
    """代表MCP服务器上可调用的工具的客户端代理"""
    
    session: Optional[ClientSession] = None
    server_id: str = ""  # 添加服务器标识符
    original_name: str = ""  # 原始工具名称
    
    async def execute(self, **kwargs) -> ToolResult:
        """通过远程调用MCP服务器执行工具"""
        if not self.session:
            return ToolResult(error="未连接到MCP服务器")
            
        try:
            logger.info(f"执行工具: {self.original_name}")
            result = await self.session.call_tool(self.original_name, kwargs)
            content_str = ", ".join(
                item.text for item in result.content if hasattr(item, "text")
            )
            return ToolResult(output=content_str or "无输出返回。")
        except Exception as e:
            return ToolResult(error=f"执行工具失败: {str(e)}")
```

### 9.3 MCP服务器

```python
class MCPServer:
    """MCP服务器实现，提供工具注册和执行功能"""
    
    def __init__(self, name: str = "kunlunsec"):
        """初始化MCP服务器"""
        self.server = FastMCP(name)
        self.tools: Dict[str, BaseTool] = {}
        
        # 初始化标准工具
        self.tools["bash"] = BashTool()
        self.tools["file_operator"] = FileOperatorTool()
        self.tools["terminate"] = TerminateTool()
    
    def register_tool(self, tool: BaseTool, method_name: Optional[str] = None) -> None:
        """注册工具，验证参数并生成文档"""
        tool_name = method_name or tool.name
        tool_param = tool.to_param()
        tool_function = tool_param["function"]
        
        # 定义要注册的异步函数
        async def tool_method(**kwargs):
            logger.info(f"执行 {tool_name}: {kwargs}")
            result = await tool.execute(**kwargs)
            
            logger.info(f"{tool_name} 的执行结果: {result}")
            
            # 处理不同类型的结果
            if hasattr(result, "model_dump"):
                return json.dumps(result.model_dump())
            elif isinstance(result, dict):
                return json.dumps(result)
            return result
        
        # 设置方法元数据
        tool_method.__name__ = tool_name
        tool_method.__doc__ = self._build_docstring(tool_function)
        tool_method.__signature__ = self._build_signature(tool_function)
        
        # 注册到服务器
        self.server.tool()(tool_method)
        logger.info(f"已注册工具: {tool_name}")
    
    def _build_docstring(self, tool_function: dict) -> str:
        """根据工具函数元数据构建格式化的文档字符串"""
        description = tool_function.get("description", "")
        param_props = tool_function.get("parameters", {}).get("properties", {})
        required_params = tool_function.get("parameters", {}).get("required", [])
        
        # 构建文档字符串
        docstring = description
        if param_props:
            docstring += "\n\n参数:\n"
            for param_name, param_details in param_props.items():
                required_str = "(必需)" if param_name in required_params else "(可选)"
                param_type = param_details.get("type", "any")
                param_desc = param_details.get("description", "")
                docstring += f"    {param_name} ({param_type}) {required_str}: {param_desc}\n"
                
        return docstring
    
    def register_all_tools(self) -> None:
        """注册所有工具"""
        for tool in self.tools.values():
            self.register_tool(tool)
    
    async def cleanup(self) -> None:
        """清理服务器资源"""
        logger.info("正在清理资源")
        # 清理有cleanup方法的工具
        for tool_name, tool_instance in self.tools.items():
            if hasattr(tool_instance, "cleanup") and asyncio.iscoroutinefunction(
                tool_instance.cleanup
            ):
                try:
                    logger.debug(f"正在清理工具: {tool_name}")
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(f"清理工具 '{tool_name}' 失败: {e}", exc_info=True)
        
        logger.info("资源清理完成")
    
    def run(self, transport: str = "stdio") -> None:
        """运行MCP服务器"""
        # 注册所有工具
        self.register_all_tools()
        
        # 注册清理函数
        atexit.register(lambda: asyncio.run(self.cleanup()))
        
        # 启动服务器
        logger.info(f"启动 KunlunSec 服务器 ({transport} 模式)")
        self.server.run(transport=transport)
```

### 9.4 MCP配置模型

```python
class MCPServerConfig(BaseModel):
    """MCP服务器配置"""
    
    id: str = Field(..., description="服务器唯一标识符")
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器连接类型(sse或stdio)")
    url: Optional[str] = Field(None, description="SSE连接的服务器URL")
    command: Optional[str] = Field(None, description="stdio连接的命令")
    args: List[str] = Field(default_factory=list, description="stdio命令的参数")
    auto_connect: bool = Field(default=True, description="启动时自动连接")
    
    @validator("type")
    def validate_type(cls, v):
        """验证连接类型"""
        if v not in ["sse", "stdio"]:
            raise ValueError(f"不支持的连接类型: {v}，必须是'sse'或'stdio'")
        return v
    
    @validator("url")
    def validate_url(cls, v, values):
        """验证URL（当类型为sse时必需）"""
        if values.get("type") == "sse" and not v:
            raise ValueError("SSE连接类型必须提供URL")
        return v
    
    @validator("command")
    def validate_command(cls, v, values):
        """验证命令（当类型为stdio时必需）"""
        if values.get("type") == "stdio" and not v:
            raise ValueError("stdio连接类型必须提供命令")
        return v
```

### 9.5 智能体与MCP系统集成

```python
class AutomationTestAgent(ToolCallAgent):
    """自动化测试执行智能体"""
    
    # MCP客户端
    mcp_manager: MCPManager = Field(default_factory=MCPManager)
    
    # 初始化方法
    @classmethod
    async def create(cls, **kwargs) -> "AutomationTestAgent":
        """创建并初始化自动化测试智能体"""
        instance = cls(**kwargs)
        await instance.initialize_environments()
        await instance.initialize_mcp_connections()
        return instance
    
    async def initialize_mcp_connections(self):
        """初始化MCP工具连接"""
        # 连接配置的MCP服务器
        for server_config in config.mcp_config.servers.values():
            if server_config.auto_connect:
                await self.mcp_manager.connect_mcp_server(server_config)
    
    async def cleanup(self):
        """清理智能体资源"""
        # 断开所有MCP连接
        for server_id in list(self.mcp_manager.connected_servers.keys()):
            await self.mcp_manager.disconnect_mcp_server(server_id)
        
        # 调用父类清理方法
        await super().cleanup()
```

## 10. 车联网安全测试工具

为了支持车联网安全测试的特定需求，我们设计了一系列专用工具，这些工具可以帮助智能体执行各种安全测试任务。

### 10.1 网络协议分析工具

```python
class NetworkProtocolAnalyzerTool(BaseTool):
    """车联网网络协议分析工具"""
    
    name: str = "network_protocol_analyzer"
    description: str = "分析车联网通信协议，识别安全漏洞和异常模式"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["analyze_pcap", "scan_protocol", "detect_anomalies", "extract_messages"],
                "description": "要执行的操作类型"
            },
            "protocol": {
                "type": "string",
                "enum": ["can", "lin", "flexray", "ethernet", "doip", "someip", "j1939", "uds"],
                "description": "要分析的协议类型"
            },
            "input_file": {
                "type": "string",
                "description": "输入文件路径（如pcap文件）"
            },
            "filters": {
                "type": "object",
                "description": "分析过滤条件"
            },
            "timeout": {
                "type": "integer",
                "description": "分析超时时间（秒）",
                "default": 300
            }
        },
        "required": ["operation", "protocol"]
    }

    async def execute(self, operation: str, protocol: str, input_file: Optional[str] = None,
                     filters: Optional[Dict[str, Any]] = None, timeout: int = 300, **kwargs) -> ToolResult:
        """执行网络协议分析"""
        try:
            # 确认协议分析器可用
            analyzer = self._get_protocol_analyzer(protocol)
            if not analyzer:
                return ToolResult(error=f"不支持的协议: {protocol}")
                
            # 执行请求的操作
            if operation == "analyze_pcap":
                if not input_file:
                    return ToolResult(error="分析pcap文件需要提供input_file参数")
                    
                result = await self._analyze_pcap_file(analyzer, input_file, filters, timeout)
                
            elif operation == "scan_protocol":
                result = await self._scan_protocol(analyzer, filters, timeout)
                
            elif operation == "detect_anomalies":
                if not input_file:
                    return ToolResult(error="检测异常需要提供input_file参数")
                    
                result = await self._detect_anomalies(analyzer, input_file, filters, timeout)
                
            elif operation == "extract_messages":
                if not input_file:
                    return ToolResult(error="提取消息需要提供input_file参数")
                    
                result = await self._extract_messages(analyzer, input_file, filters, timeout)
                
            else:
                return ToolResult(error=f"不支持的操作: {operation}")
                
            return ToolResult(output=result)
            
        except Exception as e:
            return ToolResult(error=f"协议分析失败: {str(e)}")
    
    def _get_protocol_analyzer(self, protocol: str):
        """获取指定协议的分析器"""
        analyzers = {
            "can": CANAnalyzer(),
            "lin": LINAnalyzer(),
            "flexray": FlexRayAnalyzer(),
            "ethernet": EthernetAnalyzer(),
            "doip": DoIPAnalyzer(),
            "someip": SomeIPAnalyzer(),
            "j1939": J1939Analyzer(),
            "uds": UDSAnalyzer()
        }
        return analyzers.get(protocol.lower())
    
    async def _analyze_pcap_file(self, analyzer, file_path: str, 
                               filters: Optional[Dict[str, Any]], timeout: int) -> Dict[str, Any]:
        """分析PCAP文件"""
        # 实现PCAP文件分析逻辑
        pass
    
    async def _scan_protocol(self, analyzer, filters: Optional[Dict[str, Any]], 
                           timeout: int) -> Dict[str, Any]:
        """扫描协议漏洞"""
        # 实现协议扫描逻辑
        pass
    
    async def _detect_anomalies(self, analyzer, file_path: str, 
                              filters: Optional[Dict[str, Any]], timeout: int) -> Dict[str, Any]:
        """检测通信异常"""
        # 实现异常检测逻辑
        pass
    
    async def _extract_messages(self, analyzer, file_path: str, 
                              filters: Optional[Dict[str, Any]], timeout: int) -> Dict[str, Any]:
        """提取通信消息"""
        # 实现消息提取逻辑
        pass
```

### 10.2 固件分析工具

```python
class FirmwareAnalyzerTool(BaseTool):
    """车联网固件分析工具"""
    
    name: str = "firmware_analyzer"
    description: str = "分析车联网设备固件，检测安全漏洞和后门"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["extract", "analyze", "scan_vulnerabilities", "check_backdoors", "identify_components"],
                "description": "要执行的操作类型"
            },
            "firmware_path": {
                "type": "string",
                "description": "固件文件路径"
            },
            "output_dir": {
                "type": "string",
                "description": "输出目录路径"
            },
            "scan_depth": {
                "type": "string",
                "enum": ["basic", "normal", "deep"],
                "description": "扫描深度",
                "default": "normal"
            },
            "timeout": {
                "type": "integer",
                "description": "分析超时时间（秒）",
                "default": 600
            }
        },
        "required": ["operation", "firmware_path"]
    }
    
    async def execute(self, operation: str, firmware_path: str, output_dir: Optional[str] = None,
                     scan_depth: str = "normal", timeout: int = 600, **kwargs) -> ToolResult:
        """执行固件分析"""
        try:
            # 验证固件文件存在
            if not os.path.exists(firmware_path):
                return ToolResult(error=f"固件文件不存在: {firmware_path}")
                
            # 设置输出目录
            if not output_dir:
                output_dir = f"./firmware_analysis_{uuid.uuid4().hex[:8]}"
                os.makedirs(output_dir, exist_ok=True)
                
            # 执行请求的操作
            if operation == "extract":
                result = await self._extract_firmware(firmware_path, output_dir, timeout)
                
            elif operation == "analyze":
                result = await self._analyze_firmware(firmware_path, output_dir, scan_depth, timeout)
                
            elif operation == "scan_vulnerabilities":
                result = await self._scan_vulnerabilities(firmware_path, output_dir, scan_depth, timeout)
                
            elif operation == "check_backdoors":
                result = await self._check_backdoors(firmware_path, output_dir, scan_depth, timeout)
                
            elif operation == "identify_components":
                result = await self._identify_components(firmware_path, output_dir, timeout)
                
            else:
                return ToolResult(error=f"不支持的操作: {operation}")
                
            return ToolResult(output=result)
            
        except Exception as e:
            return ToolResult(error=f"固件分析失败: {str(e)}")
    
    async def _extract_firmware(self, firmware_path: str, output_dir: str, timeout: int) -> Dict[str, Any]:
        """提取固件内容"""
        # 实现固件提取逻辑
        pass
    
    async def _analyze_firmware(self, firmware_path: str, output_dir: str, 
                              scan_depth: str, timeout: int) -> Dict[str, Any]:
        """全面分析固件"""
        # 实现固件分析逻辑
        pass
    
    async def _scan_vulnerabilities(self, firmware_path: str, output_dir: str, 
                                  scan_depth: str, timeout: int) -> Dict[str, Any]:
        """扫描固件漏洞"""
        # 实现漏洞扫描逻辑
        pass
    
    async def _check_backdoors(self, firmware_path: str, output_dir: str, 
                             scan_depth: str, timeout: int) -> Dict[str, Any]:
        """检查后门"""
        # 实现后门检查逻辑
        pass
    
    async def _identify_components(self, firmware_path: str, output_dir: str, 
                                 timeout: int) -> Dict[str, Any]:
        """识别固件组件"""
        # 实现组件识别逻辑
        pass
```

### 10.3 ECU测试工具

```python
class ECUTestTool(BaseTool):
    """ECU测试工具"""
    
    name: str = "ecu_tester"
    description: str = "执行ECU安全测试，包括诊断服务测试、会话管理测试和访问控制测试"
    parameters: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["diagnostic_test", "session_test", "access_control_test", "fuzzing_test", "replay_attack"],
                "description": "要执行的测试类型"
            },
            "target_device": {
                "type": "string",
                "description": "目标设备标识符或地址"
            },
            "interface": {
                "type": "string",
                "enum": ["can0", "can1", "vcan0", "eth0", "doip"],
                "description": "通信接口"
            },
            "test_config": {
                "type": "object",
                "description": "测试配置参数"
            },
            "timeout": {
                "type": "integer",
                "description": "测试超时时间（秒）",
                "default": 300
            }
        },
        "required": ["operation", "target_device", "interface"]
    }
    
    async def execute(self, operation: str, target_device: str, interface: str,
                     test_config: Optional[Dict[str, Any]] = None, 
                     timeout: int = 300, **kwargs) -> ToolResult:
        """执行ECU测试"""
        try:
            # 初始化测试环境
            test_env = await self._initialize_test_environment(interface, target_device)
            if not test_env:
                return ToolResult(error=f"无法初始化测试环境: {interface}, {target_device}")
            
            # 准备测试配置
            config = test_config or {}
            
            # 执行请求的测试
            if operation == "diagnostic_test":
                result = await self._run_diagnostic_test(test_env, config, timeout)
                
            elif operation == "session_test":
                result = await self._run_session_test(test_env, config, timeout)
                
            elif operation == "access_control_test":
                result = await self._run_access_control_test(test_env, config, timeout)
                
            elif operation == "fuzzing_test":
                result = await self._run_fuzzing_test(test_env, config, timeout)
                
            elif operation == "replay_attack":
                result = await self._run_replay_attack(test_env, config, timeout)
                
            else:
                return ToolResult(error=f"不支持的测试类型: {operation}")
                
            # 清理测试环境
            await self._cleanup_test_environment(test_env)
            
            return ToolResult(output=result)
            
        except Exception as e:
            return ToolResult(error=f"ECU测试失败: {str(e)}")
    
    async def _initialize_test_environment(self, interface: str, target: str) -> Dict[str, Any]:
        """初始化测试环境"""
        # 实现测试环境初始化逻辑
        pass
    
    async def _run_diagnostic_test(self, test_env: Dict[str, Any], 
                                 config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行诊断服务测试"""
        # 实现诊断服务测试逻辑
        pass
    
    async def _run_session_test(self, test_env: Dict[str, Any], 
                              config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行会话管理测试"""
        # 实现会话管理测试逻辑
        pass
    
    async def _run_access_control_test(self, test_env: Dict[str, Any], 
                                     config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行访问控制测试"""
        # 实现访问控制测试逻辑
        pass
    
    async def _run_fuzzing_test(self, test_env: Dict[str, Any], 
                              config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行模糊测试"""
        # 实现模糊测试逻辑
        pass
    
    async def _run_replay_attack(self, test_env: Dict[str, Any], 
                               config: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行重放攻击测试"""
        # 实现重放攻击测试逻辑
        pass
    
    async def _cleanup_test_environment(self, test_env: Dict[str, Any]) -> None:
        """清理测试环境"""
        # 实现环境清理逻辑
        pass
```

### 10.4 安全测试报告生成工具

```python
class SecurityReportGeneratorTool(BaseTool):
    """安全测试报告生成工具"""
    
    name: str = "security_report_generator"
    description: str = "根据测试结果生成安全测试报告"
    parameters: dict = {
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "enum": ["summary", "detailed", "compliance", "executive", "technical"],
                "description": "报告类型"
            },
            "test_results": {
                "type": "array",
                "description": "测试结果数据"
            },
            "compliance_standards": {
                "type": "array",
                "description": "需要检查合规性的标准列表",
                "items": {
                    "type": "string"
                }
            },
            "output_format": {
                "type": "string",
                "enum": ["html", "pdf", "markdown", "json"],
                "description": "输出格式",
                "default": "html"
            },
            "output_path": {
                "type": "string",
                "description": "输出文件路径"
            }
        },
        "required": ["report_type", "test_results"]
    }
    
    async def execute(self, report_type: str, test_results: List[Dict[str, Any]],
                     compliance_standards: Optional[List[str]] = None,
                     output_format: str = "html", output_path: Optional[str] = None, **kwargs) -> ToolResult:
        """生成安全测试报告"""
        try:
            # 验证测试结果
            if not test_results:
                return ToolResult(error="测试结果为空，无法生成报告")
                
            # 设置输出路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"./security_report_{report_type}_{timestamp}.{output_format}"
                
            # 生成报告
            if report_type == "summary":
                report_data = await self._generate_summary_report(test_results, output_format)
                
            elif report_type == "detailed":
                report_data = await self._generate_detailed_report(test_results, output_format)
                
            elif report_type == "compliance":
                if not compliance_standards:
                    return ToolResult(error="生成合规性报告需要提供compliance_standards参数")
                    
                report_data = await self._generate_compliance_report(test_results, compliance_standards, output_format)
                
            elif report_type == "executive":
                report_data = await self._generate_executive_report(test_results, output_format)
                
            elif report_type == "technical":
                report_data = await self._generate_technical_report(test_results, output_format)
                
            else:
                return ToolResult(error=f"不支持的报告类型: {report_type}")
        
            # 保存报告
            await self._save_report(report_data, output_path, output_format)
            
            return ToolResult(output={
                "report_path": output_path,
                "report_type": report_type,
                "format": output_format,
                "summary": report_data.get("summary", {})
            })
            
        except Exception as e:
            return ToolResult(error=f"报告生成失败: {str(e)}")
    
    async def _generate_summary_report(self, test_results: List[Dict[str, Any]], 
                                     output_format: str) -> Dict[str, Any]:
        """生成摘要报告"""
        # 实现摘要报告生成逻辑
        pass
    
    async def _generate_detailed_report(self, test_results: List[Dict[str, Any]], 
                                      output_format: str) -> Dict[str, Any]:
        """生成详细报告"""
        # 实现详细报告生成逻辑
        pass
    
    async def _generate_compliance_report(self, test_results: List[Dict[str, Any]], 
                                        standards: List[str], output_format: str) -> Dict[str, Any]:
        """生成合规性报告"""
        # 实现合规性报告生成逻辑
        pass
    
    async def _generate_executive_report(self, test_results: List[Dict[str, Any]], 
                                       output_format: str) -> Dict[str, Any]:
        """生成管理层报告"""
        # 实现管理层报告生成逻辑
        pass
    
    async def _generate_technical_report(self, test_results: List[Dict[str, Any]], 
                                       output_format: str) -> Dict[str, Any]:
        """生成技术报告"""
        # 实现技术报告生成逻辑
        pass
    
    async def _save_report(self, report_data: Dict[str, Any], output_path: str, 
                         output_format: str) -> None:
        """保存报告到文件"""
        # 实现报告保存逻辑
        pass
```

