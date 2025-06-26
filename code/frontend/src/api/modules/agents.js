/**
 * 智能体API模块
 * 提供智能体执行、状态查询、工具管理等接口
 */

import { apiClient } from '../index'

const agentsAPI = {
  /**
   * 获取所有智能体列表
   */
  getAgentsList() {
    return apiClient.get('/agents')
  },

  /**
   * 初始化智能体实例
   * @param {string} agentType - 智能体类型
   */
  initializeAgent(agentType) {
    return apiClient.post(`/agents/${agentType}/initialize`)
  },

  /**
   * 终止智能体实例
   * @param {string} agentType - 智能体类型
   */
  terminateAgent(agentType) {
    return apiClient.delete(`/agents/${agentType}/terminate`)
  },

  /**
   * 执行指定智能体
   * @param {string} agentType - 智能体类型 (tara|test_case|automation_test|report_analysis|knowledge_base)
   * @param {Object} params - 执行参数
   * @param {string} params.user_request - 用户请求内容
   * @param {Object} params.context - 执行上下文
   * @param {number} params.timeout - 超时时间(秒)
   * @param {boolean} params.stream - 是否启用流式响应
   * @param {string} params.priority - 优先级
   * @param {Object} params.metadata - 请求元数据
   * @param {boolean} params.enable_planning - 启用智能步骤分配
   * @param {boolean} params.step_by_step - 启用步骤化执行
   * @param {boolean} params.chat_mode - 启用聊天模式
   * @param {Object} params.agent_config - 智能体特定配置
   */
  executeAgent(agentType, params) {
    return apiClient.post(`/agents/${agentType}/execute`, params)
  },

  /**
   * 流式执行智能体
   * @param {string} agentType - 智能体类型
   * @param {Object} params - 执行参数
   */
  async streamAgentExecution(agentType, params) {
    // 使用apiClient的baseURL，确保URL路径一致
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://192.168.136.129:8000'
    // 使用完整的API路径
    const url = `${baseUrl}/api/v1/agents/${agentType}/stream`
    
    console.log(`Streaming agent execution to: ${url}`)
    
    const response = await fetch(url, {
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
   * 获取智能体状态
   * @param {string} agentType - 智能体类型
   */
  getAgentStatus(agentType) {
    return apiClient.get(`/agents/${agentType}/status`)
  },

  /**
   * 获取智能体性能指标
   * @param {string} agentType - 智能体类型
   * @param {number} days - 统计天数
   */
  getAgentMetrics(agentType, days = 7) {
    return apiClient.get(`/agents/${agentType}/metrics`, { params: { days } })
  },

  /**
   * 获取智能体可用工具
   * @param {string} agentType - 智能体类型
   */
  getAgentTools(agentType) {
    return apiClient.get(`/agents/${agentType}/tools`)
  },

  /**
   * 获取活跃任务列表
   * @param {string} agentType - 按智能体类型筛选
   * @param {number} limit - 返回数量限制
   * @param {number} offset - 偏移量
   */
  getActiveTasks(agentType = null, limit = 100, offset = 0) {
    const params = { limit, offset }
    if (agentType) params.agent_type = agentType
    return apiClient.get('/agents/tasks/active', { params })
  },

  /**
   * 获取任务详细信息
   * @param {string} taskId - 任务ID
   */
  getTaskDetail(taskId) {
    return apiClient.get(`/agents/tasks/${taskId}`)
  },

  /**
   * 取消任务执行
   * @param {string} taskId - 任务ID
   */
  cancelTask(taskId) {
    return apiClient.delete(`/agents/tasks/${taskId}`)
  },

  /**
   * 批量执行智能体任务
   * @param {Array} requests - 任务请求列表
   */
  batchExecute(requests) {
    return apiClient.post('/agents/batch/execute', requests)
  },

  /**
   * 获取批次任务状态
   * @param {string} batchId - 批次ID
   */
  getBatchStatus(batchId) {
    return apiClient.get(`/agents/batch/${batchId}/status`)
  },

  /**
   * TARA智能体相关接口
   */
  tara: {
    /**
     * 执行TARA分析
     * @param {Object} params - TARA分析参数
     */
    analyze(params) {
      return agentsAPI.executeAgent('tara', params)
    },

    /**
     * 流式TARA分析
     * @param {Object} params - TARA分析参数
     */
    analyzeStream(params) {
      return agentsAPI.streamAgentExecution('tara', params)
    },

    /**
     * 获取TARA状态
     */
    getStatus() {
      return agentsAPI.getAgentStatus('tara')
    },

    /**
     * 获取TARA性能指标
     * @param {number} days - 统计天数
     */
    getMetrics(days = 7) {
      return agentsAPI.getAgentMetrics('tara', days)
    },

    /**
     * 初始化TARA智能体
     */
    initialize() {
      return agentsAPI.initializeAgent('tara')
    },

    /**
     * 终止TARA智能体
     */
    terminate() {
      return agentsAPI.terminateAgent('tara')
    }
  },

  /**
   * 测试用例智能体相关接口
   */
  testCase: {
    /**
     * 生成测试用例
     * @param {Object} params - 测试用例生成参数
     */
    generate(params) {
      return agentsAPI.executeAgent('test_case', params)
    },

    /**
     * 流式生成测试用例
     * @param {Object} params - 测试用例生成参数
     */
    generateStream(params) {
      return agentsAPI.streamAgentExecution('test_case', params)
    },

    /**
     * 获取测试用例智能体状态
     */
    getStatus() {
      return agentsAPI.getAgentStatus('test_case')
    },

    /**
     * 获取性能指标
     * @param {number} days - 统计天数
     */
    getMetrics(days = 7) {
      return agentsAPI.getAgentMetrics('test_case', days)
    },

    /**
     * 初始化测试用例智能体
     */
    initialize() {
      return agentsAPI.initializeAgent('test_case')
    },

    /**
     * 终止测试用例智能体
     */
    terminate() {
      return agentsAPI.terminateAgent('test_case')
    }
  },

  /**
   * 自动化测试智能体相关接口
   */
  automation: {
    /**
     * 执行自动化测试
     * @param {Object} params - 自动化测试参数
     */
    execute(params) {
      return agentsAPI.executeAgent('automation_test', params)
    },

    /**
     * 流式执行自动化测试
     * @param {Object} params - 自动化测试参数
     */
    executeStream(params) {
      return agentsAPI.streamAgentExecution('automation_test', params)
    },

    /**
     * 获取自动化测试智能体状态
     */
    getStatus() {
      return agentsAPI.getAgentStatus('automation_test')
    },

    /**
     * 获取性能指标
     * @param {number} days - 统计天数
     */
    getMetrics(days = 7) {
      return agentsAPI.getAgentMetrics('automation_test', days)
    },

    /**
     * 初始化自动化测试智能体
     */
    initialize() {
      return agentsAPI.initializeAgent('automation_test')
    },

    /**
     * 终止自动化测试智能体
     */
    terminate() {
      return agentsAPI.terminateAgent('automation_test')
    }
  },

  /**
   * 报告分析智能体相关接口
   */
  report: {
    /**
     * 生成分析报告
     * @param {Object} params - 报告生成参数
     */
    generate(params) {
      return agentsAPI.executeAgent('report_analysis', params)
    },

    /**
     * 流式生成报告
     * @param {Object} params - 报告生成参数
     */
    generateStream(params) {
      return agentsAPI.streamAgentExecution('report_analysis', params)
    },

    /**
     * 获取报告分析智能体状态
     */
    getStatus() {
      return agentsAPI.getAgentStatus('report_analysis')
    },

    /**
     * 获取性能指标
     * @param {number} days - 统计天数
     */
    getMetrics(days = 7) {
      return agentsAPI.getAgentMetrics('report_analysis', days)
    },

    /**
     * 初始化报告分析智能体
     */
    initialize() {
      return agentsAPI.initializeAgent('report_analysis')
    },

    /**
     * 终止报告分析智能体
     */
    terminate() {
      return agentsAPI.terminateAgent('report_analysis')
    }
  },

  /**
   * 知识库智能体相关接口
   */
  knowledge: {
    /**
     * 查询知识库
     * @param {Object} params - 查询参数
     */
    query(params) {
      return agentsAPI.executeAgent('knowledge_base', params)
    },

    /**
     * 流式查询知识库
     * @param {Object} params - 查询参数
     */
    queryStream(params) {
      return agentsAPI.streamAgentExecution('knowledge_base', params)
    },

    /**
     * 获取知识库智能体状态
     */
    getStatus() {
      return agentsAPI.getAgentStatus('knowledge_base')
    },

    /**
     * 获取性能指标
     * @param {number} days - 统计天数
     */
    getMetrics(days = 7) {
      return agentsAPI.getAgentMetrics('knowledge_base', days)
    },

    /**
     * 初始化知识库智能体
     */
    initialize() {
      return agentsAPI.initializeAgent('knowledge_base')
    },

    /**
     * 终止知识库智能体
     */
    terminate() {
      return agentsAPI.terminateAgent('knowledge_base')
    }
  },

  /**
   * 执行智能体并支持智能步骤分配
   * @param {string} agentType - 智能体类型
   * @param {Object} params - 执行参数
   * @param {string} params.user_request - 用户请求内容
   * @param {Object} params.context - 执行上下文
   * @param {boolean} params.enable_planning - 是否启用智能步骤分配
   * @param {boolean} params.stream - 是否启用流式响应
   */
  executeAgentWithPlanning(agentType, params) {
    const requestParams = {
      ...params,
      enable_planning: true,
      step_by_step: true,
      chat_mode: true
    }
    return this.executeAgent(agentType, requestParams)
  },

  /**
   * 带智能规划的流式执行智能体
   * @param {string} agentType - 智能体类型
   * @param {Object} params - 执行参数
   */
  async streamAgentExecutionWithPlanning(agentType, params) {
    // 确保设置了规划相关参数
    const execParams = {
      ...params,
      enable_planning: true,
      stream: true
    }
    
    // 使用apiClient的baseURL，确保URL路径一致
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://192.168.136.129:8000'
    // 使用完整的API路径
    const url = `${baseUrl}/api/v1/agents/${agentType}/stream`
    
    console.log(`Streaming agent execution with planning to: ${url}`)
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...apiClient.defaults.headers,
      },
      body: JSON.stringify(execParams)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    return response.body.getReader()
  }
}

export default agentsAPI

// 兼容性方法
agentsAPI.listAgents = agentsAPI.getAgentsList

// 添加便利方法
agentsAPI.getAgentOverview = function() {
  return Promise.all([
    this.getAgentsList(),
    this.tara.getStatus(),
    this.testCase.getStatus(),
    this.automation.getStatus(),
    this.report.getStatus(),
    this.knowledge.getStatus()
  ]).then(([list, taraStatus, testCaseStatus, automationStatus, reportStatus, knowledgeStatus]) => {
    return {
      list: list.data || [],
      statuses: {
        tara: taraStatus.data,
        test_case: testCaseStatus.data,
        automation_test: automationStatus.data,
        report_analysis: reportStatus.data,
        knowledge_base: knowledgeStatus.data
      }
    }
  })
} 