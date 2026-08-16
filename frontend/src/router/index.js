import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  // 普通信息员 - 横向导航
  {
    path: '/reporter',
    component: () => import('@/layouts/HorizontalLayout.vue'),
    meta: { requiresAuth: true, roles: ['reporter'] },
    children: [
      {
        path: '',
        redirect: '/reporter/dashboard'
      },
      {
        path: 'dashboard',
        name: 'ReporterDashboard',
        component: () => import('@/views/reporter/Dashboard.vue'),
        meta: { title: '灾情态势大屏', icon: 'DataLine' }
      },
      {
        path: 'report',
        name: 'ReporterReport',
        component: () => import('@/views/reporter/Report.vue'),
        meta: { title: '灾情上报', icon: 'EditPen' }
      },
      {
        path: 'backend',
        name: 'ReporterBackend',
        component: () => import('@/views/reporter/BackendFunctions.vue'),
        meta: { title: '后端功能', icon: 'Cpu' }
      }
    ]
  },
  // 应急指挥人员 - 横向导航
  {
    path: '/commander',
    component: () => import('@/layouts/HorizontalLayout.vue'),
    meta: { requiresAuth: true, roles: ['commander'] },
    children: [
      {
        path: '',
        redirect: '/commander/dashboard'
      },
      {
        path: 'dashboard',
        name: 'CommanderDashboard',
        component: () => import('@/views/commander/Dashboard.vue'),
        meta: { title: '灾情态势大屏', icon: 'DataLine' }
      },
      {
        path: 'review',
        name: 'CommanderReview',
        component: () => import('@/views/commander/Review.vue'),
        meta: { title: '审核事件', icon: 'CircleCheck' }
      },
      {
        path: 'plan',
        name: 'CommanderPlan',
        component: () => import('@/views/commander/PlanWorkbench.vue'),
        meta: { title: '处置方案', icon: 'Document' }
      },
      {
        path: 'dispatch',
        name: 'CommanderDispatch',
        component: () => import('@/views/commander/DispatchBoard.vue'),
        meta: { title: '调度看板', icon: 'Share' }
      },
      {
        path: 'resources',
        name: 'CommanderResources',
        component: () => import('@/views/commander/ResourceQuery.vue'),
        meta: { title: '救援资源查询', icon: 'Search' }
      },
      {
        path: 'report',
        name: 'CommanderReport',
        component: () => import('@/views/reporter/Report.vue'),
        meta: { title: '灾情上报', icon: 'EditPen' }
      }
    ]
  },
  // 资源管理员 - 竖向导航
  {
    path: '/resource',
    component: () => import('@/layouts/VerticalLayout.vue'),
    meta: { requiresAuth: true, roles: ['resmanager'] },
    children: [
      {
        path: '',
        redirect: '/resource/dashboard'
      },
      {
        path: 'dashboard',
        name: 'ResourceDashboard',
        component: () => import('@/views/resource/Dashboard.vue'),
        meta: { title: '灾情态势大屏', icon: 'DataLine' }
      },
      {
        path: 'dispatch',
        name: 'ResourceDispatch',
        component: () => import('@/views/resource/DispatchManage.vue'),
        meta: { title: '调度看板', icon: 'Share' }
      }
    ]
  },
  // 系统管理员 - 竖向导航
  {
    path: '/admin',
    component: () => import('@/layouts/VerticalLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '灾情态势大屏', icon: 'DataLine' }
      },
      {
        path: 'knowledge',
        name: 'AdminKnowledge',
        component: () => import('@/views/admin/KnowledgeBase.vue'),
        meta: { title: '知识库管理', icon: 'Reading' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'models',
        name: 'AdminModels',
        component: () => import('@/views/admin/ModelManage.vue'),
        meta: { title: '模型管理', icon: 'Cpu' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const title = to.meta?.title ? `${to.meta.title} - 云南省自然灾害应急响应平台` : '云南省自然灾害应急响应平台'
  document.title = title

  if (to.meta?.requiresAuth && !userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta?.roles && userStore.userInfo?.role) {
    if (!to.meta.roles.includes(userStore.userInfo.role)) {
      next({ path: '/login' })
      return
    }
  }

  if (to.path === '/login' && userStore.isLoggedIn) {
    const rolePathMap = {
      reporter: '/reporter',
      commander: '/commander',
      resmanager: '/resource',
      admin: '/admin'
    }
    next(rolePathMap[userStore.userInfo.role] || '/login')
    return
  }

  next()
})

export default router
