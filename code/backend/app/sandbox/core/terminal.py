"""
KunlunSec AI Platform - Docker终端实现

提供与Docker容器的交互式终端功能。
"""

import asyncio
import os
from typing import Dict, Optional, List, Any

from docker.models.containers import Container

from app.core.logging import logger
from app.sandbox.core.exceptions import SandboxTerminalError


class DockerTerminal:
    """Docker终端实现，提供与Docker容器的交互式终端功能"""
    
    def __init__(self, container: Container, working_dir: str = "/workspace"):
        """初始化Docker终端
        
        Args:
            container: Docker容器对象
            working_dir: 工作目录
        """
        self.container = container
        self.working_dir = working_dir
        self.exec_id = None
        self.socket = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化终端"""
        if self._initialized:
            return
            
        try:
            # 创建执行实例
            exec_config = self.container.client.api.exec_create(
                self.container.id,
                cmd="/bin/bash",
                tty=True,
                stdin=True,
                working_dir=self.working_dir
            )
            
            self.exec_id = exec_config["Id"]
            
            # 启动执行实例
            self.socket = self.container.client.api.exec_start(
                self.exec_id,
                socket=True,
                tty=True,
                stdin=True,
                stream=True
            )
            
            # 发送初始命令，设置环境
            await self._write("export PS1='$ '\n")
            await self._read()  # 读取初始输出
            
            self._initialized = True
            logger.info(f"Docker终端已初始化，容器ID: {self.container.id}")
        except Exception as e:
            logger.error(f"初始化Docker终端失败: {str(e)}")
            raise SandboxTerminalError(f"初始化Docker终端失败: {str(e)}")
    
    async def send(self, command: str) -> str:
        """发送命令到终端并获取输出
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        if not self._initialized:
            raise SandboxTerminalError("终端未初始化")
            
        try:
            # 特殊命令处理
            if command.strip() == "ctrl+c":
                await self._write("\x03")  # 发送CTRL+C
                return "发送了中断信号 (CTRL+C)"
                
            # 清除之前的输出
            await self._write("clear\n")
            await self._read()
            
            # 发送命令
            sentinel = f"__END_OF_COMMAND_{os.urandom(4).hex()}__"
            full_command = f"{command}\necho {sentinel}\n"
            
            await self._write(full_command)
            
            # 读取输出直到找到哨兵
            output = ""
            while True:
                chunk = await self._read()
                if not chunk:
                    break
                    
                output += chunk
                if sentinel in output:
                    # 去除哨兵及其之后的内容
                    output = output.split(sentinel)[0]
                    break
            
            # 清理输出（去除命令本身和提示符）
            lines = output.split("\n")
            if lines and command in lines[0]:
                lines = lines[1:]
                
            # 如果最后一行是提示符，去除它
            if lines and lines[-1].strip() == "$":
                lines = lines[:-1]
                
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"发送命令到终端失败: {str(e)}")
            raise SandboxTerminalError(f"发送命令到终端失败: {str(e)}")
    
    async def _write(self, data: str) -> None:
        """向终端写入数据"""
        if not self.socket:
            raise SandboxTerminalError("终端套接字未初始化")
            
        try:
            self.socket._sock.send(data.encode())
        except Exception as e:
            logger.error(f"向终端写入数据失败: {str(e)}")
            raise SandboxTerminalError(f"向终端写入数据失败: {str(e)}")
    
    async def _read(self, timeout: float = 0.5) -> str:
        """从终端读取数据
        
        Args:
            timeout: 读取超时时间（秒）
            
        Returns:
            读取的数据
        """
        if not self.socket:
            raise SandboxTerminalError("终端套接字未初始化")
            
        try:
            # 设置套接字为非阻塞模式
            self.socket._sock.setblocking(False)
            
            # 使用select等待数据
            loop = asyncio.get_event_loop()
            ready = await loop.run_in_executor(
                None,
                lambda: asyncio.get_event_loop().run_until_complete(
                    asyncio.wait_for(
                        loop.sock_recv(self.socket._sock, 4096),
                        timeout
                    )
                )
            )
            
            if not ready:
                return ""
                
            # 读取数据
            data = b""
            try:
                while True:
                    chunk = self.socket._sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except (BlockingIOError, TimeoutError):
                pass
                
            # 解码数据
            return data.decode("utf-8", errors="replace")
        except asyncio.TimeoutError:
            return ""
        except Exception as e:
            logger.error(f"从终端读取数据失败: {str(e)}")
            raise SandboxTerminalError(f"从终端读取数据失败: {str(e)}")
    
    async def close(self) -> None:
        """关闭终端"""
        if not self._initialized:
            return
            
        try:
            if self.socket:
                # 发送退出命令
                await self._write("exit\n")
                
                # 关闭套接字
                try:
                    self.socket._sock.close()
                except:
                    pass
                    
                self.socket = None
                
            self._initialized = False
            logger.info("Docker终端已关闭")
        except Exception as e:
            logger.error(f"关闭Docker终端失败: {str(e)}")
            # 即使关闭失败也不抛出异常，以免影响其他清理操作 