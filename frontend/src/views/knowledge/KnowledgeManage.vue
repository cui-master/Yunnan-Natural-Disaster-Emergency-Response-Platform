<script setup lang="ts">
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
</script>

<template>
  <div class="kb">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
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
        </el-table-column>
      </el-table>
    </el-card>

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
      </template>
    </el-dialog>
  </div>
</template>
