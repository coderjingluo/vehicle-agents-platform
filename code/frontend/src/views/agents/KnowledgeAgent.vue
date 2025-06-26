<template>
  <div class="knowledge-agent-container">
    <h1>知识库智能体</h1>
    <p>这个页面将实现知识库查询和知识管理功能。</p>
    
    <!-- 知识查询表单 -->
    <div class="query-form">
      <el-form :model="queryParams" label-width="120px">
        <el-form-item label="查询内容">
          <el-input 
            v-model="queryParams.user_request" 
            type="textarea" 
            rows="3"
            placeholder="输入您的知识查询"
          />
        </el-form-item>
        
        <el-form-item label="知识库">
          <el-select v-model="queryParams.context.knowledge_base_id" placeholder="选择知识库">
            <el-option label="车联网安全标准库" value="auto_security_standards" />
            <el-option label="测试用例库" value="test_case_repository" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="queryKnowledge">查询知识</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { agentsAPI } from '@/api'

// 查询参数
const queryParams = ref({
  user_request: "",
  context: {
    knowledge_base_id: "auto_security_standards",
    query_type: "semantic",
    top_k: 5,
    score_threshold: 0.7
  },
  timeout: 180,
  stream: true,
  // 添加缺失的参数
  priority: "normal",
  metadata: {
    source: "knowledge_ui",
    version: "1.0"
  },
  enable_planning: true,
  step_by_step: true,
  chat_mode: true,
  agent_config: {
    model: "default"
  }
})

// 查询知识方法
const queryKnowledge = async () => {
  try {
    const response = await agentsAPI.executeAgent('knowledge', queryParams.value)
    console.log('知识查询结果:', response.data)
  } catch (error) {
    console.error('知识查询失败:', error)
  }
}
</script>

<style scoped>
.knowledge-agent-container {
  padding: 20px;
}

.query-form {
  max-width: 600px;
  margin-top: 20px;
}
</style>
