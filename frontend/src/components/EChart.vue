<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, shallowRef } from 'vue'
// 按需引入 ECharts：仅注册本项目实际用到的图表与组件（pie/bar/line + tooltip/legend/grid + axisPointer + Canvas 渲染器）
// 相比 `import * as echarts from 'echarts'` 全量引入，可显著减小打包体积。
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  AxisPointerComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  AxisPointerComponent,
  CanvasRenderer
])

const props = defineProps<{ option: Record<string, unknown>; height?: string }>()
const el = ref<HTMLDivElement>()
const chart = shallowRef<ReturnType<typeof echarts.init>>()

function resize() {
  chart.value?.resize()
}

onMounted(() => {
  chart.value = echarts.init(el.value as HTMLDivElement)
  chart.value.setOption(props.option)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  (opt) => chart.value?.setOption(opt, true),
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart.value?.dispose()
})
</script>

<template>
  <div ref="el" :style="{ width: '100%', height: height || '300px' }"></div>
</template>
