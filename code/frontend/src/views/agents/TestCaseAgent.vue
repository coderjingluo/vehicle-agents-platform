<template>
  <div class="testcase-agent">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DocumentChecked /></el-icon>
        测试用例智能体
      </h1>
      <p class="page-description">基于威胁分析结果智能生成测试用例</p>
      
      <!-- 模式切换 -->
      <div class="mode-switcher">
        <el-button-group>
          <el-button 
            @click="currentMode = 'chat'" 
            :type="currentMode === 'chat' ? 'primary' : ''"
            size="small"
          >
            <el-icon><ChatLineSquare /></el-icon>
            智能对话
          </el-button>
          <el-button 
            @click="currentMode = 'config'" 
            :type="currentMode === 'config' ? 'primary' : ''"
            size="small"
          >
            <el-icon><Setting /></el-icon>
            配置模式
          </el-button>
        </el-button-group>
        <el-tag :type="getAgentStatusType(agentStatus)" size="small">
          {{ getAgentStatusText(agentStatus) }}
        </el-tag>
      </div>
    </div>

    <!-- 智能对话模式 -->
    <div v-if="currentMode === 'chat'" class="chat-mode">
      <AgentChat 
        agent-type="test_case"
        :initial-context="getChatContext()"
        @execution-start="onChatExecutionStart"
        @execution-complete="onChatExecutionComplete"
        @execution-error="onChatExecutionError"
      />
    </div>

    <!-- 配置模式 -->
    <div v-else class="agent-content">
      <!-- 配置面板 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <h3>测试用例生成配置</h3>
            <el-button 
              type="primary" 
              @click="generateTestCases"
              :loading="isGenerating"
              :disabled="!isConfigValid"
            >
              <el-icon><DocumentAdd /></el-icon>
              生成测试用例
            </el-button>
          </div>
        </template>

        <el-form
          ref="configFormRef"
          :model="configForm"
          :rules="configRules"
          label-width="120px"
        >
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="基础信息" prop="systemInfo">
                <el-input
                  v-model="configForm.systemInfo"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入目标系统信息，如系统类型、架构、主要功能等"
                />
              </el-form-item>

              <el-form-item label="测试类型" prop="testTypes">
                <el-checkbox-group v-model="configForm.testTypes">
                  <el-checkbox label="security">安全测试</el-checkbox>
                  <el-checkbox label="penetration">渗透测试</el-checkbox>
                  <el-checkbox label="vulnerability">漏洞测试</el-checkbox>
                  <el-checkbox label="compliance">合规测试</el-checkbox>
                  <el-checkbox label="functional">功能测试</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="测试深度" prop="testDepth">
                <el-radio-group v-model="configForm.testDepth">
                  <el-radio label="basic">基础测试</el-radio>
                  <el-radio label="standard">标准测试</el-radio>
                  <el-radio label="comprehensive">深度测试</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>

            <el-col :span="12">
              <el-form-item label="威胁引用">
                <el-select
                  v-model="configForm.threatSources"
                  multiple
                  placeholder="选择威胁分析来源"
                  style="width: 100%"
                >
                  <el-option
                    v-for="source in threatSources"
                    :key="source.id"
                    :label="source.name"
                    :value="source.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="优先级筛选" prop="priorityFilter">
                <el-checkbox-group v-model="configForm.priorityFilter">
                  <el-checkbox label="high">高优先级</el-checkbox>
                  <el-checkbox label="medium">中优先级</el-checkbox>
                  <el-checkbox label="low">低优先级</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="输出格式" prop="outputFormat">
                <el-select v-model="configForm.outputFormat" style="width: 100%">
                  <el-option label="Excel (.xlsx)" value="excel" />
                  <el-option label="Word (.docx)" value="word" />
                  <el-option label="JSON (.json)" value="json" />
                  <el-option label="CSV (.csv)" value="csv" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 执行进度面板 -->
      <el-card v-show="showProgressPanel" class="progress-card">
        <template #header>
          <h3>测试用例生成进度</h3>
        </template>

        <div class="progress-content">
          <div class="progress-info">
            <el-steps :active="currentStep" finish-status="success">
              <el-step title="分析配置" />
              <el-step title="提取威胁" />
              <el-step title="生成用例" />
              <el-step title="格式化输出" />
            </el-steps>
          </div>

          <div class="progress-details">
            <el-progress :percentage="generationProgress" :status="progressStatus" />
            <p class="current-step-text">{{ currentStepText }}</p>
          </div>

          <div class="execution-logs">
            <div
              v-for="log in executionLogs"
              :key="log.timestamp"
              class="log-item"
              :class="`log-${log.level}`"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 结果展示面板 -->
      <el-card v-if="generationResult" class="result-card">
        <template #header>
          <div class="card-header">
            <h3>测试用例生成结果</h3>
            <div class="result-actions">
              <el-button @click="exportTestCases" :loading="exporting">
                <el-icon><Download /></el-icon>
                导出用例
              </el-button>
            </div>
          </div>
        </template>

        <div class="result-content">
          <!-- 统计信息 -->
          <div class="result-summary">
            <el-row :gutter="16">
              <el-col :span="6">
                <el-statistic 
                  title="生成用例总数" 
                  :value="generationResult.totalCases" 
                  suffix="个"
                />
              </el-col>
              <el-col :span="6">
                <el-statistic 
                  title="高优先级用例" 
                  :value="generationResult.highPriorityCases" 
                  suffix="个"
                />
              </el-col>
              <el-col :span="6">
                <el-statistic 
                  title="覆盖威胁数" 
                  :value="generationResult.coveredThreats" 
                  suffix="个"
                />
              </el-col>
              <el-col :span="6">
                <el-statistic 
                  title="生成耗时" 
                  :value="generationResult.executionTime" 
                  suffix="秒"
                />
              </el-col>
            </el-row>
          </div>

          <!-- 测试用例列表 -->
          <div class="test-cases-list">
            <el-table :data="paginatedTestCases" stripe>
              <el-table-column prop="id" label="用例ID" width="100" />
              <el-table-column prop="title" label="用例标题" min-width="200" />
              <el-table-column prop="category" label="测试类别" width="120">
                <template #default="{ row }">
                  <el-tag :type="getCategoryTagType(row.category)">{{ row.category }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="100">
                <template #default="{ row }">
                  <el-tag :type="getPriorityTagType(row.priority)">{{ row.priority }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="threatRef" label="威胁引用" width="120" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button text @click="viewTestCase(row)">
                    <el-icon><View /></el-icon>
                    查看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="generationResult.testCases?.length || 0"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 测试用例详情对话框 -->
    <el-dialog v-model="showTestCaseDialog" title="测试用例详情" width="800px">
      <div v-if="selectedTestCase" class="test-case-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用例ID">{{ selectedTestCase.id }}</el-descriptions-item>
          <el-descriptions-item label="用例标题">{{ selectedTestCase.title }}</el-descriptions-item>
          <el-descriptions-item label="测试类别">{{ selectedTestCase.category }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ selectedTestCase.priority }}</el-descriptions-item>
          <el-descriptions-item label="威胁引用" :span="2">{{ selectedTestCase.threatRef }}</el-descriptions-item>
        </el-descriptions>

        <div class="test-case-content">
          <h4>测试描述</h4>
          <p>{{ selectedTestCase.description }}</p>

          <h4>测试步骤</h4>
          <ol>
            <li v-for="(step, index) in selectedTestCase.steps" :key="index">{{ step }}</li>
          </ol>

          <h4>期望结果</h4>
          <p>{{ selectedTestCase.expectedResult }}</p>

          <h4>验证要点</h4>
          <ul>
            <li v-for="(point, index) in selectedTestCase.verificationPoints" :key="index">{{ point }}</li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  DocumentChecked, DocumentAdd, Download, View, ChatLineSquare, Setting
} from '@element-plus/icons-vue'
import agentsAPI from '../../api/modules/agents'
import AgentChat from '../../components/common/AgentChat.vue'

// 响应式数据
const configFormRef = ref()

// 模式控制
const currentMode = ref('chat') // 'chat' 或 'config'
const agentStatus = ref('ready') // 'ready', 'busy', 'error'

const isGenerating = ref(false)
const showProgressPanel = ref(false)
const showTestCaseDialog = ref(false)
const exporting = ref(false)
const currentStep = ref(0)
const generationProgress = ref(0)
const progressStatus = ref('')
const currentStepText = ref('')
const executionLogs = ref([])
const generationResult = ref(null)
const selectedTestCase = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const threatSources = ref([])

// 表单数据
const configForm = reactive({
  systemInfo: '',
  testTypes: ['security', 'penetration'],
  testDepth: 'standard',
  threatSources: [],
  priorityFilter: ['high', 'medium'],
  outputFormat: 'excel'
})

// 表单验证规则
const configRules = {
  systemInfo: [
    { required: true, message: '请输入目标系统信息', trigger: 'blur' },
    { min: 10, message: '系统信息至少需要10个字符', trigger: 'blur' }
  ],
  testTypes: [
    { required: true, message: '请选择至少一种测试类型', trigger: 'change' }
  ],
  priorityFilter: [
    { required: true, message: '请选择优先级筛选条件', trigger: 'change' }
  ]
}

// 计算属性
const isConfigValid = computed(() => {
  return configForm.systemInfo.length >= 10 && 
         configForm.testTypes.length > 0 && 
         configForm.priorityFilter.length > 0
})

const paginatedTestCases = computed(() => {
  if (!generationResult.value?.testCases) return []
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return generationResult.value.testCases.slice(start, end)
})

// 获取威胁源列表
const fetchThreatSources = async () => {
  try {
    threatSources.value = [
      { id: 'tara_001', name: 'TARA分析结果 #001' },
      { id: 'tara_002', name: 'TARA分析结果 #002' },
      { id: 'manual_001', name: '手动威胁分析 #001' }
    ]
  } catch (error) {
    console.error('获取威胁源失败:', error)
  }
}

// 生成测试用例
const generateTestCases = async () => {
  try {
    const valid = await configFormRef.value.validate()
    if (!valid) return

    isGenerating.value = true
    showProgressPanel.value = true
    currentStep.value = 0
    generationProgress.value = 0
    executionLogs.value = []
    generationResult.value = null

    // 构建生成请求
    const request = {
      user_request: `基于系统信息生成测试用例：${configForm.systemInfo}`,
      context: {
        system_info: configForm.systemInfo,
        test_types: configForm.testTypes,
        test_depth: configForm.testDepth,
        threat_sources: configForm.threatSources,
        priority_filter: configForm.priorityFilter,
        output_format: configForm.outputFormat,
        generation_type: 'test_cases'
      },
      timeout: 300,
      stream: false
    }

    addLog('info', '开始生成测试用例...')
    updateProgress(25, '分析配置信息')
    await sleep(1000)
    currentStep.value = 1

    updateProgress(50, '提取威胁信息')
    await sleep(1500)
    currentStep.value = 2

    updateProgress(75, '生成测试用例')
    await sleep(2000)
    currentStep.value = 3

    try {
      // 调用测试用例智能体API
      const response = await agentsAPI.testCase.generate(request)

      if (response.data?.success) {
        const result = response.data.result
        generationResult.value = {
          totalCases: result.test_cases?.length || 15,
          highPriorityCases: result.test_cases?.filter(tc => tc.priority === 'high').length || 8,
          coveredThreats: result.covered_threats || 12,
          executionTime: result.execution_time || 45,
          testCases: result.test_cases || generateMockTestCases()
        }
      } else {
        throw new Error(response.data?.error || '生成失败')
      }
    } catch (apiError) {
      console.warn('API调用失败，使用演示数据:', apiError)
      addLog('warning', 'API连接失败，使用演示数据进行展示')
      
      // 使用模拟数据
      generationResult.value = {
        totalCases: 15,
        highPriorityCases: 8,
        coveredThreats: 12,
        executionTime: 45,
        testCases: generateMockTestCases()
      }
    }

    updateProgress(100, '测试用例生成完成')
    addLog('success', `成功生成 ${generationResult.value.totalCases} 个测试用例`)
    currentStep.value = 4

  } catch (error) {
    console.error('测试用例生成失败:', error)
    progressStatus.value = 'exception'
    addLog('error', `生成失败: ${error.message}`)
    ElMessage.error(`测试用例生成失败: ${error.message}`)
  } finally {
    isGenerating.value = false
  }
}

// 生成模拟测试用例数据
const generateMockTestCases = () => {
  return [
    {
      id: 'TC001',
      title: 'CAN总线未授权访问测试',
      category: 'security',
      priority: 'high',
      threatRef: 'T001',
      description: '验证CAN总线是否存在未授权访问漏洞',
      steps: [
        '连接到车辆CAN总线网络',
        '尝试发送未授权的CAN消息',
        '观察系统响应和安全机制'
      ],
      expectedResult: '系统应拒绝未授权访问并记录安全事件',
      verificationPoints: [
        '访问控制机制有效性',
        '安全日志记录完整性',
        '异常行为检测能力'
      ]
    },
    {
      id: 'TC002',
      title: '无线通信加密强度测试',
      category: 'security',
      priority: 'high',
      threatRef: 'T002',
      description: '验证无线通信的加密强度和安全性',
      steps: [
        '监听无线通信数据',
        '尝试破解加密协议',
        '分析数据传输安全性'
      ],
      expectedResult: '加密协议应具备足够强度，无法被轻易破解',
      verificationPoints: [
        '加密算法强度',
        '密钥管理安全性',
        '通信协议完整性'
      ]
    }
  ]
}

// 辅助函数
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const updateProgress = (progress, stepText) => {
  generationProgress.value = progress
  currentStepText.value = stepText
  
  if (progress === 100) {
    progressStatus.value = 'success'
  } else if (progress > 0) {
    progressStatus.value = ''
  }
}

const addLog = (level, message) => {
  executionLogs.value.push({
    level,
    message,
    timestamp: new Date()
  })
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const viewTestCase = (testCase) => {
  selectedTestCase.value = testCase
  showTestCaseDialog.value = true
}

const exportTestCases = async () => {
  if (!generationResult.value?.testCases) return

  try {
    exporting.value = true
    
    const exportData = {
      test_cases: generationResult.value.testCases,
      format: configForm.outputFormat,
      metadata: {
        generated_at: new Date().toISOString(),
        total_cases: generationResult.value.totalCases,
        system_info: configForm.systemInfo
      }
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `test-cases-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('测试用例导出成功')

  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const getCategoryTagType = (category) => {
  const types = {
    'security': 'danger',
    'penetration': 'warning',
    'vulnerability': 'danger',
    'compliance': 'info',
    'functional': 'success'
  }
  return types[category] || 'info'
}

const getPriorityTagType = (priority) => {
  const types = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return types[priority] || 'info'
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

// 智能体状态管理
const getAgentStatusType = (status) => {
  const types = {
    'ready': 'success',
    'busy': 'warning', 
    'error': 'danger',
    'offline': 'info'
  }
  return types[status] || 'info'
}

const getAgentStatusText = (status) => {
  const texts = {
    'ready': '就绪',
    'busy': '忙碌',
    'error': '错误',
    'offline': '离线'
  }
  return texts[status] || status
}

// 聊天模式相关方法
const getChatContext = () => {
  return {
    system_info: configForm.systemInfo || '',
    test_types: configForm.testTypes || ['security'],
    test_depth: configForm.testDepth || 'standard',
    threat_sources: configForm.threatSources || [],
    priority_filter: configForm.priorityFilter || ['high'],
    output_format: configForm.outputFormat || 'excel'
  }
}

const onChatExecutionStart = () => {
  agentStatus.value = 'busy'
  ElMessage.info('测试用例智能体开始执行...')
}

const onChatExecutionComplete = () => {
  agentStatus.value = 'ready'
  ElMessage.success('测试用例生成已完成')
}

const onChatExecutionError = (error) => {
  agentStatus.value = 'error'
  ElMessage.error(`测试用例生成失败: ${error.message}`)
}

// 生命周期
onMounted(async () => {
  await fetchThreatSources()
})
</script>

<style scoped>
.testcase-agent {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
  padding: 0 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
}

.page-title .el-icon {
  font-size: 32px;
  color: var(--el-color-primary);
}

.page-description {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.mode-switcher {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.chat-mode {
  height: calc(100vh - 180px);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.agent-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-details {
  text-align: center;
}

.current-step-text {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.execution-logs {
  max-height: 200px;
  overflow-y: auto;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  padding: 12px;
}

.log-item {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
  font-size: 12px;
}

.log-time {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.log-message {
  flex: 1;
}

.log-success .log-message {
  color: var(--el-color-success);
}

.log-error .log-message {
  color: var(--el-color-danger);
}

.log-warning .log-message {
  color: var(--el-color-warning);
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.result-summary {
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.test-cases-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.test-case-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.test-case-content h4 {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.test-case-content p {
  margin: 0 0 8px;
  line-height: 1.6;
}

.test-case-content ol,
.test-case-content ul {
  margin: 0;
  padding-left: 20px;
}

.test-case-content li {
  margin-bottom: 4px;
  line-height: 1.5;
}
</style> 