# 车联网安全测试生命周期管理平台 - 技术架构详细说明

## 1. 整体架构概览

### 1.1 系统架构图
```
                    ┌─────────────────────────────────────┐
                    │          用户界面层                  │
                    │  ┌─────────────┐  ┌─────────────┐   │
                    │  │   Web UI    │  │ Mobile App  │   │
                    │  │  Vue.js 3   │  │   (Future)  │   │
                    │  └─────────────┘  └─────────────┘   │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │          API网关层                   │
                    │  ┌─────────────┐  ┌─────────────┐   │
                    │  │   Nginx     │  │  WebSocket  │   │
                    │  │ 负载均衡     │  │   Gateway   │   │
                    │  └─────────────┘  └─────────────┘   │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │         应用服务层                   │
                    │  ┌─────────────┐  ┌─────────────┐   │
                    │  │  FastAPI    │  │   Celery    │   │
                    │  │  Web API    │  │ 异步任务队列 │   │
                    │  └─────────────┘  └─────────────┘   │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │         多智能体协作层               │
                    │  ┌─────────────┐  ┌─────────────┐   │
                    │  │Multi-Agent  │  │Tool Registry│   │
                    │  │Collaboration│  │  工具注册表  │   │
                    │  │             │  │             │   │
                    │  │ ┌─────────┐ │  │ ┌─────────┐ │   │
                    │  │ │ 4 Agents│ │  │ │MCP Tools│ │   │
                    │  │ └─────────┘ │  │ └─────────┘ │   │
                    │  └─────────────┘  └─────────────┘   │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │         数据存储层                   │
                    │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                    │  │PostgreSQL│ │  Redis  │ │ Chroma │ │
                    │  │  主数据库 │ │  缓存   │ │向量数据库│ │
                    │  └─────────┘ └─────────┘ └────────┘ │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │         外部服务层                   │
                    │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                    │  │LLM APIs │ │MCP Tools│ │Monitor │ │
                    │  │OpenAI等 │ │外部工具 │ │ 监控   │ │
                    │  └─────────┘ └─────────┘ └────────┘ │
                    └─────────────────────────────────────┘
```

### 1.2 核心组件关系
```python
# 智能体架构 - 通用能力 + 专业化应用
FastAPI App
├── Agent Engine                      # 智能体引擎核心
│   ├── Task Decomposer              # 任务分解器（基于大模型生成计划）
│   ├── Step Executor                # 步骤执行器（工具调度管理）
│   ├── Result Aggregator            # 结果聚合器（智能结果整合）
│   ├── LLM Client                   # 大语言模型客户端
│   └── Agent Base Class             # 智能体基础类
├── Specialized Agents               # 专业化智能体（基于通用能力）
│   ├── TARA Agent                   # TARA分析智能体
│   ├── Test Case Agent              # 测试用例生成智能体  
│   ├── Automation Test Agent        # 自动化测试智能体
│   ├── Report Analysis Agent        # 报告分析智能体
│   └── Agent Coordinator           # 智能体协调器
├── Tool Registry                    # 工具注册表
│   ├── Built-in Tools              # 内置工具
│   ├── Testing Tools               # 测试工具
│   ├── MCP Connectors             # MCP连接器
│   └── Analysis Tools             # 分析工具
├── Knowledge Learning Engine        # 知识学习引擎
│   ├── Auto Archive System         # 自动归档系统
│   ├── Knowledge Extractor         # 知识提取器
│   ├── Vector Store                # 向量存储
│   └── Learning Optimizer          # 学习优化器
└── WebSocket Manager               # WebSocket管理器
    ├── Task Progress Monitor       # 任务进度监控
    ├── Agent Status Monitor        # 智能体状态监控
    ├── Real-time Notifier         # 实时通知器
    └── Collaboration Sync         # 协作同步器
```

## 2. 前端架构设计

### 2.1 Vue.js 3 应用架构
```javascript
// 前端架构层次
src/
├── main.js                 # 应用入口
├── App.vue                 # 根组件
├── components/             # 组件层
│   ├── layout/            # 布局组件
│   │   ├── AppHeader.vue
│   │   ├── AppSidebar.vue
│   │   └── AppMain.vue
│   ├── common/            # 通用组件
│   │   ├── BaseButton.vue
│   │   ├── BaseTable.vue
│   │   └── BaseModal.vue
│   └── business/          # 业务组件
│       ├── TaskCard.vue
│       ├── KnowledgeBaseTree.vue
│       └── ModelConfigForm.vue
├── views/                 # 页面视图
│   ├── Dashboard.vue
│   ├── TaskManagement.vue
│   ├── KnowledgeBase.vue
│   └── Settings.vue
├── stores/                # 状态管理 (Pinia)
│   ├── auth.js
│   ├── task.js
│   ├── knowledge.js
│   └── websocket.js
├── composables/           # 组合式函数
│   ├── useAPI.js
│   ├── useWebSocket.js
│   └── useAuth.js
├── router/                # 路由配置
│   └── index.js
├── utils/                 # 工具函数
│   ├── http.js
│   ├── websocket.js
│   └── helpers.js
└── types/                 # JavaScript类型
    ├── api.js
    ├── task.js
    └── user.js
```

### 2.2 状态管理设计
```typescript
// stores/auth.js - 认证状态管理
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: false,
  }),
  
  actions: {
    async login(credentials: LoginRequest) {
      const response = await authAPI.login(credentials)
      this.setAuth(response.data)
    },
    
    setAuth(authData: AuthResponse) {
      this.user = authData.user
      this.token = authData.token
      this.isAuthenticated = true
      localStorage.setItem('token', authData.token)
    },
    
    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    }
  }
})
```

### 2.3 组合式函数设计
```typescript
// composables/useWebSocket.js
import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useWebSocket(url: string) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const messages = ref<any[]>([])
  
  const connect = () => {
    socket.value = new WebSocket(url)
    
    socket.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }
    
    socket.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      messages.value.push(message)
      handleMessage(message)
    }
    
    socket.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
      // 重连逻辑
      setTimeout(connect, 3000)
    }
  }
  
  const send = (message: any) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(message))
    }
  }
  
  onMounted(connect)
  onUnmounted(() => {
    socket.value?.close()
  })
  
  return {
    isConnected: computed(() => isConnected.value),
    messages: computed(() => messages.value),
    send
  }
}
```

## 3. 后端架构设计

### 3.1 FastAPI应用结构
```python
# app/main.py - FastAPI应用入口
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, tasks, knowledge, models, tools
from app.core.config import settings
from app.core.websocket import websocket_manager

app = FastAPI(
    title="KunlunSec AI Platform",
    description="智能安全分析平台",
    version="1.0.0"
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])

# WebSocket路由
app.mount("/ws", websocket_manager.app)

@app.on_event("startup")
async def startup_event():
    await websocket_manager.startup()
    
@app.on_event("shutdown")
async def shutdown_event():
    await websocket_manager.shutdown()
```

### 3.2 数据模型设计
```python
# app/models/task.py - 任务数据模型
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=1)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    config = Column(JSON)
    results = Column(JSON)

class TaskExecution(Base):
    __tablename__ = "task_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), default="pending")
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    steps = Column(JSON)
    logs = Column(JSON)
```

### 3.3 业务服务层
```python
# app/services/task_service.py - 任务业务服务
from typing import List, Optional
from app.models.task import Task, TaskExecution
from app.core.agent_engine import AgentEngine
from app.core.database import get_db
from sqlalchemy.orm import Session

class TaskService:
    def __init__(self, db: Session, agent_engine: AgentEngine):
        self.db = db
        self.agent_engine = agent_engine
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """创建新任务"""
        task = Task(**task_data.dict())
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    async def execute_task(self, task_id: str, user_id: str) -> TaskExecution:
        """执行任务"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # 创建执行记录
        execution = TaskExecution(
            task_id=task_id,
            status="running"
        )
        self.db.add(execution)
        self.db.commit()
        
        # 使用智能代理执行任务
        try:
            result = await self.agent_engine.execute_task(task, user_id)
            execution.status = "completed"
            execution.results = result
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
        
        self.db.commit()
        return execution
    
    def get_tasks(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """获取任务列表"""
        return self.db.query(Task).filter(
            Task.created_by == user_id
        ).offset(skip).limit(limit).all()
```

## 4. 智能代理引擎架构

### 4.1 Agent Engine核心设计
```python
# app/core/agent_engine.py - 智能代理引擎
from typing import Dict, List, Any
from app.core.llm_client import LLMClient
from app.core.tool_registry import ToolRegistry
from app.models.task import Task

class AgentEngine:
    def __init__(self, llm_client: LLMClient, tool_registry: ToolRegistry):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.task_decomposer = TaskDecomposer(llm_client)
        self.step_executor = StepExecutor(tool_registry)
        self.result_aggregator = ResultAggregator(llm_client)
    
    async def execute_task(self, task: Task, user_id: str) -> Dict[str, Any]:
        """执行任务主流程"""
        # 1. 任务分解
        steps = await self.task_decomposer.decompose(task)
        
        # 2. 步骤执行
        step_results = []
        for step in steps:
            result = await self.step_executor.execute(step)
            step_results.append(result)
            
            # 实时更新进度
            await self.notify_progress(task.id, step, result)
        
        # 3. 结果聚合
        final_result = await self.result_aggregator.aggregate(step_results)
        
        return final_result

class TaskDecomposer:
    """任务分解器"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def decompose(self, task: Task) -> List[Step]:
        """将任务分解为可执行步骤"""
        prompt = self._build_decomposition_prompt(task)
        response = await self.llm_client.generate(prompt)
        return self._parse_steps(response)

class StepExecutor:
    """步骤执行器"""
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
    
    async def execute(self, step: Step) -> StepResult:
        """执行单个步骤"""
        tool = self.tool_registry.get_tool(step.tool_name)
        return await tool.execute(step.parameters)
```

### 4.2 工具注册表设计
```python
# app/core/tool_registry.py - 工具注册表
from typing import Dict, List, Protocol
from abc import ABC, abstractmethod

class Tool(Protocol):
    """工具接口"""
    name: str
    description: str
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """执行工具"""
        ...

class ToolRegistry:
    """工具注册表"""
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.mcp_connectors: Dict[str, MCPConnector] = {}
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Tool:
        """获取工具"""
        if name in self.tools:
            return self.tools[name]
        elif name in self.mcp_connectors:
            return self.mcp_connectors[name]
        else:
            raise ValueError(f"Tool {name} not found")
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys()) + list(self.mcp_connectors.keys())

# 内置工具示例
class KnowledgeSearchTool(Tool):
    name = "knowledge_search"
    description = "搜索知识库"
    
    def __init__(self, knowledge_service):
        self.knowledge_service = knowledge_service
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        query = parameters.get("query")
        kb_id = parameters.get("knowledge_base_id")
        return await self.knowledge_service.search(query, kb_id)
```

## 5. 数据存储架构

### 5.1 PostgreSQL数据库设计
```sql
-- 核心表结构设计
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
    status VARCHAR(20) DEFAULT 'pending',
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

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50),
    file_size BIGINT,
    chunk_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

-- 索引优化
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_documents_kb_id ON documents(kb_id);
CREATE INDEX idx_documents_processed ON documents(processed);
```

### 5.2 Redis缓存策略
```python
# app/core/cache.py - Redis缓存管理
import redis
import json
from typing import Any, Optional
from app.core.config import settings

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)
    
    # 缓存策略
    def task_cache_key(self, task_id: str) -> str:
        return f"task:{task_id}"
    
    def user_cache_key(self, user_id: str) -> str:
        return f"user:{user_id}"
    
    def search_cache_key(self, query: str, kb_id: str) -> str:
        return f"search:{kb_id}:{hash(query)}"
```

### 5.3 向量数据库集成
```python
# app/core/vector_store.py - 向量数据库管理
import chromadb
from typing import List, Dict, Any
from app.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
    
    def create_collection(self, name: str) -> None:
        """创建集合"""
        self.client.create_collection(name=name)
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict], ids: List[str]) -> None:
        """添加文档"""
        collection = self.client.get_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, collection_name: str, query: str, 
              n_results: int = 10) -> Dict[str, Any]:
        """搜索文档"""
        collection = self.client.get_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def delete_collection(self, name: str) -> None:
        """删除集合"""
        self.client.delete_collection(name=name)
```

## 6. 安全架构设计

### 6.1 认证授权机制
```python
# app/core/security.py - 安全认证
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """密码加密"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user
```

### 6.2 权限控制系统
```python
# app/core/permissions.py - 权限控制
from enum import Enum
from typing import List
from functools import wraps
from fastapi import HTTPException, status

class Permission(str, Enum):
    READ_TASKS = "read:tasks"
    WRITE_TASKS = "write:tasks"
    READ_KNOWLEDGE = "read:knowledge"
    WRITE_KNOWLEDGE = "write:knowledge"
    ADMIN = "admin"

class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ_TASKS, Permission.READ_KNOWLEDGE],
    Role.ANALYST: [
        Permission.READ_TASKS, Permission.WRITE_TASKS,
        Permission.READ_KNOWLEDGE, Permission.WRITE_KNOWLEDGE
    ],
    Role.ADMIN: [perm for perm in Permission]
}

def require_permission(permission: Permission):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## 7. 监控和日志架构

### 7.1 日志系统设计
```python
# app/core/logging.py - 日志配置
import logging
import sys
from datetime import datetime
from app.core.config import settings

# 日志格式配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}

def setup_logging():
    """设置日志配置"""
    logging.config.dictConfig(LOGGING_CONFIG)
```

### 7.2 性能监控
```python
# app/core/metrics.py - 性能指标收集
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 指标定义
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_active_connections', 'Active WebSocket connections')
TASK_EXECUTION_TIME = Histogram('task_execution_duration_seconds', 'Task execution time')

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
    return wrapper

class MetricsCollector:
    """指标收集器"""
    
    def record_request(self, method: str, endpoint: str):
        """记录请求"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    
    def record_websocket_connection(self, action: str):
        """记录WebSocket连接"""
        if action == "connect":
            ACTIVE_CONNECTIONS.inc()
        elif action == "disconnect":
            ACTIVE_CONNECTIONS.dec()
    
    def record_task_execution(self, duration: float):
        """记录任务执行时间"""
        TASK_EXECUTION_TIME.observe(duration)
```

---

此技术架构文档详细说明了KunlunSec AI Platform的各个技术层面，为开发团队提供了完整的技术实现指导。 