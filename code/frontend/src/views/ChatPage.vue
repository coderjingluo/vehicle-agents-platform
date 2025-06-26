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
        <div class="chat-left-panel" :class="{ 'expanded': isRightPanelCollapsed }">
          <div class="chat-messages" ref="messageContainer">
            <div v-for="(message, index) in messages" :key="index" 
              :class="['message-container', message.role === 'user' ? 'user-message' : 'agent-message']">
              <div class="message-avatar">
                <el-avatar :size="36" :src="message.role === 'user' ? userAvatar : agentAvatar"></el-avatar>
              </div>
              <div class="message-content">
                <div class="message-sender">{{ message.role === 'user' ? '您' : '天工' }}</div>
                <div class="message-text" v-html="message.content"></div>
                <div v-if="message.plan" class="message-plan">
                  <div class="plan-header" @click="togglePlan(message.id)">
                    <el-icon :class="{ 'is-rotate': openPlans.includes(message.id) }">
                      <ArrowDown />
                    </el-icon>
                    <span>{{ message.plan.title || '待办清单' }}</span>
                    <span class="plan-status">{{ message.plan.status || '自动执行' }}</span>
                  </div>
                  <div v-show="openPlans.includes(message.id)" class="plan-content">
                    <div v-for="(step, stepIndex) in message.plan.steps" :key="stepIndex" class="plan-step">
                      <div class="step-number">{{ stepIndex + 1 }}. {{ step.title }}</div>
                      <div v-if="step.description" class="step-description">
                        <div v-for="(desc, descIndex) in step.description.split('\n')" :key="descIndex" class="description-item">
                          <span v-if="desc.trim().startsWith('•')">{{ desc }}</span>
                          <span v-else>• {{ desc }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="message.tools && message.tools.length > 0" class="message-tools">
                  <div v-for="(tool, toolIndex) in message.tools" :key="toolIndex" 
                    class="tool-item" @click="showToolDetails(tool)">
                    <div class="tool-icon">
                      <el-icon v-if="tool.type === 'mcp'"><Tools /></el-icon>
                      <el-icon v-else-if="tool.type === 'search'"><Search /></el-icon>
                      <el-icon v-else><Document /></el-icon>
                    </div>
                    <div class="tool-info">
                      <div class="tool-name">{{ tool.name }}</div>
                      <div v-if="tool.action" class="tool-action">{{ tool.action }}</div>
                    </div>
                    <el-icon class="tool-arrow"><ArrowRight /></el-icon>
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
        <div v-if="!isRightPanelCollapsed" class="chat-right-panel" :class="{ 'fullscreen': isFullscreen }">
          <div v-if="selectedTool" class="right-panel-content">
            <div class="editor-header">
              <div class="skywork-title">
                <span>Skywork虚拟机</span>
                <div class="header-actions">
                  <el-icon class="expand-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
                  <el-icon class="collapse-icon" @click="collapseRightPanel"><Close /></el-icon>
                </div>
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
          
          <div v-else-if="currentFile" class="right-panel-content">
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
        
        <!-- Collapsed panel button -->
        <div v-if="isRightPanelCollapsed" class="collapsed-panel-button" @click="expandRightPanel">
          <el-icon><ArrowLeft /></el-icon>
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
import { Back, Share, Bell, PictureFilled, Document, Link, Position, FullScreen, Setting, ArrowDown, Connection, ArrowRight, Close, Tools, Search, ArrowLeft } from '@element-plus/icons-vue';
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
const isRightPanelCollapsed = ref(false);
const openPlans = ref([]);

// Sample messages with tool calls
const messages = ref([
  {
    id: 'msg1',
    role: 'user',
    content: '帮我制作一个关于车联网网络安全的综合智能体的设计方案'
  },
  {
    id: 'msg2',
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
    id: 'msg3',
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
  },
  {
    id: 'msg4',
    role: 'agent',
    content: '感谢您的确认。我将为您制作一个结构化的计划。',
    plan: {
      title: '待办清单',
      status: '自动执行',
      steps: [
        {
          title: '收集车联网安全背景信息',
          description: '调研当前车联网网络安全现状、主要威胁和挑战\n搜索相关的法律法规和行业标准（如TARA分析方法）\n研究构成综合智能体的各项关键技术（如自动化测试、风险评估模型）'
        },
        {
          title: '梳理各智能体功能与关联',
          description: '整理TARA智能体的核心功能与实现逻辑\n归纳车辆测试用例智能体、自动化测试智能体和报告分析智能体的工作流程\n分析各智能体之间的协同工作关系和数据流转路径'
        },
        {
          title: '生成PPT大纲',
          description: '基于收集的资料整理PPT大纲\n设计演示文稿结构和视觉效果\n准备关键图表和示例'
        }
      ]
    }
  },
  {
    id: 'msg5',
    role: 'agent',
    content: '我将开始执行计划的第一阶段：收集车联网安全与TARA分析背景信息。我将努力收集必要的信息。',
    tools: [
      {
        name: 'MCP工具',
        type: 'mcp',
        action: '浏览',
        status: '正在浏览',
        content: `基于ISO 21434的汽车网络安全实践

"致敬自推出多种技术术语（上海）有限公司, 作者Vector China"

商业领域的IT系统和嵌入式产品的IT系统正在成为一种一体化"多功能系统"。相应地，关于汽车网络安全的ISO 21434标准应运而生。该标准的意义在于提供了一个指南，可用于评估产品、项目和组织中存在的安全风险。为了有效实施ISO 21434标准，本文介绍了ISO 21434的系统安全工程方法，并通过实际案例进行分析。

**汽车网络安全风险**

汽车网络领域的犯罪正在急剧增加。在过去几年，网络犯罪的投资回报率已经了巨大变化。通过使用勒索软件，如今的网络犯罪比毒品交易有时可获得更高利润。据统计，网络犯罪每年造成的损失约为6000亿美元，而毒品交易的利润全球估计为4000亿美元[1]。由于这可观的利润，网络攻击几乎是必然增长的趋势[1]。`,
        file: 'https://www.cnblogs.com/trinitytec/p/17358673.html'
      },
      {
        name: 'MCP工具',
        type: 'mcp',
        action: '检索',
        status: '已完成',
        content: 'ISO/SAE 21434 TARA 实践案例\nGB 44495-2024 汽车车载信息安全技术要求 文本 或 详细解读\nUN R155 UNECE 车辆网络安全法规具体内容'
      },
      {
        name: 'MCP工具',
        type: 'mcp',
        action: '浏览',
        status: '已完成',
        content: 'NHTSA 美国车联网网络安全法规要求'
      }
    ]
  },
  {
    id: 'msg6',
    role: 'agent',
    content: '我已经完成了"收集车联网安全背景信息"阶段。现在，我将更新计划。',
    tools: [
      {
        name: 'MCP工具',
        type: 'mcp',
        action: '写入文件',
        status: '已完成',
        content: '# 车联网网络安全综合智能体设计方案\n\n## 1. 背景与需求\n\n随着车联网技术的快速发展，车辆网络安全面临的威胁日益增加。为了有效应对这些安全挑战，需要建立一个综合性的智能体系统，覆盖从威胁分析、测试用例生成到自动化测试执行和报告分析的完整生命周期。\n\n### 1.1 行业现状\n\n- 车联网安全事件频发，攻击手段多样化\n- 法规标准日益完善（ISO/SAE 21434, UN R155, GB/T 38278等）\n- 传统安全测试方法效率低下，覆盖率不足\n- 安全分析与测试流程割裂，缺乏闭环管理',
        file: 'TODO.md'
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

const collapseRightPanel = () => {
  isRightPanelCollapsed.value = true;
};

const expandRightPanel = () => {
  isRightPanelCollapsed.value = false;
};

const togglePlan = (messageId) => {
  const index = openPlans.value.indexOf(messageId);
  if (index > -1) {
    openPlans.value.splice(index, 1);
  } else {
    openPlans.value.push(messageId);
  }
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #2c2c2c;
  background-color: #111215;
}

.back-button {
  font-size: 20px;
  cursor: pointer;
  margin-right: 15px;
  color: #fff;
}

.chat-title {
  font-size: 18px;
  font-weight: 500;
  color: #fff;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  border-color: #2c2c2c;
  color: #aaa;
}

.action-button:hover {
  color: #fff;
  border-color: #4080ff;
}

.chat-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  background-color: #111215;
}

.chat-left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #2c2c2c;
  transition: flex 0.3s;
}

.chat-left-panel.expanded {
  flex: 1;
  width: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #111215;
}

.message-container {
  display: flex;
  margin-bottom: 25px;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 15px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.user-message .message-text {
  background-color: #2b2d56;
  text-align: left;
}

.user-message .message-sender {
  text-align: right;
}

.message-sender {
  font-size: 14px;
  color: #aaa;
  margin-bottom: 5px;
}

.message-text {
  background-color: #1d1e22;
  padding: 12px 15px;
  border-radius: 6px;
  line-height: 1.5;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.message-plan {
  margin-top: 10px;
}

.plan-header {
  display: flex;
  align-items: center;
  background-color: #1d1e22;
  padding: 12px 15px;
  border-radius: 6px;
  margin-top: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.plan-header:hover {
  background-color: #2c2c2c;
}

.plan-header .el-icon {
  margin-right: 10px;
  transition: transform 0.3s;
  font-size: 14px;
}

.plan-header .el-icon.is-rotate {
  transform: rotate(180deg);
}

.plan-status {
  margin-left: auto;
  background-color: #2c2c2c;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: #4080ff;
}

.plan-content {
  padding: 10px 15px;
}

.plan-step {
  margin-bottom: 15px;
}

.step-number {
  font-weight: 500;
  margin-bottom: 8px;
  color: #fff;
}

.step-description {
  padding-left: 20px;
}

.description-item {
  margin-bottom: 8px;
  color: #aaa;
  line-height: 1.5;
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
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 8px;
}

.tool-item:hover {
  background-color: #3e3e3e;
}

.tool-icon {
  margin-right: 8px;
  color: #aaa;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-weight: 500;
}

.tool-action {
  font-size: 11px;
  color: #aaa;
}

.tool-arrow {
  font-size: 12px;
}

.chat-input-area {
  padding: 15px 20px;
  border-top: 1px solid #2c2c2c;
  background-color: #111215;
}

.tool-buttons {
  display: flex;
  margin-bottom: 10px;
}

.tool-buttons .el-button {
  color: #aaa;
}

.tool-buttons .el-button:hover {
  color: #fff;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
}

.input-wrapper :deep(.el-textarea__inner) {
  background-color: #1d1e22;
  border-color: #2c2c2c;
  color: #fff;
  border-radius: 8px;
  padding: 12px 15px;
  resize: none;
  margin-bottom: 10px;
  transition: border-color 0.2s;
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
  background-color: #1a1a1e;
  border-left: 1px solid #2c2c2c;
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
  color: #fff;
  font-weight: 500;
}

.expand-icon, .collapse-icon {
  cursor: pointer;
  font-size: 16px;
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
  padding: 0 15px 15px;
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

.collapsed-panel-button {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background-color: #1a1a1e;
  border-radius: 4px 0 0 4px;
  border: 1px solid #2c2c2c;
  border-right: none;
  padding: 10px 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: background-color 0.2s;
}

.collapsed-panel-button:hover {
  background-color: #2c2c2c;
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

.right-panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>