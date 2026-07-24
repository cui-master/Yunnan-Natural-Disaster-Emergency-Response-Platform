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
let legendEl: HTMLDivElement | null = null

const levelColor: Record<string, string> = {
  I: '#7b241c',
  II: '#c0392b',
  III: '#e67e22',
  IV: '#f1c40f'
}
const levelLabel: Record<string, string> = {
  I: 'Ⅰ级 特别重大',
  II: 'Ⅱ级 重大',
  III: 'Ⅲ级 较大',
  IV: 'Ⅳ级 一般'
}
const typeIcon: Record<string, string> = {
  EARTHQUAKE: '🌐', FLOOD: '🌊', LANDSLIDE: '⛰️', DEBRIS_FLOW: '🪨',
  DROUGHT: '☀️', FOREST_FIRE: '🔥', HAIL: '🌨️', TYPHOON: '🌀'
}
const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震', FLOOD: '洪涝', LANDSLIDE: '滑坡', DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱', FOREST_FIRE: '森林火灾', HAIL: '冰雹', TYPHOON: '台风'
}

function getCoords(e: DisasterEvent): [number, number] | null {
  const lat = e.geo?.lat ?? (e as any).lat
  const lng = e.geo?.lng ?? (e as any).lng
  if (typeof lat === 'number' && typeof lng === 'number' && lat && lng) return [lat, lng]
  return null
}

function renderMarkers() {
  if (!map) return
  if (layer) layer.remove()
  layer = L.layerGroup().addTo(map)
  props.events.forEach((e) => {
    const coords = getCoords(e)
    if (!coords) return
    const color = levelColor[e.level] || '#999'
    const icon = typeIcon[e.type] || '📍'
    const pulse = e.level === 'I' || e.level === 'II'
    const html = `<div class="ydr-pin lv-${e.level} ${pulse ? 'pulse' : ''}"><span>${icon}</span></div>`
    const marker = L.marker(coords, {
      icon: L.divIcon({ className: 'ydr-marker', html, iconSize: [30, 30], iconAnchor: [15, 28] })
    })
    marker.bindTooltip(
      `<b>${e.title}</b><br/>等级：${e.level || '—'} 级<br/>状态：${e.status}<br/>影响人口：${e.affectedPopulation || 0}`,
      { direction: 'top', offset: [0, -26] }
    )
    marker.bindPopup(
      `<div class="ydr-popup-title">${e.title}</div>
       <div class="ydr-popup-meta">
         <span>类型：${typeLabel[e.type] || e.type}</span>
         <span>等级：${e.level || '—'}</span>
       </div>
       <div class="ydr-popup-meta">
         <span>位置：${e.location || '—'}</span>
       </div>
       <div style="margin-top:4px;color:#5a6675">${e.description || ''}</div>`
    )
    layer!.addLayer(marker)
  })
}

function addLegend() {
  if (!map || legendEl) return
  legendEl = document.createElement('div')
  legendEl.className = 'ydr-legend'
  legendEl.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px">灾情等级</div>
    ${Object.keys(levelLabel)
      .map(
        (k) =>
          `<div class="lg-row"><span class="lg-dot" style="background:${levelColor[k]}"></span>${levelLabel[k]}</div>`
      )
      .join('')}`
  const control = new L.Control({ position: 'bottomright' })
  control.onAdd = () => legendEl as HTMLElement
  control.addTo(map)
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
  addLegend()
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
  border-radius: 12px;
  overflow: hidden;
}
</style>
