# KunlunSec AI Platform - 后端服务Docker配置

本目录包含了KunlunSec AI平台后端服务所需的所有Docker配置文件。

## 目录结构

```
docker/
├── chroma/                   # Chroma向量数据库配置
│   ├── Dockerfile
│   └── chroma_auth.txt       # Chroma认证配置
├── nginx/                    # Nginx反向代理配置
│   ├── Dockerfile
│   ├── conf.d/               # Nginx站点配置
│   │   ├── backend.conf      # 后端API代理配置
│   │   └── frontend.conf     # 前端代理配置
│   ├── nginx.conf            # Nginx主配置
│   └── ssl/                  # SSL证书目录
├── postgres/                 # PostgreSQL数据库配置
│   ├── Dockerfile
│   ├── init.sql              # 数据库初始化脚本
│   ├── pg_hba.conf           # 访问控制配置 
│   └── postgresql.conf       # PostgreSQL主配置
└── redis/                    # Redis缓存配置
    ├── Dockerfile
    └── redis.conf            # Redis配置文件
```

## 依赖服务

平台依赖以下服务：

1. **PostgreSQL**: 主数据库，用于存储结构化数据
2. **Redis**: 缓存和消息队列
3. **Chroma**: 向量数据库，用于知识库语义搜索
4. **Nginx**: 反向代理和负载均衡

## 快速开始

### 使用Docker Compose启动所有依赖服务

```bash
cd code/backend
docker-compose -f docker-compose.services.yml up -d
```

### 独立启动特定服务

```bash
# 仅启动数据库服务
docker-compose -f docker-compose.services.yml up -d postgres

# 仅启动Redis
docker-compose -f docker-compose.services.yml up -d redis

# 仅启动Chroma
docker-compose -f docker-compose.services.yml up -d chroma
```

## 管理和监控

平台包含以下管理工具：

1. **PGAdmin**: PostgreSQL管理工具，访问 http://localhost:5050
2. **Redis Commander**: Redis管理界面，访问 http://localhost:8081
3. **Prometheus**: 监控服务，访问 http://localhost:9090
4. **Grafana**: 可视化监控面板，访问 http://localhost:3000

## 数据持久化

所有服务的数据通过Docker卷进行持久化：

- postgres_data: PostgreSQL数据
- redis_data: Redis数据
- chroma_data: Chroma向量数据库
- pgadmin_data: PGAdmin配置
- prometheus_data: Prometheus监控数据
- grafana_data: Grafana配置和面板

## 网络配置

所有服务连接到名为`tara_network`的Docker网络，子网段为`172.20.0.0/16`。