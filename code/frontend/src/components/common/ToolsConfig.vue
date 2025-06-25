<template>
  <div class="tools-config">
    <div class="config-section">
      <h4 class="section-title">Model</h4>
      <el-select v-model="selectedModel" placeholder="选择模型" class="full-width">
        <el-option label="deepseek-chat" value="deepseek-chat" />
        <el-option label="anthropic/claude-3.7-sonnet" value="anthropic/claude-3.7-sonnet" />
        <el-option label="gpt-4o" value="gpt-4o" />
        <el-option label="claude-3-sonnet" value="claude-3-sonnet" />
      </el-select>
    </div>

    <div class="config-section">
      <h4 class="section-title">Selected Tools</h4>
      <div class="selected-tools-display">
        <div v-for="tool in selectedTools" :key="tool.id" class="selected-tool-item">
          <div class="tool-info">
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-description">{{ tool.description }}</div>
          </div>
          <el-button text size="small" @click="removeTool(tool.id)" class="remove-btn">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <div class="config-section">
      <h4 class="section-title">Available Tools</h4>
      <div class="tools-grid">
        <div 
          v-for="tool in availableTools" 
          :key="tool.id" 
          class="tool-card"
          :class="{ selected: isToolSelected(tool.id) }"
          @click="toggleTool(tool)"
        >
          <div class="tool-header">
            <div class="tool-icon">
              <el-icon><component :is="tool.icon" /></el-icon>
            </div>
            <div class="tool-content">
              <div class="tool-name">{{ tool.name }}</div>
              <div class="tool-description">{{ tool.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tool Market Section -->
    <div class="config-section">
      <div class="tool-market">
        <div class="market-item">
          <div class="market-info">
            <div class="market-name">mcp_17491452597</div>
            <div class="market-description">MCP工具项: idapro (23个工具)</div>
          </div>
          <div class="market-actions">
            <el-button text type="primary">Browse Market</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="config-footer">
      <h5 class="market-title">Tool Market</h5>
      <p class="market-subtitle">Discover and install new tools from our marketplace</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Close, Check, Setting, Search, DocumentCopy, Cpu } from '@element-plus/icons-vue'

// 事件定义
const emit = defineEmits(['apply', 'close'])

// 响应式数据
const selectedModel = ref('deepseek-chat')
const selectedTools = ref([
  { id: 'bash', name: 'bash', description: 'Execute command line operations' },
  { id: 'file_operator', name: 'file_operator', description: 'A tool for performing file operations' }
])

const availableTools = ref([
  { id: 'knowledge_manager', name: 'knowledge_manager', description: 'Manage knowledge base documents - add, delete, list documents and create knowledge bases', icon: 'Search' },
  { id: 'code_audit_v2', name: 'code_audit_v2', description: 'Advanced code auditing tool for ANALYSIS ONLY - scans code for security vulnerabilities', icon: 'DocumentCopy' },
  { id: 'planning', name: 'planning', description: 'A planning tool that allows the agent to create and manage plans for complex workflow', icon: 'Setting' },
  { id: 'web_search', name: 'web_search', description: 'Search the web for information', icon: 'Search' },
  { id: 'create_chat_completion', name: 'create_chat_completion', description: 'Create a structured completion with specified output formatting', icon: 'DocumentCopy' },
  { id: 'rag_query', name: 'rag_query', description: 'Query knowledge base for relevant information using RAG (Retrieval-Augmented Generation)', icon: 'Search' },
  { id: 'browser_use', name: 'browser_use', description: 'Browser automation tool', icon: 'Search' },
  { id: 'deep_research', name: 'deep_research', description: 'Perform deep research on topics', icon: 'Search' },
  { id: 'str_replace_editor', name: 'str_replace_editor', description: 'String replacement editor', icon: 'Search' }
])

// 计算属性
const isToolSelected = computed(() => (toolId) => {
  return selectedTools.value.some(t => t.id === toolId)
})

// 方法
const toggleTool = (tool) => {
  const index = selectedTools.value.findIndex(t => t.id === tool.id)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  } else {
    selectedTools.value.push({
      id: tool.id,
      name: tool.name,
      description: tool.description
    })
  }
}

const removeTool = (toolId) => {
  const index = selectedTools.value.findIndex(t => t.id === toolId)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  }
}

const applyConfig = () => {
  emit('apply', {
    model: selectedModel.value,
    tools: selectedTools.value
  })
  emit('close')
}
</script>

<style scoped>
.tools-config {
  padding: 0;
  color: #cccccc;
}

.config-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
  margin: 0 0 12px 0;
  text-align: center;
}

.full-width {
  width: 100%;
}

/* Selected Tools Display */
.selected-tools-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.selected-tool-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
}

.selected-tool-item .tool-info {
  flex: 1;
  text-align: center;
}

.selected-tool-item .tool-name {
  font-size: 16px;
  font-weight: 600;
  color: #cccccc;
  margin-bottom: 4px;
}

.selected-tool-item .tool-description {
  font-size: 12px;
  color: #9d9d9d;
}

.remove-btn {
  color: #9d9d9d;
  padding: 4px;
}

.remove-btn:hover {
  color: #cccccc;
  background: rgba(255, 255, 255, 0.1);
}

/* Available Tools Grid */
.tools-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.tool-card {
  display: block;
  padding: 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-card:hover {
  background: #2d2d30;
  border-color: #007acc;
}

.tool-card.selected {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.tool-icon {
  width: 32px;
  height: 32px;
  background: #007acc;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
}

.tool-content {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 4px;
  font-size: 14px;
}

.tool-description {
  color: #9d9d9d;
  font-size: 12px;
  line-height: 1.4;
}

/* Tool Market */
.tool-market {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.market-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  font-size: 13px;
}

.market-info {
  flex: 1;
  min-width: 0;
}

.market-name {
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 2px;
}

.market-description {
  color: #9d9d9d;
  font-size: 12px;
}

.market-actions {
  margin-left: 8px;
}

.config-footer {
  text-align: center;
  padding: 12px 0;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
}

.market-title {
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
  margin: 0 0 8px 0;
}

.market-subtitle {
  color: #9d9d9d;
  font-size: 12px;
  margin: 0;
}

/* Element Plus 样式覆盖 */
:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  box-shadow: none;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #007acc;
}

:deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #007acc;
  box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
}

:deep(.el-select .el-input__inner) {
  color: #cccccc;
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

:deep(.el-scrollbar) {
  height: 100%;
}

:deep(.el-scrollbar__thumb) {
  background: #464647;
}

:deep(.el-scrollbar__thumb:hover) {
  background: #6c6c6c;
}
</style> 