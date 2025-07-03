FROM chromadb/chroma:latest

LABEL maintainer="KunlunSec AI Platform <admin@kunlunsec.com>"

# 环境变量设置
ENV CHROMA_SERVER_HOST=0.0.0.0 \
    CHROMA_SERVER_HTTP_PORT=8000 \
    PERSIST_DIRECTORY=/chroma/chroma \
    CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER=chromadb.auth.basic.BasicAuthCredentialsProvider \
    CHROMA_SERVER_AUTH_CREDENTIALS_FILE=/chroma/auth.txt

# 复制认证文件
COPY chroma_auth.txt /chroma/auth.txt

# 创建数据目录并设置权限
RUN mkdir -p /chroma/chroma && \
    chmod -R 755 /chroma

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/heartbeat || exit 1

# 暴露端口
EXPOSE 8000

# 修正启动命令
CMD ["uvicorn", "chromadb.app:app", "--host", "0.0.0.0", "--port", "8000"] 