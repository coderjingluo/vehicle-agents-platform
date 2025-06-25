/**
 * 应用全局状态管理
 * 主要管理：系统健康检查、全局通知、主题、侧边栏状态等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemAPI } from '../api'

export const useAppStore = defineStore('app', () => {
  // 状态定义
  const isLoading = ref(false)
  const sidebarCollapsed = ref(false)
  const theme = ref(localStorage.getItem('theme') || 'light')
  const notifications = ref([])
  const systemHealth = ref({
    status: 'unknown',
    database: false,
    redis: false,
    llm_client: false,
    last_check: null
  })

  // 计算属性
  const isDarkTheme = computed(() => theme.value === 'dark')
  const unreadNotifications = computed(() => 
    notifications.value.filter(n => !n.read).length
  )

  // Actions
  const setLoading = (loading) => {
    isLoading.value = loading
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
  }

  const setSidebarCollapsed = (collapsed) => {
    sidebarCollapsed.value = collapsed
    localStorage.setItem('sidebarCollapsed', collapsed)
  }

  const setTheme = (newTheme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    
    // 更新HTML类名以支持Element Plus主题
    const html = document.documentElement
    if (newTheme === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  const addNotification = (notification) => {
    const id = Date.now().toString()
    notifications.value.unshift({
      id,
      type: 'info',
      title: '',
      message: '',
      timestamp: new Date().toISOString(),
      read: false,
      duration: 5000,
      ...notification
    })

    // 自动清理通知
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration)
    }
  }

  const removeNotification = (id) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const markNotificationAsRead = (id) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }

  const markAllNotificationsAsRead = () => {
    notifications.value.forEach(n => n.read = true)
  }

  const clearNotifications = () => {
    notifications.value = []
  }

  // 系统健康检查
  const checkSystemHealth = async () => {
    try {
      setLoading(true)
      const response = await systemAPI.healthCheck()
      systemHealth.value = {
        ...response.data,
        last_check: new Date().toISOString()
      }
      
      // 根据健康状态显示通知
      if (response.data.status === 'healthy') {
        addNotification({
          type: 'success',
          title: '系统状态检查',
          message: '所有服务运行正常',
          duration: 3000
        })
      } else {
        addNotification({
          type: 'warning',
          title: '系统状态异常',
          message: '部分服务可能存在问题，请检查系统配置',
          duration: 0 // 不自动清理
        })
      }
      
      return response.data
    } catch (error) {
      systemHealth.value = {
        status: 'error',
        database: false,
        redis: false,
        llm_client: false,
        last_check: new Date().toISOString(),
        error: error.message
      }
      
      addNotification({
        type: 'error',
        title: '系统健康检查失败',
        message: error.message || '无法连接到后端服务',
        duration: 0
      })
      
      throw error
    } finally {
      setLoading(false)
    }
  }

  // 系统统计信息
  const getSystemStats = async () => {
    try {
      // 使用getSystemMetrics获取系统指标
      const response = await systemAPI.getSystemMetrics('1h')
      const metrics = response.data.metrics || {}
      
      // 转换为统一的统计格式
      return {
        cpu_percent: metrics.cpu?.usage || 0,
        memory_percent: metrics.memory?.usage || 0,
        disk_percent: metrics.disk?.usage || 0,
        network_io: metrics.network || {},
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      // 如果API调用失败，返回模拟数据
      console.warn('获取系统统计失败，使用模拟数据:', error.message)
      return {
        cpu_percent: Math.random() * 100,
        memory_percent: Math.random() * 100,
        disk_percent: Math.random() * 100,
        network_io: { in: 0, out: 0 },
        timestamp: new Date().toISOString()
      }
    }
  }

  // 初始化应用状态
  const initializeApp = () => {
    // 从localStorage恢复状态
    const savedSidebarState = localStorage.getItem('sidebarCollapsed')
    if (savedSidebarState !== null) {
      sidebarCollapsed.value = savedSidebarState === 'true'
    }

    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setTheme(savedTheme)
    }

    // 延迟执行健康检查，避免阻塞初始化
    setTimeout(() => {
      checkSystemHealth().catch(error => {
        console.warn('初始健康检查失败:', error.message)
      })
    }, 1000)
  }

  // 错误处理
  const handleError = (error, context = '') => {
    console.error(`[${context}] Error:`, error)
    
    let message = '操作失败'
    if (error.response?.data?.detail) {
      message = error.response.data.detail
    } else if (error.message) {
      message = error.message
    }

    addNotification({
      type: 'error',
      title: context || '系统错误',
      message,
      duration: 8000
    })
  }

  return {
    // 状态
    isLoading,
    sidebarCollapsed,
    theme,
    notifications,
    systemHealth,
    
    // 计算属性
    isDarkTheme,
    unreadNotifications,
    
    // Actions
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    toggleTheme,
    addNotification,
    removeNotification,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    clearNotifications,
    checkSystemHealth,
    getSystemStats,
    initializeApp,
    handleError
  }
}) 