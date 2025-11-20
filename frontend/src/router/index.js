import { createRouter, createWebHistory } from 'vue-router'

// 导入组件
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页', requiresAuth: true }
  },
  // 模型配置相关路由已整合到ModelTraining中
  {
    path: '/model-list',
    name: 'ModelList',
    component: () => import('../views/ModelList.vue'),
    meta: { title: '模型列表', requiresAuth: true }
  },
  {
    path: '/model-config',
    name: 'ModelConfig',
    component: () => import('../views/ModelConfig.vue'),
    meta: { title: '配置管理', requiresAuth: true }
  },
  {
    path: '/model-training',
    name: 'ModelTraining',
    component: () => import('../views/ModelTraining.vue'),
    meta: { title: '预测模型训练', requiresAuth: true }
  },
  // 数据库管理相关路由
  {
    path: '/database-connect',
    name: 'DatabaseConnect',
    component: () => import('../views/DatabaseConnect.vue'),
    meta: { title: '数据库连接', requiresAuth: true }
  },
  {
    path: '/data-select',
    name: 'DataSelect',
    component: () => import('../views/DataSelect.vue'),
    meta: { title: '数据选择', requiresAuth: true }
  },
  // 规则生成相关路由
  {
    path: '/rule-generate',
    name: 'RuleGenerate',
    component: () => import('../views/RuleGenerate.vue'),
    meta: { title: '规则生成', requiresAuth: true }
  },
  {
    path: '/rule-library',
    name: 'RuleLibrary',
    component: () => import('../views/RuleLibrary.vue'),
    meta: { title: '规则库管理', requiresAuth: true }
  },
  // 质量检测相关路由
  {
    path: '/quality-check',
    name: 'QualityCheck',
    component: () => import('../views/QualityCheck.vue'),
    meta: { title: '质量检测', requiresAuth: true }
  },
  {
    path: '/quality-report',
    name: 'QualityReport',
    component: () => import('../views/QualityReport.vue'),
    meta: { title: '检测报告', requiresAuth: true }
  },
  // 文本数据质检路由
  {
    path: '/llm-quality-check',
    name: 'LLMQualityCheck',
    component: () => import('../views/LLMQualityCheck.vue'),
    meta: { title: '文本数据质检', requiresAuth: true }
  },
  // 井名白名单管理路由
  {
    path: '/well-whitelist',
    name: 'WellWhitelist',
    component: () => import('../views/WellWhitelist.vue'),
    meta: { title: '井名白名单管理', requiresAuth: true }
  },
  // 钻井数据质检路由
  {
    path: '/drilling-data',
    name: 'DrillingData',
    component: () => import('../views/DrillingData.vue'),
    meta: { title: '钻井数据质检', requiresAuth: true }
  },
  // 生产数据质检路由
  {
    path: '/product-data',
    name: 'ProductData',
    component: () => import('../views/ProductData.vue'),
    meta: { title: '生产数据质检', requiresAuth: true }
  },

]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 从sessionStorage检查登录状态
  const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
  
  // 检查URL中是否有SSO token参数
  const hasToken = to.query.token || to.query.ssoToken || to.query.accessToken
  
  // 如果URL中有SSO token，直接允许访问（SSO模式）
  if (hasToken) {
    console.log('检测到SSO token，允许直接访问')
    next()
    return
  }
  
  // 如果路由需要认证但用户未登录（非SSO模式）
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
  }
  // 如果用户已登录且访问登录页，跳转到首页
  else if (to.path === '/login' && isLoggedIn) {
    next('/')
  }
  // 其他情况正常跳转
  else {
    next()
  }
})

export default router 