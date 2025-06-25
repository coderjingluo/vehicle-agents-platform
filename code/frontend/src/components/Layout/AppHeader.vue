<template>
  <el-header class="app-header" :class="headerClasses">
    <!-- 左侧区域 -->
    <div class="header-left">
      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item
          v-for="item in breadcrumbItems"
          :key="item.path"
          :to="item.path"
        >
          <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>

      <!-- 工作流进度显示 -->
      <div v-if="workflowStore.isExecuting" class="workflow-indicator">
        <el-icon class="indicator-icon spinning"><Loading /></el-icon>
        <span class="indicator-text">{{ workflowStore.currentStep }}</span>
        <el-progress 
          :percentage="workflowStore.executionProgress" 
          :show-text="false"
          :stroke-width="3"
          class="mini-progress"
        />
      </div>
    </div>

    <!-- 右侧区域 -->
    <div class="header-right">
      <!-- 快速操作按钮组 -->
      <div class="action-buttons">
        <!-- 系统健康检查 -->
        <el-tooltip content="检查系统健康状态" placement="bottom">
          <el-button
            :icon="Refresh"
            @click="handleHealthCheck"
            circle
            size="small"
            class="action-btn"
          />
        </el-tooltip>

        <!-- 通知中心 -->
        <el-popover
          placement="bottom-end"
          :width="320"
          trigger="click"
          popper-class="notification-popover"
        >
          <template #reference>
            <el-badge 
              :value="appStore.unreadNotifications" 
              :max="99"
              :hidden="appStore.unreadNotifications === 0"
              class="notification-badge"
            >
              <el-button
                :icon="Bell"
                circle
                size="small"
                class="action-btn"
              />
            </el-badge>
          </template>

          <div class="notification-panel">
            <div class="notification-header">
              <span class="notification-title">通知中心</span>
              <el-button
                text
                size="small"
                @click="appStore.markAllNotificationsAsRead"
                :disabled="appStore.unreadNotifications === 0"
              >
                全部已读
              </el-button>
            </div>

            <el-scrollbar max-height="300px" class="notification-list">
              <div
                v-for="notification in recentNotifications"
                :key="notification.id"
                class="notification-item"
                :class="{ 'unread': !notification.read }"
                @click="markAsRead(notification.id)"
              >
                <el-icon :class="`icon-${notification.type}`">
                  <component :is="getNotificationIcon(notification.type)" />
                </el-icon>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
                </div>
              </div>
              
              <el-empty 
                v-if="appStore.notifications.length === 0"
                :image-size="60"
                description="暂无通知"
              />
            </el-scrollbar>

            <div class="notification-footer">
              <el-button
                text
                size="small"
                @click="appStore.clearNotifications"
                :disabled="appStore.notifications.length === 0"
              >
                清空通知
              </el-button>
            </div>
          </div>
        </el-popover>

        <!-- 全屏切换 -->
        <el-tooltip :content="isFullscreen ? '退出全屏' : '进入全屏'" placement="bottom">
          <el-button
            :icon="isFullscreen ? OfficeBuilding : FullScreen"
            @click="toggleFullscreen"
            circle
            size="small"
            class="action-btn"
          />
        </el-tooltip>

        <!-- 主题切换 -->
        <el-tooltip :content="appStore.isDarkTheme ? '切换到亮色主题' : '切换到暗色主题'" placement="bottom">
          <el-button
            :icon="appStore.isDarkTheme ? Sunny : Moon"
            @click="appStore.toggleTheme"
            circle
            size="small"
            class="action-btn theme-toggle"
          />
        </el-tooltip>
      </div>

      <!-- 用户菜单 -->
      <el-dropdown trigger="click" class="user-dropdown">
        <div class="user-avatar">
          <el-avatar :size="32" class="avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span v-if="!isMobile" class="username">管理员</span>
        </div>
        
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>
              <el-icon><User /></el-icon>
              个人资料
            </el-dropdown-item>
            <el-dropdown-item>
              <el-icon><Setting /></el-icon>
              账户设置
            </el-dropdown-item>
            <el-dropdown-item divided>
              <el-icon><Key /></el-icon>
              修改密码
            </el-dropdown-item>
            <el-dropdown-item>
              <el-icon><Document /></el-icon>
              使用文档
            </el-dropdown-item>
            <el-dropdown-item divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../../stores/app'
import { useWorkflowStore } from '../../stores/workflow'
import {
  Refresh, Bell, FullScreen, OfficeBuilding, Sunny, Moon, User, Setting, Key,
  Document, SwitchButton, Loading, SuccessFilled, WarningFilled, 
  CircleCloseFilled, InfoFilled
} from '@element-plus/icons-vue'

// 状态管理
const appStore = useAppStore()
const workflowStore = useWorkflowStore()
const route = useRoute()
const router = useRouter()

// 响应式数据
const isFullscreen = ref(false)
const isMobile = ref(window.innerWidth < 768)

// 计算属性
const headerClasses = computed(() => ({
  'header-dark': appStore.isDarkTheme,
  'header-mobile': isMobile.value
}))

const breadcrumbItems = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title,
    icon: item.meta.icon
  }))
})

const recentNotifications = computed(() => {
  return appStore.notifications.slice(0, 10)
})

// 方法
const handleHealthCheck = async () => {
  try {
    await appStore.checkSystemHealth()
  } catch (error) {
    console.error('健康检查失败:', error)
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const markAsRead = (notificationId) => {
  appStore.markNotificationAsRead(notificationId)
}

const getNotificationIcon = (type) => {
  const icons = {
    success: SuccessFilled,
    warning: WarningFilled,
    error: CircleCloseFilled,
    info: InfoFilled
  }
  return icons[type] || InfoFilled
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 24小时内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// 生命周期
onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
.app-header {
  height: 60px;
  background-color: var(--el-bg-color-overlay);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 100;
}

.header-dark {
  background-color: var(--el-bg-color);
  border-bottom-color: var(--el-border-color);
}

/* 左侧区域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
  min-width: 0;
}

.breadcrumb {
  font-size: 14px;
}

.breadcrumb .el-breadcrumb__item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.breadcrumb .el-icon {
  font-size: 14px;
}

/* 工作流指示器 */
.workflow-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background-color: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: 16px;
  font-size: 12px;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.indicator-icon {
  font-size: 14px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.indicator-text {
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-progress {
  width: 60px;
}

/* 右侧区域 */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  background-color: var(--el-fill-color);
  border: 1px solid var(--el-border-color-light);
  color: var(--el-text-color-regular);
  transition: all 0.3s ease;
}

.action-btn:hover {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
  transform: translateY(-1px);
}

.theme-toggle {
  position: relative;
  overflow: hidden;
}

.theme-toggle::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, var(--el-color-primary-light-8), transparent);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.3s ease;
}

.theme-toggle:hover::before {
  width: 100%;
  height: 100%;
}

/* 通知相关 */
.notification-badge {
  position: relative;
}

.notification-panel {
  width: 100%;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.notification-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.notification-list {
  max-height: 300px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background-color 0.3s ease;
  position: relative;
}

.notification-item:hover {
  background-color: var(--el-fill-color-light);
}

.notification-item.unread {
  background-color: var(--el-color-primary-light-9);
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--el-color-primary);
}

.notification-item .el-icon {
  margin-top: 2px;
  font-size: 16px;
}

.icon-success {
  color: var(--el-color-success);
}

.icon-warning {
  color: var(--el-color-warning);
}

.icon-error {
  color: var(--el-color-danger);
}

.icon-info {
  color: var(--el-color-info);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-content .notification-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notification-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.notification-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  text-align: center;
}

/* 用户菜单 */
.user-dropdown {
  cursor: pointer;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.user-avatar:hover {
  background-color: var(--el-fill-color-light);
}

.avatar {
  background-color: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 移动端适配 */
.header-mobile {
  padding: 0 12px;
}

.header-mobile .header-left {
  gap: 12px;
}

.header-mobile .header-right {
  gap: 8px;
}

.header-mobile .action-buttons {
  gap: 4px;
}

.header-mobile .workflow-indicator {
  display: none;
}

.header-mobile .username {
  display: none;
}

/* 响应式断点 */
@media (max-width: 768px) {
  .breadcrumb {
    font-size: 12px;
  }
  
  .breadcrumb .el-breadcrumb__item:not(:last-child) {
    display: none;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0 8px;
  }
  
  .action-buttons .action-btn:nth-child(1),
  .action-buttons .action-btn:nth-child(2) {
    display: none;
  }
}

/* 暗色主题适配 */
.header-dark .workflow-indicator {
  background-color: var(--el-color-primary-dark-2);
  border-color: var(--el-color-primary);
}

.header-dark .action-btn {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
}

.header-dark .notification-item.unread {
  background-color: var(--el-color-primary-dark-2);
}

/* 动画效果 */
.action-btn {
  transform-origin: center;
}

.action-btn:active {
  transform: translateY(-1px) scale(0.95);
}

.notification-item {
  transform: translateX(0);
}

.notification-item:hover {
  transform: translateX(2px);
}

/* 加载状态 */
.action-btn.is-loading {
  pointer-events: none;
}

/* 特殊效果 */
.user-avatar {
  position: relative;
  overflow: hidden;
}

.user-avatar::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, var(--el-color-primary-light-8), transparent);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.3s ease;
  z-index: -1;
}

.user-avatar:hover::before {
  width: 120%;
  height: 120%;
}

/* 通知弹窗样式 */
:deep(.notification-popover) {
  padding: 0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

:deep(.notification-popover .el-popover__content) {
  padding: 0;
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu) {
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
}

:deep(.el-dropdown-menu .el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
}

:deep(.el-dropdown-menu .el-dropdown-menu__item:hover) {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
</style> 