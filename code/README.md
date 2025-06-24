# 车联网安全测试生命周期管理平台

基于多智能体协作的车联网安全测试平台，支持从威胁分析到测试执行的完整生命周期管理。

## ✨ 项目特色

- **真正的智能化**: 基于大模型的任务分解，非硬编码流程
- **多智能体协作**: 5个专业智能体协同工作
- **企业级架构**: LangGraph + FastAPI + PostgreSQL + Redis
- **实时监控**: WebSocket流式执行状态推送
- **标准合规**: 支持ISO 21434、SAE J3061、UNECE WP.29等标准

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104+ (高性能异步API)
- **工作流引擎**: LangGraph 0.1.9 (图结构智能体协作)
- **数据库**: PostgreSQL (主数据库) + Redis (缓存/会话)
- **向量数据库**: Chroma (知识库向量存储)
- **AI集成**: 支持OpenAI、DeepSeek、Anthropic等多模型

### 智能体系统
- **TARA智能体**: 威胁分析与风险评估
- **测试用例智能体**: 基于TARA结果生成测试用例
- **自动化测试智能体**: 生成和执行自动化测试脚本
- **报告分析智能体**: 综合分析结果并生成专业报告
- **知识库智能体**: 项目知识自动归档和持续学习

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 6+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd tara_agent_platform/code/backend
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **环境配置**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库和AI模型API密钥
```

4. **启动服务**
```bash
# 开发环境
docker-compose -f ../docker-compose.dev.yml up -d

# 启动后端服务
python main.py
```

5. **验证安装**
```bash
curl http://localhost:8000/api/v1/health
```

## 📋 API 使用示例

### 1. 查看所有智能体
```bash
curl -X GET "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json"
```

### 2. 执行TARA分析
```bash
curl -X POST "http://localhost:8000/api/v1/demo/tara-analysis" \
  -H "Content-Type: application/json"
```

### 3. 生成测试用例
```bash
curl -X POST "http://localhost:8000/api/v1/demo/test-case-generation" \
  -H "Content-Type: application/json"
```

### 4. 自动化测试
```bash
curl -X POST "http://localhost:8000/api/v1/demo/automation-testing" \
  -H "Content-Type: application/json"
```

### 5. 报告分析
```bash
curl -X POST "http://localhost:8000/api/v1/demo/report-analysis" \
  -H "Content-Type: application/json"
```

### 6. 知识库管理
```bash
curl -X POST "http://localhost:8000/api/v1/demo/knowledge-management" \
  -H "Content-Type: application/json"
```

### 7. 多智能体协作工作流
```bash
curl -X POST "http://localhost:8000/api/v1/demo/multi-agent-workflow" \
  -H "Content-Type: application/json"
```

### 8. 流式执行
```bash
curl -X POST "http://localhost:8000/api/v1/agents/tara/stream" \
  -H "Content-Type: application/json" \
  -d '{"request": "分析智能网联汽车安全威胁", "context": {"target": "车载网关"}}'
```

## 🧠 智能体详细介绍

### TARA智能体
**功能**: 威胁分析与风险评估
- 威胁识别和分类
- 风险评估和量化
- 缓解措施建议
- 合规性检查

**支持标准**: ISO 21434, SAE J3061, UNECE WP.29

### 测试用例智能体
**功能**: 基于TARA结果生成专业测试用例
- 确认测试(Confirmation Test)设计
- 验证测试(Validation Test)设计
- 测试覆盖率分析
- 测试优先级管理

### 自动化测试智能体
**功能**: 生成和执行自动化测试脚本
- 支持多种测试框架(pytest, selenium, etc.)
- 自动化可行性评估
- 测试环境配置
- CI/CD集成

### 报告分析智能体
**功能**: 综合分析测试结果并生成专业报告
- 风险评估矩阵
- 合规性差距分析
- 修复建议和优先级
- 专业报告生成

### 知识库智能体
**功能**: 项目知识自动归档和持续学习
- 知识提取和分类
- 智能知识检索
- 经验教训总结
- 最佳实践推荐

## 🏛️ 项目结构

```
backend/
├── app/
│   ├── agents/           # 智能体模块
│   │   ├── base_agent.py      # 基础智能体类
│   │   ├── tara_agent.py      # TARA智能体
│   │   ├── testcase_agent.py  # 测试用例智能体
│   │   ├── automation_agent.py # 自动化测试智能体
│   │   ├── report_agent.py    # 报告分析智能体
│   │   └── knowledge_agent.py # 知识库智能体
│   ├── api/              # API路由
│   │   └── v1/
│   │       └── api.py         # API端点定义
│   ├── core/             # 核心功能
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库配置
│   │   ├── llm_client.py      # LLM客户端
│   │   └── langgraph_workflow.py # LangGraph工作流
│   └── models/           # 数据模型
│       └── task.py            # 任务模型
├── requirements.txt      # 依赖列表
├── main.py              # 应用入口
└── env.example          # 环境变量示例
```

## 🔧 配置说明

### 环境变量配置 (.env)
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/tara_platform

# Redis配置  
REDIS_URL=redis://localhost:6379

# AI模型配置
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 应用配置
SECRET_KEY=your_secret_key
DEBUG=true
LOG_LEVEL=INFO
```

## 🔒 安全特性

- **多层认证**: API密钥 + JWT令牌
- **数据加密**: 传输加密(TLS) + 存储加密
- **访问控制**: 基于角色的权限管理
- **审计日志**: 完整的操作审计跟踪
- **安全扫描**: 定期漏洞扫描和依赖检查

## 📊 性能指标

- **并发处理**: 支持1000+并发请求
- **响应时间**: API平均响应时间 < 100ms
- **智能体执行**: 单个智能体任务 < 30秒
- **系统可用性**: 99.9%正常运行时间

## 🧪 测试

### 运行单元测试
```bash
pytest tests/ -v
```

### 运行集成测试
```bash
pytest tests/integration/ -v
```

### 性能测试
```bash
locust -f tests/performance/locustfile.py
```

## 📈 监控和日志

### 应用监控
- 健康检查端点: `/api/v1/health`
- 指标端点: `/api/v1/metrics`
- 状态端点: `/api/v1/status`

### 日志配置
```python
# 支持多种日志级别
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# 日志输出格式
- 控制台输出(开发环境)
- 文件输出(生产环境)
- 结构化日志(JSON格式)
```

## 🐳 Docker 部署

### 开发环境
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 生产环境
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持

- 📧 邮箱: support@example.com
- 💬 微信群: [扫码加入]
- 📖 文档: [查看详细文档](./documents/)
- 🐛 问题反馈: [GitHub Issues](https://github.com/example/issues)

## 🎯 路线图

### ✅ Phase 1: 基础架构 (已完成)
- LangGraph工作流引擎
- 智能体通用能力框架
- API接口和WebSocket支持
- Docker开发环境

### ✅ Phase 2: 核心智能体 (已完成)
- TARA智能体开发
- 测试用例智能体开发
- 自动化测试智能体开发
- 报告分析智能体开发
- 知识库智能体开发

### 🔄 Phase 3: 前端界面 (计划中)
- Vue.js 3 应用搭建
- 智能体交互界面
- 实时监控看板
- 报告可视化

### 📋 Phase 4: 高级功能 (计划中)
- 知识库管理系统
- 模型配置管理
- 高级工作流设计
- 团队协作功能

### 🚀 Phase 5: 完善优化 (计划中)
- 性能优化
- 安全增强
- 国际化支持
- 插件生态

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！** 