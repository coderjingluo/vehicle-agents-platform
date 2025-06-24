# 车联网安全测试生命周期管理平台

## 项目简介

这是一个基于多智能体协作的车联网安全测试生命周期管理平台，覆盖从TARA分析、测试用例生成、自动化测试执行到报告分析的完整闭环，并通过知识库自学习实现持续改进。

## 核心功能

### 🤖 专业化智能体
- **TARA智能体**: 威胁分析与风险评估，法规合规咨询
- **测试用例智能体**: 基于TARA结果自动生成测试用例
- **自动化测试智能体**: 测试插件生成和自动化执行
- **报告分析智能体**: 智能分析和修复建议

### 🧠 智能体通用能力
- 基于大模型的任务分解和计划生成
- 智能工具选择和执行调度
- 结果聚合和分析
- 实时状态监控

### 📚 知识库自学习
- 测试项目自动归档
- 知识提取和持续学习
- 智能推荐和应用

## 技术架构

### 后端技术栈
- **FastAPI**: 高性能异步Web框架
- **SQLAlchemy**: 强大的ORM支持
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话管理
- **Chroma**: 向量数据库
- **LangChain**: AI应用框架

### 前端技术栈
- **Vue.js 3**: 现代化前端框架
- **TypeScript**: 类型安全
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **Vite**: 构建工具

## 快速开始

### 开发环境要求
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 启动开发环境

1. 启动数据库服务
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. 后端服务启动
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. 前端服务启动
```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
automotive-security-testing-platform/
├── backend/                   # FastAPI后端应用
│   ├── app/
│   │   ├── agents/           # 智能体模块
│   │   ├── api/              # API路由
│   │   ├── core/             # 核心业务逻辑
│   │   ├── models/           # 数据模型
│   │   └── services/         # 业务服务
│   ├── alembic/              # 数据库迁移
│   └── requirements.txt
├── frontend/                  # Vue.js前端应用
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── views/            # 页面视图
│   │   ├── stores/           # 状态管理
│   │   └── utils/            # 工具函数
│   └── package.json
├── docs/                      # 项目文档
├── tests/                     # 测试文件
└── docker-compose.yml
```

## 开发规范

### 代码质量
- 后端：100%类型注解，90%+测试覆盖率
- 前端：TypeScript严格模式，80%+组件测试覆盖率
- 统一的代码格式化和lint检查

### Git工作流
- 基于feature分支的开发流程
- 严格的代码review
- 自动化CI/CD检查

## License

MIT License 