<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
  center: { type: Array, default: () => [25.04, 101.5] },
  zoom: { type: Number, default: 7 },
  focusEvent: { type: Object, default: null }
})

// 高德开放平台 Key & 安全密钥（从 .env 读取：VITE_AMAP_KEY / VITE_AMAP_SECURITY）
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''
const AMAP_SECURITY = import.meta.env.VITE_AMAP_SECURITY || ''

const mapEl = ref()
let map = null
let infoWindow = null
let markers = []
let markerEventMap = []   // { eventId, marker }
let legendEl = null
let ro = null
let statusOverlay = null
let focusCircle = null
let focusAnimTimer = null
let pendingFocusEvent = null

function showStatus(text, type = 'info') {
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

const levelColor = {
  I: '#7b241c',
  II: '#c0392b',
  III: '#e67e22',
  IV: '#f1c40f'
}
const levelLabel = {
  I: 'Ⅰ级 特别重大',
  II: 'Ⅱ级 重大',
  III: 'Ⅲ级 较大',
  IV: 'Ⅳ级 一般'
}
const typeIcon = {
  RAINSTORM: '🌧️', FLOOD: '🌊', FLASH_FLOOD: '⛈️', LANDSLIDE: '⛰️', DEBRIS_FLOW: '🪨',
  COLLAPSE: '🏚️', EARTHQUAKE: '🌐'
}
const typeLabel = {
  RAINSTORM: '暴雨', FLOOD: '洪涝', FLASH_FLOOD: '山洪', LANDSLIDE: '滑坡',
  DEBRIS_FLOW: '泥石流', COLLAPSE: '崩塌', EARTHQUAKE: '地震'
}

function getCoords(e) {
  const lat = e.geo?.lat ?? e.lat
  const lng = e.geo?.lng ?? e.lng
  if (typeof lat === 'number' && typeof lng === 'number' && lat && lng) return [lat, lng]
  return null
}

function loadAMap() {
  return new Promise((resolve, reject) => {
    if (!AMAP_KEY || !AMAP_SECURITY) {
      reject(new Error('缺少高德 Key/安全密钥：请在 .env 配置 VITE_AMAP_KEY 与 VITE_AMAP_SECURITY'))
      return
    }
    if (window.AMap) {
      console.log('[AMap] AMap 已存在，版本:', window.AMap?.version || 'unknown')
      return resolve(window.AMap)
    }
    console.log('[AMap] 开始加载 SDK 脚本...')
    // 安全密钥必须在 SDK 脚本加载前设置
    window._AMapSecurityConfig = { securityJsCode: AMAP_SECURITY }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`
    script.onerror = () => reject(new Error('高德地图 SDK 脚本加载失败（onerror），检查网络/白名单）'))
    script.onload = () => {
      console.log('[AMap] SDK 脚本加载完成，window.AMap =', typeof window.AMap)
      if (window.AMap) resolve(window.AMap)
      else reject(new Error('AMap 未挂载到 window'))
    }
    document.head.appendChild(script)
  })
}

function buildInfoContent(e) {
  return `<div class="ydr-popup-title">${e.title || '—'}</div>
    <div class="ydr-popup-meta">
      <span>类型：${typeLabel[e.type] || e.type || '—'}</span>
      <span>等级：${levelLabel[e.level] || e.level || '—'}</span>
    </div>
    <div class="ydr-popup-meta">
      <span>位置：${e.location || '—'}</span>
    </div>
    <div style="margin-top:4px;color:#5a6675">${e.description || ''}</div>`
}

function renderMarkers(AMap) {
  if (!map) return
  if (markers.length) {
    map.remove(markers)
    markers = []
    markerEventMap = []
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
      infoWindow.setContent(buildInfoContent(e))
      infoWindow.open(map, position)
    })
    marker.addTo(map)
    markers.push(marker)
    markerEventMap.push({ eventId: e.id, marker })
  })
}

function focusOnEvent(e) {
  const AMap = window.AMap
  if (!map || !AMap || !e) return
  const lat = e.geo?.lat ?? e.lat
  const lng = e.geo?.lng ?? e.lng
  if (lat == null || lng == null || isNaN(lat) || isNaN(lng)) return
  const position = new AMap.LngLat(lng, lat)

  // 移动到事件位置并放大
  map.setZoomAndCenter(14, position)

  // 查找或创建临时 Marker
  let found = markerEventMap.find(m => m.eventId === e.id)
  let marker = found?.marker
  if (!marker) {
    const icon = typeIcon[e.type] || '📍'
    const html = `<div class="ydr-marker flash-focus"><div class="ydr-pin lv-${e.level}"><span>${icon}</span></div></div>`
    marker = new AMap.Marker({
      position,
      content: html,
      anchor: 'bottom-center',
      offset: new AMap.Pixel(0, 0),
      title: e.title
    })
    marker.addTo(map)
    markers.push(marker)
    markerEventMap.push({ eventId: e.id, marker })
  }

  // 打开信息窗
  infoWindow.setContent(buildInfoContent(e))
  infoWindow.open(map, marker.getPosition ? marker.getPosition() : position)

  // Marker 闪烁动画
  const el = marker.getContent ? marker.getContent() : null
  if (el && el.classList) {
    el.classList.add('flash-focus')
    setTimeout(() => {
      try { el.classList.remove('flash-focus') } catch (_) {}
    }, 3000)
  }

  // 涟漪扩散圈（持续 2 秒）
  if (focusCircle) {
    try { map.remove(focusCircle) } catch (_) {}
    focusCircle = null
  }
  focusCircle = new AMap.Circle({
    center: position,
    radius: 50,
    strokeColor: '#f5222d',
    strokeWeight: 2,
    fillColor: '#f5222d',
    fillOpacity: 0.25
  })
  focusCircle.addTo(map)

  if (focusAnimTimer) clearInterval(focusAnimTimer)
  let r = 50
  focusAnimTimer = setInterval(() => {
    r += 25
    focusCircle.setRadius(r)
    if (r >= 600) {
      clearInterval(focusAnimTimer)
      focusAnimTimer = null
      setTimeout(() => {
        if (focusCircle) {
          try { map.remove(focusCircle) } catch (_) {}
          focusCircle = null
        }
      }, 200)
    }
  }, 30)
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

function initMap(AMap) {
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
    if (props.focusEvent) {
      setTimeout(() => focusOnEvent(props.focusEvent), 200)
    }

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
  } catch (err) {
    console.error('[AMap] initMap error:', err)
    showStatus('地图初始化失败：' + (err.message || err), 'error')
    throw err
  }
}

onMounted(() => {
  showStatus('正在加载高德地图...')
  console.log('[AMap] using key prefix:', AMAP_KEY.slice(0, 8) + '****, len=' + AMAP_KEY.length)
  console.log('[AMap] security code len:', AMAP_SECURITY.length)
  loadAMap()
    .then((AMap) => initMap(AMap)).catch((err) => {
      console.error('[AMap]', err)
      showStatus('地图加载失败：' + (err && err.message ? err.message : err), 'error')
    })
})

watch(
  () => props.events,
  () => {
    const AMap = window.AMap
    if (map && AMap) {
      renderMarkers(AMap)
      if (props.focusEvent) {
        setTimeout(() => focusOnEvent(props.focusEvent), 100)
      }
    }
  },
  { deep: true }
)

watch(
  () => props.focusEvent,
  (val) => {
    if (val && map && window.AMap) {
      setTimeout(() => focusOnEvent(val), 100)
    }
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (ro) ro.disconnect()
  if (focusAnimTimer) clearInterval(focusAnimTimer)
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<template>
  <div ref="mapEl" class="map"></div>
</template>

<style scoped>
.map {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
}

:deep(.ydr-marker) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.ydr-pin) {
  width: 34px;
  height: 34px;
  border-radius: 50% 50% 50% 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  transform: rotate(-45deg);
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}

:deep(.ydr-pin span) {
  transform: rotate(45deg);
}

:deep(.ydr-pin.lv-I) { background: #7b241c; }
:deep(.ydr-pin.lv-II) { background: #c0392b; }
:deep(.ydr-pin.lv-III) { background: #e67e22; }
:deep(.ydr-pin.lv-IV) { background: #f1c40f; }

:deep(.ydr-pin.pulse) {
  animation: ydr-pulse 2s infinite;
}

:deep(.ydr-marker.flash-focus .ydr-pin) {
  animation: ydr-pulse 1s infinite;
  border-color: #f5222d;
  box-shadow: 0 0 0 4px rgba(245, 34, 45, 0.3);
}

@keyframes ydr-pulse {
  0% { box-shadow: 0 0 0 0 rgba(192, 57, 43, 0.5); }
  70% { box-shadow: 0 0 0 12px rgba(192, 57, 43, 0); }
  100% { box-shadow: 0 0 0 0 rgba(192, 57, 43, 0); }
}

:deep(.ydr-legend) {
  background: rgba(255, 255, 255, 0.92) !important;
  color: #334155 !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 8px 10px !important;
  font-size: 12px !important;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
}

:deep(.ydr-legend .lg-row) {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}

:deep(.ydr-legend .lg-dot) {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

:deep(.ydr-popup-title) {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  color: #1f2937;
}

:deep(.ydr-popup-meta) {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

:deep(.amap-info-content) {
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e2e8f0;
}
</style>
