<template>
  <div class="model-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">MCP工具管理</h1>
        <p class="page-description">管理模型调用协议(Model Context Protocol) 工具配置</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshAllConnections" :loading="refreshing">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
        <el-button @click="showImportDialog">
          <el-icon><Upload /></el-icon>
          导入配置
        </el-button>
        <el-button @click="exportConfigs">
          <el-icon><Download /></el-icon>
          导出配置
        </el-button>
        <el-button type="primary" @click="showAddMCPDialog">
          <el-icon><Plus /></el-icon>
          添加MCP
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-number">{{ mcpList.length }}</div>
        <div class="stat-label">总配置数</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ activeMCPCount }}</div>
        <div class="stat-label">已连接</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ totalToolCount }}</div>
        <div class="stat-label">可用工具</div>
      </div>
    </div>

    <!-- 配置选项卡 -->
    <div class="config-tabs">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="配置列表" name="list">
          <!-- 操作栏 -->
          <div class="operation-bar">
            <div class="search-box">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索MCP配置..."
                prefix-icon="Search"
                clearable
                @input="handleSearch"
              />
            </div>
            <div class="filter-box">
              <el-select v-model="statusFilter" placeholder="状态筛选" clearable>
                <el-option label="全部" value="" />
                <el-option label="已连接" value="active" />
                <el-option label="已断开" value="inactive" />
              </el-select>
            </div>
          </div>

          <!-- MCP工具列表 -->
          <div class="mcp-list">
            <div v-for="mcp in filteredMCPList" :key="mcp.id" class="mcp-item">
              <div class="mcp-header">
                <div class="mcp-icon">
                  <el-icon><component :is="mcp.icon" /></el-icon>
                </div>
                <div class="mcp-info">
                  <div class="mcp-name">{{ mcp.name }}</div>
                  <div class="mcp-description">{{ mcp.description }}</div>
                </div>
                <div class="mcp-status">
                  <el-tag :type="mcp.status === 'active' ? 'success' : 'info'">
                    {{ mcp.status === 'active' ? '已连接' : '已断开' }}
                  </el-tag>
                </div>
                <div class="mcp-actions">
                  <el-button 
                    text 
                    @click="testConnection(mcp)" 
                    :loading="mcp.testing"
                    title="测试连接"
                  >
                    <el-icon><Connection /></el-icon>
                    测试
                  </el-button>
                  <el-button 
                    text 
                    @click="toggleMCPStatus(mcp)"
                    :type="mcp.status === 'active' ? 'warning' : 'success'"
                  >
                    <el-icon><component :is="mcp.status === 'active' ? 'VideoPause' : 'VideoPlay'" /></el-icon>
                    {{ mcp.status === 'active' ? '断开' : '连接' }}
                  </el-button>
                  <el-button text @click="editMCP(mcp)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button text @click="viewTools(mcp)">
                    <el-icon><View /></el-icon>
                    工具
                  </el-button>
                  <el-button text type="danger" @click="deleteMCP(mcp.id)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
              
              <div class="mcp-details">
                <div class="detail-row">
                  <span class="label">类型：</span>
                  <span class="value">{{ mcp.type }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">地址：</span>
                  <span class="value">{{ mcp.url }}</span>
                </div>
                <div class="detail-row" v-if="mcp.lastConnected">
                  <span class="label">最后连接：</span>
                  <span class="value">{{ formatDate(mcp.lastConnected) }}</span>
                </div>
                <div class="detail-row">
                  <span class="label">工具数量：</span>
                  <span class="value">{{ mcp.toolCount }}</span>
                </div>
                <div class="detail-row" v-if="mcp.responseTime">
                  <span class="label">响应时间：</span>
                  <span class="value">{{ mcp.responseTime }}ms</span>
                </div>
              </div>

              <!-- 展开的工具列表 -->
              <div v-if="mcp.showTools && mcp.tools" class="tools-section">
                <h4 class="tools-title">可用工具 ({{ mcp.tools.length }})</h4>
                <div class="tools-grid">
                  <div v-for="tool in mcp.tools" :key="tool.name" class="tool-item">
                    <div class="tool-name">{{ tool.name }}</div>
                    <div class="tool-desc">{{ tool.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="连接日志" name="logs">
          <div class="logs-section">
            <div class="logs-header">
              <h3>连接日志</h3>
              <el-button @click="clearLogs" size="small">清空日志</el-button>
            </div>
            <div class="logs-list">
              <div v-for="log in connectionLogs" :key="log.id" class="log-item">
                <div class="log-time">{{ formatDate(log.timestamp) }}</div>
                <div class="log-level" :class="log.level">{{ log.level.toUpperCase() }}</div>
                <div class="log-message">{{ log.message }}</div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加/编辑MCP对话框 -->
    <el-dialog 
      v-model="mcpDialogVisible" 
      :title="isEditMode ? '编辑MCP配置' : '添加MCP配置'" 
      width="500px"
    >
      <el-form ref="dialogMcpForm" :model="dialogMCPForm" :rules="mcpRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="dialogMCPForm.name" placeholder="MCP服务器名称" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="dialogMCPForm.description" 
            type="textarea" 
            :rows="2"
            placeholder="描述功能"
          />
        </el-form-item>

        <el-form-item label="类型" prop="type">
          <el-select v-model="dialogMCPForm.type" placeholder="连接类型" class="full-width">
            <el-option label="SSE (HTTP)" value="SSE" />
            <el-option label="WebSocket" value="WebSocket" />
            <el-option label="Local Process" value="Local" />
          </el-select>
        </el-form-item>

        <el-form-item label="URL" prop="url">
          <el-input v-model="dialogMCPForm.url" placeholder="服务器地址" />
        </el-form-item>

        <el-form-item label="认证" v-if="dialogMCPForm.type !== 'Local'">
          <el-input 
            v-model="dialogMCPForm.apiKey" 
            type="password"
            placeholder="API Key (可选)"
            show-password
          />
        </el-form-item>

        <el-form-item label="超时时间">
          <el-input-number 
            v-model="dialogMCPForm.timeout" 
            :min="1000" 
            :max="30000"
            :step="1000"
            placeholder="毫秒"
          />
        </el-form-item>

        <el-form-item label="自动连接">
          <el-switch v-model="dialogMCPForm.autoConnect" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="mcpDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDialogForm" :loading="submitting">
          {{ isEditMode ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 工具详情对话框 -->
    <el-dialog v-model="toolsDialogVisible" title="工具详情" width="800px">
      <div v-if="selectedMCP" class="tools-detail">
        <div class="tools-header">
          <h3>{{ selectedMCP.name }} - 可用工具</h3>
          <el-button @click="refreshTools(selectedMCP)" :loading="selectedMCP.refreshing">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <div v-if="selectedMCP.tools && selectedMCP.tools.length > 0" class="tools-table">
          <el-table :data="selectedMCP.tools" stripe>
            <el-table-column prop="name" label="工具名称" width="200" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="inputSchema" label="输入参数" width="120">
              <template #default="{ row }">
                <el-button text @click="viewSchema(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-else class="no-tools">
          <el-empty description="暂无可用工具" />
        </div>
      </div>
    </el-dialog>

    <!-- 导入配置对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入配置" width="400px">
      <div class="import-section">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="false"
          accept=".json"
          @change="handleFileUpload"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            选择配置文件
          </el-button>
        </el-upload>
        
        <div v-if="importData" class="import-preview">
          <h4>预览 ({{ importData.length }} 个配置)</h4>
          <div class="preview-list">
            <div v-for="config in importData" :key="config.name" class="preview-item">
              {{ config.name }} - {{ config.description }}
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmImport" 
          :disabled="!importData"
          :loading="importing"
        >
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Edit, Delete, Setting, Monitor, Refresh, Upload, Download,
  Connection, VideoPause, VideoPlay, View, Search
} from '@element-plus/icons-vue'

// API imports
import modelsAPI from '../api/modules/models'
import systemAPI from '../api/modules/system'

// 响应式数据
const activeTab = ref('list')
const mcpDialogVisible = ref(false)
const toolsDialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEditMode = ref(false)
const refreshing = ref(false)
const submitting = ref(false)
const importing = ref(false)
const loading = ref(false)
const selectedMCP = ref(null)
const editingMCPId = ref(null)
const searchKeyword = ref('')
const statusFilter = ref('')
const importData = ref(null)

// 表单引用
const dialogMcpForm = ref(null)
const uploadRef = ref(null)

// 数据存储
const mcpList = ref([])
const connectionLogs = ref([])
const modelProviders = ref([])

// 表单数据
const dialogMCPForm = reactive({
  name: '',
  description: '',
  type: 'SSE',
  url: '',
  apiKey: '',
  timeout: 5000,
  autoConnect: false
})

// 表单验证规则
const mcpRules = {
  name: [
    { required: true, message: '请输入MCP名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择连接类型', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ]
}

// 计算属性
const activeMCPCount = computed(() => {
  return mcpList.value.filter(mcp => mcp.status === 'active').length
})

const totalToolCount = computed(() => {
  return mcpList.value.reduce((sum, mcp) => sum + (mcp.toolCount || 0), 0)
})

const filteredMCPList = computed(() => {
  let filtered = mcpList.value
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(mcp => 
      mcp.name.toLowerCase().includes(keyword) ||
      mcp.description.toLowerCase().includes(keyword)
    )
  }
  
  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter(mcp => mcp.status === statusFilter.value)
  }
  
  return filtered
})

// 获取MCP配置列表
const fetchMCPConfigs = async () => {
  try {
    loading.value = true
    const response = await modelsAPI.getMCPConfigs()
    
    if (response.data?.success !== false) {
      const configs = response.data?.configs || response.data || []
      
      mcpList.value = configs.map(config => ({
        id: config.id,
        name: config.name,
        description: config.description || '无描述',
        type: config.type || 'SSE',
        url: config.url,
        status: config.status || 'inactive',
        lastConnected: config.last_connected,
        toolCount: config.tool_count || 0,
        icon: getIconByType(config.type),
        testing: false,
        responseTime: config.response_time,
        autoConnect: config.auto_connect || false,
        timeout: config.timeout || 5000,
        tools: config.tools || [],
        apiKey: config.api_key || ''
      }))
    }
  } catch (error) {
    console.error('获取MCP配置失败:', error)
    ElMessage.error('获取MCP配置失败')
  } finally {
    loading.value = false
  }
}

// 获取模型提供商列表
const fetchModelProviders = async () => {
  try {
    const response = await systemAPI.getLLMProviders()
    if (response.data?.success !== false) {
      modelProviders.value = response.data?.providers || response.data || []
    }
  } catch (error) {
    console.error('获取模型提供商失败:', error)
  }
}

// 获取连接日志
const fetchConnectionLogs = async () => {
  try {
    const response = await modelsAPI.getConnectionLogs()
    if (response.data?.success !== false) {
      const logs = response.data?.logs || response.data || []
      
      connectionLogs.value = logs.map(log => ({
        id: log.id,
        timestamp: new Date(log.timestamp),
        level: log.level,
        message: log.message
      }))
    }
  } catch (error) {
    console.error('获取连接日志失败:', error)
  }
}

// MCP操作方法
const showAddMCPDialog = () => {
  isEditMode.value = false
  resetDialogForm()
  mcpDialogVisible.value = true
}

const editMCP = (mcp) => {
  isEditMode.value = true
  editingMCPId.value = mcp.id
  
  // 填充表单
  Object.assign(dialogMCPForm, {
    name: mcp.name,
    description: mcp.description,
    type: mcp.type,
    url: mcp.url,
    apiKey: mcp.apiKey || '',
    timeout: mcp.timeout,
    autoConnect: mcp.autoConnect
  })
  
  mcpDialogVisible.value = true
}

const deleteMCP = async (mcpId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个MCP配置吗？此操作不可恢复。',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await modelsAPI.deleteMCPConfig(mcpId)
    ElMessage.success('MCP配置删除成功')
    
    await fetchMCPConfigs()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除MCP配置失败:', error)
      ElMessage.error('删除MCP配置失败')
    }
  }
}

const testConnection = async (mcp) => {
  if (mcp.testing) return
  
  try {
    mcp.testing = true
    addLog('info', `开始测试连接: ${mcp.name}`)
    
    const startTime = Date.now()
    const response = await modelsAPI.testMCPConnection(mcp.id)
    const responseTime = Date.now() - startTime
    
    if (response.data?.success !== false) {
      mcp.status = 'active'
      mcp.responseTime = responseTime
      mcp.lastConnected = new Date().toISOString()
      
      // 更新工具列表
      if (response.data?.tools) {
        mcp.tools = response.data.tools
        mcp.toolCount = response.data.tools.length
      }
      
      addLog('success', `${mcp.name} 连接成功，响应时间: ${responseTime}ms`)
      ElMessage.success(`${mcp.name} 连接测试成功`)
    } else {
      throw new Error(response.data?.message || '连接测试失败')
    }
    
  } catch (error) {
    console.error('连接测试失败:', error)
    mcp.status = 'inactive'
    mcp.responseTime = null
    
    addLog('error', `${mcp.name} 连接失败: ${error.message}`)
    ElMessage.error(`${mcp.name} 连接测试失败: ${error.message}`)
  } finally {
    mcp.testing = false
  }
}

const toggleMCPStatus = async (mcp) => {
  if (mcp.status === 'active') {
    // 断开连接
    try {
      await modelsAPI.disconnectMCP(mcp.id)
      mcp.status = 'inactive'
      addLog('info', `${mcp.name} 已断开连接`)
      ElMessage.success(`${mcp.name} 已断开连接`)
    } catch (error) {
      console.error('断开连接失败:', error)
      ElMessage.error('断开连接失败')
    }
  } else {
    // 建立连接
    await testConnection(mcp)
  }
}

const viewTools = (mcp) => {
  selectedMCP.value = mcp
  toolsDialogVisible.value = true
}

const refreshTools = async (mcp) => {
  if (mcp.refreshing) return
  
  try {
    mcp.refreshing = true
    const response = await modelsAPI.getMCPTools(mcp.id)
    
    if (response.data?.success !== false) {
      mcp.tools = response.data?.tools || []
      mcp.toolCount = mcp.tools.length
      ElMessage.success('工具列表刷新成功')
    }
  } catch (error) {
    console.error('刷新工具列表失败:', error)
    ElMessage.error('刷新工具列表失败')
  } finally {
    mcp.refreshing = false
  }
}

const refreshAllConnections = async () => {
  refreshing.value = true
  
  try {
    // 刷新所有活跃连接的状态
    const activeConnections = mcpList.value.filter(mcp => mcp.status === 'active')
    
    const promises = activeConnections.map(mcp => testConnection(mcp))
    await Promise.allSettled(promises)
    
    ElMessage.success('连接状态刷新完成')
  } catch (error) {
    console.error('刷新连接状态失败:', error)
    ElMessage.error('刷新连接状态失败')
  } finally {
    refreshing.value = false
  }
}

// 表单操作
const submitDialogForm = async () => {
  try {
    const valid = await dialogMcpForm.value?.validate()
    if (!valid) return
    
    submitting.value = true
    
    const formData = {
      name: dialogMCPForm.name.trim(),
      description: dialogMCPForm.description.trim(),
      type: dialogMCPForm.type,
      url: dialogMCPForm.url.trim(),
      api_key: dialogMCPForm.apiKey || null,
      timeout: dialogMCPForm.timeout,
      auto_connect: dialogMCPForm.autoConnect
    }
    
    if (isEditMode.value) {
      // 更新配置
      await modelsAPI.updateMCPConfig(editingMCPId.value, formData)
      ElMessage.success('MCP配置更新成功')
    } else {
      // 创建配置
      await modelsAPI.createMCPConfig(formData)
      ElMessage.success('MCP配置创建成功')
    }
    
    mcpDialogVisible.value = false
    await fetchMCPConfigs()
    
  } catch (error) {
    console.error('保存MCP配置失败:', error)
    ElMessage.error('保存MCP配置失败')
  } finally {
    submitting.value = false
  }
}

const resetDialogForm = () => {
  Object.assign(dialogMCPForm, {
    name: '',
    description: '',
    type: 'SSE',
    url: '',
    apiKey: '',
    timeout: 5000,
    autoConnect: false
  })
  
  editingMCPId.value = null
  dialogMcpForm.value?.resetFields()
}

// 搜索和筛选
const handleSearch = () => {
  // 搜索逻辑在computed中处理
}

// 配置导入导出
const exportConfigs = () => {
  try {
    const configs = mcpList.value.map(mcp => ({
      name: mcp.name,
      description: mcp.description,
      type: mcp.type,
      url: mcp.url,
      timeout: mcp.timeout,
      autoConnect: mcp.autoConnect
    }))
    
    const blob = new Blob([JSON.stringify(configs, null, 2)], { 
      type: 'application/json' 
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'mcp-configs.json'
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('配置导出成功')
  } catch (error) {
    console.error('导出配置失败:', error)
    ElMessage.error('导出配置失败')
  }
}

const showImportDialog = () => {
  importDialogVisible.value = true
  importData.value = null
}

const handleFileUpload = (file) => {
  if (!file.raw) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (Array.isArray(data)) {
        importData.value = data
      } else {
        throw new Error('配置文件格式不正确')
      }
    } catch (error) {
      console.error('解析配置文件失败:', error)
      ElMessage.error('配置文件格式不正确')
    }
  }
  reader.readAsText(file.raw)
}

const confirmImport = async () => {
  if (!importData.value) return
  
  try {
    importing.value = true
    
    const promises = importData.value.map(config => 
      modelsAPI.createMCPConfig(config)
    )
    
    const results = await Promise.allSettled(promises)
    const successful = results.filter(r => r.status === 'fulfilled').length
    const failed = results.filter(r => r.status === 'rejected').length
    
    if (successful > 0) {
      ElMessage.success(`成功导入 ${successful} 个配置`)
    }
    if (failed > 0) {
      ElMessage.warning(`${failed} 个配置导入失败`)
    }
    
    importDialogVisible.value = false
    await fetchMCPConfigs()
    
  } catch (error) {
    console.error('导入配置失败:', error)
    ElMessage.error('导入配置失败')
  } finally {
    importing.value = false
  }
}

// 日志管理
const clearLogs = () => {
  connectionLogs.value = []
  ElMessage.success('日志已清空')
}

const addLog = (level, message) => {
  connectionLogs.value.unshift({
    id: Date.now(),
    timestamp: new Date(),
    level,
    message
  })
  
  // 保持最新的100条日志
  if (connectionLogs.value.length > 100) {
    connectionLogs.value = connectionLogs.value.slice(0, 100)
  }
}

// 辅助函数
const getIconByType = (type) => {
  switch (type) {
    case 'SSE': return 'Monitor'
    case 'WebSocket': return 'Connection'
    case 'Local': return 'Setting'
    default: return 'Monitor'
  }
}

const viewSchema = (tool) => {
  ElMessage.info('工具参数详情功能开发中...')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '从未连接'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  loading.value = true
  
  try {
    // 并行获取数据
    await Promise.all([
      fetchMCPConfigs(),
      fetchModelProviders(),
      fetchConnectionLogs()
    ])
    
    // 自动连接启用了自动连接的MCP
    const autoConnectConfigs = mcpList.value.filter(mcp => 
      mcp.autoConnect && mcp.status === 'inactive'
    )
    
    for (const mcp of autoConnectConfigs) {
      setTimeout(() => testConnection(mcp), 1000)
    }
    
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('页面初始化失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.model-config-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #cccccc;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  border-bottom: 1px solid #3c3c3c;
  background: #252526;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #cccccc;
  margin: 0 0 4px 0;
}

.page-description {
  color: #9d9d9d;
  margin: 0;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计信息 */
.stats-section {
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.stat-card {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
  padding: 16px 20px;
  text-align: center;
  min-width: 120px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #007acc;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #9d9d9d;
}

/* 配置选项卡 */
.config-tabs {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

/* 操作栏 */
.operation-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  align-items: center;
}

.search-box {
  flex: 1;
  max-width: 300px;
}

.filter-box {
  min-width: 150px;
}

/* MCP列表 */
.mcp-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.mcp-item {
  background: #252526;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.mcp-item:hover {
  border-color: #007acc;
  box-shadow: 0 2px 8px rgba(0, 122, 204, 0.1);
}

.mcp-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.mcp-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(0, 122, 204, 0.1);
  color: #007acc;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.mcp-info {
  flex: 1;
  min-width: 0;
}

.mcp-name {
  font-size: 16px;
  font-weight: 600;
  color: #cccccc;
  margin-bottom: 4px;
}

.mcp-description {
  font-size: 14px;
  color: #9d9d9d;
}

.mcp-status {
  flex: 0 0 auto;
}

.mcp-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mcp-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #3c3c3c;
}

.detail-row {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.detail-row .label {
  color: #9d9d9d;
  margin-right: 8px;
  min-width: 80px;
}

.detail-row .value {
  color: #cccccc;
  word-break: break-all;
}

/* 工具展示 */
.tools-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #3c3c3c;
}

.tools-title {
  color: #cccccc;
  font-size: 14px;
  margin: 0 0 12px 0;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.tool-item {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  padding: 12px;
}

.tool-name {
  font-weight: 500;
  color: #007acc;
  margin-bottom: 4px;
  font-size: 13px;
}

.tool-desc {
  color: #9d9d9d;
  font-size: 12px;
  line-height: 1.4;
}

/* 日志部分 */
.logs-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-header h3 {
  color: #cccccc;
  margin: 0;
}

.logs-list {
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  padding: 16px;
  overflow-y: auto;
  max-height: 400px;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #3c3c3c;
  font-size: 13px;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #9d9d9d;
  min-width: 140px;
  font-family: monospace;
}

.log-level {
  min-width: 60px;
  font-weight: bold;
  text-transform: uppercase;
}

.log-level.info {
  color: #007acc;
}

.log-level.warning {
  color: #ffa500;
}

.log-level.error {
  color: #f56565;
}

.log-message {
  flex: 1;
  color: #cccccc;
}

/* 对话框样式 */
.full-width {
  width: 100%;
}

.tools-detail {
  color: #cccccc;
}

.tools-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tools-header h3 {
  margin: 0;
  color: #cccccc;
}

.no-tools {
  text-align: center;
  padding: 40px;
}

.import-section {
  text-align: center;
  padding: 20px;
}

.import-preview {
  margin-top: 20px;
  text-align: left;
}

.import-preview h4 {
  color: #cccccc;
  margin-bottom: 12px;
}

.preview-list {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.preview-item {
  padding: 6px 0;
  color: #cccccc;
  font-size: 13px;
  border-bottom: 1px solid #3c3c3c;
}

.preview-item:last-child {
  border-bottom: none;
}

/* Element Plus 深色主题覆盖 */
:deep(.el-input__wrapper) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  box-shadow: none;
}

:deep(.el-input__wrapper:hover) {
  border-color: #007acc;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #007acc;
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
}

:deep(.el-input__inner) {
  color: #cccccc;
}

:deep(.el-select .el-input) {
  background: #1e1e1e;
}

:deep(.el-select-dropdown) {
  background: #252526;
  border: 1px solid #3c3c3c;
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  color: #cccccc;
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background: #007acc;
}

:deep(.el-textarea__inner) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  color: #cccccc;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background: #007acc;
}

:deep(.el-input-number .el-input__wrapper) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
}

:deep(.el-table) {
  background: #1e1e1e;
  color: #cccccc;
}

:deep(.el-table th) {
  background: #252526;
  color: #cccccc;
  border-bottom: 1px solid #3c3c3c;
}

:deep(.el-table td) {
  border-bottom: 1px solid #3c3c3c;
}

:deep(.el-table tr:hover > td) {
  background: #2d2d30;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .stats-section {
    flex-wrap: wrap;
  }
  
  .operation-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .mcp-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .mcp-actions {
    justify-content: flex-start;
  }
  
  .mcp-details {
    grid-template-columns: 1fr;
  }
  
  .tools-grid {
    grid-template-columns: 1fr;
  }
}
</style> 