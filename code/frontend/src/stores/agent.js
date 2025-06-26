import { defineStore } from 'pinia';
import { agentsAPI } from '@/api';

export const useAgentStore = defineStore('agent', {
  state: () => ({
    agents: {
      tara: {
        id: 'tara',
        name: 'TARA智能体',
        description: '威胁分析与风险评估专业智能体',
        icon: '🛡️',
        capabilities: [
          '基于法规强标的TARA分析',
          '导出目标和需求分析',
          '为车企体系部分提供专业方案',
          '风险评估和缓解措施规划'
        ],
        history: []
      },
      test_case: {
        id: 'test_case',
        name: '测试用例智能体',
        description: '基于TARA结果生成测试用例',
        icon: '📝',
        capabilities: [
          '基于TARA分析结果自动生成测试用例',
          '确认测试(Confirmation Test)方案生成',
          '验证测试(Validation Test)方案生成',
          '测试覆盖率分析'
        ],
        history: []
      },
      automation: {
        id: 'automation',
        name: '自动化测试智能体',
        description: '执行测试用例和收集结果',
        icon: '⚙️',
        capabilities: [
          '基于测试方案自动生成测试插件',
          '自动化测试脚本生成和执行',
          '测试环境配置和管理',
          '测试结果收集和初步分析'
        ],
        history: []
      },
      report: {
        id: 'report',
        name: '报告分析智能体',
        description: '分析结果并生成综合报告',
        icon: '📊',
        capabilities: [
          '基于测试结果生成综合分析报告',
          '智能化问题识别和分类',
          '修复建议和优化方案',
          '合规性检查结果'
        ],
        history: []
      }
    },
    activeAgent: 'tara',
    chatHistory: {},
    settings: {
      modelConfig: {
        tara: {
          modelName: 'Claude-3.7-Sonnet',
          temperature: 0.7,
          maxTokens: 4000,
          tools: ['knowledge_base', 'analyzer', 'network_scanner']
        },
        test_case: {
          modelName: 'Claude-3.7-Sonnet',
          temperature: 0.5,
          maxTokens: 4000,
          tools: ['knowledge_base', 'test_generator', 'code_analyzer']
        },
        automation: {
          modelName: 'Claude-3.7-Sonnet',
          temperature: 0.3,
          maxTokens: 4000,
          tools: ['script_generator', 'test_executor', 'report_collector']
        },
        report: {
          modelName: 'Claude-3.7-Sonnet',
          temperature: 0.6,
          maxTokens: 4000,
          tools: ['knowledge_base', 'report_generator', 'data_analyzer']
        }
      }
    }
  }),
  
  getters: {
    getCurrentAgent: (state) => state.agents[state.activeAgent],
    getAgentList: (state) => Object.values(state.agents),
    getAgentById: (state) => (id) => state.agents[id],
    getAgentHistory: (state) => (id) => state.chatHistory[id] || [],
    getAgentSettings: (state) => (id) => state.settings.modelConfig[id] || {},
  },
  
  actions: {
    setActiveAgent(agentId) {
      if (this.agents[agentId]) {
        this.activeAgent = agentId;
      }
    },
    
    addMessageToHistory(agentId, message) {
      if (!this.chatHistory[agentId]) {
        this.chatHistory[agentId] = [];
      }
      
      this.chatHistory[agentId].push(message);
      
      // Save to localStorage
      localStorage.setItem(`chat_history_${agentId}`, JSON.stringify(this.chatHistory[agentId]));
    },
    
    clearAgentHistory(agentId) {
      this.chatHistory[agentId] = [];
      localStorage.removeItem(`chat_history_${agentId}`);
    },
    
    updateAgentSettings(agentId, settings) {
      if (this.settings.modelConfig[agentId]) {
        this.settings.modelConfig[agentId] = {
          ...this.settings.modelConfig[agentId],
          ...settings
        };
      }
    },
    
    initializeAgentData() {
      // Load chat history from localStorage for each agent
      Object.keys(this.agents).forEach(agentId => {
        const savedHistory = localStorage.getItem(`chat_history_${agentId}`);
        if (savedHistory) {
          try {
            this.chatHistory[agentId] = JSON.parse(savedHistory);
          } catch (e) {
            console.error(`Error parsing chat history for ${agentId}`, e);
            this.chatHistory[agentId] = [];
          }
        } else {
          this.chatHistory[agentId] = [];
        }
      });
    },
    
    async fetchAgentStatus(agentType) {
      this.loadingStatus = true;
      
      try {
        const response = await agentsAPI.getAgentStatus(agentType);
        this.agentStatus[agentType] = response.status;
        return response;
      } catch (error) {
        console.error(`Failed to fetch ${agentType} agent status:`, error);
        return { status: 'unknown' };
      } finally {
        this.loadingStatus = false;
      }
    },
    
    async fetchAllAgentStatus() {
      const agentTypes = ['tara', 'test_case', 'automation_test', 'report_analysis', 'knowledge_base'];
      
      for (const type of agentTypes) {
        await this.fetchAgentStatus(type);
      }
    },
    
    async fetchActiveTasks() {
      try {
        const response = await agentsAPI.getActiveTasks();
        this.activeTasks = response;
        return response;
      } catch (error) {
        console.error('Failed to fetch active tasks:', error);
        return [];
      }
    },
    
    async cancelTask(taskId) {
      try {
        await agentsAPI.cancelTask(taskId);
        // 更新活跃任务列表
        this.activeTasks = this.activeTasks.filter(task => task.id !== taskId);
        return true;
      } catch (error) {
        console.error(`Failed to cancel task ${taskId}:`, error);
        return false;
      }
    },
    
    addHistoryItem(item) {
      // 确保有必要的字段
      if (!item.query || !item.agentType || !item.timestamp) {
        item.timestamp = new Date().toISOString();
      }
      
      // 添加到历史记录前面
      this.history.unshift(item);
      
      // 保持历史记录不超过100条
      if (this.history.length > 100) {
        this.history = this.history.slice(0, 100);
      }
      
      // 保存到本地存储
      localStorage.setItem('agent_history', JSON.stringify(this.history));
    },
    
    clearHistory() {
      this.history = [];
      localStorage.removeItem('agent_history');
    }
  }
}); 