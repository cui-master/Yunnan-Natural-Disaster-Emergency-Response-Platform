<script setup lang="ts">
<<<<<<< HEAD
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import UserCluster from './UserCluster.vue'

const route = useRoute()
const pageTitle = computed(() => (route.meta.title as string) || '云南省自然灾害应急响应平台')

const now = ref('')
let timer: number | null = null
function tick() {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  now.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(
    d.getMinutes()
  )}:${p(d.getSeconds())}`
}
onMounted(() => {
  tick()
  timer = window.setInterval(tick, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
=======
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { USE_MOCK } from '@/api/mock'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const pageTitle = computed(() => (route.meta.title as string) || '云南省自然灾害应急响应平台')

function logout() {
  auth.logout()
  router.push('/login')
}
>>>>>>> feature-cui
</script>

<template>
  <div class="header">
<<<<<<< HEAD
    <div class="left">
      <span class="bar"></span>
      <span class="title">{{ pageTitle }}</span>
      <span class="clock">{{ now }}</span>
    </div>
    <UserCluster />
=======
    <div class="title">{{ pageTitle }}</div>
    <div class="right">
      <el-tag v-if="USE_MOCK" type="warning" size="small" effect="plain">Mock 联调</el-tag>
      <el-tag v-else type="success" size="small" effect="plain">真实后端</el-tag>
      <el-dropdown @command="logout">
        <span class="user">
          <el-avatar :size="28">{{ (auth.realName || 'U')[0] }}</el-avatar>
          <span class="name">{{ auth.realName }}</span>
          <span class="role">{{ auth.roleName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
>>>>>>> feature-cui
  </div>
</template>

<style scoped>
.header {
<<<<<<< HEAD
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--ydr-border);
  box-shadow: 0 2px 10px oklch(24% 0.02 255 / 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  position: relative;
  z-index: 20;
}
.left {
=======
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.title {
  font-size: 17px;
  font-weight: 600;
  color: #1f2d3d;
}
.right {
>>>>>>> feature-cui
  display: flex;
  align-items: center;
  gap: 12px;
}
<<<<<<< HEAD
.bar {
  width: 4px;
  height: 18px;
  border-radius: 2px;
  background: var(--ydr-primary);
}
.title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--ydr-ink);
  letter-spacing: -0.01em;
}
.clock {
  font-size: 12px;
  color: var(--ydr-sub);
  font-variant-numeric: tabular-nums;
=======
.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.name {
  font-size: 14px;
  color: #303133;
}
.role {
  font-size: 12px;
  color: #909399;
>>>>>>> feature-cui
}
</style>
