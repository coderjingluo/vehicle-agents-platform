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
          <h2>车联网安全测试助手</h2>
          <p>智能体协作工作流平台</p>
        </div>
        <div class="chat-actions">
          <el-button text class="action-btn" @click="startNewTask">
            <el-icon><Plus /></el-icon>
            New Task
          </el-button>
          <el-button text class="action-btn" @click="shareCurrentChat">
            <el-icon><Share /></el-icon>
            Share
          </el-button>
          <el-button text class="action-btn" @click="showToolsConfig">
            <el-icon><Setting /></el-icon>
            Tool Config
          </el-button>
        </div>
      </div>

      <!-- 智能体选择器 -->
      <div class="agent-selector">
        <el-select 
          v-model="currentAgent" 
          placeholder="选择智能体" 
          @change="onAgentChange"
          class="agent-select"
        >
          <el-option
            v-for="agent in availableAgents"
            :key="agent.value"
            :label="agent.label"
            :value="agent.value"
          >
            <div class="agent-option">
              <el-icon :class="agent.icon"></el-icon>
              <span>{{ agent.label }}</span>
            </div>
          </el-option>
        </el-select>
        
        <el-tag 
          :type="getAgentStatusType(agentStatus)" 
          size="small"
          class="agent-status-tag"
        >
          {{ getAgentStatusText(agentStatus) }}
        </el-tag>
      </div>

      <!-- AgentChat组件 -->
      <div class="agent-chat-container">
        <AgentChat 
          ref="agentChatRef"
          :agent-type="currentAgent"
          :initial-context="getCurrentAgentContext()"
          @execution-start="onAgentExecutionStart"
          @execution-complete="onAgentExecutionComplete"
          @execution-error="onAgentExecutionError"
          :key="`${currentAgent}-${agentContextVersion}`"
        />
      </div>
    </div>

    <!-- Models Configuration 对话框 -->
    <el-dialog
      v-model="modelsConfigVisible"
      title="Models"
      width="700px"
      :show-close="true"
      class="models-config-dialog"
      :modal-class="'models-config-modal'"
    >
      <ModelsConfig @apply="applyModelsConfig" @close="modelsConfigVisible = false" />
    </el-dialog>

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
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Clock, Plus, Share, Promotion, Setting, Monitor,
  Lock, DocumentChecked, VideoPlay, Document, Search
} from '@element-plus/icons-vue'
import ToolsConfig from '../components/common/ToolsConfig.vue'
import ModelsConfig from '../components/common/ModelsConfig.vue'
import AgentChat from '../components/common/AgentChat.vue'

// API imports
import workflowAPI from '../api/modules/workflow'
import systemAPI from '../api/modules/system'
import agentsAPI from '../api/modules/agents'
import { WEBSOCKET_URL } from '../api'

// 响应式数据
const currentTaskId = ref(null)
const agentChatRef = ref(null)
const toolsConfigVisible = ref(false)
const modelsConfigVisible = ref(false)

// AgentChat相关数据
const currentAgent = ref('tara')
const agentStatus = ref('ready')
const agentContextVersion = ref(0)

// 数据状态
const loading = ref(false)
const recentTasks = ref([])
const systemStatus = ref(null)
const workflowExecutions = ref([])

// 可用智能体列表
const availableAgents = ref([
  { 
    value: 'tara', 
    label: 'TARA智能体', 
    icon: 'Lock',
    description: '威胁分析与风险评估'
  },
  { 
    value: 'test_case', 
    label: '测试用例智能体', 
    icon: 'DocumentChecked',
    description: '智能生成测试用例'
  },
  { 
    value: 'automation_test', 
    label: '自动化测试智能体', 
    icon: 'VideoPlay',
    description: '自动化测试执行'
  },
  { 
    value: 'report_analysis', 
    label: '报告分析智能体', 
    icon: 'Document',
    description: '测试报告分析'
  },
  { 
    value: 'knowledge_base', 
    label: '知识库智能体', 
    icon: 'Search',
    description: '知识库搜索与学习'
  }
])

// WebSocket连接
let websocket = null

// 计算属性
const hasActiveTasks = computed(() => recentTasks.value.length > 0)
const isSystemHealthy = computed(() => systemStatus.value?.status === 'healthy')

// 获取最近任务
const fetchRecentTasks = async () => {
  try {
    const response = await workflowAPI.getExecutionHistory({ limit: 10 })
    if (response.data?.success) {
      recentTasks.value = response.data.executions.map(exec => ({
        id: exec.execution_id,
        title: exec.workflow_name || '工作流执行',
        preview: exec.description || exec.initial_request?.slice(0, 50) + '...',
        status: exec.status,
        timestamp: exec.created_at,
        type: exec.workflow_type || 'general'
      }))
    }
  } catch (error) {
    console.error('获取最近任务失败:', error)
    ElMessage.error('获取最近任务失败')
  }
}

// 获取系统状态
const fetchSystemStatus = async () => {
  try {
    const response = await systemAPI.healthCheck()
    systemStatus.value = response.data
  } catch (error) {
    console.error('获取系统状态失败:', error)
    systemStatus.value = { status: 'error', message: '系统状态检查失败' }
  }
}

// 选择任务
const selectTask = async (task) => {
  if (currentTaskId.value === task.id) return
  
  currentTaskId.value = task.id
  loading.value = true
  
  try {
    // 获取任务详情和消息历史
    const response = await workflowAPI.getExecutionDetail(task.id)
    if (response.data?.success) {
      const execution = response.data.execution
      
      // 转换执行步骤为聊天消息格式
      messages.value = []
      
      // 添加初始用户请求
      if (execution.initial_request) {
        messages.value.push({
          id: 'initial',
          type: 'user',
          content: execution.initial_request,
          timestamp: new Date(execution.created_at)
        })
      }
      
      // 添加执行步骤
      if (execution.steps && execution.steps.length > 0) {
        execution.steps.forEach((step, index) => {
          messages.value.push({
            id: `step-${index}`,
            type: 'assistant',
            content: formatExecutionStep(step),
            timestamp: new Date(step.timestamp || execution.created_at),
            stepType: step.step_type,
            status: step.status
          })
        })
      }
      
      // 添加最终结果
      if (execution.result) {
        messages.value.push({
          id: 'result',
          type: 'assistant',
          content: formatExecutionResult(execution.result),
          timestamp: new Date(execution.updated_at),
          isResult: true
        })
      }
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 格式化执行步骤
const formatExecutionStep = (step) => {
  let content = `**${step.step_type}**: ${step.description}\n\n`
  
  if (step.agent_type) {
    content += `**执行智能体**: ${step.agent_type}\n`
  }
  
  if (step.input) {
    content += `**输入**: ${typeof step.input === 'string' ? step.input : JSON.stringify(step.input, null, 2)}\n`
  }
  
  if (step.output) {
    content += `**输出**: ${typeof step.output === 'string' ? step.output : JSON.stringify(step.output, null, 2)}\n`
  }
  
  if (step.error) {
    content += `**错误**: ${step.error}\n`
  }
  
  content += `**状态**: ${step.status} | **耗时**: ${step.execution_time || 0}ms`
  
  return content
}

// 格式化执行结果
const formatExecutionResult = (result) => {
  if (typeof result === 'string') {
    return result
  }
  
  let content = '## 执行结果\n\n'
  
  if (result.summary) {
    content += `**总结**: ${result.summary}\n\n`
  }
  
  if (result.outputs) {
    content += '**详细输出**:\n```json\n' + JSON.stringify(result.outputs, null, 2) + '\n```\n\n'
  }
  
  if (result.metrics) {
    content += `**性能指标**: 总耗时 ${result.metrics.total_time}ms, 成功步骤 ${result.metrics.successful_steps}/${result.metrics.total_steps}\n`
  }
  
  return content
}

// AgentChat相关方法
const getCurrentAgentContext = () => {
  // 根据当前选择的智能体返回相应的上下文
  const agentContexts = {
    'tara': {
      system_name: '车载网关系统',
      system_type: 'gateway',
      analysis_depth: 'comprehensive',
      standards: ['iso21434', 'sae_j3061']
    },
    'test_case': {
      system_info: '车载T-Box系统',
      test_types: ['security', 'penetration'],
      test_depth: 'standard',
      priority_filter: ['high', 'medium']
    },
    'automation_test': {
      target_system: '车载IVI系统',
      test_framework: 'pytest',
      execution_mode: 'automated'
    },
    'report_analysis': {
      report_type: 'vulnerability_scan',
      analysis_scope: 'comprehensive'
    },
    'knowledge_base': {
      search_scope: 'automotive_security',
      query_type: 'semantic'
    }
  }
  
  return agentContexts[currentAgent.value] || {}
}

const onAgentChange = (agentType) => {
  console.log('切换智能体:', agentType)
  agentStatus.value = 'ready'
  agentContextVersion.value++
  ElMessage.info(`已切换到${availableAgents.value.find(a => a.value === agentType)?.label}`)
}

const onAgentExecutionStart = () => {
  agentStatus.value = 'busy'
  ElMessage.info(`${availableAgents.value.find(a => a.value === currentAgent.value)?.label}开始执行...`)
}

const onAgentExecutionComplete = () => {
  agentStatus.value = 'ready'
  ElMessage.success('智能体执行完成')
  
  // 刷新任务列表
  fetchRecentTasks()
}

const onAgentExecutionError = (error) => {
  agentStatus.value = 'error'
  ElMessage.error(`智能体执行失败: ${error.message || error}`)
}

const getAgentStatusType = (status) => {
  const statusTypes = {
    'ready': 'success',
    'busy': 'warning', 
    'error': 'danger'
  }
  return statusTypes[status] || 'info'
}

const getAgentStatusText = (status) => {
  const statusTexts = {
    'ready': '就绪',
    'busy': '忙碌',
    'error': '错误'
  }
  return statusTexts[status] || '未知'
}

// 新任务
const startNewTask = () => {
  if (agentChatRef.value) {
    agentChatRef.value.clearChat()
    ElMessage.info('已清空对话，开始新任务')
  }
}

// 分享当前对话
const shareCurrentChat = () => {
  ElMessage.info('分享功能开发中...')
}

// 监听工作流执行
const monitorExecution = async (executionId) => {
  try {
    // 使用WebSocket监听实时进度
    if (websocket) {
      websocket.send(JSON.stringify({
        type: 'monitor_execution',
        execution_id: executionId
      }))
    }
    
    // 轮询获取执行状态
    let completed = false
    const maxAttempts = 60 // 最多等待5分钟
    let attempts = 0
    
    while (!completed && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)) // 等待5秒
      
      try {
        const statusResponse = await workflowAPI.getExecutionStatus(executionId)
        if (statusResponse.data?.success) {
          const execution = statusResponse.data.execution
          
          // 添加进度消息
          if (execution.current_step) {
            const progressMessage = {
              id: `progress-${Date.now()}`,
              type: 'assistant',
              content: `正在执行: ${execution.current_step}`,
              timestamp: new Date(),
              isProgress: true
            }
            
            // 更新或添加进度消息
            const existingIndex = messages.value.findIndex(m => m.isProgress && !m.isCompleted)
            if (existingIndex >= 0) {
              messages.value[existingIndex] = progressMessage
            } else {
              messages.value.push(progressMessage)
            }
            
            await nextTick()
            scrollToBottom()
          }
          
          // 检查是否完成
          if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
            completed = true
            
            // 标记进度消息为完成
            const progressMsg = messages.value.find(m => m.isProgress && !m.isCompleted)
            if (progressMsg) {
              progressMsg.isCompleted = true
            }
            
            // 添加最终结果
            const resultContent = execution.status === 'completed' 
              ? formatExecutionResult(execution.result)
              : `执行${execution.status === 'failed' ? '失败' : '被取消'}: ${execution.error || '未知原因'}`
            
            messages.value.push({
              id: `result-${executionId}`,
              type: 'assistant',
              content: resultContent,
              timestamp: new Date(),
              isResult: true,
              status: execution.status
            })
          }
        }
      } catch (error) {
        console.error('获取执行状态失败:', error)
        break
      }
      
      attempts++
    }
    
    if (!completed) {
      ElMessage.warning('执行监控超时，请手动刷新查看结果')
    }
    
  } catch (error) {
    console.error('监听执行失败:', error)
  }
}

// 初始化WebSocket连接
const initWebSocket = () => {
  // 暂时禁用WebSocket连接，后端未实现相关功能
  console.log('WebSocket功能暂未实现，跳过连接');
  
  /* 
  try {
    const wsUrl = `${WEBSOCKET_URL}/workflow`
    websocket = new WebSocket(wsUrl)
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (error) {
        console.error('WebSocket消息解析失败:', error)
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket连接错误:', error)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket连接已关闭')
      // 可以在这里实现重连逻辑
    }
  } catch (error) {
    console.error('WebSocket初始化失败:', error)
  }
  */
}

// 处理WebSocket消息
const handleWebSocketMessage = (data) => {
  if (data.type === 'execution_progress') {
    // 更新执行进度
    const progressMessage = {
      id: `ws-progress-${Date.now()}`,
      type: 'assistant',
      content: data.message || `执行进度: ${data.progress}%`,
      timestamp: new Date(),
      isProgress: true
    }
    
    messages.value.push(progressMessage)
    nextTick(() => scrollToBottom())
  } else if (data.type === 'execution_completed') {
    // 执行完成
    fetchRecentTasks() // 刷新任务列表
  }
}

// 其他方法
const formatTime = (timestamp) => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(timestamp))
}

const showToolsConfig = () => {
  toolsConfigVisible.value = true
}

const applyToolsConfig = (config) => {
  ElMessage.success('工具配置已应用')
  toolsConfigVisible.value = false
}

const showModelsConfig = () => {
  modelsConfigVisible.value = true
}

const applyModelsConfig = (config) => {
  ElMessage.success('模型配置已应用')
  modelsConfigVisible.value = false
}

// 定期刷新系统状态
const startStatusPolling = () => {
  const interval = setInterval(async () => {
    await fetchSystemStatus()
  }, 30000) // 每30秒刷新一次
  
  return interval
}

// 生命周期
onMounted(async () => {
  loading.value = true
  
  try {
    // 并行获取初始数据
    await Promise.all([
      fetchRecentTasks(),
      fetchSystemStatus()
    ])
    
    // 初始化WebSocket连接
    initWebSocket()
    
    // 开始状态轮询
    const statusInterval = startStatusPolling()
    
    // 保存定时器引用用于清理
    onUnmounted(() => {
      clearInterval(statusInterval)
      // WebSocket暂未实现，不需要关闭连接
      /*
      if (websocket) {
        websocket.close()
      }
      */
    })
    
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('Dashboard初始化失败')
  } finally {
    loading.value = false
  }
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

/* ========== 智能体选择器 ========== */
.agent-selector {
  padding: 12px 20px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-select {
  flex: 1;
  max-width: 300px;
}

.agent-select :deep(.el-input__wrapper) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  color: #cccccc;
}

.agent-select :deep(.el-input__inner) {
  color: #cccccc;
}

.agent-select :deep(.el-select__popper) {
  background: #2d2d30;
  border: 1px solid #3c3c3c;
}

.agent-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-status-tag {
  font-size: 11px;
  border: none;
  font-weight: 500;
}

/* ========== AgentChat容器 ========== */
.agent-chat-container {
  flex: 1;
  background: #1e1e1e;
  overflow: hidden;
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

/* AgentChat组件内部处理输入区域样式 */

/* Models Configuration 对话框样式 */
:deep(.models-config-modal) {
  background: rgba(0, 0, 0, 0.5);
}

:deep(.models-config-dialog) {
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
}

:deep(.models-config-dialog .el-dialog__header) {
  background: #2c2c2c;
  border-bottom: 1px solid #3c3c3c;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
}

:deep(.models-config-dialog .el-dialog__title) {
  color: #cccccc;
  font-size: 16px;
  font-weight: 600;
}

:deep(.models-config-dialog .el-dialog__headerbtn) {
  top: 16px;
  right: 20px;
}

:deep(.models-config-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #9d9d9d;
  font-size: 16px;
}

:deep(.models-config-dialog .el-dialog__headerbtn .el-dialog__close:hover) {
  color: #cccccc;
}

:deep(.models-config-dialog .el-dialog__body) {
  padding: 0;
  background: #252526;
  max-height: 70vh;
  overflow: hidden;
  border-radius: 0 0 8px 8px;
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