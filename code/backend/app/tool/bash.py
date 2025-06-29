import asyncio
import os
from typing import Optional

from app.core.logging import logger
from app.sandbox.client import SANDBOX_CLIENT
from .base import BaseTool, ToolResult


_BASH_DESCRIPTION = """执行Bash命令并返回结果。
* 长时间运行的命令: 对于可能无限期运行的命令，应在后台运行，并将输出重定向到文件，例如 command = `python3 app.py > server.log 2>&1 &`。
* 交互式: 如果bash命令返回退出代码`-1`，这意味着进程尚未完成。助手必须发送第二个调用到终端，command为空（这将检索任何额外的日志），或者可以发送额外的文本（将command设置为文本）到运行进程的STDIN，或者可以发送command=`ctrl+c`来中断进程。
* 超时: 如果命令执行结果显示"命令超时。向进程发送SIGINT"，助手应尝试在后台运行该命令。
"""


class _BashSession:
    """Bash会话类，管理单个bash shell会话"""
    
    _started: bool
    _process: asyncio.subprocess.Process
    
    command: str = "/bin/bash"
    _output_delay: float = 0.2  # 秒
    _timeout: float = 120.0  # 秒
    _sentinel: str = "<<exit>>"
    
    def __init__(self):
        self._started = False
        self._timed_out = False
    
    async def start(self):
        """启动bash会话"""
        if self._started:
            return
            
        self._process = await asyncio.create_subprocess_shell(
            self.command,
            preexec_fn=os.setsid,
            shell=True,
            bufsize=0,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        self._started = True
    
    def stop(self):
        """终止bash会话"""
        if not self._started:
            raise ValueError("会话尚未启动")
        if self._process.returncode is not None:
            return
        self._process.terminate()
    
    async def run(self, command: str):
        """在bash会话中执行命令"""
        if not self._started:
            raise ValueError("会话尚未启动")
        if self._process.returncode is not None:
            return ToolResult(
                error=f"bash已退出，返回码为 {self._process.returncode}",
                system="工具必须重启"
            )
        if self._timed_out:
            raise ValueError(
                f"超时: bash在 {self._timeout} 秒内未返回，必须重启"
            )
            
        # 我们知道这些不是None，因为我们使用PIPE创建了进程
        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr
        
        # 向进程发送命令
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()
        
        # 从进程读取输出，直到找到哨兵
        try:
            async with asyncio.timeout(self._timeout):
                while True:
                    await asyncio.sleep(self._output_delay)
                    # 如果直接从stdout/stderr读取，它将永远等待EOF
                    # 直接使用StreamReader缓冲区
                    output = self._process.stdout._buffer.decode()
                    if self._sentinel in output:
                        # 去除哨兵并中断
                        output = output[:output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            self._timed_out = True
            raise ValueError(
                f"超时: bash在 {self._timeout} 秒内未返回，必须重启"
            )
            
        if output.endswith("\n"):
            output = output[:-1]
            
        error = self._process.stderr._buffer.decode()
        if error.endswith("\n"):
            error = error[:-1]
            
        # 清除缓冲区，以便正确读取下一个输出
        self._process.stdout._buffer.clear()
        self._process.stderr._buffer.clear()
        
        return ToolResult(output=output, error=error)


class Bash(BaseTool):
    """Bash命令执行工具"""
    
    name: str = "bash"
    description: str = _BASH_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的Bash命令。可以为空以查看前一个命令的额外日志。可以是`ctrl+c`来中断当前运行的进程。"
            },
            "restart": {
                "type": "boolean",
                "description": "是否重启bash会话"
            }
        },
        "required": ["command"]
    }
    
    _session: Optional[_BashSession] = None
    
    async def execute(self, command: str = None, restart: bool = False, **kwargs) -> ToolResult:
        """执行Bash命令"""
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()
            
            return ToolResult(system="工具已重启")
            
        if self._session is None:
            self._session = _BashSession()
            await self._session.start()
            
        if command is not None:
            try:
                return await self._session.run(command)
            except ValueError as e:
                logger.error(f"执行命令失败: {str(e)}")
                return ToolResult(error=str(e))
            
        raise ValueError("未提供命令") 