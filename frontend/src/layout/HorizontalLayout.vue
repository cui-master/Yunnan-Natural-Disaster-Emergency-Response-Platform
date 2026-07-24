<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoleMenu } from '@/composables/useRoleMenu'
import { useAuthStore } from '@/stores/auth'
import UserCluster from './UserCluster.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { themeClass, meta, menuRoutes } = useRoleMenu()

// 指挥员=深色指挥风；信息员=浅色青绿风
const dark = computed(() => auth.roleKey === 'ROLE_COMMANDER')

// 角色签名
const ROLE_SIG: Record<string, { emoji: string; label: string }> = {
  ROLE_REPORTER:  { emoji: '🌿', label: '一线 · 上报台' },
  ROLE_COMMANDER: { emoji: '🎯', label: '指挥 · 中枢'   },
  ROLE_RESMGR:    { emoji: '📦', label: '资源 · 调度台' },
  ROLE_ADMIN:     { emoji: '⚙️', label: '系统 · 控制台' }
}
const emoji = computed(() => ROLE_SIG[auth.roleKey]?.emoji || '⚠')
const signatureLabel = computed(() => ROLE_SIG[auth.roleKey]?.label || '云南应急')

const activeMenu = computed(() => route.path)
function handleSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="role-shell" :class="[themeClass, dark ? 'htop--dark' : 'htop--light']">
    <!-- 横排顶部导航 -->
    <header class="htop">
      <div class="hbrand">
        <span class="hbadge">{{ emoji }}</span>
        <div class="hbrand-text">
          <div class="hbrand-name">{{ meta.brand }}</div>
          <div class="hbrand-sub">{{ meta.sub }}</div>
        </div>
      </div>

      <el-menu
        class="hmenu"
        mode="horizontal"
        :default-active="activeMenu"
        :ellipsis="false"
        @select="handleSelect"
      >
        <el-menu-item v-for="m in menuRoutes" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>

      <div class="hright">
        <span class="role-signature">{{ signatureLabel }}</span>
        <span class="hmode">{{ meta.backend }}</span>
        <UserCluster />
      </div>
    </header>

    <main class="main">
      <keep-alive max="10">
        <RouterView />
      </keep-alive>
    </main>
  </div>
</template>

<style scoped>
.role-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--ydr-bg);
}

/* ===== 顶部横排导航 ===== */
.htop {
  position: relative;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 18px;
  height: 64px;
  padding: 0 22px;
  flex-shrink: 0;
}
.hbrand {
  display: flex;
  align-items: center;
  gap: 11px;
  flex-shrink: 0;
}
.hbadge {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  background: var(--role-sidebar-grad);
  box-shadow: 0 4px 12px oklch(50% 0.2 25 / 0.32);
}
.hbrand-text {
  min-width: 0;
}
.hbrand-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.2px;
}
.hbrand-sub {
  font-size: 11px;
  margin-top: 1px;
  white-space: nowrap;
}
.hmenu {
  flex: 1;
  min-width: 0;
  border-bottom: none !important;
  background: transparent !important;
}
.hmenu :deep(.el-menu-item) {
  height: 64px;
  line-height: 64px;
  border-bottom: 3px solid transparent;
  font-size: 14.5px;
  font-weight: 600;
  transition: color 0.18s var(--ease-out-quart), border-color 0.18s var(--ease-out-quart);
}
.hmenu :deep(.el-menu-item .el-icon) {
  margin-right: 6px;
  font-size: 17px;
}
.hmenu :deep(.el-menu-item.is-active) {
  border-bottom-color: var(--ydr-primary);
}
.hright {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.hmode {
  font-size: 11.5px;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}

/* —— 深色指挥风（指挥员） —— */
.htop--dark .htop {
  background: linear-gradient(180deg, #0e1b2e 0%, #16263a 100%);
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.28);
}
.htop--dark .hbrand-name {
  color: #fff;
}
.htop--dark .hbrand-sub {
  color: var(--role-sidebar-muted);
}
.htop--dark .hmenu :deep(.el-menu-item) {
  color: var(--role-sidebar-text);
}
.htop--dark .hmenu :deep(.el-menu-item:hover) {
  color: #fff;
}
.htop--dark .hmenu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: transparent;
}
.htop--dark .hmode {
  color: #cdd6e3;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* —— 浅色青绿风（信息员） —— */
.htop--light .htop {
  background: #fff;
  border-bottom: 1px solid var(--ydr-border);
  box-shadow: 0 2px 10px oklch(24% 0.02 255 / 0.05);
}
.htop--light .hbrand-name {
  color: var(--ydr-ink);
}
.htop--light .hbrand-sub {
  color: var(--ydr-sub);
}
.htop--light .hmenu :deep(.el-menu-item) {
  color: var(--ydr-text);
}
.htop--light .hmenu :deep(.el-menu-item:hover) {
  color: var(--ydr-primary);
}
.htop--light .hmenu :deep(.el-menu-item.is-active) {
  color: var(--ydr-primary);
}
.htop--light .hmode {
  color: var(--ydr-primary-dark, #0b7d79);
  background: var(--ydr-primary-soft);
}

.main {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 18px 22px;
  background: var(--ydr-bg);
}
</style>
