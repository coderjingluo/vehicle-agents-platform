import os
import logging
from typing import Optional, Dict, Any

import aiofiles

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


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
            logger.error(f"文件操作失败: {str(e)}")
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
            if content is None:
                return ToolResult(error="缺少要写入的内容")
                
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
    
    async def _delete_file(self, path: str) -> ToolResult:
        """删除文件"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"文件不存在: {path}")
                
            if os.path.isdir(path):
                os.rmdir(path)
                return ToolResult(output=f"目录删除成功: {path}")
            else:
                os.remove(path)
                return ToolResult(output=f"文件删除成功: {path}")
        except Exception as e:
            return ToolResult(error=f"删除文件失败: {str(e)}")
    
    async def _file_exists(self, path: str) -> ToolResult:
        """检查文件是否存在"""
        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False
        is_dir = os.path.isdir(path) if exists else False
        
        return ToolResult(output={
            "exists": exists,
            "is_file": is_file,
            "is_dir": is_dir,
            "path": path
        })
    
    async def _make_directory(self, path: str) -> ToolResult:
        """创建目录"""
        try:
            os.makedirs(path, exist_ok=True)
            return ToolResult(output=f"目录创建成功: {path}")
        except Exception as e:
            return ToolResult(error=f"创建目录失败: {str(e)}") 