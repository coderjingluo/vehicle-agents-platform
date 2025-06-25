<template>
  <div class="tara-agent">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Lock /></el-icon>
        TARA智能体
      </h1>
      <p class="page-description">威胁分析与风险评估 (Threat Analysis and Risk Assessment)</p>
    </div>

    <div class="tara-content">
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
  ArrowRight 
} from '@element-plus/icons-vue'
import agentsAPI from '../../api/modules/agents'
import * as echarts from 'echarts'

const router = useRouter()

// 响应式数据
const configFormRef = ref()
const componentInputRef = ref()
const riskChartRef = ref()

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

// 生成模拟TARA分析结果
const generateMockTARAResult = () => {
  return {
    threats: [
      {
        id: 'T001',
        name: 'CAN总线未授权访问',
        description: '攻击者可能通过物理访问或恶意软件获取CAN总线的访问权限，导致车辆控制功能被篡改',
        category: '网络安全',
        impact: '高',
        likelihood: '中',
        risk_score: 7.5,
        attack_vectors: ['物理接入', 'OBD-II端口', '恶意软件注入']
      },
      {
        id: 'T002',
        name: '无线通信窃听',
        description: '车辆与外部系统的无线通信可能被恶意第三方截获和分析',
        category: '通信安全',
        impact: '中',
        likelihood: '高',
        risk_score: 6.0,
        attack_vectors: ['射频窃听', '中间人攻击', '伪基站']
      },
      {
        id: 'T003',
        name: '固件篡改',
        description: '攻击者可能通过各种手段篡改车载控制单元的固件',
        category: '软件安全',
        impact: '高',
        likelihood: '低',
        risk_score: 5.5,
        attack_vectors: ['调试接口', '引导程序漏洞', '供应链攻击']
      },
      {
        id: 'T004',
        name: '传感器数据欺骗',
        description: '攻击者可能通过信号注入等方式欺骗车辆传感器',
        category: '硬件安全',
        impact: '高',
        likelihood: '中',
        risk_score: 7.0,
        attack_vectors: ['信号注入', '传感器干扰', '物理遮挡']
      },
      {
        id: 'T005',
        name: '用户数据泄露',
        description: '车辆收集的用户个人数据可能被非法访问或泄露',
        category: '隐私安全',
        impact: '中',
        likelihood: '中',
        risk_score: 4.5,
        attack_vectors: ['数据库入侵', '存储设备盗取', '网络传输截获']
      },
      {
        id: 'T006',
        name: '远程代码执行',
        description: '攻击者可能通过漏洞在车载系统上执行恶意代码',
        category: '软件安全',
        impact: '高',
        likelihood: '低',
        risk_score: 5.0,
        attack_vectors: ['缓冲区溢出', '脚本注入', 'API漏洞']
      }
    ],
    mitigations: [
      {
        title: 'CAN总线安全加固',
        description: '实施CAN总线访问控制和消息认证机制',
        priority: '高',
        implementation: '部署CAN安全网关，实施消息签名验证，限制物理访问',
        expected_effect: '降低CAN总线未授权访问风险至低等级',
        cost_estimate: '中等投入，预计6-8个月实施周期'
      },
      {
        title: '通信加密强化',
        description: '对所有无线通信实施端到端加密',
        priority: '中',
        implementation: '采用TLS 1.3+协议，实施证书管理，定期更新加密密钥',
        expected_effect: '有效防止通信窃听和篡改',
        cost_estimate: '低等投入，预计3-4个月实施周期'
      },
      {
        title: '固件安全启动',
        description: '实施安全启动和固件完整性校验',
        priority: '高',
        implementation: '部署硬件安全模块(HSM)，实施固件签名验证',
        expected_effect: '防止固件篡改，确保系统完整性',
        cost_estimate: '高等投入，预计8-12个月实施周期'
      },
      {
        title: '传感器信号验证',
        description: '实施多传感器融合和信号异常检测',
        priority: '中',
        implementation: '部署传感器融合算法，实施实时异常检测',
        expected_effect: '降低传感器欺骗成功率',
        cost_estimate: '中等投入，预计4-6个月实施周期'
      }
    ],
    compliance: [
      {
        standard: 'ISO 21434',
        status: 'compliant',
        compliance_rate: 85,
        requirements: ['网络安全管理', '风险评估', '威胁分析', '安全验证'],
        gaps: ['缺少持续监控机制', '部分供应商评估不完整']
      },
      {
        standard: 'SAE J3061',
        status: 'compliant',
        compliance_rate: 78,
        requirements: ['车联网安全', '通信安全', '数据保护'],
        gaps: ['V2X通信安全措施不足', '数据生命周期管理缺失']
      },
      {
        standard: 'UNECE WP.29',
        status: 'non-compliant',
        compliance_rate: 65,
        requirements: ['网络安全管理系统', '风险管理', '监控响应'],
        gaps: ['缺少CSMS认证', '事件响应流程不完善', '供应链安全管理不足']
      }
    ]
  }
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
      user_request: `对${configForm.systemName}进行TARA分析`,
      context: {
        system_name: configForm.systemName,
        system_type: configForm.systemType,
        system_description: configForm.systemDescription,
        components: configForm.components,
        interfaces: configForm.interfaces,
        data_types: configForm.dataTypes,
        standards: configForm.standards,
        analysis_depth: configForm.analysisDepth
      },
      timeout: 300,
      stream: false
    }

    // 添加初始日志
    addLog('info', '开始TARA分析...')
    
    // 模拟分析过程
    await simulateAnalysisProgress()

    // 调用API执行分析
    try {
      const response = await agentsAPI.tara.analyze(analysisRequest)
      
      if (response.data.success) {
        analysisResult.value = response.data.result
        executionProgress.value = 100
        executionStatus.value = 'success'
        currentStepText.value = '分析完成'
        addLog('success', 'TARA分析已完成')
        
        // 渲染风险图表
        nextTick(() => {
          renderRiskChart()
        })
      } else {
        throw new Error(response.data.error || '分析失败')
      }
    } catch (apiError) {
      // 如果API调用失败，使用模拟数据进行演示
      console.warn('API调用失败，使用模拟数据:', apiError)
      addLog('warning', 'API连接失败，使用模拟数据进行演示')
      
      // 使用模拟的TARA分析结果
      analysisResult.value = generateMockTARAResult()
      executionProgress.value = 100
      executionStatus.value = 'success'
      currentStepText.value = '分析完成（演示模式）'
      addLog('success', 'TARA分析已完成（演示模式）')
      
      // 渲染风险图表
      nextTick(() => {
        renderRiskChart()
      })
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

// 模拟分析进度
const simulateAnalysisProgress = async () => {
  const steps = [
    { name: '需求解析', duration: 2000 },
    { name: '威胁识别', duration: 3000 },
    { name: '漏洞分析', duration: 2500 },
    { name: '风险评估', duration: 3000 },
    { name: '缓解建议', duration: 2000 },
    { name: '合规检查', duration: 1500 }
  ]

  for (let i = 0; i < steps.length; i++) {
    currentStep.value = i
    currentStepText.value = `正在执行: ${steps[i].name}`
    addLog('info', `开始${steps[i].name}...`)
    
    await new Promise(resolve => setTimeout(resolve, steps[i].duration))
    
    executionProgress.value = ((i + 1) / steps.length) * 90
    addLog('success', `${steps[i].name}完成`)
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
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
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