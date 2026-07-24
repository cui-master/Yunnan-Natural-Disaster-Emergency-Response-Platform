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
  <!-- 不在顶层使用路由过渡：Login↔RoleLayout(含 Leaflet 大屏) 的离场过渡
       在重型组件上 transitionend 不可靠触发，会导致新页面不挂载而白屏(需刷新)。
       页面级微动效(ydr-rise 等)保留在各自组件内。 -->
  <router-view v-slot="{ Component }">
    <component :is="Component" />
  </router-view>
</template>
