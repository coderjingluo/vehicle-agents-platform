<template>
  <div class="models-config">
    <!-- 左侧标签栏 -->
    <div class="config-sidebar">
      <div class="sidebar-tabs">
        <div 
          class="tab-item"
          :class="{ active: activeTab === 'models' }"
          @click="activeTab = 'models'"
        >
          Models
        </div>
        <div 
          class="tab-item"
          :class="{ active: activeTab === 'preferences' }"
          @click="activeTab = 'preferences'"
        >
          Preferences
        </div>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="config-content">
      <!-- Models 标签页 -->
      <div v-if="activeTab === 'models'" class="models-panel">
        <div class="panel-header">
          <h3 class="panel-title">Models</h3>
          <p class="panel-subtitle">Configure your models</p>
          <el-button type="primary" @click="showAddModelDialog" class="add-model-btn">
            <el-icon><Plus /></el-icon>
            Add New Model
          </el-button>
        </div>

        <div class="models-list">
          <div v-for="model in modelsList" :key="model.id" class="model-item">
            <div class="model-info">
              <div class="model-name">{{ model.name }}</div>
              <div class="model-url">{{ model.url }}</div>
            </div>
            <div class="model-actions">
              <el-button text size="small" @click="editModel(model)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button text size="small" type="danger" @click="deleteModel(model.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Preferences 标签页 -->
      <div v-if="activeTab === 'preferences'" class="preferences-panel">
        <div class="panel-header">
          <h3 class="panel-title">Preferences</h3>
          <p class="panel-subtitle">Configure your preferences</p>
        </div>

        <div class="preferences-form">
          <el-form :model="preferencesForm" label-width="120px">
            <el-form-item label="Default Model">
              <el-select v-model="preferencesForm.defaultModel" placeholder="选择默认模型" class="full-width">
                <el-option 
                  v-for="model in modelsList" 
                  :key="model.id" 
                  :label="model.name" 
                  :value="model.id" 
                />
              </el-select>
            </el-form-item>

            <el-form-item label="Temperature">
              <el-slider 
                v-model="preferencesForm.temperature" 
                :min="0" 
                :max="2" 
                :step="0.1" 
                show-input 
                class="full-width"
              />
            </el-form-item>

            <el-form-item label="Max Tokens">
              <el-input-number 
                v-model="preferencesForm.maxTokens" 
                :min="1" 
                :max="8000" 
                :step="100"
                class="full-width"
              />
            </el-form-item>

            <el-form-item label="Auto Save">
              <el-switch v-model="preferencesForm.autoSave" />
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 添加模型对话框 -->
    <el-dialog
      v-model="addModelDialogVisible"
      title="Add New Model"
      width="400px"
      class="add-model-dialog"
    >
      <el-form ref="modelForm" :model="newModelForm" :rules="modelRules" label-width="80px">
        <el-form-item label="Name" prop="name">
          <el-input v-model="newModelForm.name" placeholder="Model name" />
        </el-form-item>

        <el-form-item label="URL" prop="url">
          <el-input v-model="newModelForm.url" placeholder="https://api.example.com/v1" />
        </el-form-item>

        <el-form-item label="API Key" prop="apiKey">
          <el-input v-model="newModelForm.apiKey" type="password" placeholder="API Key" show-password />
        </el-form-item>

        <el-form-item label="Provider" prop="provider">
          <el-select v-model="newModelForm.provider" placeholder="Select provider" class="full-width">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Custom" value="custom" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addModelDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="submitNewModel">Add Model</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

// 事件定义
const emit = defineEmits(['apply', 'close'])

// 响应式数据
const activeTab = ref('models')
const addModelDialogVisible = ref(false)
const modelForm = ref(null)

// 模型列表
const modelsList = ref([
  {
    id: 'deepseek-chat',
    name: 'deepseek-chat',
    url: 'https://api.deepseek.com/v1',
    provider: 'deepseek',
    apiKey: '***'
  },
  {
    id: 'anthropic-claude',
    name: 'anthropic/claude-3.7-sonnet',
    url: 'https://api.anthropic.com/v1',
    provider: 'anthropic',
    apiKey: '***'
  }
])

// 偏好设置表单
const preferencesForm = reactive({
  defaultModel: 'deepseek-chat',
  temperature: 0.7,
  maxTokens: 2000,
  autoSave: true
})

// 新模型表单
const newModelForm = reactive({
  name: '',
  url: '',
  apiKey: '',
  provider: ''
})

// 表单验证规则
const modelRules = {
  name: [
    { required: true, message: 'Please input model name', trigger: 'blur' }
  ],
  url: [
    { required: true, message: 'Please input API URL', trigger: 'blur' },
    { type: 'url', message: 'Please input valid URL', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: 'Please select provider', trigger: 'change' }
  ]
}

// 方法
const showAddModelDialog = () => {
  addModelDialogVisible.value = true
  // 重置表单
  Object.assign(newModelForm, {
    name: '',
    url: '',
    apiKey: '',
    provider: ''
  })
}

const editModel = (model) => {
  // 编辑模型逻辑
  Object.assign(newModelForm, model)
  addModelDialogVisible.value = true
}

const deleteModel = (modelId) => {
  const index = modelsList.value.findIndex(m => m.id === modelId)
  if (index > -1) {
    modelsList.value.splice(index, 1)
    ElMessage.success('Model deleted successfully')
  }
}

const submitNewModel = async () => {
  if (!modelForm.value) return
  
  try {
    await modelForm.value.validate()
    
    // 添加新模型
    const newModel = {
      id: newModelForm.name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      name: newModelForm.name,
      url: newModelForm.url,
      provider: newModelForm.provider,
      apiKey: newModelForm.apiKey ? '***' : ''
    }
    
    modelsList.value.push(newModel)
    addModelDialogVisible.value = false
    ElMessage.success('Model added successfully')
    
  } catch (error) {
    console.error('Form validation failed:', error)
  }
}

const applyConfig = () => {
  emit('apply', {
    models: modelsList.value,
    preferences: preferencesForm
  })
  emit('close')
}
</script>

<style scoped>
.models-config {
  display: flex;
  height: 100%;
  min-height: 400px;
  background: #252526;
  color: #cccccc;
}

/* 左侧标签栏 */
.config-sidebar {
  width: 150px;
  background: #1e1e1e;
  border-right: 1px solid #3c3c3c;
}

.sidebar-tabs {
  display: flex;
  flex-direction: column;
}

.tab-item {
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #9d9d9d;
  border-bottom: 1px solid #3c3c3c;
  transition: all 0.2s ease;
}

.tab-item:hover {
  background: #2d2d30;
  color: #cccccc;
}

.tab-item.active {
  background: #007acc;
  color: #ffffff;
}

/* 右侧内容区域 */
.config-content {
  flex: 1;
  padding: 20px;
}

.panel-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #cccccc;
  margin: 0 0 4px 0;
}

.panel-subtitle {
  font-size: 14px;
  color: #9d9d9d;
  margin: 0;
}

.add-model-btn {
  margin-left: auto;
}

/* 模型列表 */
.models-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 8px;
}

.model-info {
  flex: 1;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 4px;
}

.model-url {
  font-size: 12px;
  color: #9d9d9d;
  font-family: 'SF Mono', Monaco, 'Consolas', monospace;
}

.model-actions {
  display: flex;
  gap: 8px;
}

/* 偏好设置 */
.preferences-form {
  max-width: 400px;
}

.full-width {
  width: 100%;
}

/* Element Plus 样式覆盖 */
:deep(.el-form-item__label) {
  color: #cccccc;
}

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

:deep(.el-slider__runway) {
  background: #3c3c3c;
}

:deep(.el-slider__bar) {
  background: #007acc;
}

:deep(.el-slider__button) {
  border-color: #007acc;
}

:deep(.el-input-number .el-input__wrapper) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background: #007acc;
}

/* 添加模型对话框 */
:deep(.add-model-dialog) {
  background: #252526;
  border: 1px solid #3c3c3c;
}

:deep(.add-model-dialog .el-dialog__header) {
  background: #2c2c2c;
  border-bottom: 1px solid #3c3c3c;
}

:deep(.add-model-dialog .el-dialog__title) {
  color: #cccccc;
}

:deep(.add-model-dialog .el-dialog__body) {
  background: #252526;
}
</style> 