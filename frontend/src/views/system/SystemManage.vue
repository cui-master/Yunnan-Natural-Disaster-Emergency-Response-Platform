<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemUsers, createSystemUser, getRoles, getSystemConfig } from '@/api/system'
import type { RoleCode } from '@/types'

const activeTab = ref('user')
const users = ref<any[]>([])
const roles = ref<any[]>([])
const configs = ref<any[]>([])
const dialog = ref(false)
const form = reactive({ username: '', realName: '', password: '123456', roles: [] as RoleCode[] })

const roleLabel: Record<string, string> = {
  REPORTER: '信息员', COMMANDER: '指挥人员', RESOURCE_ADMIN: '资源管理员', SYS_ADMIN: '系统管理员'
}

function loadUsers() {
  getSystemUsers().then((r: any) => (users.value = r.list))
}
function loadRoles() {
  getRoles().then((r: any) => (roles.value = r))
}
function loadConfig() {
  getSystemConfig().then((r: any) => (configs.value = r))
}

function openAdd() {
  form.username = ''
  form.realName = ''
  form.password = '123456'
  form.roles = []
  dialog.value = true
}
function submitUser() {
  if (!form.username || !form.roles.length) {
    ElMessage.warning('请填写用户名并分配角色')
    return
  }
  createSystemUser({ ...form }).then(() => {
    ElMessage.success('用户已创建')
    dialog.value = false
    loadUsers()
  })
}

onMounted(() => {
  loadUsers()
  loadRoles()
  loadConfig()
})
</script>

<template>
  <div class="sys">
    <el-card class="page-card">
<<<<<<< HEAD
      <template #header>
        <div class="section-title">系统管理</div>
        <div class="head-sub">用户、角色权限（RBAC）与系统配置的统一维护</div>
      </template>
=======
>>>>>>> feature-cui
      <el-tabs v-model="activeTab">
        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="user">
          <div class="bar">
            <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 新建用户</el-button>
          </div>
          <el-table :data="users" border stripe>
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="realName" label="姓名" width="120" />
            <el-table-column label="角色" min-width="200">
              <template #default="{ row }">
                <el-tag v-for="r in row.roles" :key="r" size="small" style="margin-right: 4px">{{ roleLabel[r] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }"><el-tag :type="row.status === 'ENABLED' ? 'success' : 'info'" size="small">{{ row.status === 'ENABLED' ? '启用' : '停用' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="lastLoginAt" label="最近登录" width="180" />
          </el-table>
        </el-tab-pane>

        <!-- 角色权限 RBAC -->
        <el-tab-pane label="角色权限" name="role">
          <el-table :data="roles" border stripe>
            <el-table-column prop="name" label="角色" width="140" />
            <el-table-column prop="description" label="职责" width="240" />
            <el-table-column label="权限点" min-width="300">
              <template #default="{ row }">
                <el-tag v-for="p in row.permissions" :key="p" size="small" type="info" style="margin: 2px">{{ p }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 系统配置 -->
        <el-tab-pane label="系统配置" name="config">
          <el-table :data="configs" border stripe>
            <el-table-column prop="group" label="分组" width="120" />
            <el-table-column prop="key" label="配置项" width="200" />
            <el-table-column prop="value" label="值" width="160" />
            <el-table-column prop="remark" label="说明" min-width="240" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialog" title="新建用户" width="460px">
      <el-form label-width="80px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.realName" /></el-form-item>
        <el-form-item label="初始密码"><el-input v-model="form.password" /></el-form-item>
        <el-form-item label="分配角色">
          <el-select v-model="form.roles" multiple style="width: 100%">
            <el-option v-for="(l, k) in roleLabel" :key="k" :label="l" :value="k" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="submitUser">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.bar {
  margin-bottom: 12px;
}
</style>
