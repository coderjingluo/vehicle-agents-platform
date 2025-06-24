/**
 * API接口对接层 - 主入口
 * 车联网安全测试生命周期管理平台前端API
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const WEBSOCKET_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token（如果有）
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求时间戳
    config.metadata = { startTime: new Date() }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 计算请求耗时
    const endTime = new Date()
    const duration = endTime - response.config.metadata.startTime
    console.log(`API请求耗时: ${duration}ms - ${response.config.url}`)
    
    return response
  },
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    
    // 显示错误消息
    ElMessage.error(message)
    
    // 根据状态码处理特定错误
    if (error.response?.status === 401) {
      // 未授权，清除token并跳转登录
      localStorage.removeItem('auth_token')
      // router.push('/login') // It's better to handle this in the store or component
    }
    
    return Promise.reject(error)
  }
)

// 导出API客户端和URL配置
export { apiClient, API_BASE_URL, WEBSOCKET_URL }

// 导出具体API模块
export { default as systemAPI } from './modules/system'
export { default as workflowAPI } from './modules/workflow'
export { default as agentsAPI } from './modules/agents'
export { default as knowledgeAPI } from './modules/knowledge'
export { default as modelsAPI } from './modules/models'
export { default as demoAPI } from './modules/demo'
export { default as authAPI } from './modules/auth'

/**
 * @description 设置认证token
 * @param {string} token
 */
export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
} 