<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-title">页面未找到</div>
      <div class="error-description">
        抱歉，您访问的页面不存在或已被移动
      </div>
      
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          <el-icon><House /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
    </div>
    
    <div class="error-illustration">
      <el-icon class="error-icon"><Warning /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { House, ArrowLeft, Warning } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 40px 20px;
  gap: 60px;
}

.not-found-content {
  text-align: center;
  max-width: 400px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: var(--el-color-primary);
  line-height: 1;
  margin-bottom: 20px;
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.error-description {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.error-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon {
  font-size: 200px;
  color: var(--el-color-info-light-5);
  opacity: 0.6;
}

@media (max-width: 768px) {
  .not-found {
    flex-direction: column;
    gap: 40px;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .error-title {
    font-size: 24px;
  }
  
  .error-description {
    font-size: 14px;
  }
  
  .error-icon {
    font-size: 120px;
  }
}
</style> 