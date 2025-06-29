"""
KunlunSec AI Platform - WebSocket端点

提供WebSocket连接端点，用于实时通信和状态更新。
"""

import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.security import get_current_user, get_token_from_query, get_current_user_from_token
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.flow import Flow

# 创建路由器
ws_router = APIRouter()

# WebSocket连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 任务执行连接 {task_id: {user_id: WebSocket}}
        self.task_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 通知连接 {user_id: WebSocket}
        self.notification_connections: Dict[str, WebSocket] = {}
    
    async def connect_task(self, websocket: WebSocket, task_id: str, user_id: str):
        """连接到任务执行WebSocket"""
        await websocket.accept()
        
        if task_id not in self.task_connections:
            self.task_connections[task_id] = {}
        
        self.task_connections[task_id][user_id] = websocket
    
    async def disconnect_task(self, task_id: str, user_id: str):
        """断开任务执行WebSocket连接"""
        if task_id in self.task_connections and user_id in self.task_connections[task_id]:
            del self.task_connections[task_id][user_id]
            
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
    
    async def connect_notification(self, websocket: WebSocket, user_id: str):
        """连接到通知WebSocket"""
        await websocket.accept()
        self.notification_connections[user_id] = websocket
    
    async def disconnect_notification(self, user_id: str):
        """断开通知WebSocket连接"""
        if user_id in self.notification_connections:
            del self.notification_connections[user_id]
    
    async def broadcast_task_update(self, task_id: str, message: Dict[str, Any]):
        """广播任务更新消息"""
        if task_id in self.task_connections:
            for user_id, connection in self.task_connections[task_id].items():
                try:
                    await connection.send_json(message)
                except Exception:
                    # 连接可能已关闭
                    await self.disconnect_task(task_id, user_id)
    
    async def send_notification(self, user_id: str, message: Dict[str, Any]):
        """发送通知消息给指定用户"""
        if user_id in self.notification_connections:
            try:
                await self.notification_connections[user_id].send_json(message)
            except Exception:
                # 连接可能已关闭
                await self.disconnect_notification(user_id)
    
    async def broadcast_notification(self, message: Dict[str, Any], exclude_user_id: Optional[str] = None):
        """广播通知消息给所有用户"""
        for user_id, connection in list(self.notification_connections.items()):
            if exclude_user_id and user_id == exclude_user_id:
                continue
                
            try:
                await connection.send_json(message)
            except Exception:
                # 连接可能已关闭
                await self.disconnect_notification(user_id)

# 创建连接管理器实例
manager = ConnectionManager()

@ws_router.websocket("/task_execution/{task_id}")
async def websocket_task_execution(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    任务执行WebSocket端点
    
    用于实时接收任务执行状态更新
    """
    try:
        # 验证token
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 检查任务是否存在
        from sqlalchemy.future import select
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        
        if not task:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 建立连接
        await manager.connect_task(websocket, task_id, user.id)
        
        try:
            # 发送初始状态
            await websocket.send_json({
                "type": "task_status_update",
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "current_step": task.current_step,
                "timestamp": task.updated_at.isoformat() if task.updated_at else None
            })
            
            # 等待客户端消息
            while True:
                data = await websocket.receive_json()
                
                # 处理订阅请求
                if data.get("type") == "subscribe" and data.get("channel") == "task_execution":
                    # 已经订阅，无需操作
                    pass
                
        except WebSocketDisconnect:
            await manager.disconnect_task(task_id, user.id)
            
    except Exception as e:
        # 处理连接错误
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass

@ws_router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    系统通知WebSocket端点
    
    用于接收系统通知和MCP连接状态变化
    """
    try:
        # 验证token
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 建立连接
        await manager.connect_notification(websocket, user.id)
        
        try:
            # 发送欢迎消息
            await websocket.send_json({
                "type": "system_message",
                "message": "已连接到通知服务",
                "timestamp": datetime.now().isoformat()
            })
            
            # 等待客户端消息
            while True:
                await websocket.receive_text()  # 保持连接活跃
                
        except WebSocketDisconnect:
            await manager.disconnect_notification(user.id)
            
    except Exception as e:
        # 处理连接错误
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass

# 以下函数供其他模块调用，用于发送WebSocket消息

async def send_task_status_update(task_id: str, status: str, progress: int, current_step: str):
    """发送任务状态更新"""
    await manager.broadcast_task_update(task_id, {
        "type": "task_status_update",
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "current_step": current_step,
        "timestamp": datetime.now().isoformat()
    })

async def send_step_completed(task_id: str, step_id: str, step_name: str, result: Dict[str, Any], duration: int):
    """发送步骤完成事件"""
    await manager.broadcast_task_update(task_id, {
        "type": "step_completed",
        "task_id": task_id,
        "step_id": step_id,
        "step_name": step_name,
        "result": result,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    })

async def send_notification(user_id: str, level: str, title: str, message: str):
    """发送通知给指定用户"""
    await manager.send_notification(user_id, {
        "type": "notification",
        "level": level,
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })

async def broadcast_notification(level: str, title: str, message: str, exclude_user_id: Optional[str] = None):
    """广播通知给所有用户"""
    await manager.broadcast_notification({
        "type": "notification",
        "level": level,
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }, exclude_user_id)

async def broadcast_mcp_status_change(connection_id: str, name: str, status: str):
    """广播MCP连接状态变化"""
    await manager.broadcast_notification({
        "type": "mcp_status_change",
        "connection_id": connection_id,
        "name": name,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }) 