<template>
  <div class="tools-config">
    <!-- 模型选择 -->
    <div class="config-section">
      <h4 class="section-title">Model</h4>
      <el-select v-model="selectedModel" placeholder="选择模型" class="model-select">
        <el-option label="deepseek-chat" value="deepseek-chat" />
        <el-option label="anthropic/claude-3.7-sonnet" value="anthropic/claude-3.7-sonnet" />
        <el-option label="gpt-4o" value="gpt-4o" />
        <el-option label="claude-3-sonnet" value="claude-3-sonnet" />
      </el-select>
    </div>

    <!-- 已选择的工具 -->
    <div class="config-section">
      <h4 class="section-title">Selected Tools</h4>
      <div class="selected-tools-area">
        <div v-for="tool in selectedTools" :key="tool.id" class="selected-tool-card">
          <div class="tool-icon">
            <el-icon><component :is="getToolIcon(tool.icon || 'Search')" /></el-icon>
          </div>
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

    <!-- 可用工具网格 -->
    <div class="config-section">
      <div class="available-tools-grid">
        <!-- 第一行工具 -->
        <div class="tools-row">
          <div 
            v-for="tool in firstRowTools" 
            :key="tool.id"
            class="tool-grid-item"
            :class="{ 
              active: isToolSelected(tool.id),
              disabled: tool.disabled 
            }"
            @click="!tool.disabled && toggleTool(tool)"
          >
            <div class="grid-tool-icon">
              <el-icon><component :is="getToolIcon(tool.icon)" /></el-icon>
            </div>
            <div class="grid-tool-name">{{ tool.name }}</div>
            <div class="grid-tool-desc">{{ tool.shortDesc }}</div>
            <div v-if="isToolSelected(tool.id)" class="tool-check">
              <el-icon><Check /></el-icon>
            </div>
          </div>
        </div>

        <!-- 第二行工具 -->
        <div class="tools-row">
          <div 
            v-for="tool in secondRowTools" 
            :key="tool.id"
            class="tool-grid-item"
            :class="{ 
              active: isToolSelected(tool.id),
              disabled: tool.disabled 
            }"
            @click="!tool.disabled && toggleTool(tool)"
          >
            <div class="grid-tool-icon">
              <el-icon><component :is="getToolIcon(tool.icon)" /></el-icon>
            </div>
            <div class="grid-tool-name">{{ tool.name }}</div>
            <div class="grid-tool-desc">{{ tool.shortDesc }}</div>
            <div v-if="isToolSelected(tool.id)" class="tool-check">
              <el-icon><Check /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MCP工具区域 -->
    <div class="config-section">
      <div 
        class="mcp-tool-item"
        :class="{ active: isMcpToolSelected }"
        @click="toggleMcpTool"
      >
        <div class="mcp-tool-icon">
          <div class="mcp-icon-bg">
            <span class="mcp-icon-text">Q</span>
          </div>
        </div>
        <div class="mcp-tool-info">
          <div class="mcp-tool-name">mcp_17491452597</div>
          <div class="mcp-tool-desc">MCP工具项: idapro (23个工具)</div>
        </div>
        <div v-if="isMcpToolSelected" class="tool-check">
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>

    <!-- 工具市场 -->
    <div class="config-section">
      <div class="tool-market-card" @click="openToolMarket">
        <div class="market-header">
          <h5 class="market-title">Tool Market</h5>
          <el-button text type="primary" class="browse-btn">Browse Market</el-button>
        </div>
        <p class="market-desc">Discover and install new tools from our marketplace</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Close, Check, Setting, Search, DocumentCopy, Cpu, Document, Monitor, Avatar } from '@element-plus/icons-vue'

// 事件定义
const emit = defineEmits(['apply', 'close'])

// 响应式数据
const selectedModel = ref('deepseek-chat')
const isMcpToolSelected = ref(false)

const selectedTools = ref([
  { 
    id: 'bash', 
    name: 'bash', 
    description: 'A tool for performing file operations. Provides functionality for reading, writing, and executing operations',
    icon: 'Terminal'
  },
  { 
    id: 'file_operator', 
    name: 'file_operator', 
    description: 'A tool for performing file operations. Provides functionality for reading, writing, and executing operations',
    icon: 'FileText'
  },
  { 
    id: 'create_chat_completion', 
    name: 'create_chat_completion', 
    description: 'Creates a structured completion with specified output formatting',
    icon: 'DocumentCopy'
  },
  { 
    id: 'knowledge_manager', 
    name: 'knowledge_manager', 
    description: 'Manage knowledge base documents - add, delete, list documents and create knowledge bases',
    icon: 'Search'
  }
])

// 第一行工具（4个）
const firstRowTools = ref([
  { 
    id: 'str_replace_editor', 
    name: 'str_replace_editor', 
    shortDesc: 'Custom editing tool for viewing, creating and editing',
    description: 'String replacement editor',
    icon: 'DocumentCopy'
  },
  { 
    id: 'code_audit_v2', 
    name: 'code_audit_v2', 
    shortDesc: 'Advanced code auditing tool for ANALYSIS ONLY',
    description: 'Advanced code auditing tool for ANALYSIS ONLY - scans code for security vulnerabilities',
    icon: 'DocumentCopy'
  },
  { 
    id: 'planning', 
    name: 'planning', 
    shortDesc: 'A planning tool that allows the agent to create and',
    description: 'A planning tool that allows the agent to create and manage plans for complex workflow',
    icon: 'Setting'
  },
  { 
    id: 'browser_use', 
    name: 'browser_use', 
    shortDesc: 'Browser automation tool',
    description: 'Browser automation tool',
    icon: 'Monitor'
  }
])

// 第二行工具（4个）
const secondRowTools = ref([
  { 
    id: 'deep_research', 
    name: 'deep_research', 
    shortDesc: 'Perform deep research on topics',
    description: 'Perform deep research on topics',
    icon: 'Search'
  },
  { 
    id: 'web_search', 
    name: 'web_search', 
    shortDesc: 'Search the web for information',
    description: 'Search the web for information',
    icon: 'Search'
  },
  { 
    id: 'rag_query', 
    name: 'rag_query', 
    shortDesc: 'Query knowledge base for relevant information using',
    description: 'Query knowledge base for relevant information using RAG (Retrieval-Augmented Generation)',
    icon: 'Search'
  },
  { 
    id: 'mcp_17498061732', 
    name: 'mcp_17498061732', 
    shortDesc: 'MCP工具项: test-winch (1个工具)',
    description: 'MCP工具项: test-winch (1个工具)',
    icon: 'Cpu',
    disabled: true
  }
])

// 计算属性
const isToolSelected = computed(() => (toolId) => {
  return selectedTools.value.some(t => t.id === toolId)
})

// 方法
const getToolIcon = (iconName) => {
  const iconMap = {
    'Setting': Setting,
    'Search': Search,
    'DocumentCopy': DocumentCopy,
    'Cpu': Cpu,
    'Code': DocumentCopy,
    'Globe': Monitor,
    'FileText': Document,
    'Terminal': Avatar
  }
  return iconMap[iconName] || Search
}

const toggleTool = (tool) => {
  const index = selectedTools.value.findIndex(t => t.id === tool.id)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  } else {
    selectedTools.value.push({
      id: tool.id,
      name: tool.name,
      description: tool.description,
      icon: tool.icon
    })
  }
}

const toggleMcpTool = () => {
  const mcpTool = {
    id: 'mcp_17491452597',
    name: 'mcp_17491452597',
    description: 'MCP工具项: idapro (23个工具)',
    icon: 'Cpu'
  }

  if (isMcpToolSelected.value) {
    const index = selectedTools.value.findIndex(t => t.id === mcpTool.id)
    if (index > -1) {
      selectedTools.value.splice(index, 1)
    }
    isMcpToolSelected.value = false
  } else {
    selectedTools.value.push(mcpTool)
    isMcpToolSelected.value = true
  }
}

const removeTool = (toolId) => {
  const index = selectedTools.value.findIndex(t => t.id === toolId)
  if (index > -1) {
    selectedTools.value.splice(index, 1)
  }
  
  // 如果移除的是MCP工具，更新状态
  if (toolId === 'mcp_17491452597') {
    isMcpToolSelected.value = false
  }
}

const openToolMarket = () => {
  // 打开工具市场逻辑
  console.log('Opening tool market...')
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
  padding: 20px;
  background: #252526;
  color: #cccccc;
  min-height: 500px;
}

.config-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #cccccc;
  margin: 0 0 12px 0;
}

/* 模型选择 */
.model-select {
  width: 100%;
}

/* 已选择的工具 */
.selected-tools-area {
  border: 1px solid #007acc;
  border-radius: 6px;
  padding: 12px;
  min-height: 120px;
  background: rgba(0, 122, 204, 0.05);
}

.selected-tool-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  margin-bottom: 8px;
}

.selected-tool-card:last-child {
  margin-bottom: 0;
}

.selected-tool-card .tool-icon {
  width: 24px;
  height: 24px;
  background: #007acc;
  color: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
}

.selected-tool-card .tool-info {
  flex: 1;
  min-width: 0;
}

.selected-tool-card .tool-name {
  font-size: 13px;
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 2px;
}

.selected-tool-card .tool-description {
  font-size: 11px;
  color: #9d9d9d;
  line-height: 1.3;
}

.remove-btn {
  color: #9d9d9d;
  padding: 2px;
}

.remove-btn:hover {
  color: #cccccc;
}

/* 可用工具网格 */
.available-tools-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tools-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.tool-grid-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 16px 8px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 100px;
}

.tool-grid-item:hover {
  border-color: #007acc;
  background: #2d2d30;
}

.tool-grid-item.active {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.tool-grid-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-grid-item.disabled:hover {
  border-color: #3c3c3c;
  background: #1e1e1e;
}

.grid-tool-icon {
  width: 32px;
  height: 32px;
  background: #007acc;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  font-size: 16px;
}

.grid-tool-name {
  font-size: 12px;
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 4px;
  word-break: break-all;
}

.grid-tool-desc {
  font-size: 10px;
  color: #9d9d9d;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tool-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 16px;
  height: 16px;
  background: #007acc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

/* MCP工具 */
.mcp-tool-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mcp-tool-item:hover {
  border-color: #007acc;
  background: #2d2d30;
}

.mcp-tool-item.active {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.mcp-tool-icon {
  flex-shrink: 0;
}

.mcp-icon-bg {
  width: 32px;
  height: 32px;
  background: #007acc;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mcp-icon-text {
  font-size: 16px;
  font-weight: bold;
}

.mcp-tool-info {
  flex: 1;
  min-width: 0;
}

.mcp-tool-name {
  font-size: 14px;
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 4px;
}

.mcp-tool-desc {
  font-size: 12px;
  color: #9d9d9d;
}

/* 工具市场 */
.tool-market-card {
  padding: 16px;
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-market-card:hover {
  border-color: #007acc;
  background: #2d2d30;
}

.market-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.market-title {
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
  margin: 0;
}

.browse-btn {
  color: #007acc;
  font-size: 12px;
  padding: 4px 8px;
}

.browse-btn:hover {
  background: rgba(0, 122, 204, 0.1);
}

.market-desc {
  font-size: 12px;
  color: #9d9d9d;
  margin: 0;
  line-height: 1.3;
}

/* Element Plus 样式覆盖 */
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
</style> 