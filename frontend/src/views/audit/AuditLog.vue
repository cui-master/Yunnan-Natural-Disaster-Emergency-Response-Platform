<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAuditLogs } from '@/api/system'
import type { AuditLog } from '@/types'

const list = ref<AuditLog[]>([])
const total = ref(0)
const loading = ref(false)
const keyword = ref('')
const roleLabel: Record<string, string> = {
  REPORTER: '信息员', COMMANDER: '指挥人员', RESOURCE_ADMIN: '资源管理员', SYS_ADMIN: '系统管理员'
}

function load() {
  loading.value = true
  getAuditLogs({ keyword: keyword.value || undefined, page: 1, pageSize: 50 })
    .then((resp: any) => {
      list.value = resp.list
      total.value = resp.total
    })
    .finally(() => (loading.value = false))
}

onMounted(load)
</script>

<template>
  <div class="audit">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
<<<<<<< HEAD
          <div>
            <div class="section-title">审计日志</div>
            <div class="head-sub">记录关键操作与登录行为，支持按操作人 / 动作检索</div>
          </div>
=======
          <b>审计日志</b>
>>>>>>> feature-cui
          <div>
            <el-input v-model="keyword" placeholder="操作人/动作" style="width: 180px; margin-right: 10px" @keyup.enter="load" />
            <el-button type="primary" @click="load">查询</el-button>
          </div>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column label="角色" width="110">
          <template #default="{ row }">{{ roleLabel[row.role] }}</template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="action" label="动作" width="140" />
        <el-table-column prop="target" label="对象" min-width="160" show-overflow-tooltip />
        <el-table-column label="结果" width="90">
          <template #default="{ row }">
            <el-tag :type="row.result === 'SUCCESS' ? 'success' : 'danger'" size="small">{{ row.result === 'SUCCESS' ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="120" />
        <el-table-column prop="createdAt" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>
