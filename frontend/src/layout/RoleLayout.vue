<script setup lang="ts">
import { useRoleMenu } from '@/composables/useRoleMenu'
import HorizontalLayout from './HorizontalLayout.vue'
import VerticalLayout from './VerticalLayout.vue'

// 普通信息员 / 应急指挥人员：横排导航；资源管理员 / 系统管理员：竖排导航
const { isHorizontal } = useRoleMenu()
</script>

<template>
  <!-- 普通信息员 / 应急指挥人员：横排导航 -->
  <HorizontalLayout v-if="isHorizontal" />
  <!-- 资源管理员 / 系统管理员：竖排导航 -->
  <VerticalLayout v-else />
</template>
