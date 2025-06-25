<script setup>
import { computed, ref, onMounted, provide } from 'vue'
import { useAppStore } from './stores/app'
import { useRoute } from 'vue-router'
import NotificationCenter from './components/common/NotificationCenter.vue'
import {
  House, Document, Setting, User, Moon, Close
} from '@element-plus/icons-vue'

// 状态管理
const appStore = useAppStore()
const route = useRoute()

// 响应式数据
const rightPanelTitle = ref('Tool Workspace')
const rightPanelComponent = ref('ToolWorkspace')
const rightPanelProps = ref({})

// 计算属性
const isDarkTheme = computed(() => appStore.isDarkTheme || true) // 默认深色主题

// 计算是否显示右侧面板 - 在主页和智能体页面显示
const showRightPanel = computed(() => {
  return route.path === '/' || 
         route.path === '/dashboard' || 
         route.path.startsWith('/agents/')
})

// 方法
const toggleTheme = () => {
  appStore.toggleTheme()
}

const toggleRightPanel = () => {
  // 仅在允许显示右侧面板的页面才能切换
  if (showRightPanel.value) {
    // 可以在这里添加强制隐藏逻辑
    console.log('Toggle right panel')
  }
}

// 全局方法：显示右侧面板
const showRightPanelWith = (title, component, props = {}) => {
  // 只在聊天页面允许显示右侧面板
  if (showRightPanel.value) {
    rightPanelTitle.value = title
    rightPanelComponent.value = component
    rightPanelProps.value = props
  }
}

// 生命周期
onMounted(() => {
  // 初始化应用状态
  appStore.initializeApp()
  // 设置深色主题
  document.documentElement.classList.add('dark')
})

// 全局提供方法
provide('showRightPanel', showRightPanelWith)
provide('toggleRightPanel', toggleRightPanel)
</script>

<template>
  <div id="app" class="cursor-app">
    <!-- 主要布局容器 -->
    <div class="app-layout">
      <!-- 左侧Activity Bar -->
      <aside class="activity-bar">
        <!-- 品牌Logo -->
        <div class="brand-section">
          <div class="brand-logo">
            <img src="/vite.svg" alt="KunlunSec" />
          </div>
        </div>

        <!-- 导航图标 -->
        <nav class="activity-nav">
          <router-link 
            to="/" 
            class="activity-item"
            :class="{ active: $route.path === '/' }"
            title="主页"
          >
            <el-icon><House /></el-icon>
          </router-link>

          <router-link 
            to="/knowledge" 
            class="activity-item"
            :class="{ active: $route.path === '/knowledge' }"
            title="知识库"
          >
            <el-icon><Document /></el-icon>
          </router-link>

          <router-link 
            to="/mcp-tools" 
            class="activity-item"
            :class="{ active: $route.path === '/mcp-tools' }"
            title="MCP工具"
          >
            <el-icon><Setting /></el-icon>
          </router-link>
        </nav>

        <!-- 底部操作 -->
        <div class="activity-footer">
          <div class="activity-item" @click="toggleTheme" title="切换主题">
            <el-icon><House v-if="isDarkTheme" /><Moon v-else /></el-icon>
          </div>
          <div class="activity-item user-avatar" title="用户">
            <el-icon><User /></el-icon>
          </div>
        </div>
      </aside>

      <!-- 中央主要内容区域 -->
      <main class="main-workspace" :class="{ 'panel-open': showRightPanel }">
        <router-view />
      </main>

      <!-- 右侧工具面板 -->
      <aside class="tool-panel" v-if="showRightPanel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Setting /></el-icon>
            <span>{{ rightPanelTitle }}</span>
          </div>
          <el-button text @click="toggleRightPanel" class="close-btn">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="panel-content">
          <!-- 工具工作区组件 -->
          <div class="tool-workspace">
            <div class="workspace-header">
              <h3>KunlunSec Computer</h3>
              <p>KunlunSec is using tool_1749948061732-execute_command</p>
            </div>
            
            <div class="tool-execution">
              <div class="execution-header">
                <el-icon><Setting /></el-icon>
                <span>Tool Execution</span>
              </div>
              
              <div class="tool-details">
                <div class="tool-name">
                  <el-icon><Setting /></el-icon>
                  1749948061732-execute_command
                </div>
                
                <div class="parameters-section">
                  <h4>Parameters</h4>
                  <div class="param-item">
                    <span class="param-key">shell</span>
                    <span class="param-value">cmd</span>
                  </div>
                  <div class="param-item">
                    <span class="param-key">command</span>
                    <span class="param-value">schtasks /query /fo LIST</span>
                  </div>
                </div>

                <div class="result-section">
                  <h4>Result</h4>
                  <div class="result-content">
                    <pre>任务名: \Microsoft\Windows\HelloFace\FODCleanupTask
下次运行时间: 暂缺
状态: 就绪
登录模式: 交互/后台</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- 全局通知 -->
    <NotificationCenter />
  </div>
</template>

<style>
/* 全局重置和深色主题 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1e1e1e;
  color: #cccccc;
}

#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* Element Plus 深色主题变量覆盖 */
:root {
  --el-bg-color-page: #1e1e1e;
  --el-bg-color: #252526;
  --el-bg-color-overlay: #2d2d30;
  --el-border-color: #3c3c3c;
  --el-border-color-light: #464647;
  --el-text-color-primary: #cccccc;
  --el-text-color-regular: #9d9d9d;
  --el-text-color-secondary: #6c6c6c;
  --el-color-primary: #007acc;
  --el-color-primary-light-3: #4fc3f7;
  --el-color-primary-light-5: #81d4fa;
  --el-color-primary-light-7: #b3e5fc;
  --el-color-primary-light-8: #e1f5fe;
  --el-color-primary-light-9: #f0f9ff;
  --el-fill-color-light: rgba(255, 255, 255, 0.08);
  --el-fill-color: rgba(255, 255, 255, 0.04);
}
</style>

<style scoped>
.cursor-app {
  height: 100vh;
  background: #1e1e1e;
  color: #cccccc;
  overflow: hidden;
}

.app-layout {
  display: flex;
  height: 100vh;
}

/* ========== 左侧Activity Bar ========== */
.activity-bar {
  width: 48px;
  background: #2c2c2c;
  border-right: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 100;
}

.brand-section {
  padding: 8px 0;
  border-bottom: 1px solid #3c3c3c;
  width: 100%;
  display: flex;
  justify-content: center;
}

.brand-logo {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-logo img {
  width: 24px;
  height: 24px;
}

.activity-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  gap: 4px;
  width: 100%;
  align-items: center;
}

.activity-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9d9d9d;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
  font-size: 18px;
  position: relative;
}

.activity-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #cccccc;
}

.activity-item.active {
  color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.activity-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 20px;
  background: #007acc;
}

.activity-footer {
  padding: 8px 0;
  border-top: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  align-items: center;
}

.user-avatar {
  margin-bottom: 8px;
}

/* ========== 中央主要内容区域 ========== */
.main-workspace {
  flex: 1;
  background: #1e1e1e;
  transition: all 0.3s ease;
  min-width: 0;
}

/* 当有右侧面板时不需要特殊样式，当没有右侧面板时占满剩余空间 */

/* ========== 右侧工具面板 ========== */
.tool-panel {
  width: 450px;
  background: #252526;
  border-left: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
  z-index: 50;
}

.panel-header {
  height: 35px;
  background: #2c2c2c;
  border-bottom: 1px solid #3c3c3c;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #cccccc;
  font-weight: 500;
}

.close-btn {
  color: #9d9d9d;
  font-size: 14px;
  padding: 2px;
  height: 20px;
  width: 20px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* 工具工作区样式 */
.tool-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workspace-header h3 {
  font-size: 16px;
  color: #cccccc;
  margin-bottom: 4px;
}

.workspace-header p {
  font-size: 12px;
  color: #9d9d9d;
  line-height: 1.4;
}

.tool-execution {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  overflow: hidden;
}

.execution-header {
  background: #2c2c2c;
  padding: 8px 12px;
  border-bottom: 1px solid #3c3c3c;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #cccccc;
  font-weight: 500;
}

.tool-details {
  padding: 12px;
}

.tool-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #007acc;
  margin-bottom: 16px;
  font-family: 'SF Mono', Monaco, 'Consolas', monospace;
}

.parameters-section,
.result-section {
  margin-bottom: 16px;
}

.parameters-section h4,
.result-section h4 {
  font-size: 12px;
  color: #9d9d9d;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.param-item {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, 'Consolas', monospace;
}

.param-key {
  color: #9cdcfe;
  min-width: 60px;
}

.param-value {
  color: #ce9178;
}

.result-content {
  background: #0c0c0c;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  padding: 8px;
  font-family: 'SF Mono', Monaco, 'Consolas', monospace;
  font-size: 11px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
}

.result-content pre {
  color: #d4d4d4;
  white-space: pre-wrap;
  margin: 0;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .tool-panel {
    width: 100%;
    position: absolute;
    right: 0;
    top: 0;
    height: 100vh;
    z-index: 1000;
  }
  
  .main-workspace.panel-open {
    margin-right: 0;
  }
}
</style>
