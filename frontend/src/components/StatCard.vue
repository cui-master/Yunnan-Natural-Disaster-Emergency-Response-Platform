<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  suffix?: string
  color?: string
  icon?: string
}>()
</script>

<template>
  <div class="stat-card" :style="{ borderTopColor: color || '#c0392b' }">
    <div class="icon" :style="{ background: (color || '#c0392b') + '22', color: color || '#c0392b' }">
      <el-icon v-if="icon"><component :is="icon" /></el-icon>
    </div>
    <div class="meta">
      <div class="label">{{ title }}</div>
      <div class="value" :style="{ color: color || '#1f2d3d' }">
        {{ value }}<span class="suffix">{{ suffix }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 8px;
  border-top: 3px solid #c0392b;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.label {
  font-size: 13px;
  color: #909399;
}
.value {
  font-size: 24px;
  font-weight: 700;
}
.suffix {
  font-size: 13px;
  margin-left: 3px;
  color: #909399;
  font-weight: 400;
}
</style>
