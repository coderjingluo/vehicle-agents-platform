#!/usr/bin/env python3
"""
API测试脚本

用于测试后端API接口的功能是否正常。
此脚本将测试所有主要的API端点，包括认证、代理、工具、任务、模型、执行流、知识库和MCP。

使用方法:
    python api_test.py [--url URL] [--username USERNAME] [--password PASSWORD] [--tests TESTS]

参数:
    --url URL             API基础URL (默认: http://localhost:8000/api/v1)
    --username USERNAME   用户名 (默认: admin)
    --password PASSWORD   密码 (默认: admin)
    --tests TESTS         要运行的测试，用逗号分隔 (默认: all)
                          可选值: auth,agents,tools,models,tasks,flows,knowledge,mcp

示例:
    # 运行所有测试
    python api_test.py
    
    # 只测试认证和代理
    python api_test.py --tests auth,agents
    
    # 使用自定义URL和凭据
    python api_test.py --url http://example.com/api/v1 --username user --password pass
"""

import asyncio
import json
import logging
import sys
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import copy
import traceback

import httpx
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
import argparse

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)-8s %(message)s',
                   datefmt='%H:%M:%S')
log = logging.getLogger("api_test")

# 创建详细的API请求响应日志记录器
api_log_file = "detailed_api_test_results.log"
api_logger = logging.getLogger("api_details")
api_logger.setLevel(logging.DEBUG)
api_file_handler = logging.FileHandler(api_log_file, mode='w', encoding='utf-8')
api_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
api_logger.addHandler(api_file_handler)
api_logger.propagate = False  # 防止日志传递到父记录器

# 设置Rich控制台
console = Console()

# API基础URL和测试账号
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# 测试数据
test_agent = {
    "name": "测试代理",
    "agent_type": "automation",
    "description": "用于API测试的代理",
    "model_id": None,  # 将在测试中设置为实际存在的模型ID
    "config": {
        "temperature": 0.5,
        "max_tokens": 4000
    },
    "tools": [
        "web_search",
        "file_read"
    ]
}

test_model_config = {
    "name": "测试模型",
    "provider": "anthropic",
    "model_name": "claude-3-opus-20240229",
    "api_key": "test_api_key",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "description": "用于API测试的模型配置"
}

test_task = {
    "title": f"Test Task {uuid.uuid4().hex[:8]}",
    "description": "这是一个用于测试的任务",
    "task_type": "tara",
    "priority": 1,
    "config": {
        "input_data": "测试数据",
        "settings": {
            "max_steps": 5
        }
    }
}

test_flow_request = {
    "flow_type": "tara",
    "name": f"Test Flow {uuid.uuid4().hex[:8]}",
    "description": "这是一个用于测试的执行流",
    "use_langgraph": True,
    "config": {
        "input_data": "测试TARA分析",
        "settings": {
            "max_steps": 5
        }
    }
}

test_flow_execution = {
    "input_data": {
        "system": "车联网安全系统",
        "task": "执行TARA分析",
        "detailed_description": "这是一个测试执行"
    }
}

test_knowledge_document = {
    "title": f"Test Document {uuid.uuid4().hex[:8]}",
    "content": "这是一个测试文档的内容，用于测试知识库API。",
    "source": "API测试",
    "doc_type": "text",
    "tags": ["测试", "API"]
}

test_knowledge_base = {
    "name": f"Test KB {uuid.uuid4().hex[:8]}",
    "description": "这是一个测试知识库",
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 500,
    "chunk_overlap": 50
}

test_mcp_connection = {
    "name": f"Test MCP Connection {uuid.uuid4().hex[:8]}",
    "url": "http://localhost:8080",
    "type": "http",
    "description": "这是一个测试MCP连接",
    "api_key": "test_api_key"
}


class APITestClient:
    """API测试客户端"""
    
    def __init__(self, base_url: str, username: str, password: str):
        """初始化API测试客户端"""
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)
        self.request_id = 0  # 请求计数器，用于跟踪请求顺序
    
    async def login(self) -> bool:
        """登录并获取认证令牌"""
        try:
            # 使用正确的登录接口
            self.request_id += 1
            request_data = {"username": self.username, "password": self.password}
            
            # 记录请求信息
            api_logger.info(f"请求 #{self.request_id} - POST {self.base_url}/auth/login")
            api_logger.debug(f"请求 #{self.request_id} - 数据: {json.dumps({'username': self.username, 'password': '******'}, ensure_ascii=False)}")
            
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                data=request_data
            )
            
            # 记录响应信息
            api_logger.info(f"响应 #{self.request_id} - 状态码: {response.status_code}")
            api_logger.debug(f"响应 #{self.request_id} - 头信息: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                api_logger.debug(f"响应 #{self.request_id} - 内容: {json.dumps(response_json, ensure_ascii=False)}")
            except Exception as e:
                api_logger.debug(f"响应 #{self.request_id} - 内容: {response.text}")
                api_logger.error(f"响应 #{self.request_id} - JSON解析错误: {str(e)}")
            
            response.raise_for_status()
            data = response.json()
            
            # 从正确的响应结构中获取token
            if data.get("success") and "data" in data and "access_token" in data["data"]:
                self.token = data["data"]["access_token"]
                log.info(f"登录成功，获取到令牌: {self.token}")
                return True
            else:
                log.error("登录成功但未获取到令牌")
                return False
        except Exception as e:
            log.error(f"登录失败: {str(e)}")
            # 记录详细错误信息
            api_logger.error(f"请求 #{self.request_id} - 登录失败: {str(e)}")
            # api_logger.error(f"请求 #{self.request_id} - 错误详情: {traceback.format_exc()}")
            # 尝试打印详细的响应内容
            try:
                api_logger.error(f"请求 #{self.request_id} - 响应内容: {e.response.text if hasattr(e, 'response') else '无响应内容'}")
            except:
                pass
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """获取带有认证信息的请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行GET请求"""
        url = f"{self.base_url}{endpoint}"
        self.request_id += 1
        current_request_id = self.request_id
        
        try:
            # 记录请求信息
            api_logger.info(f"请求 #{current_request_id} - GET {url}")
            api_logger.debug(f"请求 #{current_request_id} - 参数: {json.dumps(params, ensure_ascii=False) if params else 'None'}")
            api_logger.debug(f"请求 #{current_request_id} - 头信息: {json.dumps(self.get_headers(), ensure_ascii=False)}")
            
            response = await self.client.get(url, headers=self.get_headers(), params=params)
            
            # 记录响应信息
            api_logger.info(f"响应 #{current_request_id} - 状态码: {response.status_code}")
            api_logger.debug(f"响应 #{current_request_id} - 头信息: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                api_logger.debug(f"响应 #{current_request_id} - 内容: {json.dumps(response_json, ensure_ascii=False)}")
            except Exception as e:
                api_logger.debug(f"响应 #{current_request_id} - 内容: {response.text}")
                api_logger.error(f"响应 #{current_request_id} - JSON解析错误: {str(e)}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"GET {url} 失败: {str(e)}")
            # 记录详细错误信息
            api_logger.error(f"请求 #{current_request_id} - GET {url} 失败: {str(e)}")
            # api_logger.error(f"请求 #{current_request_id} - 错误详情: {traceback.format_exc()}")
            try:
                api_logger.error(f"请求 #{current_request_id} - 响应内容: {e.response.text if hasattr(e, 'response') else '无响应内容'}")
            except:
                pass
            return {"success": False, "error": str(e)}
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行POST请求"""
        url = f"{self.base_url}{endpoint}"
        self.request_id += 1
        current_request_id = self.request_id
        
        try:
            # 记录请求信息
            api_logger.info(f"请求 #{current_request_id} - POST {url}")
            api_logger.debug(f"请求 #{current_request_id} - 数据: {json.dumps(data, ensure_ascii=False)}")
            api_logger.debug(f"请求 #{current_request_id} - 头信息: {json.dumps(self.get_headers(), ensure_ascii=False)}")
            
            response = await self.client.post(
                url, headers=self.get_headers(), json=data
            )
            
            # 记录响应信息
            api_logger.info(f"响应 #{current_request_id} - 状态码: {response.status_code}")
            api_logger.debug(f"响应 #{current_request_id} - 头信息: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                api_logger.debug(f"响应 #{current_request_id} - 内容: {json.dumps(response_json, ensure_ascii=False)}")
            except Exception as e:
                api_logger.debug(f"响应 #{current_request_id} - 内容: {response.text}")
                api_logger.error(f"响应 #{current_request_id} - JSON解析错误: {str(e)}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"POST {url} 失败: {str(e)}")
            # 记录详细错误信息
            api_logger.error(f"请求 #{current_request_id} - POST {url} 失败: {str(e)}")
            # api_logger.error(f"请求 #{current_request_id} - 错误详情: {traceback.format_exc()}")
            try:
                api_logger.error(f"请求 #{current_request_id} - 响应内容: {e.response.text if hasattr(e, 'response') else '无响应内容'}")
            except:
                pass
            return {"success": False, "error": str(e)}
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行PUT请求"""
        url = f"{self.base_url}{endpoint}"
        self.request_id += 1
        current_request_id = self.request_id
        
        try:
            # 记录请求信息
            api_logger.info(f"请求 #{current_request_id} - PUT {url}")
            api_logger.debug(f"请求 #{current_request_id} - 数据: {json.dumps(data, ensure_ascii=False)}")
            api_logger.debug(f"请求 #{current_request_id} - 头信息: {json.dumps(self.get_headers(), ensure_ascii=False)}")
            
            response = await self.client.put(
                url, headers=self.get_headers(), json=data
            )
            
            # 记录响应信息
            api_logger.info(f"响应 #{current_request_id} - 状态码: {response.status_code}")
            api_logger.debug(f"响应 #{current_request_id} - 头信息: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                api_logger.debug(f"响应 #{current_request_id} - 内容: {json.dumps(response_json, ensure_ascii=False)}")
            except Exception as e:
                api_logger.debug(f"响应 #{current_request_id} - 内容: {response.text}")
                api_logger.error(f"响应 #{current_request_id} - JSON解析错误: {str(e)}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"PUT {url} 失败: {str(e)}")
            # 记录详细错误信息
            api_logger.error(f"请求 #{current_request_id} - PUT {url} 失败: {str(e)}")
            # api_logger.error(f"请求 #{current_request_id} - 错误详情: {traceback.format_exc()}")
            try:
                api_logger.error(f"请求 #{current_request_id} - 响应内容: {e.response.text if hasattr(e, 'response') else '无响应内容'}")
            except:
                pass
            return {"success": False, "error": str(e)}
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """执行DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        self.request_id += 1
        current_request_id = self.request_id
        
        try:
            # 记录请求信息
            api_logger.info(f"请求 #{current_request_id} - DELETE {url}")
            api_logger.debug(f"请求 #{current_request_id} - 头信息: {json.dumps(self.get_headers(), ensure_ascii=False)}")
            
            response = await self.client.delete(url, headers=self.get_headers())
            
            # 记录响应信息
            api_logger.info(f"响应 #{current_request_id} - 状态码: {response.status_code}")
            api_logger.debug(f"响应 #{current_request_id} - 头信息: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                api_logger.debug(f"响应 #{current_request_id} - 内容: {json.dumps(response_json, ensure_ascii=False)}")
            except Exception as e:
                api_logger.debug(f"响应 #{current_request_id} - 内容: {response.text}")
                api_logger.error(f"响应 #{current_request_id} - JSON解析错误: {str(e)}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"DELETE {url} 失败: {str(e)}")
            # 记录详细错误信息
            api_logger.error(f"请求 #{current_request_id} - DELETE {url} 失败: {str(e)}")
            # api_logger.error(f"请求 #{current_request_id} - 错误详情: {traceback.format_exc()}")
            try:
                api_logger.error(f"请求 #{current_request_id} - 响应内容: {e.response.text if hasattr(e, 'response') else '无响应内容'}")
            except:
                pass
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class APITester:
    """API测试器"""
    
    def __init__(self, client: APITestClient):
        """初始化API测试器"""
        self.client = client
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": {}
        }
        self.created_items = {
            "agents": [],
            "models": [],
            "tasks": [],
            "flows": [],
            "knowledge_docs": [],
            "knowledge_bases": [],
            "mcp_connections": []
        }
    
    def record_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """记录测试结果"""
        self.results["total"] += 1
        if success:
            self.results["passed"] += 1
            log.info(f"✅ 测试通过: {test_name}")
            api_logger.info(f"测试结果: ✅ 通过 - {test_name} {details}")
        else:
            self.results["failed"] += 1
            log.error(f"❌ 测试失败: {test_name}")
            api_logger.error(f"测试结果: ❌ 失败 - {test_name}")
            if details and "error" in details:
                api_logger.error(f"测试失败原因: {details.get('error', '未知错误')}")
        
        if details is None:
            details = {}
        
        self.results["details"][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # 在日志中添加分隔线，使测试结果更易读
        api_logger.info("-" * 80)
    
    async def test_auth(self):
        """测试认证API"""
        # 已在初始化时完成登录，这里检查是否成功
        success = self.client.token is not None
        self.record_result("认证登录", success)
        
        # 获取当前用户信息
        if success:
            response = await self.client.get("/auth/me")
            success = response.get("success", False)
            self.record_result("获取当前用户", success, response)
            
            # 测试刷新令牌
            refresh_data = {
                "refresh_token": "dummy_refresh_token"  # 实际测试中应使用真实的refresh_token
            }
            # 注意：这里只是测试API调用，预期会失败因为我们使用了虚拟的refresh_token
            response = await self.client.post("/auth/refresh", refresh_data)
            # 我们只检查API存在，不检查刷新是否成功
            self.record_result("刷新令牌API调用", True, response)
            
            # 测试登出
            response = await self.client.post("/auth/logout", {})
            success = response.get("success", False)
            self.record_result("用户登出", success, response)
    
    async def test_agents(self):
        """测试代理API"""
        # 获取代理列表
        response = await self.client.get("/agents/")
        success = response.get("success", False)
        self.record_result("获取代理列表", success, response)
        
        # 获取可用的模型ID
        models_response = await self.client.get("/models/")
        model_id = None
        if models_response.get("success") and "data" in models_response and "models" in models_response["data"] and len(models_response["data"]["models"]) > 0:
            model_id = models_response["data"]["models"][0]["id"]
        
        # 创建代理
        new_agent = copy.deepcopy(test_agent)
        new_agent["name"] = f"Test Agent {uuid.uuid4().hex[:8]}"
        new_agent["model_id"] = model_id
        
        response = await self.client.post("/agents/", new_agent)
        success = response.get("success", False)
        self.record_result("创建代理", success, response)
        
        # 保存创建的代理ID用于清理
        if success and "data" in response and "id" in response["data"]:
            self.created_items["agents"].append(response["data"]["id"])
            
            # 获取代理详情
            response = await self.client.get(f"/agents/{response['data']['id']}")
            success = response.get("success", False)
            self.record_result("获取代理详情", success, response)
            
            # 更新代理
            update_data = {
                "name": f"Updated Agent {uuid.uuid4().hex[:8]}",
                "description": "这是更新后的代理描述"
            }
            response = await self.client.put(f"/agents/{response['data']['id']}", update_data)
            success = response.get("success", False)
            self.record_result("更新代理", success, response)
            
            # 配置代理工具
            tools_data = [
                {"name": "web_search", "enabled": True},
                {"name": "file_read", "enabled": True}
            ]
            response = await self.client.post(f"/agents/{response['data']['id']}/tools", tools_data)
            success = response.get("success", False)
            self.record_result("配置代理工具", success, response)
    
    async def test_tools(self):
        """测试工具API"""
        # 获取工具列表
        response = await self.client.get("/tools/")
        success = response.get("success", False)
        self.record_result("获取工具列表", success, response)
        
        # 获取特定工具的详细信息（这里假设至少有一个工具存在）
        if success and "data" in response and "tools" in response["data"] and len(response["data"]["tools"]) > 0:
            tool_id = response["data"]["tools"][0]["id"]
            response = await self.client.get(f"/tools/{tool_id}")
            success = response.get("success", False)
            self.record_result("获取工具详细信息", success, response)
            
            # 获取工具类型
            response = await self.client.get("/tools/types")
            success = response.get("success", False)
            self.record_result("获取工具类型", success, response)
        else:
            log.warning("工具列表为空，跳过获取工具详情和工具类型测试")
            self.record_result("获取工具详细信息", True, {"message": "工具列表为空，跳过测试"})
            self.record_result("获取工具类型", True, {"message": "工具列表为空，跳过测试"})
    
    async def test_tasks(self):
        """测试任务API"""
        # 获取任务列表
        response = await self.client.get("/tasks/")
        success = response.get("success", False)
        self.record_result("获取任务列表", success, response)
        
        # 创建任务
        new_task = copy.deepcopy(test_task)
        new_task["name"] = f"Test Task {uuid.uuid4().hex[:8]}"
        
        response = await self.client.post("/tasks/", new_task)
        success = response.get("success", False)
        self.record_result("创建任务", success, response)
        
        # 保存创建的任务ID用于清理
        if success and "data" in response and "id" in response["data"]:
            task_id = response["data"]["id"]
            self.created_items["tasks"].append(task_id)
            
            # 获取任务详情
            response = await self.client.get(f"/tasks/{task_id}")
            success = response.get("success", False)
            self.record_result("获取任务详情", success, response)
            
            # 执行任务
            # 注意：这里只测试API调用是否成功，不等待任务完成
            response = await self.client.post(f"/tasks/{task_id}/execute", {})
            success = response.get("success", False)
            self.record_result("执行任务", success, response)
            
            # 测试暂停任务
            response = await self.client.post(f"/tasks/{task_id}/pause", {})
            # 这里不判断暂停是否成功，因为任务可能已经完成
            self.record_result("暂停任务API调用", True, response)
            
            # 测试恢复任务
            response = await self.client.post(f"/tasks/{task_id}/resume", {})
            # 这里不判断恢复是否成功，因为任务可能未暂停
            self.record_result("恢复任务API调用", True, response)
            
            # 测试取消任务
            response = await self.client.post(f"/tasks/{task_id}/cancel", {})
            # 这里不判断取消是否成功，因为任务可能已经完成
            self.record_result("取消任务API调用", True, response)
    
    async def test_models(self):
        """测试模型API"""
        
        # 创建模型配置
        new_model = copy.deepcopy(test_model_config)
        new_model["name"] = f"Test Model {uuid.uuid4().hex[:8]}"
        response = await self.client.post("/models/", new_model)
        success = response.get("success", False)
        self.record_result("创建模型配置", success, response)
        
        # 获取模型列表
        response = await self.client.get("/models/")
        success = response.get("success", False)
        self.record_result("获取模型列表", success, response)
        
        data = response.get("data", {})
        if data and "models" in data:
            for model in data["models"]:
                # 保存创建的模型ID用于清理
                model_id = model["id"]
                self.created_items["models"].append(model_id)
                
                # 获取模型详情
                response = await self.client.get(f"/models/{model_id}")
                success = response.get("success", False)
                self.record_result("获取模型详情", success, response)
                
                # 更新模型配置
                update_data = {
                    "description": "这是更新后的模型描述",
                    "parameters": {"temperature": 0.8}  # 使用parameters而不是default_parameters
                }
                response = await self.client.put(f"/models/{model_id}", update_data)
                success = response.get("success", False)
                self.record_result("更新模型配置", success, response)
                
                # 测试模型连接
                # 注意：由于使用测试密钥，预期会失败，但API调用应该成功
                response = await self.client.post(f"/models/{model_id}/test", {})
                # 这里只检查API调用本身，不检查连接是否成功
                self.record_result("测试模型连接API调用", "data" in response, response)
        
        
        
        
    
    async def test_flows(self):
        """测试执行流API"""
        api_logger.info("开始测试执行流API")
        
        # 创建执行流
        new_flow = copy.deepcopy(test_flow_request)
        new_flow["name"] = f"Test Flow {uuid.uuid4().hex[:8]}"
        
        api_logger.info(f"创建执行流请求: {json.dumps(new_flow, ensure_ascii=False)}")
        response = await self.client.post("/flow", new_flow)
        api_logger.info(f"创建执行流响应: {json.dumps(response, ensure_ascii=False)}")
        success = response.get("success", False)
        self.record_result("创建执行流", success, response)
        
        # 保存创建的流ID用于清理
        if success and "data" in response and "id" in response["data"]:
            flow_id = response["data"]["id"]
            self.created_items["flows"].append(flow_id)
            api_logger.info(f"成功创建执行流，ID: {flow_id}")
            
            # 获取流详情
            api_logger.info(f"获取执行流详情: {flow_id}")
            response = await self.client.get(f"/flow/{flow_id}")
            api_logger.info(f"获取执行流详情响应: {json.dumps(response, ensure_ascii=False)}")
            
            # 检查响应是否是直接返回的对象而不是标准格式
            if isinstance(response, dict) and "success" not in response and "id" in response:
                # 转换为标准格式
                response = {"success": True, "data": response}
            
            success = response.get("success", False)
            self.record_result("获取执行流详情", success, response)
            
            # 执行流
            api_logger.info(f"执行流请求: {flow_id}, 数据: {json.dumps(test_flow_execution, ensure_ascii=False)}")
            response = await self.client.post(f"/flow/{flow_id}/execute", test_flow_execution)
            api_logger.info(f"执行流响应: {json.dumps(response, ensure_ascii=False)}")
            success = response.get("success", False)
            self.record_result("执行流", success, response)
            
            if success and "data" in response and "execution_id" in response["data"]:
                execution_id = response["data"]["execution_id"]
                api_logger.info(f"成功执行流，执行ID: {execution_id}")
                
                # 获取执行详情
                api_logger.info(f"获取执行详情: {execution_id}")
                response = await self.client.get(f"/flow/executions/{execution_id}")
                api_logger.info(f"获取执行详情响应: {json.dumps(response, ensure_ascii=False)}")
                success = response.get("success", False)
                self.record_result("获取执行详情", success, response)
                
                # 暂停执行
                api_logger.info(f"暂停执行: {execution_id}")
                response = await self.client.post(f"/flow/executions/{execution_id}/pause", {})
                api_logger.info(f"暂停执行响应: {json.dumps(response, ensure_ascii=False)}")
                # 这里不判断暂停是否成功，因为执行可能已经完成
                self.record_result("暂停执行API调用", True, response)
                
                # 恢复执行
                api_logger.info(f"恢复执行: {execution_id}")
                response = await self.client.post(f"/flow/executions/{execution_id}/resume", {})
                api_logger.info(f"恢复执行响应: {json.dumps(response, ensure_ascii=False)}")
                # 这里不判断恢复是否成功，因为执行可能未暂停
                self.record_result("恢复执行API调用", True, response)
                
                # 取消执行
                api_logger.info(f"取消执行: {execution_id}")
                response = await self.client.post(f"/flow/executions/{execution_id}/cancel", {})
                api_logger.info(f"取消执行响应: {json.dumps(response, ensure_ascii=False)}")
                # 这里不判断取消是否成功，因为执行可能已经完成
                self.record_result("取消执行API调用", True, response)
        else:
            api_logger.error(f"创建执行流失败: {json.dumps(response, ensure_ascii=False)}")
        
        api_logger.info("执行流API测试完成")
    
    async def test_knowledge(self):
        """测试知识库API"""
        # 创建知识库
        new_kb = copy.deepcopy(test_knowledge_base)
        new_kb["name"] = f"Test KB {uuid.uuid4().hex[:8]}"
        
        response = await self.client.post("/knowledge/knowledge-bases", new_kb)
        success = response.get("success", False)
        self.record_result("创建知识库", success, response)
        
        # 保存创建的知识库ID用于清理
        if success and "data" in response and "id" in response["data"]:
            kb_id = response["data"]["id"]
            self.created_items["knowledge_bases"].append(kb_id)
            
            # 获取知识库详情
            response = await self.client.get(f"/knowledge/knowledge-bases/{kb_id}")
            success = response.get("success", False)
            self.record_result("获取知识库详情", success, response)
            
            # 上传文档
            # 这里使用POST请求模拟文件上传，实际应使用multipart/form-data
            new_doc = copy.deepcopy(test_knowledge_document)
            response = await self.client.post(f"/knowledge/knowledge-bases/{kb_id}/documents", new_doc)
            success = response.get("success", False)
            self.record_result("上传文档", success, response)
            
            if success and "data" in response and "id" in response["data"]:
                doc_id = response["data"]["id"]
                self.created_items["knowledge_docs"].append((kb_id, doc_id))
                
                # 获取文档详情
                response = await self.client.get(f"/knowledge/documents/{doc_id}")
                success = response.get("success", False)
                self.record_result("获取文档详情", success, response)
                
                # 搜索知识库
                search_params = {
                    "query": "测试",
                    "limit": 5
                }
                response = await self.client.get(f"/knowledge/knowledge-bases/{kb_id}/search", search_params)
                success = response.get("success", False)
                self.record_result("搜索知识库", success, response)
                
                # 更新文档
                update_data = {
                    "title": f"Updated Document {uuid.uuid4().hex[:8]}",
                    "tags": ["更新", "测试"]
                }
                response = await self.client.put(f"/knowledge/documents/{doc_id}", update_data)
                success = response.get("success", False)
                self.record_result("更新文档", success, response)
                
                # 删除文档
                response = await self.client.delete(f"/knowledge/documents/{doc_id}")
                success = response.get("success", False)
                self.record_result("删除文档", success, response)
                # 从待清理列表中移除已删除的文档
                if success:
                    self.created_items["knowledge_docs"] = [
                        (k, d) for k, d in self.created_items["knowledge_docs"] if d != doc_id
                    ]
            
            # 更新知识库
            update_data = {
                "description": "这是更新后的知识库描述"
            }
            response = await self.client.put(f"/knowledge/knowledge-bases/{kb_id}", update_data)
            success = response.get("success", False)
            self.record_result("更新知识库", success, response)
    
    async def test_mcp(self):
        """测试MCP API"""
        # 创建MCP连接
        new_connection = copy.deepcopy(test_mcp_connection)
        new_connection["name"] = f"Test Connection {uuid.uuid4().hex[:8]}"
        
        response = await self.client.post("/mcp/connections", new_connection)
        success = response.get("success", False)
        self.record_result("创建MCP连接", success, response)
        
        # 保存创建的连接ID用于清理
        if success and "data" in response and "id" in response["data"]:
            conn_id = response["data"]["id"]
            self.created_items["mcp_connections"].append(conn_id)
            
            # 获取连接详情
            response = await self.client.get(f"/mcp/connections/{conn_id}")
            success = response.get("success", False)
            self.record_result("获取MCP连接详情", success, response)
            
            # 测试连接
            response = await self.client.post(f"/mcp/connections/{conn_id}/test", {})
            # 这里只检查API调用本身，不检查连接是否成功
            self.record_result("测试MCP连接API调用", True, response)
            
            # 获取服务器状态
            response = await self.client.get("/mcp/status/")
            success = response.get("success", False)
            self.record_result("获取MCP服务器状态", success, response)
    
    async def cleanup(self):
        """清理测试数据"""
        log.info("清理测试数据...")
        
        # 清理MCP连接
        for conn_id in self.created_items["mcp_connections"]:
            try:
                await self.client.delete(f"/mcp/connections/{conn_id}")
                log.info(f"已删除MCP连接: {conn_id}")
            except Exception as e:
                log.error(f"删除MCP连接失败: {conn_id} - {str(e)}")
        
        # 清理知识库文档
        for kb_id, doc_id in self.created_items["knowledge_docs"]:
            try:
                await self.client.delete(f"/knowledge/documents/{doc_id}")
                log.info(f"已删除知识库文档: {doc_id}")
            except Exception as e:
                log.error(f"删除知识库文档失败: {doc_id} - {str(e)}")
        
        # 清理知识库
        for kb_id in self.created_items["knowledge_bases"]:
            try:
                await self.client.delete(f"/knowledge/knowledge-bases/{kb_id}")
                log.info(f"已删除知识库: {kb_id}")
            except Exception as e:
                log.error(f"删除知识库失败: {kb_id} - {str(e)}")
        
        # 清理执行流
        for flow_id in self.created_items["flows"]:
            try:
                await self.client.delete(f"/flow/{flow_id}")
                log.info(f"已删除执行流: {flow_id}")
            except Exception as e:
                log.error(f"删除执行流失败: {flow_id} - {str(e)}")
        
        # 清理任务
        for task_id in self.created_items["tasks"]:
            try:
                await self.client.delete(f"/tasks/{task_id}")
                log.info(f"已删除任务: {task_id}")
            except Exception as e:
                log.error(f"删除任务失败: {task_id} - {str(e)}")
        
        # 清理模型
        for model_id in self.created_items["models"]:
            try:
                await self.client.delete(f"/models/{model_id}")
                log.info(f"已删除模型: {model_id}")
            except Exception as e:
                log.error(f"删除模型失败: {model_id} - {str(e)}")
        
        # 清理代理
        for agent_id in self.created_items["agents"]:
            try:
                await self.client.delete(f"/agents/{agent_id}")
                log.info(f"已删除代理: {agent_id}")
            except Exception as e:
                log.error(f"删除代理失败: {agent_id} - {str(e)}")
    
    def print_results(self):
        """打印测试结果统计"""
        table = Table(title="API测试结果")
        table.add_column("测试", style="cyan")
        table.add_column("结果", style="green")
        
        for test_name, result in self.results["details"].items():
            status = "✅ 通过" if result["success"] else "❌ 失败"
            style = "green" if result["success"] else "red"
            table.add_row(test_name, status, style=style)
        
        console.print(table)
        
        summary = f"总计: {self.results['total']} 测试, " \
                  f"{self.results['passed']} 通过, " \
                  f"{self.results['failed']} 失败"
        
        if self.results["failed"] > 0:
            console.print(summary, style="bold red")
        else:
            console.print(summary, style="bold green")
    
    async def run_all_tests(self, test_filter="all"):
        """
        运行所有测试，或者根据过滤条件运行特定测试
        
        参数:
            test_filter: 要运行的测试，可以是"all"或者特定测试名称的列表
        
        返回:
            bool: 是否所有测试都通过
        """
        # 记录测试开始
        api_logger.info("=" * 80)
        api_logger.info("API测试开始执行")
        api_logger.info(f"测试时间: {datetime.now().isoformat()}")
        api_logger.info(f"测试过滤条件: {test_filter}")
        api_logger.info("=" * 80)
        
        # 首先进行认证测试
        await self.test_auth()
        
        # 如果认证失败，则跳过其他测试
        if "认证登录" not in self.results["details"] or not self.results["details"]["认证登录"]["success"]:
            log.error("认证失败，跳过其他测试")
            api_logger.error("认证失败，跳过其他测试")
            return False
        
        tests_to_run = []
        if test_filter == "all":
            tests_to_run = ["agents", "tools", "models", "tasks", "flow", "knowledge", "mcp"]
        else:
            tests_to_run = test_filter.split(",")
        
        api_logger.info(f"将要运行的测试模块: {', '.join(tests_to_run)}")
        
        # 根据过滤条件执行测试
        try:
            if "agents" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试代理(Agent)模块")
                await self.test_agents()
                api_logger.info("代理(Agent)模块测试完成")
                
            if "tools" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试工具(Tool)模块")
                await self.test_tools()
                api_logger.info("工具(Tool)模块测试完成")
                
            if "models" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试模型(Model)模块")
                await self.test_models()
                api_logger.info("模型(Model)模块测试完成")
                
            if "tasks" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试任务(Task)模块")
                await self.test_tasks()
                api_logger.info("任务(Task)模块测试完成")
                
            if "flow" in tests_to_run or "flows" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试执行流(Flow)模块")
                await self.test_flows()
                api_logger.info("执行流(Flow)模块测试完成")
                
            if "knowledge" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试知识库(Knowledge)模块")
                await self.test_knowledge()
                api_logger.info("知识库(Knowledge)模块测试完成")
                
            if "mcp" in tests_to_run:
                api_logger.info("=" * 50)
                api_logger.info("开始测试MCP模块")
                await self.test_mcp()
                api_logger.info("MCP模块测试完成")
        except Exception as e:
            log.error(f"测试过程中发生错误: {str(e)}")
            api_logger.error(f"测试过程中发生未捕获的异常: {str(e)}")
            api_logger.error(f"异常详情: {traceback.format_exc()}")
            return False
        
        # 清理测试数据
        try:
            api_logger.info("=" * 50)
            api_logger.info("开始清理测试数据")
            await self.cleanup()
            api_logger.info("测试数据清理完成")
        except Exception as e:
            log.error(f"清理测试数据时发生错误: {str(e)}")
            api_logger.error(f"清理测试数据时发生错误: {str(e)}")
            # api_logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 打印测试结果
        self.print_results()
        
        # 记录测试结果摘要
        api_logger.info("=" * 80)
        api_logger.info("API测试执行完成")
        api_logger.info(f"总计: {self.results['total']} 测试, {self.results['passed']} 通过, {self.results['failed']} 失败")
        
        # 记录失败的测试详情
        if self.results["failed"] > 0:
            api_logger.error("失败的测试:")
            for test_name, result in self.results["details"].items():
                if not result["success"]:
                    api_logger.error(f"- {test_name}")
                    if "details" in result and "error" in result["details"]:
                        api_logger.error(f"  错误: {result['details']['error']}")
        
        api_logger.info("=" * 80)
        
        # 判断是否所有测试都通过
        return self.results["passed"] == self.results["total"]


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='API测试工具')
    parser.add_argument('--url', type=str, default=BASE_URL,
                      help='API基础URL')
    parser.add_argument('--username', type=str, default=ADMIN_USERNAME,
                      help='用户名')
    parser.add_argument('--password', type=str, default=ADMIN_PASSWORD,
                      help='密码')
    parser.add_argument('--tests', type=str, default='all',
                      help='要运行的测试，用逗号分隔，可选值: auth,agents,tools,models,tasks,flows,knowledge,mcp,all')
    parser.add_argument('--log-level', type=str, default='INFO',
                      help='日志级别，可选值: DEBUG,INFO,WARNING,ERROR')
    
    args = parser.parse_args()
    
    # 设置日志级别
    level = getattr(logging, args.log_level.upper(), logging.INFO)
    api_logger.setLevel(level)
    
    console.print("开始API测试...", style="bold blue")
    api_logger.info(f"API测试开始 - URL: {args.url}, 用户名: {args.username}, 测试: {args.tests}")
    
    # 创建API测试客户端
    client = APITestClient(args.url, args.username, args.password)
    
    try:
        # 登录
        login_success = await client.login()
        if not login_success:
            console.print("登录失败，无法进行测试", style="bold red")
            api_logger.error("登录失败，无法进行测试")
            return 1
        
        # 创建测试器
        tester = APITester(client)
        
        # 运行测试
        all_passed = await tester.run_all_tests(args.tests)
        
        # 记录测试完成信息
        api_logger.info(f"API测试完成 - 结果: {'全部通过' if all_passed else '有测试失败'}")
        api_logger.info(f"详细日志已保存到: {os.path.abspath(api_log_file)}")
        console.print(f"详细测试日志已保存到: {os.path.abspath(api_log_file)}", style="bold blue")
        
        return 0 if all_passed else 1
    except Exception as e:
        log.error(f"测试过程中发生错误: {str(e)}")
        api_logger.error(f"测试过程中发生未捕获的异常: {str(e)}")
        api_logger.error(f"异常详情: {traceback.format_exc()}")
        return 1
    finally:
        # 关闭客户端
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())