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
import { connectWs } from './utils/ws'

const route = useRoute()
const auth = useAuth()

onMounted(async () => {
  if (auth.token) {
    await auth.fetchMe()
    connectWs((m) => {
      if (m.type === 'NEW_INCIDENT' || m.type === 'INCIDENT_STATUS') {
        window.dispatchEvent(new CustomEvent('incident-update'))
      }
    })
  }
})

function logout() {
  auth.logout()
  location.href = '/#/login'
}
</script>
