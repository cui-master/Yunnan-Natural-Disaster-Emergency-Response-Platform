<script setup lang="ts">
<<<<<<< HEAD
import { onMounted, reactive, ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useKnowledgeKitStore } from '@/stores/knowledgeKit'
import { listKnowledgeKitDocs } from '@/api/knowledgeKit'
import { KNOWLEDGE_KITS, type KnowledgeKitMeta, type KnowledgeKitDoc } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'

const kitStore = useKnowledgeKitStore()
const { docs, loading, uploading, progress, bases } = storeToRefs(kitStore)

// 知识库注册表：优先取自 DB（/api/knowledge/bases），未取到时回退硬编码常量
const kits = ref<KnowledgeKitMeta[]>(KNOWLEDGE_KITS)
function syncKitsFromDb() {
  if (bases.value && bases.value.length) {
    kits.value = bases.value.map((b) => ({
      key: (b.kbKey === 'OPTIMIZE' ? 'OPTIMIZE' : 'RISK') as KnowledgeKitMeta['key'],
      name: b.kbName,
      datasetId: b.datasetId,
      desc: b.description
    }))
  }
}

const activeKey = ref<KnowledgeKitMeta['key']>('OPTIMIZE')
const activeKit = computed(() => kits.value.find((k) => k.key === activeKey.value)!)
const activeName = computed(() => activeKit.value.name)

const counts = reactive<Record<string, number>>({ OPTIMIZE: 0, RISK: 0 })
const statusText: Record<string, string> = { PARSING: '解析中', COMPLETED: '已完成', FAILED: '失败' }

function maskId(id: string) {
  return id.length > 14 ? id.slice(0, 8) + '…' + id.slice(-4) : id
}

async function loadAll() {
  for (const k of kits.value) {
    const resp = await listKnowledgeKitDocs(k.name).catch(() => ({ list: [] as KnowledgeKitDoc[] }))
    counts[k.key] = resp.list.length
  }
  await refresh()
}
async function refresh() {
  await kitStore.fetchDocs(activeName.value)
  counts[activeKey.value] = kitStore.docs.length
}

function selectKit(key: KnowledgeKitMeta['key']) {
  activeKey.value = key
  refresh()
}

// ----- 上传 -----
const dialog = ref(false)
const fileList = ref<File[]>([])

function onFileChange(file: any, list: any[]) {
  fileList.value = list.map((f) => f.raw).filter(Boolean)
}
function onFileRemove(_file: any, list: any[]) {
  fileList.value = list.map((f) => f.raw).filter(Boolean)
}
function openUpload() {
  fileList.value = []
  dialog.value = true
}

async function submitUpload() {
  if (!fileList.value.length) {
    ElMessage.warning('请先选择文件（支持 .txt / .pdf / .docx）')
    return
  }
  const r = await kitStore.upload(activeName.value, fileList.value)
  ElMessage.success(`已提交 ${fileList.value.length} 个文件至「${activeName.value}」知识库，后台正在解析切片`)
  dialog.value = false
  refresh()
}

async function removeDoc(row: KnowledgeKitDoc) {
  await ElMessageBox.confirm(`确认从「${activeName.value}」知识库删除「${row.name}」？删除后需重新上传更新。`, '提示', {
    type: 'warning'
  })
  await kitStore.remove(activeName.value, row.id)
  ElMessage.success('已删除')
  refresh()
}

onMounted(async () => {
  await kitStore.fetchBases()
  syncKitsFromDb()
  await loadAll()
})
=======
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { KnowledgeCategory, DisasterType, KnowledgeDoc } from '@/types'

const knowledge = useKnowledgeStore()
const { docs, loading } = storeToRefs(knowledge)

const categoryLabel: Record<string, string> = {
  EMERGENCY_PLAN: '应急预案',
  DISASTER_SPEC: '处置规范',
  LAW: '法律法规',
  CASE: '历史案例',
  GUIDE: '操作指南'
}
const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震', FLOOD: '洪涝', LANDSLIDE: '滑坡', DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱', FOREST_FIRE: '森林火灾', HAIL: '冰雹', TYPHOON: '台风'
}

const filterCategory = ref<KnowledgeCategory | ''>('')
const dialog = ref(false)
const form = reactive({
  title: '',
  category: 'EMERGENCY_PLAN' as KnowledgeCategory,
  tags: [] as string[],
  disasterTypes: [] as DisasterType[],
  fileUrl: ''
})
const uploadFileName = ref('')

function load() {
  knowledge.fetchDocs({ category: filterCategory.value || undefined })
}

function openUpload() {
  form.title = ''
  form.category = 'EMERGENCY_PLAN'
  form.tags = []
  form.disasterTypes = []
  form.fileUrl = ''
  uploadFileName.value = ''
  dialog.value = true
}

function onFileChange(file: any) {
  uploadFileName.value = file.name
  form.fileUrl = '/mock/kb/' + file.name
}

async function submitUpload() {
  if (!form.title || !form.fileUrl) {
    ElMessage.warning('请填写标题并上传文档')
    return
  }
  await knowledge.upload({
    title: form.title,
    category: form.category,
    tags: form.tags,
    disasterTypes: form.disasterTypes,
    fileUrl: form.fileUrl
  })
  ElMessage.success('已入库，文档已分块并向量化（RAG 可用）')
  dialog.value = false
  load()
}

async function remove(row: KnowledgeDoc) {
  await ElMessageBox.confirm(`确认从知识库删除「${row.title}」？`, '提示', { type: 'warning' })
  await knowledge.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
>>>>>>> feature-cui
</script>

<template>
  <div class="kb">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
<<<<<<< HEAD
          <div>
            <div class="section-title">知识库管理（Dify RAG）</div>
            <div class="head-sub">
              文件经 FastAPI ai_service 自动解析、切片、向量化入库；上传即提交任务，解析完成前不可检索。
            </div>
          </div>
        </div>
      </template>

      <!-- 知识库选择 -->
      <div class="kit-row">
        <button
          v-for="k in kits"
          :key="k.key"
          class="kit-card"
          :class="{ active: k.key === activeKey }"
          @click="selectKit(k.key)"
        >
          <div class="kit-top">
            <span class="kit-name">{{ k.name }}</span>
            <span class="kit-count">{{ counts[k.key] || 0 }} 篇</span>
          </div>
          <div class="kit-desc">{{ k.desc }}</div>
          <div class="kit-id">dataset: {{ maskId(k.datasetId) }}</div>
        </button>
      </div>

      <!-- 文档列表 -->
      <div class="doc-head">
        <div class="section-title">「{{ activeName }}」知识库文档</div>
        <el-button type="primary" :loading="uploading" @click="openUpload">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
      </div>

      <el-table :data="docs" v-loading="loading" border stripe empty-text="该知识库暂无文档">
        <el-table-column prop="name" label="文档名称" min-width="240" show-overflow-tooltip />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'COMPLETED' ? 'success' : row.status === 'FAILED' ? 'danger' : 'warning'"
              size="small"
              effect="light"
            >
              {{ statusText[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunkCount" label="分块数" width="100" />
        <el-table-column prop="wordCount" label="字数" width="100" />
        <el-table-column prop="uploadedAt" label="入库时间" min-width="170" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeDoc(row)">删除</el-button>
          </template>
=======
          <b>知识库管理</b>
          <div>
            <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width: 150px; margin-right: 10px" @change="load">
              <el-option v-for="(l, k) in categoryLabel" :key="k" :label="l" :value="k" />
            </el-select>
            <el-button type="primary" @click="openUpload"><el-icon><Plus /></el-icon> 入库文档</el-button>
          </div>
        </div>
      </template>
      <el-table :data="docs" v-loading="loading" border stripe>
        <el-table-column prop="title" label="文档标题" min-width="220" show-overflow-tooltip />
        <el-table-column label="分类" width="110">
          <template #default="{ row }">{{ categoryLabel[row.category] }}</template>
        </el-table-column>
        <el-table-column label="灾害类型" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="t in row.disasterTypes" :key="t" size="small" style="margin-right: 4px">{{ typeLabel[t] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunkCount" label="分块数" width="90" />
        <el-table-column prop="uploader" label="上传人" width="100" />
        <el-table-column prop="uploadedAt" label="上传时间" width="170" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }"><el-button link type="danger" @click="remove(row)">删除</el-button></template>
>>>>>>> feature-cui
        </el-table-column>
      </el-table>
    </el-card>

<<<<<<< HEAD
    <!-- 上传弹窗 -->
    <el-dialog v-model="dialog" title="上传文档至知识库" width="560px">
      <div class="up-target">
        目标知识库：<b>{{ activeName }}</b>
        <span class="up-id">（{{ maskId(activeKit.datasetId) }}）</span>
      </div>
      <el-upload
        drag
        multiple
        :auto-upload="false"
        accept=".txt,.pdf,.docx,.md"
        :on-change="onFileChange"
        :on-remove="onFileRemove"
        :file-list="[]"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 .txt / .pdf / .docx / .md，单个文件请控制大小</div>
        </template>
      </el-upload>

      <div v-if="fileList.length" class="up-files">
        <div v-for="f in fileList" :key="f.name" class="up-file">
          <el-icon><Document /></el-icon>
          <span class="up-file-name">{{ f.name }}</span>
          <span class="up-file-size">{{ (f.size / 1024).toFixed(1) }} KB</span>
        </div>
      </div>

      <el-progress
        v-if="uploading"
        :percentage="progress"
        :stroke-width="10"
        status="success"
        class="up-progress"
      />

      <div class="up-note">
        ⚠ Dify 原生 API 不支持修改已入库文档。如需更新，请先在本页删除旧文档，再上传新版本，避免 RAG 研判冲突。
      </div>

      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">确认上传</el-button>
=======
    <el-dialog v-model="dialog" title="知识库文档入库" width="520px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="(l, k) in categoryLabel" :key="k" :label="l" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="灾害类型">
          <el-select v-model="form.disasterTypes" multiple style="width: 100%" placeholder="关联灾害类型">
            <el-option v-for="(l, k) in typeLabel" :key="k" :label="l" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width: 100%" placeholder="可输入自定义标签">
            <el-option v-for="t in ['地震', '滑坡', '泥石流', '森林', '干旱', '内涝', '预案', '案例']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="文档文件">
          <el-upload :auto-upload="false" :limit="1" :on-change="onFileChange" :show-file-list="true">
            <el-button>选择文件（PDF/Word/Markdown）</el-button>
          </el-upload>
          <span v-if="uploadFileName" class="text-muted">已选：{{ uploadFileName }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload">确认入库</el-button>
>>>>>>> feature-cui
      </template>
    </el-dialog>
  </div>
</template>
<<<<<<< HEAD

<style scoped>
.kit-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 18px;
}
.kit-card {
  text-align: left;
  border: 1.5px solid var(--ydr-border);
  background: var(--ydr-surface);
  border-radius: 14px;
  padding: 16px 18px;
  cursor: pointer;
  transition: border-color 0.18s var(--ease-out-quart), box-shadow 0.18s var(--ease-out-quart),
    transform 0.18s var(--ease-out-quart);
}
.kit-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ydr-shadow);
}
.kit-card.active {
  border-color: var(--ydr-primary);
  box-shadow: 0 8px 22px oklch(55% 0.2 25 / 0.16);
}
.kit-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.kit-name {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--ydr-ink);
}
.kit-count {
  font-size: 12px;
  color: var(--ydr-primary);
  background: var(--ydr-primary-soft);
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.kit-desc {
  margin: 8px 0 10px;
  font-size: 13px;
  color: var(--ydr-sub);
}
.kit-id {
  font-size: 11px;
  color: var(--ydr-sub);
  font-family: var(--font-display);
  opacity: 0.8;
}

.doc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 6px 0 12px;
}

.up-target {
  font-size: 13px;
  color: var(--ydr-text);
  margin-bottom: 12px;
}
.up-target b {
  color: var(--ydr-primary);
}
.up-id {
  color: var(--ydr-sub);
  font-family: var(--font-display);
  font-size: 12px;
}
.up-files {
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.up-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: 1px solid var(--ydr-border);
  border-radius: 9px;
  font-size: 13px;
  color: var(--ydr-text);
}
.up-file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.up-file-size {
  color: var(--ydr-sub);
  font-size: 12px;
}
.up-progress {
  margin: 4px 0 10px;
}
.up-note {
  margin-top: 10px;
  padding: 9px 12px;
  border-radius: 9px;
  background: var(--ydr-primary-soft);
  color: var(--ydr-primary-dark, var(--ydr-text));
  font-size: 12px;
  line-height: 1.6;
}
</style>
=======
>>>>>>> feature-cui
