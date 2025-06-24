/**
 * 知识库API模块
 * 提供知识库管理、文档处理、搜索等接口
 */

import { apiClient } from '../index'

const knowledgeAPI = {
  /**
   * 获取知识库列表
   * @param {Object} params - 查询参数
   */
  getKnowledgeBases(params = {}) {
    return apiClient.get('/knowledge-bases', { params })
  },

  /**
   * 创建知识库
   * @param {Object} data - 知识库数据
   * @param {string} data.name - 知识库名称
   * @param {string} data.description - 描述
   * @param {string} data.type - 类型
   */
  createKnowledgeBase(data) {
    return apiClient.post('/knowledge-bases', data)
  },

  /**
   * 获取知识库详情
   * @param {string} id - 知识库ID
   */
  getKnowledgeBase(id) {
    return apiClient.get(`/knowledge-bases/${id}`)
  },

  /**
   * 更新知识库
   * @param {string} id - 知识库ID
   * @param {Object} data - 更新数据
   */
  updateKnowledgeBase(id, data) {
    return apiClient.put(`/knowledge-bases/${id}`, data)
  },

  /**
   * 删除知识库
   * @param {string} id - 知识库ID
   */
  deleteKnowledgeBase(id) {
    return apiClient.delete(`/knowledge-bases/${id}`)
  },

  /**
   * 上传文档到知识库
   * @param {string} id - 知识库ID
   * @param {FormData} formData - 包含文件的表单数据
   */
  uploadDocument(id, formData) {
    return apiClient.post(`/knowledge-bases/${id}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取知识库文档列表
   * @param {string} id - 知识库ID
   * @param {Object} params - 查询参数
   */
  getDocuments(id, params = {}) {
    return apiClient.get(`/knowledge-bases/${id}/documents`, { params })
  },

  /**
   * 删除文档
   * @param {string} id - 知识库ID
   * @param {string} docId - 文档ID
   */
  deleteDocument(id, docId) {
    return apiClient.delete(`/knowledge-bases/${id}/documents/${docId}`)
  },

  /**
   * 搜索知识库
   * @param {Object} params - 搜索参数
   * @param {string} params.query - 搜索查询
   * @param {Array} params.knowledge_base_ids - 知识库ID列表
   * @param {number} params.top_k - 返回结果数量
   * @param {number} params.score_threshold - 相似度阈值
   */
  search(params) {
    return apiClient.post('/knowledge-bases/search', params)
  },

  /**
   * 获取知识库统计信息
   */
  getStats() {
    return apiClient.get('/knowledge-bases/stats/overview')
  },

  /**
   * 演示功能 - 创建示例数据
   */
  createSampleData() {
    return apiClient.get('/knowledge-bases/demo/sample-data')
  },

  /**
   * 演示功能 - 上传并搜索
   * @param {Object} params - 演示参数
   */
  uploadAndSearch(params) {
    return apiClient.post('/knowledge-bases/demo/upload-and-search', params)
  },

  /**
   * 获取支持的文件格式
   */
  getSupportedFormats() {
    return {
      documents: ['.txt', '.md', '.pdf', '.docx', '.doc'],
      code: ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c'],
      data: ['.json', '.xml', '.csv']
    }
  },

  /**
   * 批量上传文档
   * @param {string} id - 知识库ID
   * @param {Array} files - 文件列表
   */
  async batchUploadDocuments(id, files) {
    const results = []
    
    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const result = await this.uploadDocument(id, formData)
        results.push({ file: file.name, success: true, result })
      } catch (error) {
        results.push({ file: file.name, success: false, error: error.message })
      }
    }
    
    return results
  }
}

export default knowledgeAPI 