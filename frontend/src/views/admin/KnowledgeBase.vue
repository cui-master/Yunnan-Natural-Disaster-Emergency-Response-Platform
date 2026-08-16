<template>
  <div class="kb-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#1890ff"><Reading /></el-icon>
        <span>知识库管理</span>
        <el-tag type="info" effect="light" size="small">Dify 知识库</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新建知识库
        </el-button>
        <el-button :icon="Upload" @click="handleOpenUploadDialog">
          上传文档
        </el-button>
      </div>
    </div>

    <div class="content">
      <div class="table-card">
        <div class="search-bar">
          <el-input v-model="searchKeyword" placeholder="搜索知识库名称" style="width: 240px;" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 140px;">
            <el-option label="启用" value="启用" />
            <el-option label="禁用" value="禁用" />
          </el-select>
          <el-button :icon="Refresh" @click="loadData">刷新</el-button>
        </div>

        <el-table
          :data="filteredData"
          stripe
          style="width: 100%"
          v-loading="loading"
          border
          @row-dblclick="handleRowDblClick"
        >
          <el-table-column prop="name" label="知识库名称" min-width="200">
            <template #default="{ row }">
              <div class="kb-name">
                <el-icon color="#1890ff"><Collection /></el-icon>
                {{ row.name }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="140" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.enabled"
                :active-text="'启用'"
                :inactive-text="'禁用'"
                @change="(val) => handleToggleStatus(row, val)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="160" />
          <el-table-column prop="updatedAt" label="更新时间" width="160" />
          <el-table-column label="操作" width="280" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleOpenDocList(row)">文档列表</el-button>
              <el-button size="small" type="success" link @click="handleEdit(row)">编辑</el-button>
              <el-popconfirm title="确定删除该知识库吗？" @confirm="handleDelete(row)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            background
          />
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" @closed="formRef?.resetFields()">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="formData.type" style="width: 100%;">
            <el-option label="优化调度" value="优化调度" />
            <el-option label="风险评估" value="风险评估" />
            <el-option label="应急管理" value="应急管理" />
            <el-option label="案例库" value="案例库" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="可选，简要描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio value="启用">启用</el-radio>
            <el-radio value="禁用">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档到知识库" width="480px" @closed="resetUploadForm">
      <el-form label-width="100px">
        <el-form-item label="目标知识库" required>
          <el-select v-model="uploadKbId" style="width: 100%;" placeholder="请选择知识库">
            <el-option
              v-for="kb in tableData"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <el-button :icon="Document">选择文件</el-button>
            <template #tip>
              <div class="upload-tip">支持 pdf / doc / docx / txt / md 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUploadDoc">上传</el-button>
      </template>
    </el-dialog>

    <!-- 文档列表弹窗 -->
    <el-dialog v-model="docDialogVisible" :title="`${currentKb?.name || '知识库'} - 文档列表`" width="760px">
      <div v-if="currentKb" class="doc-tip">双击知识库名称可打开此窗口。以下文档已同步到 Dify 知识库。</div>
      <el-table :data="docList" stripe v-loading="docLoading" border style="width: 100%;">
        <el-table-column prop="name" label="文档名称" min-width="200" />
        <el-table-column prop="fileType" label="类型" width="120" />
        <el-table-column prop="fileSize" label="大小" width="120">
          <template #default="{ row }">{{ formatFileSize(row.fileSize) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '可用' : '错误' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="上传时间" width="160" />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确定删除该文档吗？" @confirm="handleDeleteDocument(row)">
              <template #reference>
                <el-button size="small" type="danger" link :icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getKnowledgeList, addKnowledge, updateKnowledge, deleteKnowledge,
  toggleKnowledgeStatus, uploadKnowledgeDoc, getKnowledgeDocuments, deleteKnowledgeDocument
} from '@/api'
import { Reading, Plus, Upload, Search, Refresh, Collection, Document, Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const searchKeyword = ref('')
const statusFilter = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)

const uploadDialogVisible = ref(false)
const uploadKbId = ref('')
const uploadFile = ref(null)
const uploading = ref(false)

const docDialogVisible = ref(false)
const currentKb = ref(null)
const docList = ref([])
const docLoading = ref(false)

const formData = reactive({
  id: '',
  name: '',
  type: '优化调度',
  description: '',
  status: '启用'
})

const formRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑知识库' : '新建知识库')

const filteredData = computed(() => {
  return tableData.value.filter(item => {
    const matchKeyword = !searchKeyword.value || item.name.includes(searchKeyword.value)
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchKeyword && matchStatus
  })
})

async function loadData() {
  loading.value = true
  try {
    const params = {
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value || undefined,
      status: statusFilter.value !== '' ? (statusFilter.value === '启用' ? 1 : 0) : undefined
    }
    const res = await getKnowledgeList(params)
    if (res.success) {
      tableData.value = (res.data.records || res.data.list || []).map(item => mapBackendToFrontend(item))
      total.value = res.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

function mapBackendToFrontend(item) {
  const enabled = item.status === 1
  return {
    id: item.id,
    name: item.name || '',
    type: item.category || '-',
    docCount: item.documentCount || 0,
    status: enabled ? '启用' : '禁用',
    enabled,
    description: item.description || '',
    kbId: item.kbId || '',
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
    _raw: item
  }
}

function mapFrontendToBackend(form) {
  return {
    id: form.id || undefined,
    name: form.name,
    category: form.type,
    description: form.description,
    status: form.status === '启用' ? 1 : 0,
    documentCount: 0
  }
}

function handleAdd() {
  isEdit.value = false
  formData.id = ''
  formData.name = ''
  formData.type = '优化调度'
  formData.description = ''
  formData.status = '启用'
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完善必填信息')
    return
  }

  saving.value = true
  try {
    const payload = mapFrontendToBackend(formData)
    if (isEdit.value) {
      const res = await updateKnowledge(formData.id, payload)
      if (res.success) {
        ElMessage.success('更新成功')
        loadData()
      }
    } else {
      const res = await addKnowledge(payload)
      if (res.success) {
        ElMessage.success('创建成功')
        loadData()
      }
    }
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  const res = await deleteKnowledge(row.id)
  if (res.success) {
    ElMessage.success('删除成功')
    loadData()
  }
}

async function handleToggleStatus(row, val) {
  const statusText = val ? '启用' : '禁用'
  const statusNum = val ? 1 : 0
  try {
    await ElMessageBox.confirm(
      `确定${statusText}知识库「${row.name}」吗？`,
      '确认操作',
      { type: 'warning' }
    )
    const res = await toggleKnowledgeStatus(row.id, statusNum)
    if (res.success) {
      ElMessage.success(`已${statusText}`)
      loadData()
    }
  } catch {
    row.enabled = !val
  }
}

const uploadRef = ref(null)

function handleOpenUploadDialog() {
  uploadKbId.value = ''
  uploadFile.value = null
  uploadDialogVisible.value = true
}

function resetUploadForm() {
  uploadKbId.value = ''
  uploadFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

function handleFileChange(file) {
  uploadFile.value = file.raw
}

function handleFileRemove() {
  uploadFile.value = null
}

async function handleUploadDoc() {
  if (!uploadKbId.value) {
    ElMessage.warning('请选择目标知识库')
    return
  }
  if (!uploadFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    const res = await uploadKnowledgeDoc(uploadKbId.value, formData)
    if (res.success) {
      ElMessage.success('文档上传成功，正在解析...')
      uploadDialogVisible.value = false
      resetUploadForm()
      loadData()
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function handleRowDblClick(row) {
  handleOpenDocList(row)
}

function handleOpenDocList(row) {
  currentKb.value = row
  docDialogVisible.value = true
  loadDocuments(row.id)
}

async function loadDocuments(kbId) {
  docLoading.value = true
  try {
    const res = await getKnowledgeDocuments(kbId)
    if (res.success) {
      docList.value = res.data || []
    }
  } finally {
    docLoading.value = false
  }
}

async function handleDeleteDocument(row) {
  const res = await deleteKnowledgeDocument(row.id)
  if (res.success) {
    ElMessage.success('删除成功')
    loadDocuments(currentKb.value.id)
    loadData()
  }
}

function formatFileSize(size) {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  if (size < 1024 * 1024 * 1024) return (size / 1024 / 1024).toFixed(2) + ' MB'
  return (size / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.kb-page {
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
  gap: 10px;
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

.kb-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.upload-tip {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
}

.doc-tip {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 12px;
}
</style>
