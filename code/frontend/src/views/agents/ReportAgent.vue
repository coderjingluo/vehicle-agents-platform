<template>
  <div class="report-agent-container">
    <h1>报告分析智能体</h1>
    <p>这个页面将实现测试报告的分析和生成功能。</p>
    
    <!-- 报告分析表单 -->
    <div class="analysis-form">
      <el-form :model="analysisParams" label-width="120px">
        <el-form-item label="测试结果来源">
          <el-select v-model="analysisParams.context.result_source" placeholder="选择测试结果来源">
            <el-option label="自动化测试" value="automation" />
            <el-option label="外部测试" value="external" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="报告类型">
          <el-select v-model="analysisParams.context.report_type" placeholder="选择报告类型">
            <el-option label="详细技术报告" value="technical" />
            <el-option label="管理层摘要" value="executive" />
            <el-option label="合规性报告" value="compliance" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="generateReport">生成报告</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { agentsAPI } from '@/api'

// 分析参数
const analysisParams = ref({
  user_request: "分析测试结果并生成报告",
  context: {
    result_source: "automation",
    report_type: "technical",
    system_name: "测试系统",
    include_recommendations: true,
    include_visualizations: true
  },
  timeout: 300,
  stream: true,
  // 添加缺失的参数
  priority: "normal",
  metadata: {
    source: "report_ui",
    version: "1.0"
  },
  enable_planning: true,
  step_by_step: true,
  chat_mode: false,
  agent_config: {
    model: "default"
  }
})

// 生成报告方法
const generateReport = async () => {
  try {
    const response = await agentsAPI.executeAgent('report', analysisParams.value)
    console.log('报告生成结果:', response.data)
  } catch (error) {
    console.error('报告生成失败:', error)
  }
}
</script>

<style scoped>
.report-agent-container {
  padding: 20px;
}

.analysis-form {
  max-width: 600px;
  margin-top: 20px;
}
</style>
