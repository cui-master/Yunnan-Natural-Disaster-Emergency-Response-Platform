<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
<<<<<<< HEAD
=======
import L from 'leaflet'
>>>>>>> feature-cui
import type { DisasterEvent } from '@/types'

const props = defineProps<{
  events: DisasterEvent[]
  center?: [number, number]
  zoom?: number
}>()

<<<<<<< HEAD
// 高德开放平台 Key & 安全密钥（从 .env 读取：VITE_AMAP_KEY / VITE_AMAP_SECURITY_CODE）
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''
const AMAP_SECURITY_CODE = import.meta.env.VITE_AMAP_SECURITY_CODE || ''

const mapEl = ref<HTMLDivElement>()
let map: any = null
let infoWindow: any = null
let markers: any[] = []
let legendEl: HTMLDivElement | null = null
let ro: ResizeObserver | null = null
let statusOverlay: HTMLDivElement | null = null

function showStatus(text: string, type: 'info' | 'error' = 'info') {
  if (!mapEl.value) return
  if (!statusOverlay) {
    statusOverlay = document.createElement('div')
    statusOverlay.style.cssText =
      'position:absolute;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;' +
      'padding:24px;font-size:13px;line-height:1.6;text-align:center;pointer-events:none;'
    mapEl.value.appendChild(statusOverlay)
  }
  statusOverlay.textContent = text
  statusOverlay.style.background = type === 'error' ? 'rgba(254,226,226,0.92)' : 'rgba(255,255,255,0.85)'
  statusOverlay.style.color = type === 'error' ? '#991b1b' : '#334155'
}

function hideStatus() {
  if (statusOverlay) {
    statusOverlay.remove()
    statusOverlay = null
  }
}
=======
const mapEl = ref<HTMLDivElement>()
let map: L.Map | null = null
let layer: L.LayerGroup | null = null
>>>>>>> feature-cui

const levelColor: Record<string, string> = {
  I: '#7b241c',
  II: '#c0392b',
  III: '#e67e22',
  IV: '#f1c40f'
}
<<<<<<< HEAD
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

function loadAMap(): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!AMAP_KEY || !AMAP_SECURITY_CODE) {
      reject(new Error('缺少高德 Key/安全密钥：请在 .env 配置 VITE_AMAP_KEY 与 VITE_AMAP_SECURITY_CODE'))
      return
    }
    if ((window as any).AMap) {
      console.log('[AMap] AMap 已存在，版本:', (window as any).AMap?.version || 'unknown')
      return resolve((window as any).AMap)
    }
    console.log('[AMap] 开始加载 SDK 脚本...')
    // 安全密钥必须在 SDK 脚本加载前设置
    ;(window as any)._AMapSecurityConfig = { securityJsCode: AMAP_SECURITY_CODE }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`
    script.onerror = () => reject(new Error('高德地图 SDK 脚本加载失败（onerror），检查网络/白名单）'))
    script.onload = () => {
      console.log('[AMap] SDK 脚本加载完成，window.AMap =', typeof (window as any).AMap)
      if ((window as any).AMap) resolve((window as any).AMap)
      else reject(new Error('AMap 未挂载到 window'))
    }
    document.head.appendChild(script)
  })
}

function renderMarkers(AMap: any) {
  if (!map) return
  if (markers.length) {
    map.remove(markers)
    markers = []
  }
  props.events.forEach((e) => {
    const coords = getCoords(e)
    if (!coords) return
    const [lat, lng] = coords
    const icon = typeIcon[e.type] || '📍'
    const pulse = e.level === 'I' || e.level === 'II'
    const html = `<div class="ydr-marker"><div class="ydr-pin lv-${e.level} ${pulse ? 'pulse' : ''}"><span>${icon}</span></div></div>`
    const position = new AMap.LngLat(lng, lat)
    const marker = new AMap.Marker({
      position,
      content: html,
      anchor: 'bottom-center',
      offset: new AMap.Pixel(0, 0),
      title: `${e.title} | ${typeLabel[e.type] || e.type} | ${levelLabel[e.level] || '—'}级`
    })
    marker.on('click', () => {
      infoWindow.setContent(
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
      infoWindow.open(map, position)
    })
    marker.addTo(map)
    markers.push(marker)
  })
}

function addLegend() {
  if (!map || legendEl) return
  const container = map.getContainer()
  legendEl = document.createElement('div')
  legendEl.className = 'ydr-legend'
  legendEl.style.cssText = 'position:absolute;right:10px;bottom:10px;z-index:100;'
  legendEl.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px">灾情等级</div>
    ${Object.keys(levelLabel)
      .map(
        (k) =>
          `<div class="lg-row"><span class="lg-dot" style="background:${levelColor[k]}"></span>${levelLabel[k]}</div>`
      )
      .join('')}`
  container.appendChild(legendEl)
}

function initMap(AMap: any) {
  try {
    const el = mapEl.value
    if (!el) throw new Error('地图容器未挂载')
    const rect = el.getBoundingClientRect()
    console.log('[AMap] 容器尺寸:', rect.width, 'x', rect.height)
    if (rect.width < 20 || rect.height < 20) {
      throw new Error(`地图容器尺寸过小(${rect.width.toFixed(0)}x${rect.height.toFixed(0)})，请检查父容器高度`)
    }
    const [lat, lng] = props.center || [25.04, 101.5]
    console.log('[AMap] 初始化 Map, center=', [lng, lat], 'zoom=', props.zoom || 7)
    map = new AMap.Map(el, {
      zoom: props.zoom || 7,
      center: [lng, lat],
      viewMode: '2D',
      zooms: [3, 20]
    })
    console.log('[AMap] Map 实例已创建')
    infoWindow = new AMap.InfoWindow({
      isCustom: true,
      content: '',
      offset: new AMap.Pixel(0, -30),
      autoMove: true,
      closeWhenClickMap: true
    })
    renderMarkers(AMap)
    addLegend()
    hideStatus()

    const resize = () => {
      if (map && typeof map.resize === 'function') {
        try { map.resize() } catch (e) { /* ignore */ }
      }
    }
    setTimeout(resize, 200)
    setTimeout(resize, 600)
    if (typeof ResizeObserver !== 'undefined' && mapEl.value) {
      ro = new ResizeObserver(() => resize())
      ro.observe(mapEl.value)
    }
  } catch (err: any) {
    console.error('[AMap] initMap error:', err)
    showStatus('地图初始化失败：' + (err.message || err), 'error')
    throw err
  }
}

onMounted(() => {
  showStatus('正在加载高德地图...')
  // 调试用：确认浏览器实际加载的是哪个 Key（便于排查 .env 未生效/缓存问题）
  console.log('[AMap] using key prefix:', AMAP_KEY.slice(0, 8) + '****, len=' + AMAP_KEY.length)
  console.log('[AMap] security code len:', AMAP_SECURITY_CODE.length)
  loadAMap()
    .then((AMap) => initMap(AMap))
    .catch((err) => {
      console.error('[AMap]', err)
      showStatus('地图加载失败：' + (err && err.message ? err.message : err), 'error')
    })
=======
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
>>>>>>> feature-cui
})

watch(
  () => props.events,
<<<<<<< HEAD
  () => {
    const AMap = (window as any).AMap
    if (map && AMap) renderMarkers(AMap)
  },
=======
  () => renderMarkers(),
>>>>>>> feature-cui
  { deep: true }
)

onBeforeUnmount(() => {
<<<<<<< HEAD
  if (ro) ro.disconnect()
  if (map) {
    map.destroy()
    map = null
  }
=======
  map?.remove()
  map = null
>>>>>>> feature-cui
})
</script>

<template>
  <div ref="mapEl" class="map"></div>
</template>

<style scoped>
.map {
<<<<<<< HEAD
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 12px;
=======
  width: 100%;
  height: 100%;
  border-radius: 8px;
>>>>>>> feature-cui
  overflow: hidden;
}
</style>
