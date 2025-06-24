/**
 * 模型配置API模块
 * 提供模型管理、连接测试、使用统计等接口
 */

import { apiClient } from '../index'

const modelsAPI = {
  /**
   * 获取模型列表
   * @param {Object} params - 查询参数
   */
  getModels(params = {}) {
    return apiClient.get('/models', { params })
  },

  /**
   * 创建模型配置
   * @param {Object} data - 模型配置数据
   * @param {string} data.name - 模型名称
   * @param {string} data.provider - 提供商
   * @param {string} data.model_type - 模型类型
   * @param {string} data.api_key - API密钥
   * @param {string} data.base_url - 基础URL
   * @param {Object} data.config - 配置参数
   */
  createModel(data) {
    return apiClient.post('/models', data)
  },

  /**
   * 获取模型详情
   * @param {string} id - 模型ID
   */
  getModel(id) {
    return apiClient.get(`/models/${id}`)
  },

  /**
   * 更新模型配置
   * @param {string} id - 模型ID
   * @param {Object} data - 更新数据
   */
  updateModel(id, data) {
    return apiClient.put(`/models/${id}`, data)
  },

  /**
   * 删除模型配置
   * @param {string} id - 模型ID
   */
  deleteModel(id) {
    return apiClient.delete(`/models/${id}`)
  },

  /**
   * 测试模型连接
   * @param {string} id - 模型ID
   */
  testModel(id) {
    return apiClient.post(`/models/${id}/test`)
  },

  /**
   * 批量测试模型
   * @param {Array} modelIds - 模型ID列表
   */
  batchTestModels(modelIds) {
    return apiClient.post('/models/batch-test', { model_ids: modelIds })
  },

  /**
   * 获取模型使用统计
   * @param {string} id - 模型ID
   * @param {Object} params - 查询参数
   */
  getModelStats(id, params = {}) {
    return apiClient.get(`/models/${id}/stats`, { params })
  },

  /**
   * 获取提供商信息
   * @param {string} provider - 提供商名称
   */
  getProvider(provider) {
    return apiClient.get(`/models/providers/${provider}`)
  },

  /**
   * 获取默认模型
   * @param {string} modelType - 模型类型 (chat|embedding|completion|vision|audio)
   */
  getDefaultModel(modelType) {
    return apiClient.get(`/models/defaults/${modelType}`)
  },

  /**
   * 设置默认模型
   * @param {string} modelType - 模型类型
   * @param {string} modelId - 模型ID
   */
  setDefaultModel(modelType, modelId) {
    return apiClient.post(`/models/defaults/${modelType}`, { model_id: modelId })
  },

  /**
   * 获取支持的提供商列表
   */
  getSupportedProviders() {
    return apiClient.get('/models/demo/providers')
  },

  /**
   * 快速设置演示配置
   * @param {Object} params - 配置参数
   */
  quickSetupDemo(params) {
    return apiClient.post('/models/demo/quick-setup', params)
  },

  /**
   * 演示对话
   * @param {string} id - 模型ID
   * @param {Object} params - 对话参数
   * @param {string} params.message - 消息内容
   * @param {Array} params.history - 对话历史
   */
  demoChat(id, params) {
    return apiClient.post(`/models/${id}/demo/chat`, params)
  },

  /**
   * 获取模型提供商的预设配置
   */
  getProviderPresets() {
    return {
      openai: {
        name: 'OpenAI',
        baseUrl: 'https://api.openai.com/v1',
        models: ['gpt-4', 'gpt-3.5-turbo', 'text-embedding-ada-002'],
        requiresApiKey: true
      },
      deepseek: {
        name: 'DeepSeek',
        baseUrl: 'https://api.deepseek.com/v1',
        models: ['deepseek-chat', 'deepseek-coder'],
        requiresApiKey: true
      },
      anthropic: {
        name: 'Anthropic',
        baseUrl: 'https://api.anthropic.com',
        models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
        requiresApiKey: true
      },
      azure: {
        name: 'Azure OpenAI',
        baseUrl: 'https://{resource}.openai.azure.com',
        models: ['gpt-4', 'gpt-35-turbo'],
        requiresApiKey: true,
        additionalFields: ['resource_name', 'deployment_name', 'api_version']
      },
      google: {
        name: 'Google AI',
        baseUrl: 'https://generativelanguage.googleapis.com',
        models: ['gemini-pro', 'gemini-pro-vision'],
        requiresApiKey: true
      },
      cohere: {
        name: 'Cohere',
        baseUrl: 'https://api.cohere.ai',
        models: ['command', 'command-light'],
        requiresApiKey: true
      }
    }
  },

  /**
   * 获取模型类型配置
   */
  getModelTypes() {
    return {
      chat: {
        name: '对话模型',
        description: '用于对话和文本生成',
        icon: 'ChatDotRound'
      },
      embedding: {
        name: '嵌入模型',
        description: '用于文本向量化',
        icon: 'DataAnalysis'
      },
      completion: {
        name: '补全模型',
        description: '用于文本补全',
        icon: 'EditPen'
      },
      vision: {
        name: '视觉模型',
        description: '用于图像理解',
        icon: 'Picture'
      },
      audio: {
        name: '音频模型',
        description: '用于音频处理',
        icon: 'Microphone'
      }
    }
  }
}

export default modelsAPI 