<template>
  <div class="report-agent">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        报告分析智能体
      </h1>
      <p class="page-description">综合分析报告生成</p>
    </div>

    <el-empty description="报告分析智能体功能开发中...">
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.report-agent {
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
