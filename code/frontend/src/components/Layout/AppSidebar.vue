<template>
  <div class="sidebar-layout">
    <!-- 品牌区域 -->
    <div class="brand-section">
      <div class="brand-content" :class="{ collapsed: isCollapsed }">
        <div class="brand-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="28" height="28">
              <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,6A6,6 0 0,1 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6M12,8A4,4 0 0,0 8,12A4,4 0 0,0 12,16A4,4 0 0,0 16,12A4,4 0 0,0 12,8Z"/>
            </svg>
          </div>
          <transition name="brand-fade">
            <div v-show="!isCollapsed" class="brand-text">
              <h1 class="brand-title">TARA</h1>
              <p class="brand-subtitle">车联网安全测试平台</p>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <div class="navigation-section">
      <nav class="nav-menu">
        <!-- 主要导航 -->
        <div class="nav-group">
          <div v-if="!isCollapsed" class="nav-group-title">主要功能</div>
          
          <!-- 仪表板 -->
          <router-link to="/dashboard" class="nav-item" :class="{ active: isActive('/dashboard') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M3,2H21A1,1 0 0,1 22,3V21A1,1 0 0,1 21,22H3A1,1 0 0,1 2,21V3A1,1 0 0,1 3,2M13,4V12L21,4M13,20V14H21V20M11,20V4H4V20"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">仪表板</span>
              </transition>
            </div>
          </router-link>

          <!-- 工作流管理 -->
          <router-link to="/workflow" class="nav-item" :class="{ active: isActive('/workflow') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M12,2A2,2 0 0,1 14,4C14,5.5 13,6.76 11.65,6.95C11.87,7.31 12,7.72 12,8.15V11.85C12,12.28 11.87,12.69 11.65,13.05C13,13.24 14,14.5 14,16C14,17.66 12.66,19 11,19S8,17.66 8,16C8,14.5 9,13.24 10.35,13.05C10.13,12.69 10,12.28 10,11.85V8.15C10,7.72 10.13,7.31 10.35,6.95C9,6.76 8,5.5 8,4A2,2 0 0,1 10,2A2,2 0 0,1 12,2Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">工作流管理</span>
              </transition>
            </div>
          </router-link>
        </div>

        <!-- 智能体模块 -->
        <div class="nav-group">
          <div v-if="!isCollapsed" class="nav-group-title">智能体模块</div>
          
          <!-- TARA智能体 -->
          <router-link to="/agents/tara" class="nav-item" :class="{ active: isActive('/agents/tara') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,3.18L19,6.3V11.22C19,15.54 16.19,19.52 12,20.5C7.81,19.52 5,15.54 5,11.22V6.3L12,3.18M11,7V13H13V7H11M11,15V17H13V15H11Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">TARA智能体</span>
              </transition>
            </div>
          </router-link>

          <!-- 测试用例智能体 -->
          <router-link to="/agents/testcase" class="nav-item" :class="{ active: isActive('/agents/testcase') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">测试用例智能体</span>
              </transition>
            </div>
          </router-link>

          <!-- 自动化测试智能体 -->
          <router-link to="/agents/automation" class="nav-item" :class="{ active: isActive('/agents/automation') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">自动化测试</span>
              </transition>
            </div>
          </router-link>

          <!-- 报告分析智能体 -->
          <router-link to="/agents/report" class="nav-item" :class="{ active: isActive('/agents/report') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">报告分析</span>
              </transition>
            </div>
          </router-link>

          <!-- 知识管理智能体 -->
          <router-link to="/agents/knowledge" class="nav-item" :class="{ active: isActive('/agents/knowledge') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M5,3H7V5H5V10A2,2 0 0,1 3,8V5A2,2 0 0,1 5,3M19,3A2,2 0 0,1 21,5V8A2,2 0 0,1 19,10V5H17V3H19M16,19H8V21H16V19M12,2A1,1 0 0,1 13,3V5H11V3A1,1 0 0,1 12,2Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">知识管理</span>
              </transition>
            </div>
          </router-link>
        </div>

        <!-- 系统管理 -->
        <div class="nav-group">
          <div v-if="!isCollapsed" class="nav-group-title">系统管理</div>
          
          <!-- 知识库 -->
          <router-link to="/knowledge" class="nav-item" :class="{ active: isActive('/knowledge') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">知识库</span>
              </transition>
            </div>
          </router-link>

          <!-- 模型配置 -->
          <router-link to="/models" class="nav-item" :class="{ active: isActive('/models') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M17,17H7V7H17M21,11V9H19V7C19,5.89 18.1,5 17,5H15V3H13V5H11V3H9V5H7C5.89,5 5,5.89 5,7V9H3V11H5V13H3V15H5V17C5,18.1 5.89,19 7,19H9V21H11V19H13V21H15V19H17C18.1,19 19,18.1 19,17V15H21V13H19V11M17,15H7V9H17V15Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">模型配置</span>
              </transition>
            </div>
          </router-link>

          <!-- 系统设置 -->
          <router-link to="/settings" class="nav-item" :class="{ active: isActive('/settings') }">
            <div class="nav-item-content">
              <div class="nav-icon">
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path fill="currentColor" d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
                </svg>
              </div>
              <transition name="nav-fade">
                <span v-show="!isCollapsed" class="nav-text">系统设置</span>
              </transition>
            </div>
          </router-link>
        </div>
      </nav>
    </div>

    <!-- 底部状态栏 -->
    <div class="status-section">
      <!-- 系统状态 -->
      <div class="status-indicator" :class="{ collapsed: isCollapsed }">
        <div class="status-content">
          <div class="status-dot" :class="statusClass"></div>
          <transition name="status-fade">
            <div v-show="!isCollapsed" class="status-info">
              <span class="status-text">{{ statusText }}</span>
              <span class="status-version">v{{ appStore.systemInfo.version }}</span>
            </div>
          </transition>
        </div>
      </div>

      <!-- 折叠按钮 -->
      <button class="collapse-btn" @click="toggleSidebar" :title="collapseTooltip">
        <div class="collapse-icon" :class="{ rotated: isCollapsed }">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z"/>
          </svg>
        </div>
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../../stores/app'

export default {
  name: 'AppSidebar',
  setup() {
    const route = useRoute()
    const appStore = useAppStore()

    // 计算属性
    const isCollapsed = computed(() => appStore.ui.sidebarCollapsed)
    
    const statusClass = computed(() => ({
      'status-healthy': appStore.systemInfo.status === 'healthy',
      'status-warning': appStore.systemInfo.status === 'warning', 
      'status-error': appStore.systemInfo.status === 'error'
    }))

    const statusText = computed(() => {
      const statusMap = {
        'healthy': '系统正常',
        'warning': '系统警告',
        'error': '系统异常'
      }
      return statusMap[appStore.systemInfo.status] || '未知状态'
    })

    const collapseTooltip = computed(() => {
      return isCollapsed.value ? '展开侧边栏' : '收起侧边栏'
    })

    // 方法
    const isActive = (path) => {
      return route.path === path || route.path.startsWith(path + '/')
    }

    const toggleSidebar = () => {
      appStore.toggleSidebar()
    }

    return {
      route,
      appStore,
      isCollapsed,
      statusClass,
      statusText,
      collapseTooltip,
      isActive,
      toggleSidebar
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

// 品牌区域
.brand-section {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-content {
  transition: all 0.3s ease;

  &.collapsed {
    text-align: center;
  }
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  min-width: 0;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.brand-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  margin: 2px 0 0 0;
  line-height: 1.2;
}

// 导航区域
.navigation-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }
}

.nav-menu {
  padding: 0 12px;
}

.nav-group {
  margin-bottom: 32px;

  &:last-child {
    margin-bottom: 16px;
  }
}

.nav-group-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 12px;
  padding: 0 12px;
}

.nav-item {
  display: block;
  margin-bottom: 4px;
  text-decoration: none;
  color: inherit;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(2px);
  }

  &.active {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: #ffffff;
    }
  }
}

.nav-item-content {
  display: flex;
  align-items: center;
  padding: 12px;
  gap: 12px;
  min-height: 44px;
}

.nav-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
  overflow: hidden;
}

// 状态区域
.status-section {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.status-indicator {
  margin-bottom: 16px;

  &.collapsed {
    text-align: center;
  }
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  
  &.status-healthy {
    background: #10b981;
    box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  }
  
  &.status-warning {
    background: #f59e0b;
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
  }
  
  &.status-error {
    background: #ef4444;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
  }
}

.status-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.status-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  line-height: 1.2;
}

.status-version {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.2;
}

// 折叠按钮
.collapse-btn {
  width: 100%;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.3);
  }

  &:active {
    transform: scale(0.98);
  }
}

.collapse-icon {
  transition: transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &.rotated {
    transform: rotate(180deg);
  }
}

// 过渡动画
.brand-fade-enter-active,
.brand-fade-leave-active,
.nav-fade-enter-active,
.nav-fade-leave-active,
.status-fade-enter-active,
.status-fade-leave-active {
  transition: all 0.3s ease;
}

.brand-fade-enter-from,
.brand-fade-leave-to,
.nav-fade-enter-from,
.nav-fade-leave-to,
.status-fade-enter-from,
.status-fade-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar-layout {
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);
  }
}
</style> 