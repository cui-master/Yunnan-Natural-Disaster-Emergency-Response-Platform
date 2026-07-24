<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()

onMounted(async () => {
  if (auth.token) {
    await auth.fetchMe()
  }
})
</script>

<template>
  <!--
    路由切换动画由 GSAP 主导（见 useGsapTransition.ts）。
    这里保留一个极简的 opacity 兜底 transition，避免和 gsap 的 transform 冲突。
  -->
  <router-view v-slot="{ Component, route }">
    <transition name="route-fade" mode="out-in">
      <div :key="route.path" class="route-stage">
        <component :is="Component" />
      </div>
    </transition>
  </router-view>
</template>

<style scoped>
.route-stage {
  width: 100%;
  min-height: 100%;
}
.route-fade-enter-active,
.route-fade-leave-active {
  transition: opacity 0.18s ease;
}
.route-fade-enter-from,
.route-fade-leave-to {
  opacity: 0;
}
</style>