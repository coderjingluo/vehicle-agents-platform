#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动KunlunSec MCP服务器
"""

import argparse
from app.mcp.server import MCPServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KunlunSec MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse"],
        default="sse",
        help="通信方式: sse (默认: sse)",
    )
    args = parser.parse_args()

    # 创建并运行MCP服务器
    server = MCPServer()
    server.run(transport=args.transport) 