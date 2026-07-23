<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoleMenu } from '@/composables/useRoleMenu'
import { useAuthStore } from '@/stores/auth'
import HeaderBar from './HeaderBar.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { themeClass, meta, menuRoutes } = useRoleMenu()

const activeMenu = computed(() => route.path)
function handleSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="role-shell" :class="themeClass">
    <aside class="side">
      <div class="rail"></div>
      <div class="brand">
        <span class="logo"><span class="badge">⚠</span></span>
        <div class="brand-text">
          <div class="brand-name">{{ meta.brand }}</div>
          <div class="brand-sub">{{ meta.sub }}</div>
        </div>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu :default-active="activeMenu" router :collapse="false" @select="handleSelect">
          <el-menu-item v-for="m in menuRoutes" :key="m.path" :index="m.path">
            <el-icon><component :is="m.icon" /></el-icon>
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
      <div class="side-foot">
        <span class="dot"></span>
        <span class="foot-text">{{ auth.realName }} · {{ auth.roleName }}</span>
      </div>
    </aside>

    <div class="content">
      <HeaderBar />
      <main class="main">
        <keep-alive max="10">
          <RouterView />
        </keep-alive>
      </main>
    </div>
  </div>
</template>

<style scoped>
.role-shell {
  display: flex;
  height: 100vh;
  background: var(--ydr-bg);
}
.side {
  position: relative;
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--role-sidebar-bg, #16202e);
  overflow: hidden;
}
.rail {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: var(--ydr-primary);
}
.brand {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 11px;
  height: 64px;
  padding: 0 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo .badge {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--role-sidebar-grad);
  color: #fff;
  font-size: 18px;
  box-shadow: 0 4px 12px oklch(50% 0.18 25 / 0.35);
}
.brand-text {
  min-width: 0;
}
.brand-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.2px;
  white-space: nowrap;
}
.brand-sub {
  font-size: 11px;
  color: var(--role-sidebar-muted);
  margin-top: 2px;
  white-space: nowrap;
}
.menu-scroll {
  flex: 1;
  min-height: 0;
}
.side :deep(.el-menu) {
  border-right: none;
  background: transparent;
  padding: 10px 10px;
}
.side :deep(.el-menu-item) {
  position: relative;
  color: var(--role-sidebar-text);
  border-radius: 9px;
  margin-bottom: 5px;
  height: 46px;
  transition: background 0.18s var(--ease-out-quart), color 0.18s var(--ease-out-quart);
}
.side :deep(.el-menu-item .el-icon) {
  font-size: 17px;
}
.side :deep(.el-menu-item.is-active) {
  background: var(--role-sidebar-grad);
  color: #fff;
  box-shadow: 0 6px 16px oklch(50% 0.2 25 / 0.3);
}
.side :deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 2px;
  background: #fff;
}
.side :deep(.el-menu-item:hover) {
  background: var(--role-sidebar-hover);
  color: #fff;
}
.side-foot {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 12px 18px;
  font-size: 11px;
  color: var(--role-sidebar-muted);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.side-foot .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2ecc71;
  box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
  flex-shrink: 0;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.main {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 16px;
  background: var(--ydr-bg);
}
</style>
