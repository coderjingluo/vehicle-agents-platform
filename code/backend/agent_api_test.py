#!/usr/bin/env python
"""
车联网安全测试平台 - API动态规划测试脚本

该脚本测试智能体是否能够正确地动态生成执行计划，将大任务智能拆分为子任务。
"""

import asyncio
import json
import logging
import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
import uuid

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_api_test.log')
    ]
)

logger = logging.getLogger(__name__)

# API配置
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
DEFAULT_USERNAME = os.getenv('API_USERNAME', 'admin')
DEFAULT_PASSWORD = os.getenv('API_PASSWORD', 'admin123')


class AgentAPITester:
    """测试智能体API的动态规划能力"""
    
    def __init__(self, base_url: str = API_BASE_URL, username: str = DEFAULT_USERNAME, password: str = DEFAULT_PASSWORD):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        self.access_token = None
    
    def login(self) -> bool:
        """登录并获取访问令牌"""
        login_url = f"{self.base_url}/auth/login"
        
        # 使用表单数据格式进行登录，这是OAuth2的标准格式
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            logger.info(f"尝试登录，用户名: {self.username}")
            # 使用表单格式提交登录请求
            response = requests.post(
                login_url, 
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("data", {}).get("access_token")
                
                if self.access_token:
                    # 设置认证头
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    logger.info("登录成功，已获取访问令牌")
                    return True
                else:
                    logger.error("登录响应中未包含访问令牌")
                    return False
            else:
                logger.error(f"登录失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"登录过程中出错: {str(e)}")
            return False
    
    def _log_response(self, response, message: str):
        """记录响应结果"""
        try:
            result = response.json() if response.content else {}
            logger.info(f"{message}: {response.status_code}")
            logger.info(f"获取响应内容: {response.text}")
            
            if response.status_code >= 400:
                logger.error(f"错误响应: {response.text}")
            logger.debug(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except Exception as e:
            logger.error(f"{message}失败: {e}")
            logger.error(f"响应状态码: {response.status_code}")
            logger.error(f"响应文本: {response.text}")
            return None
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        response = self.session.post(f"{self.base_url}/tasks/", json=task_data)
        return self._log_response(response, "创建任务")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        # 移除 UUID 周围的引号
        if task_id.startswith('"') and task_id.endswith('"'):
            task_id = task_id[1:-1]
        response = self.session.get(f"{self.base_url}/tasks/{task_id}")
        return self._log_response(response, "获取任务状态")
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情"""
        # 移除 UUID 周围的引号
        if task_id.startswith('"') and task_id.endswith('"'):
            task_id = task_id[1:-1]
        response = self.session.get(f"{self.base_url}/tasks/{task_id}")
        return self._log_response(response, "获取任务详情")
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行任务"""
        # 移除 UUID 周围的引号
        if task_id.startswith('"') and task_id.endswith('"'):
            task_id = task_id[1:-1]
        response = self.session.post(f"{self.base_url}/tasks/{task_id}/execute")
        return self._log_response(response, "执行任务")
    
    def _extract_plan_from_response(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """从响应中提取执行计划
        
        我们修改了智能体实现，计划可能存储在不同的位置
        """
        try:
            # 尝试从output_data中提取
            output_data = details.get("data", {}).get("output_data", {})
            if isinstance(output_data, str):
                output_data = json.loads(output_data)
            
            # 首先检查output_data中的plan字段
            plan = output_data.get("plan", {})
            if plan and isinstance(plan, dict) and "subtasks" in plan:
                return plan
            
            # 检查memory中是否包含计划
            memory = output_data.get("memory", [])
            if memory:
                # 查找包含current_plan的系统消息
                for msg in memory:
                    if msg.get("role") == "system" and "current_plan" in str(msg.get("content", "")):
                        # 尝试从消息中提取JSON
                        import re
                        json_match = re.search(r'{.*"subtasks".*}', msg.get("content", ""))
                        if json_match:
                            try:
                                extracted_plan = json.loads(json_match.group(0))
                                if "subtasks" in extracted_plan:
                                    return extracted_plan
                            except:
                                pass
            
            # 直接查找current_plan字段
            current_plan = output_data.get("current_plan", {})
            if current_plan and isinstance(current_plan, dict) and "subtasks" in current_plan:
                return current_plan
            
            # 最后尝试在整个响应中查找
            for key, value in details.get("data", {}).items():
                if isinstance(value, dict) and "subtasks" in value:
                    return value
            
            return {"subtasks": []}
        except Exception as e:
            logger.error(f"提取计划时出错: {str(e)}")
            return {"subtasks": []}
    
    def test_tara_dynamic_planning(self) -> Dict[str, Any]:
        """测试TARA智能体的动态规划能力"""
        logger.info("开始测试TARA智能体的动态规划能力")
        
        # 创建TARA任务
        task_data = {
            "name": "执行车联网ECU安全TARA分析",
            "description": "针对车载ECU系统执行威胁分析与风险评估，识别资产、威胁、风险，并提出缓解措施",
            "type": "tara",
            "input_data": {
                "target_system": "车载ECU",
                "security_focus": "网络安全",
                "output_format": "详细报告"
            }
        }
        
        # 发送任务创建请求
        result = self.create_task(task_data)
        
        if not result or not result.get("success"):
            return {"success": False, "error": "创建TARA任务失败"}
        
        task_id = result.get("data", {}).get("id")
        logger.info(f"创建的任务ID: {task_id}")
        logger.info(f"任务详情: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
        
        if not task_id:
            return {"success": False, "error": "未获取到任务ID"}
        
        # 执行任务
        execute_result = self.execute_task(task_id)
        if not execute_result or not execute_result.get("success"):
            logger.warning("执行任务可能失败，尝试继续检查任务状态")
        
        # 等待任务完成并获取结果
        max_retries = 300
        retry_interval = 2
        
        for i in range(max_retries):
            logger.info(f"等待TARA任务完成，第 {i+1}/{max_retries} 次检查")
            
            task_status = self.get_task_status(task_id)
            
            if not task_status or not task_status.get("success"):
                time.sleep(retry_interval)
                continue
                
            status = task_status.get("data", {}).get("status")
            
            if status == "completed":
                logger.info("TARA任务已完成")
                
                # 获取任务细节
                details = self.get_task_details(task_id)
                
                if not details or not details.get("success"):
                    return {"success": False, "error": "获取任务详情失败"}
                
                # 使用新的方法提取计划
                plan = self._extract_plan_from_response(details)
                subtasks = plan.get("subtasks", [])
                
                if subtasks:
                    logger.info(f"TARA智能体成功生成了动态计划，包含 {len(subtasks)} 个子任务")
                    return {
                        "success": True,
                        "agent_type": "tara",
                        "task_id": task_id,
                        "plan": plan,
                        "subtasks_count": len(subtasks)
                    }
                else:
                    logger.error("TARA智能体未能生成动态计划")
                    return {
                        "success": False,
                        "error": "未能生成动态计划",
                        "details": details.get("data", {})
                    }
            elif status == "failed":
                logger.error("TARA任务执行失败")
                return {"success": False, "error": "任务执行失败", "details": task_status.get("data", {})}
            
            # 等待后再次检查
            time.sleep(retry_interval)
        
        logger.error("等待TARA任务完成超时")
        return {"success": False, "error": "任务执行超时"}
    
    def test_testcase_dynamic_planning(self) -> Dict[str, Any]:
        """测试测试用例生成智能体的动态规划能力"""
        logger.info("开始测试测试用例生成智能体的动态规划能力")
        
        # 创建测试用例生成任务
        task_data = {
            "name": "针对车载网络安全生成测试用例",
            "description": "针对车联网系统的CAN总线网络安全特性，生成一组完整的渗透测试用例",
            "type": "test_case",
            "input_data": {
                "target_system": "CAN总线网络",
                "test_focus": "渗透测试",
                "security_level": "高"
            }
        }
        
        # 发送任务创建请求
        result = self.create_task(task_data)
        
        if not result or not result.get("success"):
            return {"success": False, "error": "创建测试用例生成任务失败"}
        
        task_id = result.get("data", {}).get("id")
        logger.info(f"创建的任务ID: {task_id}")
        logger.info(f"任务详情: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
        
        if not task_id:
            return {"success": False, "error": "未获取到任务ID"}
        
        # 执行任务
        execute_result = self.execute_task(task_id)
        if not execute_result or not execute_result.get("success"):
            logger.warning("执行任务可能失败，尝试继续检查任务状态")
        
        # 等待任务完成并获取结果
        max_retries = 300
        retry_interval = 2
        
        for i in range(max_retries):
            logger.info(f"等待测试用例生成任务完成，第 {i+1}/{max_retries} 次检查")
            
            task_status = self.get_task_status(task_id)
            
            if not task_status or not task_status.get("success"):
                time.sleep(retry_interval)
                continue
                
            status = task_status.get("data", {}).get("status")
            
            if status == "completed":
                logger.info("测试用例生成任务已完成")
                
                # 获取任务细节
                details = self.get_task_details(task_id)
                
                if not details or not details.get("success"):
                    return {"success": False, "error": "获取任务详情失败"}
                
                # 使用新的方法提取计划
                plan = self._extract_plan_from_response(details)
                subtasks = plan.get("subtasks", [])
                
                if subtasks:
                    logger.info(f"测试用例生成智能体成功生成了动态计划，包含 {len(subtasks)} 个子任务")
                    return {
                        "success": True,
                        "agent_type": "testcase",
                        "task_id": task_id,
                        "plan": plan,
                        "subtasks_count": len(subtasks)
                    }
                else:
                    logger.error("测试用例生成智能体未能生成动态计划")
                    return {
                        "success": False,
                        "error": "未能生成动态计划",
                        "details": details.get("data", {})
                    }
            elif status == "failed":
                logger.error("测试用例生成任务执行失败")
                return {"success": False, "error": "任务执行失败", "details": task_status.get("data", {})}
            
            # 等待后再次检查
            time.sleep(retry_interval)
        
        logger.error("等待测试用例生成任务完成超时")
        return {"success": False, "error": "任务执行超时"}
    
    def test_automation_dynamic_planning(self) -> Dict[str, Any]:
        """测试自动化测试智能体的动态规划能力"""
        logger.info("开始测试自动化测试智能体的动态规划能力")
        
        # 创建自动化测试任务
        task_data = {
            "name": "执行车联网CAN总线安全自动化测试",
            "description": "使用自动化工具执行CAN总线安全渗透测试，包括模糊测试、DoS测试和重放攻击",
            "type": "automation",
            "input_data": {
                "target_system": "CAN总线",
                "test_type": ["fuzzing", "dos", "replay"],
                "duration": "standard"
            }
        }
        
        # 发送任务创建请求
        result = self.create_task(task_data)
        
        if not result or not result.get("success"):
            return {"success": False, "error": "创建自动化测试任务失败"}
        
        task_id = result.get("data", {}).get("id")
        logger.info(f"创建的任务ID: {task_id}")
        logger.info(f"任务详情: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
        
        if not task_id:
            return {"success": False, "error": "未获取到任务ID"}
        
        # 执行任务
        execute_result = self.execute_task(task_id)
        if not execute_result or not execute_result.get("success"):
            logger.warning("执行任务可能失败，尝试继续检查任务状态")
        
        # 等待任务完成并获取结果
        max_retries = 300
        retry_interval = 2
        
        for i in range(max_retries):
            logger.info(f"等待自动化测试任务完成，第 {i+1}/{max_retries} 次检查")
            
            task_status = self.get_task_status(task_id)
            
            if not task_status or not task_status.get("success"):
                time.sleep(retry_interval)
                continue
                
            status = task_status.get("data", {}).get("status")
            
            if status == "completed":
                logger.info("自动化测试任务已完成")
                
                # 获取任务细节
                details = self.get_task_details(task_id)
                
                if not details or not details.get("success"):
                    return {"success": False, "error": "获取任务详情失败"}
                
                # 使用新的方法提取计划
                plan = self._extract_plan_from_response(details)
                subtasks = plan.get("subtasks", [])
                
                if subtasks:
                    logger.info(f"自动化测试智能体成功生成了动态计划，包含 {len(subtasks)} 个子任务")
                    return {
                        "success": True,
                        "agent_type": "automation",
                        "task_id": task_id,
                        "plan": plan,
                        "subtasks_count": len(subtasks)
                    }
                else:
                    logger.error("自动化测试智能体未能生成动态计划")
                    return {
                        "success": False,
                        "error": "未能生成动态计划",
                        "details": details.get("data", {})
                    }
            elif status == "failed":
                logger.error("自动化测试任务执行失败")
                return {"success": False, "error": "任务执行失败", "details": task_status.get("data", {})}
            
            # 等待后再次检查
            time.sleep(retry_interval)
        
        logger.error("等待自动化测试任务完成超时")
        return {"success": False, "error": "任务执行超时"}
    
    def test_report_dynamic_planning(self) -> Dict[str, Any]:
        """测试报告生成智能体的动态规划能力"""
        logger.info("开始测试报告生成智能体的动态规划能力")
        
        # 创建报告生成任务
        task_data = {
            "name": "生成车联网安全测试综合报告",
            "description": "基于TARA分析结果和自动化测试结果，生成一份全面的车联网安全测试报告",
            "type": "report",
            "input_data": {
                "report_type": "comprehensive",
                "include_sections": ["executive_summary", "threats", "vulnerabilities", "recommendations"],
                "format": "pdf"
            }
        }
        
        # 发送任务创建请求
        result = self.create_task(task_data)
        
        if not result or not result.get("success"):
            return {"success": False, "error": "创建报告生成任务失败"}
        
        task_id = result.get("data", {}).get("id")
        logger.info(f"创建的任务ID: {task_id}")
        logger.info(f"任务详情: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
        
        if not task_id:
            return {"success": False, "error": "未获取到任务ID"}
        
        # 执行任务
        execute_result = self.execute_task(task_id)
        if not execute_result or not execute_result.get("success"):
            logger.warning("执行任务可能失败，尝试继续检查任务状态")
        
        # 等待任务完成并获取结果
        max_retries = 300
        retry_interval = 2
        
        for i in range(max_retries):
            logger.info(f"等待报告生成任务完成，第 {i+1}/{max_retries} 次检查")
            
            task_status = self.get_task_status(task_id)
            
            if not task_status or not task_status.get("success"):
                time.sleep(retry_interval)
                continue
                
            status = task_status.get("data", {}).get("status")
            
            if status == "completed":
                logger.info("报告生成任务已完成")
                
                # 获取任务细节
                details = self.get_task_details(task_id)
                
                if not details or not details.get("success"):
                    return {"success": False, "error": "获取任务详情失败"}
                
                # 使用新的方法提取计划
                plan = self._extract_plan_from_response(details)
                subtasks = plan.get("subtasks", [])
                
                if subtasks:
                    logger.info(f"报告生成智能体成功生成了动态计划，包含 {len(subtasks)} 个子任务")
                    return {
                        "success": True,
                        "agent_type": "report",
                        "task_id": task_id,
                        "plan": plan,
                        "subtasks_count": len(subtasks)
                    }
                else:
                    logger.error("报告生成智能体未能生成动态计划")
                    return {
                        "success": False,
                        "error": "未能生成动态计划",
                        "details": details.get("data", {})
                    }
            elif status == "failed":
                logger.error("报告生成任务执行失败")
                return {"success": False, "error": "任务执行失败", "details": task_status.get("data", {})}
            
            # 等待后再次检查
            time.sleep(retry_interval)
        
        logger.error("等待报告生成任务完成超时")
        return {"success": False, "error": "任务执行超时"}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        start_time = datetime.now()
        logger.info(f"开始全面测试动态规划能力 - {start_time}")
        
        # 首先登录
        if not self.login():
            logger.error("登录失败，无法继续测试")
            return {
                "success": False,
                "error": "登录失败",
                "timestamp": start_time.isoformat()
            }
        
        results = {
            "timestamp": start_time.isoformat(),
            "tests": {}
        }
        
        # 测试TARA智能体
        results["tests"]["tara"] = self.test_tara_dynamic_planning()
        
        # 测试测试用例生成智能体
        results["tests"]["testcase"] = self.test_testcase_dynamic_planning()
        
        # 测试自动化测试智能体
        results["tests"]["automation"] = self.test_automation_dynamic_planning()
        
        # 测试报告生成智能体
        results["tests"]["report"] = self.test_report_dynamic_planning()
        
        # 计算成功率
        success_count = sum(1 for test in results["tests"].values() if test.get("success", False))
        total_tests = len(results["tests"])
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": success_count,
            "success_rate": f"{success_rate:.2f}%",
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        # 记录测试结果
        with open("dynamic_planning_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试完成，成功率: {success_rate:.2f}%")
        return results


if __name__ == "__main__":
    tester = AgentAPITester()
    results = tester.run_all_tests()
    sys.exit(0 if results["summary"]["successful_tests"] == results["summary"]["total_tests"] else 1) 