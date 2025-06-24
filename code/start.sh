#!/bin/bash

# 车联网安全测试生命周期管理平台 - Docker启动脚本
# 使用方法: ./start.sh [dev|prod|stop|restart|logs]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="vehicle_security_platform"
COMPOSE_PROJECT_NAME="vehicle_security"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker和Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p {logs,backup,config,uploads}
    mkdir -p logs/{nginx,backend}
    mkdir -p config/{ssl,grafana/provisioning}
    
    log_success "目录创建完成"
}

# 设置权限
set_permissions() {
    log_info "设置文件权限..."
    
    # 设置脚本执行权限
    chmod +x start.sh
    
    # 设置日志目录权限
    chmod -R 755 logs
    
    log_success "权限设置完成"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f .env ]; then
        log_warning ".env 文件不存在，正在创建示例文件..."
        
        cat > .env << EOF
# 车联网安全测试生命周期管理平台 - 环境配置
APP_NAME=车联网安全测试生命周期管理平台
SECRET_KEY=your-super-secret-key-$(openssl rand -hex 16)
DEBUG=false

# 数据库配置
POSTGRES_PASSWORD=admin123
REDIS_PASSWORD=admin123

# LLM API密钥 (请配置你的API密钥)
OPENAI_API_KEY=your-openai-api-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# 监控配置
GRAFANA_ADMIN_PASSWORD=admin123
EOF
        
        log_warning "请编辑 .env 文件并配置必要的API密钥"
    fi
}

# 初始化配置文件
init_config() {
    log_info "初始化配置文件..."
    
    # 创建 Chroma 认证文件
    if [ ! -f config/chroma_auth.txt ]; then
        echo "admin:admin123" > config/chroma_auth.txt
    fi
    
    # 创建 Redis 配置
    if [ ! -f config/redis.conf ]; then
        cat > config/redis.conf << EOF
# Redis配置
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
    fi
    
    # 创建 Prometheus 配置
    if [ ! -f config/prometheus.yml ]; then
        cat > config/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
      
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF
    fi
    
    log_success "配置文件初始化完成"
}

# 开发环境启动
start_dev() {
    log_info "启动开发环境..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    docker-compose -f docker-compose.dev.yml up -d
    
    log_success "开发环境启动完成"
    log_info "服务访问地址:"
    log_info "  - 后端API: http://localhost:8000"
    log_info "  - 前端界面: http://localhost:3000"
    log_info "  - 数据库管理: http://localhost:5050"
    log_info "  - Redis管理: http://localhost:8081"
    log_info "  - Chroma数据库: http://localhost:8001"
}

# 生产环境启动
start_prod() {
    log_info "启动生产环境..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
    
    log_success "生产环境启动完成"
    log_info "服务访问地址:"
    log_info "  - 应用首页: http://localhost"
    log_info "  - API文档: http://localhost/api/docs"
    log_info "  - 数据库管理: http://localhost:5050"
    log_info "  - 监控面板: http://localhost:3000"
    log_info "  - Prometheus: http://localhost:9090"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
    
    log_success "所有服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    stop_services
    sleep 2
    
    if [ "$1" == "dev" ]; then
        start_dev
    else
        start_prod
    fi
}

# 查看日志
show_logs() {
    log_info "显示服务日志..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    
    if [ -n "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    docker-compose -f docker-compose.yml build --no-cache
    
    log_success "镜像构建完成"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
    docker-compose down -v --remove-orphans
    docker system prune -f
    
    log_success "清理完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查后端服务
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "后端服务运行正常"
    else
        log_error "后端服务异常"
    fi
    
    # 检查前端服务
    if curl -s http://localhost/ > /dev/null; then
        log_success "前端服务运行正常"
    else
        log_error "前端服务异常"
    fi
    
    # 检查数据库
    if docker exec tara_postgres pg_isready -U admin > /dev/null 2>&1; then
        log_success "数据库运行正常"
    else
        log_error "数据库异常"
    fi
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据库
    docker exec tara_postgres pg_dump -U admin automotive_security > "$BACKUP_DIR/database.sql"
    
    # 备份上传文件
    cp -r uploads "$BACKUP_DIR/" 2>/dev/null || true
    
    log_success "数据备份完成: $BACKUP_DIR"
}

# 主函数
main() {
    case "${1:-help}" in
        "dev")
            check_dependencies
            create_directories
            set_permissions
            check_env_file
            init_config
            start_dev
            ;;
        "prod")
            check_dependencies
            create_directories
            set_permissions
            check_env_file
            init_config
            start_prod
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services "${2:-prod}"
            ;;
        "logs")
            show_logs "$2"
            ;;
        "build")
            build_images
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            health_check
            ;;
        "backup")
            backup_data
            ;;
        "help"|*)
            echo "车联网安全测试生命周期管理平台 - Docker管理脚本"
            echo ""
            echo "使用方法: $0 [命令] [参数]"
            echo ""
            echo "命令:"
            echo "  dev         启动开发环境"
            echo "  prod        启动生产环境"
            echo "  stop        停止所有服务"
            echo "  restart     重启服务 [dev|prod]"
            echo "  logs        查看日志 [服务名]"
            echo "  build       构建Docker镜像"
            echo "  cleanup     清理Docker资源"
            echo "  health      健康检查"
            echo "  backup      备份数据"
            echo "  help        显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 dev              # 启动开发环境"
            echo "  $0 prod             # 启动生产环境"
            echo "  $0 logs backend     # 查看后端日志"
            echo "  $0 restart dev      # 重启开发环境"
            ;;
    esac
}

# 执行主函数
main "$@" 