<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useRoleMenu } from '@/composables/useRoleMenu'
import { useAuthStore } from '@/stores/auth'
import { useGsapTransition } from '@/composables/useGsapTransition'
import HorizontalLayout from './HorizontalLayout.vue'
import VerticalLayout from './VerticalLayout.vue'

// 普通信息员 / 应急指挥人员：横排导航；资源管理员 / 系统管理员：竖排导航
const { isHorizontal } = useRoleMenu()
const auth = useAuthStore()
const { enterPage, transitionTheme } = useGsapTransition()

const rootRef = ref<HTMLElement | null>(null)

// 角色变化时（登录/切换账号）：1) 主题色脉冲过渡 2) 重新触发入场动画
watch(() => auth.roleKey, async () => {
  transitionTheme()
  await nextTick()
  // 等子布局渲染完再播入场（首次进入 immediate 也会走这里）
  setTimeout(() => enterPage(rootRef.value), 80)
}, { immediate: true })
</script>

<template>
  <div ref="rootRef" class="role-layout-root">
    <!-- 普通信息员 / 应急指挥人员：横排导航 -->
    <HorizontalLayout v-if="isHorizontal" />
    <!-- 资源管理员 / 系统管理员：竖排导航 -->
    <VerticalLayout v-else />
  </div>
</template>

<style scoped>
.role-layout-root {
  width: 100%;
  height: 100%;
}
</style>