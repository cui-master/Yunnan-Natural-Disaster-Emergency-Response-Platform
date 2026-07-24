<script setup lang="ts">
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
</script>

<template>
  <div class="header">
    <div class="left">
      <span class="bar"></span>
      <span class="title">{{ pageTitle }}</span>
      <span class="clock">{{ now }}</span>
    </div>
    <UserCluster />
  </div>
</template>

<style scoped>
.header {
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
  display: flex;
  align-items: center;
  gap: 12px;
}
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
}
</style>
