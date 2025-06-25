<template>
  <div class="testcase-agent">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DocumentChecked /></el-icon>
        测试用例智能体
      </h1>
      <p class="page-description">智能测试用例生成与管理</p>
    </div>

    <el-empty description="测试用例智能体功能开发中...">
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { DocumentChecked } from '@element-plus/icons-vue'
</script>

<style scoped>
.testcase-agent {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
  padding: 0 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
}

.page-title .el-icon {
  font-size: 32px;
  color: var(--el-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
</style> 