<template>
  <div class="tara-agent">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Lock /></el-icon>
        TARA智能体
      </h1>
      <p class="page-description">威胁分析与风险评估 (Threat Analysis and Risk Assessment)</p>
      
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
        agent-type="tara"
        :initial-context="getChatContext()"
        @execution-start="onChatExecutionStart"
        @execution-complete="onChatExecutionComplete"
        @execution-error="onChatExecutionError"
      />
    </div>

    <!-- 配置模式 -->
    <div v-else class="tara-content">
      <!-- 分析配置面板 -->
      <el-card class="config-panel" shadow="never">
        <template #header>
          <div class="card-header">
            <span>TARA分析配置</span>
            <el-button
              type="primary"
              :loading="isExecuting"
              :disabled="!isFormValid"
              @click="startAnalysis"
            >
              <el-icon><CaretRight /></el-icon>
              开始分析
            </el-button>
          </div>
        </template>

        <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="140px">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="系统名称" prop="systemName">
                <el-input
                  v-model="configForm.systemName"
                  placeholder="请输入车联网系统名称"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="系统类型" prop="systemType">
                <el-select v-model="configForm.systemType" placeholder="请选择系统类型" style="width: 100%">
                  <el-option label="T-Box" value="t-box" />
                  <el-option label="OBD-II" value="obd-ii" />
                  <el-option label="IVI系统" value="ivi" />
                  <el-option label="ADAS系统" value="adas" />
                  <el-option label="车载网关" value="gateway" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="系统描述" prop="systemDescription">
            <el-input
              v-model="configForm.systemDescription"
              type="textarea"
              :rows="3"
              placeholder="请详细描述系统功能、用途和特点"
            />
          </el-form-item>

          <el-form-item label="系统组件">
            <el-tag
              v-for="(component, index) in configForm.components"
              :key="index"
              class="component-tag"
              closable
              @close="removeComponent(index)"
            >
              {{ component }}
            </el-tag>
            <el-input
              v-if="showComponentInput"
              ref="componentInputRef"
              v-model="newComponent"
              class="component-input"
              size="small"
              @keyup.enter="addComponent"
              @blur="addComponent"
            />
            <el-button v-else size="small" @click="showComponentInput = true">
              <el-icon><Plus /></el-icon>
              添加组件
            </el-button>
          </el-form-item>

          <el-form-item label="接口类型">
            <el-checkbox-group v-model="configForm.interfaces">
              <el-checkbox value="can">CAN总线</el-checkbox>
              <el-checkbox value="ethernet">以太网</el-checkbox>
              <el-checkbox value="wifi">Wi-Fi</el-checkbox>
              <el-checkbox value="bluetooth">蓝牙</el-checkbox>
              <el-checkbox value="cellular">蜂窝网络</el-checkbox>
              <el-checkbox value="usb">USB</el-checkbox>
              <el-checkbox value="serial">串行接口</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="数据类型">
            <el-checkbox-group v-model="configForm.dataTypes">
              <el-checkbox value="sensor">传感器数据</el-checkbox>
              <el-checkbox value="location">位置信息</el-checkbox>
              <el-checkbox value="vehicle_status">车辆状态</el-checkbox>
              <el-checkbox value="diagnostic">诊断数据</el-checkbox>
              <el-checkbox value="personal">个人信息</el-checkbox>
              <el-checkbox value="biometric">生物特征</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="法规标准">
                <el-checkbox-group v-model="configForm.standards">
                  <el-checkbox value="iso21434">ISO 21434</el-checkbox>
                  <el-checkbox value="sae_j3061">SAE J3061</el-checkbox>
                  <el-checkbox value="unece_wp29">UNECE WP.29</el-checkbox>
                  <el-checkbox value="iso26262">ISO 26262</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="分析深度">
                <el-radio-group v-model="configForm.analysisDepth">
                  <el-radio value="basic">基础分析</el-radio>
                  <el-radio value="standard">标准分析</el-radio>
                  <el-radio value="comprehensive">全面分析</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 执行状态面板 -->
      <el-card v-if="showExecutionPanel" class="execution-panel" shadow="never">
        <template #header>
          <div class="card-header">
            <span>分析执行状态</span>
            <el-button v-if="isExecuting" size="small" type="danger" @click="cancelAnalysis">
              <el-icon><Close /></el-icon>
              取消分析
            </el-button>
          </div>
        </template>

        <div class="execution-content">
          <div class="progress-section">
            <el-progress
              :percentage="executionProgress"
              :status="executionStatus"
              :stroke-width="8"
              text-inside
            />
            <p class="progress-text">{{ currentStepText }}</p>
          </div>

          <div class="steps-section">
            <el-steps :active="currentStep" finish-status="success" process-status="process">
              <el-step title="需求解析" description="分析系统架构和需求" />
              <el-step title="威胁识别" description="基于STRIDE模型识别威胁" />
              <el-step title="漏洞分析" description="评估系统安全漏洞" />
              <el-step title="风险评估" description="计算风险等级和影响" />
              <el-step title="缓解建议" description="制定安全缓解措施" />
              <el-step title="合规检查" description="验证法规符合性" />
            </el-steps>
          </div>

          <div v-if="executionLogs.length > 0" class="logs-section">
            <h4>执行日志</h4>
            <div class="logs-container">
              <div
                v-for="(log, index) in executionLogs"
                :key="index"
                :class="['log-item', `log-${log.level}`]"
              >
                <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 分析结果面板 -->
      <el-card v-if="analysisResult" class="result-panel" shadow="never">
        <template #header>
          <div class="card-header">
            <span>TARA分析结果</span>
            <div>
              <el-button size="small" @click="exportResult">
                <el-icon><Download /></el-icon>
                导出报告
              </el-button>
              <el-button size="small" type="primary" @click="proceedToTestCase">
                <el-icon><ArrowRight /></el-icon>
                生成测试用例
              </el-button>
            </div>
          </div>
        </template>

        <el-tabs v-model="activeResultTab" class="result-tabs">
          <!-- 威胁识别结果 -->
          <el-tab-pane label="威胁识别" name="threats">
            <div class="threats-section">
              <div class="section-summary">
                <el-statistic title="识别威胁总数" :value="analysisResult.threats?.length || 0" />
                <el-statistic title="高风险威胁" :value="getHighRiskThreats().length" />
                <el-statistic title="中风险威胁" :value="getMediumRiskThreats().length" />
                <el-statistic title="低风险威胁" :value="getLowRiskThreats().length" />
              </div>

              <el-table :data="analysisResult.threats" style="width: 100%" max-height="400">
                <el-table-column prop="id" label="威胁ID" width="100" />
                <el-table-column prop="name" label="威胁名称" min-width="200" />
                <el-table-column prop="category" label="威胁类别" width="120" />
                <el-table-column prop="impact" label="影响等级" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getImpactTagType(row.impact)">{{ row.impact }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="likelihood" label="可能性" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getLikelihoodTagType(row.likelihood)">{{ row.likelihood }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="risk_score" label="风险评分" width="100">
                  <template #default="{ row }">
                    <el-progress
                      :percentage="(row.risk_score / 10) * 100"
                      :color="getRiskColor(row.risk_score)"
                      :show-text="false"
                      :stroke-width="14"
                    />
                    <span class="risk-score">{{ row.risk_score }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row }">
                    <el-button size="small" @click="viewThreatDetail(row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- 风险评估结果 -->
          <el-tab-pane label="风险评估" name="risks">
            <div class="risks-section">
              <div class="risk-matrix">
                <h4>风险评估矩阵</h4>
                <div class="matrix-container">
                  <div class="matrix-grid">
                    <div class="matrix-header">
                      <div class="matrix-cell header">影响 / 可能性</div>
                      <div class="matrix-cell header">低</div>
                      <div class="matrix-cell header">中</div>
                      <div class="matrix-cell header">高</div>
                    </div>
                    <div class="matrix-row">
                      <div class="matrix-cell header">高</div>
                      <div class="matrix-cell medium">{{ getRiskCount('高', '低') }}</div>
                      <div class="matrix-cell high">{{ getRiskCount('高', '中') }}</div>
                      <div class="matrix-cell critical">{{ getRiskCount('高', '高') }}</div>
                    </div>
                    <div class="matrix-row">
                      <div class="matrix-cell header">中</div>
                      <div class="matrix-cell low">{{ getRiskCount('中', '低') }}</div>
                      <div class="matrix-cell medium">{{ getRiskCount('中', '中') }}</div>
                      <div class="matrix-cell high">{{ getRiskCount('中', '高') }}</div>
                    </div>
                    <div class="matrix-row">
                      <div class="matrix-cell header">低</div>
                      <div class="matrix-cell low">{{ getRiskCount('低', '低') }}</div>
                      <div class="matrix-cell low">{{ getRiskCount('低', '中') }}</div>
                      <div class="matrix-cell medium">{{ getRiskCount('低', '高') }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="risk-summary">
                <h4>风险分布统计</h4>
                <div ref="riskChartRef" class="risk-chart"></div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 缓解建议 -->
          <el-tab-pane label="缓解建议" name="mitigations">
            <div class="mitigations-section">
              <el-collapse>
                <el-collapse-item
                  v-for="(mitigation, index) in analysisResult.mitigations"
                  :key="index"
                  :title="mitigation.title"
                  :name="index"
                >
                  <template #title>
                    <div class="mitigation-header">
                      <span class="mitigation-title">{{ mitigation.title }}</span>
                      <el-tag :type="getPriorityTagType(mitigation.priority)" size="small">
                        {{ mitigation.priority }}
                      </el-tag>
                    </div>
                  </template>
                  <div class="mitigation-content">
                    <p><strong>描述：</strong>{{ mitigation.description }}</p>
                    <p><strong>实施建议：</strong>{{ mitigation.implementation }}</p>
                    <p><strong>预期效果：</strong>{{ mitigation.expected_effect }}</p>
                    <div v-if="mitigation.cost_estimate" class="cost-estimate">
                      <strong>成本评估：</strong>{{ mitigation.cost_estimate }}
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-tab-pane>

          <!-- 合规检查 -->
          <el-tab-pane label="合规检查" name="compliance">
            <div class="compliance-section">
              <div class="compliance-summary">
                <h4>法规符合性检查</h4>
                <div class="compliance-items">
                  <div
                    v-for="(compliance, index) in analysisResult.compliance"
                    :key="index"
                    class="compliance-item"
                  >
                    <div class="compliance-header">
                      <h5>{{ compliance.standard }}</h5>
                      <el-tag :type="compliance.status === 'compliant' ? 'success' : 'danger'">
                        {{ compliance.status === 'compliant' ? '符合' : '不符合' }}
                      </el-tag>
                    </div>
                    <div class="compliance-details">
                      <p><strong>检查项目：</strong>{{ compliance.requirements.join(', ') }}</p>
                      <p><strong>符合率：</strong>{{ compliance.compliance_rate }}%</p>
                      <div v-if="compliance.gaps.length > 0" class="compliance-gaps">
                        <strong>合规缺口：</strong>
                        <ul>
                          <li v-for="gap in compliance.gaps" :key="gap">{{ gap }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 威胁详情对话框 -->
    <el-dialog v-model="showThreatDialog" title="威胁详情" width="600px">
      <div v-if="selectedThreat" class="threat-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="威胁ID">{{ selectedThreat.id }}</el-descriptions-item>
          <el-descriptions-item label="威胁名称">{{ selectedThreat.name }}</el-descriptions-item>
          <el-descriptions-item label="威胁类别">{{ selectedThreat.category }}</el-descriptions-item>
          <el-descriptions-item label="风险评分">{{ selectedThreat.risk_score }}</el-descriptions-item>
          <el-descriptions-item label="影响等级" :span="2">
            <el-tag :type="getImpactTagType(selectedThreat.impact)">{{ selectedThreat.impact }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="可能性" :span="2">
            <el-tag :type="getLikelihoodTagType(selectedThreat.likelihood)">{{ selectedThreat.likelihood }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="威胁描述" :span="2">
            {{ selectedThreat.description }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedThreat.attack_vectors" label="攻击向量" :span="2">
            <el-tag v-for="vector in selectedThreat.attack_vectors" :key="vector" class="threat-tag">
              {{ vector }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Lock, 
  CaretRight, 
  Plus, 
  Close, 
  Download, 
  ArrowRight,
  ChatLineSquare,
  Setting
} from '@element-plus/icons-vue'
import agentsAPI from '../../api/modules/agents'
import * as echarts from 'echarts'
import AgentChat from '../../components/common/AgentChat.vue'

const router = useRouter()

// 响应式数据
const configFormRef = ref()
const componentInputRef = ref()
const riskChartRef = ref()

// 模式控制
const currentMode = ref('chat') // 'chat' 或 'config'
const agentStatus = ref('ready') // 'ready', 'busy', 'error'

const isExecuting = ref(false)
const showExecutionPanel = ref(false)
const showComponentInput = ref(false)
const newComponent = ref('')
const executionProgress = ref(0)
const executionStatus = ref('')
const currentStep = ref(0)
const currentStepText = ref('')
const executionLogs = ref([])
const analysisResult = ref(null)
const activeResultTab = ref('threats')
const showThreatDialog = ref(false)
const selectedThreat = ref(null)

// 表单数据
const configForm = reactive({
  systemName: '',
  systemType: '',
  systemDescription: '',
  components: [],
  interfaces: [],
  dataTypes: [],
  standards: ['iso21434'],
  analysisDepth: 'standard'
})

// 表单验证规则
const configRules = {
  systemName: [
    { required: true, message: '请输入系统名称', trigger: 'blur' }
  ],
  systemType: [
    { required: true, message: '请选择系统类型', trigger: 'change' }
  ],
  systemDescription: [
    { required: true, message: '请输入系统描述', trigger: 'blur' },
    { min: 10, message: '系统描述至少需要10个字符', trigger: 'blur' }
  ]
}

// 计算属性
const isFormValid = computed(() => {
  return configForm.systemName && 
         configForm.systemType && 
         configForm.systemDescription &&
         configForm.systemDescription.length >= 10
})

// 组件管理
const addComponent = () => {
  if (newComponent.value && !configForm.components.includes(newComponent.value)) {
    configForm.components.push(newComponent.value)
    newComponent.value = ''
  }
  showComponentInput.value = false
}

const removeComponent = (index) => {
  configForm.components.splice(index, 1)
}

// 威胁筛选
const getHighRiskThreats = () => {
  return analysisResult.value?.threats?.filter(t => t.risk_score >= 7) || []
}

const getMediumRiskThreats = () => {
  return analysisResult.value?.threats?.filter(t => t.risk_score >= 4 && t.risk_score < 7) || []
}

const getLowRiskThreats = () => {
  return analysisResult.value?.threats?.filter(t => t.risk_score < 4) || []
}

// 风险矩阵计算
const getRiskCount = (impact, likelihood) => {
  if (!analysisResult.value?.threats) return 0
  return analysisResult.value.threats.filter(t => 
    t.impact === impact && t.likelihood === likelihood
  ).length
}

// 样式辅助函数
const getImpactTagType = (impact) => {
  const types = { '高': 'danger', '中': 'warning', '低': 'info' }
  return types[impact] || 'info'
}

const getLikelihoodTagType = (likelihood) => {
  const types = { '高': 'danger', '中': 'warning', '低': 'success' }
  return types[likelihood] || 'info'
}

const getPriorityTagType = (priority) => {
  const types = { '紧急': 'danger', '高': 'warning', '中': 'primary', '低': 'info' }
  return types[priority] || 'info'
}

const getRiskColor = (score) => {
  if (score >= 7) return '#f56c6c'
  if (score >= 4) return '#e6a23c'
  return '#67c23a'
}

// 时间格式化
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
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
    system_name: configForm.systemName || '',
    system_type: configForm.systemType || '',
    system_description: configForm.systemDescription || '',
    components: configForm.components || [],
    interfaces: configForm.interfaces || [],
    data_types: configForm.dataTypes || [],
    standards: configForm.standards || ['iso21434'],
    analysis_depth: configForm.analysisDepth || 'standard'
  }
}

const onChatExecutionStart = () => {
  agentStatus.value = 'busy'
  ElMessage.info('TARA智能体开始执行...')
}

const onChatExecutionComplete = () => {
  agentStatus.value = 'ready'
  ElMessage.success('TARA分析已完成')
}

const onChatExecutionError = (error) => {
  agentStatus.value = 'error'
  ElMessage.error(`TARA分析失败: ${error.message}`)
}

// 分析执行
const startAnalysis = async () => {
  try {
    // 表单验证
    const valid = await configFormRef.value.validate()
    if (!valid) return

    isExecuting.value = true
    showExecutionPanel.value = true
    executionProgress.value = 0
    currentStep.value = 0
    executionLogs.value = []
    analysisResult.value = null

    // 构建分析请求
    const analysisRequest = {
      user_request: `对${configForm.systemName}进行TARA威胁分析和风险评估`,
      context: {
        system_name: configForm.systemName,
        system_type: configForm.systemType,
        system_description: configForm.systemDescription,
        components: configForm.components,
        interfaces: configForm.interfaces,
        data_types: configForm.dataTypes,
        standards: configForm.standards,
        analysis_depth: configForm.analysisDepth,
        analysis_type: 'tara'
      },
      timeout: 300,
      stream: false,
      // 添加缺失的参数
      priority: "normal",
      metadata: {
        source: "tara_ui",
        version: "1.0"
      },
      enable_planning: true,
      step_by_step: true,
      chat_mode: false,
      agent_config: {
        model: "qwen3"
      }
    }

    // 添加初始日志
    addLog('info', '开始TARA分析...')
    addLog('info', `分析目标: ${configForm.systemName}`)
    addLog('info', `分析深度: ${configForm.analysisDepth}`)
    
    try {
      // 调用TARA智能体API执行分析
      const response = await agentsAPI.tara.analyze(analysisRequest)
      
      if (response.data?.success) {
        const result = response.data.result
        
        // 解析分析结果
        if (typeof result === 'string') {
          // 如果结果是字符串，尝试解析JSON
          try {
            analysisResult.value = JSON.parse(result)
          } catch (parseError) {
            // 如果无法解析为JSON，创建一个包装结果
            analysisResult.value = {
              summary: result,
              threats: [],
              mitigations: [],
              compliance: [],
              raw_output: result
            }
          }
        } else if (typeof result === 'object') {
          analysisResult.value = result
        } else {
          throw new Error('分析结果格式不正确')
        }
        
        executionProgress.value = 100
        executionStatus.value = 'success'
        currentStepText.value = '分析完成'
        addLog('success', 'TARA分析已完成')
        
        // 记录结果统计
        if (analysisResult.value.threats) {
          addLog('info', `识别威胁: ${analysisResult.value.threats.length} 个`)
        }
        if (analysisResult.value.mitigations) {
          addLog('info', `生成缓解措施: ${analysisResult.value.mitigations.length} 个`)
        }
        if (analysisResult.value.compliance) {
          addLog('info', `合规检查: ${analysisResult.value.compliance.length} 项标准`)
        }
        
        // 渲染风险图表
        await nextTick()
        renderRiskChart()
        
      } else {
        throw new Error(response.data?.error || response.data?.message || '分析失败')
      }
      
    } catch (apiError) {
      console.error('TARA分析API调用失败:', apiError)
      executionStatus.value = 'exception'
      addLog('error', `API调用失败: ${apiError.message}`)
      
      // 根据错误类型给出不同的提示
      if (apiError.response?.status === 404) {
        ElMessage.error('TARA智能体服务未启动，请联系管理员')
      } else if (apiError.response?.status === 500) {
        ElMessage.error('TARA智能体执行错误，请检查输入参数')
      } else if (apiError.code === 'ECONNREFUSED') {
        ElMessage.error('无法连接到后端服务，请检查网络连接')
      } else {
        ElMessage.error(`分析失败: ${apiError.message}`)
      }
    }

  } catch (error) {
    console.error('TARA分析失败:', error)
    executionStatus.value = 'exception'
    addLog('error', `分析失败: ${error.message}`)
    ElMessage.error(`分析失败: ${error.message}`)
  } finally {
    isExecuting.value = false
  }
}

// 流式分析执行
const startStreamAnalysis = async () => {
  try {
    // 表单验证
    const valid = await configFormRef.value.validate()
    if (!valid) return

    isExecuting.value = true
    showExecutionPanel.value = true
    executionProgress.value = 0
    currentStep.value = 0
    executionLogs.value = []
    analysisResult.value = null

    // 构建分析请求
    const analysisRequest = {
      user_request: `对${configForm.systemName}进行TARA威胁分析和风险评估`,
      context: {
        system_name: configForm.systemName,
        system_type: configForm.systemType,
        system_description: configForm.systemDescription,
        components: configForm.components,
        interfaces: configForm.interfaces,
        data_types: configForm.dataTypes,
        standards: configForm.standards,
        analysis_depth: configForm.analysisDepth,
        analysis_type: 'tara'
      },
      timeout: 300,
      stream: true
    }

    addLog('info', '开始流式TARA分析...')
    
    try {
      // 使用流式API
      const reader = await agentsAPI.tara.analyzeStream(analysisRequest)
      
      let buffer = ''
      let stepProgress = 0
      const maxSteps = 6 // 预期分析步骤数
      
      // 读取流式响应
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        // 解码响应数据
        const chunk = new TextDecoder().decode(value)
        buffer += chunk
        
        // 处理完整的行
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后不完整的行
        
        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              handleStreamData(data)
              
              // 更新进度
              if (data.type === 'step_completed') {
                stepProgress++
                executionProgress.value = (stepProgress / maxSteps) * 90
              }
            } catch (parseError) {
              console.warn('流式数据解析失败:', parseError)
            }
          }
        }
      }
      
      // 完成分析
      executionProgress.value = 100
      executionStatus.value = 'success'
      currentStepText.value = '流式分析完成'
      addLog('success', '流式TARA分析已完成')
      
      // 渲染风险图表
      await nextTick()
      renderRiskChart()
      
    } catch (streamError) {
      console.error('流式分析失败:', streamError)
      executionStatus.value = 'exception'
      addLog('error', `流式分析失败: ${streamError.message}`)
      ElMessage.error(`流式分析失败: ${streamError.message}`)
    }

  } catch (error) {
    console.error('流式TARA分析失败:', error)
    executionStatus.value = 'exception'
    addLog('error', `分析失败: ${error.message}`)
    ElMessage.error(`分析失败: ${error.message}`)
  } finally {
    isExecuting.value = false
  }
}

// 处理流式数据
const handleStreamData = (data) => {
  switch (data.type) {
    case 'step_start':
      currentStepText.value = `正在执行: ${data.step_name}`
      addLog('info', `开始${data.step_name}...`)
      break
      
    case 'step_progress':
      if (data.message) {
        addLog('info', data.message)
      }
      break
      
    case 'step_completed':
      addLog('success', `${data.step_name}完成`)
      if (data.result) {
        // 逐步构建分析结果
        if (!analysisResult.value) {
          analysisResult.value = {
            threats: [],
            mitigations: [],
            compliance: []
          }
        }
        
        // 根据步骤类型更新相应结果
        if (data.step_name.includes('威胁') && data.result.threats) {
          analysisResult.value.threats = data.result.threats
        } else if (data.step_name.includes('缓解') && data.result.mitigations) {
          analysisResult.value.mitigations = data.result.mitigations
        } else if (data.step_name.includes('合规') && data.result.compliance) {
          analysisResult.value.compliance = data.result.compliance
        }
      }
      break
      
    case 'partial_result':
      // 处理部分结果
      if (data.threats) {
        if (!analysisResult.value) analysisResult.value = {}
        analysisResult.value.threats = data.threats
        addLog('info', `发现威胁: ${data.threats.length} 个`)
      }
      if (data.mitigations) {
        if (!analysisResult.value) analysisResult.value = {}
        analysisResult.value.mitigations = data.mitigations
        addLog('info', `生成缓解措施: ${data.mitigations.length} 个`)
      }
      break
      
    case 'error':
      addLog('error', data.message || '执行过程中发生错误')
      break
      
    default:
      if (data.message) {
        addLog('info', data.message)
      }
  }
}

// 添加日志
const addLog = (level, message) => {
  executionLogs.value.push({
    level,
    message,
    timestamp: new Date()
  })
}

// 取消分析
const cancelAnalysis = async () => {
  try {
    await ElMessageBox.confirm('确定要取消当前分析吗？', '确认取消', {
      type: 'warning'
    })
    
    isExecuting.value = false
    executionStatus.value = 'exception'
    addLog('warning', '分析已被用户取消')
    ElMessage.info('分析已取消')
  } catch {
    // 用户取消确认
  }
}

// 查看威胁详情
const viewThreatDetail = (threat) => {
  selectedThreat.value = threat
  showThreatDialog.value = true
}

// 导出结果
const exportResult = () => {
  const data = JSON.stringify(analysisResult.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `TARA_Analysis_${configForm.systemName}_${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('分析结果已导出')
}

// 进入测试用例生成
const proceedToTestCase = () => {
  ElMessageBox.confirm(
    '是否基于当前TARA分析结果生成测试用例？',
    '生成测试用例',
    {
      type: 'info',
      confirmButtonText: '继续',
      cancelButtonText: '取消'
    }
  ).then(() => {
    router.push({
      path: '/agents/test-case',
      query: { taraResult: JSON.stringify(analysisResult.value) }
    })
  }).catch(() => {
    // 用户取消
  })
}

// 渲染风险图表
const renderRiskChart = () => {
  if (!riskChartRef.value || !analysisResult.value?.threats) return

  const chart = echarts.init(riskChartRef.value)
  
  const riskData = [
    { name: '高风险', value: getHighRiskThreats().length, itemStyle: { color: '#f56c6c' } },
    { name: '中风险', value: getMediumRiskThreats().length, itemStyle: { color: '#e6a23c' } },
    { name: '低风险', value: getLowRiskThreats().length, itemStyle: { color: '#67c23a' } }
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '风险分布',
        type: 'pie',
        radius: '50%',
        data: riskData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  chart.setOption(option)
}

// 组件挂载时的处理
onMounted(() => {
  // 监听组件输入框显示状态
  watch(showComponentInput, (newVal) => {
    if (newVal) {
      nextTick(() => {
        componentInputRef.value?.focus()
      })
    }
  })
})
</script>

<style scoped>
.tara-agent {
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

.tara-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-tag {
  margin: 0 8px 8px 0;
}

.component-input {
  width: 120px;
  margin-right: 8px;
}

.execution-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.progress-section {
  text-align: center;
}

.progress-text {
  margin: 12px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.steps-section {
  padding: 0 24px;
}

.logs-section h4 {
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  background: var(--el-bg-color-page);
}

.log-item {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
}

.log-time {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.log-message {
  flex: 1;
}

.log-info .log-message {
  color: var(--el-text-color-primary);
}

.log-success .log-message {
  color: var(--el-color-success);
}

.log-warning .log-message {
  color: var(--el-color-warning);
}

.log-error .log-message {
  color: var(--el-color-danger);
}

.result-tabs {
  margin-top: 16px;
}

.section-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.threats-section .risk-score {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 600;
}

.matrix-container {
  margin-bottom: 24px;
}

.matrix-grid {
  display: inline-block;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
}

.matrix-header,
.matrix-row {
  display: flex;
}

.matrix-cell {
  width: 80px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid var(--el-border-color);
  border-bottom: 1px solid var(--el-border-color);
  font-weight: 500;
}

.matrix-cell:last-child {
  border-right: none;
}

.matrix-row:last-child .matrix-cell {
  border-bottom: none;
}

.matrix-cell.header {
  background: var(--el-fill-color-light);
  font-weight: 600;
}

.matrix-cell.low {
  background: #f0f9ff;
  color: #0369a1;
}

.matrix-cell.medium {
  background: #fffbeb;
  color: #d97706;
}

.matrix-cell.high {
  background: #fef2f2;
  color: #dc2626;
}

.matrix-cell.critical {
  background: #7f1d1d;
  color: white;
}

.risk-chart {
  height: 300px;
  width: 100%;
}

.mitigation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.mitigation-title {
  flex: 1;
}

.mitigation-content {
  padding: 16px 0;
}

.mitigation-content p {
  margin: 8px 0;
  line-height: 1.6;
}

.cost-estimate {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 13px;
}

.compliance-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compliance-item {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
}

.compliance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.compliance-header h5 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.compliance-details p {
  margin: 8px 0;
  line-height: 1.6;
}

.compliance-gaps ul {
  margin: 8px 0 0 20px;
}

.compliance-gaps li {
  margin: 4px 0;
}

.threat-detail .threat-tag {
  margin: 0 8px 8px 0;
}

@media (max-width: 768px) {
  .section-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .matrix-cell {
    width: 60px;
    height: 40px;
    font-size: 12px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}
</style> 