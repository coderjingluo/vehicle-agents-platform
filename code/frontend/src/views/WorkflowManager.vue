<template>
  <div class="workflow-manager">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon class="page-icon"><Share /></el-icon>
        工作流管理
      </h1>
      <p class="page-description">管理和监控AI智能体工作流程</p>
    </div>

    <div class="workflow-content">
      <el-card class="workflow-card">
        <template #header>
          <div class="card-header">
            <span>工作流列表</span>
            <el-button type="primary" size="small">
              <el-icon><Plus /></el-icon>
              创建工作流
            </el-button>
          </div>
        </template>
        
        <div class="workflow-list">
          <el-empty 
            description="暂无工作流数据"
            :image-size="200"
          >
            <el-button type="primary">开始创建</el-button>
          </el-empty>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { Share, Plus } from '@element-plus/icons-vue'

export default {
  name: 'WorkflowManager',
  components: {
    Share,
    Plus
  },
  data() {
    return {
      workflows: []
    }
  },
  mounted() {
    this.loadWorkflows()
  },
  methods: {
    loadWorkflows() {
      // TODO: 加载工作流数据
      console.log('Loading workflows...')
    }
  }
}
</script>

<style scoped>
.workflow-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-icon {
  font-size: 28px;
  color: var(--el-color-primary);
}

.page-description {
  color: var(--el-text-color-regular);
  margin: 0;
  font-size: 14px;
}

.workflow-content {
  width: 100%;
}

.workflow-card {
  box-shadow: var(--el-box-shadow-light);
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.workflow-list {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workflow-manager {
    padding: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}
</style> 