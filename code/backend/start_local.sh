#!/bin/bash

# KunlunSec AI Platform - 本地开发启动脚本

echo "正在启动本地PostgreSQL数据库..."
if ! docker ps | grep -q postgres; then
    docker run -d --name kunlunsec-postgres \
        -e POSTGRES_USER=admin \
        -e POSTGRES_PASSWORD=admin123 \
        -e POSTGRES_DB=automotive_security \
        -p 5432:5432 \
        postgres:15
fi

echo "正在启动本地Redis服务..."
if ! docker ps | grep -q redis; then
    docker run -d --name kunlunsec-redis \
        -p 6379:6379 \
        redis:7
fi

echo "正在启动本地Chroma向量数据库..."
if ! docker ps | grep -q chroma; then
    docker run -d --name kunlunsec-chroma \
        -p 8100:8000 \
        chromadb/chroma:0.4.14
fi

echo "等待服务启动..."
sleep 3

echo "启动后端服务..."
cd $(dirname "$0")
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug