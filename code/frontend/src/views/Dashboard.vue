<template>
  <div class="cursor-dashboard">
    <!-- 左侧任务面板 -->
    <div class="tasks-sidebar">
      <div class="sidebar-header">
        <h3>RECENT TASKS</h3>
      </div>
      <div class="tasks-list">
        <div 
          v-for="task in recentTasks" 
          :key="task.id" 
          class="task-item"
          :class="{ active: task.id === currentTaskId }"
          @click="selectTask(task)"
        >
          <div class="task-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="task-content">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-preview">{{ task.preview }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 中央聊天区域 -->
    <div class="chat-area">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="chat-info">
          <h2>KunlunSec</h2>
          <p>Step 6 (25.5k input, 159 completion)</p>
        </div>
        <div class="chat-actions">
          <el-button text class="action-btn">
            <el-icon><Plus /></el-icon>
            New Task
          </el-button>
          <el-button text class="action-btn">
            <el-icon><Share /></el-icon>
            Share
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div class="messages-list">
          <div v-for="message in messages" :key="message.id" class="message-wrapper">
            <!-- 用户消息 -->
            <div v-if="message.type === 'user'" class="message user-message">
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
              </div>
            </div>

            <!-- AI回复 -->
            <div v-else class="message ai-message">
              <div class="message-header">
                <div class="ai-info">
                  <div class="ai-avatar">
                    <span>★</span>
                  </div>
                  <span class="ai-name">KunlunSec</span>
                </div>
                <div class="message-meta">{{ formatTime(message.timestamp) }}</div>
              </div>
              <div class="message-content">
                <div class="message-text" v-html="message.content"></div>
              </div>
            </div>
          </div>

          <!-- AI正在输入 -->
          <div v-if="isTyping" class="message ai-message typing">
            <div class="message-header">
              <div class="ai-info">
                <div class="ai-avatar">
                  <span>★</span>
                </div>
                <span class="ai-name">KunlunSec</span>
              </div>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="currentMessage"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="请描述您需要的网络安全分析任务..."
            class="message-input"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.ctrl.enter.exact="addNewLine"
          />
          <div class="input-actions">
            <el-button 
              text 
              class="config-btn"
              @click="showToolsConfig"
              title="工具配置"
            >
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button 
              type="primary" 
              :disabled="!currentMessage.trim() || isTyping"
              @click="sendMessage"
              class="send-btn"
            >
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="input-hint">
          使用 ⌘+L 快速提问 • ⌘+K 搜索 • Ctrl+Enter 换行
        </div>
      </div>
    </div>

    <!-- Tools Configuration 对话框 -->
    <el-dialog
      v-model="toolsConfigVisible"
      title="Tools Configuration"
      width="600px"
      :show-close="true"
      class="tools-config-dialog"
      :modal-class="'tools-config-modal'"
    >
      <ToolsConfig @apply="applyToolsConfig" @close="toolsConfigVisible = false" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Clock, Plus, Share, Promotion, Setting } from '@element-plus/icons-vue'
import ToolsConfig from '../components/common/ToolsConfig.vue'

// 响应式数据
const currentMessage = ref('')
const isTyping = ref(false)
const currentTaskId = ref(1)
const messagesContainer = ref(null)
const toolsConfigVisible = ref(false)

// 最近任务列表
const recentTasks = ref([
  {
    id: 1,
    title: '通过我们的ctf知识进行...',
    preview: '请帮我们通过我们的ctf知识进行渗透测试或者分析这个靶机'
  },
  {
    id: 2,
    title: '通过我们的ctf知识进行...',
    preview: '在这个任务中，我需要你帮助分析网络安全相关的问题'
  },
  {
    id: 3,
    title: 'pwn分析，本地搭建环境...',
    preview: 'pwn分析，本地搭建环境，需要完成二进制漏洞利用分析'
  },
  {
    id: 4,
    title: '安全requirements分析...',
    preview: '对目标系统进行全面的安全需求分析和风险评估'
  },
  {
    id: 5,
    title: '漏洞扫描和检测...',
    preview: '使用自动化工具对Web应用进行漏洞扫描'
  },
  {
    id: 6,
    title: '网络流量分析...',
    preview: '分析网络数据包，查找异常流量和潜在威胁'
  }
])

// 聊天消息
const messages = ref([
  {
    id: 1,
    type: 'user',
    content: '当前状态：已登录获取到用户，漏洞扫描已完成，需要执行：netstat -ano 检查网络连接',
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: 2,
    type: 'assistant',
    content: '我理解您需要检查当前系统的网络连接状态。我将执行 `netstat -ano` 命令来获取详细的网络连接信息，包括监听端口和进程信息。\n\n让我为您执行这个命令：',
    timestamp: new Date(Date.now() - 240000)
  },
  {
    id: 3,
    type: 'user',
    content: '立即执行以下任务：执行 netstat /query /fo LIST 命令，检查系统网络连接状况。',
    timestamp: new Date(Date.now() - 60000)
  },
  {
    id: 4,
    type: 'assistant',
    content: '我正在为您执行网络连接检查命令。让我使用 `schtasks /query /fo LIST` 来查看系统任务，然后进行网络状态分析：\n\n执行任务下列表：',
    timestamp: new Date(Date.now() - 30000)
  }
])

// 方法
const selectTask = (task) => {
  currentTaskId.value = task.id
  // 可以在这里加载特定任务的聊天历史
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isTyping.value) return

  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: currentMessage.value.trim(),
    timestamp: new Date()
  }
  messages.value.push(userMessage)

  const messageText = currentMessage.value.trim()
  currentMessage.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 模拟AI响应
  isTyping.value = true
  setTimeout(async () => {
    const aiResponse = generateAIResponse(messageText)
    messages.value.push({
      id: Date.now(),
      type: 'assistant',
      content: aiResponse,
      timestamp: new Date()
    })
    isTyping.value = false
    await nextTick()
    scrollToBottom()
  }, 2000)
}

const addNewLine = () => {
  currentMessage.value += '\n'
}

const generateAIResponse = (userMessage) => {
  const responses = {
    '网络': '我将帮您分析网络安全状况。让我执行相关的网络检测命令来获取详细信息。',
    '漏洞': '正在进行漏洞扫描和分析。我会使用专业的安全工具来识别潜在的安全风险。',
    'netstat': '正在执行网络连接检查命令 `netstat -ano`，这将显示所有活动的网络连接和监听端口。',
    'pwn': '开始进行二进制漏洞分析。我将设置本地调试环境并分析目标二进制文件的安全漏洞。',
    '扫描': '启动自动化安全扫描程序。正在检测目标系统的开放端口、服务版本和潜在漏洞。'
  }

  const message = userMessage.toLowerCase()
  for (const [key, response] of Object.entries(responses)) {
    if (message.includes(key)) {
      return response
    }
  }

  return `我正在分析您的请求："${userMessage}"。请稍等，我将为您提供详细的安全分析结果。`
}

const formatTime = (timestamp) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(timestamp)
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const showToolsConfig = () => {
  toolsConfigVisible.value = true
}

const applyToolsConfig = () => {
  // 实现工具配置应用逻辑
}

// 生命周期
onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.cursor-dashboard {
  height: 100%;
  display: flex;
  background: #1e1e1e;
  color: #cccccc;
}

/* ========== 左侧任务面板 ========== */
.tasks-sidebar {
  width: 200px;
  background: #252526;
  border-right: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #3c3c3c;
}

.sidebar-header h3 {
  font-size: 11px;
  font-weight: 600;
  color: #9d9d9d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.tasks-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 4px;
}

.task-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.task-item.active {
  background: rgba(0, 122, 204, 0.15);
  border: 1px solid rgba(0, 122, 204, 0.3);
}

.task-icon {
  color: #9d9d9d;
  font-size: 14px;
  margin-top: 2px;
  flex-shrink: 0;
}

.task-content {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 13px;
  color: #cccccc;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-preview {
  font-size: 11px;
  color: #9d9d9d;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* ========== 中央聊天区域 ========== */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  height: 50px;
  background: #1e1e1e;
  border-bottom: 1px solid #3c3c3c;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.chat-info h2 {
  font-size: 16px;
  color: #cccccc;
  margin: 0 0 2px 0;
  font-weight: 600;
}

.chat-info p {
  font-size: 12px;
  color: #9d9d9d;
  margin: 0;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  color: #9d9d9d;
  font-size: 13px;
  height: 32px;
  padding: 0 12px;
}

.action-btn:hover {
  color: #cccccc;
  background: rgba(255, 255, 255, 0.05);
}

/* 消息区域 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.messages-list {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.message-wrapper {
  margin-bottom: 24px;
}

.message {
  display: flex;
  flex-direction: column;
}

.user-message {
  align-items: flex-end;
}

.user-message .message-content {
  background: #007acc;
  color: white;
  border-radius: 18px 18px 4px 18px;
  padding: 12px 16px;
  max-width: 70%;
  word-wrap: break-word;
}

.ai-message .message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.ai-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-avatar {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
  font-weight: bold;
}

.ai-name {
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
}

.message-meta {
  font-size: 11px;
  color: #6c6c6c;
}

.ai-message .message-content {
  background: #2d2d30;
  border: 1px solid #3c3c3c;
  border-radius: 12px;
  padding: 16px;
  max-width: 85%;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  color: #cccccc;
  white-space: pre-wrap;
}

/* 输入状态 */
.typing .message-content {
  background: #2d2d30;
  border: 1px solid #3c3c3c;
  border-radius: 12px;
  padding: 16px;
  max-width: 85%;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9d9d9d;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* ========== 输入区域 ========== */
.input-area {
  background: #252526;
  border-top: 1px solid #3c3c3c;
  padding: 16px 20px;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  color: #cccccc;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: #007acc;
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
}

.config-btn {
  height: 40px;
  width: 40px;
  border-radius: 50%;
  background: #464647;
  border: 1px solid #6c6c6c;
  color: #cccccc;
  font-size: 16px;
  flex-shrink: 0;
  margin-right: 8px;
}

.config-btn:hover {
  background: #6c6c6c;
  border-color: #007acc;
  color: #ffffff;
}

.send-btn {
  height: 40px;
  width: 40px;
  border-radius: 50%;
  background: #007acc;
  border: none;
  font-size: 16px;
  flex-shrink: 0;
}

.send-btn:hover {
  background: #005a99;
}

.send-btn:disabled {
  background: #464647;
  color: #6c6c6c;
}

.input-hint {
  font-size: 11px;
  color: #6c6c6c;
  text-align: center;
  margin-top: 8px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

/* Tools Configuration 对话框样式 */
:deep(.tools-config-modal) {
  background: rgba(0, 0, 0, 0.5);
}

:deep(.tools-config-dialog) {
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
}

:deep(.tools-config-dialog .el-dialog__header) {
  background: #2c2c2c;
  border-bottom: 1px solid #3c3c3c;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
}

:deep(.tools-config-dialog .el-dialog__title) {
  color: #cccccc;
  font-size: 16px;
  font-weight: 600;
}

:deep(.tools-config-dialog .el-dialog__headerbtn) {
  top: 16px;
  right: 20px;
}

:deep(.tools-config-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #9d9d9d;
  font-size: 16px;
}

:deep(.tools-config-dialog .el-dialog__headerbtn .el-dialog__close:hover) {
  color: #cccccc;
}

:deep(.tools-config-dialog .el-dialog__body) {
  padding: 20px;
  background: #252526;
  max-height: 60vh;
  overflow-y: auto;
  border-radius: 0 0 8px 8px;
}

:deep(.tools-config-dialog .el-dialog__body::-webkit-scrollbar) {
  width: 6px;
}

:deep(.tools-config-dialog .el-dialog__body::-webkit-scrollbar-track) {
  background: #1e1e1e;
}

:deep(.tools-config-dialog .el-dialog__body::-webkit-scrollbar-thumb) {
  background: #464647;
  border-radius: 3px;
}

:deep(.tools-config-dialog .el-dialog__body::-webkit-scrollbar-thumb:hover) {
  background: #6c6c6c;
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .cursor-dashboard {
    flex-direction: column;
  }
  
  .tasks-sidebar {
    width: 100%;
    height: 150px;
    border-right: none;
    border-bottom: 1px solid #3c3c3c;
  }
  
  .tasks-list {
    display: flex;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 8px;
    gap: 8px;
  }
  
  .task-item {
    min-width: 200px;
    flex-shrink: 0;
  }
  
  .messages-list {
    padding: 16px;
  }
  
  .input-area {
    padding: 12px 16px;
  }
}
</style> 