"""
工具注册表
管理所有可用的工具，包括内置工具和MCP工具
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import asyncio
from datetime import datetime
from enum import Enum


class ToolType(Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"      # 内置工具
    MCP = "mcp"             # MCP工具
    CUSTOM = "custom"        # 自定义工具


class ToolStatus(Enum):
    """工具状态枚举"""
    AVAILABLE = "available"  # 可用
    DISABLED = "disabled"    # 已禁用
    ERROR = "error"         # 错误状态


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        tool_type: ToolType = ToolType.BUILTIN
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.tool_type = tool_type
        self.status = ToolStatus.AVAILABLE
        self.last_used = None
        self.usage_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        pass
    
    def update_usage_stats(self, success: bool = True):
        """更新使用统计"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        if not success:
            self.error_count += 1
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "tool_type": self.tool_type.value,
            "status": self.status.value,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "error_count": self.error_count
        }


class BuiltinTool(BaseTool):
    """内置工具"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable
    ):
        super().__init__(name, description, parameters, ToolType.BUILTIN)
        self.func = func
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        try:
            # 如果函数是协程，直接await
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**parameters)
            else:
                result = self.func(**parameters)
            
            self.update_usage_stats(success=True)
            return {"success": True, "result": result}
            
        except Exception as e:
            self.update_usage_stats(success=False)
            return {"success": False, "error": str(e)}


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._disabled_tools: set = set()
        
        # 初始化内置工具
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        
        # 文本处理工具
        self.register_tool(BuiltinTool(
            name="text_analyzer",
            description="分析文本内容，提取关键信息",
            parameters={
                "text": {"type": "string", "description": "要分析的文本"},
                "analysis_type": {"type": "string", "description": "分析类型"}
            },
            func=self._text_analyzer
        ))
        
        # TARA分析工具
        self.register_tool(BuiltinTool(
            name="tara_analyzer",
            description="进行威胁分析和风险评估",
            parameters={
                "system_description": {"type": "string", "description": "系统描述"},
                "threat_model": {"type": "string", "description": "威胁模型"}
            },
            func=self._tara_analyzer
        ))
        
        # 测试用例生成工具
        self.register_tool(BuiltinTool(
            name="testcase_generator",
            description="基于TARA结果生成测试用例",
            parameters={
                "tara_results": {"type": "object", "description": "TARA分析结果"},
                "test_type": {"type": "string", "description": "测试类型"}
            },
            func=self._testcase_generator
        ))
    
    async def _text_analyzer(self, text: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """文本分析工具实现"""
        if analysis_type == "summary":
            sentences = text.split('。')
            summary = '。'.join(sentences[:3]) + '。' if len(sentences) > 3 else text
            return {"summary": summary, "word_count": len(text)}
        return {"result": f"分析完成: {analysis_type}"}
    
    async def _tara_analyzer(self, system_description: str, threat_model: str) -> Dict[str, Any]:
        """TARA分析工具实现"""
        threats = [
            {"id": "T001", "name": "未授权访问", "severity": "高"},
            {"id": "T002", "name": "拒绝服务攻击", "severity": "中"}
        ]
        return {"threats": threats, "system": system_description}
    
    async def _testcase_generator(self, tara_results: Dict[str, Any], test_type: str = "security") -> Dict[str, Any]:
        """测试用例生成工具实现"""
        test_cases = []
        if "threats" in tara_results:
            for threat in tara_results["threats"]:
                test_case = {
                    "id": f"TC_{threat['id']}",
                    "name": f"测试{threat['name']}",
                    "type": test_type
                }
                test_cases.append(test_case)
        return {"test_cases": test_cases}
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出工具"""
        tools_info = {}
        for name, tool in self._tools.items():
            if name not in self._disabled_tools:
                tools_info[name] = tool.get_info()
        return tools_info
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"工具 {tool_name} 不存在"}
        
        if tool_name in self._disabled_tools:
            return {"success": False, "error": f"工具 {tool_name} 已被禁用"}
        
        return await tool.execute(parameters)


# 全局工具注册表实例
tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表"""
    return tool_registry 