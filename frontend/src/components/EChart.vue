<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{ option: Record<string, unknown>; height?: string }>()
const el = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
let ro: ResizeObserver | null = null

function resize() {
  chart.value?.resize()
}

onMounted(() => {
  chart.value = echarts.init(el.value as HTMLDivElement)
  chart.value.setOption(props.option)
  window.addEventListener('resize', resize)
  // 容器尺寸变化（flex 布局/响应式）时同步重绘，避免图表被压成 0 高
  if (typeof ResizeObserver !== 'undefined' && el.value) {
    ro = new ResizeObserver(() => resize())
    ro.observe(el.value)
  }
})

watch(
  () => props.option,
  (opt) => chart.value?.setOption(opt, true),
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  ro?.disconnect()
  chart.value?.dispose()
})
</script>

<template>
  <div ref="el" :style="{ width: '100%', height: height || '300px' }"></div>
</template>
