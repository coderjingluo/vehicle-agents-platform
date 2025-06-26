<template>
  <div class="app-layout">
    <!-- 头部导航栏 -->
    <header class="app-header">
      <div class="logo-container">
        <el-icon class="logo-icon"><Monitor /></el-icon>
        <span class="logo-text">天工</span>
      </div>
      <div class="header-title">
        {{ currentPage }}
      </div>
      <div class="header-right">
        <div class="credits">
          <el-tooltip content="邀请好友赚积分" placement="bottom">
            <div class="credit-item invite">
              <el-icon><Present /></el-icon>
              邀请好友赚积分
            </div>
          </el-tooltip>
          <div class="credit-item amount">
            <el-icon><Coin /></el-icon>
            {{ credits }}
          </div>
          <div class="credit-item recharge" @click="$emit('recharge')">
            积分充值
          </div>
        </div>
        <div class="notification">
          <el-badge :value="notificationCount" class="notification-badge">
            <el-icon><Bell /></el-icon>
          </el-badge>
        </div>
        <div class="user-avatar" @click="showUserMenu = !showUserMenu">
          <el-avatar :size="32" :src="userAvatar"></el-avatar>
          <el-icon><ArrowDown /></el-icon>
          <div class="user-menu" v-if="showUserMenu">
            <ul>
              <li>个人设置</li>
              <li>退出登录</li>
            </ul>
          </div>
        </div>
      </div>
    </header>

    <!-- 侧边栏 -->
    <div class="app-content">
      <aside class="app-sidebar">
        <div class="sidebar-search">
          <el-input placeholder="搜索 (⌘+k)" prefix-icon="Search" />
        </div>
        <div class="sidebar-menu">
          <div class="menu-item" :class="{ active: isActive('/') }" @click="navigateTo('/')">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </div>
          <div class="menu-item" :class="{ active: isActive('/project/new') }" @click="navigateTo('/project/new')">
            <el-icon><Plus /></el-icon>
            <span>新建项目</span>
          </div>
          <div class="menu-group">
            <div class="group-title">项目</div>
            <div 
              class="menu-item project-item" 
              :class="{ active: isActive('/project/vehicle-security') }"
              @click="navigateTo('/project/vehicle-security')"
            >
              <el-icon><Monitor /></el-icon>
              <span>车联网网络安全综合智能体设计方案</span>
            </div>
            <div 
              class="menu-item project-item" 
              :class="{ active: isActive('/project/vehicle-test') }"
              @click="navigateTo('/project/vehicle-test')"
            >
              <el-icon><Monitor /></el-icon>
              <span>车联网网络安全智能测试用例</span>
            </div>
            <div 
              class="menu-item project-item" 
              :class="{ active: isActive('/project/vehicle-automation') }"
              @click="navigateTo('/project/vehicle-automation')"
            >
              <el-icon><Monitor /></el-icon>
              <span>车联网网络安全智能自动化测试</span>
            </div>
            <div 
              class="menu-item project-item" 
              :class="{ active: isActive('/project/vehicle-incident') }"
              @click="navigateTo('/project/vehicle-incident')"
            >
              <el-icon><Monitor /></el-icon>
              <span>车联网网络安全事件分析</span>
            </div>
          </div>
          <div class="menu-item" :class="{ active: isActive('/knowledge') }" @click="navigateTo('/knowledge')">
            <el-icon><Box /></el-icon>
            <span>知识库</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="app-main">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Bell, Present, Coin, HomeFilled, Plus, Monitor, Box, ArrowDown, Search } from '@element-plus/icons-vue';
import { useUserStore } from '@/stores';

// User states
const userStore = useUserStore();
const userAvatar = computed(() => userStore.userAvatar);
const credits = computed(() => userStore.credits || '1500');
const notificationCount = ref(1);
const showUserMenu = ref(false);

// Router
const router = useRouter();
const route = useRoute();

const navigateTo = (path) => {
  router.push(path);
};

const isActive = (path) => {
  if (path === '/') {
    return route.path === path;
  }
  return route.path.startsWith(path);
};

// Computed title based on current route
const currentPage = computed(() => {
  if (route.name === 'home') return '首页';
  if (route.name === 'chat') return route.params.agentType === 'tara' ? '车联网网络安全综合智能体设计方案' : '智能体对话';
  if (route.name === 'knowledge') return '知识库';
  return '智能体平台';
});
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #111215;
  color: #fff;
}

.app-header {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #2c2c2c;
  background-color: #111215;
}

.logo-container {
  display: flex;
  align-items: center;
  margin-right: 20px;
}

.logo-icon {
  font-size: 24px;
  color: #4080ff;
  margin-right: 8px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
}

.header-title {
  flex: 1;
  font-size: 16px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
}

.credits {
  display: flex;
  align-items: center;
  margin-right: 20px;
}

.credit-item {
  display: flex;
  align-items: center;
  margin-left: 15px;
  cursor: pointer;
}

.credit-item.invite {
  border-radius: 16px;
  background-image: linear-gradient(90deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%);
  padding: 2px 10px;
  color: #111215;
}

.credit-item.amount {
  color: #f8c93a;
}

.credit-item.recharge {
  color: #4080ff;
}

.notification {
  margin-right: 20px;
  cursor: pointer;
}

.notification :deep(.el-badge__content) {
  top: 5px;
  right: 5px;
}

.user-avatar {
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.user-avatar .el-icon {
  margin-left: 5px;
  font-size: 12px;
  transition: transform 0.3s;
}

.user-avatar:hover .el-icon {
  transform: rotate(180deg);
}

.user-menu {
  position: absolute;
  top: 45px;
  right: 0;
  width: 120px;
  background: #2c2c2c;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.user-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-menu li {
  padding: 10px 15px;
  cursor: pointer;
}

.user-menu li:hover {
  background-color: #3e3e3e;
}

.app-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 260px;
  border-right: 1px solid #2c2c2c;
  display: flex;
  flex-direction: column;
  padding: 15px;
  background-color: #111215;
  overflow-y: auto;
}

.sidebar-search {
  margin-bottom: 20px;
}

.sidebar-search :deep(.el-input__wrapper) {
  background-color: #2c2c2c;
  box-shadow: none;
  border-radius: 8px;
}

.sidebar-search :deep(.el-input__inner) {
  color: #fff;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 5px;
  transition: background-color 0.2s;
}

.menu-group {
  margin: 10px 0;
}

.group-title {
  padding: 5px 15px;
  color: #aaa;
  font-size: 12px;
}

.menu-item.project-item {
  padding-left: 30px;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-item.active {
  background-color: #3e3e3e;
}

.menu-item:hover {
  background-color: #2c2c2c;
}

.menu-item .el-icon {
  margin-right: 10px;
}

.app-main {
  flex: 1;
  overflow: auto;
  padding: 0;
  background-color: #111215;
}
</style>