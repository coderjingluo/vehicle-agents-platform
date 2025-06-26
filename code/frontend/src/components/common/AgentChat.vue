<template>
  <div class="agent-chat">
    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 聊天消息区域 -->
      <div class="chat-container" ref="chatContainer">
        <!-- 智能规划固定显示 -->
      <div v-if="hasPlanningMessage" class="planning-fixed">
        <div class="planning-content">
          <div class="planning-header">
            <div class="planning-header-left">
              <div class="planning-icon">
              <el-icon><Operation /></el-icon>
            </div>
            <div class="planning-title">智能任务规划</div>
            <span class="planning-steps-count">{{ planningSteps.length }} 步</span>
            </div>
            <div class="planning-header-right">
              <el-button 
              type="text" 
              class="planning-details-btn"
              @click="togglePlanningDetails">
              {{ showPlanningDetails ? '收起详情' : '查看详情' }}
            </el-button>
            </div>
          </div>
          
          <div class="planning-message">{{ planningMessage }}</div>
          
          <div v-if="showPlanningDetails && planningSteps.length > 0" class="planning-steps">
            <div v-for="(step, index) in planningSteps" :key="index" class="planning-step">
              <div class="planning-step-number">{{ index + 1 }}</div>
              <div class="planning-step-content">
                <div class="planning-step-title">{{ step.title }}</div>
                <div class="planning-step-description">{{ step.description }}</div>
                <div v-if="step.tools && step.tools.length > 0" class="planning-step-tools">
                  <span v-for="(tool, toolIndex) in step.tools" :key="toolIndex" class="tool-tag">
                    {{ tool }}
                  </span>
                </div>
              </div>
              <div class="planning-step-status" :class="'status-' + step.status">
                {{ getStatusText(step.status) }}
              </div>
            </div>
          </div>
        </div>
      </div>
        <div class="chat-messages">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="`message-${message.type}`"
          >
            <!-- 用户消息 -->
            <div v-if="message.type === 'user'" class="user-message">
              <div class="message-content">
                {{ message.content }}
              </div>
              <div class="message-header">
                <el-icon><User /></el-icon>
              </div>
            </div>

            <!-- 智能体消息 -->
            <div v-else-if="message.type === 'agent'" class="agent-message">
              <div class="message-header">
                <div class="agent-logo">
                  <span>{{ getAgentShortName(message.agentType) }}</span>
                </div>
              </div>
              <div class="message-content">
                <!-- 步骤执行内容 -->
                <div v-if="message.stepType === 'execution'" class="execution-content">
                  <div class="step-header">
                    <div class="step-title">
                      <span v-if="message.stepNumber" class="step-number">Step {{ message.stepNumber }}</span>
                      <span v-if="message.stepInputOutput" class="step-io">{{ message.stepInputOutput }}</span>
                    </div>
                    <div class="step-timestamp">{{ formatTime(message.timestamp) }}</div>
                  </div>

                  <div class="step-body">
                    <!-- 当前状态 -->
                    <div class="step-section">
                      <div class="section-title">当前状态:</div>
                      <div class="section-content">{{ message.content }}</div>
                    </div>

                    <!-- 已收集的信息 -->
                    <div v-if="message.collectedInfo" class="step-section">
                      <div class="section-title">已收集的信息:</div>
                      <div class="section-content" v-html="message.collectedInfo"></div>
                    </div>

                    <!-- 下一步行动 -->
                    <div v-if="message.nextAction" class="step-section">
                      <div class="section-title">下一步行动:</div>
                      <div class="section-content">{{ message.nextAction }}</div>
                    </div>

                    <!-- 工具调用 -->
                    <div v-if="message.tools && message.tools.length > 0" class="step-section">
                      <div class="section-title">我将立即执行以下工具:</div>
                      <div class="tools-list">
                        <div v-for="(tool, index) in message.tools" :key="index" class="tool-item">
                          <div class="tool-icon" :class="'tool-' + tool.type">
                            <el-icon><Tools /></el-icon>
                          </div>
                          <div class="tool-name">{{ tool.name }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- 进度条 -->
                    <div v-if="message.progress !== undefined" class="step-progress">
                      <el-progress 
                        :percentage="message.progress" 
                        :status="message.status === 'completed' ? 'success' : ''" 
                        :show-text="false"
                      />
                    </div>
                  </div>
                </div>

                <!-- 结果或一般消息 -->
                <div v-else-if="message.stepType !== 'planning'" class="message-text">
                  <div v-if="message.resultData" class="result-data">
                    <!-- 如果是对象或数组类型，美化显示 -->
                    <div v-if="typeof message.resultData === 'object'" class="structured-result">
                      <div v-if="message.resultData.intelligent_summary" class="summary-section">
                        <h4>分析摘要</h4>
                        <div class="summary-overview">
                          <strong>概况:</strong> {{ message.resultData.intelligent_summary.overview }}
                        </div>
                        
                        <div v-if="message.resultData.intelligent_summary.achievements" class="summary-achievements">
                          <strong>主要成果:</strong>
                          <ul>
                            <li v-for="(item, i) in message.resultData.intelligent_summary.achievements" :key="i">
                              {{ item }}
                            </li>
                          </ul>
                        </div>
                        
                        <div v-if="message.resultData.intelligent_summary.issues && message.resultData.intelligent_summary.issues.length > 0" class="summary-issues">
                          <strong>发现的问题:</strong>
                          <ul>
                            <li v-for="(item, i) in message.resultData.intelligent_summary.issues" :key="i">
                              {{ item }}
                            </li>
                          </ul>
                        </div>
                        
                        <div v-if="message.resultData.intelligent_summary.recommendations" class="summary-recommendations">
                          <strong>建议:</strong>
                          <ul>
                            <li v-for="(item, i) in message.resultData.intelligent_summary.recommendations" :key="i">
                              {{ item }}
                            </li>
                          </ul>
                        </div>
                      </div>
                      
                      <el-collapse v-if="!message.resultData.intelligent_summary">
                        <el-collapse-item title="查看详细结果" name="1">
                          <pre class="json-result">{{ JSON.stringify(message.resultData, null, 2) }}</pre>
                        </el-collapse-item>
                      </el-collapse>
                    </div>
                    
                    <!-- 如果是字符串类型，直接显示 -->
                    <div v-else class="string-result">
                      {{ message.resultData }}
                    </div>
                  </div>
                  <div v-else>
                    {{ message.content }}
                  </div>
                </div>
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

          <!-- 加载指示器 -->
          <div v-if="isTyping" class="typing-indicator">
            <div class="agent-logo">
              <span>{{ getAgentShortName(props.agentType) }}</span>
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

    <!-- 右侧面板：工具调用信息 -->
    <div class="chat-sidebar" v-if="currentToolCalls.length > 0">
      <div class="sidebar-header">
        <h3>{{ currentAgentName }} 调用工具</h3>
      </div>
      <div class="sidebar-content">
        <div class="tool-info">
          <h4>查询</h4>
          <div class="tool-query">{{ currentQuery }}</div>
          
          <h4>结果数量</h4>
          <div class="tool-result-count">{{ currentToolCalls.length }}</div>
          
          <h4>结果</h4>
          <div class="tool-results">
            <div v-for="(result, index) in currentToolCalls" :key="index" class="tool-result-item">
              <div class="result-number">{{ index + 1 }}</div>
              <div class="result-content">
                <div v-if="result.title" class="result-title">{{ result.title }}</div>
                <div v-if="result.url" class="result-url">
                  <span>URL:</span> <a :href="result.url" target="_blank">{{ result.url }}</a>
                </div>
                <div v-if="result.description" class="result-description">
                  <span>Description:</span> {{ result.description }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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
const currentToolCalls = ref([])
const currentQuery = ref('')

// 智能规划相关
const hasPlanningMessage = ref(false)
const planningMessage = ref('')
const planningSteps = ref([])
const showPlanningDetails = ref(false)

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

// 品牌标识
const brandName = 'KunlunSec'

// 方法
const getAgentName = (agentType) => {
  return agentNames[agentType] || agentType
}

const getAgentShortName = (agentType) => {
  return brandName
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

// 切换规划详情显示
const togglePlanningDetails = () => {
  showPlanningDetails.value = !showPlanningDetails.value
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
    currentToolCalls.value = []
    currentQuery.value = ''

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
      planningMessage.value = data.message || data.data?.message || '正在分析任务需求并制定执行计划...'
      planningSteps.value = data.steps || data.data?.steps || []
      hasPlanningMessage.value = true
      
      addMessage({
        type: 'agent',
        agentType: props.agentType,
        stepType: 'planning',
        content: planningMessage.value,
        timestamp: new Date()
      })
      break
      
    case 'step_start':
    case 'start':
      // 步骤开始
      const stepNumber = messages.value.filter(m => m.stepType === 'execution').length + 1
      const stepName = data.step_name || data.data?.step_name || '执行步骤'
      
      addMessage({
        type: 'agent',
        agentType: props.agentType,
        stepType: 'execution',
        stepNumber: stepNumber,
        stepName: stepName,
        stepInputOutput: data.step_io || data.data?.step_io || '',
        content: data.message || data.data?.message || `开始执行: ${stepName}`,
        collectedInfo: data.collected_info || data.data?.collected_info || '',
        nextAction: data.next_action || data.data?.next_action || '',
        tools: data.tools || data.data?.tools || [],
        progress: 0,
        timestamp: new Date()
      })
      break
      
    case 'step_progress':
    case 'progress':
      // 步骤进度更新
      const updateData = {
        progress: data.progress || data.data?.progress,
        content: data.message || data.data?.message,
        collectedInfo: data.collected_info || data.data?.collected_info,
        nextAction: data.next_action || data.data?.next_action,
        realTimeOutput: data.output || data.data?.output
      }
      
      // 如果有工具调用信息
      if (data.tool_calls && data.tool_calls.length > 0) {
        updateData.tools = data.tool_calls.map(tool => ({
          type: tool.tool || 'unknown',
          name: tool.tool || 'unknown',
          input: tool.input || {}
        }))
        
        // 支持网络搜索结果显示
        if (data.tool_calls[0].tool === 'web_search') {
          currentQuery.value = data.tool_calls[0].input
          const results = data.tool_calls[0].output?.results || []
          currentToolCalls.value = results.map(result => ({
            title: result.title,
            url: result.url,
            description: result.description
          }))
        }
      }
      
      updateLastMessage(updateData)
      break
      
    case 'step_completed':
    case 'step_complete':
    case 'complete':
      // 步骤完成
      updateLastMessage({
        status: 'completed',
        progress: 100,
        content: data.message || data.data?.message || '步骤执行完成',
        collectedInfo: data.collected_info || data.data?.collected_info,
        nextAction: data.next_action || data.data?.next_action
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
  currentToolCalls.value = []
  currentQuery.value = ''
}

// 暴露方法
defineExpose({
  clearChat,
  addMessage,
  startAgentExecution
})

// 生命周期
onMounted(() => {
  // 清空之前的消息
  clearChat()
  
  // 添加欢迎消息
  addMessage({
    type: 'agent',
    agentType: props.agentType,
    content: `您好！我是${brandName}，请告诉我您需要进行什么分析？`,
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
  height: 100%;
  background: #f5f7fa;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-right: 1px solid #e4e7ed;
  position: relative;
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
  margin-bottom: 16px;
}

/* 用户消息样式 - 右侧显示 */
.user-message {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 12px;
  justify-content: flex-end;
  margin: 16px 0;
}

.user-message .message-header {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e6f1ff;
  color: #409eff;
}

.user-message .message-content {
  background: #ecf5ff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #d9ecff;
  max-width: 80%;
  text-align: center;
  font-size: 15px;
  color: #333;
}

/* 智能体消息样式 - 左侧显示 */
.agent-message {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 12px;
  justify-content: flex-start;
  margin: 16px 0;
}

.agent-message .message-header {
  display: flex;
  align-items: center;
}

.agent-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ff9500;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.agent-message .message-content {
  background: #ffffff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  max-width: 100%;
  min-width: 80%;
  text-align: center;
  font-size: 15px;
  color: #333;
}

.execution-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-number {
  font-weight: 600;
  color: #f56c6c;
}

.step-io {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
}

.step-timestamp {
  font-size: 12px;
  color: #909399;
}

.step-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-section {
  text-align: left;
  padding: 8px;
  background: #ffffff;
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
}

.section-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  border-bottom: 1px dashed #ebeef5;
  padding-bottom: 4px;
}

.section-content {
  line-height: 1.5;
  white-space: pre-wrap;
  color: #606266;
}

.tools-list {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.tool-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  margin-right: 8px;
}

.tool-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.tool-name {
  font-size: 12px;
  color: #606266;
}

/* 步骤进度条 */
.step-progress {
  margin-top: 12px;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 系统消息样式 */
.system-message {
  margin-left: 44px;
  margin-right: 44px;
  text-align: center;
}

/* 输入区域 */
.chat-input-area {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: white;
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

/* 控制按钮 */
.chat-controls {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  background: #f5f7fa;
  text-align: center;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-left: 16px;
}

.typing-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
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
  color: #909399;
}

/* 右侧面板样式 */
.chat-sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  background: white;
  border-left: 1px solid #e4e7ed;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.tool-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tool-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 8px 0;
}

.tool-query {
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  border: 1px solid #e4e7ed;
}

.tool-result-count {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.tool-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-result-item {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.result-number {
  font-weight: 600;
  color: #606266;
}

.result-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-title {
  font-weight: 500;
}

.result-url, .result-description {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

.result-url a {
  color: #409eff;
  text-decoration: none;
}

.result-url a:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-chat {
    flex-direction: column;
  }
  
  .chat-sidebar {
    width: 100%;
    max-height: 300px;
  }
}

/* 结果展示相关样式 */
.result-data {
  text-align: center;
}

.structured-result {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  text-align: left;
}

.summary-section {
  margin-bottom: 12px;
}

.summary-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #333;
  font-size: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.summary-overview {
  margin-bottom: 12px;
  line-height: 1.5;
}

.summary-achievements,
.summary-issues,
.summary-recommendations {
  margin-bottom: 12px;
}

.summary-achievements strong,
.summary-issues strong,
.summary-recommendations strong {
  display: block;
  margin-bottom: 6px;
  color: #555;
}

.summary-achievements ul,
.summary-issues ul,
.summary-recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.summary-achievements li,
.summary-issues li,
.summary-recommendations li {
  margin-bottom: 4px;
  line-height: 1.5;
}

.summary-issues strong {
  color: #e74c3c;
}

.summary-recommendations strong {
  color: #2ecc71;
}

.json-result {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  overflow-x: auto;
  font-size: 13px;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
}

.string-result {
  white-space: pre-wrap;
  line-height: 1.5;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .structured-result {
    padding: 10px;
  }
  
  .json-result {
    font-size: 12px;
  }
}

/* 智能规划样式 */
.planning-fixed {
  /* position: sticky; */
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
  background: #f5f7fa;
  padding: 2px;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  
}

.planning-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-radius: 8px;
  background: #ffffff;
  padding: 12px;
  text-align: center;
  border: 1px solid #ebeef5;
}

.planning-header {
  display: flex;
  align-items: center;
  justify-content:space-between;
  gap: 8px;
  margin-bottom: 8px;
  
}
.planning-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.planning-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.planning-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.planning-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.planning-steps-count {
  background: #409eff;
  color: white;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 12px;
  margin: 0 8px;
}

.planning-details-btn {
  padding: 2px 8px !important;
  height: auto !important;
  font-size: 12px !important;
}

.planning-message {
  color: #606266;
  line-height: 1.5;
  text-align: center;
  font-weight: 500;
  padding: 8px 0;
}

.planning-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.planning-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  background: #ffffff;
  border: 1px solid #ebeef5;
  text-align: left;
}

.planning-step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.planning-step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.planning-step-title {
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.planning-step-description {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.planning-step-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.tool-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  background: #f0f2f5;
  color: #606266;
}

.planning-step-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
}

.status-pending {
  background: #e6f1ff;
  color: #409eff;
}

.status-running {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-completed {
  background: #f0f9eb;
  color: #67c23a;
}

.status-failed {
  background: #fef0f0;
  color: #f56c6c;
}

/* 工具图标样式 */
.tool-web_search {
  background: #409eff;
}

.tool-bash {
  background: #67c23a;
}

.tool-file_operator {
  background: #e6a23c;
}

.tool-deep_research {
  background: #9254de;
}

.tool-create_chat_completion {
  background: #f56c6c;
}

.tool-terminate {
  background: #909399;
}
</style>