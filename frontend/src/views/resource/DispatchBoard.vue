<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useResourceStore } from '@/stores/resource'
import { ElMessage } from 'element-plus'
import type { DispatchRecord } from '@/types'

const resource = useResourceStore()
const { dispatches, loading } = storeToRefs(resource)

const statusMeta: Record<string, { label: string; type: string }> = {
  PENDING: { label: '待发', type: 'info' },
  EXECUTING: { label: '执行中', type: 'primary' },
  ARRIVED: { label: '已到达', type: 'success' },
  RETURNED: { label: '已返回', type: 'warning' },
  CANCELLED: { label: '已取消', type: 'danger' }
}

const stats = computed(() => {
  const s = { executing: 0, arrived: 0, conflict: 0, total: dispatches.value.length }
  dispatches.value.forEach((d) => {
    if (d.status === 'EXECUTING') s.executing++
    if (d.status === 'ARRIVED') s.arrived++
    if (d.conflict) s.conflict++
  })
  return s
})

function load() {
  resource.fetchDispatches()
}

async function cancel(row: DispatchRecord) {
  await resource.cancel(row.id)
  ElMessage.success('已取消调度，资源释放')
  load()
}

onMounted(load)
</script>

<template>
  <div class="dispatch">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
          <b>调度看板</b>
          <div class="kpi">
            <span>执行中 <b>{{ stats.executing }}</b></span>
            <span>已到达 <b>{{ stats.arrived }}</b></span>
            <span :class="{ warn: stats.conflict }">冲突 <b>{{ stats.conflict }}</b></span>
          </div>
        </div>
      </template>
      <el-table :data="dispatches" v-loading="loading" border stripe>
        <el-table-column prop="eventCode" label="工单" width="170" />
        <el-table-column prop="resourceName" label="资源" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ row.resourceType }}</template>
        </el-table-column>
        <el-table-column label="路线" min-width="160">
          <template #default="{ row }">{{ row.fromCity }} → {{ row.toCity }}{{ row.toLocation }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><el-tag :type="(statusMeta[row.status]?.type as any)" size="small">{{ statusMeta[row.status]?.label }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="dispatchedBy" label="调度人" width="90" />
        <el-table-column prop="eta" label="预计" width="70" />
        <el-table-column label="冲突" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.conflict" type="danger" size="small">冲突</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'CANCELLED'" link type="danger" @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-alert
        v-if="stats.conflict"
        type="warning"
        :closable="false"
        style="margin-top: 12px"
        title="存在调度冲突"
        description="冲突资源已被其他任务锁定/占用，请协调资源管理员释放或改派。"
      />
    </el-card>
  </div>
</template>

<style scoped>
.kpi {
  display: flex;
  gap: 18px;
  font-size: 13px;
  color: #606266;
}
.kpi b {
  color: #c0392b;
  font-size: 16px;
}
.kpi .warn b {
  color: #e6a23c;
}
</style>
