# 车联网安全测试生命周期管理平台 - Docker部署指南

## 📋 概述

本文档提供车联网安全测试生命周期管理平台的完整Docker化部署方案，包括开发环境和生产环境的部署配置。

## 🎯 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端服务 (Nginx)                         │
│  Vue.js 3 + Element Plus + 响应式设计                       │
│  端口: 80/443                                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   后端服务 (FastAPI)                        │
│  LangGraph + 5个智能体 + 多模型支持                         │
│  端口: 8000                                                 │
└─────────┬───────────┬───────────┬─────────────────────────────┘
          │           │           │
┌─────────┴───┐ ┌─────┴────┐ ┌────┴──────┐
│PostgreSQL 15│ │Redis 7   │ │ChromaDB   │
│端口: 5432   │ │端口: 6379│ │端口: 8001 │
└─────────────┘ └──────────┘ └───────────┘
```

## 🚀 快速启动

### 开发环境
```bash
# 克隆项目
git clone <repository-url>
cd tara_agent_platform/code

# 启动开发环境
./start.sh dev
```

### 生产环境
```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥

# 启动生产环境
./start.sh prod
```

## 📁 文件结构

```
code/
├── backend/
│   ├── Dockerfile              # 后端Docker文件
│   ├── requirements.txt        # Python依赖
│   └── app/                    # 应用代码
├── frontend/
│   ├── Dockerfile              # 前端Docker文件
│   ├── nginx.conf              # Nginx配置
│   └── src/                    # 前端代码
├── docker-compose.yml          # 生产环境配置
├── docker-compose.dev.yml      # 开发环境配置
├── docker-compose.override.yml # 生产环境优化
├── start.sh                    # 启动脚本
└── DOCKER_DEPLOYMENT.md        # 本文档
```

## 🔧 镜像加速配置

### 后端镜像 (Python)
```dockerfile
# 使用清华大学Debian镜像源
RUN sed -i 's@http://deb.debian.org/debian@https://mirrors.tuna.tsinghua.edu.cn/debian@g' /etc/apt/sources.list.d/debian.sources

# 使用阿里云pip镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com
```

### 前端镜像 (Node.js)
```dockerfile
# 使用淘宝npm镜像源
RUN npm config set registry https://registry.npmmirror.com && \
    pnpm config set registry https://registry.npmmirror.com
```

## 🛠️ 详细配置

### 环境变量配置 (.env)
```bash
# ============ 基本配置 ============
APP_NAME=车联网安全测试生命周期管理平台
SECRET_KEY=your-super-secret-key-here
DEBUG=false

# ============ 数据库配置 ============
DATABASE_URL=postgresql://admin:admin123@postgres:5432/automotive_security
REDIS_URL=redis://redis:6379
CHROMA_URL=http://chroma:8000

# ============ LLM API密钥 ============
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ============ 性能配置 ============
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=60
```

### 服务端口配置
| 服务 | 端口 | 说明 |
|-----|------|------|
| Frontend (Nginx) | 80/443 | 前端应用 |
| Backend (FastAPI) | 8000 | 后端API |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存/消息队列 |
| ChromaDB | 8001 | 向量数据库 |
| PGAdmin | 5050 | 数据库管理 |
| Redis Commander | 8081 | Redis管理 |
| Prometheus | 9090 | 监控系统 |
| Grafana | 3000 | 可视化监控 |

## 📊 监控和健康检查

### 健康检查配置
所有服务都配置了健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### 监控访问
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **系统监控**: http://localhost/api/metrics

## 🔒 安全配置

### 网络安全
- 使用自定义网络 `tara_network`
- 服务间通信使用内部网络
- 只暴露必要的端口

### 数据安全
- 数据持久化到Docker卷
- 数据库密码通过环境变量配置
- API密钥加密存储

### Nginx安全头
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## 📝 运维脚本

### 启动脚本命令
```bash
./start.sh dev          # 启动开发环境
./start.sh prod         # 启动生产环境
./start.sh stop         # 停止所有服务
./start.sh restart      # 重启服务
./start.sh logs         # 查看日志
./start.sh logs backend # 查看后端日志
./start.sh build        # 构建镜像
./start.sh cleanup      # 清理资源
./start.sh health       # 健康检查
./start.sh backup       # 备份数据
```

### 日志管理
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近100行日志
docker-compose logs --tail=100 backend
```

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs [service_name]

# 检查资源使用
docker stats
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker exec tara_postgres pg_isready -U admin

# 重启数据库服务
docker-compose restart postgres

# 查看数据库日志
docker-compose logs postgres
```

#### 3. API连接超时
```bash
# 检查后端服务状态
curl http://localhost:8000/health

# 检查网络连接
docker network ls
docker network inspect tara_tara_network
```

#### 4. 前端页面无法访问
```bash
# 检查Nginx配置
docker exec tara_frontend nginx -t

# 重启前端服务
docker-compose restart frontend

# 检查端口占用
netstat -tlnp | grep :80
```

### 性能优化

#### 1. 后端性能优化
```yaml
# 生产环境资源限制
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

#### 2. 数据库性能优化
```bash
# PostgreSQL配置优化
max_connections=200
shared_buffers=256MB
effective_cache_size=1GB
maintenance_work_mem=64MB
```

#### 3. Redis性能优化
```bash
# Redis内存优化
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
```

## 🚀 生产环境部署

### 1. 服务器要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 100GB以上SSD
- **操作系统**: Ubuntu 20.04+ / CentOS 8+

### 2. 部署步骤
```bash
# 1. 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. 克隆代码
git clone <repository-url>
cd tara_agent_platform/code

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件配置API密钥

# 4. 启动服务
./start.sh prod

# 5. 验证部署
./start.sh health
```

### 3. SSL证书配置
```bash
# 使用Let's Encrypt证书
certbot --nginx -d your-domain.com

# 手动配置证书
mkdir -p config/ssl
cp your-cert.pem config/ssl/cert.pem
cp your-key.key config/ssl/key.pem
```

### 4. 域名配置
修改 `frontend/nginx.conf` 中的 `server_name`：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
}
```

## 📈 监控告警

### Grafana仪表板
访问 http://localhost:3000，使用以下预配置仪表板：
- 系统资源监控
- 应用性能监控
- 数据库性能监控
- API请求监控

### Prometheus指标
访问 http://localhost:9090，查看以下关键指标：
- `backend_requests_total`: API请求总数
- `backend_request_duration`: 请求响应时间
- `postgres_up`: 数据库状态
- `redis_connected_clients`: Redis连接数

## 🔄 备份恢复

### 自动备份
```bash
# 设置定时备份 (每天凌晨2点)
0 2 * * * /path/to/start.sh backup
```

### 手动备份
```bash
# 创建备份
./start.sh backup

# 备份文件位置
ls -la backup/
```

### 数据恢复
```bash
# 恢复数据库
docker exec -i tara_postgres psql -U admin automotive_security < backup/20240101_020000/database.sql

# 恢复文件
cp -r backup/20240101_020000/uploads/* uploads/
```

## 📞 技术支持

### 日志位置
- **应用日志**: `logs/backend/app.log`
- **Nginx日志**: `logs/nginx/access.log`
- **错误日志**: `logs/nginx/error.log`

### 性能监控
- **系统指标**: http://localhost:9090
- **应用指标**: http://localhost:8000/metrics
- **健康检查**: http://localhost:8000/health

### 联系方式
如遇到问题，请通过以下方式联系技术支持：
- 🐛 **Bug报告**: 创建GitHub Issue
- 📧 **技术咨询**: support@automotive-security.com
- 📱 **紧急支持**: +86-xxx-xxxx-xxxx

---

🎉 **恭喜！车联网安全测试生命周期管理平台已成功部署！** 