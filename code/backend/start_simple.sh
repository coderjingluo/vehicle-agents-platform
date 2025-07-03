#!/bin/bash

# KunlunSec AI Platform - 简单启动脚本
# 只启动 FastAPI 应用程序，不启动其他服务

echo "启动后端服务..."
cd $(dirname "$0")
python -m app.main 