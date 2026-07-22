<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import type { DisasterEvent } from '@/types'

const props = defineProps<{
  events: DisasterEvent[]
  center?: [number, number]
  zoom?: number
}>()

const mapEl = ref<HTMLDivElement>()
let map: L.Map | null = null
let layer: L.LayerGroup | null = null

const levelColor: Record<string, string> = {
  I: '#7b241c',
  II: '#c0392b',
  III: '#e67e22',
  IV: '#f1c40f'
}
const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震',
  FLOOD: '洪涝',
  LANDSLIDE: '滑坡',
  DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱',
  FOREST_FIRE: '森林火灾',
  HAIL: '冰雹',
  TYPHOON: '台风'
}

function renderMarkers() {
  if (!map) return
  if (layer) layer.remove()
  layer = L.layerGroup().addTo(map)
  props.events.forEach((e) => {
    const color = levelColor[e.level] || '#999'
    const icon = L.divIcon({
      className: 'ydr-marker',
      html: `<div style="width:18px;height:18px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 0 2px ${color}55"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    })
    const marker = L.marker([e.geo.lat, e.geo.lng], { icon })
    marker.bindTooltip(
      `<b>${e.title}</b><br/>等级：${e.level} 级<br/>状态：${e.status}<br/>影响人口：${e.affectedPopulation || 0}`,
      { direction: 'top' }
    )
    marker.bindPopup(
      `<div style="min-width:200px"><b>${e.title}</b><br/>
       类型：${typeLabel[e.type]}<br/>等级：${e.level}<br/>
       位置：${e.location}<br/>描述：${e.description}</div>`
    )
    layer!.addLayer(marker)
  })
}

onMounted(() => {
  map = L.map(mapEl.value as HTMLDivElement, {
    center: props.center || [25.04, 101.5],
    zoom: props.zoom || 7,
    attributionControl: false
  })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18
  }).addTo(map)
  renderMarkers()
})

watch(
  () => props.events,
  () => renderMarkers(),
  { deep: true }
)

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div ref="mapEl" class="map"></div>
</template>

<style scoped>
.map {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}
</style>
