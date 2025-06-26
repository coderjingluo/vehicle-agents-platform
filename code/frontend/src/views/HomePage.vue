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
                <el-dropdown>
                  <div class="dropdown-label">
                    <el-icon><Setting /></el-icon>
                    <span>通用场景</span>
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </div>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item>TARA分析</el-dropdown-item>
                      <el-dropdown-item>测试用例生成</el-dropdown-item>
                      <el-dropdown-item>自动化测试</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
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
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Setting, Connection, ArrowDown, ArrowRight } from '@element-plus/icons-vue';
import AppLayout from '@/components/Layout/AppLayout.vue';
import { useUserStore } from '@/stores';

const router = useRouter();
const userStore = useUserStore();
const userInput = ref('');
const activeMode = ref('tara');

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

.submit-button {
  margin-left: auto;
}

.submit-button :deep(.el-button) {
  background-color: #4080ff;
  padding: 12px;
}

.network-button :deep(.el-button) {
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
</style> 