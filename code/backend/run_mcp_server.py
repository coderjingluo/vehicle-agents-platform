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
        choices=["stdio"],
        default="stdio",
        help="通信方式: stdio (默认: stdio)",
    )
    args = parser.parse_args()

    # 创建并运行MCP服务器
    server = MCPServer()
    server.run(transport=args.transport) 