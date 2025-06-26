# 前端Dockerfile - 车联网安全测试生命周期管理平台
# 多阶段构建：构建阶段 + 运行阶段

# ============ 构建阶段 ============
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 配置npm国内镜像源（淘宝镜像）
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set cache /tmp/.npm

# 复制package文件
COPY package*.json ./

# 安装依赖 (修复构建错误)
RUN npm install --production=false --silent

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# ============ 运行阶段 ============
FROM nginx:alpine

# 设置时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 