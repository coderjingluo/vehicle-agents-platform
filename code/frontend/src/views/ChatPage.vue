<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 头部导航 -->
      <div class="chat-header">
        <div class="back-button" @click="goBack">
          <el-icon><Back /></el-icon>
        </div>
        <div class="chat-title">{{ chatTitle }}</div>
        <div class="header-actions">
          <el-button type="primary" plain circle class="action-button" title="分享">
            <el-icon><Share /></el-icon>
          </el-button>
          <el-badge :value="1" class="notification-badge">
            <el-button type="primary" plain circle class="action-button" title="通知">
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>
          <el-avatar :size="32" :src="userAvatar"></el-avatar>
        </div>
      </div>
      
      <!-- 聊天内容区域 -->
      <div class="chat-body">
        <!-- 左侧聊天记录和输入区 -->
        <div class="chat-left-panel">
          <div class="chat-messages" ref="messageContainer">
            <div v-for="(message, index) in messages" :key="index" 
              :class="['message-container', message.role === 'user' ? 'user-message' : 'agent-message']">
              <div class="message-avatar" v-if="message.role === 'agent-message'">
                <el-avatar :size="36" :src="message.role === 'user' ? userAvatar : agentAvatar"></el-avatar>
              </div>
              <div class="message-content">
                <div class="message-sender">{{ message.role === 'user' ? '您' : '天工' }}</div>
                <div class="message-text" v-html="message.content"></div>
                <div v-if="message.tools && message.tools.length > 0" class="message-tools">
                  <div v-for="(tool, toolIndex) in message.tools" :key="toolIndex" 
                    class="tool-item" @click="showToolDetails(tool)">
                    <el-icon><Document /></el-icon>
                    <span>{{ tool.name }}</span>
                    <el-icon><ArrowRight /></el-icon>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="isAgentTyping" class="message-container agent-message">
              <div class="message-avatar">
                <el-avatar :size="36" :src="agentAvatar"></el-avatar>
              </div>
              <div class="message-content">
                <div class="message-sender">天工</div>
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="chat-input-area">
            <div class="tool-buttons">
              <el-button type="text" circle title="上传图片">
                <el-icon><PictureFilled /></el-icon>
              </el-button>
              <el-button type="text" circle title="上传文档">
                <el-icon><Document /></el-icon>
              </el-button>
              <el-button type="text" circle title="插入链接">
                <el-icon><Link /></el-icon>
              </el-button>
            </div>
            <div class="input-wrapper">
              <el-input 
                v-model="userInput" 
                type="textarea" 
                :rows="1" 
                :autosize="{ minRows: 1, maxRows: 4 }" 
                placeholder="发送消息..." 
                @keydown.enter.prevent="sendMessage"
              />
              <div class="send-options">
                <el-dropdown>
                  <span class="scene-dropdown">
                    <el-icon><Setting /></el-icon>
                    <span>通用场景</span>
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item>TARA分析</el-dropdown-item>
                      <el-dropdown-item>安全测试</el-dropdown-item>
                      <el-dropdown-item>漏洞验证</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button type="primary" class="network-button" plain>
                  <el-icon><Connection /></el-icon>
                  <span>联网</span>
                </el-button>
              </div>
              <el-button type="primary" class="send-button" :disabled="!userInput" @click="sendMessage">
                <el-icon><Position /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 右侧工具详情区域 -->
        <div class="chat-right-panel" v-if="selectedTool">
          <div class="editor-header">
            <div class="skywork-title">
              <span>Skywork虚拟机</span>
              <el-icon class="expand-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
            </div>
            <div class="tool-info">
              <div class="tool-status">
                <el-icon><Document /></el-icon>
                <span>MCP工具 {{ selectedTool.status }}</span>
              </div>
              <div class="file-info" v-if="selectedTool.file">
                <span>正在{{ selectedTool.action || '浏览' }} </span>
                <span class="file-path">{{ selectedTool.file }}</span>
              </div>
            </div>
          </div>
          
          <div class="editor-content">
            <div class="file-tabs" v-if="selectedTool.file">
              <div class="tab active">{{ getFileName(selectedTool.file) }}</div>
            </div>
            <div class="editor-view">
              <div class="editor-actions">
                <el-button-group>
                  <el-button plain size="small">差异</el-button>
                  <el-button plain size="small">原始内容</el-button>
                  <el-button type="primary" size="small">最新内容</el-button>
                </el-button-group>
              </div>
              <pre class="tool-content" v-html="formatToolContent(selectedTool.content)"></pre>
            </div>
          </div>
        </div>
        
        <div class="chat-right-panel" v-else-if="!selectedTool && currentFile">
          <div class="editor-header">
            <div class="skywork-title">
              <span>Skywork虚拟机</span>
              <el-icon class="expand-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
            </div>
            <div class="tool-info">
              <div class="tool-status">
                <el-icon><Document /></el-icon>
                <span>MCP工具 正在编辑文件</span>
              </div>
              <div class="file-name">正在编辑文件 {{ currentFile }}</div>
            </div>
          </div>
          
          <div class="editor-content">
            <div class="file-tabs">
              <div class="tab active">{{ currentFile }}</div>
            </div>
            <div class="editor-view">
              <div class="editor-actions">
                <el-button-group>
                  <el-button plain size="small">差异</el-button>
                  <el-button plain size="small">原始内容</el-button>
                  <el-button type="primary" size="small">最新内容</el-button>
                </el-button-group>
              </div>
              <div class="markdown-content" v-html="markdownContent"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Tool Modal Dialog -->
    <el-dialog
      v-model="showToolModal"
      :title="currentToolAction"
      width="80%"
      class="tool-dialog"
      :show-close="true"
    >
      <div class="tool-modal-content">
        <pre v-html="formatToolContent(currentToolOutput)"></pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Back, Share, Bell, PictureFilled, Document, Link, Position, FullScreen, Setting, ArrowDown, Connection, ArrowRight } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { agentsAPI } from '@/api';
import { useUserStore } from '@/stores';
import MarkdownIt from 'markdown-it';
import highlightjs from 'highlight.js';

// Initialize markdown parser
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && highlightjs.getLanguage(lang)) {
      try {
        return highlightjs.highlight(str, { language: lang }).value;
      } catch (__) {}
    }
    return '';
  }
});

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const messageContainer = ref(null);
const userInput = ref('');
const isAgentTyping = ref(false);
const agentType = computed(() => route.params.agentType);
const initialPrompt = computed(() => route.query.prompt || '');
const userAvatar = computed(() => userStore.userAvatar || 'https://avatars.githubusercontent.com/u/1234567');
const agentAvatar = ref('/src/components/common/agent-logo.png');

const currentFile = ref('outline_final_report_7.md');
const markdownContent = ref(`
## 结论与展望

本设计方案提出的车联网网络安全综合智能体系统，通过TARA智能体、车辆测试用例智能体、自动化测试智能体和报告分析智能体的协同工作，构建了一个从威胁分析、测试用例生成、自动化测试执行到结果分析报告输出的闭环安全保障体系。该系统能够显著提升车联网网络安全防护的效率和效果，确保车辆在全生命周期内的网络安全合规性。

该综合智能体系统的优势主要体现在以下几个方面：

* **自动化与智能化**：大幅减少人工干预，提高安全分析、测试和报告生成的效率与准确性。
* **合规性保障**：深度整合行业法规和标准，确保安全设计、测试和验证过程符合最新的合规要求。
* **风险前置与闭环管理**：在开发早期识别并缓解潜在风险，并通过持续的测试和反馈机制实现风险的闭环管理。
* **可扩展性与适应性**：模块化设计使得系统易于扩展，能够适应未来车联网技术发展和新威胁的出现。
`);

// Tool details
const selectedTool = ref(null);
const showToolModal = ref(false);
const currentToolAction = ref('');
const currentToolOutput = ref('');
const isFullscreen = ref(false);

// Sample messages with tool calls
const messages = ref([
  {
    role: 'user',
    content: '帮我制作一个关于车联网网络安全的综合智能体的设计方案'
  },
  {
    role: 'agent',
    content: '您的问题已成功接收，天工即将梳理思路，为您呈现全面且精准的答案。好的，我将帮助您完成关于车联网网络安全的综合智能体的设计方案。现在，我将首先分析并查找相关信息。',
    tools: [
      { 
        name: 'MCP工具',
        type: 'mcp',
        action: '意图识别',
        status: '已完成',
        content: '{"intent": "design_security_agent", "domain": "vehicle_network_security", "task": "create_comprehensive_design"}'
      }
    ]
  },
  {
    role: 'agent',
    content: '好的，我已分析完您的需求。为确保我能充分理解您的需求，接下来我将询问几个问题以澄清细节。',
    tools: [
      { 
        name: '搜索网页',
        type: 'search',
        action: '检索',
        status: '已完成',
        content: 'ISO/SAE 21434 车辆网络安全标准\nGBT 38278 智能网联汽车网络安全技术要求\nUN R155 车联网网络安全法规',
        file: 'search_results.md' 
      }
    ]
  }
]);

const chatTitle = computed(() => {
  if (agentType.value === 'tara') {
    return '车联网网络安全综合智能体设计方案';
  } else if (agentType.value === 'test_case') {
    return '测试用例智能体';
  } else if (agentType.value === 'automation') {
    return '自动化测试智能体';
  } else if (agentType.value === 'report') {
    return '报告分析智能体';
  } else {
    return '智能体对话';
  }
});

onMounted(async () => {
  if (initialPrompt.value) {
    userInput.value = initialPrompt.value;
    await nextTick();
    sendMessage();
  }
  scrollToBottom();
});

// Watch for messages changes to auto-scroll
watch(messages, () => {
  nextTick(() => {
    scrollToBottom();
  });
});

const goBack = () => {
  router.push('/');
};

const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
};

const sendMessage = async () => {
  if (!userInput.value.trim()) return;
  
  const message = {
    role: 'user',
    content: userInput.value
  };
  
  messages.value.push(message);
  const currentInput = userInput.value;
  userInput.value = '';
  
  scrollToBottom();
  
  // 开始处理中状态
  isAgentTyping.value = true;
  
  try {
    // Mock response for demonstration
    setTimeout(() => {
      isAgentTyping.value = false;
      
      const toolExample = { 
        name: 'MCP工具',
        type: 'mcp',
        action: '浏览',
        status: '正在浏览',
        content: `基于ISO 21434的汽车网络安全实践

"致敬自推出多种技术术语（上海）有限公司, 作者Vector China"

商业领域的IT系统和嵌入式产品的IT系统正在成为一种一体化"多功能系统"。相应地，关于汽车网络安全的ISO 21434标准应运而生。该标准的意义在于提供了一个指南，可用于评估产品、项目和组织中存在的安全风险。为了有效实施ISO 21434标准，本文介绍了ISO 21434的系统安全工程方法，并通过实际案例进行分析。

**汽车网络安全风险**

汽车网络领域的犯罪正在急剧增加。在过去几年，网络犯罪的投资回报率已经了巨大变化。通过使用勒索软件，如今的网络犯罪比毒品交易有时可获得更高利润。据统计，网络犯罪每年造成的损失约为6000亿美元，而毒品交易的利润全球估计为4000亿美元[1]。由于这可观的利润，网络攻击几乎是必然增长的趋势[1]。

回到车辆安全的计划与制度实施**产品网络安全关联**的综述组织的影响覆盖多方面，例如改变交通动能等驾驶员外界功能，操纵数据和软件等故障。成因这些攻击，许多是依赖DoS攻击和利用软件缺陷导致的功能失败。上述场景中，对于危险源和相关的控制措施，是能够被证实。而这些场景若车主车辆不设继续在道路使用，是会存在危险情况。但是，没有网络安全意法达到劫车的功能。

因此，在新开发的项目中，指定有明确的需求和相应的细节是极其重要的，这些需求应该以ISO 21434为依据进行相关的网络安全管理，测试证明和验证。`,
        file: 'https://www.cnblogs.com/trinitytec/p/17358673.html'
      };
      
      messages.value.push({
        role: 'agent',
        content: `感谢您提供的需求。根据您的请求，我会帮您设计一个关于车联网网络安全的综合智能体方案。

首先，我需要查阅一些相关的车联网安全标准和最佳实践，以确保我们的设计符合行业规范。`,
        tools: [toolExample]
      });
      
      scrollToBottom();
    }, 2000);
    
  } catch (error) {
    ElMessage.error('与智能体通信失败，请稍后再试');
    console.error('Agent communication error:', error);
    
    // 添加错误消息
    messages.value.push({
      role: 'agent',
      content: '抱歉，我遇到了一些问题，无法完成您的请求。请稍后再试。'
    });
  } finally {
    setTimeout(() => {
      isAgentTyping.value = false;
    }, 2000);
  }
};

// Tool related functions
const showToolDetails = (tool) => {
  selectedTool.value = tool;
  currentToolAction.value = tool.action || '查看工具';
  currentToolOutput.value = tool.content || '';
  scrollToBottom();
};

const formatToolContent = (content) => {
  try {
    // Try to parse as JSON
    const parsedContent = JSON.parse(content);
    return JSON.stringify(parsedContent, null, 2);
  } catch (e) {
    // Return as is if not valid JSON
    return content;
  }
};

const getFileName = (path) => {
  if (!path) return '';
  const parts = path.split('/');
  return parts[parts.length - 1];
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};
</script>

<style scoped>
.chat-page {
  height: 100vh;
  background-color: #111215;
  color: #fff;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #2c2c2c;
}

.back-button {
  font-size: 20px;
  cursor: pointer;
  margin-right: 15px;
  color: #fff;
}

.chat-title {
  flex: 1;
  font-size: 16px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.action-button {
  color: #fff;
  border-color: #2c2c2c;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #2c2c2c;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message-container {
  display: flex;
  margin-bottom: 25px;
}

.user-message {
  justify-content: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 15px;
}

.message-content {
  max-width: 70%;
}

.user-message .message-content {
  text-align: right;
}

.message-sender {
  margin-bottom: 5px;
  font-size: 12px;
  color: #aaa;
}

.message-text {
  background-color: #1d1e22;
  padding: 12px;
  border-radius: 6px;
  line-height: 1.5;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.user-message .message-text {
  background-color: #2b2d56;
}

.message-tools {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tool-item {
  display: flex;
  align-items: center;
  background-color: #2c2c2c;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.tool-item:hover {
  background-color: #3e3e3e;
}

.tool-item .el-icon {
  margin-right: 4px;
}

.tool-item .el-icon:last-child {
  margin-left: 4px;
  margin-right: 0;
  font-size: 10px;
}

.typing-indicator {
  display: flex;
  padding: 12px;
  background-color: #1d1e22;
  border-radius: 6px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #aaa;
  border-radius: 50%;
  display: inline-block;
  margin: 0 2px;
  animation: bounce 1.5s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}

.chat-input-area {
  padding: 15px;
  border-top: 1px solid #2c2c2c;
}

.tool-buttons {
  display: flex;
  margin-bottom: 10px;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
}

.input-wrapper :deep(.el-textarea__inner) {
  background-color: #2c2c2c;
  border-color: #3e3e3e;
  color: #fff;
  border-radius: 8px;
  padding: 12px;
  resize: none;
  margin-bottom: 10px;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #4080ff;
}

.send-options {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  justify-content: space-between;
}

.scene-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #aaa;
}

.scene-dropdown .el-icon {
  margin-right: 5px;
}

.network-button {
  border-color: #4080ff;
  color: #4080ff;
}

.send-button {
  background-color: #4080ff;
  align-self: flex-end;
  padding: 8px 24px;
  border-radius: 4px;
}

.chat-right-panel {
  width: 40%;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.chat-right-panel.fullscreen {
  width: 100%;
  position: absolute;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 1000;
}

.editor-header {
  padding: 15px;
  border-bottom: 1px solid #2c2c2c;
  background-color: #1a1a1e;
}

.skywork-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.expand-icon {
  cursor: pointer;
}

.tool-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #aaa;
}

.file-info {
  font-size: 14px;
  color: #aaa;
  display: flex;
  align-items: center;
  gap: 5px;
}

.file-path {
  color: #4080ff;
  text-decoration: underline;
  cursor: pointer;
}

.file-name {
  font-size: 14px;
  color: #aaa;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #1a1a1e;
}

.file-tabs {
  padding: 0 15px;
  border-bottom: 1px solid #2c2c2c;
  background-color: #1a1a1e;
}

.tab {
  display: inline-block;
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab.active {
  border-bottom-color: #4080ff;
  color: #4080ff;
}

.editor-view {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
}

.editor-actions {
  margin-bottom: 15px;
  display: flex;
  justify-content: flex-end;
}

.markdown-content,
.tool-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-content {
  background-color: transparent;
  margin: 0;
  padding: 0;
}

.tool-dialog .el-dialog__body {
  padding: 0;
  margin-top: 20px;
}

.tool-modal-content {
  padding: 15px;
  background-color: #1a1a1e;
  border-radius: 4px;
  max-height: 70vh;
  overflow-y: auto;
}
</style>