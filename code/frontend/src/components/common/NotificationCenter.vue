<template>
  <!-- 浮动通知区域 -->
  <transition-group
    name="notification"
    tag="div"
    class="notification-container"
  >
    <div
      v-for="notification in visibleNotifications"
      :key="notification.id"
      class="notification-item"
      :class="getNotificationClass(notification)"
      @click="handleNotificationClick(notification)"
    >
      <!-- 图标 -->
      <div class="notification-icon">
        <el-icon>
          <component :is="getNotificationIcon(notification.type)" />
        </el-icon>
      </div>

      <!-- 内容 -->
      <div class="notification-content">
        <div v-if="notification.title" class="notification-title">
          {{ notification.title }}
        </div>
        <div class="notification-message">
          {{ notification.message }}
        </div>
        <div class="notification-time">
          {{ formatNotificationTime(notification.timestamp) }}
        </div>
      </div>

      <!-- 关闭按钮 -->
      <div class="notification-close" @click.stop="closeNotification(notification.id)">
        <el-icon><Close /></el-icon>
      </div>

      <!-- 进度条（自动关闭时显示） -->
      <div
        v-if="notification.duration > 0"
        class="notification-progress"
        :style="{ animationDuration: `${notification.duration}ms` }"
      ></div>
    </div>
  </transition-group>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../../stores/app'
import {
  SuccessFilled, WarningFilled, CircleCloseFilled, InfoFilled, Close
} from '@element-plus/icons-vue'

// 状态管理
const appStore = useAppStore()

// 计算属性
const visibleNotifications = computed(() => {
  // 只显示最近的5个通知，并且过滤掉已读的重要通知
  return appStore.notifications
    .filter(n => !n.read || n.type === 'error')
    .slice(0, 5)
})

// 方法
const getNotificationClass = (notification) => ({
  [`notification-${notification.type}`]: true,
  'notification-clickable': !!notification.action
})

const getNotificationIcon = (type) => {
  const icons = {
    success: SuccessFilled,
    warning: WarningFilled,
    error: CircleCloseFilled,
    info: InfoFilled
  }
  return icons[type] || InfoFilled
}

const formatNotificationTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

const handleNotificationClick = (notification) => {
  // 标记为已读
  appStore.markNotificationAsRead(notification.id)
  
  // 执行自定义操作
  if (notification.action) {
    notification.action()
  }
}

const closeNotification = (id) => {
  appStore.removeNotification(id)
}

// 监听全局消息
let messageCleanup = null

onMounted(() => {
  // 简化初始化，移除复杂的消息监听
})

onUnmounted(() => {
  if (messageCleanup) {
    messageCleanup()
  }
})
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 400px;
  pointer-events: none;
}

.notification-item {
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 320px;
  max-width: 400px;
  position: relative;
  overflow: hidden;
  pointer-events: auto;
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.notification-item:hover {
  transform: translateX(-4px);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.2);
}

.notification-clickable {
  cursor: pointer;
}

.notification-clickable:hover {
  border-color: var(--el-color-primary-light-7);
}

/* 通知类型样式 */
.notification-success {
  border-left: 4px solid var(--el-color-success);
}

.notification-success .notification-icon {
  color: var(--el-color-success);
}

.notification-warning {
  border-left: 4px solid var(--el-color-warning);
}

.notification-warning .notification-icon {
  color: var(--el-color-warning);
}

.notification-error {
  border-left: 4px solid var(--el-color-danger);
}

.notification-error .notification-icon {
  color: var(--el-color-danger);
}

.notification-info {
  border-left: 4px solid var(--el-color-info);
}

.notification-info .notification-icon {
  color: var(--el-color-info);
}

/* 图标 */
.notification-icon {
  font-size: 20px;
  margin-top: 2px;
  flex-shrink: 0;
}

/* 内容 */
.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-message {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  word-break: break-word;
}

.notification-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
}

/* 关闭按钮 */
.notification-close {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.notification-close:hover {
  background-color: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.notification-close .el-icon {
  font-size: 12px;
}

/* 进度条 */
.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background-color: var(--el-color-primary);
  animation: progress-countdown linear forwards;
  transform-origin: left;
}

@keyframes progress-countdown {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}

/* 动画效果 */
.notification-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.8);
}

.notification-move {
  transition: transform 0.3s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notification-container {
    right: 12px;
    left: 12px;
    max-width: none;
  }
  
  .notification-item {
    min-width: 0;
    max-width: none;
    padding: 12px;
  }
  
  .notification-title {
    font-size: 13px;
  }
  
  .notification-message {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .notification-container {
    top: 60px;
  }
  
  .notification-item {
    padding: 10px;
    gap: 8px;
  }
  
  .notification-icon {
    font-size: 16px;
  }
}

/* 暗色主题适配 */
.app-dark .notification-item {
  background: var(--el-bg-color);
  border-color: var(--el-border-color);
}

/* 特殊效果 */
.notification-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent, rgba(255, 255, 255, 0.05));
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.notification-item:hover::before {
  opacity: 1;
}

/* 堆叠效果 */
.notification-item:nth-child(n+2) {
  margin-top: -4px;
  transform: scale(0.98);
  opacity: 0.9;
}

.notification-item:nth-child(n+3) {
  margin-top: -8px;
  transform: scale(0.96);
  opacity: 0.8;
}

.notification-item:nth-child(n+4) {
  margin-top: -12px;
  transform: scale(0.94);
  opacity: 0.7;
}

.notification-item:nth-child(n+5) {
  display: none;
}

/* 悬停时展开堆叠 */
.notification-container:hover .notification-item {
  margin-top: 0 !important;
  transform: scale(1) !important;
  opacity: 1 !important;
}

/* 加载状态 */
.notification-item.loading .notification-content::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.4),
    transparent
  );
  animation: loading-shimmer 1.5s infinite;
}

/* 紧急通知样式 */
.notification-item.urgent {
  animation: urgent-pulse 2s ease-in-out infinite;
  border-width: 2px;
}

@keyframes urgent-pulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  50% {
    box-shadow: 0 4px 20px rgba(var(--el-color-danger-rgb), 0.3);
  }
}

/* 成功通知特殊效果 */
.notification-success::after {
  content: '✨';
  position: absolute;
  top: 8px;
  right: 30px;
  font-size: 12px;
  opacity: 0.6;
  animation: sparkle 2s ease-in-out infinite;
}

@keyframes sparkle {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* 错误通知振动效果 */
.notification-error {
  animation: error-shake 0.5s ease-in-out;
}

@keyframes error-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

/* 自定义进度条颜色 */
.notification-success .notification-progress {
  background-color: var(--el-color-success);
}

.notification-warning .notification-progress {
  background-color: var(--el-color-warning);
}

.notification-error .notification-progress {
  background-color: var(--el-color-danger);
}

.notification-info .notification-progress {
  background-color: var(--el-color-info);
}
</style> 