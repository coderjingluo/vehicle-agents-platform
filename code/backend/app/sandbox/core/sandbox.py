"""
KunlunSec AI Platform - Docker沙箱实现

提供基于Docker容器的沙箱环境。
"""

import os
import asyncio
import tempfile
from typing import Dict, List, Optional, Any, Tuple

import docker
from docker.errors import DockerException, ImageNotFound, APIError

from app.core.logging import logger
from app.sandbox.core.exceptions import SandboxError, SandboxInitError, SandboxCommandError, SandboxFileError
from app.sandbox.core.terminal import DockerTerminal


class DockerSandbox:
    """Docker沙箱实现，提供安全的命令执行环境"""
    
    def __init__(self, image: str = "ubuntu:latest", workspace: str = "/workspace"):
        """初始化Docker沙箱
        
        Args:
            image: Docker镜像名称
            workspace: 容器内的工作目录
        """
        self.image = image
        self.workspace = workspace
        self.container = None
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化沙箱环境"""
        if self._initialized:
            return
            
        try:
            # 创建Docker客户端
            self.client = docker.from_env()
            
            # 检查镜像是否存在，不存在则拉取
            try:
                self.client.images.get(self.image)
                logger.info(f"使用已有的镜像: {self.image}")
            except ImageNotFound:
                logger.info(f"拉取镜像: {self.image}")
                self.client.images.pull(self.image)
            
            # 创建容器
            self.container = self.client.containers.run(
                self.image,
                command="tail -f /dev/null",  # 保持容器运行
                detach=True,
                tty=True,
                working_dir=self.workspace,
                volumes={},  # 可以根据需要添加卷映射
                environment={},  # 可以根据需要添加环境变量
                remove=True,  # 容器停止后自动删除
                network_mode="bridge",  # 使用桥接网络
                cap_add=["SYS_ADMIN"],  # 添加必要的权限
                security_opt=["seccomp=unconfined"],  # 禁用seccomp安全配置
            )
            
            # 确保工作目录存在
            self.container.exec_run(f"mkdir -p {self.workspace}")
            
            self._initialized = True
            logger.info(f"Docker沙箱初始化完成，容器ID: {self.container.id}")
        except (DockerException, APIError) as e:
            logger.error(f"初始化Docker沙箱失败: {str(e)}")
            raise SandboxInitError(f"初始化Docker沙箱失败: {str(e)}")
    
    async def run_command(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        timeout: int = 60,
        env: Optional[Dict[str, str]] = None
    ) -> str:
        """在沙箱中执行命令
        
        Args:
            command: 要执行的命令
            cwd: 工作目录
            timeout: 超时时间（秒）
            env: 环境变量
            
        Returns:
            命令执行结果
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            # 准备命令
            exec_command = command
            if cwd:
                exec_command = f"cd {cwd} && {command}"
                
            # 准备环境变量
            environment = {}
            if env:
                environment.update(env)
                
            # 执行命令
            logger.debug(f"执行命令: {exec_command}")
            result = await asyncio.wait_for(
                self._exec_command(exec_command, environment),
                timeout=timeout
            )
            
            return result
        except asyncio.TimeoutError:
            logger.warning(f"命令执行超时: {command}")
            raise asyncio.TimeoutError(f"命令执行超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            raise SandboxCommandError(f"执行命令失败: {str(e)}")
    
    async def _exec_command(self, command: str, env: Dict[str, str] = None) -> str:
        """执行命令并返回结果"""
        loop = asyncio.get_event_loop()
        
        def _exec():
            exec_id = self.client.api.exec_create(
                self.container.id,
                command,
                environment=env or {}
            )
            output = self.client.api.exec_start(exec_id)
            exit_code = self.client.api.exec_inspect(exec_id)["ExitCode"]
            
            # 解码输出
            result = output.decode("utf-8", errors="replace")
            
            if exit_code != 0:
                logger.warning(f"命令执行返回非零退出码: {exit_code}")
                
            return result
            
        return await loop.run_in_executor(None, _exec)
    
    async def read_file(self, path: str) -> str:
        """读取沙箱中的文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile() as temp:
                temp_path = temp.name
                
                # 从容器复制文件到临时文件
                bits, stat = self.container.get_archive(path)
                with open(temp_path, 'wb') as f:
                    for chunk in bits:
                        f.write(chunk)
                        
                # 解压缩tar文件并读取内容
                extract_dir = tempfile.mkdtemp()
                try:
                    import tarfile
                    with tarfile.open(temp_path) as tar:
                        tar.extractall(path=extract_dir)
                        
                    # 获取文件名（不包含路径）
                    filename = os.path.basename(path)
                    extracted_path = os.path.join(extract_dir, filename)
                    
                    # 读取文件内容
                    with open(extracted_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    return content
                finally:
                    # 清理临时目录
                    import shutil
                    shutil.rmtree(extract_dir)
        except Exception as e:
            logger.error(f"读取文件失败 {path}: {str(e)}")
            raise SandboxFileError(f"读取文件失败: {str(e)}")
    
    async def write_file(self, path: str, content: str) -> bool:
        """写入内容到沙箱中的文件
        
        Args:
            path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                temp_path = temp.name
                temp.write(content)
                
            try:
                # 确保目标目录存在
                directory = os.path.dirname(path)
                if directory:
                    await self.run_command(f"mkdir -p {directory}")
                    
                # 从临时文件复制到容器
                with open(temp_path, 'rb') as f:
                    self.container.put_archive(
                        os.path.dirname(path) or "/",
                        docker.utils.tar(os.path.basename(path), f.read())
                    )
                    
                return True
            finally:
                # 删除临时文件
                os.unlink(temp_path)
        except Exception as e:
            logger.error(f"写入文件失败 {path}: {str(e)}")
            raise SandboxFileError(f"写入文件失败: {str(e)}")
    
    async def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """列出沙箱中的目录内容
        
        Args:
            path: 目录路径
            
        Returns:
            目录内容列表
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            # 执行ls命令获取目录内容
            result = await self.run_command(f"ls -la {path}")
            
            # 解析ls命令输出
            entries = []
            lines = result.strip().split("\n")
            
            # 跳过第一行（总计行）
            for line in lines[1:]:
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    permissions = parts[0]
                    size = parts[4]
                    date = f"{parts[5]} {parts[6]} {parts[7]}"
                    name = parts[8]
                    
                    is_dir = permissions.startswith("d")
                    
                    entries.append({
                        "name": name,
                        "is_directory": is_dir,
                        "size": size,
                        "date": date,
                        "permissions": permissions
                    })
                    
            return entries
        except Exception as e:
            logger.error(f"列出目录失败 {path}: {str(e)}")
            raise SandboxFileError(f"列出目录失败: {str(e)}")
    
    async def file_exists(self, path: str) -> bool:
        """检查沙箱中的文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            文件是否存在
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            result = await self.run_command(f"[ -e {path} ] && echo 'exists' || echo 'not exists'")
            return "exists" in result
        except Exception as e:
            logger.error(f"检查文件是否存在失败 {path}: {str(e)}")
            raise SandboxFileError(f"检查文件是否存在失败: {str(e)}")
    
    async def create_terminal(self) -> DockerTerminal:
        """创建交互式终端
        
        Returns:
            DockerTerminal对象
        """
        if not self._initialized or not self.container:
            raise SandboxError("沙箱未初始化")
            
        try:
            terminal = DockerTerminal(self.container, self.workspace)
            await terminal.initialize()
            return terminal
        except Exception as e:
            logger.error(f"创建终端失败: {str(e)}")
            raise SandboxError(f"创建终端失败: {str(e)}")
    
    async def cleanup(self) -> None:
        """清理沙箱资源"""
        if not self._initialized:
            return
            
        try:
            if self.container:
                self.container.stop()
                logger.info(f"已停止容器: {self.container.id}")
                self.container = None
                
            self._initialized = False
        except Exception as e:
            logger.error(f"清理沙箱资源失败: {str(e)}")
            # 即使清理失败也不抛出异常，以免影响其他清理操作 