<template>
  <div class="automation-agent-container">
    <h1>自动化测试智能体</h1>
    <p>这个页面将实现自动化测试用例的执行和管理功能。</p>
    
    <!-- 执行自动化测试的表单 -->
    <div class="execution-form">
      <el-form :model="executionParams" label-width="120px">
        <el-form-item label="测试用例来源">
          <el-select v-model="executionParams.context.test_source" placeholder="选择测试用例来源">
            <el-option label="测试用例生成器" value="generator" />
            <el-option label="已有测试用例" value="existing" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="执行环境">
          <el-select v-model="executionParams.context.execution_environment" placeholder="选择执行环境">
            <el-option label="虚拟环境" value="virtual" />
            <el-option label="实际硬件" value="hardware" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="executeTests">执行测试</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { agentsAPI } from '@/api'

// 执行参数
const executionParams = ref({
  user_request: "执行自动化测试用例",
  context: {
    test_source: "generator",
    execution_environment: "virtual",
    system_name: "测试系统",
    test_mode: "automated"
  },
  timeout: 600,
  stream: true,
  // 添加缺失的参数
  priority: "normal",
  metadata: {
    source: "automation_ui",
    version: "1.0"
  },
  enable_planning: true,
  step_by_step: true,
  chat_mode: false,
  agent_config: {
    model: "default"
  }
})

// 执行测试方法
const executeTests = async () => {
  try {
    const response = await agentsAPI.executeAgent('automation', executionParams.value)
    console.log('测试执行结果:', response.data)
  } catch (error) {
    console.error('执行测试失败:', error)
  }
}
</script>

<style scoped>
.automation-agent-container {
  padding: 20px;
}

.execution-form {
  max-width: 600px;
  margin-top: 20px;
}
</style>
