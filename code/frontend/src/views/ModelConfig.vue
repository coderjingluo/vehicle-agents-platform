<template>
  <div class="model-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">MCP工具管理</h1>
        <p class="page-description">管理模型调用协议(Model Context Protocol) 工具配置</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showAddMCPDialog">
          <el-icon><Plus /></el-icon>
          添加MCP
        </el-button>
      </div>
    </div>

    <!-- 配置选项卡 -->
    <div class="config-tabs">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="配置列表" name="list">
          <!-- MCP工具列表 -->
          <div class="mcp-list">
            <div v-for="mcp in mcpList" :key="mcp.id" class="mcp-item">
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
                  <el-button text @click="editMCP(mcp)">
                    <el-icon><Edit /></el-icon>
                    编辑
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
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="添加配置" name="add">
          <!-- 添加MCP配置表单 -->
          <div class="add-mcp-form">
            <h3 class="form-title">添加MCP配置</h3>
            <p class="form-description">配置新的MCP服务器连接</p>

            <el-form ref="mcpForm" :model="newMCPForm" :rules="mcpRules" label-width="120px">
              <el-form-item label="名称" prop="name">
                <el-input v-model="newMCPForm.name" placeholder="输入MCP服务器名称" />
              </el-form-item>

              <el-form-item label="描述" prop="description">
                <el-input 
                  v-model="newMCPForm.description" 
                  type="textarea" 
                  :rows="3"
                  placeholder="描述MCP服务器的功能和用途"
                />
              </el-form-item>

              <el-form-item label="连接类型" prop="type">
                <el-select v-model="newMCPForm.type" placeholder="选择连接类型" class="full-width">
                  <el-option label="SSE (HTTP)" value="SSE" />
                  <el-option label="WebSocket" value="WebSocket" />
                  <el-option label="Local Process" value="Local" />
                </el-select>
              </el-form-item>

              <el-form-item label="服务器URL" prop="url">
                <el-input 
                  v-model="newMCPForm.url" 
                  placeholder="http://localhost:3001/mcp"
                />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="submitMCPForm">添加配置</el-button>
                <el-button @click="resetForm">取消</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加MCP对话框 -->
    <el-dialog v-model="addMCPDialogVisible" title="添加MCP配置" width="500px">
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
      </el-form>

      <template #footer>
        <el-button @click="addMCPDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDialogForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, Setting, Monitor } from '@element-plus/icons-vue'

// 响应式数据
const activeTab = ref('list')
const addMCPDialogVisible = ref(false)

// 表单引用
const mcpForm = ref(null)
const dialogMcpForm = ref(null)

// MCP列表数据
const mcpList = ref([
  {
    id: 'test1',
    name: 'test1',
    description: 'A test',
    type: 'SSE',
    url: 'http://127.0.0.1:8744/sse',
    status: 'inactive',
    lastConnected: '2025-06-17T13:22:16.822258',
    toolCount: 0,
    icon: 'Monitor'
  },
  {
    id: 'idapro',
    name: 'idapro',
    description: '本地idapro@mcp',
    type: 'SSE',
    url: 'http://127.0.0.1:8744/sse',
    status: 'active',
    lastConnected: '2025-06-17T13:22:16.822258',
    toolCount: 23,
    icon: 'Monitor'
  },
  {
    id: 'test-wincli',
    name: 'test-wincli',
    description: 'Test Windows CLI MCP Server',
    type: 'SSE',
    url: 'http://localhost:8081/sse',
    status: 'inactive',
    lastConnected: null,
    toolCount: 9,
    icon: 'Setting'
  }
])

// 表单数据
const newMCPForm = reactive({
  name: '',
  description: '',
  type: 'SSE',
  url: 'http://localhost:3001/mcp'
})

const dialogMCPForm = reactive({
  name: '',
  description: '',
  type: 'SSE',
  url: ''
})

// 表单验证规则
const mcpRules = {
  name: [
    { required: true, message: '请输入MCP名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择连接类型', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入服务器URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 方法
const showAddMCPDialog = () => {
  addMCPDialogVisible.value = true
  resetDialogForm()
}

const editMCP = (mcp) => {
  // 编辑MCP配置
  ElMessage.info('编辑功能开发中...')
}

const deleteMCP = (mcpId) => {
  ElMessage({
    type: 'warning',
    message: '确定要删除这个MCP配置吗？',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    const index = mcpList.value.findIndex(mcp => mcp.id === mcpId)
    if (index > -1) {
      mcpList.value.splice(index, 1)
      ElMessage.success('删除成功')
    }
  }).catch(() => {
    // 取消删除
  })
}

const submitMCPForm = async () => {
  if (!mcpForm.value) return
  
  try {
    await mcpForm.value.validate()
    addMCPConfig(newMCPForm)
    resetForm()
    ElMessage.success('MCP配置添加成功')
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const submitDialogForm = async () => {
  if (!dialogMcpForm.value) return
  
  try {
    await dialogMcpForm.value.validate()
    addMCPConfig(dialogMCPForm)
    addMCPDialogVisible.value = false
    resetDialogForm()
    ElMessage.success('MCP配置添加成功')
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const addMCPConfig = (formData) => {
  const newMCP = {
    id: `mcp_${Date.now()}`,
    name: formData.name,
    description: formData.description,
    type: formData.type,
    url: formData.url,
    status: 'inactive',
    lastConnected: null,
    toolCount: 0,
    icon: 'Monitor'
  }
  mcpList.value.push(newMCP)
}

const resetForm = () => {
  Object.assign(newMCPForm, {
    name: '',
    description: '',
    type: 'SSE',
    url: 'http://localhost:3001/mcp'
  })
  if (mcpForm.value) {
    mcpForm.value.resetFields()
  }
}

const resetDialogForm = () => {
  Object.assign(dialogMCPForm, {
    name: '',
    description: '',
    type: 'SSE',
    url: ''
  })
  if (dialogMcpForm.value) {
    dialogMcpForm.value.resetFields()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '从未连接'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.model-config-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 4px 0;
}

.page-description {
  color: var(--el-text-color-secondary);
  margin: 0;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 配置选项卡 */
.config-tabs {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

.config-tabs .el-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* MCP列表 */
.mcp-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mcp-item {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.mcp-item:hover {
  border-color: var(--el-color-primary-light-7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
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
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.mcp-description {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.mcp-status {
  flex: 0 0 auto;
}

.mcp-actions {
  display: flex;
  gap: 8px;
}

.mcp-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.detail-row {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.detail-row .label {
  color: var(--el-text-color-secondary);
  margin-right: 8px;
  min-width: 80px;
}

.detail-row .value {
  color: var(--el-text-color-primary);
  word-break: break-all;
}

/* 添加表单 */
.add-mcp-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.form-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px 0;
}

.form-description {
  color: var(--el-text-color-secondary);
  margin: 0 0 24px 0;
  font-size: 14px;
}

.full-width {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .mcp-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .mcp-details {
    grid-template-columns: 1fr;
  }
  
  .add-mcp-form {
    margin: 0;
    padding: 16px;
  }
}
</style> 