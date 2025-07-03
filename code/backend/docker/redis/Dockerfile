FROM redis:7-alpine

LABEL maintainer="KunlunSec AI Platform <admin@kunlunsec.com>"

# 复制Redis配置文件
COPY redis.conf /usr/local/etc/redis/redis.conf

# 创建数据目录
RUN mkdir -p /data && \
    chown redis:redis /data

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD redis-cli ping || exit 1

# 暴露端口
EXPOSE 6379

# 设置启动命令
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"] 