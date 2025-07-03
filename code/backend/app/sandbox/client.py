"""
KunlunSec AI Platform - 沙箱客户端

提供与沙箱环境交互的客户端接口。
"""

import os
import asyncio
from typing import Dict, List, Optional, Union, Any

from app.core.logging import logger
from app.sandbox.core.sandbox import DockerSandbox
from app.sandbox.core.exceptions import SandboxError


class SandboxClient:
    """沙箱客户端，提供与沙箱环境交互的接口"""
    
    def __init__(self):
        """初始化沙箱客户端"""
        self._sandbox = None
        self._active_terminals = {}
        self._initialized = False
    
    async def _ensure_initialized(self):
        """确保沙箱已初始化"""
        if not self._initialized:
            await self.initialize()
    
    async def initialize(self, image: str = "ubuntu:latest", workspace: str = "/workspace"):
        """初始化沙箱环境
        
        Args:
            image: Docker镜像名称
            workspace: 沙箱中的工作目录
        """
        if self._initialized:
            return
            
        try:
            self._sandbox = DockerSandbox(image=image, workspace=workspace)
            await self._sandbox.initialize()
            self._initialized = True
            logger.info(f"沙箱环境已初始化，使用镜像 {image}")
        except Exception as e:
            logger.error(f"初始化沙箱环境失败: {str(e)}")
            raise SandboxError(f"初始化沙箱环境失败: {str(e)}")
    
    async def run_command(self, command: str, cwd: Optional[str] = None, 
                         timeout: int = 60, env: Optional[Dict[str, str]] = None) -> str:
        """在沙箱中执行命令
        
        Args:
            command: 要执行的命令
            cwd: 工作目录
            timeout: 超时时间（秒）
            env: 环境变量
            
        Returns:
            命令执行结果
        """
        await self._ensure_initialized()
        
        try:
            result = await self._sandbox.run_command(
                command=command,
                cwd=cwd,
                timeout=timeout,
                env=env
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"命令执行超时: {command}")
            raise TimeoutError(f"命令执行超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            raise SandboxError(f"执行命令失败: {str(e)}")
    
    async def read_file(self, path: str) -> str:
        """读取沙箱中的文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容
        """
        await self._ensure_initialized()
        
        try:
            content = await self._sandbox.read_file(path)
            return content
        except Exception as e:
            logger.error(f"读取文件失败 {path}: {str(e)}")
            raise SandboxError(f"读取文件失败: {str(e)}")
    
    async def write_file(self, path: str, content: str) -> bool:
        """写入内容到沙箱中的文件
        
        Args:
            path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        await self._ensure_initialized()
        
        try:
            success = await self._sandbox.write_file(path, content)
            return success
        except Exception as e:
            logger.error(f"写入文件失败 {path}: {str(e)}")
            raise SandboxError(f"写入文件失败: {str(e)}")
    
    async def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """列出沙箱中的目录内容
        
        Args:
            path: 目录路径
            
        Returns:
            目录内容列表
        """
        await self._ensure_initialized()
        
        try:
            entries = await self._sandbox.list_directory(path)
            return entries
        except Exception as e:
            logger.error(f"列出目录失败 {path}: {str(e)}")
            raise SandboxError(f"列出目录失败: {str(e)}")
    
    async def file_exists(self, path: str) -> bool:
        """检查沙箱中的文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            文件是否存在
        """
        await self._ensure_initialized()
        
        try:
            exists = await self._sandbox.file_exists(path)
            return exists
        except Exception as e:
            logger.error(f"检查文件是否存在失败 {path}: {str(e)}")
            raise SandboxError(f"检查文件是否存在失败: {str(e)}")
    
    async def create_terminal(self, terminal_id: Optional[str] = None) -> str:
        """创建交互式终端
        
        Args:
            terminal_id: 终端ID，如果为None则自动生成
            
        Returns:
            终端ID
        """
        await self._ensure_initialized()
        
        try:
            if terminal_id is None:
                terminal_id = f"term_{len(self._active_terminals) + 1}"
                
            if terminal_id in self._active_terminals:
                logger.warning(f"终端ID已存在: {terminal_id}，将返回现有终端")
                return terminal_id
                
            terminal = await self._sandbox.create_terminal()
            self._active_terminals[terminal_id] = terminal
            
            logger.info(f"创建终端: {terminal_id}")
            return terminal_id
        except Exception as e:
            logger.error(f"创建终端失败: {str(e)}")
            raise SandboxError(f"创建终端失败: {str(e)}")
    
    async def terminal_send(self, terminal_id: str, command: str) -> str:
        """向终端发送命令
        
        Args:
            terminal_id: 终端ID
            command: 要发送的命令
            
        Returns:
            命令执行结果
        """
        if terminal_id not in self._active_terminals:
            raise SandboxError(f"终端不存在: {terminal_id}")
            
        try:
            terminal = self._active_terminals[terminal_id]
            result = await terminal.send(command)
            return result
        except Exception as e:
            logger.error(f"向终端发送命令失败: {str(e)}")
            raise SandboxError(f"向终端发送命令失败: {str(e)}")
    
    async def close_terminal(self, terminal_id: str) -> bool:
        """关闭终端
        
        Args:
            terminal_id: 终端ID
            
        Returns:
            是否成功
        """
        if terminal_id not in self._active_terminals:
            logger.warning(f"尝试关闭不存在的终端: {terminal_id}")
            return False
            
        try:
            terminal = self._active_terminals[terminal_id]
            await terminal.close()
            del self._active_terminals[terminal_id]
            logger.info(f"关闭终端: {terminal_id}")
            return True
        except Exception as e:
            logger.error(f"关闭终端失败: {str(e)}")
            raise SandboxError(f"关闭终端失败: {str(e)}")
    
    async def cleanup(self):
        """清理所有资源"""
        if not self._initialized:
            return
            
        # 关闭所有终端
        terminal_ids = list(self._active_terminals.keys())
        for terminal_id in terminal_ids:
            try:
                await self.close_terminal(terminal_id)
            except Exception as e:
                logger.error(f"清理终端 {terminal_id} 失败: {str(e)}")
        
        # 关闭沙箱
        if self._sandbox:
            try:
                await self._sandbox.cleanup()
                self._initialized = False
                logger.info("沙箱环境已清理")
            except Exception as e:
                logger.error(f"清理沙箱环境失败: {str(e)}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        if self._initialized and self._sandbox:
            logger.warning("沙箱客户端被销毁但未清理，这可能导致资源泄漏") 
            
SANDBOX_CLIENT = SandboxClient()