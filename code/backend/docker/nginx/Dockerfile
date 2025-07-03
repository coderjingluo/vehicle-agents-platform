FROM nginx:alpine

LABEL maintainer="KunlunSec AI Platform <admin@kunlunsec.com>"

# 删除默认的Nginx配置文件
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义的Nginx配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# 创建SSL证书目录
RUN mkdir -p /etc/nginx/ssl

# 复制SSL证书（如果有）
# COPY ssl/ /etc/nginx/ssl/

# 创建日志目录
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

# 暴露HTTP和HTTPS端口
EXPOSE 80 443

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"] 