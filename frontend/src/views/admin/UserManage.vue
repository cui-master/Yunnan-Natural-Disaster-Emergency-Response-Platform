<template>
  <div class="user-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#e64545"><User /></el-icon>
        <span>用户管理</span>
        <el-tag type="info" effect="light" size="small">RBAC 角色权限</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新增用户
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="user-tabs">
      <el-tab-pane label="用户管理" name="users" />
      <el-tab-pane label="角色权限" name="roles" />
    </el-tabs>

    <div v-show="activeTab === 'users'" class="content">
      <div class="table-card">
        <div class="search-bar">
          <el-input v-model="searchKeyword" placeholder="搜索用户名/姓名" style="width: 240px;" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width: 140px;">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.roleName"
              :value="role.roleCode"
            />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 140px;">
            <el-option label="启用" value="启用" />
            <el-option label="禁用" value="禁用" />
          </el-select>
          <el-button :icon="Refresh" @click="loadData">刷新</el-button>
        </div>

        <el-table :data="filteredData" stripe style="width: 100%" v-loading="loading" border>
          <el-table-column type="index" label="#" width="60" align="center" />
          <el-table-column prop="username" label="用户名" width="140" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="role" label="角色" width="140">
            <template #default="{ row }">
              <el-tag :type="roleTagType(row.role)" effect="light" size="small">
                {{ row.roleName }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="联系电话" width="140" />
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
          <el-table-column prop="lastLogin" label="最近登录" width="180" />
          <el-table-column label="操作" width="240" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="warning" link @click="handleResetPassword(row)">重置密码</el-button>
              <el-popconfirm title="确定删除该用户吗？" @confirm="handleDelete(row)">
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

    <div v-show="activeTab === 'roles'" class="content">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
        <template #title>
          系统角色从 role 表加载，角色编码与 users 表的 role_code 字段一一对应。
        </template>
      </el-alert>
      <el-row v-loading="rolesLoading" :gutter="16">
        <el-col :xs="24" :sm="12" :md="6" v-for="role in roleList" :key="role.id">
          <div class="role-card">
            <div class="role-header">
              <div
                class="role-icon"
                :style="{
                  background: (roleMeta[role.roleCode]?.color || '#909399') + '15',
                  color: roleMeta[role.roleCode]?.color || '#909399'
                }"
              >
                <el-icon :size="28"><component :is="roleMeta[role.roleCode]?.icon || 'User'" /></el-icon>
              </div>
              <div class="role-name">{{ role.roleName }}</div>
            </div>
            <div class="role-desc">{{ role.description || '-' }}</div>
            <div class="role-count">{{ roleStats[role.roleCode]?.count || 0 }} 位用户</div>
            <div class="role-status">
              <el-switch
                v-model="role.enabled"
                :active-text="'启用'"
                :inactive-text="'禁用'"
                @change="(val) => handleToggleRoleStatus(role, val)"
              />
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 新增/编辑用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" @closed="formRef?.resetFields()">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" style="width: 100%;" placeholder="请选择角色">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.roleName"
              :value="role.roleCode"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="手机号码" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="电子邮箱" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="formData.department" placeholder="所属部门" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <el-input v-model="formData.password" type="password" placeholder="默认 123456" />
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, addUser, updateUser, deleteUser, toggleUserStatus, resetUserPassword, getRoleList, getRoleStats, toggleRoleStatus } from '@/api'
import {
  User, Plus, Search, Refresh, EditPen, DataLine, Share, Setting
} from '@element-plus/icons-vue'

const activeTab = ref('users')
const loading = ref(false)
const tableData = ref([])
const searchKeyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref(null)

const rolesLoading = ref(false)
const roleList = ref([])
const roleStats = ref({})

const roleMeta = {
  reporter: { icon: 'EditPen', color: '#52c41a' },
  commander: { icon: 'DataLine', color: '#fa8c16' },
  resmanager: { icon: 'Share', color: '#1890ff' },
  admin: { icon: 'Setting', color: '#722ed1' }
}

const formData = reactive({
  id: '',
  username: '',
  name: '',
  role: 'reporter',
  phone: '',
  email: '',
  department: '',
  password: '123456',
  status: '启用'
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const filteredData = computed(() => {
  return tableData.value.filter(item => {
    const matchKeyword = !searchKeyword.value ||
      item.username.includes(searchKeyword.value) ||
      item.name.includes(searchKeyword.value)
    const matchRole = !roleFilter.value || item.role === roleFilter.value
    return matchKeyword && matchRole
  })
})

function roleTagType(role) {
  const map = {
    reporter: 'success',
    commander: 'warning',
    resmanager: 'info',
    admin: 'danger'
  }
  return map[role] || 'info'
}

async function loadRoles() {
  rolesLoading.value = true
  try {
    const [listRes, statsRes] = await Promise.all([getRoleList(), getRoleStats()])
    if (listRes.success) {
      roleList.value = (listRes.data || []).map(r => ({
        ...r,
        enabled: r.status === 1
      }))
    }
    if (statsRes.success) {
      roleStats.value = statsRes.data || {}
    }
  } finally {
    rolesLoading.value = false
  }
}

async function handleToggleRoleStatus(role, val) {
  const statusText = val ? '启用' : '禁用'
  const statusNum = val ? 1 : 0
  try {
    await ElMessageBox.confirm(
      `确定${statusText}角色「${role.roleName}」吗？`,
      '确认操作',
      { type: 'warning' }
    )
    const res = await toggleRoleStatus(role.id, statusNum)
    if (res.success) {
      ElMessage.success(`已${statusText}`)
      loadRoles()
    }
  } catch {
    role.enabled = !val
  }
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      roleCode: roleFilter.value || undefined,
      status: statusFilter.value !== '' ? (statusFilter.value === '启用' ? 1 : 0) : undefined,
      keyword: searchKeyword.value || undefined
    }
    const res = await getUserList(params)
    if (res.success) {
      tableData.value = (res.data.records || res.data.list || []).map(item => mapBackendToFrontend(item))
      total.value = res.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

function getRoleName(roleCode) {
  const found = roleList.value.find(r => r.roleCode === roleCode)
  if (found) return found.roleName
  const roleMap = {
    reporter: '普通信息员',
    commander: '应急指挥员',
    resmanager: '资源管理员',
    admin: '系统管理员'
  }
  return roleMap[roleCode] || roleCode || '-'
}

function mapBackendToFrontend(item) {
  const enabled = item.status === 1
  return {
    id: item.id,
    username: item.username || '',
    name: item.realName || '',
    role: item.roleCode || '',
    roleName: getRoleName(item.roleCode),
    phone: item.phone || '',
    email: item.email || '',
    department: item.department || '',
    status: enabled ? '启用' : '禁用',
    enabled,
    lastLogin: item.lastLoginAt,
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
    _raw: item
  }
}

function mapFrontendToBackend(form) {
  return {
    id: form.id || undefined,
    username: form.username,
    realName: form.name,
    roleCode: form.role,
    phone: form.phone,
    email: form.email || null,
    department: form.department || null,
    password: form.password || undefined,
    status: form.status === '启用' ? 1 : 0
  }
}

function handleAdd() {
  isEdit.value = false
  formData.id = ''
  formData.username = ''
  formData.name = ''
  formData.role = 'reporter'
  formData.phone = ''
  formData.email = ''
  formData.department = ''
  formData.password = '123456'
  formData.status = '启用'
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  Object.assign(formData, row)
  formData.password = ''
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
      // 编辑时密码为空则不更新密码
      if (!payload.password) delete payload.password
      const res = await updateUser(formData.id, payload)
      if (res.success) {
        ElMessage.success('更新成功')
        loadData()
      }
    } else {
      const res = await addUser(payload)
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
  const res = await deleteUser(row.id)
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
      `确定${statusText}用户「${row.name}」吗？`,
      '确认操作',
      { type: 'warning' }
    )
    const res = await toggleUserStatus(row.id, statusNum)
    if (res.success) {
      ElMessage.success(`已${statusText}`)
      loadData()
    }
  } catch {
    row.enabled = !val
  }
}

async function handleResetPassword(row) {
  try {
    await ElMessageBox.confirm(
      `确定重置用户「${row.name}」的密码为 123456 吗？`,
      '重置密码',
      { type: 'warning' }
    )
    const res = await resetUserPassword(row.id)
    if (res.success) {
      ElMessage.success('密码已重置为 123456')
    }
  } catch {
    // cancel
  }
}

onMounted(() => {
  loadRoles()
  loadData()
})
</script>

<style scoped lang="scss">
.user-page {
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

.user-tabs {
  margin-bottom: 16px;
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

.role-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
}

.role-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.role-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.role-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.role-desc {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 12px;
  line-height: 1.5;
}

.role-count {
  font-size: 12px;
  color: #9ca3af;
  padding-top: 10px;
  border-top: 1px solid #f3f4f6;
}

.role-status {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
