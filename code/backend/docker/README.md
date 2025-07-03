# 后端依赖服务Docker配置

此目录包含了KunlunSec AI平台后端所依赖的各个服务的Docker配置。

## 服务目录

- **postgres**: PostgreSQL数据库服务配置
- **redis**: Redis缓存和消息队列服务配置
- **chroma**: Chroma向量数据库服务配置
- **nginx**: Nginx反向代理服务配置

## 服务配置说明

### PostgreSQL

PostgreSQL配置文件位于`postgres`目录：
- `Dockerfile`: 基于postgres:15的构建文件
- `postgresql.conf`: 数据库服务器主配置
- `pg_hba.conf`: 访问控制配置
- `init.sql`: 数据库初始化SQL脚本

### Redis

Redis配置文件位于`redis`目录：
- `Dockerfile`: 基于redis:7-alpine的构建文件
- `redis.conf`: Redis服务器配置文件

### Chroma

Chroma向量数据库配置文件位于`chroma`目录：
- `Dockerfile`: 基于chromadb/chroma的构建文件
- `chroma_auth.txt`: 认证配置文件

### Nginx

Nginx反向代理配置文件位于`nginx`目录：
- `Dockerfile`: 基于nginx:alpine的构建文件
- `nginx.conf`: Nginx主配置文件
- `conf.d/`: 包含站点配置文件
  - `backend.conf`: 后端API代理配置
  - `frontend.conf`: 前端应用代理配置
- `ssl/`: SSL证书目录（在生产环境中需要添加）

## 使用方法

所有这些服务通过`../docker-compose.services.yml`文件进行编排和管理。请参考根目录中的README文件了解如何启动这些服务。

## 服务定制

如果需要定制这些服务，可以修改相应的Dockerfile和配置文件。修改后需要重新构建Docker镜像：

```bash
# 例如重新构建PostgreSQL服务
docker-compose -f ../docker-compose.services.yml build postgres

# 重新构建所有服务
docker-compose -f ../docker-compose.services.yml build
```

## 注意事项

1. 在生产环境中，请确保修改所有默认密码和凭据
2. 对于PostgreSQL和Redis，建议根据实际硬件资源调整配置参数
3. 请确保数据卷正确配置，以防止数据丢失
4. 在Nginx配置中，请根据实际域名调整server_name 