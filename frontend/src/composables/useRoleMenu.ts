import { computed } from 'vue'
import { routes } from '@/router'
import { useAuthStore } from '@/stores/auth'
import type { RoleCode } from '@/types'

export interface RoleMenuMeta {
  brand: string
  sub: string
  /** 该角色的后端连接方式（用于界面提示/记忆） */
  backend: string
  /** 导航形态：horizontal=横排，vertical=竖排 */
  nav: 'horizontal' | 'vertical'
}

export const ROLE_META: Record<RoleCode, RoleMenuMeta> = {
  ROLE_REPORTER: {
    brand: '一线上报台',
    sub: '灾情采集 · 快速上报',
    backend: 'Neo4j（灾情图数据库）',
    nav: 'horizontal'
  },
  ROLE_COMMANDER: {
    brand: '指挥中枢',
    sub: '审核事件 · 生成处置方案',
    backend: 'REST API + Dify（RAG 研判）',
    nav: 'horizontal'
  },
  ROLE_RESMGR: {
    brand: '资源调度台',
    sub: '人员 · 车辆 · 物资 · 避难场所',
    backend: 'Neo4j（资源关系图）',
    nav: 'vertical'
  },
  ROLE_ADMIN: {
    brand: '系统控制台',
    sub: '知识库 · 用户 · 模型 · 数据源',
    backend: 'REST API + Dify（知识库）',
    nav: 'vertical'
  }
}

export function useRoleMenu() {
  const auth = useAuthStore()

  const themeClass = computed(() => 'theme-' + (auth.roleKey || 'commander'))
  const meta = computed(() => ROLE_META[(auth.roleKey as RoleCode)] || ROLE_META.ROLE_COMMANDER)
  const isHorizontal = computed(() => meta.value.nav === 'horizontal')

  // 按角色过滤菜单 —— 不同角色看到不同导航（导航不复用）
  const menuRoutes = computed(() => {
    const root = routes.find((r) => r.path === '/')
    const children = (root?.children || []).filter((r) => r.path !== '')
    return children
      .map((r) => ({
        path: '/' + r.path,
        title: (r.meta?.title as string) || (r.name as string) || r.path,
        icon: (r.meta?.icon as string) || 'Menu',
        roles: (r.meta?.roles as string[]) || []
      }))
      .filter((m) => {
        if (!m.roles.length) return true
        return m.roles.some((role) => auth.hasRole(role))
      })
  })

  return { themeClass, meta, isHorizontal, menuRoutes }
}
