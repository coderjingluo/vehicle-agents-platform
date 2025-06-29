<template>
  <div class="home-page">
    <AppLayout>
      <div class="home-content">
        <div class="welcome-section">
          <h1>天工超级智能体<span class="accent">✨</span></h1>
          <h2>车联网安全综合智能体平台</h2>
          
          <div class="agent-input-area">
            <div class="mode-tabs">
              <div class="tab" :class="{ active: activeMode === 'tara' }" @click="activeMode = 'tara'">
                <span class="tab-icon">🛡️</span>
                <span>TARA智能体</span>
              </div>
              <div class="tab" :class="{ active: activeMode === 'test' }" @click="activeMode = 'test'">
                <span class="tab-icon">📝</span>
                <span>测试用例智能体</span>
              </div>
            </div>
            
            <div class="prompt-input">
              <el-input 
                v-model="userInput" 
                type="textarea" 
                :rows="3" 
                placeholder="请输入需求描述，或上传文件，让智能体为您进行车联网安全分析" 
              />
            </div>
            
            <div class="action-buttons">
              <div class="scenario-selector">
                <el-button @click="showMcpToolConfig" type="text" class="mcp-tool-button">
                  <div class="dropdown-label">
                    <el-icon><Setting /></el-icon>
                    <span>MCP工具</span>
                    <!-- <el-icon class="el-icon--right"><ArrowDown /></el-icon> -->
                  </div>
                </el-button>
              </div>
              
              <div class="network-button">
                <el-button type="primary" plain>
                  <el-icon><Connection /></el-icon>
                  <span>联网</span>
                </el-button>
              </div>
              
              <div class="submit-button">
                <el-button type="primary" circle @click="startChat" :disabled="!userInput">
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="agents-showcase">
          <h3>— 车联网安全测试案例 —</h3>
          
          <div class="showcase-cards">
            <div class="showcase-card" v-for="(card, index) in showcaseCards" :key="index" @click="selectTemplate(card)">
              <div class="card-content">
                <h4>{{ card.title }}</h4>
                <p>{{ card.description }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="agent-types">
          <div class="agent-type-card special" @click="selectAgentType('tara')">
            <div class="type-icon">🛡️</div>
            <div class="type-name">TARA智能体</div>
          </div>
          <div class="agent-type-card special" @click="selectAgentType('test_case')">
            <div class="type-icon">📝</div>
            <div class="type-name">测试用例智能体</div>
          </div>
          <div class="agent-type-card special" @click="selectAgentType('automation')">
            <div class="type-icon">⚙️</div>
            <div class="type-name">自动化测试智能体</div>
          </div>
          <div class="agent-type-card special" @click="selectAgentType('report')">
            <div class="type-icon">📊</div>
            <div class="type-name">报告分析智能体</div>
          </div>
          <div class="agent-type-card" @click="selectAgentType('knowledge')">
            <div class="type-icon">📚</div>
            <div class="type-name">知识库智能体</div>
          </div>
        </div>
      </div>
    </AppLayout>
    
    <!-- Tool Modal Dialog -->
    <el-dialog
      v-model="showToolModal"
      title="Tools Configuration"
      width="80%"
      class="tool-dialog"
      :show-close="true"
    >
      <div class="tool-config-content">
        <div class="tool-config-header">
          <div class="model-section">
            <div class="section-label">Model</div>
            <div class="model-dropdown">
              <span>deepseak-chat</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
          </div>
          <div class="selected-tools-section">
            <div class="section-label">Selected Tools</div>
            <div class="selected-tools-list">
              <div v-for="tool in selectedTools" :key="tool" class="tool-tag">
                {{ tool }} <el-icon @click="toggleToolSelection(tool)"><Close /></el-icon>
              </div>
            </div>
          </div>
        </div>
        
        <div class="tools-grid">
          <div class="tool-card">
            <div class="tool-card-header">
              <span>file_operator</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('file_operator')" 
                  :class="{ 'selected': selectedTools.includes('file_operator') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              A tool for performing file operations. Provides functionality for reading, writing, and checking file contents.
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>str_replace_editor</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('str_replace_editor')" 
                  :class="{ 'selected': selectedTools.includes('str_replace_editor') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              Custom editing tool for viewing, creating and editing files * State is persistent across command calls and sessions.
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>code_audit_v2</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('code_audit_v2')" 
                  :class="{ 'selected': selectedTools.includes('code_audit_v2') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              Advanced code auditing tool for ANALYSIS ONLY - scans code for security vulnerabilities and quality issues.
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>planning</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('planning')" 
                  :class="{ 'selected': selectedTools.includes('planning') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              A planning tool that allows the agent to create and manage plans for solving complex tasks. The tool...
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>create_chat_completion</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('create_chat_completion')" 
                  :class="{ 'selected': selectedTools.includes('create_chat_completion') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              Creates a structured completion with specified output formatting.
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>knowledge_manager</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('knowledge_manager')" 
                  :class="{ 'selected': selectedTools.includes('knowledge_manager') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              Manage knowledge base documents - add, delete, list documents and create knowledge bases
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>rag_query</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('rag_query')" 
                  :class="{ 'selected': selectedTools.includes('rag_query') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              Query knowledge base for relevant information using RAG (Retrieval-Augmented Generation)
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>mcp_1749814525997</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('mcp_1749814525997')" 
                  :class="{ 'selected': selectedTools.includes('mcp_1749814525997') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              MCP工具组: idapro (23个工具)
            </div>
          </div>
          
          <div class="tool-card">
            <div class="tool-card-header">
              <span>mcp_1749948061732</span>
              <div class="tool-card-actions">
                <el-icon><InfoFilled /></el-icon>
                <el-icon 
                  @click="toggleToolSelection('mcp_1749948061732')" 
                  :class="{ 'selected': selectedTools.includes('mcp_1749948061732') }"
                ><Check /></el-icon>
              </div>
            </div>
            <div class="tool-card-description">
              MCP工具组: test-wincli (9个工具)
            </div>
          </div>
        </div>
        
        <div class="tool-market-section">
          <div class="market-info">
            <div class="section-label">Tool Market</div>
            <div class="market-description">Discover and install new tools from our marketplace</div>
          </div>
          <div class="market-action">
            <el-button>Browse Market</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Setting, Connection, ArrowDown, ArrowRight, Check, InfoFilled, Close } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import AppLayout from '@/components/Layout/AppLayout.vue';
import { useUserStore } from '@/stores';

const router = useRouter();
const userStore = useUserStore();
const userInput = ref('');
const activeMode = ref('tara');
const showToolModal = ref(false);

// Tool configuration
const selectedTools = ref([
  'bash', 
  'file_operator', 
  'create_chat_completion', 
  'knowledge_manager', 
  'rag_query', 
  'code_audit_v2', 
  'planning', 
  'browser_use', 
  'deep_research', 
  'web_search', 
  'str_replace_editor'
]);

const showcaseCards = [
  {
    title: '车联网TARA威胁分析与风险评估',
    description: '基于ISO 21434标准对车联网系统进行威胁分析与风险评估',
    template: 'tara-analysis'
  },
  {
    title: '车载软件测试用例自动生成',
    description: '基于TARA分析结果自动生成车载软件安全测试用例',
    template: 'test-case-generation'
  },
  {
    title: '车联网安全自动化测试执行',
    description: '针对车联网系统的自动化安全测试执行与结果分析',
    template: 'automated-testing'
  }
];

const selectTemplate = (card) => {
  userInput.value = `请帮我进行"${card.title}"，${card.description}`;
};

const selectAgentType = (type) => {
  if (type === 'tara') {
    activeMode.value = 'tara';
  } else {
    router.push(`/chat/${type}`);
  }
};

const startChat = () => {
  if (activeMode.value === 'tara') {
    router.push({
      path: '/chat/tara',
      query: { prompt: userInput.value }
    });
  } else if (activeMode.value === 'test') {
    router.push({
      path: '/chat/test_case',
      query: { prompt: userInput.value }
    });
  }
};

const showMcpToolConfig = () => {
  // Show the MCP tool configuration dialog
  showToolModal.value = true;
  console.log('Showing MCP tool configuration dialog');
};

const toggleToolSelection = (toolName) => {
  const index = selectedTools.value.indexOf(toolName);
  if (index > -1) {
    // Tool is already selected, remove it
    selectedTools.value.splice(index, 1);
    ElMessage({
      message: `${toolName} 工具已取消选中`,
      type: 'info',
    });
  } else {
    // Tool is not selected, add it
    selectedTools.value.push(toolName);
    ElMessage({
      message: `${toolName} 工具已选中`,
      type: 'success',
    });
  }
};
</script>

<style scoped>
.home-page {
  height: 100%;
}

.home-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 60px;
  width: 100%;
}

h1 {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 10px;
}

h2 {
  font-size: 24px;
  font-weight: 400;
  margin-bottom: 40px;
  color: #aaa;
}

.accent {
  color: #4080ff;
}

.agent-input-area {
  background-color: #1d1e22;
  border-radius: 10px;
  padding: 20px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mode-tabs {
  display: flex;
  margin-bottom: 15px;
}

.tab {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  margin-right: 10px;
  transition: background-color 0.2s;
  font-weight: 500;
}

.tab.active {
  background-color: rgba(64, 128, 255, 0.1);
  color: #4080ff;
}

.tab-icon {
  margin-right: 8px;
  font-size: 18px;
}

.prompt-input {
  margin-bottom: 15px;
}

.prompt-input :deep(.el-textarea__inner) {
  background-color: #2c2c2c;
  border-color: #3e3e3e;
  color: #fff;
  border-radius: 8px;
  padding: 12px;
  resize: none;
}

.prompt-input :deep(.el-textarea__inner:focus) {
  border-color: #4080ff;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #aaa;
}

.dropdown-label .el-icon {
  margin-right: 5px;
}

.mcp-tool-button {
  padding: 8px 12px;
  border-radius: 4px;
}

.mcp-tool-button:hover {
  background-color: rgba(64, 128, 255, 0.1);
}

.mcp-tool-button:hover .dropdown-label {
  color: #4080ff;
}

.submit-button {
  margin-left: auto;
}

.submit-button :deep(.el-button) {
  background-color: #4080ff;
  border-color: #4080ff;
  padding: 12px;
}

.submit-button :deep(.el-button:hover) {
  background-color: #3a75e6;
  border-color: #3a75e6;
}

.submit-button :deep(.el-button:disabled) {
  background-color: #2c2c2c;
  border-color: #2c2c2c;
  color: #666;
}

.network-button :deep(.el-button) {
  border-color: #4080ff;
  color: #4080ff;
  background-color: transparent;
}

.network-button :deep(.el-button:hover) {
  background-color: rgba(64, 128, 255, 0.1);
  border-color: #4080ff;
  color: #4080ff;
}

.agents-showcase {
  width: 100%;
  margin-bottom: 60px;
}

h3 {
  text-align: center;
  font-weight: 400;
  color: #aaa;
  margin-bottom: 30px;
  position: relative;
}

h3::before, h3::after {
  content: "";
  position: absolute;
  top: 50%;
  height: 1px;
  width: 100px;
  background-color: #3e3e3e;
}

h3::before {
  right: calc(50% + 120px);
}

h3::after {
  left: calc(50% + 120px);
}

.showcase-cards {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.showcase-card {
  width: 30%;
  min-width: 280px;
  background-color: #1d1e22;
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.showcase-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.showcase-card h4 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #fff;
}

.showcase-card p {
  font-size: 14px;
  color: #aaa;
  line-height: 1.5;
}

.agent-types {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
  width: 100%;
}

.agent-type-card {
  width: 120px;
  height: 120px;
  background-color: #1d1e22;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.agent-type-card.special {
  background-color: #242529;
}

.agent-type-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.type-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.type-name {
  font-size: 14px;
  color: #aaa;
}

/* Add styles for the tool dialog */
.tool-dialog :deep(.el-dialog__body) {
  padding: 0;
  margin-top: 20px;
}

.tool-config-content {
  padding: 15px;
  background-color: #1a1a1e;
  border-radius: 4px;
  max-height: 70vh;
  overflow-y: auto;
}

.tool-config-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  color: #fff;
}

.model-section {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.section-label {
  font-weight: 500;
  margin-right: 10px;
  color: #d4d4d4;
}

.model-dropdown {
  display: flex;
  align-items: center;
  background-color: #2c2c2c;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.model-dropdown span {
  margin-right: 10px;
}

.selected-tools-section {
  margin-bottom: 15px;
}

.selected-tools-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  max-width: 100%;
  overflow-x: auto;
  padding-bottom: 5px;
}

.tool-tag {
  background-color: #2c2c2c;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.tool-tag .el-icon {
  margin-left: 5px;
  font-size: 12px;
  cursor: pointer;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.tool-card {
  background-color: #2c2c2c;
  padding: 15px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.tool-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 500;
  color: #d4d4d4;
}

.tool-card-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-card-actions .el-icon {
  cursor: pointer;
  font-size: 16px;
}

.tool-card-actions .el-icon.selected {
  color: #4080ff;
}

.tool-card-description {
  font-size: 13px;
  color: #aaa;
  line-height: 1.4;
}

.tool-market-section {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #2c2c2c;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.market-info {
  display: flex;
  flex-direction: column;
}

.market-description {
  color: #aaa;
  font-size: 13px;
  margin-top: 5px;
}

.market-action {
  display: flex;
  justify-content: flex-end;
}

.tool-market-section .market-action :deep(.el-button) {
  background-color: #4080ff;
  border-color: #4080ff;
  color: #fff;
}

.tool-market-section .market-action :deep(.el-button:hover) {
  background-color: #3a75e6;
  border-color: #3a75e6;
}
</style> 