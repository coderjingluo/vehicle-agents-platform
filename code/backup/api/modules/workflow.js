/**
 * 工作流API模块
 * 提供LangGraph工作流创建、执行、监控、管理等接口
 */

import { apiClient } from '../index'

const workflowAPI = {
  /**
   * 创建新的工作流实例
   * @param {Object} params - 工作流创建参数
   * @param {string} params.name - 工作流名称
   * @param {string} params.description - 工作流描述
   * @param {Object} params.config - 工作流配置
   */
  createWorkflow(params) {
    return apiClient.post('/workflows/create', params)
  },

  /**
   * 执行工作流
   * @param {string} workflowId - 工作流ID
   * @param {Object} params - 执行参数
   * @param {string} params.user_request - 用户请求
   * @param {Object} params.context - 上下文数据
   * @param {number} params.max_iterations - 最大迭代次数
   * @param {number} params.max_retries - 最大重试次数
   * @param {Object} params.config - 执行配置
   */
  executeWorkflow(workflowId, params) {
    return apiClient.post(`/workflows/${workflowId}/execute`, params)
  },

  /**
   * 流式执行工作流
   * @param {string} workflowId - 工作流ID
   * @param {Object} params - 执行参数
   */
  async streamWorkflowExecution(workflowId, params) {
    const response = await fetch(`${apiClient.defaults.baseURL}/workflows/${workflowId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...apiClient.defaults.headers,
      },
      body: JSON.stringify(params)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    return response.body.getReader()
  },

  /**
   * 获取工作流状态
   * @param {string} workflowId - 工作流ID
   */
  getWorkflowStatus(workflowId) {
    return apiClient.get(`/workflows/${workflowId}/status`)
  },

  /**
   * 获取工作流进度
   * @param {string} workflowId - 工作流ID
   */
  getWorkflowProgress(workflowId) {
    return apiClient.get(`/workflows/${workflowId}/progress`)
  },

  /**
   * 获取工作流执行历史
   * @param {string} workflowId - 工作流ID
   * @param {number} limit - 返回数量
   * @param {number} offset - 偏移量
   */
  getWorkflowHistory(workflowId, limit = 100, offset = 0) {
    return apiClient.get(`/workflows/${workflowId}/history`, {
      params: { limit, offset }
    })
  },

  /**
   * 暂停工作流
   * @param {string} workflowId - 工作流ID
   */
  pauseWorkflow(workflowId) {
    return apiClient.post(`/workflows/${workflowId}/pause`)
  },

  /**
   * 恢复工作流
   * @param {string} workflowId - 工作流ID
   */
  resumeWorkflow(workflowId) {
    return apiClient.post(`/workflows/${workflowId}/resume`)
  },

  /**
   * 停止工作流
   * @param {string} workflowId - 工作流ID
   */
  stopWorkflow(workflowId) {
    return apiClient.post(`/workflows/${workflowId}/stop`)
  },

  /**
   * 删除工作流
   * @param {string} workflowId - 工作流ID
   */
  deleteWorkflow(workflowId) {
    return apiClient.delete(`/workflows/${workflowId}`)
  },

  /**
   * 获取所有工作流列表
   * @param {number} limit - 返回数量
   * @param {number} offset - 偏移量
   * @param {string} status - 按状态筛选
   */
  getWorkflowsList(limit = 100, offset = 0, status = null) {
    const params = { limit, offset }
    if (status) params.status = status
    return apiClient.get('/workflows', { params })
  },

  /**
   * 批量执行工作流
   * @param {Array} workflowRequests - 工作流请求列表
   */
  batchExecute(workflowRequests) {
    return apiClient.post('/workflows/batch/execute', {
      workflow_requests: workflowRequests
    })
  },

  /**
   * 获取批次执行状态
   * @param {string} batchId - 批次ID
   */
  getBatchStatus(batchId) {
    return apiClient.get(`/workflows/batch/${batchId}/status`)
  },

  /**
   * 获取工作流统计信息
   * @param {number} days - 统计天数
   */
  getWorkflowStats(days = 7) {
    return apiClient.get('/workflows/stats', { params: { days } })
  },

  /**
   * 清理已完成的工作流
   * @param {number} daysOld - 清理多少天前的数据
   */
  cleanupCompletedWorkflows(daysOld = 30) {
    return apiClient.delete('/workflows/cleanup', {
      params: { days_old: daysOld }
    })
  },

  /**
   * 工作流模板管理
   */
  templates: {
    /**
     * 获取工作流模板列表
     */
    getList() {
      return apiClient.get('/workflows/templates')
    },

    /**
     * 创建工作流模板
     * @param {Object} template - 模板数据
     */
    create(template) {
      return apiClient.post('/workflows/templates', template)
    },

    /**
     * 获取模板详情
     * @param {string} templateId - 模板ID
     */
    getById(templateId) {
      return apiClient.get(`/workflows/templates/${templateId}`)
    },

    /**
     * 更新模板
     * @param {string} templateId - 模板ID
     * @param {Object} template - 模板数据
     */
    update(templateId, template) {
      return apiClient.put(`/workflows/templates/${templateId}`, template)
    },

    /**
     * 删除模板
     * @param {string} templateId - 模板ID
     */
    delete(templateId) {
      return apiClient.delete(`/workflows/templates/${templateId}`)
    },

    /**
     * 从模板创建工作流
     * @param {string} templateId - 模板ID
     * @param {Object} params - 实例化参数
     */
    instantiate(templateId, params) {
      return apiClient.post(`/workflows/templates/${templateId}/instantiate`, params)
    }
  },

  /**
   * 预定义的完整生命周期工作流
   */
  lifecycle: {
    /**
     * 执行完整车联网安全测试生命周期
     * @param {Object} params - 生命周期执行参数
     * @param {string} params.project_name - 项目名称
     * @param {string} params.system_description - 系统描述
     * @param {Array} params.requirements - 安全需求列表
     * @param {Object} params.config - 执行配置
     */
    executeFullLifecycle(params) {
      return apiClient.post('/workflows/lifecycle/full', params)
    },

    /**
     * 流式执行完整生命周期
     * @param {Object} params - 生命周期执行参数
     */
    async streamFullLifecycle(params) {
      const response = await fetch(`${apiClient.defaults.baseURL}/workflows/lifecycle/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...apiClient.defaults.headers,
        },
        body: JSON.stringify(params)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      return response.body.getReader()
    },

    /**
     * 执行TARA分析阶段
     * @param {Object} params - TARA分析参数
     */
    executeTARAPhase(params) {
      return apiClient.post('/workflows/lifecycle/tara', params)
    },

    /**
     * 执行测试用例生成阶段
     * @param {Object} params - 测试用例生成参数
     */
    executeTestCasePhase(params) {
      return apiClient.post('/workflows/lifecycle/test-case', params)
    },

    /**
     * 执行自动化测试阶段
     * @param {Object} params - 自动化测试参数
     */
    executeAutomationPhase(params) {
      return apiClient.post('/workflows/lifecycle/automation', params)
    },

    /**
     * 执行报告生成阶段
     * @param {Object} params - 报告生成参数
     */
    executeReportPhase(params) {
      return apiClient.post('/workflows/lifecycle/report', params)
    },

    /**
     * 获取生命周期阶段状态
     * @param {string} executionId - 执行ID
     */
    getPhaseStatus(executionId) {
      return apiClient.get(`/workflows/lifecycle/${executionId}/phases`)
    }
  },

  /**
   * 工作流监控和分析
   */
  monitoring: {
    /**
     * 获取活跃工作流统计
     */
    getActiveWorkflowStats() {
      return workflowAPI.getWorkflowStats(1).then(res => {
        const stats = res.data || {}
        return {
          running: stats.running || 0,
          paused: stats.paused || 0,
          waiting: stats.waiting || 0,
          total_active: (stats.running || 0) + (stats.paused || 0) + (stats.waiting || 0)
        }
      })
    },

    /**
     * 获取工作流性能指标
     * @param {number} days - 统计天数
     */
    getPerformanceMetrics(days = 7) {
      return workflowAPI.getWorkflowStats(days).then(res => {
        const stats = res.data || {}
        return {
          total_executions: stats.total_executions || 0,
          successful_executions: stats.successful_executions || 0,
          failed_executions: stats.failed_executions || 0,
          average_duration: stats.average_duration || 0,
          success_rate: stats.success_rate || 0
        }
      })
    },

    /**
     * 获取工作流瓶颈分析
     */
    getBottleneckAnalysis() {
      return apiClient.get('/workflows/analysis/bottlenecks')
    },

    /**
     * 获取资源使用情况
     */
    getResourceUsage() {
      return apiClient.get('/workflows/analysis/resources')
    },

    /**
     * 获取错误模式分析
     */
    getErrorPatterns() {
      return apiClient.get('/workflows/analysis/errors')
    }
  },

  /**
   * 工作流配置管理
   */
  config: {
    /**
     * 获取默认工作流配置
     */
    getDefaultConfig() {
      return apiClient.get('/workflows/config/default')
    },

    /**
     * 更新默认配置
     * @param {Object} config - 配置数据
     */
    updateDefaultConfig(config) {
      return apiClient.put('/workflows/config/default', config)
    },

    /**
     * 获取工作流限制配置
     */
    getLimitsConfig() {
      return apiClient.get('/workflows/config/limits')
    },

    /**
     * 更新限制配置
     * @param {Object} limits - 限制配置
     */
    updateLimitsConfig(limits) {
      return apiClient.put('/workflows/config/limits', limits)
    },

    /**
     * 验证工作流配置
     * @param {Object} config - 要验证的配置
     */
    validateConfig(config) {
      return apiClient.post('/workflows/config/validate', config)
    }
  }
}

export default workflowAPI

// 兼容性方法和便利方法
workflowAPI.listWorkflows = workflowAPI.getWorkflowsList
workflowAPI.restartWorkflow = workflowAPI.resumeWorkflow

// 添加获取最近工作流的便利方法
workflowAPI.getRecentWorkflows = function(limit = 10) {
  return this.getWorkflowsList(limit, 0).then(res => {
    if (res.data && res.data.workflows) {
      // 按创建时间排序，返回最近的工作流
      return res.data.workflows.sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
    }
    return []
  })
}

// 添加执行简单工作流的方法（用于向后兼容）
workflowAPI.executeSimpleWorkflow = function(params) {
  // 创建一个临时工作流然后执行
  return this.createWorkflow({
    name: params.name || 'Temporary Workflow',
    description: params.description || 'Auto-generated workflow',
    config: params
  }).then(createRes => {
    if (createRes.data && createRes.data.workflow_id) {
      return this.executeWorkflow(createRes.data.workflow_id, params)
    }
    throw new Error('Failed to create workflow')
  })
} 