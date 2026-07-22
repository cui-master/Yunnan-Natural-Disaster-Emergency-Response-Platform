<script setup lang="ts">
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
</script>

<template>
  <div class="header">
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
  </div>
</template>

<style scoped>
.header {
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
  display: flex;
  align-items: center;
  gap: 12px;
}
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
}
</style>
