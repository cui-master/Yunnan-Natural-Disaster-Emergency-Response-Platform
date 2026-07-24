<<<<<<< HEAD
<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
=======
<template>
  <div v-if="route.path !== '/login'" class="layout">
    <header class="topbar">
      <span class="logo">云南应急协同决策平台</span>
      <nav>
        <router-link to="/">事件看板</router-link>
        <router-link v-if="auth.roleKey === 'ROLE_REPORTER'" to="/report">灾情上报</router-link>
        <router-link v-if="auth.roleKey === 'ROLE_RESMGR'" to="/resources">资源调度</router-link>
      </nav>
      <span class="user">
        {{ auth.realName }}（{{ auth.roleName }}）
        <el-button link @click="logout">退出</el-button>
      </span>
    </header>
    <main class="page"><router-view /></main>
  </div>
  <router-view v-else />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuth } from './stores/auth'
import { onMounted } from 'vue'

const route = useRoute()
const auth = useAuth()
>>>>>>> feature-cui

onMounted(async () => {
  if (auth.token) {
    await auth.fetchMe()
  }
})
<<<<<<< HEAD
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
=======

function logout() {
  auth.logout()
  location.href = '/#/login'
}
</script>
>>>>>>> feature-cui
