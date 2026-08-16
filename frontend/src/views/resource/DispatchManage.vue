<template>
  <div class="dispatch-manage-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#722ed1"><Share /></el-icon>
        <span>调度看板管理</span>
        <el-tag type="info" effect="light" size="small">{{ graphData.triples.length }} 条三元组</el-tag>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="viewMode" size="default" @change="onViewModeChange">
          <el-radio-button label="table">表格视图</el-radio-button>
          <el-radio-button label="graph">图谱视图</el-radio-button>
        </el-radio-group>
        <template v-if="viewMode === 'table'">
          <el-radio-group v-model="activeTab" size="default" @change="onTabChange">
            <el-radio-button label="warehouse">仓库</el-radio-button>
            <el-radio-button label="team">救援队伍</el-radio-button>
            <el-radio-button label="shelter">避难场所</el-radio-button>
            <el-radio-button label="material">物资</el-radio-button>
            <el-radio-button label="relationship">关系</el-radio-button>
          </el-radio-group>
          <el-button type="primary" :icon="Plus" @click="handleAdd">
            新增{{ activeTab === 'relationship' ? '关系' : typeLabel }}
          </el-button>
        </template>
        <template v-else>
          <el-button type="primary" :icon="Plus" @click="openAddEntity">新增实体</el-button>
          <el-button type="primary" :icon="Connection" @click="openAddRelationshipFromGraph">新增关系</el-button>
          <el-button type="danger" :icon="Delete" @click="deleteSelectedGraphNode" :disabled="!selectedGraphNode">
            删除选中节点
          </el-button>
        </template>
        <el-button type="success" :icon="Check" :loading="saving" @click="handleSaveJson">
          保存到图数据库
        </el-button>
      </div>
    </div>

    <div class="content">
      <div class="table-card" v-show="viewMode === 'table'">
        <div class="search-bar">
          <el-input v-model="searchKeyword" placeholder="搜索名称/地址/关系" style="width: 240px;" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button :icon="Refresh" @click="loadJson">刷新</el-button>
        </div>

        <!-- 实体表格 -->
        <el-table v-if="activeTab !== 'relationship'" :data="filteredEntities" stripe style="width: 100%" v-loading="loading" border>
          <el-table-column prop="subject" label="名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="properties['位于']" label="位置" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ row.properties['位于'] || '-' }}</template>
          </el-table-column>
          <el-table-column label="容量/上限" width="120" align="center">
            <template #default="{ row }">{{ row.properties['承载上限'] || row.properties['最大容纳人数'] || row.properties['最大运载重量'] || '-' }}</template>
          </el-table-column>
          <el-table-column label="数量" width="100" align="center">
            <template #default="{ row }">{{ row.properties['数量'] || row.properties['已容纳人数'] || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态/类型" width="140" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="light">{{ row.properties['状态'] || row.properties['队伍类型'] || row.properties['类型'] || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditEntity(row)">编辑</el-button>
              <el-button size="small" type="success" link @click="handleShowTriples(row)">三元组</el-button>
              <el-popconfirm title="确定删除该实体及其所有三元组吗？" @confirm="handleDeleteEntity(row)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <!-- 关系表格 -->
        <el-table v-else :data="filteredRelationships" stripe style="width: 100%" v-loading="loading" border>
          <el-table-column prop="subject" label="主语" min-width="160" show-overflow-tooltip />
          <el-table-column prop="subject_type" label="主语类型" width="110" />
          <el-table-column prop="predicate" label="关系" width="110" align="center" />
          <el-table-column prop="object" label="宾语" min-width="160" show-overflow-tooltip />
          <el-table-column prop="object_type" label="宾语类型" width="110" />
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row, $index }">
              <el-button size="small" type="primary" link @click="handleEditRelationship(row, $index)">编辑</el-button>
              <el-popconfirm title="确定删除该关系吗？" @confirm="handleDeleteRelationship($index)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="hint">
          当前共 {{ activeTab === 'relationship' ? filteredRelationships.length : filteredEntities.length }} 条数据（未过滤前 {{ activeTab === 'relationship' ? relationships.length : entities.length }} 条）
        </div>
      </div>

      <!-- 图谱视图（图数据库视角） -->
      <div v-show="viewMode === 'graph'" class="graph-card">
        <!-- 左侧：节点类别 + 关系类型 -->
        <div class="graph-side-panel">
          <div class="stat-card">
            <div class="stat-title">
              <el-icon :size="14"><Search /></el-icon>
              节点搜索
            </div>
            <el-input v-model="graphSearchKeyword" placeholder="输入节点名称" clearable size="small" />
            <div class="search-result-list" v-if="graphSearchResults.length">
              <div
                v-for="n in graphSearchResults"
                :key="n.id"
                class="search-result-item"
                @click="onGraphSearchSelect(n)"
              >
                <span class="label-dot" :style="{ background: getLabelColor(n.group) }"></span>
                <span class="search-result-name">{{ n.label }}</span>
                <span class="search-result-type">{{ n.group }}</span>
              </div>
            </div>
            <div v-else-if="graphSearchKeyword.trim()" class="empty-hint">无匹配节点</div>
          </div>

          <div class="stat-card">
            <div class="stat-title">
              <el-icon :size="14"><FullScreen /></el-icon>
              全局视图
            </div>
            <el-button type="primary" plain size="small" style="width: 100%;" @click="showAllGraph">
              显示全部实体和关系
            </el-button>
          </div>

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
                <span class="label-dot" :style="{ background: getLabelColor(lb.label) }"></span>
                <span class="label-name">{{ lb.label }}</span>
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
            <div class="stat-title">画布统计</div>
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
        <div class="graph-panel" v-loading="loading">
          <div ref="graphRef" class="graph-container"></div>
          <div class="graph-hint" v-if="canvasNodes.length === 0 && !loading">
            <el-icon :size="48" color="#d1d5db"><Grid /></el-icon>
            <p>请在左侧选择一个节点类别开始浏览</p>
            <p class="hint-sub">双击节点展开/收起邻居</p>
          </div>
          <div class="graph-tip" v-if="canvasNodes.length > 0">
            <el-tag size="small" effect="plain">单击查看详情 · 双击展开邻居 · 滚轮缩放 · 拖拽移动</el-tag>
          </div>
        </div>

        <!-- 右侧：节点详情面板 -->
        <div class="detail-panel" v-if="selectedGraphNode">
          <div class="detail-header">
            <div class="detail-title">
              <span class="detail-dot" :style="{ background: getLabelColor(selectedGraphNode.group) }"></span>
              {{ selectedGraphNode.group }}
            </div>
            <el-button text :icon="Close" @click="clearGraphSelection" size="small" />
          </div>
          <div class="detail-name">{{ selectedGraphNode.label }}</div>
          <div class="detail-section">
            <div class="section-title">属性</div>
            <div class="prop-list">
              <div v-for="(val, key) in selectedGraphNode.properties" :key="key" class="prop-item">
                <span class="prop-key">{{ key }}</span>
                <span class="prop-val">{{ formatPropVal(val) }}</span>
              </div>
            </div>
          </div>
          <div class="detail-actions">
            <el-button size="small" type="primary" @click="expandFromSelected" :disabled="isExpanded(selectedGraphNode.id)">
              {{ isExpanded(selectedGraphNode.id) ? '已展开' : '展开邻居' }}
            </el-button>
            <el-button size="small" type="primary" @click="editSelectedGraphItem">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSelectedGraphNode">删除</el-button>
          </div>
        </div>

        <!-- 右侧：关系详情面板 -->
        <div class="detail-panel" v-else-if="selectedGraphEdge">
          <div class="detail-header">
            <div class="detail-title">
              <span class="detail-dot" :style="{ background: '#999' }"></span>
              关系
            </div>
            <el-button text :icon="Close" @click="clearGraphSelection" size="small" />
          </div>
          <div class="detail-name">{{ selectedGraphEdge.label }}</div>
          <div class="detail-row">
            <div>{{ selectedGraphEdge.fromName }} → {{ selectedGraphEdge.toName }}</div>
          </div>
          <div class="detail-actions">
            <el-button size="small" type="primary" @click="editSelectedGraphItem">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSelectedGraphEdge">删除</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 实体编辑弹窗 -->
    <el-dialog v-model="entityDialogVisible" :title="entityDialogTitle" width="700px" @closed="resetEntityForm">
      <el-form ref="entityFormRef" :model="entityForm" label-width="120px">
        <el-form-item label="实体名称" required>
          <el-input v-model="entityForm.subject" placeholder="实体名称" />
        </el-form-item>
        <el-form-item label="实体类型" required>
          <el-select v-model="entityForm.subject_type" placeholder="选择已有实体类型" filterable style="width: 100%;">
            <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">属性与关系（predicate → object）</el-divider>
        <div v-for="(prop, idx) in entityForm.properties" :key="idx" class="property-row">
          <el-input v-model="prop.predicate" placeholder="关系/属性名" style="width: 160px;" />
          <el-input v-model="prop.object" placeholder="值" style="flex: 1;" />
          <el-select v-model="prop.object_type" placeholder="值类型" filterable size="small" style="width: 140px;">
            <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
          </el-select>
          <el-button type="danger" link :icon="Delete" @click="removeEntityProperty(idx)">删除</el-button>
        </div>
        <el-button type="primary" link :icon="Plus" @click="addEntityProperty">添加属性/关系</el-button>
      </el-form>
      <template #footer>
        <el-button @click="entityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEntitySave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 关系编辑弹窗 -->
    <el-dialog v-model="relDialogVisible" :title="relEditMode ? '编辑关系' : '新增关系'" width="600px" @closed="resetRelForm">
      <el-form ref="relFormRef" :model="relForm" label-width="120px">
        <el-form-item label="主语" prop="subject" required>
          <el-input v-model="relForm.subject" placeholder="实体名称" />
        </el-form-item>
        <el-form-item label="主语类型" prop="subject_type" required>
          <el-select v-model="relForm.subject_type" placeholder="选择已有类型" filterable style="width: 100%;">
            <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系" prop="predicate" required>
          <el-input v-model="relForm.predicate" placeholder="如：位于、拥有、临近" />
        </el-form-item>
        <el-form-item label="宾语" prop="object" required>
          <el-input v-model="relForm.object" placeholder="值/实体名称" />
        </el-form-item>
        <el-form-item label="宾语类型" prop="object_type" required>
          <el-select v-model="relForm.object_type" placeholder="选择已有类型" filterable style="width: 100%;">
            <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRelSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 三元组查看弹窗 -->
    <el-dialog v-model="triplesDialogVisible" title="实体三元组" width="600px">
      <el-table :data="selectedEntityTriples" stripe border>
        <el-table-column prop="predicate" label="关系/属性" width="140" />
        <el-table-column prop="object" label="值" />
        <el-table-column prop="object_type" label="值类型" width="120" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Network } from 'vis-network'
import {
  Share, Plus, Search, Refresh, Check, Delete, Grid, Connection, Close, FullScreen
} from '@element-plus/icons-vue'

import { saveGraphJson } from '@/api'

const typeMap = {
  warehouse: '物资仓库',
  team: '救援队伍',
  shelter: '避难场所',
  material: '物资单品'
}

const typeLabelMap = {
  warehouse: '仓库',
  team: '救援队伍',
  shelter: '避难场所',
  material: '物资'
}

const activeTab = ref('warehouse')
const viewMode = ref('table')
const loading = ref(false)
const saving = ref(false)
const searchKeyword = ref('')
const graphData = ref({ graph_name: '', version: '', total_triples: 0, triples: [] })

const typeLabel = computed(() => typeLabelMap[activeTab.value] || '')

// 实体列表
const entities = computed(() => {
  if (activeTab.value === 'relationship') return []
  const type = typeMap[activeTab.value]
  const grouped = {}
  graphData.value.triples.forEach(t => {
    if (t.subject_type === type) {
      if (!grouped[t.subject]) {
        grouped[t.subject] = { subject: t.subject, subject_type: type, properties: {} }
      }
      grouped[t.subject].properties[t.predicate] = t.object
    }
  })
  return Object.values(grouped)
})

const filteredEntities = computed(() => {
  const kw = searchKeyword.value.trim()
  if (!kw) return entities.value
  return entities.value.filter(e =>
    e.subject.includes(kw) ||
    Object.values(e.properties).some(v => String(v).includes(kw))
  )
})

// 关系列表
const relationships = computed(() => {
  return graphData.value.triples.map((t, index) => ({ ...t, _index: index }))
})

const filteredRelationships = computed(() => {
  const kw = searchKeyword.value.trim()
  if (!kw) return relationships.value
  return relationships.value.filter(r =>
    r.subject.includes(kw) ||
    r.predicate.includes(kw) ||
    r.object.includes(kw) ||
    r.subject_type.includes(kw) ||
    r.object_type.includes(kw)
  )
})

const allSubjectTypes = computed(() => {
  const types = new Set(graphData.value.triples.map(t => t.subject_type))
  return Array.from(types).filter(Boolean)
})

const allTypes = computed(() => {
  const types = new Set()
  graphData.value.triples.forEach(t => {
    if (t.subject_type) types.add(t.subject_type)
    if (t.object_type) types.add(t.object_type)
  })
  return Array.from(types).filter(Boolean)
})

async function loadJson() {
  loading.value = true
  try {
    // 加时间戳避免浏览器/Vite缓存，确保保存后能立即读到最新文件
    const res = await fetch(`/full_graph_triples.json?t=${Date.now()}`)
    if (!res.ok) throw new Error('加载 JSON 失败')
    graphData.value = await res.json()
    ElMessage.success(`已加载图谱：${graphData.value.total_triples || graphData.value.triples.length} 条三元组`)
    refreshGraphIfVisible()
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function refreshGraphIfVisible() {
  if (viewMode.value === 'graph') {
    refreshGraphDatabaseView()
  }
}

function onTabChange() {
  searchKeyword.value = ''
}

// 实体编辑
const entityDialogVisible = ref(false)
const entityEditMode = ref(false)
const entityFormRef = ref(null)
const entityForm = reactive({
  subject: '',
  subject_type: '',
  properties: []
})
const originalEntitySubject = ref('')
const originalEntityType = ref('')

const entityDialogTitle = computed(() => (entityEditMode.value ? '编辑' : '新增') + (typeLabel.value || '实体'))

function handleAdd() {
  if (activeTab.value === 'relationship') {
    resetRelForm()
    relEditMode.value = false
    relDialogVisible.value = true
  } else {
    openAddEntity()
  }
}

function openAddEntity() {
  resetEntityForm()
  entityEditMode.value = false
  entityForm.subject_type = typeMap[activeTab.value] || '物资仓库'
  entityDialogVisible.value = true
}

function handleEditEntity(row) {
  resetEntityForm()
  entityEditMode.value = true
  entityForm.subject = row.subject
  entityForm.subject_type = row.subject_type
  originalEntitySubject.value = row.subject
  originalEntityType.value = row.subject_type
  entityForm.properties = Object.entries(row.properties).map(([predicate, object]) => ({
    predicate,
    object,
    object_type: getObjectType(row.subject, predicate)
  }))
  entityDialogVisible.value = true
}

function getObjectType(subject, predicate) {
  const t = graphData.value.triples.find(x => x.subject === subject && x.predicate === predicate)
  return t ? t.object_type : '文本'
}

function resetEntityForm() {
  entityForm.subject = ''
  entityForm.subject_type = ''
  entityForm.properties = []
  originalEntitySubject.value = ''
  originalEntityType.value = ''
}

function addEntityProperty() {
  entityForm.properties.push({ predicate: '', object: '', object_type: '文本' })
}

function removeEntityProperty(idx) {
  entityForm.properties.splice(idx, 1)
}

function confirmEntitySave() {
  if (!entityForm.subject.trim()) {
    ElMessage.warning('请输入实体名称')
    return
  }
  if (!entityForm.subject_type.trim()) {
    ElMessage.warning('实体类型不能为空')
    return
  }

  const triples = graphData.value.triples
  const newSubject = entityForm.subject.trim()
  const newType = entityForm.subject_type.trim()

  if (entityEditMode.value) {
    const oldSubject = originalEntitySubject.value
    const oldType = originalEntityType.value

    // 1. 把旧实体在全部三元组中的引用替换成新名称/新类型
    triples.forEach(t => {
      if (t.subject === oldSubject && t.subject_type === oldType) {
        t.subject = newSubject
        t.subject_type = newType
      }
      if (t.object === oldSubject && t.object_type === oldType) {
        t.object = newSubject
        t.object_type = newType
      }
    })

    // 2. 删除该实体作为主语的所有三元组，随后用表单里的属性/关系重新生成
    for (let i = triples.length - 1; i >= 0; i--) {
      if (triples[i].subject === newSubject && triples[i].subject_type === newType) {
        triples.splice(i, 1)
      }
    }
  }

  // 新增/更新三元组
  entityForm.properties.forEach(p => {
    if (!p.predicate.trim()) return
    triples.push({
      subject: newSubject,
      subject_type: newType,
      predicate: p.predicate.trim(),
      object: String(p.object),
      object_type: p.object_type.trim() || '文本'
    })
  })

  graphData.value.total_triples = triples.length
  entityDialogVisible.value = false
  refreshGraphIfVisible()
  ElMessage.success(entityEditMode.value ? '实体更新成功（尚未保存到 Neo4j 中）' : '实体新增成功（尚未保存到 Neo4j 中）')
}

// 关系编辑
const relDialogVisible = ref(false)
const relEditMode = ref(false)
const relFormRef = ref(null)
const relForm = reactive({
  subject: '',
  subject_type: '',
  predicate: '',
  object: '',
  object_type: ''
})
const editingRelIndex = ref(-1)

function resetRelForm() {
  relForm.subject = ''
  relForm.subject_type = ''
  relForm.predicate = ''
  relForm.object = ''
  relForm.object_type = ''
  editingRelIndex.value = -1
}

function handleEditRelationship(row, index) {
  resetRelForm()
  relEditMode.value = true
  Object.assign(relForm, row)
  editingRelIndex.value = index
  relDialogVisible.value = true
}

function entityExists(name, type) {
  return graphData.value.triples.some(
    t => t.subject === name && t.subject_type === type
  )
}

function confirmRelSave() {
  if (!relForm.subject.trim() || !relForm.predicate.trim() || !relForm.object.trim()) {
    ElMessage.warning('请填写完整关系信息')
    return
  }

  const subject = relForm.subject.trim()
  const subjectType = relForm.subject_type.trim() || '实体'
  const object = relForm.object.trim()
  const objectType = relForm.object_type.trim() || '文本'

  // 关系两端必须是已存在的实体（在图谱中有以该实体为主语的三元组）
  if (!entityExists(subject, subjectType)) {
    ElMessage.warning(`主语实体不存在：${subject}（${subjectType}）`)
    return
  }
  if (!entityExists(object, objectType)) {
    ElMessage.warning(`宾语实体不存在：${object}（${objectType}）`)
    return
  }

  const newTriple = {
    subject,
    subject_type: subjectType,
    predicate: relForm.predicate.trim(),
    object,
    object_type: objectType
  }

  if (relEditMode.value && editingRelIndex.value >= 0) {
    graphData.value.triples[editingRelIndex.value] = newTriple
  } else {
    graphData.value.triples.push(newTriple)
  }
  graphData.value.total_triples = graphData.value.triples.length
  relDialogVisible.value = false
  refreshGraphIfVisible()
  ElMessage.success(relEditMode.value ? '关系更新成功（尚未保存到 Neo4j 中）' : '关系新增成功（尚未保存到 Neo4j 中）')
}

function handleDeleteEntity(row) {
  const triples = graphData.value.triples
  for (let i = triples.length - 1; i >= 0; i--) {
    const t = triples[i]
    // 删除以该实体为主语的所有属性/关系，以及以该实体为宾语的所有关系
    if (
      (t.subject === row.subject && t.subject_type === row.subject_type) ||
      (t.object === row.subject && t.object_type === row.subject_type)
    ) {
      triples.splice(i, 1)
    }
  }
  graphData.value.total_triples = triples.length
  refreshGraphIfVisible()
  ElMessage.success('实体及其关联关系删除成功（尚未保存到 Neo4j 中）')
}

function handleDeleteRelationship(index) {
  graphData.value.triples.splice(index, 1)
  graphData.value.total_triples = graphData.value.triples.length
  refreshGraphIfVisible()
  ElMessage.success('关系删除成功（尚未保存到 Neo4j 中）')
}

// 三元组查看
const triplesDialogVisible = ref(false)
const selectedEntityTriples = ref([])

function handleShowTriples(row) {
  selectedEntityTriples.value = graphData.value.triples.filter(t => t.subject === row.subject)
  triplesDialogVisible.value = true
}

// 保存 JSON
async function handleSaveJson() {
  saving.value = true
  try {
    const res = await saveGraphJson(graphData.value)
    if (res.success || res.code === 200) {
      ElMessage.success('已保存')
      loadJson()
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// ============ 图谱视图（图数据库视角） ============

const graphRef = ref(null)
let network = null
const selectedGraphNode = ref(null)
const selectedGraphEdge = ref(null)

const selectedLabel = ref('')
const labels = ref([])
const relTypes = ref([])
const allNodeMap = ref(new Map())
const allEdgeMap = ref(new Map())
const canvasNodeMap = ref(new Map())
const canvasEdgeMap = ref(new Map())
const expandedNodes = ref(new Set())
const expansionMap = ref(new Map())
const graphSearchKeyword = ref('')

const canvasNodes = computed(() => Array.from(canvasNodeMap.value.values()))
const canvasEdges = computed(() => Array.from(canvasEdgeMap.value.values()))

const graphSearchResults = computed(() => {
  const kw = graphSearchKeyword.value.trim()
  if (!kw) return []
  return Array.from(allNodeMap.value.values())
    .filter(n => n.label && n.label.includes(kw))
    .slice(0, 20)
})

const colorPalette = ['#f5222d', '#fa8c16', '#faad14', '#52c41a', '#13c2c2', '#1890ff', '#2f54eb', '#722ed1', '#eb2f96', '#8c8c8c', '#a0d911', '#1677ff', '#e91e63', '#00bcd4', '#ff5722']
const labelColorCache = new Map()
let colorIdx = 0

const presetColors = {
  '受灾点': '#f5222d',
  '物资仓库': '#1890ff',
  '物资': '#1890ff',
  '救援队伍': '#fa8c16',
  '避难场所': '#52c41a',
  '道路': '#8c8c8c',
  '调度指令': '#722ed1',
  '地点': '#faad14',
  '危险等级': '#cf1322',
  '受灾人数': '#e67022',
  '灾害类型': '#531dab',
  '地点名称': '#d48806',
  '状态': '#bfbfbf',
  '队伍类型': '#d46b08',
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
  'Incident': '#f5222d',
  'Resource': '#1890ff',
  'DispatchOrder': '#722ed1',
  'Location': '#faad14',
  'RiskLevel': '#cf1322',
  'AffectedCount': '#e67022',
  'DisasterType': '#531dab',
  'Road': '#8c8c8c',
  'PlaceName': '#d48806'
}

const LEVEL1_ENTITIES = new Set(['受灾点', '物资仓库', '救援队伍', '避难场所', '道路', 'Incident', 'Resource', 'DispatchOrder', 'Location'])

function buildNodeId(name, type) {
  return `${type}:${name}`
}

function buildEdgeId(fromId, toId, predicate) {
  return `${fromId}|${predicate}|${toId}`
}

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
    nodeMap.get(subId).properties[t.predicate] = t.object

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
        label: t.predicate,
        fromName: t.subject,
        toName: t.object
      })
      relCount.set(t.predicate, (relCount.get(t.predicate) || 0) + 1)
    }
  })

  return { nodeMap, edgeMap, labelCount, relCount }
}

function loadGraphData() {
  const { nodeMap, edgeMap, labelCount, relCount } = parseTriples(graphData.value.triples || [])
  allNodeMap.value = nodeMap
  allEdgeMap.value = edgeMap
  labels.value = Array.from(labelCount.entries())
    .map(([label, count]) => ({ label, displayName: label, count }))
    .sort((a, b) => b.count - a.count)
  relTypes.value = Array.from(relCount.entries())
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count)
}

function getNeighborEdges(nodeId) {
  return graphData.value.triples.filter(t =>
    buildNodeId(t.subject, t.subject_type) === nodeId ||
    buildNodeId(t.object, t.object_type) === nodeId
  )
}

function loadLabelNodes(label) {
  if (!label) return
  loading.value = true
  selectedGraphNode.value = null
  selectedGraphEdge.value = null
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
    allEdgeMap.value.forEach(edge => {
      if (canvasNodeMap.value.has(edge.from) && canvasNodeMap.value.has(edge.to)) {
        canvasEdgeMap.value.set(edge.id, edge)
      }
    })
    selectedLabel.value = label
    nextTick(() => renderGraph())
  } catch (e) {
    console.error('加载节点失败:', e)
  } finally {
    loading.value = false
  }
}

let physicsStopTimer = null

function buildVisNodes() {
  return canvasNodes.value.map(n => {
    const isLevel1 = LEVEL1_ENTITIES.has(n.group) || LEVEL1_ENTITIES.has(n.rawLabel)
    const bgColor = getLabelColor(n.group)
    return {
      id: n.id,
      label: n.label || '未命名',
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
      shadow: isLevel1 ? { enabled: true, color: 'rgba(0,0,0,0.2)', size: 8, x: 2, y: 2 } : false
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
    network.once('stabilizationIterationsDone', () => {
      setPhysicsStatic()
    })
  }
}

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

function bindEvents() {
  network.on('doubleClick', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      toggleExpand(nodeId)
    } else if (params.edges.length > 0) {
      editSelectedGraphItem()
    }
  })

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      selectedGraphNode.value = canvasNodeMap.value.get(nodeId) || null
      selectedGraphEdge.value = null
    } else if (params.edges.length > 0) {
      const edgeId = params.edges[0]
      selectedGraphEdge.value = canvasEdgeMap.value.get(edgeId) || null
      selectedGraphNode.value = null
    } else {
      selectedGraphNode.value = null
      selectedGraphEdge.value = null
    }
  })

  network.on('dragStart', (params) => {
    if (params.nodes.length > 0) {
      setPhysicsElastic(3000)
    }
  })

  network.on('dragEnd', (params) => {
    if (params.nodes.length > 0) {
      setPhysicsElastic(2000)
    }
  })

  network.on('zoom', () => {
    if (physicsStopTimer) clearTimeout(physicsStopTimer)
  })
}

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

    allEdgeMap.value.forEach(edge => {
      if (canvasNodeMap.value.has(edge.from) && canvasNodeMap.value.has(edge.to)) {
        canvasEdgeMap.value.set(edge.id, edge)
      }
    })

    expandedNodes.value.add(nodeId)
    expansionMap.value.set(nodeId, { neighborIds, edgeIds })
    await nextTick()
    renderGraph()
    setPhysicsElastic(2500)
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
    edgeIds.forEach(eid => canvasEdgeMap.value.delete(eid))

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
    if (selectedGraphNode.value && !canvasNodeMap.value.has(selectedGraphNode.value.id)) {
      selectedGraphNode.value = null
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
  if (selectedGraphNode.value) {
    toggleExpand(selectedGraphNode.value.id)
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

function onGraphSearchSelect(node) {
  if (!node) return
  // 切到该节点所属类别
  loadLabelNodes(node.group)
  nextTick(() => {
    // 把节点加入画布（如果只是邻居节点可能还没显示）
    if (!canvasNodeMap.value.has(node.id)) {
      canvasNodeMap.value.set(node.id, node)
      allEdgeMap.value.forEach(edge => {
        if (canvasNodeMap.value.has(edge.from) && canvasNodeMap.value.has(edge.to)) {
          canvasEdgeMap.value.set(edge.id, edge)
        }
      })
      renderGraph()
    }
    selectedGraphNode.value = node
    selectedGraphEdge.value = null
    if (network) {
      network.selectNodes([node.id])
      network.focus(node.id, { scale: 1.2, animation: { duration: 400, easingFunction: 'easeInOutQuad' } })
    }
  })
}

function showAllGraph() {
  loading.value = true
  selectedGraphNode.value = null
  selectedGraphEdge.value = null
  expandedNodes.value.clear()
  expansionMap.value.clear()
  selectedLabel.value = ''
  if (network) {
    network.destroy()
    network = null
  }
  try {
    canvasNodeMap.value.clear()
    canvasEdgeMap.value.clear()
    allNodeMap.value.forEach(node => canvasNodeMap.value.set(node.id, node))
    allEdgeMap.value.forEach(edge => canvasEdgeMap.value.set(edge.id, edge))
    nextTick(() => {
      renderGraph()
      setPhysicsElastic(2500)
    })
  } catch (e) {
    console.error('显示全部图谱失败:', e)
  } finally {
    loading.value = false
  }
}

function refreshGraphDatabaseView() {
  loadGraphData()
  const target = selectedLabel.value && labels.value.some(l => l.label === selectedLabel.value)
    ? selectedLabel.value
    : (labels.value[0]?.label || '')
  if (target) {
    loadLabelNodes(target)
  } else {
    canvasNodeMap.value.clear()
    canvasEdgeMap.value.clear()
    expandedNodes.value.clear()
    expansionMap.value.clear()
    selectedGraphNode.value = null
    selectedGraphEdge.value = null
    if (network) {
      network.destroy()
      network = null
    }
  }
}

function onViewModeChange() {
  if (viewMode.value === 'graph') {
    nextTick(() => refreshGraphDatabaseView())
  }
}

function clearGraphSelection() {
  selectedGraphNode.value = null
  selectedGraphEdge.value = null
  if (network) network.unselectAll()
}

function editSelectedGraphItem() {
  if (selectedGraphNode.value) {
    const name = selectedGraphNode.value.label
    const type = selectedGraphNode.value.group
    const props = {}
    graphData.value.triples.filter(t => t.subject === name).forEach(t => {
      props[t.predicate] = t.object
    })
    handleEditEntity({
      subject: name,
      subject_type: type,
      properties: props
    })
  } else if (selectedGraphEdge.value) {
    const edge = selectedGraphEdge.value
    const tripleIndex = graphData.value.triples.findIndex(t =>
      buildNodeId(t.subject, t.subject_type) === edge.from &&
      buildNodeId(t.object, t.object_type) === edge.to &&
      t.predicate === edge.label
    )
    if (tripleIndex >= 0) {
      handleEditRelationship(graphData.value.triples[tripleIndex], tripleIndex)
    }
  }
}

function deleteSelectedGraphNode() {
  if (!selectedGraphNode.value) return
  const node = selectedGraphNode.value
  const sepIndex = node.id.indexOf(':')
  const nodeType = node.id.slice(0, sepIndex)
  const nodeName = node.id.slice(sepIndex + 1)
  const triples = graphData.value.triples
  for (let i = triples.length - 1; i >= 0; i--) {
    const t = triples[i]
    if (
      (t.subject === nodeName && t.subject_type === nodeType) ||
      (t.object === nodeName && t.object_type === nodeType)
    ) {
      triples.splice(i, 1)
    }
  }
  graphData.value.total_triples = triples.length
  selectedGraphNode.value = null
  refreshGraphDatabaseView()
  ElMessage.success('节点及其关联关系已删除（尚未保存到 Neo4j 中）')
}

function deleteSelectedGraphEdge() {
  if (!selectedGraphEdge.value) return
  const edge = selectedGraphEdge.value
  const triples = graphData.value.triples
  for (let i = triples.length - 1; i >= 0; i--) {
    const t = triples[i]
    if (
      buildNodeId(t.subject, t.subject_type) === edge.from &&
      buildNodeId(t.object, t.object_type) === edge.to &&
      t.predicate === edge.label
    ) {
      triples.splice(i, 1)
      break
    }
  }
  graphData.value.total_triples = triples.length
  selectedGraphEdge.value = null
  refreshGraphDatabaseView()
  ElMessage.success('关系已删除（尚未保存到 Neo4j 中）')
}

function openAddRelationshipFromGraph() {
  resetRelForm()
  relEditMode.value = false
  if (selectedGraphNode.value) {
    relForm.subject = selectedGraphNode.value.label
    relForm.subject_type = selectedGraphNode.value.group
  }
  relDialogVisible.value = true
}

onMounted(() => {
  loadJson()
})

onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
  if (physicsStopTimer) clearTimeout(physicsStopTimer)
})
</script>

<style scoped lang="scss">
.dispatch-manage-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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
  gap: 12px;
  align-items: center;
}

.table-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.property-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.hint {
  margin-top: 12px;
  color: #6b7280;
  font-size: 13px;
}

.graph-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  display: flex;
  height: calc(100vh - 180px);
  overflow: hidden;
}

.graph-side-panel {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding: 12px;
  border-right: 1px solid #e5e7eb;
  background: #fafafa;
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

.search-result-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 8px;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;

  &:hover {
    background: #f3f4f6;
  }
}

.search-result-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-result-type {
  font-size: 11px;
  color: #9ca3af;
  flex-shrink: 0;
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

.graph-panel {
  flex: 1;
  background: #fafafa;
  position: relative;
  overflow: hidden;
  min-width: 0;
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

.graph-tip {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.detail-panel {
  width: 280px;
  border-left: 1px solid #e5e7eb;
  padding: 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  word-break: break-all;
}

.detail-section {
  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f3f4f6;
  }
}

.prop-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prop-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  gap: 8px;
}

.prop-key {
  color: #6b7280;
  flex-shrink: 0;
}

.prop-val {
  color: #1f2937;
  word-break: break-all;
  text-align: right;
}

.detail-row {
  color: #6b7280;
  font-size: 13px;
}

.detail-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
