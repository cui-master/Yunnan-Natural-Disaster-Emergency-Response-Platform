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
  <div class="stat-card" :style="{ '--accent': color || '#e03e2f' }">
    <div
      class="icon"
      :style="{ background: (color || '#e03e2f') + '1f', color: color || '#e03e2f' }"
    >
      <el-icon v-if="icon"><component :is="icon" /></el-icon>
    </div>
    <div class="meta">
      <div class="label">{{ title }}</div>
      <div class="value" :style="{ color: color || 'var(--ydr-ink)' }">
        {{ value }}<span class="suffix">{{ suffix }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  --accent: #e03e2f;
  position: relative;
  background: #fff;
  border: 1px solid var(--ydr-border);
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--ydr-shadow);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--accent);
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--ydr-shadow-lg);
}
.icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}
.label {
  font-size: var(--fs-sm);
  color: var(--ydr-sub);
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.value {
  font-family: var(--font-display);
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--ydr-ink);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.suffix {
  font-size: var(--fs-sm);
  margin-left: 3px;
  color: var(--ydr-sub);
  font-weight: 500;
  letter-spacing: 0;
}
</style>
