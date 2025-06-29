"""
KunlunSec AI Platform - 字符串替换编辑器工具

提供文件查看、创建和编辑功能，支持沙箱环境。
"""

import os
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, List, Literal, Optional, Dict, Union

from app.core.logging import logger
from app.sandbox.client import SANDBOX_CLIENT
from .base import BaseTool, ToolResult


# 命令类型定义
Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]

# 常量
SNIPPET_LINES: int = 4
MAX_RESPONSE_LEN: int = 16000
TRUNCATED_MESSAGE: str = (
    "<响应被截断><注意>为了节省上下文，只向您显示了此文件的一部分。"
    "您应该在使用`grep -n`在文件中搜索以找到您要查找的内容的行号后重试此工具。</注意>"
)

# 工具描述
_STR_REPLACE_EDITOR_DESCRIPTION = """自定义编辑工具，用于查看、创建和编辑文件
* 状态在命令调用和与用户的讨论之间保持持久
* 如果`path`是文件，`view`显示应用`cat -n`的结果。如果`path`是目录，`view`列出最多2级深度的非隐藏文件和目录
* 如果指定的`path`已经存在为文件，则不能使用`create`命令
* 如果`command`生成较长的输出，它将被截断并标记为`<响应被截断>`
* `undo_edit`命令将恢复对`path`处文件的最后一次编辑

使用`str_replace`命令的注意事项：
* `old_str`参数应与原始文件中的一行或多行连续内容完全匹配。注意空格！
* 如果`old_str`参数在文件中不是唯一的，则不会执行替换。确保在`old_str`中包含足够的上下文以使其唯一
* `new_str`参数应包含应替换`old_str`的编辑行
"""


def maybe_truncate(
    content: str, truncate_after: Optional[int] = MAX_RESPONSE_LEN
) -> str:
    """如果内容超过指定长度，则截断内容并附加通知"""
    if not truncate_after or len(content) <= truncate_after:
        return content
    return content[:truncate_after] + TRUNCATED_MESSAGE


class StrReplaceEditorTool(BaseTool):
    """字符串替换编辑器工具，用于查看、创建和编辑文件，支持沙箱环境"""

    name: str = "str_replace_editor"
    description: str = _STR_REPLACE_EDITOR_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "要运行的命令。允许的选项是：`view`、`create`、`str_replace`、`insert`、`undo_edit`。",
                "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                "type": "string",
            },
            "path": {
                "description": "文件或目录的绝对路径。",
                "type": "string",
            },
            "file_text": {
                "description": "`create`命令的必需参数，包含要创建的文件的内容。",
                "type": "string",
            },
            "old_str": {
                "description": "`str_replace`命令的必需参数，包含要替换的`path`中的字符串。",
                "type": "string",
            },
            "new_str": {
                "description": "`str_replace`命令的可选参数，包含新字符串（如果未给出，则不会添加字符串）。`insert`命令的必需参数，包含要插入的字符串。",
                "type": "string",
            },
            "insert_line": {
                "description": "`insert`命令的必需参数。`new_str`将在`path`的行`insert_line`之后插入。",
                "type": "integer",
            },
            "view_range": {
                "description": "当`path`指向文件时，`view`命令的可选参数。如果未提供，则显示完整文件。如果提供，则将在指定的行号范围内显示文件，例如[11, 12]将显示第11行和第12行。索引从1开始。设置`[start_line, -1]`显示从`start_line`到文件末尾的所有行。",
                "items": {"type": "integer"},
                "type": "array",
            },
        },
        "required": ["command", "path"],
    }
    
    # 文件历史记录
    _file_history: DefaultDict[str, List[str]] = defaultdict(list)
    
    async def execute(
        self,
        command: str,
        path: str,
        file_text: Optional[str] = None,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """执行文件操作命令"""
        try:
            # 验证路径和命令组合
            await self._validate_path(command, path)
            
            # 执行相应的命令
            if command == "view":
                result = await self._view(path, view_range)
            elif command == "create":
                if file_text is None:
                    return ToolResult(error="命令create需要参数`file_text`")
                result = await self._create(path, file_text)
            elif command == "str_replace":
                if old_str is None:
                    return ToolResult(error="命令str_replace需要参数`old_str`")
                result = await self._str_replace(path, old_str, new_str)
            elif command == "insert":
                if insert_line is None:
                    return ToolResult(error="命令insert需要参数`insert_line`")
                if new_str is None:
                    return ToolResult(error="命令insert需要参数`new_str`")
                result = await self._insert(path, insert_line, new_str)
            elif command == "undo_edit":
                result = await self._undo_edit(path)
            else:
                return ToolResult(error=f"未识别的命令：{command}")
                
            return result
        except Exception as e:
            logger.error(f"文件操作失败: {str(e)}")
            return ToolResult(error=f"文件操作失败: {str(e)}")
    
    async def _validate_path(self, command: str, path: str) -> None:
        """验证路径和命令组合"""
        # 检查路径是否为绝对路径
        if not os.path.isabs(path):
            raise ValueError(f"路径 {path} 不是绝对路径")
            
        # 对于非create命令，检查路径是否存在
        if command != "create":
            exists = await self._file_exists(path)
            if not exists:
                raise ValueError(f"路径 {path} 不存在。请提供有效路径。")
                
            # 检查路径是否为目录
            is_dir = await self._is_directory(path)
            if is_dir and command != "view":
                raise ValueError(f"路径 {path} 是目录，只能对目录使用`view`命令")
                
        # 对于create命令，检查文件是否已存在
        elif command == "create":
            exists = await self._file_exists(path)
            if exists:
                raise ValueError(f"文件已存在于：{path}。不能使用`create`命令覆盖文件。")
    
    async def _view(self, path: str, view_range: Optional[List[int]] = None) -> ToolResult:
        """查看文件或目录内容"""
        # 检查是否为目录
        is_dir = await self._is_directory(path)
        
        if is_dir:
            # 查看目录
            return await self._view_directory(path)
        else:
            # 查看文件
            return await self._view_file(path, view_range)
    
    async def _view_directory(self, path: str) -> ToolResult:
        """查看目录内容"""
        try:
            # 使用ls命令列出目录内容
            cmd = f"find {path} -maxdepth 2 -not -path '*/\\.*' | sort"
            result = await SANDBOX_CLIENT.run_command(cmd)
            
            # 格式化输出
            lines = result.strip().split('\n')
            formatted_output = f"目录内容 ({path}):\n\n"
            
            for line in lines:
                if line.strip():
                    rel_path = os.path.relpath(line, path)
                    if rel_path == '.':
                        continue
                    formatted_output += f"{rel_path}\n"
                    
            return ToolResult(output=formatted_output)
        except Exception as e:
            return ToolResult(error=f"查看目录失败: {str(e)}")
    
    async def _view_file(self, path: str, view_range: Optional[List[int]] = None) -> ToolResult:
        """查看文件内容"""
        try:
            # 读取文件内容
            content = await self._read_file(path)
            
            # 如果指定了查看范围，则只显示指定行
            if view_range and len(view_range) == 2:
                lines = content.split('\n')
                start_line = max(1, view_range[0])
                end_line = view_range[1] if view_range[1] != -1 else len(lines)
                end_line = min(len(lines), end_line)
                
                # 确保范围有效
                if start_line > end_line:
                    return ToolResult(error=f"无效的查看范围: {view_range}")
                    
                # 提取指定行
                selected_lines = lines[start_line-1:end_line]
                
                # 格式化输出
                formatted_output = f"文件内容 ({path}, 行 {start_line}-{end_line}):\n\n"
                for i, line in enumerate(selected_lines, start=start_line):
                    formatted_output += f"{i:4d} | {line}\n"
                    
                return ToolResult(output=maybe_truncate(formatted_output))
            else:
                # 显示整个文件，带行号
                lines = content.split('\n')
                formatted_output = f"文件内容 ({path}, {len(lines)} 行):\n\n"
                
                for i, line in enumerate(lines, start=1):
                    formatted_output += f"{i:4d} | {line}\n"
                    
                return ToolResult(output=maybe_truncate(formatted_output))
        except Exception as e:
            return ToolResult(error=f"查看文件失败: {str(e)}")
    
    async def _create(self, path: str, file_text: str) -> ToolResult:
        """创建文件"""
        try:
            # 确保目录存在
            directory = os.path.dirname(path)
            if directory:
                await SANDBOX_CLIENT.run_command(f"mkdir -p {directory}")
                
            # 写入文件内容
            await self._write_file(path, file_text)
            
            # 保存到历史记录
            self._file_history[path].append(file_text)
            
            return ToolResult(output=f"文件创建成功: {path}")
        except Exception as e:
            return ToolResult(error=f"创建文件失败: {str(e)}")
    
    async def _str_replace(self, path: str, old_str: str, new_str: Optional[str] = None) -> ToolResult:
        """字符串替换"""
        try:
            # 读取文件内容
            content = await self._read_file(path)
            
            # 检查旧字符串是否存在于文件中
            if old_str not in content:
                return ToolResult(error=f"文件中未找到指定的字符串")
                
            # 检查旧字符串是否唯一
            if content.count(old_str) > 1:
                return ToolResult(error=f"文件中找到多个匹配项。请提供更具体的上下文以确保唯一性。")
                
            # 执行替换
            new_content = content.replace(old_str, new_str or "")
            
            # 保存到历史记录
            self._file_history[path].append(content)
            
            # 写入新内容
            await self._write_file(path, new_content)
            
            return ToolResult(output=f"替换成功: {path}")
        except Exception as e:
            return ToolResult(error=f"字符串替换失败: {str(e)}")
    
    async def _insert(self, path: str, insert_line: int, new_str: str) -> ToolResult:
        """在指定行后插入内容"""
        try:
            # 读取文件内容
            content = await self._read_file(path)
            lines = content.split('\n')
            
            # 检查行号是否有效
            if insert_line < 0 or insert_line > len(lines):
                return ToolResult(error=f"无效的行号: {insert_line}，文件共有 {len(lines)} 行")
                
            # 保存到历史记录
            self._file_history[path].append(content)
            
            # 执行插入
            new_lines = lines[:insert_line]
            new_lines.append(new_str)
            new_lines.extend(lines[insert_line:])
            new_content = '\n'.join(new_lines)
            
            # 写入新内容
            await self._write_file(path, new_content)
            
            return ToolResult(output=f"插入成功: {path}, 行 {insert_line}")
        except Exception as e:
            return ToolResult(error=f"插入内容失败: {str(e)}")
    
    async def _undo_edit(self, path: str) -> ToolResult:
        """撤销上一次编辑"""
        try:
            # 检查历史记录
            if not self._file_history[path]:
                return ToolResult(error=f"没有可撤销的编辑: {path}")
                
            # 获取上一个版本
            previous_content = self._file_history[path].pop()
            
            # 写入上一个版本
            await self._write_file(path, previous_content)
            
            return ToolResult(output=f"撤销成功: {path}")
        except Exception as e:
            return ToolResult(error=f"撤销编辑失败: {str(e)}")
    
    async def _read_file(self, path: str) -> str:
        """读取文件内容"""
        return await SANDBOX_CLIENT.read_file(path)
    
    async def _write_file(self, path: str, content: str) -> None:
        """写入文件内容"""
        await SANDBOX_CLIENT.write_file(path, content)
    
    async def _file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        try:
            result = await SANDBOX_CLIENT.run_command(f"test -e {path} && echo 'true' || echo 'false'")
            return "true" in result
        except:
            return False
    
    async def _is_directory(self, path: str) -> bool:
        """检查路径是否为目录"""
        try:
            result = await SANDBOX_CLIENT.run_command(f"test -d {path} && echo 'true' || echo 'false'")
            return "true" in result
        except:
            return False 