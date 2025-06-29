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
                <div v-if="message.intentInfo" class="message-intent-info">
                  <div class="intent-header" @click="toggleIntentInfo(message.id)">
                    <div class="intent-left">
                      <el-icon :class="{ 'is-rotate': openIntentInfo.includes(message.id) }">
                        <ArrowDown />
                      </el-icon>
                      <span>{{ message.intentInfo.title }}</span>
                    </div>
                    <div class="intent-right">
                      <span class="intent-status">{{ message.intentInfo.status }}</span>
                      <el-icon :class="{ 'is-rotate': openIntentInfo.includes(message.id) }">
                        <ArrowDown />
                      </el-icon>
                    </div>
                  </div>
                  <div v-if="openIntentInfo.includes(message.id)" class="intent-content">
                    <div class="intent-description">{{ message.intentInfo.description }}</div>
                    <div v-for="(question, qIndex) in message.intentInfo.questions" :key="qIndex" class="intent-question">
                      <div class="question-text">
                        {{ question.question }} <span v-if="question.required" class="required">*</span>
                      </div>
                      <!-- Checkbox type inputs -->
                      <div v-if="question.type === 'checkbox' && question.options && question.options.length > 0" class="question-options">
                        <div v-for="(option, oIndex) in question.options" :key="oIndex" class="option">
                          <el-checkbox 
                            :id="`opt-${message.id}-${qIndex}-${oIndex}`"
                            v-model="question.selectedOptions"
                            :label="option"
                          >
                            {{ option }}
                          </el-checkbox>
                        </div>
                      </div>
                      <!-- Select dropdown type -->
                      <div v-else-if="question.type === 'select' && question.options && question.options.length > 0" class="question-answer">
                        <el-select v-model="question.answer" class="answer-select">
                          <el-option
                            v-for="(option, oIndex) in question.options"
                            :key="oIndex"
                            :label="option"
                            :value="option"
                          />
                        </el-select>
                      </div>
                      <!-- File upload type -->
                      <div v-else-if="question.type === 'file'" class="question-answer">
                        <el-upload
                          action="#"
                          :auto-upload="false"
                          class="answer-upload"
                        >
                          <el-button type="primary">选择文件</el-button>
                          <template #tip>
                            <div class="el-upload__tip">
                              支持任意类型文件
                            </div>
                          </template>
                        </el-upload>
                      </div>
                      <!-- Text input type (default) -->
                      <div v-else class="question-answer">
                        <el-input 
                          v-model="question.answer" 
                          class="answer-input" 
                          :placeholder="question.required ? '必填' : '选填'"
                        />
                      </div>
                      <div v-if="question.answer && question.answer !== ''" class="question-selection">
                        <el-icon><Check /></el-icon>
                        <span>{{ question.answer }}</span>
                      </div>
                    </div>
                    <div class="intent-actions">
                      <el-button type="primary" @click="submitIntentInfo(message.id)">提交</el-button>
                      <el-button @click="skipIntentInfo(message.id)">跳过</el-button>
                    </div>
                  </div>
                </div>
                <div v-if="message.planSummary" class="message-plan-summary">
                  <div class="plan-summary-header" @click="togglePlanSummary(message.id)">
                    <div class="summary-left">
                      <el-icon :class="{ 'is-rotate': openPlanSummaries.includes(message.id) }">
                        <ArrowDown />
                      </el-icon>
                      <span>{{ message.planSummary.title }}</span>
                    </div>
                    <div class="summary-right">
                      <span class="plan-status">{{ message.planSummary.status }}</span>
                      <el-icon :class="{ 'is-rotate': openPlanSummaries.includes(message.id) }">
                        <ArrowDown />
                      </el-icon>
                    </div>
                  </div>
                  <div v-show="openPlanSummaries.includes(message.id)" class="plan-summary-content">
                    <div v-for="(step, index) in message.planSummary.steps" :key="index" class="plan-step-text">
                      {{ step }}
                    </div>
                  </div>
                </div>
                <div v-if="message.plan" class="message-plan">
                  <div class="plan-header" @click="togglePlan(message.id)">
                    <el-icon :class="{ 'is-rotate': openPlans.includes(message.id) }">
                      <ArrowDown />
                    </el-icon>
                    <span>{{ message.plan.title || '待办清单' }}</span>
                    <span class="plan-status">{{ message.plan.status || '自动执行' }}</span>
                  </div>
                  <div v-if="openPlans.includes(message.id)" class="plan-content">
                    <div v-for="(step, stepIndex) in message.plan.steps" :key="stepIndex" class="plan-step">
                      <div class="step-title">{{ step.title }}</div>
                      <div class="step-content" v-if="step.content">{{ step.content }}</div>
                      <div v-if="step.subSteps && step.subSteps.length > 0" class="sub-steps">
                        <div v-for="(subStep, subStepIndex) in step.subSteps" :key="subStepIndex" class="sub-step">
                          <div class="sub-step-text">{{ subStep.text }}</div>
                          <div v-if="subStep.tools && subStep.tools.length > 0" class="step-tools">
                            <div 
                              v-for="(tool, toolIndex) in subStep.tools" 
                              :key="toolIndex" 
                              class="tool-item" 
                              @click="saveScrollPosition(); showToolDetails(tool); expandRightPanel()"
                            >
                              <div class="tool-icon">
                                <el-icon v-if="tool.type === 'mcp'"><Tools /></el-icon>
                                <el-icon v-else-if="tool.type === 'search'"><Search /></el-icon>
                                <el-icon v-else><Document /></el-icon>
                              </div>
                              <div class="tool-info">
                                <div class="tool-name">{{ tool.name }}</div>
                                <div v-if="tool.action" class="tool-action">{{ tool.action }} <span>{{ tool.content }}</span></div>
                              </div>
                              <span style="margin-right: 10px;">{{ tool.status }}</span>
                              <el-icon class="tool-arrow"><ArrowRight /></el-icon>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
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
              <div class="send-style">
                <div class="send-options">
                  <el-button type="primary" plain class="mcp-config-button" @click="showMcpToolConfig">
                    <el-icon><Setting /></el-icon>
                    <span>配置MCP工具</span>
                  </el-button>
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
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Back, Share, Bell, PictureFilled, Document, Link, Position, FullScreen, Setting, ArrowDown, Connection, ArrowRight, Close, Tools, Search, ArrowLeft, Check, InfoFilled } from '@element-plus/icons-vue';
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
const currentContent = ref(`# 车联网网络安全综合智能体设计方案

## 摘要

本文提出了一种车联网网络安全综合智能体设计方案，旨在解决当前车联网安全测试中存在的挑战。该方案基于TARA（威胁分析与风险评估）方法论，集成了测试用例自动生成、自动化测试执行和报告分析等功能模块，形成了一个完整的车联网安全测试闭环系统。

## 设计目标
本方案的主要设计目标包括：

* **安全测试自动化**：通过智能体技术降低人工干预，提高测试效率和覆盖率。
* **一致性与标准化**：确保测试过程符合ISO/SAE 21434、GB/T 38278等行业标准。
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
const openIntentInfo = ref([]);
const openPlanSummaries = ref([]);

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

// Store scroll position when interacting with panels
let savedScrollPosition = 0;

const saveScrollPosition = () => {
  if (messageContainer.value) {
    savedScrollPosition = messageContainer.value.scrollTop;
  }
};

const restoreScrollPosition = () => {
  if (messageContainer.value && savedScrollPosition) {
    nextTick(() => {
      messageContainer.value.scrollTop = savedScrollPosition;
    });
  }
};

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
    intentInfo: {
      title: '补充信息',
      status: '自动执行',
      description: '如选择跳过或自动执行，AI将自行判断需求并执行',
      questions: [
        {
          id: 'title',
          question: '1.标题',
          required: true,
          answer: 'AI自动规划决策',
          options: [],
          selectedOptions: [],
          type: 'text'
        },
        {
          id: 'agents',
          question: '2.您希望重点展示哪个智能体？',
          required: false,
          answer: 'AI自动规划决策',
          options: ['TARA', '测试用例', '自动化测试'],
          selectedOptions: [],
          type: 'checkbox'
        },
        {
          id: 'tech',
          question: '3.您期望深入展示哪些技术原理？',
          required: false,
          answer: '',
          options: ['架构', '算法', '集成'],
          selectedOptions: [],
          type: 'select'
        },
        {
          id: 'file',
          question: '4.上传参考文件（可选）',
          required: false,
          answer: '',
          options: [],
          selectedOptions: [],
          type: 'file'
        }
      ]
    }
  },
  {
    id: 'msg2b',
    role: 'agent',
    content: '好的，我明白了。我将为您创建一个结构化的计划。',
    planSummary: {
      title: '待办清单',
      status: '自动执行',
      steps: [
        '1. 智能体技术原理与架构研究',
        '• 搜索车联网网络安全领域中智能体的核心技术和应用',
        '• 研究TARA、测试用例、自动化测试及报告分析智能体的具体实现原理',
        '• 调研多智能体系统的通用架构方案',
        '2. 生成PPT大纲',
        '• 规划PPT的整体结构，突出各智能体的技术原理与系统架构',
        '• 设计各章节的核心内容和逻辑流程',
        '3. 制作PPT',
        '• 创建PPT封面、目录及内容页面',
        '• 将技术方案、架构图等内容填充至各页面',
        '• 添加图表和视觉元素，增强报告的专业性'
      ]
    }
  },
  {
    id: 'msg3',
    role: 'agent',
    content: '我将开始收集车联网网络安全及TARA分析的背景信息。',
    plan: {
      title: '收集车联网网络安全及TARA分析的背景信息',
      status: '正在执行',
      steps: [
        {
          title: 'Action 1: 我将首先搜索车联网网络安全的基本概念和重要性。这将为后续任务提供基础理解。然后，我会初步了解TARA方法论在汽车行业的应用概况。',
          subSteps: [
            { 
              text: '搜索车联网安全基础知识',
              tools: [
                { 
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网网络安全基本概念'
                }
              ]
            },
            { 
              text: '了解TARA在汽车行业的应用',
              tools: [
                { 
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网网络安全重要性'
                },
                { 
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: 'TARA 威胁分析与风险评估 汽车行业 应用'
                }
              ]
            },
          ]
        }
      ]
    },
  },
  {
    id: 'msg4',
    role: 'agent',
    content: '我已全面了解车联网网络安全概念、TARA方法论及国内外法规标准，下一步将深入研究中国具体标准。',
    plan: {
      title: '收集车联网网络安全及TARA分析的背景信息',
      status: '正在执行',
      steps: [
        {
          title: '我已全面了解车联网网络安全概念、TARA方法论及国内外法规标准，下一步将深入研究中国具体标准。',
          subSteps: [
            {
              text: '搜索中国车联网网络安全标准信息',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '中国车联网网络安全已发布具体标准名称 编号'
                }
              ]
            },
            {
              text: '研究车联网信息服务安全规范',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网信息服务安全规范 GB/T 35279 内容要点'
                }
              ]
            },
            {
              text: '了解用户信息保护要求',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网信息服务用户真实身份信息保护要求 JT/T 1301 内容要点'
                }
              ]
            }
          ]
        }
      ]
    }
  },
  {
    id: 'msg5',
    role: 'agent',
    content: '我已收集车联网网络安全概念、TARA方法论及国内外法规标准，下一步将深入研究具体标准内容。',
    plan: {
      title: '收集车联网网络安全及TARA分析的背景信息',
      status: '正在执行',
      steps: [
        {
          title: '我已收集车联网网络安全概念、TARA方法论及国内外法规标准，下一步将深入研究具体标准内容。',
          subSteps: [
            {
              text: '浏览中国标准文件内容',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '浏览',
                  status: '已完成',
                  content: 'https://std.samr.gov.cn/gb/search/gbDetailed?id=2AD0270639OA091BE06397BE0A0A2D62'
                }
              ]
            },
            {
              text: '查阅技术实现方案',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '浏览',
                  status: '已完成',
                  content: 'https://max.book118.com/html/2020/0415/8065014057002106.shtm'
                }
              ]
            },
            {
              text: '深入国家标准细节',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '浏览',
                  status: '已完成',
                  content: 'https://ndls.org.cn/standard/detail/533d1447ab92d9349a305ec7fe440f11'
                }
              ]
            },
            {
              text: '整理收集的信息',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '聚合信息',
                  status: '已完成',
                  content: ''
                }
              ]
            },
            {
              text: '规划后续研究步骤',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '多步执行任务',
                  status: '已完成',
                  content: ''
                }
              ]
            }
          ]
        }
      ]
    }
  },
  {
    id: 'msg6',
    role: 'agent',
    content: '好的，现在我们开始执行任务。',
  },
  {
    id: 'msg7',
    role: 'agent',
    content: '我将开始研究车联网安全领域的核心技术，并设计综合智能体的总体架构。',
    plan: {
      title: '我将开始研究车联网安全领域的核心技术，并设计综合智能体的总体架构。',
      status: '正在执行',
      steps: [
        {
          title: '我将开始研究车联网安全领域的核心技术，并设计综合智能体的总体架构。',
          content: '为了完成"车联网网络安全领域的核心技术与架构研究"这一任务，我需要深入研究TARA方法论、测试用例生成、自动化测试及报告分析等关键技术在车联网安全领域的具体应用，并在此基础上设计一个包含多个专业智能体的综合系统架构。为了获取足够全面和深入的信息来支撑后续的架构设计，我将首先执行一次深度网络搜索。\n\n好的，我将开始执行任务。首先，我需要理解车联网安全领域中提到的四个关键技术：TARA（威胁分析与风险评估）、车辆测试用例生成、自动化测试和报告分析。然后收集这些技术的具体信息。Action 1:',
          subSteps: [
            {
              text: '研究TARA方法论在车联网应用',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网 TARA 方法论 应用'
                }
              ]
            },
            {
              text: '了解自动化测试用例生成技术',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网 安全 测试用例自动生成 技术'
                }
              ]
            },
            {
              text: '深入研究测试用例自动生成技术原理',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网安全 测试用例自动生成 技术原理'
                },
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: 'Automated test case generation techniques for connected vehicle cybersecurity'
                }
              ]
            },
            {
              text: '学习测试用例生成引擎实现原理',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '搜索网页',
                  status: '已完成',
                  content: '车联网安全测试用例自动生成引擎 实现原理'
                },
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '深度搜索网页',
                  status: '已完成',
                  content: ''
                }
              ]
            },
            {
              text: '整合研究成果并设计架构',
              tools: [
                {
                  name: 'MCP工具',
                  type: 'mcp',
                  action: '分发任务',
                  status: '已完成',
                  content: ''
                }
              ]
            }
          ]
        }
      ]
    }
  },
  {
    id: 'msg8',
    role: 'agent',
    content: '好的，第一阶段的核心技术与架构研究已经完成。现在我们进入第二阶段，对每个智能体的功能进行详细设计。',
  },
  {
    id: 'msg9',
    role: 'agent',
    content: '',
    plan: {
      title: '我将开始详细设计各个智能体的功能，包括TARA智能体、车辆测试用例智能体、自动化测试智能体和报告分析智能体。',
      status: '正在执行',
      steps: [
        {
          title: '我将开始详细设计各个智能体的功能，包括TARA智能体、车辆测试用例智能体、自动化测试智能体和报告分析智能体。',
          content: '',
          subSteps: [
            {
              text: '详细设计TARA智能体功能',
              tools: []
            },
            {
              text: '详细设计车辆测试用例智能体功能',
              tools: []
            },
            {
              text: '详细设计自动化测试智能体功能',
              tools: []
            },
            {
              text: '详细设计报告分析智能体功能',
              tools: []
            }
          ]
        }
      ]
    }
  },
  {
    id: 'msg10',
    role: 'agent',
    content: '好的，第二阶段的各智能体功能设计已经完成。现在我们进入最后阶段，撰写完整的设计方案。',
  },
  {
    id: 'msg11',
    role: 'agent',
    content: '',
    plan: {
      title: '我将撰写一份详细的车联网网络安全综合智能体设计方案。',
      status: '正在执行',
      steps: [
        {
          title: '我将撰写一份详细的车联网网络安全综合智能体设计方案。',
          content: '',
          subSteps: []
        }
      ]
    }
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

onMounted(() => {
  if (initialPrompt.value) {
    userInput.value = initialPrompt.value;
    sendMessage();
  }
  scrollToBottom(true);
  
  // Open plans by default
  messages.value.forEach(message => {
    if (message.plan && message.plan.steps && message.plan.steps.length > 0) {
      togglePlan(message.id);
    }
    if (message.intentInfo) {
      toggleIntentInfo(message.id);
    }
    if (message.planSummary) {
      togglePlanSummary(message.id);
    }
  });
});

// Watch for messages changes to auto-scroll
watch(messages, () => {
  nextTick(() => {
    scrollToBottom(true);
    
    // Open plans by default for new messages
    const lastMessage = messages.value[messages.value.length - 1];
    if (lastMessage?.plan?.steps?.length > 0) {
      togglePlan(lastMessage.id);
    }
    if (lastMessage?.intentInfo) {
      toggleIntentInfo(lastMessage.id);
    }
    if (lastMessage?.planSummary) {
      togglePlanSummary(lastMessage.id);
    }
  });
});

const goBack = () => {
  router.push('/');
};

const scrollToBottom = (force = false) => {
  if (messageContainer.value) {
    // Don't scroll if we have a saved position and aren't forcing a scroll
    if (savedScrollPosition > 0 && !force) {
      restoreScrollPosition();
      return;
    }
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
};

const sendMessage = async () => {
  if (!userInput.value.trim()) return;
  
  // 添加用户消息
  const userMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: userInput.value
  };
  
  messages.value.push(userMessage);
  const currentInput = userInput.value;
  userInput.value = '';
  
  scrollToBottom(true);
  
  // 开始处理中状态
  isAgentTyping.value = true;
  
  try {
    // 根据当前路由的agentType调用对应的智能体API
    const agentTypeParam = agentType.value || 'tara';
    const response = await fetch(`/api/agents/${agentTypeParam}/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_request: currentInput,
        context: {},
        chat_mode: true,
        enable_planning: true,
        step_by_step: true
      })
    });
    
    if (!response.ok) {
      throw new Error(`API请求失败: ${response.statusText}`);
    }
    
    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // 用于存储当前正在处理的消息
    let currentAgentMessage = null;
    let messageId = `agent-${Date.now()}`;
    
    // 读取流数据
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      // 解码并分割数据（可能包含多个事件）
      const text = decoder.decode(value);
      const events = text.split('\n\n').filter(e => e.trim().startsWith('data: '));
      
      for (const eventText of events) {
        // 提取JSON数据
        const jsonStr = eventText.replace('data: ', '');
        try {
          const eventData = JSON.parse(jsonStr);
          
          // 根据事件类型处理数据
          switch (eventData.type) {
            case 'task_started':
              // 新建一个智能体消息
              currentAgentMessage = {
                id: messageId,
                role: 'agent',
                content: '正在分析您的请求...'
              };
              messages.value.push(currentAgentMessage);
              break;
              
            case 'planning':
              // 更新计划信息
              if (currentAgentMessage) {
                currentAgentMessage.content = eventData.message || '正在制定执行计划...';
                
                // 添加计划摘要
                if (eventData.steps) {
                  currentAgentMessage.planSummary = {
                    title: '待办清单',
                    status: '自动执行',
                    steps: eventData.steps.map(step => step.title + (step.description ? ': ' + step.description : ''))
                  };
                  
                  // 自动打开计划摘要
                  if (!openPlanSummaries.value.includes(currentAgentMessage.id)) {
                    openPlanSummaries.value.push(currentAgentMessage.id);
                  }
                }
              }
              break;
              
            case 'step_start':
            case 'step_progress':
            case 'step_completed':
              // 处理步骤执行状态
              if (currentAgentMessage) {
                // 如果还没有plan对象，创建一个
                if (!currentAgentMessage.plan) {
                  currentAgentMessage.plan = {
                    title: '执行步骤',
                    status: '正在执行',
                    steps: []
                  };
                  
                  // 自动打开计划详情
                  if (!openPlans.value.includes(currentAgentMessage.id)) {
                    openPlans.value.push(currentAgentMessage.id);
                  }
                }
                
                // 查找或创建步骤
                let step = currentAgentMessage.plan.steps.find(s => s.title === eventData.step_name);
                if (!step) {
                  step = {
                    title: eventData.step_name,
                    content: eventData.message || '',
                    subSteps: []
                  };
                  currentAgentMessage.plan.steps.push(step);
                }
                
                // 更新步骤内容和工具信息
                if (eventData.message) {
                  step.content = eventData.message;
                }
                
                // 添加工具调用信息
                if (eventData.tool_calls) {
                  for (const toolCall of eventData.tool_calls) {
                    const subStep = {
                      text: `执行${toolCall.tool}工具`,
                      tools: [{
                        name: 'MCP工具',
                        type: 'mcp',
                        action: toolCall.input || '执行',
                        status: toolCall.status || '正在执行',
                        content: toolCall.output || ''
                      }]
                    };
                    
                    // 避免重复添加
                    const exists = step.subSteps.some(ss => 
                      ss.text === subStep.text && 
                      ss.tools && ss.tools[0] && ss.tools[0].action === subStep.tools[0].action
                    );
                    
                    if (!exists) {
                      step.subSteps.push(subStep);
                    }
                  }
                }
                
                // 更新步骤状态
                if (eventData.type === 'step_completed') {
                  step.status = '已完成';
                }
              }
              break;
              
            case 'result':
              // 结果数据处理
              if (currentAgentMessage) {
                // 更新消息内容为最终结果
                if (typeof eventData.result_data === 'string') {
                  currentAgentMessage.content = eventData.result_data;
                } else if (eventData.result_data && eventData.result_data.content) {
                  currentAgentMessage.content = eventData.result_data.content;
                } else if (eventData.message) {
                  currentAgentMessage.content = eventData.message;
                }
                
                // 如果有总结信息
                if (eventData.result_data && eventData.result_data.intelligent_summary) {
                  const summary = eventData.result_data.intelligent_summary;
                  currentAgentMessage.content = summary.overview || currentAgentMessage.content;
                  
                  // 添加成就和建议到计划摘要
                  if (!currentAgentMessage.planSummary) {
                    currentAgentMessage.planSummary = {
                      title: '分析总结',
                      status: '已完成',
                      steps: []
                    };
                  }
                  
                  if (summary.achievements) {
                    currentAgentMessage.planSummary.steps = [
                      ...currentAgentMessage.planSummary.steps,
                      ...summary.achievements.map(a => `✓ ${a}`)
                    ];
                  }
                  
                  if (summary.recommendations) {
                    currentAgentMessage.planSummary.steps = [
                      ...currentAgentMessage.planSummary.steps,
                      ...summary.recommendations.map(r => `→ ${r}`)
                    ];
                  }
                  
                  // 自动打开计划摘要
                  if (!openPlanSummaries.value.includes(currentAgentMessage.id)) {
                    openPlanSummaries.value.push(currentAgentMessage.id);
                  }
                }
                
                // 标记所有步骤完成
                if (currentAgentMessage.plan) {
                  currentAgentMessage.plan.status = '已完成';
                  currentAgentMessage.plan.steps.forEach(step => {
                    step.status = '已完成';
                  });
                }
              }
              break;
              
            case 'error':
              // 错误处理
              if (currentAgentMessage) {
                currentAgentMessage.content = `执行出错: ${eventData.message}`;
                
                if (currentAgentMessage.plan) {
                  currentAgentMessage.plan.status = '执行失败';
                }
              } else {
                // 如果还没有创建消息，创建一个错误消息
                messages.value.push({
                  id: messageId,
                  role: 'agent',
                  content: `抱歉，执行出错: ${eventData.message}`
                });
              }
              break;
              
            case 'completed':
              // 任务完成，不需要特殊处理
              break;
              
            default:
              console.log('未处理的事件类型:', eventData.type);
          }
        } catch (e) {
          console.error('解析事件数据失败:', e);
        }
      }
      
      // 每次收到新数据后滚动到底部
      scrollToBottom();
    }
    
    isAgentTyping.value = false;
    
  } catch (error) {
    console.error('智能体通信错误:', error);
    ElMessage.error('与智能体通信失败，请稍后再试');
    
    // 添加错误消息
    messages.value.push({
      id: `agent-${Date.now()}`,
      role: 'agent',
      content: '抱歉，我遇到了一些问题，无法完成您的请求。请稍后再试。'
    });
    
    isAgentTyping.value = false;
  }
};

// Tool related functions
const showToolDetails = (tool) => {
  selectedTool.value = tool;
  currentToolAction.value = tool.action || '查看工具';
  currentToolOutput.value = tool.content || '';
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
  saveScrollPosition();
  isFullscreen.value = !isFullscreen.value;
  restoreScrollPosition();
};

const collapseRightPanel = () => {
  saveScrollPosition();
  isRightPanelCollapsed.value = true;
  restoreScrollPosition();
};

const expandRightPanel = () => {
  saveScrollPosition();
  isRightPanelCollapsed.value = false;
  restoreScrollPosition();
};

const togglePlan = (messageId) => {
  if (openPlans.value.includes(messageId)) {
    openPlans.value = openPlans.value.filter(id => id !== messageId);
  } else {
    openPlans.value.push(messageId);
  }
};

const toggleIntentInfo = (messageId) => {
  if (openIntentInfo.value.includes(messageId)) {
    openIntentInfo.value = openIntentInfo.value.filter(id => id !== messageId);
  } else {
    openIntentInfo.value.push(messageId);
  }
};

const togglePlanSummary = (messageId) => {
  if (openPlanSummaries.value.includes(messageId)) {
    openPlanSummaries.value = openPlanSummaries.value.filter(id => id !== messageId);
  } else {
    openPlanSummaries.value.push(messageId);
  }
};

const submitIntentInfo = (messageId) => {
  const message = messages.value.find(msg => msg.id === messageId);
  if (!message || !message.intentInfo) return;
  
  // Validate required fields
  const requiredQuestions = message.intentInfo.questions.filter(q => q.required);
  const allRequiredAnswered = requiredQuestions.every(q => {
    if (q.type === 'checkbox') return q.selectedOptions && q.selectedOptions.length > 0;
    return q.answer && q.answer.trim() !== '';
  });
  
  if (!allRequiredAnswered) {
    // Show error message or highlight required fields
    alert('请填写所有必填项');
    return;
  }
  
  // For checkbox type, update the answer from selectedOptions
  message.intentInfo.questions.forEach(q => {
    if (q.type === 'checkbox' && q.selectedOptions && q.selectedOptions.length > 0) {
      q.answer = q.selectedOptions.join(', ');
    }
  });
  
  // Update status to show submission
  message.intentInfo.status = '已提交';
  
  // Close the form
  toggleIntentInfo(messageId);
  
  // Here you would typically send this data to the backend
  console.log('Intent info submitted:', message.intentInfo);
  
  // Continue the conversation flow
  // This is a mock - in production this would trigger the next step in the workflow
};

const skipIntentInfo = (messageId) => {
  const message = messages.value.find(msg => msg.id === messageId);
  if (!message || !message.intentInfo) return;
  
  // Mark as skipped and close
  message.intentInfo.status = '已跳过';
  toggleIntentInfo(messageId);
  
  // Continue the conversation flow
  console.log('Intent info skipped');
};

const showMcpToolConfig = () => {
  // Show the MCP tool configuration dialog
  showToolModal.value = true;
  currentToolAction.value = 'Tools Configuration';
  
  // In a real application, you would fetch the available tools from an API
  // For now, we're using the static content already defined in the template
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
  background-color: transparent;
}

.action-button:hover {
  color: #fff;
  border-color: #4080ff;
  background-color: rgba(64, 128, 255, 0.1);
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
  text-align: left;
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

.message-intent-info {
  margin-top: 10px;
}

.intent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #1d1e22;
  padding: 12px 15px;
  border-radius: 6px;
  margin-top: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.intent-header:hover {
  background-color: #2c2c2c;
}

.intent-left {
  display: flex;
  align-items: center;
}

.intent-right {
  display: flex;
  align-items: center;
}

.intent-header span:first-child {
  font-size: 16px;
  font-weight: bold;
  margin-left: 10px;
}

.intent-status {
  background-color: #272b28;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  margin-left: auto;
  margin-right: 10px;
}

.intent-header .el-icon {
  margin-left: 5px;
  transition: transform 0.3s;
  font-size: 14px;
}

.intent-header .el-icon.is-rotate {
  transform: rotate(180deg);
}

.intent-content {
  padding: 10px 15px;
  padding-left: 25px;
  padding-top: 20px;
}

.intent-description {
  margin-bottom: 10px;
  color: #aaa;
}

.intent-question {
  margin-bottom: 15px;
  position: relative;
  padding-left: 15px;
}

.question-text {
  font-weight: 500;
  margin-bottom: 8px;
  color: #ddd;
  position: relative;
}

.question-text .required {
  color: #f56c6c;
}

.question-options {
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.option {
  margin-bottom: 5px;
  background-color: #1d1e22;
  padding: 8px 15px;
  border-radius: 6px;
  min-width: 120px;
}

.question-answer {
  margin-bottom: 10px;
}

.answer-input {
  background-color: #1d1e22;
  border: 1px solid #2c2c2c;
  border-radius: 4px;
  padding: 8px;
  width: 100%;
  color: #fff;
}

.question-selection {
  display: flex;
  align-items: center;
  margin-top: 5px;
  color: #409eff;
}

.question-selection .el-icon {
  margin-right: 5px;
}

.message-plan-summary {
  margin-top: 10px;
}

.plan-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #1d1e22;
  padding: 12px 15px;
  border-radius: 6px;
  margin-top: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.plan-summary-header:hover {
  background-color: #2c2c2c;
}

.summary-left {
  display: flex;
  align-items: center;
}

.summary-right {
  display: flex;
  align-items: center;
}

.plan-summary-header span:nth-child(2) {
  font-size: 24px;
  font-weight: bold;
  margin-left: 10px;
}

.plan-summary-header .el-icon {
  margin-right: 15px;
  transition: transform 0.3s;
  font-size: 14px;
}

.plan-summary-header .el-icon.is-rotate {
  transform: rotate(180deg);
}

.plan-summary-content {
  padding: 10px 15px;
  padding-left: 30px;
  padding-top: 20px;
}

.plan-step-text {
  margin-bottom: 10px;
  color: #ddd;
  line-height: 1.6;
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

.step-title {
  font-weight: 500;
  margin-top: 15px;
  margin-bottom: 10px;
  color: #fff;
}

.step-content {
  margin-bottom: 15px;
  color: #aaa;
  line-height: 1.5;
  padding-left: 20px;
  padding-top: 10px;
}

.sub-steps {
  padding-left: 20px;
  padding-top: 10px;
}

.sub-step {
  margin-bottom: 15px;
  position: relative;
}

.sub-step-text {
  font-weight: 500;
  margin-bottom: 8px;
  color: #ddd;
  position: relative;
}

.sub-step-text::before {
  content: "•";
  position: absolute;
  left: -15px;
  color: #888;
}

.step-tools {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tool-item {
  display: flex;
  width: 100%;
  align-items: center;
  background-color: #2c2c2c;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 8px;
  margin-left: 10px;
  border-left: 2px solid #4080ff;
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
.editor-header > .tool-info {
  text-align: left;
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
  padding: 0 15px;
  border-top: 1px solid #2c2c2c;
  background-color: #111215;
}

.tool-buttons {
  display: flex;
  /* margin-bottom: 10px; */
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

.send-style {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.send-options {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  /* justify-content: space-between; */
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

.mcp-config-button {
  border-color: #4080ff;
  color: #4080ff;
  background-color: transparent;
}

.mcp-config-button:hover {
  background-color: rgba(64, 128, 255, 0.1);
  border-color: #4080ff;
  color: #4080ff;
}

.network-button {
  border-color: #4080ff;
  color: #4080ff;
  background-color: transparent;
}

.network-button:hover {
  background-color: rgba(64, 128, 255, 0.1);
  border-color: #4080ff;
  color: #4080ff;
}

.send-button {
  background-color: #4080ff;
  border-color: #4080ff;
  /* align-self: flex-end; */
  padding: 8px 24px;
  border-radius: 4px;
}

.send-button:hover {
  background-color: #3a75e6;
  border-color: #3a75e6;
}

.send-button:disabled {
  background-color: #2c2c2c;
  border-color: #2c2c2c;
  color: #666;
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

.required {
  color: #f56c6c;
  margin-left: 2px;
}

.intent-question {
  padding: 10px 15px;
  border-bottom: 1px solid #333;
}

.question-text {
  margin-bottom: 8px;
  font-size: 14px;
  color: #d4d4d4;
}

.question-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}

.option {
  display: flex;
  align-items: center;
}

.question-answer {
  margin-bottom: 8px;
}

.answer-input {
  background-color: #1d1e22;
  border: 1px solid #333;
  color: #fff;
  border-radius: 4px;
  padding: 6px 10px;
  width: 100%;
}

.intent-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
  padding: 0 15px 15px;
}

.answer-select {
  width: 100%;
}

.answer-select :deep(.el-input__wrapper) {
  background-color: #1d1e22;
  box-shadow: 0 0 0 1px #333 inset;
}

.answer-select :deep(.el-input__inner) {
  color: #fff;
}

.answer-upload {
  width: 100%;
}

.answer-upload :deep(.el-upload__tip) {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.answer-input {
  width: 100%;
}

.answer-input :deep(.el-input__wrapper) {
  background-color: #1d1e22;
  box-shadow: 0 0 0 1px #333 inset;
}

.answer-input :deep(.el-input__inner) {
  color: #fff;
}

.el-checkbox {
  color: #d4d4d4;
}

.question-selection {
  display: flex;
  align-items: center;
  color: #67c23a;
  font-size: 13px;
  margin-top: 5px;
}
</style>