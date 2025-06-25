/**
 * 企业级WebSocket连接管理
 * 支持自动重连、心跳保活、多连接管理、错误恢复
 */

import { WEBSOCKET_URL } from '../api'

export class WebSocketManager {
  constructor() {
    this.connections = new Map()
    this.reconnectIntervals = new Map()
    this.heartbeatIntervals = new Map()
    this.messageHandlers = new Map()
    this.defaultOptions = {
      reconnectDelay: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      autoReconnect: true
    }
  }

  /**
   * 创建WebSocket连接
   * @param {string} connectionId 连接ID
   * @param {string} endpoint WebSocket端点
   * @param {object} options 连接选项
   * @param {function} messageHandler 消息处理函数
   */
  createConnection(connectionId, endpoint, options = {}, messageHandler = null) {
    const config = { ...this.defaultOptions, ...options }
    const url = `${WEBSOCKET_URL}${endpoint}`

    console.log(`[WebSocket] 创建连接: ${connectionId} -> ${url}`)

    const connection = {
      id: connectionId,
      url,
      config,
      socket: null,
      status: 'connecting',
      reconnectAttempts: 0,
      lastConnectTime: null,
      lastMessageTime: null
    }

    this.connections.set(connectionId, connection)
    
    if (messageHandler) {
      this.messageHandlers.set(connectionId, messageHandler)
    }

    this._connect(connectionId)
    return connectionId
  }

  /**
   * 内部连接方法
   */
  _connect(connectionId) {
    const connection = this.connections.get(connectionId)
    if (!connection) return

    try {
      // 清理旧连接
      if (connection.socket) {
        connection.socket.close()
      }

      connection.socket = new WebSocket(connection.url)
      connection.status = 'connecting'

      // 连接成功
      connection.socket.onopen = (event) => {
        console.log(`[WebSocket] 连接成功: ${connectionId}`)
        connection.status = 'connected'
        connection.reconnectAttempts = 0
        connection.lastConnectTime = new Date()

        // 启动心跳
        this._startHeartbeat(connectionId)

        // 触发连接事件
        this._emit(connectionId, 'connected', { connectionId, event })
      }

      // 接收消息
      connection.socket.onmessage = (event) => {
        connection.lastMessageTime = new Date()
        
        try {
          const data = JSON.parse(event.data)
          console.log(`[WebSocket] 收到消息: ${connectionId}`, data)
          
          // 处理心跳响应
          if (data.type === 'pong') {
            return
          }

          // 调用消息处理器
          const handler = this.messageHandlers.get(connectionId)
          if (handler) {
            handler(data)
          }

          // 触发消息事件
          this._emit(connectionId, 'message', data)
        } catch (error) {
          console.error(`[WebSocket] 消息解析失败: ${connectionId}`, error)
          this._emit(connectionId, 'error', { type: 'parse_error', error })
        }
      }

      // 连接关闭
      connection.socket.onclose = (event) => {
        console.log(`[WebSocket] 连接关闭: ${connectionId}`, event.code, event.reason)
        connection.status = 'disconnected'
        
        // 停止心跳
        this._stopHeartbeat(connectionId)

        // 触发断开事件
        this._emit(connectionId, 'disconnected', { connectionId, event })

        // 自动重连
        if (connection.config.autoReconnect && 
            connection.reconnectAttempts < connection.config.maxReconnectAttempts) {
          this._scheduleReconnect(connectionId)
        }
      }

      // 连接错误
      connection.socket.onerror = (error) => {
        console.error(`[WebSocket] 连接错误: ${connectionId}`, error)
        connection.status = 'error'
        
        // 触发错误事件
        this._emit(connectionId, 'error', { connectionId, error })
      }

    } catch (error) {
      console.error(`[WebSocket] 创建连接失败: ${connectionId}`, error)
      connection.status = 'error'
      this._emit(connectionId, 'error', { connectionId, error })
    }
  }

  /**
   * 发送消息
   */
  send(connectionId, message) {
    const connection = this.connections.get(connectionId)
    if (!connection || !connection.socket) {
      console.warn(`[WebSocket] 连接不存在: ${connectionId}`)
      return false
    }

    if (connection.socket.readyState !== WebSocket.OPEN) {
      console.warn(`[WebSocket] 连接未就绪: ${connectionId}`)
      return false
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message)
      connection.socket.send(data)
      console.log(`[WebSocket] 发送消息: ${connectionId}`, message)
      return true
    } catch (error) {
      console.error(`[WebSocket] 发送消息失败: ${connectionId}`, error)
      return false
    }
  }

  /**
   * 关闭连接
   */
  closeConnection(connectionId) {
    const connection = this.connections.get(connectionId)
    if (!connection) return

    console.log(`[WebSocket] 手动关闭连接: ${connectionId}`)
    
    // 停止重连和心跳
    connection.config.autoReconnect = false
    this._stopReconnect(connectionId)
    this._stopHeartbeat(connectionId)

    // 关闭连接
    if (connection.socket) {
      connection.socket.close()
    }

    // 清理资源
    this.connections.delete(connectionId)
    this.messageHandlers.delete(connectionId)
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus(connectionId) {
    const connection = this.connections.get(connectionId)
    if (!connection) return 'not_found'
    return connection.status
  }

  /**
   * 获取所有连接状态
   */
  getAllConnections() {
    const result = {}
    for (const [id, connection] of this.connections) {
      result[id] = {
        id: connection.id,
        status: connection.status,
        url: connection.url,
        reconnectAttempts: connection.reconnectAttempts,
        lastConnectTime: connection.lastConnectTime,
        lastMessageTime: connection.lastMessageTime
      }
    }
    return result
  }

  /**
   * 设置消息处理器
   */
  setMessageHandler(connectionId, handler) {
    this.messageHandlers.set(connectionId, handler)
  }

  /**
   * 启动心跳
   */
  _startHeartbeat(connectionId) {
    const connection = this.connections.get(connectionId)
    if (!connection || !connection.config.heartbeatInterval) return

    this._stopHeartbeat(connectionId)

    const interval = setInterval(() => {
      if (this.getConnectionStatus(connectionId) === 'connected') {
        this.send(connectionId, { type: 'ping', timestamp: Date.now() })
      }
    }, connection.config.heartbeatInterval)

    this.heartbeatIntervals.set(connectionId, interval)
  }

  /**
   * 停止心跳
   */
  _stopHeartbeat(connectionId) {
    const interval = this.heartbeatIntervals.get(connectionId)
    if (interval) {
      clearInterval(interval)
      this.heartbeatIntervals.delete(connectionId)
    }
  }

  /**
   * 计划重连
   */
  _scheduleReconnect(connectionId) {
    const connection = this.connections.get(connectionId)
    if (!connection) return

    this._stopReconnect(connectionId)

    connection.reconnectAttempts++
    const delay = connection.config.reconnectDelay * Math.pow(2, connection.reconnectAttempts - 1)

    console.log(`[WebSocket] 计划重连: ${connectionId}, 尝试次数: ${connection.reconnectAttempts}, 延迟: ${delay}ms`)

    const timeout = setTimeout(() => {
      console.log(`[WebSocket] 开始重连: ${connectionId}`)
      this._connect(connectionId)
    }, delay)

    this.reconnectIntervals.set(connectionId, timeout)
  }

  /**
   * 停止重连
   */
  _stopReconnect(connectionId) {
    const timeout = this.reconnectIntervals.get(connectionId)
    if (timeout) {
      clearTimeout(timeout)
      this.reconnectIntervals.delete(connectionId)
    }
  }

  /**
   * 触发事件（占位符，可以集成事件总线）
   */
  _emit(connectionId, event, data) {
    console.log(`[WebSocket] 事件: ${connectionId} -> ${event}`, data)
    // 这里可以集成 Vue 的事件系统或其他事件总线
  }

  /**
   * 清理所有连接
   */
  cleanup() {
    console.log('[WebSocket] 清理所有连接')
    for (const connectionId of this.connections.keys()) {
      this.closeConnection(connectionId)
    }
  }
}

// 创建全局实例
export const webSocketManager = new WebSocketManager()

// 工作流监控专用函数
export function createWorkflowMonitor(workflowId, handlers = {}) {
  const connectionId = `workflow_${workflowId}`
  const endpoint = `/workflow/${workflowId}`

  const messageHandler = (data) => {
    switch (data.type) {
      case 'workflow_status':
        handlers.onStatus?.(data)
        break
      case 'agent_start':
        handlers.onAgentStart?.(data)
        break
      case 'agent_progress':
        handlers.onProgress?.(data)
        break
      case 'agent_complete':
        handlers.onAgentComplete?.(data)
        break
      case 'workflow_complete':
        handlers.onComplete?.(data)
        break
      case 'workflow_error':
        handlers.onError?.(data)
        break
      default:
        handlers.onMessage?.(data)
    }
  }

  const options = {
    autoReconnect: true,
    maxReconnectAttempts: 3,
    heartbeatInterval: 30000
  }

  webSocketManager.createConnection(connectionId, endpoint, options, messageHandler)

  return {
    connectionId,
    close: () => webSocketManager.closeConnection(connectionId),
    send: (message) => webSocketManager.send(connectionId, message),
    getStatus: () => webSocketManager.getConnectionStatus(connectionId)
  }
}

// Vue组合式函数
export function useWebSocket(endpoint, options = {}) {
  const { ref, onMounted, onUnmounted } = Vue || {}
  
  if (!ref) {
    // 如果不在Vue环境中，返回简化版本
    return {
      isConnected: { value: false },
      send: () => false,
      close: () => {}
    }
  }

  const isConnected = ref(false)
  const lastMessage = ref(null)
  const connectionId = ref(null)

  const connect = () => {
    const id = `use_websocket_${Date.now()}`
    connectionId.value = id

    const messageHandler = (data) => {
      lastMessage.value = data
      options.onMessage?.(data)
    }

    webSocketManager.createConnection(id, endpoint, {
      autoReconnect: true,
      ...options
    }, messageHandler)

    // 监听连接状态
    const checkStatus = () => {
      const status = webSocketManager.getConnectionStatus(id)
      isConnected.value = status === 'connected'
    }

    const statusInterval = setInterval(checkStatus, 1000)
    
    onUnmounted?.(() => {
      clearInterval(statusInterval)
      webSocketManager.closeConnection(id)
    })
  }

  const send = (message) => {
    if (connectionId.value) {
      return webSocketManager.send(connectionId.value, message)
    }
    return false
  }

  const close = () => {
    if (connectionId.value) {
      webSocketManager.closeConnection(connectionId.value)
    }
  }

  onMounted?.(connect)

  return {
    isConnected,
    lastMessage,
    send,
    close
  }
} 