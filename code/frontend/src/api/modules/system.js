/**
 * 系统API模块
 * 提供系统状态、健康检查、性能监控、配置管理等接口
 */

import { apiClient } from '../index'

const systemAPI = {
  /**
   * 根路径 - 获取API基础信息
   */
  getInfo() {
    return apiClient.get('/')
  },

  /**
   * 系统健康检查
   */
  healthCheck() {
    return apiClient.get('/system/health')
  },

  /**
   * 获取系统状态详情
   */
  getSystemStatus() {
    return apiClient.get('/system/status')
  },

  /**
   * 获取系统性能指标
   * @param {string} period - 时间段 (1h, 6h, 24h, 7d)
   */
  getSystemMetrics(period = '1h') {
    return apiClient.get('/system/metrics', { params: { period } })
  },

  /**
   * 获取系统配置
   */
  getSystemConfig() {
    return apiClient.get('/system/config')
  },

  /**
   * 更新系统配置
   * @param {Object} config - 配置数据
   */
  updateSystemConfig(config) {
    return apiClient.put('/system/config', config)
  },

  /**
   * 获取系统日志
   * @param {string} level - 日志级别
   * @param {number} limit - 返回数量
   * @param {number} offset - 偏移量
   */
  getSystemLogs(level = 'INFO', limit = 100, offset = 0) {
    return apiClient.get('/system/logs', {
      params: { level, limit, offset }
    })
  },

  /**
   * 获取缓存统计信息
   */
  getCacheStats() {
    return apiClient.get('/system/cache/stats')
  },

  /**
   * 清理缓存
   * @param {string} cacheType - 缓存类型 (all, memory, redis)
   */
  clearCache(cacheType = 'all') {
    return apiClient.delete('/system/cache/clear', {
      params: { cache_type: cacheType }
    })
  },

  /**
   * 获取系统工具列表
   */
  getSystemTools() {
    return apiClient.get('/system/tools')
  },

  /**
   * 执行系统工具
   * @param {string} toolName - 工具名称
   * @param {Object} params - 工具参数
   */
  executeSystemTool(toolName, params) {
    return apiClient.post(`/system/tools/${toolName}/execute`, {
      tool_name: toolName,
      parameters: params.parameters || {},
      context: params.context || {},
      timeout: params.timeout || 60
    })
  },

  /**
   * 获取LLM提供商列表
   */
  getLLMProviders() {
    return apiClient.get('/system/providers')
  },

  /**
   * 测试LLM连接
   * @param {string} provider - LLM提供商
   * @param {string} model - 模型名称
   * @param {string} testMessage - 测试消息
   */
  testLLMConnection(provider, model, testMessage = 'Hello, this is a test message.') {
    return apiClient.post('/system/test/llm', null, {
      params: { provider, model, test_message: testMessage }
    })
  },

  /**
   * 获取系统详细信息
   */
  getSystemInfo() {
    return apiClient.get('/system/info')
  },

  /**
   * 重启系统（仅限开发环境）
   */
  restartSystem() {
    return apiClient.post('/system/restart')
  },

  /**
   * 性能监控相关接口
   */
  performance: {
    /**
     * 获取CPU使用情况
     */
    getCPUUsage() {
      return systemAPI.getSystemMetrics('1h').then(res => res.data.metrics?.cpu || {})
    },

    /**
     * 获取内存使用情况
     */
    getMemoryUsage() {
      return systemAPI.getSystemMetrics('1h').then(res => res.data.metrics?.memory || {})
    },

    /**
     * 获取磁盘使用情况
     */
    getDiskUsage() {
      return systemAPI.getSystemMetrics('1h').then(res => res.data.metrics?.disk || {})
    },

    /**
     * 获取网络IO情况
     */
    getNetworkIO() {
      return systemAPI.getSystemMetrics('1h').then(res => res.data.metrics?.network || {})
    },

    /**
     * 获取历史性能数据
     * @param {string} metric - 指标类型 (cpu, memory, disk, network)
     * @param {string} period - 时间段
     */
    getHistoricalData(metric, period = '24h') {
      return systemAPI.getSystemMetrics(period).then(res => {
        const data = res.data.metrics || {}
        return data[metric] || {}
      })
    }
  },

  /**
   * 日志管理相关接口
   */
  logs: {
    /**
     * 获取错误日志
     * @param {number} limit - 返回数量
     * @param {number} offset - 偏移量
     */
    getErrorLogs(limit = 100, offset = 0) {
      return systemAPI.getSystemLogs('ERROR', limit, offset)
    },

    /**
     * 获取警告日志
     * @param {number} limit - 返回数量
     * @param {number} offset - 偏移量
     */
    getWarningLogs(limit = 100, offset = 0) {
      return systemAPI.getSystemLogs('WARNING', limit, offset)
    },

    /**
     * 获取信息日志
     * @param {number} limit - 返回数量
     * @param {number} offset - 偏移量
     */
    getInfoLogs(limit = 100, offset = 0) {
      return systemAPI.getSystemLogs('INFO', limit, offset)
    },

    /**
     * 获取调试日志
     * @param {number} limit - 返回数量
     * @param {number} offset - 偏移量
     */
    getDebugLogs(limit = 100, offset = 0) {
      return systemAPI.getSystemLogs('DEBUG', limit, offset)
    },

    /**
     * 搜索日志
     * @param {string} keyword - 搜索关键词
     * @param {string} level - 日志级别
     * @param {number} limit - 返回数量
     */
    searchLogs(keyword, level = 'INFO', limit = 100) {
      return systemAPI.getSystemLogs(level, limit, 0).then(res => {
        if (!keyword) return res
        
        // 简单的前端过滤，实际应该在后端实现
        const filteredLogs = res.data.logs.filter(log => 
          log.message.toLowerCase().includes(keyword.toLowerCase())
        )
        
        return {
          ...res,
          data: {
            ...res.data,
            logs: filteredLogs,
            total: filteredLogs.length
          }
        }
      })
    }
  },

  /**
   * 缓存管理相关接口
   */
  cache: {
    /**
     * 获取内存缓存统计
     */
    getMemoryCacheStats() {
      return systemAPI.getCacheStats().then(res => {
        const stats = res.data.cache_stats || {}
        return stats.memory || {}
      })
    },

    /**
     * 获取Redis缓存统计
     */
    getRedisCacheStats() {
      return systemAPI.getCacheStats().then(res => {
        const stats = res.data.cache_stats || {}
        return stats.redis || {}
      })
    },

    /**
     * 清理内存缓存
     */
    clearMemoryCache() {
      return systemAPI.clearCache('memory')
    },

    /**
     * 清理Redis缓存
     */
    clearRedisCache() {
      return systemAPI.clearCache('redis')
    },

    /**
     * 清理所有缓存
     */
    clearAllCache() {
      return systemAPI.clearCache('all')
    },

    /**
     * 获取缓存命中率
     */
    getCacheHitRate() {
      return systemAPI.getCacheStats().then(res => {
        const stats = res.data.cache_stats || {}
        const total = (stats.hits || 0) + (stats.misses || 0)
        return total > 0 ? ((stats.hits || 0) / total * 100).toFixed(2) : 0
      })
    }
  },

  /**
   * 配置管理相关接口
   */
  config: {
    /**
     * 获取并发任务配置
     */
    getConcurrencyConfig() {
      return systemAPI.getSystemConfig().then(res => ({
        max_concurrent_tasks: res.data.max_concurrent_tasks
      }))
    },

    /**
     * 更新并发任务配置
     * @param {number} maxTasks - 最大并发任务数
     */
    updateConcurrencyConfig(maxTasks) {
      return systemAPI.getSystemConfig().then(res => {
        const config = res.data
        config.max_concurrent_tasks = maxTasks
        return systemAPI.updateSystemConfig(config)
      })
    },

    /**
     * 获取超时配置
     */
    getTimeoutConfig() {
      return systemAPI.getSystemConfig().then(res => ({
        default_timeout: res.data.default_timeout
      }))
    },

    /**
     * 更新超时配置
     * @param {number} timeout - 默认超时时间(秒)
     */
    updateTimeoutConfig(timeout) {
      return systemAPI.getSystemConfig().then(res => {
        const config = res.data
        config.default_timeout = timeout
        return systemAPI.updateSystemConfig(config)
      })
    },

    /**
     * 获取功能开关配置
     */
    getFeatureFlags() {
      return systemAPI.getSystemConfig().then(res => ({
        enable_streaming: res.data.enable_streaming,
        enable_caching: res.data.enable_caching
      }))
    },

    /**
     * 更新功能开关配置
     * @param {Object} flags - 功能开关配置
     */
    updateFeatureFlags(flags) {
      return systemAPI.getSystemConfig().then(res => {
        const config = res.data
        Object.assign(config, flags)
        return systemAPI.updateSystemConfig(config)
      })
    }
  }
}

export default systemAPI 