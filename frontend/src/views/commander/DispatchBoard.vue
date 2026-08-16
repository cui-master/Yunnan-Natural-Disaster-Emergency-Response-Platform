<template>
  <div class="dispatch-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#722ed1"><Share /></el-icon>
        <span>调度看板</span>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedLabel" placeholder="选择节点类别" clearable filterable style="width: 200px;" @change="onLabelChange">
          <el-option
            v-for="lb in labels"
            :key="lb.label"
            :label="`${lb.displayName}（${lb.count}）`"
            :value="lb.label"
          />
        </el-select>
        <el-button :icon="Refresh" @click="refreshGraph" :loading="loading">刷新图谱</el-button>
        <el-button :icon="ZoomOut" @click="zoomToFit">适应画布</el-button>
        <el-button type="primary" :icon="FullScreen" @click="fullscreen = !fullscreen">全屏</el-button>
      </div>
    </div>

    <div class="dispatch-body">
      <!-- 左侧：节点分类 + 关系类型 -->
      <div class="side-panel">
        <div class="stat-card">
          <div class="stat-title">
            <el-icon :size="14"><Grid /></el-icon>
            节点类别
          </div>
          <div class="label-list">
            <div
              v-for="lb in labels"
              :key="lb.label"
              class="label-item"
              :class="{ active: selectedLabel === lb.label }"
              @click="loadLabelNodes(lb.label)"
            >
              <span class="label-dot" :style="{ background: getLabelColor(lb.displayName) }"></span>
              <span class="label-name">{{ lb.displayName }}</span>
              <span class="label-count">{{ lb.count }}</span>
            </div>
            <div v-if="labels.length === 0" class="empty-hint">加载中...</div>
          </div>
        </div>

        <div class="legend-card">
          <div class="stat-title">
            <el-icon :size="14"><Connection /></el-icon>
            关系类型
          </div>
          <div class="rel-list">
            <div v-for="rel in relTypes" :key="rel.type" class="rel-item" :title="rel.type">
              <span class="rel-arrow">→</span>
              <span class="rel-name">{{ rel.type }}</span>
              <span class="rel-count">{{ rel.count }}</span>
            </div>
          </div>
        </div>

        <div v-if="canvasNodes.length > 0" class="stat-card">
          <div class="stat-title">
            画布统计
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <span class="stat-label">节点数</span>
              <span class="stat-count">{{ canvasNodes.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">关系数</span>
              <span class="stat-count">{{ canvasEdges.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已展开</span>
              <span class="stat-count">{{ expandedNodes.size }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间图谱区域 -->
      <div class="graph-panel" :class="{ fullscreen }">
        <div ref="graphRef" class="graph-container"></div>
        <div class="graph-hint" v-if="canvasNodes.length === 0 && !loading">
          <el-icon :size="48" color="#d1d5db"><Grid /></el-icon>
          <p>请在左侧选择一个节点类别开始浏览</p>
          <p class="hint-sub">双击节点展开邻居，再次双击收起</p>
        </div>
        <div class="graph-loading" v-if="loading">
          <el-icon :size="32" class="loading-icon"><Loading /></el-icon>
          <p>加载图谱数据中...</p>
        </div>
        <div class="graph-tip" v-if="canvasNodes.length > 0">
          <el-tag size="small" effect="plain">双击展开/收起 · 单击查看详情 · 滚轮缩放 · 拖拽移动</el-tag>
        </div>
      </div>

      <!-- 右侧：节点/关系详情面板 -->
      <div class="detail-panel" v-if="selectedNode">
        <div class="detail-header">
          <div class="detail-title">
            <span class="detail-dot" :style="{ background: getLabelColor(selectedNode.group) }"></span>
            {{ selectedNode.group }}
          </div>
          <el-button text :icon="Close" @click="selectedNode = null" size="small" />
        </div>
        <div class="detail-name">{{ selectedNode.label }}</div>
        <div class="detail-tags">
          <el-tag size="small" type="warning" effect="light">{{ selectedNode.group }}</el-tag>
        </div>
        <div class="detail-section">
          <div class="section-title">属性</div>
          <div class="prop-list">
            <div v-for="(val, key) in selectedNode.properties" :key="key" class="prop-item">
              <span class="prop-key">{{ key }}</span>
              <span class="prop-val">{{ formatPropVal(val) }}</span>
            </div>
          </div>
        </div>
        <div class="detail-actions">
          <el-button size="small" type="primary" @click="expandFromSelected" :disabled="isExpanded(selectedNode.id)">
            {{ isExpanded(selectedNode.id) ? '已展开' : '展开邻居' }}
          </el-button>
          <el-button size="small" @click="focusNetwork(selectedNode.id)">定位</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Network } from 'vis-network'
import {
  Share, Refresh, FullScreen, Loading, Close, Grid, Connection, ZoomOut
} from '@element-plus/icons-vue'

const graphRef = ref(null)
const loading = ref(false)
const fullscreen = ref(false)
const selectedLabel = ref('')
const labels = ref([])
const relTypes = ref([])

// JSON 全量图谱数据
const triplesData = ref([])
const allNodeMap = ref(new Map())      // id -> node object（全量）
const allEdgeMap = ref(new Map())      // edgeId -> edge object（全量）

// 画布数据（用 Map 防止重复）
const canvasNodeMap = ref(new Map())   // id -> node object
const canvasEdgeMap = ref(new Map())   // edgeId -> edge object
const expandedNodes = ref(new Set())   // 已展开的节点 id 集合
const expansionMap = ref(new Map())    // nodeId -> { neighborIds, edgeIds }
const selectedNode = ref(null)
let network = null

// 颜色调色板（为未知标签分配颜色）
const colorPalette = [
  '#f5222d', '#fa8c16', '#faad14', '#52c41a', '#13c2c2',
  '#1890ff', '#2f54eb', '#722ed1', '#eb2f96', '#8c8c8c',
  '#a0d911', '#1677ff', '#e91e63', '#00bcd4', '#ff5722'
]
const labelColorCache = new Map()
let colorIdx = 0

// 内置标签颜色映射（严格按实体类型分配，一级实体用饱和色，二级实体用浅色/同色系）
const presetColors = {
  // 一级实体（饱和色、大节点）
  '受灾点': '#f5222d',
  '物资仓库': '#1890ff',
  '物资': '#1890ff',
  '救援队伍': '#fa8c16',
  '避难场所': '#52c41a',
  '道路': '#4d4d4d',
  '调度指令': '#722ed1',
  '地点': '#faad14',
  // 二级实体（稍浅色）
  '危险等级': '#cf1322',
  '受灾人数': '#e67022',
  '灾害类型': '#531dab',
  '地点名称': '#d48806',
  '状态': '#bfbfbf',
  '队伍类型': '#d46b08',
  '擅长灾害': '#ad6800',
  '重量': '#fa8c16',
  '场所名称': '#389e0d',
  '最大容纳人数': '#73d13d',
  '已容纳人数': '#95de64',
  '道路编号': '#595959',
  '道路名称': '#8c8c8c',
  '道路等级': '#434343',
  '通行状态': '#262626',
  '承载上限': '#a6a6a6',
  '通行代价': '#bfbfbf',
  '物资单品': '#40a9ff',
  '适用灾害': '#69c0ff',
  '数量': '#91d5ff',
  // 英文标签映射
  'Incident': '#f5222d',
  'Resource': '#1890ff',
  'DispatchOrder': '#722ed1',
  'Location': '#faad14',
  'RiskLevel': '#cf1322',
  'AffectedCount': '#e67022',
  'DisasterType': '#531dab',
  'Road': '#4d4d4d',
  'PlaceName': '#d48806'
}

// 一级实体集合（节点更大）
const LEVEL1_ENTITIES = new Set(['受灾点', '物资仓库', '救援队伍', '避难场所', '道路',
  'Incident', 'Resource', 'DispatchOrder', 'Location'])

const canvasNodes = computed(() => Array.from(canvasNodeMap.value.values()))
const canvasEdges = computed(() => Array.from(canvasEdgeMap.value.values()))

function getLabelColor(groupName) {
  if (presetColors[groupName]) return presetColors[groupName]
  if (labelColorCache.has(groupName)) return labelColorCache.get(groupName)
  const color = colorPalette[colorIdx % colorPalette.length]
  colorIdx++
  labelColorCache.set(groupName, color)
  return color
}

function formatPropVal(val) {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function isExpanded(nodeId) {
  return expandedNodes.value.has(nodeId)
}

// ============ JSON 图谱解析 ============

function buildNodeId(name, type) {
  return `${type}:${name}`
}

function buildEdgeId(fromId, toId, predicate) {
  return `${fromId}|${predicate}|${toId}`
}

function parseTriples(triples) {
  const nodeMap = new Map()
  const edgeMap = new Map()
  const labelCount = new Map()
  const relCount = new Map()

  triples.forEach(t => {
    const subId = buildNodeId(t.subject, t.subject_type)
    const objId = buildNodeId(t.object, t.object_type)

    if (!nodeMap.has(subId)) {
      nodeMap.set(subId, {
        id: subId,
        label: t.subject,
        group: t.subject_type,
        rawLabel: t.subject_type,
        properties: { type: t.subject_type }
      })
      labelCount.set(t.subject_type, (labelCount.get(t.subject_type) || 0) + 1)
    }

    if (!nodeMap.has(objId)) {
      nodeMap.set(objId, {
        id: objId,
        label: t.object,
        group: t.object_type,
        rawLabel: t.object_type,
        properties: { type: t.object_type }
      })
      labelCount.set(t.object_type, (labelCount.get(t.object_type) || 0) + 1)
    }

    const edgeId = buildEdgeId(subId, objId, t.predicate)
    if (!edgeMap.has(edgeId)) {
      edgeMap.set(edgeId, {
        id: edgeId,
        from: subId,
        to: objId,
        label: t.predicate
      })
      relCount.set(t.predicate, (relCount.get(t.predicate) || 0) + 1)
    }
  })

  return { nodeMap, edgeMap, labelCount, relCount }
}

function getNeighborEdges(nodeId) {
  const name = allNodeMap.value.get(nodeId)?.label
  if (!name) return []
  return triplesData.value.filter(t =>
    buildNodeId(t.subject, t.subject_type) === nodeId ||
    buildNodeId(t.object, t.object_type) === nodeId
  )
}

// ============ 初始化和加载 ============

async function loadGraphJson() {
  loading.value = true
  try {
    const res = await fetch('/full_graph_triples.json')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    triplesData.value = data.triples || []
    const { nodeMap, edgeMap, labelCount, relCount } = parseTriples(triplesData.value)
    allNodeMap.value = nodeMap
    allEdgeMap.value = edgeMap

    labels.value = Array.from(labelCount.entries()).map(([label, count]) => ({
      label,
      displayName: label,
      count
    })).sort((a, b) => b.count - a.count)

    relTypes.value = Array.from(relCount.entries()).map(([type, count]) => ({
      type,
      count
    })).sort((a, b) => b.count - a.count)

    // 默认全量显示所有节点/关系
    loadAllNodes()
  } catch (e) {
    console.error('加载 JSON 图谱失败:', e)
  } finally {
    loading.value = false
  }
}

function loadRelTypes() {
  // relTypes 已在 loadGraphJson 中生成
}

function loadAllNodes() {
  loading.value = true
  selectedNode.value = null
  selectedLabel.value = ''
  expandedNodes.value.clear()
  expansionMap.value.clear()
  canvasNodeMap.value = new Map(allNodeMap.value)
  canvasEdgeMap.value = new Map(allEdgeMap.value)
  if (network) {
    network.destroy()
    network = null
  }
  nextTick(renderGraph)
  loading.value = false
}

function loadLabelNodes(label) {
  if (!label) return
  loading.value = true
  selectedNode.value = null
  expandedNodes.value.clear()
  expansionMap.value.clear()
  canvasNodeMap.value.clear()
  canvasEdgeMap.value.clear()
  if (network) {
    network.destroy()
    network = null
  }
  try {
    for (const node of allNodeMap.value.values()) {
      if (node.group === label) {
        canvasNodeMap.value.set(node.id, node)
      }
    }
    // 自动展示同类节点之间的边
    allEdgeMap.value.forEach(edge => {
      if (canvasNodeMap.value.has(edge.from) && canvasNodeMap.value.has(edge.to)) {
        canvasEdgeMap.value.set(edge.id, edge)
      }
    })
    nextTick(renderGraph)
  } catch (e) {
    console.error('加载节点失败:', e)
  } finally {
    loading.value = false
  }
}

function onLabelChange(label) {
  if (label) {
    loadLabelNodes(label)
  } else {
    loadAllNodes()
  }
}

function refreshGraph() {
  loadGraphJson()
}

// ============ 图谱渲染 ============

let physicsStopTimer = null

function buildVisNodes() {
  return canvasNodes.value.map(n => {
    const isLevel1 = LEVEL1_ENTITIES.has(n.group) || LEVEL1_ENTITIES.has(n.rawLabel)
    const bgColor = getLabelColor(n.group)
    return {
      id: n.id,
      label: n.label || '未命名',
      title: buildTooltip(n),
      group: n.group,
      color: {
        background: bgColor,
        border: isExpanded(n.id) ? '#fbbf24' : '#ffffff',
        highlight: { background: bgColor, border: '#fbbf24' },
        hover: { background: bgColor, border: '#60a5fa' }
      },
      font: {
        color: '#fff',
        size: isLevel1 ? 13 : 11,
        face: 'Microsoft YaHei, "PingFang SC", sans-serif',
        strokeWidth: isLevel1 ? 3 : 2,
        strokeColor: bgColor,
        multi: false,
        bold: isLevel1
      },
      shape: 'dot',
      size: isLevel1 ? 24 : 16,
      borderWidth: isExpanded(n.id) ? 4 : 2,
      borderWidthSelected: 4,
      shadow: isLevel1 ? { enabled: true, color: 'rgba(0,0,0,0.2)', size: 8, x: 2, y: 2 } : false,
      chosen: {
        node: (values, id, selected, hovering) => {
          values.borderWidth = selected ? 5 : 3
          values.shadow = true
        }
      }
    }
  })
}

function buildVisEdges() {
  return canvasEdges.value.map(e => ({
    id: e.id,
    from: e.from,
    to: e.to,
    label: e.label || '',
    font: {
      size: 10,
      color: '#4b5563',
      strokeWidth: 3,
      strokeColor: '#ffffff',
      align: 'top',
      background: '#ffffff',
      face: 'Microsoft YaHei, "PingFang SC", sans-serif'
    },
    color: { color: '#d1d5db', highlight: '#f59e0b', hover: '#9ca3af', opacity: 0.8 },
    arrows: { to: { enabled: true, scaleFactor: 0.5, type: 'arrow' } },
    smooth: { type: 'continuous', roundness: 0.3 },
    width: 1.5,
    hoverWidth: 2.5,
    selectionWidth: 2.5
  }))
}

function visOptions() {
  return {
    nodes: { shapeProperties: { useBorderWithImage: true } },
    edges: { smooth: { type: 'continuous' } },
    physics: {
      enabled: true,
      barnesHut: {
        // 弹性参数：较强弹簧力、适中斥力、低阻尼实现弹性
        gravitationalConstant: -3000,
        centralGravity: 0.15,
        springLength: 160,
        springConstant: 0.08,
        damping: 0.45,
        avoidOverlap: 0.5
      },
      stabilization: {
        enabled: true,
        iterations: 200,
        updateInterval: 25,
        fit: true
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true,
      dragView: true,
      dragNodes: true,
      multiselect: false,
      navigationButtons: false,
      keyboard: false,
      hideEdgesOnDrag: false,
      hideNodesOnDrag: false
    }
  }
}

function renderGraph() {
  if (!graphRef.value) return
  const nodes = buildVisNodes()
  const edges = buildVisEdges()

  if (network) {
    network.setData({ nodes, edges })
  } else {
    network = new Network(graphRef.value, { nodes, edges }, visOptions())
    bindEvents()
    // 首次稳定后切换到"静态模式"（高阻尼，节点基本不动但保留弹性）
    network.once('stabilizationIterationsDone', () => {
      setPhysicsStatic()
    })
  }
}

// 静态模式：高阻尼，节点基本稳定，拖动时会有轻微弹性
function setPhysicsStatic() {
  if (!network) return
  network.setOptions({
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -1500,
        centralGravity: 0.1,
        springLength: 150,
        springConstant: 0.04,
        damping: 0.9,
        avoidOverlap: 0.3
      },
      stabilization: { enabled: false }
    }
  })
}

// 弹性模式：低阻尼，弹簧感强，用于展开/拖动后回弹
function setPhysicsElastic(durationMs = 2000) {
  if (!network) return
  network.setOptions({
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -3000,
        centralGravity: 0.15,
        springLength: 160,
        springConstant: 0.08,
        damping: 0.45,
        avoidOverlap: 0.5
      },
      stabilization: { enabled: false }
    }
  })
  if (physicsStopTimer) clearTimeout(physicsStopTimer)
  physicsStopTimer = setTimeout(() => {
    setPhysicsStatic()
  }, durationMs)
}

function stabilizeLayout(durationMs = 2000) {
  setPhysicsElastic(durationMs)
}

function buildTooltip(n) {
  let html = `<div style="max-width:260px;padding:4px;">`
  html += `<b>${n.label}</b><br/>`
  html += `<span style="color:#888;font-size:11px;">${n.rawLabel}</span><br/>`
  const props = n.properties || {}
  const keys = Object.keys(props).slice(0, 6)
  keys.forEach(k => {
    html += `<span style="font-size:11px;color:#555;">${k}: ${String(props[k]).substring(0, 40)}</span><br/>`
  })
  html += `</div>`
  return html
}

function truncateLabel(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.substring(0, maxLen) + '…' : text
}

// ============ 事件绑定 ============

function bindEvents() {
  // 双击：展开/收起邻居
  network.on('doubleClick', async (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      toggleExpand(nodeId)
    }
  })

  // 单击：选中节点并显示详情
  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const node = canvasNodeMap.value.get(nodeId)
      selectedNode.value = node || null
    } else if (params.edges.length > 0) {
      selectedNode.value = null
    } else {
      selectedNode.value = null
    }
  })

  // 开始拖动节点：切换到弹性模式，让连线有弹簧感
  network.on('dragStart', (params) => {
    if (params.nodes.length > 0) {
      setPhysicsElastic(3000)
    }
  })

  // 拖动结束：保持弹性模式让节点回弹，超时后回到静态
  network.on('dragEnd', (params) => {
    if (params.nodes.length > 0) {
      setPhysicsElastic(2000)
    }
  })

  // 缩放/平移画布时不需要物理效果
  network.on('zoom', () => {
    if (physicsStopTimer) clearTimeout(physicsStopTimer)
  })
}

// ============ 展开/收起逻辑 ============

async function toggleExpand(nodeId) {
  if (expandedNodes.value.has(nodeId)) {
    await collapseNeighbors(nodeId)
  } else {
    await expandNeighbors(nodeId)
  }
}

async function expandNeighbors(nodeId) {
  if (expandedNodes.value.has(nodeId)) return
  loading.value = true
  try {
    const connectedTriples = getNeighborEdges(nodeId)
    const neighborIds = new Set()
    const edgeIds = new Set()

    connectedTriples.forEach(t => {
      const subId = buildNodeId(t.subject, t.subject_type)
      const objId = buildNodeId(t.object, t.object_type)
      const edgeId = buildEdgeId(subId, objId, t.predicate)
      const neighborId = subId === nodeId ? objId : subId

      neighborIds.add(neighborId)
      edgeIds.add(edgeId)

      if (!canvasNodeMap.value.has(neighborId) && allNodeMap.value.has(neighborId)) {
        canvasNodeMap.value.set(neighborId, allNodeMap.value.get(neighborId))
      }
    })

    // 补全可见节点之间的所有边
    allEdgeMap.value.forEach(edge => {
      if (canvasNodeMap.value.has(edge.from) && canvasNodeMap.value.has(edge.to)) {
        canvasEdgeMap.value.set(edge.id, edge)
      }
    })

    expandedNodes.value.add(nodeId)
    expansionMap.value.set(nodeId, { neighborIds, edgeIds })
    await nextTick()
    renderGraph()
    stabilizeLayout(2500)
  } catch (e) {
    console.error('展开邻居失败:', e)
  } finally {
    loading.value = false
  }
}

async function collapseNeighbors(nodeId) {
  if (!expandedNodes.value.has(nodeId)) return
  loading.value = true
  try {
    const expansion = expansionMap.value.get(nodeId)
    if (!expansion) return

    const { neighborIds, edgeIds } = expansion
    // 移除本次展开添加的边
    edgeIds.forEach(eid => canvasEdgeMap.value.delete(eid))

    // 检查每个邻居：如果不再有边连接，移除节点
    neighborIds.forEach(nid => {
      if (nid === nodeId) return
      let stillConnected = false
      for (const edge of canvasEdgeMap.value.values()) {
        if (edge.from === nid || edge.to === nid) {
          stillConnected = true
          break
        }
      }
      if (!stillConnected) {
        canvasNodeMap.value.delete(nid)
        expandedNodes.value.delete(nid)
      }
    })

    expandedNodes.value.delete(nodeId)
    expansionMap.value.delete(nodeId)
    if (selectedNode.value && !canvasNodeMap.value.has(selectedNode.value.id)) {
      selectedNode.value = null
    }
    await nextTick()
    renderGraph()
  } catch (e) {
    console.error('收起邻居失败:', e)
  } finally {
    loading.value = false
  }
}

function expandFromSelected() {
  if (selectedNode.value) {
    toggleExpand(selectedNode.value.id)
  }
}

function focusNetwork(nodeId) {
  if (network && nodeId !== undefined && nodeId !== null) {
    network.focus(nodeId, { scale: 1.2, animation: { duration: 400, easingFunction: 'easeInOutQuad' } })
  }
}

function zoomToFit() {
  if (network) {
    network.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } })
  }
}

// ============ 生命周期 ============

onMounted(async () => {
  await loadGraphJson()
})

onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>

<style scoped lang="scss">
.dispatch-page {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.dispatch-body {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 0;
}

// ========== 左侧面板 ==========
.side-panel {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;

  @media (max-width: 900px) {
    display: none;
  }
}

.stat-card,
.legend-card {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.label-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 340px;
  overflow-y: auto;
}

.label-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
  border: 1px solid transparent;

  &:hover {
    background: #f9fafb;
    border-color: #e5e7eb;
  }

  &.active {
    background: #fef3c7;
    border-color: #fcd34d;
    color: #92400e;
    font-weight: 600;

    .label-dot {
      transform: scale(1.3);
      box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.3);
    }

    .label-count {
      color: #b45309;
    }
  }
}

.label-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.15s ease;
  border: 2px solid rgba(255,255,255,0.6);
}

.label-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.label-count {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
}

.rel-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 220px;
  overflow-y: auto;
}

.rel-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #6b7280;
  padding: 3px 6px;
}

.rel-arrow {
  color: #c4b5fd;
  font-size: 13px;
}

.rel-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rel-count {
  font-size: 10px;
  color: #d1d5db;
}

.empty-hint {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  padding: 12px 0;
}

.stat-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
}

.stat-label {
  color: #6b7280;
}

.stat-count {
  font-weight: 600;
  color: #1f2937;
}

// ========== 中间图区域 ==========
.graph-panel {
  flex: 1;
  background: #fafafa;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
  min-height: 400px;
  border: 1px solid #e5e7eb;

  &.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    border-radius: 0;
    border: none;
  }
}

.graph-container {
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle, #e5e7eb 1px, transparent 1px);
  background-size: 24px 24px;
}

.graph-hint {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  gap: 8px;
  font-size: 14px;
  pointer-events: none;

  .hint-sub {
    font-size: 12px;
    color: #d1d5db;
  }
}

.graph-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.88);
  color: #6b7280;
  gap: 10px;
  font-size: 14px;
  z-index: 10;
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: #7c3aed;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.graph-tip {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  pointer-events: none;
}

// ========== 右侧详情面板 ==========
.detail-panel {
  width: 260px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;

  @media (max-width: 1200px) {
    display: none;
  }
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

.detail-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.detail-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  word-break: break-all;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-section {
  border-top: 1px solid #f3f4f6;
  padding-top: 10px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.prop-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.prop-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 4px 0;
  border-bottom: 1px dashed #f9fafb;
}

.prop-key {
  font-size: 11px;
  color: #9ca3af;
}

.prop-val {
  font-size: 12px;
  color: #374151;
  word-break: break-all;
}

.detail-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid #f3f4f6;
}
</style>
