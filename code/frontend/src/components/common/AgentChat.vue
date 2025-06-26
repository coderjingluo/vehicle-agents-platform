<template>
  <div class="agent-chat">
    <!-- 聊天消息区域 -->
    <div class="chat-container" ref="chatContainer">
      <div class="chat-messages">
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="`message-${message.type}`"
        >
          <div class="message-header">
            <div class="message-avatar">
              <el-icon v-if="message.type === 'user'"><User /></el-icon>
              <el-icon v-else-if="message.type === 'system'"><Monitor /></el-icon>
              <div v-else class="agent-avatar">
                <el-icon><Cpu /></el-icon>
                <span class="agent-name">{{ getAgentName(message.agentType) }}</span>
              </div>
            </div>
            <div class="message-meta">
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              <el-tag
                v-if="message.status"
                :type="getStatusType(message.status)"
                size="small"
              >
                {{ getStatusText(message.status) }}
              </el-tag>
            </div>
          </div>

          <div class="message-content">
            <!-- 用户消息 -->
            <div v-if="message.type === 'user'" class="user-message">
              {{ message.content }}
            </div>

            <!-- 智能体分析消息 -->
            <div v-else-if="message.type === 'agent'" class="agent-message">
              <!-- 步骤分配 -->
              <div v-if="message.stepType === 'planning'" class="planning-section">
                <h4>
                  <el-icon><Operation /></el-icon>
                  智能步骤分配
                </h4>
                <div class="planning-content">
                  <p>{{ message.content }}</p>
                  <div v-if="message.steps" class="planned-steps">
                    <div
                      v-for="(step, index) in message.steps"
                      :key="index"
                      class="planned-step"
                      :class="{ 'active': step.status === 'running', 'completed': step.status === 'completed' }"
                    >
                      <div class="step-number">{{ index + 1 }}</div>
                      <div class="step-content">
                        <div class="step-title">{{ step.title }}</div>
                        <div class="step-description">{{ step.description }}</div>
                        <div v-if="step.tools" class="step-tools">
                          <el-tag
                            v-for="tool in step.tools"
                            :key="tool"
                            size="small"
                            type="info"
                          >
                            {{ tool }}
                          </el-tag>
                        </div>
                      </div>
                      <div class="step-status">
                        <el-icon v-if="step.status === 'completed'"><CircleCheckFilled /></el-icon>
                        <el-icon v-else-if="step.status === 'running'" class="spinning"><Loading /></el-icon>
                        <el-icon v-else><Clock /></el-icon>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 步骤执行 -->
              <div v-else-if="message.stepType === 'execution'" class="execution-section">
                <h4>
                  <el-icon><VideoPlay /></el-icon>
                  {{ message.stepName }}
                  <span class="step-progress" v-if="message.progress">
                    ({{ message.progress }}% 完成)
                  </span>
                </h4>
                <div class="execution-content">
                  <div class="execution-description">{{ message.content }}</div>
                  
                  <!-- 进度条 -->
                  <el-progress
                    v-if="message.progress !== undefined"
                    :percentage="message.progress"
                    :status="message.status === 'completed' ? 'success' : ''"
                    :show-text="false"
                    class="execution-progress"
                  />

                  <!-- 工具调用信息 -->
                  <div v-if="message.toolCalls" class="tool-calls">
                    <div
                      v-for="(call, index) in message.toolCalls"
                      :key="index"
                      class="tool-call"
                    >
                      <div class="tool-call-header">
                        <el-icon><Tools /></el-icon>
                        <span class="tool-name">{{ call.tool }}</span>
                        <el-tag :type="getToolCallStatus(call.status)" size="small">
                          {{ call.status }}
                        </el-tag>
                      </div>
                      <div class="tool-call-content">
                        <div class="tool-input">
                          <strong>输入:</strong> {{ call.input }}
                        </div>
                        <div v-if="call.output" class="tool-output">
                          <strong>输出:</strong> {{ call.output }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 实时输出 -->
                  <div v-if="message.realTimeOutput" class="real-time-output">
                    <div class="output-header">
                      <el-icon><Monitor /></el-icon>
                      实时输出
                    </div>
                    <div class="output-content">
                      <pre>{{ message.realTimeOutput }}</pre>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 结果总结 -->
              <div v-else-if="message.stepType === 'result'" class="result-section">
                <h4>
                  <el-icon><CircleCheckFilled /></el-icon>
                  执行结果
                </h4>
                <div class="result-content">
                  <div class="result-summary">{{ message.content }}</div>
                  
                  <!-- 结果数据 -->
                  <div v-if="message.resultData" class="result-data">
                    <div
                      v-for="(item, key) in message.resultData"
                      :key="key"
                      class="result-item"
                    >
                      <strong>{{ key }}:</strong> {{ item }}
                    </div>
                  </div>

                  <!-- 下载链接 -->
                  <div v-if="message.downloadLinks" class="download-links">
                    <el-button
                      v-for="link in message.downloadLinks"
                      :key="link.url"
                      type="primary"
                      size="small"
                      @click="downloadFile(link.url, link.filename)"
                    >
                      <el-icon><Download /></el-icon>
                      {{ link.filename }}
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 一般消息 -->
              <div v-else class="general-message">
                <div class="message-text">{{ message.content }}</div>
              </div>
            </div>

            <!-- 系统消息 -->
            <div v-else-if="message.type === 'system'" class="system-message">
              <el-alert
                :type="message.level || 'info'"
                :title="message.content"
                :show-icon="true"
                :closable="false"
              />
            </div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="isTyping" class="typing-indicator">
          <div class="typing-avatar">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="typing-content">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div class="typing-text">{{ currentAgentName }} 正在思考...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area" v-if="!isExecuting">
      <div class="input-container">
        <el-input
          v-model="userInput"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="请描述您需要的分析任务..."
          @keydown.enter.prevent="handleSendMessage"
          class="user-input"
        />
        <el-button
          type="primary"
          :disabled="!userInput.trim() || isTyping"
          @click="handleSendMessage"
          class="send-button"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="chat-controls" v-if="isExecuting">
      <el-button @click="stopExecution" type="danger" size="small">
        <el-icon><VideoPause /></el-icon>
        停止执行
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  User, Monitor, Cpu, Operation, VideoPlay, CircleCheckFilled, Loading,
  Clock, Tools, Download, Promotion, VideoPause
} from '@element-plus/icons-vue'
import agentsAPI from '../../api/modules/agents'

// Props
const props = defineProps({
  agentType: {
    type: String,
    default: 'tara'
  },
  initialContext: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['execution-start', 'execution-complete', 'execution-error'])

// 响应式数据
const chatContainer = ref()
const userInput = ref('')
const messages = ref([])
const isTyping = ref(false)
const isExecuting = ref(false)
const currentAgentName = ref('')
const currentExecutionId = ref(null)

// WebSocket连接
let websocket = null
let reconnectTimer = null

// 计算属性
const agentNames = {
  'tara': 'TARA智能体',
  'test_case': '测试用例智能体',
  'automation_test': '自动化测试智能体',
  'report_analysis': '报告分析智能体',
  'knowledge_base': '知识库智能体'
}

// 方法
const getAgentName = (agentType) => {
  return agentNames[agentType] || agentType
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const getStatusType = (status) => {
  const statusTypes = {
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'pending': 'info'
  }
  return statusTypes[status] || 'info'
}

const getStatusText = (status) => {
  const statusTexts = {
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'pending': '等待中'
  }
  return statusTexts[status] || status
}

const getToolCallStatus = (status) => {
  const types = {
    'success': 'success',
    'running': 'warning',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

// 发送消息
const handleSendMessage = async () => {
  if (!userInput.value.trim() || isTyping.value) return

  const messageContent = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息
  addMessage({
    type: 'user',
    content: messageContent,
    timestamp: new Date()
  })

  await startAgentExecution(messageContent)
}

// 开始智能体执行
const startAgentExecution = async (userRequest) => {
  try {
    isExecuting.value = true
    isTyping.value = true
    currentAgentName.value = getAgentName(props.agentType)

    emit('execution-start')

    // 构建执行参数
    const executionParams = {
      user_request: userRequest,
      context: {
        ...props.initialContext,
      },
      stream: true,
      timeout: 300,
      priority: "normal",
      metadata: {
        source: "chat_ui",
        version: "1.0"
      },
      enable_planning: true,
      step_by_step: true,
      chat_mode: true,
      agent_config: {
        model: "default"
      }
    }

    // 开始流式执行
    await startStreamExecutionWithPlanning(executionParams)

  } catch (error) {
    console.error('智能体执行失败:', error)
    addMessage({
      type: 'system',
      content: `执行失败: ${error.message}`,
      level: 'error',
      timestamp: new Date()
    })
    emit('execution-error', error)
  } finally {
    isExecuting.value = false
    isTyping.value = false
  }
}

// 流式执行
const startStreamExecution = async (params) => {
  try {
    const reader = await agentsAPI.streamAgentExecution(props.agentType, params)
    
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      // 解码响应数据
      const chunk = new TextDecoder().decode(value)
      buffer += chunk
      
      // 处理完整的行
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.trim().startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            await handleStreamData(data)
          } catch (parseError) {
            console.warn('流式数据解析失败:', parseError)
          }
        }
      }
    }
    
    emit('execution-complete')
    
  } catch (error) {
    console.error('流式执行失败:', error)
    throw error
  }
}

// 带智能规划的流式执行
const startStreamExecutionWithPlanning = async (params) => {
  try {
    const reader = await agentsAPI.streamAgentExecutionWithPlanning(props.agentType, params)
    
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      // 解码响应数据
      const chunk = new TextDecoder().decode(value)
      buffer += chunk
      
      // 处理完整的行
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.trim().startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            await handleStreamData(data)
          } catch (parseError) {
            console.warn('流式数据解析失败:', parseError)
          }
        }
      }
    }
    
    emit('execution-complete')
    
  } catch (error) {
    console.error('流式执行失败:', error)
    throw error
  }
}

// 处理流式数据
const handleStreamData = async (data) => {
  switch (data.type || data.event_type) {
    case 'planning':
    case 'plan':
      // 智能步骤分配
      addMessage({
        type: 'agent',
        agentType: props.agentType,
        stepType: 'planning',
        content: data.message || data.data?.message || '正在分析任务需求并制定执行计划...',
        steps: data.steps || data.data?.steps || [],
        timestamp: new Date()
      })
      break
      
    case 'step_start':
    case 'start':
      // 步骤开始
      addMessage({
        type: 'agent',
        agentType: props.agentType,
        stepType: 'execution',
        stepName: data.step_name || data.data?.step_name || '执行步骤',
        content: data.message || data.data?.message || `开始执行: ${data.step_name || data.data?.step_name || '执行步骤'}`,
        progress: 0,
        timestamp: new Date()
      })
      break
      
    case 'step_progress':
    case 'progress':
      // 步骤进度更新
      updateLastMessage({
        progress: data.progress || data.data?.progress,
        content: data.message || data.data?.message,
        realTimeOutput: data.output || data.data?.output,
        toolCalls: data.tool_calls || data.data?.tool_calls
      })
      break
      
    case 'step_completed':
    case 'step_complete':
    case 'complete':
      // 步骤完成
      updateLastMessage({
        status: 'completed',
        progress: 100,
        content: data.message || data.data?.message || '步骤执行完成'
      })
      break
      
    case 'result':
    case 'completion':
      // 最终结果
      addMessage({
        type: 'agent',
        agentType: props.agentType,
        stepType: 'result',
        content: data.message || data.data?.message || '任务执行完成',
        resultData: data.result_data || data.data?.result || data.result,
        downloadLinks: data.download_links || data.data?.download_links,
        timestamp: new Date()
      })
      break
      
    case 'error':
      // 错误处理
      addMessage({
        type: 'system',
        content: data.message || data.data?.message || '执行过程中发生错误',
        level: 'error',
        timestamp: new Date()
      })
      break
      
    default:
      // 一般消息
      if (data.message || (data.data && data.data.message)) {
        addMessage({
          type: 'agent',
          agentType: props.agentType,
          content: data.message || data.data?.message,
          timestamp: new Date()
        })
      }
  }
  
  await scrollToBottom()
}

// 添加消息
const addMessage = (message) => {
  const id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  messages.value.push({
    id,
    ...message
  })
}

// 更新最后一条消息
const updateLastMessage = (updates) => {
  if (messages.value.length === 0) return
  
  const lastMessage = messages.value[messages.value.length - 1]
  Object.assign(lastMessage, updates)
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    const container = chatContainer.value
    container.scrollTop = container.scrollHeight
  }
}

// 停止执行
const stopExecution = () => {
  if (currentExecutionId.value) {
    agentsAPI.cancelTask(currentExecutionId.value)
  }
  isExecuting.value = false
  isTyping.value = false
  
  addMessage({
    type: 'system',
    content: '用户已停止执行',
    level: 'warning',
    timestamp: new Date()
  })
}

// 下载文件
const downloadFile = (url, filename) => {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
}

// 清空聊天
const clearChat = () => {
  messages.value = []
}

// 暴露方法
defineExpose({
  clearChat,
  addMessage,
  startAgentExecution
})

// 生命周期
onMounted(() => {
  // 添加欢迎消息
  addMessage({
    type: 'agent',
    agentType: props.agentType,
    content: `您好！我是${getAgentName(props.agentType)}，请告诉我您需要进行什么分析？`,
    timestamp: new Date()
  })
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})
</script>

<style scoped>
.agent-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color);
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background: var(--el-fill-color-light);
  font-size: 14px;
  font-weight: 500;
}

.agent-avatar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.message-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-content {
  padding-left: 16px;
}

.user-message {
  background: var(--el-color-primary-light-9);
  padding: 12px 16px;
  border-radius: 12px;
  border-left: 3px solid var(--el-color-primary);
}

.agent-message {
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  overflow: hidden;
}

.planning-section,
.execution-section,
.result-section {
  padding: 16px;
}

.planning-section h4,
.execution-section h4,
.result-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.planned-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.planned-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  transition: all 0.2s ease;
}

.planned-step.active {
  border-color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.planned-step.completed {
  border-color: var(--el-color-success);
  background: var(--el-color-success-light-9);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.step-description {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.step-tools {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.step-status {
  display: flex;
  align-items: center;
  color: var(--el-color-success);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.execution-progress {
  margin: 12px 0;
}

.tool-calls {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-call {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 8px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.tool-name {
  font-weight: 500;
}

.tool-call-content {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.real-time-output {
  margin-top: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}

.output-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
  font-size: 12px;
  font-weight: 500;
}

.output-content {
  padding: 8px 12px;
  max-height: 200px;
  overflow-y: auto;
}

.output-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  line-height: 1.4;
  white-space: pre-wrap;
}

.result-data {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 12px 0;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
}

.result-item {
  font-size: 14px;
}

.download-links {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.system-message {
  margin-left: 16px;
}

.typing-indicator {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.typing-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--el-fill-color-light);
}

.typing-content {
  flex: 1;
}

.typing-dots {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-primary);
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

.typing-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.user-input {
  flex: 1;
}

.send-button {
  flex-shrink: 0;
}

.chat-controls {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color);
  background: var(--el-fill-color-lighter);
  text-align: center;
}

.general-message {
  padding: 12px 16px;
}

.message-text {
  line-height: 1.6;
}
</style>