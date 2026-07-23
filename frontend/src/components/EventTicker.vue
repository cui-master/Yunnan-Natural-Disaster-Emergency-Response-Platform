<script setup lang="ts">
import { computed } from 'vue'
import type { RealtimeEvent } from '@/types'

const props = defineProps<{ events: RealtimeEvent[]; connected: boolean }>()

const typeMeta: Record<string, { label: string; color: string }> = {
  NEW: { label: '新增', color: '#c0392b' },
  STATUS_CHANGE: { label: '状态变更', color: '#e67e22' },
  DISPATCH: { label: '调度', color: '#2980b9' },
  PLAN: { label: '方案', color: '#27ae60' }
}

const list = computed(() => props.events.slice(0, 30))
</script>

<template>
  <div class="ticker">
    <div class="ticker-head">
      <span class="live" :class="{ on: connected }">
        <span class="dot"></span>{{ connected ? '实时连接' : '模拟推送' }}
      </span>
      <span class="count">近 {{ list.length }} 条</span>
    </div>
    <el-scrollbar class="ticker-body">
      <transition-group name="fade" tag="div">
        <div v-for="e in list" :key="e.id" class="item">
          <span class="tag" :style="{ background: typeMeta[e.type]?.color + '22', color: typeMeta[e.type]?.color }">
            {{ typeMeta[e.type]?.label }}
          </span>
          <span class="msg">{{ e.message }}</span>
          <span class="time">{{ e.createdAt.slice(11, 19) }}</span>
        </div>
      </transition-group>
      <div v-if="!list.length" class="empty">暂无实时事件</div>
    </el-scrollbar>
  </div>
</template>

<style scoped>
.ticker {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.ticker-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.live {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 5px;
}
.live .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #bdc3c7;
}
.live.on .dot {
  background: #27ae60;
  box-shadow: 0 0 0 3px #27ae6033;
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 #27ae6066;
  }
  100% {
    box-shadow: 0 0 0 6px #27ae6000;
  }
}
.count {
  font-size: 12px;
  color: #c0c4cc;
}
.ticker-body {
  flex: 1;
}
.item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px dashed #f2f2f2;
  font-size: 13px;
}
.tag {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.msg {
  flex: 1;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.time {
  flex-shrink: 0;
  color: #c0c4cc;
  font-size: 11px;
}
.empty {
  text-align: center;
  color: #c0c4cc;
  padding: 20px;
  font-size: 13px;
}
.fade-enter-active {
  transition: all 0.4s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
