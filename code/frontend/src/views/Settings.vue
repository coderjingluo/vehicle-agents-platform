<template>
  <div class="settings">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Tools /></el-icon>
        系统设置
      </h1>
      <p class="page-description">用户偏好和系统参数配置</p>
    </div>

    <el-empty description="系统设置功能开发中...">
      <el-button type="primary">返回首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { Tools } from '@element-plus/icons-vue'
</script>

<style scoped>
.settings {
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