"""
KunlunSec AI Platform - 代码生成工具模块

提供基于LLM的代码生成功能。
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from pydantic import Field
import json

from app.core.config import settings
from app.core.logging import logger
from app.tool.base import BaseTool, ToolResult

class CodeGeneratorTool(BaseTool):
    """代码生成工具，使用LLM生成各种类型的代码"""
    
    name: str = "code_generator"
    description: str = "根据提供的需求生成代码，支持多种编程语言，特别适合生成测试脚本"
    parameters: dict = {
        "type": "object",
        "properties": {
            "language": {
                "description": "要生成的代码语言，如python, javascript, java等",
                "type": "string",
                "enum": ["python", "javascript", "java", "c++", "go", "rust", "typescript"]
            },
            "prompt": {
                "description": "详细的代码需求描述，应包含生成代码的功能要求、输入输出、特殊要求等",
                "type": "string"
            },
            "filename": {
                "description": "生成代码的文件名(可选)",
                "type": "string"
            },
            "framework": {
                "description": "使用的框架(可选)，如pytest, jest, junit等",
                "type": "string"
            },
            "test_case": {
                "description": "测试用例详情(可选)，用于生成测试代码时提供",
                "type": "object"
            },
            "boilerplate": {
                "description": "是否生成完整的样板代码，包括导入语句、类定义等",
                "type": "boolean",
                "default": True
            }
        },
        "required": ["prompt", "language"],
        "additionalProperties": False
    }
    
    async def execute(
        self,
        *,
        language: str,
        prompt: str,
        filename: Optional[str] = None,
        framework: Optional[str] = None,
        test_case: Optional[Dict[str, Any]] = None,
        boilerplate: bool = True,
        **kwargs
    ) -> ToolResult:
        """执行代码生成
        
        Args:
            language: 目标编程语言
            prompt: 代码需求描述
            filename: 生成代码的文件名（可选）
            framework: 使用的框架（可选）
            test_case: 测试用例详情（可选）
            boilerplate: 是否生成完整样板代码
            
        Returns:
            ToolResult: 包含生成的代码和元数据
        """
        try:
            # 记录请求
            logger.info(f"开始生成 {language} 代码")
            
            # 使用LLM生成代码
            code = await self._generate_code_with_llm(language, prompt, framework, test_case, boilerplate)
            
            # 创建结果
            result = {
                "code": code,
                "language": language,
                "filename": filename or f"generated_code.{self._get_file_extension(language)}",
                "framework": framework
            }
            
            if test_case:
                result["test_case"] = test_case
                
            logger.info(f"代码生成成功，生成了 {len(code.splitlines())} 行代码")
            
            return ToolResult(output=result)
            
        except Exception as e:
            logger.error(f"代码生成失败: {str(e)}")
            return ToolResult(error=f"代码生成失败: {str(e)}")
    
    async def _generate_code_with_llm(
        self,
        language: str,
        prompt: str,
        framework: Optional[str] = None,
        test_case: Optional[Dict[str, Any]] = None,
        boilerplate: bool = True
    ) -> str:
        """使用LLM生成代码
        
        Args:
            language: 目标编程语言
            prompt: 代码需求描述
            framework: 使用的框架（可选）
            test_case: 测试用例详情（可选）
            boilerplate: 是否生成完整样板代码
            
        Returns:
            str: 生成的代码
        """
        # 初始化LLM客户端
        from app.agent.base import LLM
        llm = LLM()
        
        # 准备系统提示
        system_prompt = """你是一个专业的代码生成助手，擅长根据需求生成高质量、符合最佳实践的代码。
请仅输出代码，不要包含解释或注释，除非特别要求。
生成的代码应该可以直接运行，包含必要的导入语句和依赖。
"""

        # 准备用户提示
        framework_info = f"使用 {framework} 框架" if framework else ""
        boilerplate_request = "生成完整的样板代码，包括必要的导入语句、类定义等" if boilerplate else "只生成核心代码逻辑，不包含样板代码"
        
        user_prompt = f"""请用 {language} {framework_info} 编写以下代码：

{prompt}

{boilerplate_request}

"""

        # 如果提供了测试用例，添加到提示中
        if test_case:
            test_case_str = json.dumps(test_case, ensure_ascii=False, indent=2)
            user_prompt += f"""
这是相关的测试用例信息，请根据这些信息生成相应的测试代码：

{test_case_str}
"""

        # 添加特定语言的最佳实践要求
        language_specific_tips = self._get_language_specific_tips(language, framework)
        if language_specific_tips:
            user_prompt += f"""
请遵循以下 {language} 的最佳实践：
{language_specific_tips}
"""

        # 调用LLM
        response = await llm.ask(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # 提取代码部分
        return self._extract_code(response, language)
    
    def _extract_code(self, response: str, language: str) -> str:
        """从LLM响应中提取代码
        
        如果响应中包含代码块标记(```python等)，则提取代码块内容
        否则返回整个响应
        
        Args:
            response: LLM响应文本
            language: 代码语言
            
        Returns:
            str: 提取的代码
        """
        import re
        
        # 尝试匹配代码块
        code_block_pattern = r"```(?:" + language + r"|[a-zA-Z]*)\s*(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            # 合并所有匹配的代码块
            return "\n\n".join(matches)
        
        # 如果没有找到代码块，返回整个响应
        return response
    
    def _get_file_extension(self, language: str) -> str:
        """获取语言对应的文件扩展名
        
        Args:
            language: 编程语言
            
        Returns:
            str: 文件扩展名
        """
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "c++": "cpp",
            "go": "go",
            "rust": "rs"
        }
        
        return extensions.get(language.lower(), "txt")
    
    def _get_language_specific_tips(self, language: str, framework: Optional[str] = None) -> str:
        """获取特定语言的最佳实践提示
        
        Args:
            language: 编程语言
            framework: 使用的框架（可选）
            
        Returns:
            str: 最佳实践提示
        """
        tips = {
            "python": """
- 使用类型提示增强代码可读性
- 遵循PEP 8编码规范
- 使用适当的异常处理
- 使用上下文管理器管理资源
""",
            "javascript": """
- 使用const和let，避免使用var
- 使用现代ES6+特性
- 适当处理异步操作和错误
""",
            "typescript": """
- 定义明确的接口和类型
- 使用类型守卫提高类型安全性
- 避免使用any类型
""",
            "python-pytest": """
- 使用fixtures共享测试资源
- 使用参数化测试减少代码重复
- 适当的测试命名和组织
- 使用assert语句而不是self.assert*方法
"""
        }
        
        key = language.lower()
        if framework:
            combined_key = f"{language.lower()}-{framework.lower()}"
            if combined_key in tips:
                return tips[combined_key]
        
        return tips.get(key, "") 