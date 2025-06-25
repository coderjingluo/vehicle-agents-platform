<template>
  <el-aside 
    :width="sidebarWidth"
    class="app-sidebar"
    :class="sidebarClasses"
  >
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <div v-if="!appStore.sidebarCollapsed" class="logo-section">
        <img src="/vite.svg" alt="Logo" class="logo-icon">
        <h1 class="logo-text">车联网安全平台</h1>
      </div>
      <el-icon 
        v-else 
        class="logo-icon-collapsed"
        @click="appStore.toggleSidebar"
      >
        <Menu />
      </el-icon>
    </div>

    <!-- 系统状态指示器 -->
    <div v-if="!appStore.sidebarCollapsed" class="system-status">
      <el-tooltip :content="systemStatusText" placement="right">
        <div class="status-indicator" :class="systemStatusClass">
          <el-icon><CircleCheckFilled v-if="isSystemHealthy" /><WarningFilled v-else /></el-icon>
          <span v-if="!appStore.sidebarCollapsed">{{ systemStatusText }}</span>
        </div>
      </el-tooltip>
    </div>

    <!-- 主导航菜单 -->
    <el-scrollbar class="sidebar-menu-wrapper">
      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <!-- 系统功能 -->
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>系统概览</template>
        </el-menu-item>

        <el-menu-item index="/workflow">
          <el-icon><Share /></el-icon>
          <template #title>工作流管理</template>
        </el-menu-item>

        <!-- 智能体分组 -->
        <el-sub-menu index="agents" v-if="!appStore.sidebarCollapsed">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>智能体</span>
          </template>
          
          <el-menu-item 
            v-for="agent in agentRoutes" 
            :key="agent.path"
            :index="agent.path"
            class="agent-menu-item"
          >
            <el-icon><component :is="iconComponents[agent.meta.icon]" /></el-icon>
            <template #title>{{ agent.meta.title }}</template>
            <el-tag 
              v-if="getAgentStatus(agent.meta.agentType)" 
              size="small" 
              :type="getAgentStatusType(agent.meta.agentType)"
              class="agent-status-tag"
            >
              {{ getAgentStatus(agent.meta.agentType) }}
            </el-tag>
          </el-menu-item>
        </el-sub-menu>

        <!-- 折叠状态下的智能体菜单 -->
        <template v-if="appStore.sidebarCollapsed">
          <el-menu-item 
            v-for="agent in agentRoutes" 
            :key="agent.path"
            :index="agent.path"
          >
            <el-icon><component :is="iconComponents[agent.meta.icon]" /></el-icon>
            <template #title>{{ agent.meta.title }}</template>
          </el-menu-item>
        </template>

        <!-- 工具和管理 -->
        <el-divider v-if="!appStore.sidebarCollapsed">
          <span class="divider-text">工具与管理</span>
        </el-divider>

        <el-menu-item index="/knowledge">
          <el-icon><Notebook /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>

        <el-menu-item index="/models">
          <el-icon><Setting /></el-icon>
          <template #title>模型配置</template>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Tools /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>

    <!-- 侧边栏底部 -->
    <div class="sidebar-footer">
      <!-- 折叠按钮 -->
      <el-tooltip 
        :content="appStore.sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'" 
        placement="right"
      >
        <el-button
          class="collapse-btn"
          @click="appStore.toggleSidebar"
          :icon="appStore.sidebarCollapsed ? Expand : Fold"
          circle
          size="small"
        />
      </el-tooltip>

      <!-- 工作流进度指示器 -->
      <div v-if="workflowStore.isExecuting && !appStore.sidebarCollapsed" class="workflow-progress">
        <div class="progress-info">
          <span class="progress-text">{{ workflowStore.currentStep }}</span>
          <span class="progress-percent">{{ workflowStore.executionProgress }}%</span>
        </div>
        <el-progress 
          :percentage="workflowStore.executionProgress" 
          :show-text="false"
          :stroke-width="4"
          size="small"
        />
      </div>

      <!-- 实时时间 -->
      <div v-if="!appStore.sidebarCollapsed" class="current-time">
        {{ currentTime }}
      </div>
    </div>
  </el-aside>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../../stores/app'
import { useWorkflowStore } from '../../stores/workflow'
import { getAgentRoutes } from '../../router'
import {
  Menu, Odometer, Share, Cpu, Lock, DocumentChecked, 
  Document, Search, Notebook, Setting, Tools, Expand, 
  Fold, CircleCheckFilled, WarningFilled
} from '@element-plus/icons-vue'

// 状态管理
const appStore = useAppStore()
const workflowStore = useWorkflowStore()
const route = useRoute()

// 响应式数据
const currentTime = ref('')
const timeInterval = ref(null)

// 图标映射
const iconComponents = {
  Lock,
  DocumentChecked,
  Cpu,
  Document,
  Search
}

// 计算属性
const sidebarWidth = computed(() => appStore.sidebarCollapsed ? '64px' : '240px')

const sidebarClasses = computed(() => ({
  'sidebar-collapsed': appStore.sidebarCollapsed,
  'sidebar-dark': appStore.isDarkTheme
}))

const activeMenu = computed(() => route.path)

const agentRoutes = computed(() => getAgentRoutes())

const isSystemHealthy = computed(() => appStore.systemHealth.status === 'healthy')

const systemStatusText = computed(() => {
  switch (appStore.systemHealth.status) {
    case 'healthy': return '系统正常'
    case 'warning': return '系统警告'
    case 'error': return '系统错误'
    default: return '状态未知'
  }
})

const systemStatusClass = computed(() => ({
  'status-indicator--success': appStore.systemHealth.status === 'healthy',
  'status-indicator--warning': appStore.systemHealth.status === 'warning',
  'status-indicator--danger': appStore.systemHealth.status === 'error',
  'status-indicator--info': appStore.systemHealth.status === 'unknown'
}))

// 方法
const getAgentStatus = (agentType) => {
  if (workflowStore.isExecuting && workflowStore.currentStep.includes(agentType)) {
    return '执行中'
  }
  if (workflowStore.executionResults[agentType]) {
    return '已完成'
  }
  return ''
}

const getAgentStatusType = (agentType) => {
  if (workflowStore.isExecuting && workflowStore.currentStep.includes(agentType)) {
    return 'primary'
  }
  if (workflowStore.executionResults[agentType]) {
    return 'success'
  }
  return 'info'
}

const updateCurrentTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  updateCurrentTime()
  timeInterval.value = setInterval(updateCurrentTime, 1000)
})

onUnmounted(() => {
  if (timeInterval.value) {
    clearInterval(timeInterval.value)
  }
})
</script>

<style scoped>
.app-sidebar {
  background-color: var(--el-bg-color-overlay);
  border-right: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.sidebar-dark {
  background-color: var(--el-bg-color);
  border-right-color: var(--el-border-color);
}

/* 侧边栏头部 */
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  transition: transform 0.3s ease;
}

.logo-icon:hover {
  transform: rotate(360deg);
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
  white-space: nowrap;
}

.logo-icon-collapsed {
  font-size: 24px;
  color: var(--el-color-primary);
  cursor: pointer;
  transition: color 0.3s ease;
}

.logo-icon-collapsed:hover {
  color: var(--el-color-primary-light-3);
}

/* 系统状态 */
.system-status {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

/* 菜单区域 */
.sidebar-menu-wrapper {
  flex: 1;
  margin: 8px 0;
}

.sidebar-menu {
  border-right: none;
  background-color: transparent;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sidebar-menu .el-menu-item:hover {
  background-color: var(--el-color-primary-light-9);
}

.sidebar-menu .el-menu-item.is-active {
  background-color: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  font-weight: 600;
  position: relative;
}

.sidebar-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background-color: var(--el-color-primary);
  border-radius: 0 2px 2px 0;
}

.sidebar-menu .el-sub-menu {
  margin: 4px 8px;
}

.sidebar-menu .el-sub-menu .el-sub-menu__title {
  height: 48px;
  line-height: 48px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sidebar-menu .el-sub-menu .el-sub-menu__title:hover {
  background-color: var(--el-color-primary-light-9);
}

/* 智能体菜单项 */
.agent-menu-item {
  position: relative;
}

.agent-status-tag {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
}

/* 分割线 */
.el-divider {
  margin: 16px 0 8px;
}

.divider-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  background-color: var(--el-fill-color);
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
}

/* 工作流进度 */
.workflow-progress {
  width: 100%;
  padding: 8px 12px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.progress-text {
  font-size: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.progress-percent {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

/* 当前时间 */
.current-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  padding: 4px 8px;
  background-color: var(--el-fill-color-lighter);
  border-radius: 4px;
  min-width: 80px;
}

/* 折叠状态样式 */
.sidebar-collapsed .sidebar-menu .el-menu-item {
  margin: 4px;
  justify-content: center;
}

.sidebar-collapsed .agent-status-tag {
  display: none;
}

.sidebar-collapsed .workflow-progress {
  display: none;
}

.sidebar-collapsed .current-time {
  display: none;
}

.sidebar-collapsed .system-status {
  padding: 12px 4px;
  text-align: center;
}

.sidebar-collapsed .status-indicator {
  justify-content: center;
  padding: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }
  
  .sidebar-collapsed {
    transform: translateX(-100%);
  }
}

/* 悬停效果 */
.app-sidebar:hover .logo-icon {
  transform: scale(1.1);
}

/* 动画效果 */
.el-menu-item,
.el-sub-menu__title {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-menu-item:active {
  transform: scale(0.98);
}

/* 暗色主题适配 */
.sidebar-dark .sidebar-header {
  border-bottom-color: var(--el-border-color);
}

.sidebar-dark .system-status {
  border-bottom-color: var(--el-border-color-lighter);
}

.sidebar-dark .sidebar-footer {
  border-top-color: var(--el-border-color);
}

.sidebar-dark .workflow-progress {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
}

.sidebar-dark .current-time {
  background-color: var(--el-fill-color);
}

/* 加载状态 */
.sidebar-menu .el-menu-item.loading {
  position: relative;
  overflow: hidden;
}

.sidebar-menu .el-menu-item.loading::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    var(--el-color-primary-light-8),
    transparent
  );
  animation: loading-shimmer 1.5s infinite;
}

@keyframes loading-shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

/* 工具提示样式 */
.el-tooltip__popper {
  font-size: 12px;
}

/* 图标旋转动画 */
.sidebar-menu .el-menu-item .el-icon {
  transition: transform 0.3s ease;
}

.sidebar-menu .el-menu-item:hover .el-icon {
  transform: scale(1.1);
}

/* 选中状态的特殊效果 */
.sidebar-menu .el-menu-item.is-active {
  box-shadow: inset 0 0 8px var(--el-color-primary-light-8);
}

/* 折叠动画 */
.app-sidebar {
  will-change: width;
}

.sidebar-menu-wrapper {
  will-change: transform;
}
</style> 