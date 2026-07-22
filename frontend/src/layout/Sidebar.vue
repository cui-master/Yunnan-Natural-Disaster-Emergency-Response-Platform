<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { routes } from '@/router'
import { useAuthStore } from '@/stores/auth'
import type { MenuMeta } from '@/router'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// 从路由表提取需鉴权的子菜单，并按角色过滤
const menuRoutes = computed(() => {
  const root = routes.find((r) => r.path === '/')
  const children = (root?.children || []).filter((r) => r.path !== '')
  return children
    .map((r) => ({
      path: '/' + r.path,
      title: (r.meta?.title as string) || r.name,
      icon: (r.meta?.icon as string) || 'Menu',
      roles: (r.meta?.roles as string[]) || []
    }))
    .filter((m) => {
      if (!m.roles.length) return true
      return m.roles.some((role) => auth.hasRole(role))
    })
})

const activeMenu = computed(() => route.path)

function handleSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="sidebar">
    <div class="logo">
      <span class="logo-icon">⚠</span>
      <span class="logo-text">云南应急</span>
    </div>
    <el-scrollbar>
      <el-menu :default-active="activeMenu" router :collapse="false" @select="handleSelect">
        <el-menu-item v-for="m in menuRoutes" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1f2d3d;
}
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo-icon {
  color: #e74c3c;
  font-size: 20px;
}
.sidebar :deep(.el-menu) {
  border-right: none;
  background: #1f2d3d;
}
.sidebar :deep(.el-menu-item) {
  color: #c0c4cc;
}
.sidebar :deep(.el-menu-item.is-active) {
  background: #c0392b;
  color: #fff;
}
.sidebar :deep(.el-menu-item:hover) {
  background: #2c3e50;
}
</style>
