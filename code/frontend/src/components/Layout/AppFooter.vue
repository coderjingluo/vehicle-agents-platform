<template>
  <el-footer class="app-footer" :class="footerClasses">
    <div class="footer-content">
      <!-- 左侧：版权信息 -->
      <div class="footer-left">
        <span class="copyright">
          © 2024 车联网安全测试平台 - 基于AI智能体的全生命周期管理系统
        </span>
      </div>

      <!-- 中间：系统状态指示器 -->
      <div class="footer-center">
        <div class="status-indicators">
          <!-- 数据库状态 -->
          <el-tooltip content="数据库连接状态" placement="top">
            <div class="status-item" :class="getDatabaseStatusClass()">
              <el-icon><Coin /></el-icon>
              <span class="status-label">DB</span>
            </div>
          </el-tooltip>

          <!-- Redis状态 -->
          <el-tooltip content="Redis缓存状态" placement="top">
            <div class="status-item" :class="getRedisStatusClass()">
              <el-icon><Cpu /></el-icon>
              <span class="status-label">Redis</span>
            </div>
          </el-tooltip>

          <!-- LLM连接状态 -->
          <el-tooltip content="AI模型连接状态" placement="top">
            <div class="status-item" :class="getLLMStatusClass()">
              <el-icon><Star /></el-icon>
              <span class="status-label">AI</span>
            </div>
          </el-tooltip>

          <!-- WebSocket状态 -->
          <el-tooltip content="实时连接状态" placement="top">
            <div class="status-item" :class="getWebSocketStatusClass()">
              <el-icon><Connection /></el-icon>
              <span class="status-label">WS</span>
            </div>
          </el-tooltip>
        </div>

        <!-- 当前活跃用户数 -->
        <div class="active-users">
          <el-icon><User /></el-icon>
          <span>{{ activeUsers }} 在线</span>
        </div>
      </div>

      <!-- 右侧：系统信息和快捷链接 -->
      <div class="footer-right">
        <!-- 系统版本 -->
        <div class="version-info">
          <span class="version">v{{ systemVersion }}</span>
          <el-divider direction="vertical" />
          <span class="build">构建 {{ buildNumber }}</span>
        </div>

        <!-- 快捷链接 -->
        <div class="quick-links">
          <el-button text size="small" @click="showApiDocs">
            API文档
          </el-button>
          <el-divider direction="vertical" />
          <el-button text size="small" @click="showSystemInfo">
            系统信息
          </el-button>
          <el-divider direction="vertical" />
          <el-button text size="small" @click="showAbout">
            关于
          </el-button>
        </div>
      </div>
    </div>

    <!-- 系统信息弹窗 -->
    <el-dialog
      v-model="systemInfoVisible"
      title="系统信息"
      width="500px"
      center
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="系统版本">{{ systemVersion }}</el-descriptions-item>
        <el-descriptions-item label="构建版本">{{ buildNumber }}</el-descriptions-item>
        <el-descriptions-item label="运行时间">{{ formatUptime(systemUptime) }}</el-descriptions-item>
        <el-descriptions-item label="最后检查">{{ lastHealthCheck }}</el-descriptions-item>
        <el-descriptions-item label="CPU使用率">
          <el-progress :percentage="systemStats.cpu" :show-text="true" :stroke-width="6" />
        </el-descriptions-item>
        <el-descriptions-item label="内存使用率">
          <el-progress :percentage="systemStats.memory" :show-text="true" :stroke-width="6" />
        </el-descriptions-item>
        <el-descriptions-item label="磁盘使用率" span="2">
          <el-progress :percentage="systemStats.disk" :show-text="true" :stroke-width="6" />
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="systemInfoVisible = false">关闭</el-button>
        <el-button type="primary" @click="refreshSystemStats">刷新</el-button>
      </template>
    </el-dialog>

    <!-- 关于弹窗 -->
    <el-dialog
      v-model="aboutVisible"
      title="关于系统"
      width="600px"
      center
    >
      <div class="about-content">
        <div class="about-header">
          <img src="/vite.svg" alt="Logo" class="about-logo">
          <div class="about-title">
            <h2>车联网安全测试生命周期管理平台</h2>
            <p>基于AI智能体的专业化安全测试解决方案</p>
          </div>
        </div>

        <el-divider />

        <div class="about-features">
          <h3>核心特性</h3>
          <ul>
            <li>🤖 5个专业AI智能体协同工作</li>
            <li>🔄 完整的测试生命周期管理</li>
            <li>📊 基于LangGraph的工作流引擎</li>
            <li>🛡️ 符合ISO 21434等国际标准</li>
            <li>📚 智能知识库与持续学习</li>
            <li>🌐 现代化Web界面与实时监控</li>
          </ul>
        </div>

        <el-divider />

        <div class="about-tech">
          <h3>技术栈</h3>
          <div class="tech-stack">
            <el-tag effect="light">Vue.js 3</el-tag>
            <el-tag effect="light">FastAPI</el-tag>
            <el-tag effect="light">LangGraph</el-tag>
            <el-tag effect="light">PostgreSQL</el-tag>
            <el-tag effect="light">Redis</el-tag>
            <el-tag effect="light">ChromaDB</el-tag>
            <el-tag effect="light">Element Plus</el-tag>
            <el-tag effect="light">WebSocket</el-tag>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="aboutVisible = false">关闭</el-button>
        <el-button type="primary" @click="openGithub">查看源码</el-button>
      </template>
    </el-dialog>
  </el-footer>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../../stores/app'
import { useWorkflowStore } from '../../stores/workflow'
import { systemAPI } from '../../api'
import {
  Coin, Cpu, Star, Connection, User
} from '@element-plus/icons-vue'

// 状态管理
const appStore = useAppStore()
const workflowStore = useWorkflowStore()

// 响应式数据
const systemInfoVisible = ref(false)
const aboutVisible = ref(false)
const activeUsers = ref(1)
const systemUptime = ref(0)
const uptimeInterval = ref(null)
const systemStats = ref({
  cpu: 0,
  memory: 0,
  disk: 0
})

// 系统信息
const systemVersion = ref('1.0.0')
const buildNumber = ref('20240101.001')

// 计算属性
const footerClasses = computed(() => ({
  'footer-dark': appStore.isDarkTheme
}))

const lastHealthCheck = computed(() => {
  if (!appStore.systemHealth.last_check) return '未检查'
  return new Date(appStore.systemHealth.last_check).toLocaleString('zh-CN')
})

// 状态检查方法
const getDatabaseStatusClass = () => ({
  'status-success': appStore.systemHealth.database,
  'status-error': !appStore.systemHealth.database
})

const getRedisStatusClass = () => ({
  'status-success': appStore.systemHealth.redis,
  'status-error': !appStore.systemHealth.redis
})

const getLLMStatusClass = () => ({
  'status-success': appStore.systemHealth.llm_client,
  'status-error': !appStore.systemHealth.llm_client
})

const getWebSocketStatusClass = () => ({
  'status-success': true, // WebSocket状态需要从WebSocket管理器获取
  'status-error': false
})

// 方法
const showApiDocs = () => {
  window.open('/docs', '_blank')
}

const showSystemInfo = async () => {
  systemInfoVisible.value = true
  await refreshSystemStats()
}

const showAbout = () => {
  aboutVisible.value = true
}

const refreshSystemStats = async () => {
  try {
    const stats = await appStore.getSystemStats()
    systemStats.value = {
      cpu: Math.round(stats.cpu_percent || 0),
      memory: Math.round(stats.memory_percent || 0),
      disk: Math.round(stats.disk_percent || 0)
    }
  } catch (error) {
    console.error('获取系统统计失败:', error)
  }
}

const formatUptime = (seconds) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`
  return `${Math.floor(seconds / 86400)}天`
}

const updateUptime = () => {
  systemUptime.value += 1
}

const openGithub = () => {
  window.open('https://github.com/your-repo', '_blank')
}

// 生命周期
onMounted(() => {
  // 模拟系统运行时间
  uptimeInterval.value = setInterval(updateUptime, 1000)
  
  // 定期刷新系统统计
  const statsInterval = setInterval(refreshSystemStats, 30000)
  
  onUnmounted(() => {
    if (uptimeInterval.value) {
      clearInterval(uptimeInterval.value)
    }
    clearInterval(statsInterval)
  })
})
</script>

<style scoped>
.app-footer {
  height: 40px;
  background-color: var(--el-bg-color-overlay);
  border-top: 1px solid var(--el-border-color-light);
  padding: 0 20px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  transition: all 0.3s ease;
}

.footer-dark {
  background-color: var(--el-bg-color);
  border-top-color: var(--el-border-color);
}

.footer-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 左侧版权信息 */
.footer-left {
  flex: 1;
  min-width: 0;
}

.copyright {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 中间状态指示器 */
.footer-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-indicators {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 12px;
  background-color: var(--el-fill-color-light);
  transition: all 0.3s ease;
  cursor: pointer;
}

.status-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-item.status-success {
  background-color: var(--el-color-success-light-8);
  color: var(--el-color-success);
}

.status-item.status-error {
  background-color: var(--el-color-danger-light-8);
  color: var(--el-color-danger);
}

.status-item .el-icon {
  font-size: 12px;
}

.status-label {
  font-size: 10px;
  font-weight: 500;
}

.active-users {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background-color: var(--el-fill-color-light);
  border-radius: 12px;
}

.active-users .el-icon {
  font-size: 12px;
}

/* 右侧信息 */
.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  justify-content: flex-end;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version, .build {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
}

.quick-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.quick-links .el-button {
  font-size: 11px;
  padding: 0 4px;
  height: 20px;
}

/* 弹窗样式 */
.about-content {
  padding: 16px 0;
}

.about-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.about-logo {
  width: 48px;
  height: 48px;
}

.about-title h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.about-title p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.about-features h3,
.about-tech h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.about-features ul {
  margin: 0;
  padding-left: 20px;
}

.about-features li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-footer {
    padding: 0 12px;
    font-size: 11px;
  }
  
  .footer-content {
    flex-direction: column;
    height: auto;
    padding: 8px 0;
    gap: 8px;
  }
  
  .footer-left,
  .footer-center,
  .footer-right {
    width: 100%;
    justify-content: center;
  }
  
  .copyright {
    text-align: center;
    font-size: 10px;
  }
  
  .status-indicators {
    justify-content: center;
  }
  
  .version-info,
  .quick-links {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .status-indicators {
    gap: 4px;
  }
  
  .status-item {
    padding: 2px 4px;
  }
  
  .status-label {
    display: none;
  }
  
  .footer-right {
    flex-direction: column;
    gap: 4px;
  }
}

/* 暗色主题适配 */
.footer-dark .status-item {
  background-color: var(--el-fill-color);
}

.footer-dark .active-users {
  background-color: var(--el-fill-color);
}

/* 动画效果 */
.status-item {
  position: relative;
  overflow: hidden;
}

.status-item::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, currentColor, transparent);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.1;
  transition: all 0.3s ease;
}

.status-item:hover::before {
  width: 100%;
  height: 100%;
}

/* 状态指示动画 */
.status-item.status-success .el-icon {
  animation: pulse-success 2s ease-in-out infinite;
}

.status-item.status-error .el-icon {
  animation: pulse-error 1s ease-in-out infinite;
}

@keyframes pulse-success {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes pulse-error {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 工具提示样式调整 */
:deep(.el-tooltip__popper) {
  font-size: 11px;
}

/* 描述列表样式 */
:deep(.el-descriptions) {
  margin-top: 16px;
}

:deep(.el-descriptions .el-descriptions__label) {
  font-weight: 600;
}

/* 进度条样式 */
:deep(.el-progress) {
  width: 100px;
}

:deep(.el-progress .el-progress__text) {
  font-size: 11px;
}
</style> 