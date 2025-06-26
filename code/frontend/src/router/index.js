import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomePage.vue'),
    meta: {
      title: '首页 - 智能体平台'
    }
  },
  {
    path: '/chat/:agentType',
    name: 'chat',
    component: () => import('../views/ChatPage.vue'),
    meta: {
      title: '智能体对话'
    }
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('../views/KnowledgePage.vue'),
    meta: {
      title: '知识库管理'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '车联网安全智能体平台'
  next()
})

export default router 