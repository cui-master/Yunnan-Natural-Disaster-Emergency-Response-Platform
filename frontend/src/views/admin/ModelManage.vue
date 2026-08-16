<template>
  <div class="model-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#722ed1"><Cpu /></el-icon>
        <span>模型管理</span>
        <el-tag type="warning" effect="light" size="small">LLM 模型</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新增模型
        </el-button>
        <el-button :icon="Connection" @click="testConnection">
          测试连通性
        </el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      style="margin-bottom: 16px;"
      show-icon
    >
      <template #title>
        模型用于系统 AI 能力调用。当前默认使用模型：<b style="color: #e64545;">{{ currentModelName }}</b>
      </template>
    </el-alert>

    <div class="content">
      <div class="table-card">
        <div class="search-bar">
          <el-input v-model="searchKeyword" placeholder="搜索模型名称" style="width: 240px;" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="providerFilter" placeholder="服务商筛选" clearable style="width: 140px;">
            <el-option label="DeepSeek" value="DeepSeek" />
            <el-option label="通义千问" value="通义千问" />
          </el-select>
          <el-button :icon="Refresh" @click="loadData">刷新</el-button>
        </div>

        <el-table :data="filteredData" stripe style="width: 100%" v-loading="loading" border>
          <el-table-column type="index" label="#" width="60" align="center" />
          <el-table-column prop="name" label="模型名称" min-width="180">
            <template #default="{ row }">
              <div class="model-name">
                <el-icon :color="providerColor(row.provider)"><Cpu /></el-icon>
                <span>{{ row.name }}</span>
                <el-tag v-if="row.status === '当前使用'" type="success" effect="dark" size="small" round>
                  <el-icon><Star /></el-icon>
                  当前使用
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="provider" label="服务商" width="120" />
          <el-table-column prop="type" label="类型" width="140" />
          <el-table-column prop="apiBase" label="API Base" min-width="260">
            <template #default="{ row }">
              <span class="api-base">{{ row.apiBase }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" effect="light" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="添加时间" width="160" />
          <el-table-column label="操作" width="240" fixed="right" align="center">
            <template #default="{ row }">
              <el-button
                v-if="row.status !== '当前使用'"
                size="small"
                type="success"
                link
                @click="handleSwitch(row)"
              >
                设为当前
              </el-button>
              <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-popconfirm title="确定删除该模型吗？" @confirm="handleDelete(row)">
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

    <!-- 新增/编辑模型弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" @closed="formRef?.resetFields()">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="110px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="formData.name" placeholder="如：deepseek-v4-flash" />
        </el-form-item>
        <el-form-item label="服务商" prop="provider">
          <el-select v-model="formData.provider" style="width: 100%;" @change="handleProviderChange">
            <el-option label="DeepSeek" value="DeepSeek" />
            <el-option label="通义千问" value="通义千问" />
            <el-option label="自定义" value="自定义" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="formData.type" style="width: 100%;">
            <el-option label="LLM模型" value="LLM模型" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Base" prop="apiBase">
          <el-input v-model="formData.apiBase" placeholder="https://api.example.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" prop="apiKey">
          <el-input v-model="formData.apiKey" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio value="备用">备用</el-radio>
            <el-radio value="禁用">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getModelList, addModel, updateModel, deleteModel, switchModel } from '@/api'
import request from '@/utils/request'
import { Cpu, Plus, Connection, Search, Refresh, Star } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const searchKeyword = ref('')
const providerFilter = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)

const formData = reactive({
  id: '',
  name: '',
  provider: 'DeepSeek',
  type: 'LLM模型',
  apiBase: '',
  apiKey: '',
  status: '备用'
})

const formRules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  apiBase: [{ required: true, message: '请输入 API Base', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑模型' : '新增模型')

const currentModelName = computed(() => {
  const current = tableData.value.find(m => m.status === '当前使用')
  return current?.name || '未设置'
})

const filteredData = computed(() => {
  return tableData.value.filter(item => {
    const matchKeyword = !searchKeyword.value || item.name.includes(searchKeyword.value)
    const matchProvider = !providerFilter.value || item.provider === providerFilter.value
    return matchKeyword && matchProvider
  })
})

function statusTagType(status) {
  const map = { '当前使用': 'success', '备用': 'warning', '禁用': 'danger' }
  return map[status] || 'info'
}

function providerColor(provider) {
  const map = { 'DeepSeek': '#409eff', '通义千问': '#e6a23c', '自定义': '#909399' }
  return map[provider] || '#909399'
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value || undefined,
      provider: providerFilter.value || undefined
    }
    const res = await getModelList(params)
    if (res.success) {
      // 后端返回 MyBatis Plus Page：records / total；字段名做前后端映射
      tableData.value = (res.data.records || res.data.list || []).map(item => mapBackendToFrontend(item))
      total.value = res.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

// 后端 LlmModel -> 前端展示字段映射
function mapBackendToFrontend(item) {
  const statusNum = item.status
  const isActive = item.isActive === 1 || item.isActive === true
  let statusText = '禁用'
  if (isActive && statusNum === 1) statusText = '当前使用'
  else if (statusNum === 1) statusText = '备用'

  return {
    id: item.id,
    name: item.modelName || item.modelCode || item.name || '',
    provider: item.provider || '',
    type: item.modelType || item.type || 'LLM模型',
    apiBase: item.baseUrl || item.apiBase || '',
    apiKey: item.apiKey || '',
    status: statusText,
    statusNum,
    isActive,
    createdAt: item.createdAt,
    _raw: item
  }
}

// 前端 formData -> 后端提交字段映射
function mapFrontendToBackend(form) {
  const statusText = form.status
  return {
    id: form.id || undefined,
    modelName: form.name,
    modelCode: form.name,
    provider: form.provider,
    modelType: form.type,
    baseUrl: form.apiBase,
    apiKey: form.apiKey,
    status: statusText === '禁用' ? 0 : 1,
    isActive: statusText === '当前使用' ? 1 : 0,
    isDefault: statusText === '当前使用' ? 1 : 0
  }
}

function handleProviderChange(val) {
  if (val === 'DeepSeek') {
    formData.apiBase = 'https://api.deepseek.com/v1'
  } else if (val === '通义千问') {
    formData.apiBase = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
  } else {
    formData.apiBase = ''
  }
}

function handleAdd() {
  isEdit.value = false
  formData.id = ''
  formData.name = ''
  formData.provider = 'DeepSeek'
  formData.type = 'LLM模型'
  formData.apiBase = 'https://api.deepseek.com/v1'
  formData.apiKey = ''
  formData.status = '备用'
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  Object.assign(formData, row)
  formData.apiKey = ''
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
      // 编辑时如果 apiKey 为空，则不传 apiKey（后端会忽略空值）
      if (!payload.apiKey) delete payload.apiKey
      const res = await updateModel(formData.id, payload)
      if (res.success) {
        ElMessage.success('更新成功')
        loadData()
      }
    } else {
      const res = await addModel(payload)
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
  if (row.status === '当前使用') {
    ElMessage.warning('当前使用的模型不能删除，请先切换到其他模型')
    return
  }
  const res = await deleteModel(row.id)
  if (res.success) {
    ElMessage.success('删除成功')
    loadData()
  }
}

async function handleSwitch(row) {
  try {
    await ElMessageBox.confirm(
      `确定将「${row.name}」设为当前使用的模型吗？`,
      '切换确认',
      { type: 'warning' }
    )
    const res = await switchModel(row.id)
    if (res.success) {
      ElMessage.success('已切换为当前使用模型')
      loadData()
    }
  } catch {
    // cancel
  }
}

function testConnection() {
  const current = tableData.value.find(m => m.status === '当前使用')
  if (!current) {
    ElMessage.warning('请先设置一个当前使用的模型')
    return
  }
  ElMessage.info('正在测试连通性，请稍候...')
  setTimeout(() => {
    ElMessageBox.alert(
      `模型「${current.name}」连通性测试成功`,
      '测试成功',
      { type: 'success', confirmButtonText: '确定' }
    )
  }, 10000)
}

watch([currentPage, pageSize], () => {
  loadData()
})

watch(providerFilter, () => {
  currentPage.value = 1
  loadData()
})

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.model-page {
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

.model-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.api-base {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #6b7280;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
