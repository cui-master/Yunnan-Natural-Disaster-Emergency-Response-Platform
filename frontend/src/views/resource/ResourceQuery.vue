<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useResourceStore } from '@/stores/resource'
import { useDisasterStore } from '@/stores/disaster'
import { ElMessage } from 'element-plus'
import type { RescueResource, ResourceType, ResourceStatus, DispatchRecord } from '@/types'

const resource = useResourceStore()
const disaster = useDisasterStore()
const { resources, loading } = storeToRefs(resource)

const filters = reactive({ type: '' as ResourceType | '', status: '' as ResourceStatus | '', city: '', keyword: '' })
const selected = ref<RescueResource[]>([])
const dispatchDialog = ref(false)
const dispatchForm = reactive({ eventId: null as number | null, toCity: '', toLocation: '', note: '' })
const dispatchResult = ref<{ records: DispatchRecord[]; conflict: boolean } | null>(null)

const typeLabel: Record<string, string> = {
  TEAM: '救援队伍', VEHICLE: '车辆', EQUIPMENT: '装备', MATERIAL: '物资', MEDICAL: '医疗', SHELTER: '安置点'
}
const statusMeta: Record<string, { label: string; type: string; led: string }> = {
  IDLE: { label: '空闲', type: 'success', led: 'green' },
  DISPATCHED: { label: '已调度', type: 'primary', led: 'blue' },
  LOCKED: { label: '锁定中', type: 'warning', led: 'amber' },
  MAINTENANCE: { label: '维护', type: 'info', led: 'red' }
}

// 调度台顶部状态计数（Andon 信号灯汇总）
const statusCount = computed(() => {
  const c: Record<string, number> = { IDLE: 0, DISPATCHED: 0, LOCKED: 0, MAINTENANCE: 0 }
  resources.value.forEach((r) => {
    if (c[r.status] !== undefined) c[r.status]++
  })
  return c
})
const events = ref<any[]>([])

function load() {
  resource.fetchResources({
    type: filters.type || undefined,
    status: filters.status || undefined,
    city: filters.city || undefined,
    keyword: filters.keyword || undefined
  })
}

function openDispatch() {
  if (!selected.value.length) {
    ElMessage.warning('请先勾选要调度的资源')
    return
  }
  dispatchResult.value = null
  dispatchForm.eventId = null
  dispatchForm.toCity = ''
  dispatchForm.toLocation = ''
  dispatchForm.note = ''
  dispatchDialog.value = true
}

async function confirmDispatch() {
  if (!dispatchForm.eventId) {
    ElMessage.warning('请选择目标灾情工单')
    return
  }
  const resp = await resource.dispatch({
    eventId: dispatchForm.eventId,
    resourceIds: selected.value.map((r) => r.id),
    toCity: dispatchForm.toCity,
    toLocation: dispatchForm.toLocation,
    note: dispatchForm.note
  })
  dispatchResult.value = resp
  if (resp.conflict) {
    ElMessage.warning('部分资源存在调度冲突，请查看下方提示')
  } else {
    ElMessage.success('调度成功')
  }
  load()
}

onMounted(() => {
  load()
  disaster.fetchList({ pageSize: 100 }).then(() => (events.value = disaster.list))
})
</script>

<template>
  <div class="resource">
    <!-- Andon 信号灯汇总条：工业调度台风格 -->
    <div class="andon-bar">
      <div class="andon-item" v-for="(m, k) in statusMeta" :key="k">
        <span class="led" :class="m.led"></span>
        <span class="andon-label">{{ m.label }}</span>
        <span class="andon-num">{{ statusCount[k] }}</span>
      </div>
      <div class="andon-total">
        资源总数 <b>{{ resources.length }}</b>
      </div>
    </div>
    <el-card class="page-card">
      <template #header><b>救援资源查询</b></template>
      <div class="filter">
        <el-select v-model="filters.type" placeholder="资源类型" clearable style="width: 140px" @change="load">
          <el-option v-for="(l, k) in typeLabel" :key="k" :label="l" :value="k" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="load">
          <el-option v-for="(m, k) in statusMeta" :key="k" :label="m.label" :value="k" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="名称/单位" style="width: 180px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="warning" :disabled="!selected.length" @click="openDispatch">调度选中（{{ selected.length }}）</el-button>
      </div>
      <el-table :data="resources" v-loading="loading" border stripe @selection-change="(rows: any) => (selected = rows)">
        <el-table-column type="selection" width="46" />
        <el-table-column prop="name" label="资源名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">{{ typeLabel[row.type] }}</template>
        </el-table-column>
        <el-table-column label="状态" width="104">
          <template #default="{ row }">
            <span class="status-cell">
              <span class="led" :class="statusMeta[row.status]?.led"></span>
              {{ statusMeta[row.status]?.label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="city" label="所在州市" width="90" />
        <el-table-column prop="owner" label="所属单位" min-width="140" show-overflow-tooltip />
        <el-table-column prop="capacity" label="规模/容量" width="100" />
        <el-table-column prop="contact" label="联系方式" width="130" />
        <el-table-column prop="lockedBy" label="锁定人" width="90" />
      </el-table>
    </el-card>

    <el-dialog v-model="dispatchDialog" title="资源调度" width="520px">
      <el-form label-width="90px">
        <el-form-item label="目标工单">
          <el-select v-model="dispatchForm.eventId" style="width: 100%" placeholder="选择灾情工单">
            <el-option v-for="e in events" :key="e.id" :label="`${e.code} ${e.title}`" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="调往州市">
          <el-input v-model="dispatchForm.toCity" placeholder="如：大理州" />
        </el-form-item>
        <el-form-item label="调往地点">
          <el-input v-model="dispatchForm.toLocation" placeholder="如：漾濞县苍山西镇" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="dispatchForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <div v-if="dispatchResult" class="result">
        <el-alert v-if="dispatchResult.conflict" type="warning" :closable="false" title="检测到调度冲突" />
        <el-alert v-else type="success" :closable="false" title="调度成功，无冲突" />
        <div v-for="r in dispatchResult.records" :key="r.id" class="rec" :class="{ conflict: r.conflict }">
          {{ r.resourceName }} → {{ r.toCity }}{{ r.toLocation }}
          <span v-if="r.conflict" class="reason">⚠ {{ r.conflictReason }}</span>
        </div>
      </div>
      <template #footer>
        <el-button v-if="!dispatchResult" type="primary" @click="confirmDispatch">确认调度</el-button>
        <el-button v-else @click="dispatchDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.resource {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
/* Andon 信号灯汇总条：钢灰底 + 琥珀描边 + 等宽数字 */
.andon-bar {
  display: flex;
  align-items: center;
  gap: 26px;
  padding: 12px 18px;
  border-radius: var(--ydr-radius-control, 8px);
  background: var(--ydr-surface, #181b21);
  border: 1px solid var(--ydr-border);
}
.andon-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ydr-sub);
}
.andon-num {
  font-family: var(--ydr-mono, 'Consolas', monospace);
  font-size: 17px;
  font-weight: 700;
  color: var(--ydr-ink);
  font-variant-numeric: tabular-nums;
}
.andon-total {
  margin-left: auto;
  font-size: 13px;
  color: var(--ydr-sub);
}
.andon-total b {
  font-family: var(--ydr-mono, 'Consolas', monospace);
  font-size: 17px;
  color: #e8a317;
  margin-left: 6px;
}
.status-cell {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
}
.filter {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.result {
  margin-top: 12px;
}
.rec {
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px dashed #f0f0f0;
}
.rec.conflict {
  color: #e6a23c;
}
.reason {
  font-size: 12px;
  color: #e6a23c;
}
</style>
