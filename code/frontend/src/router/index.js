import { createRouter, createWebHistory } from 'vue-router'

// 主要页面组件
const Dashboard = () => import('../views/Dashboard.vue')
const WorkflowManager = () => import('../views/WorkflowManager.vue')
const KnowledgeBase = () => import('../views/KnowledgeBase.vue')
const ModelConfig = () => import('../views/ModelConfig.vue')
const Settings = () => import('../views/Settings.vue')
const NotFound = () => import('../views/NotFound.vue')

// 智能体页面
const TARAAgent = () => import('../views/agents/TARAAgent.vue')
const TestCaseAgent = () => import('../views/agents/TestCaseAgent.vue')
const AutomationAgent = () => import('../views/agents/AutomationAgent.vue')
const ReportAgent = () => import('../views/agents/ReportAgent.vue')
const KnowledgeAgent = () => import('../views/agents/KnowledgeAgent.vue')

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'KunlunSec AI Platform',
      icon: 'House'
    }
  },
  {
    path: '/workflow',
    name: 'WorkflowManager',
    component: WorkflowManager,
    meta: {
      title: '工作流管理',
      icon: 'Share'
    }
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: KnowledgeBase,
    meta: {
      title: '知识库',
      icon: 'Notebook'
    }
  },
  {
    path: '/mcp-tools',
    name: 'MCPTools',
    component: ModelConfig,
    meta: {
      title: 'MCP工具管理',
      icon: 'Setting'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      icon: 'Tools'
    }
  },
  // 智能体路由
  {
    path: '/agents/tara',
    name: 'TARAAgent',
    component: TARAAgent,
    meta: {
      title: 'TARA智能体',
      icon: 'Lock',
      agentType: 'tara'
    }
  },
  {
    path: '/agents/testcase',
    name: 'TestCaseAgent',
    component: TestCaseAgent,
    meta: {
      title: '测试用例智能体',
      icon: 'DocumentChecked',
      agentType: 'testcase'
    }
  },
  {
    path: '/agents/automation',
    name: 'AutomationAgent',
    component: AutomationAgent,
    meta: {
      title: '自动化测试智能体',
      icon: 'Cpu',
      agentType: 'automation'
    }
  },
  {
    path: '/agents/report',
    name: 'ReportAgent',
    component: ReportAgent,
    meta: {
      title: '报告分析智能体',
      icon: 'Document',
      agentType: 'report'
    }
  },
  {
    path: '/agents/knowledge',
    name: 'KnowledgeAgent',
    component: KnowledgeAgent,
    meta: {
      title: '知识库智能体',
      icon: 'Search',
      agentType: 'knowledge'
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 车联网安全平台`
  }
  
  next()
})

// 获取智能体路由的辅助函数
export function getAgentRoutes() {
  return routes.filter(route => route.meta?.agentType)
}

export default router 