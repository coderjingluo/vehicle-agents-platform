"""
KunlunSec AI Platform - Python执行工具

提供安全的Python代码执行功能。
"""

import multiprocessing
import sys
import traceback
from io import StringIO
from typing import Dict, Optional, Any

from app.core.logging import logger
from .base import BaseTool, ToolResult


class PythonExecuteTool(BaseTool):
    """Python代码执行工具"""
    
    name: str = "python_execute"
    description: str = "执行Python代码并返回结果。注意：只有打印输出是可见的，函数返回值不会被捕获。使用print语句查看结果。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的Python代码"
            },
            "timeout": {
                "type": "integer",
                "description": "执行超时时间（秒），默认为5秒"
            }
        },
        "required": ["code"]
    }
    
    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        """在独立进程中执行代码
        
        Args:
            code: 要执行的Python代码
            result_dict: 存储结果的字典
            safe_globals: 安全的全局变量
        """
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            exec(code, safe_globals, safe_globals)
            result_dict["observation"] = output_buffer.getvalue()
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout
    
    async def execute(self, code: str, timeout: int = 5, **kwargs) -> ToolResult:
        """执行Python代码
        
        Args:
            code: 要执行的Python代码
            timeout: 执行超时时间（秒）
            
        Returns:
            执行结果
        """
        try:
            with multiprocessing.Manager() as manager:
                result = manager.dict({"observation": "", "success": False})
                
                # 准备安全的全局变量
                if isinstance(__builtins__, dict):
                    safe_globals = {"__builtins__": __builtins__}
                else:
                    safe_globals = {"__builtins__": __builtins__.__dict__.copy()}
                
                # 创建并启动进程
                proc = multiprocessing.Process(
                    target=self._run_code, args=(code, result, safe_globals)
                )
                proc.start()
                proc.join(timeout)
                
                # 处理超时
                if proc.is_alive():
                    proc.terminate()
                    proc.join(1)
                    return ToolResult(
                        error=f"执行超时，超过{timeout}秒",
                        output={"success": False}
                    )
                
                # 返回结果
                result_dict = dict(result)
                if result_dict["success"]:
                    return ToolResult(output=result_dict["observation"])
                else:
                    return ToolResult(
                        error=f"执行错误: {result_dict['observation']}",
                        output={"success": False}
                    )
                
        except Exception as e:
            logger.error(f"Python执行工具错误: {str(e)}\n{traceback.format_exc()}")
            return ToolResult(error=f"Python执行工具错误: {str(e)}") 