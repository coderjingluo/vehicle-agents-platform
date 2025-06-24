# KunlunSec AI Platform - 详细设计规格说明

## 1. 项目概述

### 1.1 项目目标
构建一个类似KunlunSec AI Platform的车联网安全测试生命周期管理平台，通过多个专业AI智能体协作，覆盖从TARA（威胁分析与风险评估）分析、测试用例生成、自动化测试执行到报告分析的完整闭环，并通过知识库自学习实现持续改进。

### 1.2 核心价值主张
- **Full Lifecycle Coverage**: 覆盖车联网安全测试全生命周期
- **Multi-Agent Collaboration**: 多智能体协作的专业化测试
- **Regulatory Compliance**: 基于法规强标的专业咨询服务
- **Continuous Learning**: 知识库自学习和持续改进

### 1.3 目标用户
- 车联网安全工程师
- 安全测试工程师
- 合规审计人员
- 安全管理人员
- 车企技术团队

## 2. 功能架构设计

### 2.1 核心功能模块

#### 2.1.1 主控制台 (Dashboard)
```
功能描述：提供系统概览和快速访问入口
- 系统状态监控
- 智能体和任务执行状态概览
- 快速操作面板
- 通知中心
```

#### 2.1.2 智能任务管理 (Task Management)
```
功能描述：基于图片显示的智能任务执行界面
- 基于大模型的智能任务分解和计划生成（每个智能体通用的功能）
- 多步骤任务执行界面（类似图片中显示的步骤式执行，每个智能体通用的功能）
- 实时执行进度监控和状态跟踪（每个智能体通用的功能）
- 任务历史管理和模板系统（每个智能体通用的功能）
- 智能工具选择和调度（每个智能体通用的功能）
- 结果聚合和分析（每个智能体通用的功能）
```

#### 2.1.3 TARA智能体 (TARA Agent)
```
功能描述：威胁分析与风险评估的专业智能体
- 基于法规强标的TARA分析
- 导出目标和需求分析
- 为车企体系部分提供专业方案
- 威胁识别、漏洞分析、风险评估
- 缓解措施规划和合规检查
- 法规咨询和专业建议
```

#### 2.1.4 车辆测试用例智能体 (Test Case Agent)
```
功能描述：基于TARA分析结果生成测试用例的专业智能体
- 基于TARA分析结果自动生成测试用例
- 确认测试(Confirmation Test)方案生成
- 验证测试(Validation Test)方案生成
- 测试用例模板管理和优化
- 测试覆盖率分析
- 测试策略制定
```

#### 2.1.5 自动化测试智能体 (Automation Test Agent)
```
功能描述：基于测试方案执行自动化测试的专业智能体
- 基于测试方案自动生成测试插件
- 自动化测试脚本生成和执行
- 测试环境配置和管理
- 实时测试进度监控
- 测试结果收集和初步分析
- 测试异常处理和重试机制
```

#### 2.1.6 报告分析智能体 (Report Analysis Agent)
```
功能描述：基于测试结果生成分析报告的专业智能体
- 基于自动化测试结果生成综合分析报告
- 智能化问题识别和分类
- 修复建议和优化方案
- 风险评估矩阵生成
- 合规性检查结果
- 测试覆盖率和质量评价
```

#### 2.1.7 知识库自学习系统 (Knowledge Base)
```
功能描述：支持测试项目自动归档和知识提取的智能系统
- 测试项目结束后的自动归档
- 关键知识点提取和同步到知识库
- 多知识库管理（如图片中的default、ctf_notes、ctf等）
- 文档上传和管理
- 智能文档解析和分块
- 语义搜索功能
- 持续学习和知识优化
- 支持格式：.txt, .md, .pdf, .docx, .doc, .py, .js, .html, .css, .java, .cpp, .c
```

#### 2.1.8 模型管理 (Model Management)
```
功能描述：针对不同智能体的模型配置和管理
支持的模型：
- DeepSeek-chat (https://api.deepseek.com/v1)
- Anthropic/Claude 3.7 Sonnet
- 其他兼容OpenAI API的模型

功能特性：
- 针对不同智能体的模型配置和优化
- API密钥管理
- 模型性能监控
- 模型使用统计
- 智能体与模型的匹配策略
```

#### 2.1.5 MCP工具管理 (MCP Tools)
```
功能描述：基于图片中的MCP工具管理界面
内置工具：
- test1 (SSE, http://127.0.0.1:8074/sse)
- idapro (已连接, SSE, http://127.0.0.1:8074/sse)
- test-wincli (已连接, SSE, http://localhost:8081/sse)

功能特性：
- 工具连接状态监控
- 工具配置管理
- 自定义工具集成
- 工具使用统计
```

#### 2.1.6 工具配置中心 (Tools Configuration)
```
功能描述：基于图片中的Tools Configuration界面
可用工具类别：
- 系统工具：bash, file_operator
- AI工具：create_chat_completion
- 知识管理：knowledge_manager, rag_query
- 代码分析：code_audit_v2, str_replace_editor
- 规划工具：planning
- 浏览工具：browser_use
- 研究工具：deep_research, web_search
- MCP工具：mcp_17499480617332

功能特性：
- 工具启用/禁用管理
- 工具参数配置
- 工具权限控制
- 工具市场浏览
```

### 2.2 核心业务流程

#### 2.2.1 车联网安全测试生命周期流程
```
阶段1: TARA分析阶段 (TARA Agent)
├── 法规强标需求分析
├── 威胁识别和漏洞分析
├── 风险评估和缓解措施规划
├── 为车企体系部分提供专业方案
└── 输出TARA分析报告和目标需求

阶段2: 测试用例生成阶段 (Test Case Agent)
├── 接收TARA分析结果
├── 自动生成确认测试(Confirmation Test)方案
├── 自动生成验证测试(Validation Test)方案
├── 测试用例模板管理和优化
└── 输出完整测试用例库和测试矩阵

阶段3: 自动化测试执行阶段 (Automation Test Agent)
├── 解析测试方案和配置测试环境
├── 自动生成测试插件和脚本
├── 执行自动化测试并实时监控
├── 测试异常处理和重试机制
└── 收集测试结果和初步分析

阶段4: 报告分析和建议阶段 (Report Analysis Agent)
├── 处理自动化测试结果
├── 智能化问题识别和分类
├── 生成修复建议和优化方案
├── 输出风险评估矩阵和合规性检查
└── 生成综合分析报告

阶段5: 知识库自学习阶段 (Knowledge Base)
├── 测试项目结束后自动归档
├── 提取关键知识点同步到知识库
├── 更新测试模板和经验库
├── 持续学习和知识优化
└── 为下一次测试提供智能化支持
```

## 3. 技术架构设计

### 3.1 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端应用层     │    │    API网关层     │    │   业务服务层     │
│   Vue.js 3      │◄──►│   FastAPI       │◄──►│  Agent Engine   │
│   TypeScript    │    │   WebSocket     │    │  LLM Client     │
│   Composition   │    │   身份认证       │    │  Tool Registry  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据存储层     │    │   外部服务层     │    │   基础设施层     │
│  PostgreSQL     │◄──►│   LLM APIs      │◄──►│     Docker      │
│  Redis Cache    │    │   MCP Tools     │    │  Nginx/Traefik  │
│  Vector DB      │    │   WebHooks      │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2 前端技术栈
```
核心框架：
- Vue.js 3 + Composition API
- TypeScript
- Vite构建工具

UI组件库：
- Element Plus / Ant Design Vue
- Tailwind CSS
- Vue Router 4
- Pinia状态管理

实时通信：
- WebSocket客户端
- EventSource (SSE)
- Axios HTTP客户端
```

### 3.3 后端技术栈
```
Web框架：
- FastAPI (Python 3.9+)
- Pydantic数据验证
- SQLAlchemy ORM
- Alembic数据库迁移

异步处理：
- asyncio
- Celery任务队列
- Redis消息代理

AI集成：
- LangGraph框架
- OpenAI API兼容接口
- 向量数据库集成
```

### 3.4 数据存储设计
```
主数据库 (PostgreSQL)：
- 用户和权限管理
- 任务和计划存储
- 配置和设置
- 审计日志

缓存层 (Redis)：
- 会话管理
- 实时状态缓存
- 任务队列
- WebSocket连接管理

向量数据库 (Chroma/Qdrant)：
- 知识库文档存储
- 语义搜索索引
- 相似度匹配
```

## 4. 用户界面设计

### 4.1 主界面布局
```
基于图片中的KunlunSec界面设计：

头部导航栏：
- Logo和产品名称
- 用户头像和设置
- 快速访问按钮

侧边栏菜单：
- 工具 (Tools)
  - 知识库
  - MCP工具
- 任务管理
- 历史记录
- 系统设置

主内容区：
- 欢迎界面（三大核心能力展示）
- 任务执行界面
- 配置管理界面
```

### 4.2 关键页面设计

#### 4.2.1 任务管理页面
```
基于图片中的任务执行界面：

左侧：任务列表
- 任务历史记录
- 任务状态筛选
- 搜索和排序

右侧：任务详情
- 任务执行进度
- 实时日志输出
- 工具执行状态
- 结果预览
```

#### 4.2.2 知识库管理页面
```
基于图片中的Knowledge Base Manager：

左侧：知识库列表
- 知识库选择器
- 统计信息显示
- 创建新知识库

中间：功能选项卡
- Documents：文档管理
- Search：语义搜索
- Upload：文件上传

右侧：内容展示
- 文档列表和预览
- 搜索结果展示
- 上传进度和设置
```

#### 4.2.3 模型配置页面
```
基于图片中的Models配置界面：

配置选项：
- 模型选择下拉框
- API端点配置
- 认证信息设置
- 高级参数调整

模型列表：
- 已配置模型展示
- 连接状态指示
- 编辑和删除操作
```

## 5. 数据模型设计

### 5.1 核心实体模型

#### 5.1.1 用户管理
```python
class User(BaseModel):
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool = True

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
```

#### 5.1.2 任务管理
```python
class Task(BaseModel):
    id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    config: Dict[str, Any]
    results: Optional[Dict[str, Any]]

class TaskExecution(BaseModel):
    id: str
    task_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    steps: List[ExecutionStep]
    logs: List[ExecutionLog]
```

#### 5.1.3 知识库管理
```python
class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str

class Document(BaseModel):
    id: str
    kb_id: str
    filename: str
    content_type: str
    file_size: int
    chunk_count: int
    uploaded_at: datetime
    processed: bool = False
```

#### 5.1.4 模型配置
```python
class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    api_base: str
    api_key: str
    model_name: str
    parameters: Dict[str, Any]
    is_active: bool = True
```

#### 5.1.5 工具管理
```python
class Tool(BaseModel):
    id: str
    name: str
    description: str
    tool_type: ToolType
    config: Dict[str, Any]
    is_enabled: bool = True

class MCPConnection(BaseModel):
    id: str
    name: str
    protocol: str  # SSE, WebSocket
    endpoint: str
    status: ConnectionStatus
    last_heartbeat: Optional[datetime]
```

### 5.2 数据库表结构

#### 5.2.1 主要数据表
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    config JSONB,
    results JSONB
);

-- 知识库表
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,
    embedding_model VARCHAR(100)
);
```

## 6. API设计规范

### 6.1 RESTful API接口

#### 6.1.1 认证接口
```
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
GET  /api/auth/me
```

#### 6.1.2 任务管理接口
```
GET    /api/tasks              # 获取任务列表
POST   /api/tasks              # 创建新任务
GET    /api/tasks/{id}         # 获取任务详情
PUT    /api/tasks/{id}         # 更新任务
DELETE /api/tasks/{id}         # 删除任务
POST   /api/tasks/{id}/execute # 执行任务
POST   /api/tasks/{id}/pause   # 暂停任务
POST   /api/tasks/{id}/resume  # 恢复任务
POST   /api/tasks/{id}/cancel  # 取消任务
```

#### 6.1.3 知识库接口
```
GET    /api/knowledge-bases           # 获取知识库列表
POST   /api/knowledge-bases          # 创建知识库
GET    /api/knowledge-bases/{id}     # 获取知识库详情
DELETE /api/knowledge-bases/{id}     # 删除知识库
POST   /api/knowledge-bases/{id}/documents  # 上传文档
GET    /api/knowledge-bases/{id}/documents  # 获取文档列表
DELETE /api/knowledge-bases/{kb_id}/documents/{doc_id}  # 删除文档
POST   /api/knowledge-bases/{id}/search     # 搜索知识库
```

#### 6.1.4 模型管理接口
```
GET    /api/models     # 获取模型配置
POST   /api/models     # 添加模型配置
PUT    /api/models/{id}    # 更新模型配置
DELETE /api/models/{id}    # 删除模型配置
POST   /api/models/{id}/test   # 测试模型连接
```

#### 6.1.5 工具管理接口
```
GET    /api/tools         # 获取工具列表
POST   /api/tools         # 注册新工具
PUT    /api/tools/{id}    # 更新工具配置
DELETE /api/tools/{id}    # 删除工具
POST   /api/tools/{id}/test   # 测试工具连接

GET    /api/mcp/connections    # 获取MCP连接
POST   /api/mcp/connections   # 创建MCP连接
PUT    /api/mcp/connections/{id}  # 更新MCP连接
DELETE /api/mcp/connections/{id}  # 删除MCP连接
```

### 6.2 WebSocket事件定义

#### 6.2.1 任务执行事件
```javascript
// 客户端订阅任务执行状态
{
  "type": "subscribe",
  "channel": "task_execution",
  "task_id": "uuid"
}

// 服务端推送任务状态
{
  "type": "task_status_update",
  "task_id": "uuid",
  "status": "running",
  "progress": 45,
  "current_step": "威胁识别",
  "timestamp": "2024-01-01T12:00:00Z"
}

// 步骤完成事件
{
  "type": "step_completed",
  "task_id": "uuid",
  "step_id": "step_1",
  "step_name": "威胁识别",
  "result": {...},
  "duration": 120,
  "timestamp": "2024-01-01T12:02:00Z"
}
```

#### 6.2.2 系统通知事件
```javascript
// 系统通知
{
  "type": "notification",
  "level": "info|warning|error",
  "title": "通知标题",
  "message": "通知内容",
  "timestamp": "2024-01-01T12:00:00Z"
}

// MCP连接状态变化
{
  "type": "mcp_status_change",
  "connection_id": "uuid",
  "name": "idapro",
  "status": "connected|disconnected|error",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 7. 安全设计

### 7.1 身份认证和授权
```
认证机制：
- JWT Token认证
- Session管理
- 多因素认证（可选）

授权模型：
- 基于角色的访问控制(RBAC)
- 资源级权限控制
- API访问限制
```

### 7.2 数据安全
```
数据加密：
- 敏感数据字段加密
- 传输层TLS加密
- 密钥管理

访问控制：
- IP白名单
- API访问频率限制
- 审计日志记录
```

### 7.3 API安全
```
防护措施：
- 请求签名验证
- 防重放攻击
- 输入参数验证
- SQL注入防护
- XSS防护
```

## 8. 性能优化

### 8.1 前端优化
```
- 组件懒加载
- 路由级代码分割
- 静态资源CDN
- 虚拟滚动（大列表）
- 状态管理优化
```

### 8.2 后端优化
```
- 数据库连接池
- Redis缓存策略
- 异步任务处理
- API响应压缩
- 数据库查询优化
```

### 8.3 系统监控
```
监控指标：
- 系统资源使用率
- API响应时间
- 错误率统计
- 用户行为分析

告警机制：
- 阈值监控
- 邮件/短信通知
- 日志聚合分析
```

## 9. 部署方案

### 9.1 容器化部署
```
Docker服务：
- frontend: Vue.js应用
- backend: FastAPI应用
- database: PostgreSQL
- cache: Redis
- vector-db: Chroma
- nginx: 反向代理
- monitoring: Prometheus + Grafana
```

### 9.2 环境配置
```
开发环境：
- 本地Docker Compose
- 热重载开发
- 调试工具集成

生产环境：
- Kubernetes部署
- 高可用配置
- 自动扩缩容
- 滚动更新
```

## 10. 测试策略

### 10.1 前端测试
```
- 单元测试：Jest + Vue Test Utils
- 组件测试：Cypress Component Testing
- E2E测试：Cypress/Playwright
- 视觉回归测试
```

### 10.2 后端测试
```
- 单元测试：pytest
- 集成测试：数据库+API测试
- 性能测试：压力测试
- 安全测试：漏洞扫描
```

## 11. 开发计划

### 11.1 迭代规划

#### Phase 1: 基础框架 (2-3周)
- 项目脚手架搭建
- 基础认证系统
- 数据库设计和迁移
- 基础UI组件库

#### Phase 2: 核心功能 (4-5周)
- 任务管理系统
- 智能代理引擎
- WebSocket实时通信
- 基础工具集成

#### Phase 3: 高级功能 (3-4周)
- 知识库管理
- 模型配置管理
- MCP工具集成
- 高级搜索功能

#### Phase 4: 完善优化 (2-3周)
- 性能优化
- 安全强化
- 监控告警
- 文档完善

### 11.2 技术债务管理
```
代码质量：
- ESLint + Prettier
- 代码审查流程
- 技术文档维护
- 定期重构

依赖管理：
- 定期更新依赖
- 安全漏洞扫描
- 向后兼容性检查
```

## 12. 维护和扩展

### 12.1 可扩展性设计
```
架构扩展：
- 微服务架构迁移
- 插件化工具系统
- 多租户支持
- 国际化支持

功能扩展：
- 自定义工作流
- 第三方工具集成
- API开放平台
- 移动端适配
```

### 12.2 运维支持
```
日志管理：
- 结构化日志
- 日志聚合分析
- 分布式链路追踪

备份恢复：
- 数据库备份策略
- 灾难恢复预案
- 数据迁移工具
```

---

此设计规格说明将作为项目开发的指导文档，确保团队对系统架构、功能需求和技术实现有统一的理解。 