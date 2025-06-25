/**
 * 演示API模块
 * 提供各种演示功能的接口
 */

import { apiClient } from '../index'

const demoAPI = {
  /**
   * TARA分析演示
   * @param {Object} params - TARA分析参数
   * @param {string} params.user_request - 用户请求
   * @param {Object} params.context - 上下文数据
   */
  taraAnalysis(params) {
    return apiClient.post('/demo/tara-analysis', params)
  },

  /**
   * 测试用例生成演示
   * @param {Object} params - 测试用例生成参数
   */
  testCaseGeneration(params = {}) {
    return apiClient.post('/demo/test-case-generation', params)
  },

  /**
   * 自动化测试演示
   * @param {Object} params - 自动化测试参数
   */
  automationTesting(params = {}) {
    return apiClient.post('/demo/automation-testing', params)
  },

  /**
   * 报告分析演示
   * @param {Object} params - 报告分析参数
   */
  reportAnalysis(params = {}) {
    return apiClient.post('/demo/report-analysis', params)
  },

  /**
   * 知识管理演示
   * @param {Object} params - 知识管理参数
   */
  knowledgeManagement(params = {}) {
    return apiClient.post('/demo/knowledge-management', params)
  },

  /**
   * 多智能体工作流演示
   * @param {Object} params - 工作流参数
   */
  multiAgentWorkflow(params = {}) {
    return apiClient.post('/demo/multi-agent-workflow', params)
  },

  /**
   * 获取演示数据
   */
  getDemoData() {
    return apiClient.get('/demo/data')
  },

  /**
   * 重置演示环境
   */
  resetDemo() {
    return apiClient.post('/demo/reset')
  }
}

export default demoAPI 