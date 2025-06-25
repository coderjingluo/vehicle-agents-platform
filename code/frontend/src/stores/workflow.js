/**
 * 工作流状态管理
 * 主要管理：工作流执行、实时监控、历史记录等
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workflowAPI, agentsAPI } from '../api'
import { useAppStore } from './app'

export const useWorkflowStore = defineStore('workflow', () => {
  const appStore = useAppStore()

  // 状态定义
  const currentWorkflow = ref(null)
  const workflowHistory = ref([])
  const executionProgress = ref(0)
  const isExecuting = ref(false)
  const currentStep = ref('')
  const executionLogs = ref([])
  const executionResults = ref({})
  const webSocketConnection = ref(null)

  // 计算属性
  const hasActiveWorkflow = computed(() => !!currentWorkflow.value)
  const canExecute = computed(() => !isExecuting.value)
  const executionStatus = computed(() => {
    if (!currentWorkflow.value) return 'idle'
    if (isExecuting.value) return 'running'
    if (executionProgress.value === 100) return 'completed'
    if (executionProgress.value > 0) return 'paused'
    return 'pending'
  })

  // Actions
  const setCurrentWorkflow = (workflow) => {
    currentWorkflow.value = workflow
  }

  const clearCurrentWorkflow = () => {
    currentWorkflow.value = null
    executionProgress.value = 0
    currentStep.value = ''
    executionLogs.value = []
    executionResults.value = {}
  }

  const updateExecutionProgress = (progress, step = '') => {
    executionProgress.value = Math.max(0, Math.min(100, progress))
    if (step) {
      currentStep.value = step
    }
  }

  const addExecutionLog = (log) => {
    const logEntry = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      type: 'info',
      ...log
    }
    executionLogs.value.push(logEntry)
  }

  const clearExecutionLogs = () => {
    executionLogs.value = []
  }

  // 执行工作流
  const executeWorkflow = async (workflowConfig) => {
    try {
      isExecuting.value = true
      executionProgress.value = 0
      currentStep.value = '准备执行'
      clearExecutionLogs()

      addExecutionLog({
        type: 'info',
        message: '开始执行工作流',
        data: workflowConfig
      })

      const response = await workflowAPI.executeWorkflow(workflowConfig)
      
      setCurrentWorkflow({
        id: response.data.workflow_id,
        config: workflowConfig,
        startTime: new Date().toISOString(),
        status: 'running'
      })

      addExecutionLog({
        type: 'success',
        message: `工作流已启动，ID: ${response.data.workflow_id}`,
        data: response.data
      })

      // 如果支持WebSocket，建立连接监控进度
      if (response.data.workflow_id) {
        connectWorkflowMonitor(response.data.workflow_id)
      }

      return response.data
    } catch (error) {
      isExecuting.value = false
      addExecutionLog({
        type: 'error',
        message: '工作流执行失败',
        data: error.response?.data || error.message
      })
      appStore.handleError(error, '工作流执行')
      throw error
    }
  }

  // 执行单个智能体
  const executeAgent = async (agentType, params) => {
    try {
      addExecutionLog({
        type: 'info',
        message: `开始执行${agentType}智能体`,
        data: params
      })

      const response = await agentsAPI[agentType].execute(params)
      
      executionResults.value[agentType] = response.data

      addExecutionLog({
        type: 'success',
        message: `${agentType}智能体执行完成`,
        data: response.data
      })

      return response.data
    } catch (error) {
      addExecutionLog({
        type: 'error',
        message: `${agentType}智能体执行失败`,
        data: error.response?.data || error.message
      })
      appStore.handleError(error, `${agentType}智能体执行`)
      throw error
    }
  }

  // 流式执行智能体
  const streamExecuteAgent = async (agentType, params, onProgress) => {
    try {
      addExecutionLog({
        type: 'info',
        message: `开始流式执行${agentType}智能体`,
        data: params
      })

      const response = await agentsAPI[agentType].streamExecute(params, (data) => {
        // 处理流式数据
        if (data.type === 'progress') {
          updateExecutionProgress(data.progress, data.step)
        } else if (data.type === 'log') {
          addExecutionLog({
            type: data.level || 'info',
            message: data.message,
            data: data.data
          })
        }
        
        // 调用外部进度回调
        if (onProgress) {
          onProgress(data)
        }
      })

      executionResults.value[agentType] = response.data

      addExecutionLog({
        type: 'success',
        message: `${agentType}智能体流式执行完成`,
        data: response.data
      })

      return response.data
    } catch (error) {
      addExecutionLog({
        type: 'error',
        message: `${agentType}智能体流式执行失败`,
        data: error.response?.data || error.message
      })
      appStore.handleError(error, `${agentType}智能体流式执行`)
      throw error
    }
  }

  // 获取工作流状态
  const getWorkflowStatus = async (workflowId) => {
    try {
      const response = await workflowAPI.getWorkflowStatus(workflowId)
      return response.data
    } catch (error) {
      appStore.handleError(error, '获取工作流状态')
      throw error
    }
  }

  // 获取工作流历史
  const loadWorkflowHistory = async (page = 1, limit = 20) => {
    try {
      const response = await workflowAPI.getWorkflowHistory({ page, limit })
      workflowHistory.value = response.data.items
      return response.data
    } catch (error) {
      appStore.handleError(error, '加载工作流历史')
      throw error
    }
  }

  // WebSocket连接管理
  const connectWorkflowMonitor = (workflowId) => {
    // WebSocket连接逻辑将在utils/websocket.js中实现
    // 这里只是占位符
    console.log(`连接工作流监控: ${workflowId}`)
  }

  const disconnectWorkflowMonitor = () => {
    if (webSocketConnection.value) {
      webSocketConnection.value.close()
      webSocketConnection.value = null
    }
  }

  // 处理WebSocket消息
  const handleWorkflowMessage = (message) => {
    switch (message.type) {
      case 'workflow_status':
        updateExecutionProgress(message.progress, message.current_step)
        addExecutionLog({
          type: 'info',
          message: `工作流状态更新: ${message.status}`,
          data: message
        })
        break
      
      case 'agent_start':
        currentStep.value = `执行${message.agent_type}智能体`
        addExecutionLog({
          type: 'info',
          message: `开始执行${message.agent_type}智能体`,
          data: message
        })
        break
      
      case 'agent_complete':
        executionResults.value[message.agent_type] = message.result
        addExecutionLog({
          type: 'success',
          message: `${message.agent_type}智能体执行完成`,
          data: message.result
        })
        break
      
      case 'workflow_complete':
        isExecuting.value = false
        executionProgress.value = 100
        currentStep.value = '执行完成'
        addExecutionLog({
          type: 'success',
          message: '工作流执行完成',
          data: message.result
        })
        
        // 添加到历史记录
        if (currentWorkflow.value) {
          workflowHistory.value.unshift({
            ...currentWorkflow.value,
            endTime: new Date().toISOString(),
            status: 'completed',
            result: message.result
          })
        }
        break
      
      case 'workflow_error':
        isExecuting.value = false
        addExecutionLog({
          type: 'error',
          message: '工作流执行出错',
          data: message.error
        })
        appStore.addNotification({
          type: 'error',
          title: '工作流执行失败',
          message: message.error
        })
        break
      
      default:
        console.log('未知的工作流消息类型:', message.type)
    }
  }

  // 停止工作流执行
  const stopWorkflow = async (workflowId) => {
    try {
      await workflowAPI.stopWorkflow(workflowId)
      isExecuting.value = false
      addExecutionLog({
        type: 'warning',
        message: '工作流已停止'
      })
    } catch (error) {
      appStore.handleError(error, '停止工作流')
      throw error
    }
  }

  // 重置工作流状态
  const resetWorkflow = () => {
    isExecuting.value = false
    executionProgress.value = 0
    currentStep.value = ''
    clearExecutionLogs()
    clearCurrentWorkflow()
    disconnectWorkflowMonitor()
  }

  return {
    // 状态
    currentWorkflow,
    workflowHistory,
    executionProgress,
    isExecuting,
    currentStep,
    executionLogs,
    executionResults,
    webSocketConnection,
    
    // 计算属性
    hasActiveWorkflow,
    canExecute,
    executionStatus,
    
    // Actions
    setCurrentWorkflow,
    clearCurrentWorkflow,
    updateExecutionProgress,
    addExecutionLog,
    clearExecutionLogs,
    executeWorkflow,
    executeAgent,
    streamExecuteAgent,
    getWorkflowStatus,
    loadWorkflowHistory,
    connectWorkflowMonitor,
    disconnectWorkflowMonitor,
    handleWorkflowMessage,
    stopWorkflow,
    resetWorkflow
  }
}) 