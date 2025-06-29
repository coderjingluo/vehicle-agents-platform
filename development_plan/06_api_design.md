# API设计文档

## 1. API概述

KunlunSec AI平台的API设计遵循RESTful风格，提供了一套完整的接口，用于前端与后端的交互。同时，我们还提供WebSocket接口，用于实时状态更新和长连接通信。

### 1.1 设计原则

- **一致性**: 所有API遵循一致的命名和结构规范
- **版本控制**: 明确的API版本管理机制
- **安全性**: 完善的认证和授权机制
- **文档化**: 详细的API文档和示例
- **错误处理**: 标准化的错误响应格式

### 1.2 基本URL结构

```
https://api.kunlunsec.com/v1/{resource}
```

### 1.3 通用响应格式

**成功响应**:

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

**错误响应**:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      // 详细错误信息
    }
  }
}
```

### 1.4 状态码使用

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 客户端错误
- `401 Unauthorized`: 未认证
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突
- `500 Internal Server Error`: 服务器错误

## 2. 认证与授权API

### 2.1 用户认证

#### 登录

```
POST /v1/auth/login
```

**请求体**:

```json
{
  "username": "admin",
  "password": "password"
}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_id",
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin"
    }
  },
  "message": "登录成功"
}
```

#### 登出

```
POST /v1/auth/logout
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": null,
  "message": "登出成功"
}
```

#### 刷新令牌

```
POST /v1/auth/refresh
```

**请求体**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "message": "令牌刷新成功"
}
```

#### 获取当前用户信息

```
GET /v1/auth/me
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "user_id",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "last_login": "2023-04-01T12:00:00Z"
  },
  "message": "获取用户信息成功"
}
```

## 3. 任务管理API

### 3.1 任务操作

#### 创建任务

```
POST /v1/tasks
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**请求体**:

```json
{
  "title": "车联网系统安全评估",
  "description": "对XX车联网系统进行TARA分析和测试",
  "task_type": "tara",
  "priority": 1,
  "config": {
    "target_system": "车联网系统详细描述...",
    "regulations": ["ISO 21434", "GB/T 20984"]
  }
}
```

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "title": "车联网系统安全评估",
    "description": "对XX车联网系统进行TARA分析和测试",
    "task_type": "tara",
    "status": "pending",
    "priority": 1,
    "created_by": "user_id",
    "created_at": "2023-04-01T12:00:00Z",
    "updated_at": "2023-04-01T12:00:00Z",
    "config": {
      "target_system": "车联网系统详细描述...",
      "regulations": ["ISO 21434", "GB/T 20984"]
    }
  },
  "message": "任务创建成功"
}
```

#### 获取任务列表

```
GET /v1/tasks
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**查询参数**:

- `status`: 任务状态筛选 (可选)
- `task_type`: 任务类型筛选 (可选)
- `page`: 页码，默认1 (可选)
- `limit`: 每页数量，默认10 (可选)
- `sort`: 排序字段，默认created_at (可选)
- `order`: 排序方式，asc或desc，默认desc (可选)

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task_id1",
        "title": "车联网系统安全评估",
        "description": "对XX车联网系统进行TARA分析和测试",
        "task_type": "tara",
        "status": "running",
        "priority": 1,
        "created_by": "user_id",
        "created_at": "2023-04-01T12:00:00Z",
        "updated_at": "2023-04-01T12:10:00Z"
      },
      // 更多任务...
    ],
    "pagination": {
      "total": 42,
      "page": 1,
      "limit": 10,
      "pages": 5
    }
  },
  "message": "获取任务列表成功"
}
```

#### 获取任务详情

```
GET /v1/tasks/{id}
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "title": "车联网系统安全评估",
    "description": "对XX车联网系统进行TARA分析和测试",
    "task_type": "tara",
    "status": "running",
    "priority": 1,
    "created_by": "user_id",
    "created_at": "2023-04-01T12:00:00Z",
    "updated_at": "2023-04-01T12:10:00Z",
    "config": {
      "target_system": "车联网系统详细描述...",
      "regulations": ["ISO 21434", "GB/T 20984"]
    },
    "flow": {
      "id": "flow_id",
      "status": "running",
      "steps": [
        {
          "id": "planning",
          "name": "制定执行计划",
          "status": "completed",
          "output": {
            "plan": {
              "steps": [
                {
                  "id": "step1",
                  "name": "威胁识别",
                  "description": "识别系统中的潜在威胁",
                  "status": "running"
                },
                // 更多步骤...
              ]
            }
          }
        },
        // 更多流程步骤...
      ],
      "progress": {
        "total": 5,
        "completed": 1,
        "percentage": 20
      }
    },
    "results": null
  },
  "message": "获取任务详情成功"
}
```

#### 执行任务

```
POST /v1/tasks/{id}/execute
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "status": "running",
    "flow_id": "flow_id",
    "message": "任务已开始执行"
  },
  "message": "任务执行成功"
}
```

#### 暂停任务

```
POST /v1/tasks/{id}/pause
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "status": "paused",
    "message": "任务已暂停"
  },
  "message": "任务暂停成功"
}
```

#### 恢复任务

```
POST /v1/tasks/{id}/resume
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "status": "running",
    "message": "任务已恢复"
  },
  "message": "任务恢复成功"
}
```

#### 取消任务

```
POST /v1/tasks/{id}/cancel
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "task_id",
    "status": "cancelled",
    "message": "任务已取消"
  },
  "message": "任务取消成功"
}
```

## 4. 知识库API

### 4.1 知识库管理

#### 创建知识库

```
POST /v1/knowledge-bases
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**请求体**:

```json
{
  "name": "车联网安全知识库",
  "description": "车联网安全相关法规和标准",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "embedding_model": "text-embedding-ada-002"
}
```

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": "kb_id",
    "name": "车联网安全知识库",
    "description": "车联网安全相关法规和标准",
    "created_at": "2023-04-01T12:00:00Z",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "embedding_model": "text-embedding-ada-002",
    "document_count": 0
  },
  "message": "知识库创建成功"
}
```

#### 获取知识库列表

```
GET /v1/knowledge-bases
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "knowledge_bases": [
      {
        "id": "kb_id1",
        "name": "车联网安全知识库",
        "description": "车联网安全相关法规和标准",
        "created_at": "2023-04-01T12:00:00Z",
        "document_count": 5
      },
      {
        "id": "kb_id2",
        "name": "测试用例库",
        "description": "车联网安全测试用例集合",
        "created_at": "2023-04-02T10:00:00Z",
        "document_count": 12
      }
    ]
  },
  "message": "获取知识库列表成功"
}
```

#### 获取知识库详情

```
GET /v1/knowledge-bases/{id}
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "kb_id",
    "name": "车联网安全知识库",
    "description": "车联网安全相关法规和标准",
    "created_at": "2023-04-01T12:00:00Z",
    "last_updated": "2023-04-05T15:30:00Z",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "embedding_model": "text-embedding-ada-002",
    "document_count": 5,
    "total_chunks": 128,
    "documents": [
      {
        "id": "doc_id1",
        "filename": "ISO_21434.pdf",
        "file_format": "pdf",
        "file_size": 1048576,
        "uploaded_at": "2023-04-01T12:10:00Z",
        "status": "completed",
        "chunk_count": 35
      },
      // 更多文档...
    ]
  },
  "message": "获取知识库详情成功"
}
```

### 4.2 文档管理

#### 上传文档

```
POST /v1/knowledge-bases/{id}/documents
```

**请求头**:

```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求体**:

```
file: [binary data]
metadata: {"source": "标准组织", "version": "1.0"}
```

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": "doc_id",
    "filename": "ISO_21434.pdf",
    "kb_id": "kb_id",
    "file_format": "pdf",
    "file_size": 1048576,
    "uploaded_at": "2023-04-01T12:10:00Z",
    "status": "processing",
    "metadata": {
      "source": "标准组织",
      "version": "1.0"
    }
  },
  "message": "文档上传成功，正在处理"
}
```

#### 获取文档列表

```
GET /v1/knowledge-bases/{id}/documents
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**查询参数**:

- `status`: 文档状态筛选 (可选)
- `format`: 文件格式筛选 (可选)
- `page`: 页码，默认1 (可选)
- `limit`: 每页数量，默认10 (可选)

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "doc_id1",
        "filename": "ISO_21434.pdf",
        "file_format": "pdf",
        "file_size": 1048576,
        "uploaded_at": "2023-04-01T12:10:00Z",
        "status": "completed",
        "chunk_count": 35
      },
      // 更多文档...
    ],
    "pagination": {
      "total": 5,
      "page": 1,
      "limit": 10,
      "pages": 1
    }
  },
  "message": "获取文档列表成功"
}
```

#### 删除文档

```
DELETE /v1/knowledge-bases/{kb_id}/documents/{doc_id}
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": null,
  "message": "文档删除成功"
}
```

### 4.3 知识库搜索

#### 语义搜索

```
POST /v1/knowledge-bases/{id}/search
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**请求体**:

```json
{
  "query": "车联网系统中的威胁识别方法",
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "chunk_id1",
        "content": "威胁识别是车联网系统安全分析的关键步骤，包括资产识别、威胁场景分析和风险评估...",
        "document_id": "doc_id1",
        "document_name": "ISO_21434.pdf",
        "similarity": 0.92,
        "metadata": {
          "source": "标准组织",
          "section": "第4章 威胁分析方法"
        }
      },
      // 更多结果...
    ]
  },
  "message": "搜索成功"
}
```

## 5. MCP工具API

### 5.1 MCP连接管理

#### 创建MCP连接

```
POST /v1/mcp/connections
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**请求体**:

```json
{
  "name": "idapro",
  "type": "sse",
  "url": "http://127.0.0.1:8074/sse",
  "description": "IDA Pro工具连接"
}
```

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": "conn_id",
    "name": "idapro",
    "type": "sse",
    "url": "http://127.0.0.1:8074/sse",
    "description": "IDA Pro工具连接",
    "status": "connecting",
    "tools": []
  },
  "message": "MCP连接创建成功"
}
```

#### 获取MCP连接列表

```
GET /v1/mcp/connections
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "connections": [
      {
        "id": "conn_id1",
        "name": "idapro",
        "type": "sse",
        "url": "http://127.0.0.1:8074/sse",
        "description": "IDA Pro工具连接",
        "status": "connected",
        "last_heartbeat": "2023-04-01T12:15:30Z",
        "tool_count": 3
      },
      {
        "id": "conn_id2",
        "name": "test-wincli",
        "type": "sse",
        "url": "http://localhost:8081/sse",
        "description": "Windows客户端工具",
        "status": "connected",
        "last_heartbeat": "2023-04-01T12:15:28Z",
        "tool_count": 2
      }
    ]
  },
  "message": "获取MCP连接列表成功"
}
```

#### 获取MCP连接详情

```
GET /v1/mcp/connections/{id}
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "id": "conn_id",
    "name": "idapro",
    "type": "sse",
    "url": "http://127.0.0.1:8074/sse",
    "description": "IDA Pro工具连接",
    "status": "connected",
    "last_heartbeat": "2023-04-01T12:15:30Z",
    "tools": [
      {
        "name": "ida_analyze",
        "description": "执行IDA Pro静态分析",
        "parameters": {
          "type": "object",
          "properties": {
            "file_path": {
              "type": "string",
              "description": "要分析的文件路径"
            },
            "analysis_type": {
              "type": "string",
              "enum": ["basic", "advanced"],
              "description": "分析类型"
            }
          },
          "required": ["file_path"]
        }
      },
      // 更多工具...
    ]
  },
  "message": "获取MCP连接详情成功"
}
```

#### 删除MCP连接

```
DELETE /v1/mcp/connections/{id}
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": null,
  "message": "MCP连接删除成功"
}
```

## 6. 模型管理API

### 6.1 模型配置

#### 创建模型配置

```
POST /v1/models
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**请求体**:

```json
{
  "name": "DeepSeek-chat",
  "provider": "deepseek",
  "api_base": "https://api.deepseek.com/v1",
  "api_key": "sk-xxxxxxxxxxxx",
  "model_name": "deepseek-chat",
  "parameters": {
    "max_tokens": 4096,
    "temperature": 0.7
  }
}
```

**成功响应** (201 Created):

```json
{
  "success": true,
  "data": {
    "id": "model_id",
    "name": "DeepSeek-chat",
    "provider": "deepseek",
    "api_base": "https://api.deepseek.com/v1",
    "model_name": "deepseek-chat",
    "parameters": {
      "max_tokens": 4096,
      "temperature": 0.7
    },
    "is_active": true
  },
  "message": "模型配置创建成功"
}
```

#### 获取模型配置列表

```
GET /v1/models
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "model_id1",
        "name": "DeepSeek-chat",
        "provider": "deepseek",
        "api_base": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
        "is_active": true
      },
      {
        "id": "model_id2",
        "name": "Claude-3",
        "provider": "anthropic",
        "api_base": "https://api.anthropic.com/v1",
        "model_name": "claude-3-sonnet-20240229",
        "is_active": true
      }
    ]
  },
  "message": "获取模型配置列表成功"
}
```

#### 测试模型连接

```
POST /v1/models/{id}/test
```

**请求头**:

```
Authorization: Bearer {access_token}
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "data": {
    "status": "connected",
    "message": "模型连接测试成功",
    "latency": 280
  },
  "message": "模型连接测试成功"
}
```

## 7. WebSocket API

### 7.1 任务执行状态

```
WebSocket: /ws/task_execution/{task_id}
```

**认证**:

```
Query Parameter: token={access_token}
```

**客户端订阅**:

```json
{
  "type": "subscribe",
  "channel": "task_execution",
  "task_id": "task_id"
}
```

**服务端推送 - 任务状态更新**:

```json
{
  "type": "task_status_update",
  "task_id": "task_id",
  "status": "running",
  "progress": 45,
  "current_step": "威胁识别",
  "timestamp": "2023-04-01T12:05:30Z"
}
```

**服务端推送 - 步骤完成事件**:

```json
{
  "type": "step_completed",
  "task_id": "task_id",
  "step_id": "step1",
  "step_name": "威胁识别",
  "result": {
    "threats": [
      {
        "id": "T1",
        "name": "未授权访问",
        "description": "攻击者可能通过未授权方式访问车联网系统",
        "impact": "high"
      },
      // 更多威胁...
    ]
  },
  "duration": 120,
  "timestamp": "2023-04-01T12:07:30Z"
}
```

### 7.2 系统通知

```
WebSocket: /ws/notifications
```

**认证**:

```
Query Parameter: token={access_token}
```

**服务端推送 - 系统通知**:

```json
{
  "type": "notification",
  "level": "info",
  "title": "任务完成",
  "message": "车联网系统安全评估任务已完成",
  "timestamp": "2023-04-01T14:30:00Z"
}
```

**服务端推送 - MCP连接状态变化**:

```json
{
  "type": "mcp_status_change",
  "connection_id": "conn_id",
  "name": "idapro",
  "status": "connected",
  "timestamp": "2023-04-01T12:00:30Z"
}
``` 

## 7. MCP管理API

MCP（Model Context Protocol）管理API提供管理和访问外部工具服务器的接口。

### 7.1 MCP服务器管理

#### 7.1.1 获取所有MCP服务器

```
GET /api/v1/mcp/servers
```

**说明**：获取系统中所有已配置的MCP服务器

**响应**：

```json
{
  "status": "success",
  "data": {
    "servers": [
      {
        "id": "data_analysis_tools",
        "name": "数据分析工具集",
        "type": "sse",
        "url": "http://data-tools:8000/sse",
        "status": "connected",
        "connected_at": "2023-08-01T12:34:56.789Z",
        "tools_count": 12
      },
      {
        "id": "automotive_tools",
        "name": "车联网测试工具集",
        "type": "stdio",
        "command": "python run_automotive_tools.py",
        "status": "disconnected",
        "last_error": "连接超时"
      }
    ]
  }
}
```

#### 7.1.2 连接MCP服务器

```
POST /api/v1/mcp/servers/connect
```

**说明**：连接到指定的MCP服务器

**请求体**：

```json
{
  "server_id": "data_analysis_tools"
}
```

**响应**：

```json
{
  "status": "success",
  "data": {
    "server_id": "data_analysis_tools",
    "connection_status": "connected",
    "connected_at": "2023-08-01T12:34:56.789Z"
  }
}
```

#### 7.1.3 断开MCP服务器

```
POST /api/v1/mcp/servers/disconnect
```

**说明**：断开与指定MCP服务器的连接

**请求体**：

```json
{
  "server_id": "data_analysis_tools"
}
```

**响应**：

```json
{
  "status": "success",
  "data": {
    "server_id": "data_analysis_tools",
    "connection_status": "disconnected",
    "disconnected_at": "2023-08-01T12:34:56.789Z"
  }
}
```

#### 7.1.4 添加MCP服务器配置

```
POST /api/v1/mcp/servers
```

**说明**：添加新的MCP服务器配置

**请求体**：

```json
{
  "id": "vehicle_simulation_tools",
  "name": "车辆仿真工具集",
  "type": "sse",
  "url": "http://simulation:8000/sse",
  "auto_connect": true
}
```

**响应**：

```json
{
  "status": "success",
  "data": {
    "id": "vehicle_simulation_tools",
    "name": "车辆仿真工具集",
    "type": "sse",
    "url": "http://simulation:8000/sse",
    "auto_connect": true,
    "created_at": "2023-08-01T12:34:56.789Z"
  }
}
```

#### 7.1.5 删除MCP服务器配置

```
DELETE /api/v1/mcp/servers/{server_id}
```

**说明**：删除指定的MCP服务器配置

**响应**：

```json
{
  "status": "success",
  "data": {
    "message": "MCP服务器配置已删除"
  }
}
```

### 7.2 MCP工具管理

#### 7.2.1 获取可用工具列表

```
GET /api/v1/mcp/tools
```

**说明**：获取所有已连接MCP服务器上的可用工具

**参数**：
- `server_id`（可选）：筛选特定服务器上的工具

**响应**：

```json
{
  "status": "success",
  "data": {
    "tools": [
      {
        "name": "run_simulation",
        "description": "运行车辆仿真场景",
        "server_id": "vehicle_simulation_tools",
        "original_name": "run_simulation",
        "parameters": {
          "type": "object",
          "properties": {
            "scenario_file": {
              "type": "string",
              "description": "场景配置文件路径"
            },
            "duration": {
              "type": "number",
              "description": "仿真持续时间（秒）"
            }
          },
          "required": ["scenario_file"]
        }
      },
      {
        "name": "analyze_data",
        "description": "分析车辆测试数据",
        "server_id": "data_analysis_tools",
        "original_name": "data_analysis",
        "parameters": {
          "type": "object",
          "properties": {
            "data_file": {
              "type": "string",
              "description": "数据文件路径"
            },
            "analysis_type": {
              "type": "string",
              "enum": ["performance", "security", "durability"],
              "description": "分析类型"
            }
          },
          "required": ["data_file", "analysis_type"]
        }
      }
    ]
  }
}
```

#### 7.2.2 调用MCP工具

```
POST /api/v1/mcp/tools/execute
```

**说明**：调用指定的MCP工具

**请求体**：

```json
{
  "tool_name": "run_simulation",
  "server_id": "vehicle_simulation_tools",
  "parameters": {
    "scenario_file": "/path/to/scenario.json",
    "duration": 120
  }
}
```

**响应**：

```json
{
  "status": "success",
  "data": {
    "tool_name": "run_simulation",
    "server_id": "vehicle_simulation_tools",
    "execution_id": "sim_1234567890",
    "result": {
      "status": "completed",
      "simulation_time": 120,
      "metrics": {
        "cpu_usage": 45.2,
        "memory_usage": 1256.8
      },
      "output_file": "/path/to/results/sim_1234567890.json"
    }
  }
}
```

#### 7.2.3 获取工具执行历史

```
GET /api/v1/mcp/tools/history
```

**说明**：获取MCP工具调用历史记录

**参数**：
- `tool_name`（可选）：筛选特定工具
- `server_id`（可选）：筛选特定服务器
- `page`（可选）：页码
- `limit`（可选）：每页条目数

**响应**：

```json
{
  "status": "success",
  "data": {
    "history": [
      {
        "execution_id": "sim_1234567890",
        "tool_name": "run_simulation",
        "server_id": "vehicle_simulation_tools",
        "parameters": {
          "scenario_file": "/path/to/scenario.json",
          "duration": 120
        },
        "status": "completed",
        "start_time": "2023-08-01T12:34:56.789Z",
        "end_time": "2023-08-01T12:36:56.789Z",
        "duration_ms": 120000,
        "result": "..."
      },
      {
        "execution_id": "analysis_9876543210",
        "tool_name": "analyze_data",
        "server_id": "data_analysis_tools",
        "parameters": {
          "data_file": "/path/to/data.csv",
          "analysis_type": "security"
        },
        "status": "failed",
        "start_time": "2023-08-01T11:22:33.444Z",
        "end_time": "2023-08-01T11:22:34.555Z",
        "duration_ms": 1111,
        "error": "无法读取数据文件"
      }
    ],
    "pagination": {
      "total": 128,
      "page": 1,
      "limit": 10,
      "pages": 13
    }
  }
}
``` 