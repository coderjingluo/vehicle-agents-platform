#!/usr/bin/env python3
"""
KunlunSec AI Platform - TARA智能体测试脚本

测试TARA智能体的任务创建和执行功能，包括验证执行流数据库记录的创建。
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime

import httpx
import asyncpg

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tara_agent_test.log')
    ]
)

logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户信息（根据实际情况修改）
USER_ID = "de6eb440-2610-431a-8129-126d5ab64e8c"
API_TOKEN = "your-api-token-here"  # 如果API需要认证

# 数据库连接信息
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "admin"
DB_PASSWORD = "admin123"
DB_NAME = "kunlunsec"


async def verify_database_records(task_id, flow_execution_id):
    """验证数据库中的记录"""
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        # 查询任务记录
        task_record = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1", task_id
        )
        
        if not task_record:
            logger.error(f"数据库中未找到任务记录: {task_id}")
            return False
        
        # 查询执行流记录
        flow_record = await conn.fetchrow(
            "SELECT * FROM flow_executions WHERE id = $1", flow_execution_id
        )
        
        if not flow_record:
            logger.error(f"数据库中未找到执行流记录: {flow_execution_id}")
            return False
        
        logger.info(f"数据库记录验证成功: 任务ID {task_id}, 执行流ID {flow_execution_id}")
        logger.info(f"任务状态: {task_record['status']}")
        logger.info(f"执行流状态: {flow_record['status']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"数据库验证失败: {str(e)}")
        return False


async def create_task():
    """创建TARA分析任务"""
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
    
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/tasks/", 
                json=task_data, 
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                task_id = result["data"]["id"]
                logger.info(f"创建任务: {response.status_code}")
                logger.info(f"创建的任务ID: {task_id}")
                logger.info(f"任务详情: {json.dumps(result['data'], indent=2)}")
                return task_id
            else:
                logger.error(f"创建任务失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            return None


async def execute_task(task_id):
    """执行任务"""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/tasks/{task_id}/execute", 
                headers=headers,
                timeout=30.0
            )
            
            logger.info(f"执行任务: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                flow_id = result["data"]["flow_id"]
                return flow_id
            else:
                logger.error(f"错误响应: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            return None


async def get_task_status(task_id):
    """获取任务状态"""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/tasks/{task_id}", 
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result["data"]["status"]
                logger.info(f"任务状态: {status}")
                if "flow" in result["data"]:
                    logger.info(f"执行流信息: {json.dumps(result['data']['flow'], indent=2)}")
                return status, result["data"]
            else:
                logger.error(f"获取任务状态失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
                return None, None
                
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            return None, None


async def main():
    """主测试流程"""
    logger.info("开始测试TARA智能体的动态规划能力")
    
    # 创建任务
    task_id = await create_task()
    if not task_id:
        logger.error("创建任务失败，测试终止")
        return
        
    # 执行任务
    flow_id = await execute_task(task_id)
    if not flow_id:
        logger.warning("执行任务可能失败，尝试继续检查任务状态")
    
    # 验证数据库记录
    if flow_id:
        success = await verify_database_records(task_id, flow_id)
        if not success:
            logger.error("数据库验证失败，测试终止")
            return
    
    # 等待一段时间后检查任务状态（可选）
    await asyncio.sleep(5)
    status, task_data = await get_task_status(task_id)
    
    if status:
        logger.info(f"最终任务状态: {status}")
    else:
        logger.error("无法获取任务状态")


if __name__ == "__main__":
    asyncio.run(main()) 