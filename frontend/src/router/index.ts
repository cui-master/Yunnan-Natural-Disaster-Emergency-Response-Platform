import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Login from '../views/Login.vue'
import RoleLayout from '../layout/RoleLayout.vue'
import { useAuthStore } from '../stores/auth'
import type { RoleCode } from '../types'

// 增强 vue-router 的 RouteMeta，使路由表可直接携带 title/icon/roles
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    icon?: string
    roles?: RoleCode[]
    requiresAuth?: boolean
  }
}

export interface MenuMeta {
  title: string
  icon: string
  roles: RoleCode[]
  requiresAuth?: boolean
}

const routes: RouteRecordRaw[] = [
  { path: '/login', component: Login, meta: { title: '登录' } },
  {
    path: '/',
    component: RoleLayout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        component: () => import('../views/dashboard/DisasterDashboard.vue'),
        meta: { title: '灾情态势大屏', icon: 'DataLine', roles: [], requiresAuth: true }
      },
      {
        // 普通信息员：上报灾情（唯一上报入口）
        path: 'report',
        component: () => import('../views/report/DisasterReport.vue'),
        meta: { title: '灾情上报', icon: 'Upload', roles: ['ROLE_REPORTER'], requiresAuth: true }
      },
      {
        // 应急指挥人员：审核事件
        path: 'review',
        component: () => import('../views/report/ReviewWorkbench.vue'),
        meta: { title: '信息审核', icon: 'Stamp', roles: ['ROLE_COMMANDER'], requiresAuth: true }
      },
      {
        // 应急指挥人员：生成处置方案（API + Dify）
        path: 'plan',
        component: () => import('../views/plan/PlanWorkbench.vue'),
        meta: { title: '应急方案', icon: 'MagicStick', roles: ['ROLE_COMMANDER'], requiresAuth: true }
      },
      {
        // 资源管理员：维护人员/车辆/物资/避难场所
        path: 'resources',
        component: () => import('../views/resource/ResourceQuery.vue'),
        meta: { title: '资源管理', icon: 'Box', roles: ['ROLE_RESMGR', 'ROLE_COMMANDER'], requiresAuth: true }
      },
      {
        // 资源管理员：调度看板
        path: 'dispatch',
        component: () => import('../views/resource/DispatchBoard.vue'),
        meta: { title: '调度看板', icon: 'Promotion', roles: ['ROLE_RESMGR', 'ROLE_COMMANDER'], requiresAuth: true }
      },
      {
        // 系统管理员：知识库（Dify 桥接）
        path: 'knowledge',
        component: () => import('../views/knowledge/KnowledgeManage.vue'),
        meta: { title: '知识库', icon: 'Reading', roles: ['ROLE_ADMIN'], requiresAuth: true }
      },
      {
        // 系统管理员：审计日志
        path: 'audit',
        component: () => import('../views/audit/AuditLog.vue'),
        meta: { title: '审计日志', icon: 'Document', roles: ['ROLE_ADMIN'], requiresAuth: true }
      },
      {
        // 系统管理员：用户/模型/数据源
        path: 'system',
        component: () => import('../views/system/SystemManage.vue'),
        meta: { title: '系统管理', icon: 'Setting', roles: ['ROLE_ADMIN'], requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const meta = to.meta as Partial<MenuMeta>
  if (meta.requiresAuth && !auth.token) {
    next('/login')
    return
  }
  if (meta.roles && (meta.roles as RoleCode[]).length && !auth.hasRole((meta.roles as RoleCode[])[0]) && !(meta.roles as RoleCode[]).some((r) => auth.hasRole(r))) {
    next('/dashboard')
    return
  }
  next()
})

export default router
export { routes }
