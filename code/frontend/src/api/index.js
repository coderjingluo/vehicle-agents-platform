/**
 * API接口对接层 - 主入口
 * 车联网安全测试生命周期管理平台前端API
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// API基础配置
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
export const WEBSOCKET_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://192.168.136.129:8000/ws'

// 创建axios实例
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
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
    const { response } = error
    
    if (response) {
      // Handle different error statuses
      switch (response.status) {
        case 401:
          // Unauthorized, redirect to login
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_info')
          ElMessage.error('登录已过期，请重新登录')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1000)
          break
        case 403:
          // Forbidden
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          // Not found
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // Validation errors
          const errors = response.data.errors || {}
          const firstError = Object.values(errors)[0]
          if (firstError) {
            ElMessage.error(firstError[0])
          } else {
            ElMessage.error('表单验证失败')
          }
          break
        case 429:
          // Too many requests
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          // Server error
          ElMessage.error('服务器错误，请稍后再试')
          break
        default:
          ElMessage.error('请求失败，请稍后再试')
      }
    } else {
      // Network error or other issues
      ElMessage.error('网络错误，请检查您的网络连接')
    }
    
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
export { apiClient, BASE_URL }

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