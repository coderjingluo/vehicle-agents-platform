"""
KunlunSec AI Platform - 沙箱异常

定义沙箱相关的异常类。
"""


class SandboxError(Exception):
    """沙箱操作通用异常"""
    pass


class SandboxInitError(SandboxError):
    """沙箱初始化错误"""
    pass


class SandboxCommandError(SandboxError):
    """沙箱命令执行错误"""
    pass


class SandboxFileError(SandboxError):
    """沙箱文件操作错误"""
    pass


class SandboxTerminalError(SandboxError):
    """沙箱终端操作错误"""
    pass 