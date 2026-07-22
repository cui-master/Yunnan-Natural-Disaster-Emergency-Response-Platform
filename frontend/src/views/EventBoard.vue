<template>
  <div>
    <div class="filters" style="margin-bottom:16px;display:flex;gap:12px;align-items:center">
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width:180px" @change="load">
        <el-option label="待核验" value="PENDING_VERIFY" />
        <el-option label="已确认" value="CONFIRMED" />
        <el-option label="处置中" value="IN_PROGRESS" />
        <el-option label="已结束" value="CLOSED" />
        <el-option label="已驳回" value="REJECTED" />
      </el-select>
      <el-button @click="load">刷新</el-button>
      <span style="color:#909399;font-size:13px">实时状态通过 WebSocket 推送</span>
    </div>

    <el-table v-if="auth.roleKey !== 'ROLE_REPORTER'" :data="incidents" stripe>
      <el-table-column prop="code" label="编号" width="180" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="type" label="类型" width="90" />
      <el-table-column prop="level" label="等级" width="80" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="createdAt" label="上报时间" width="180" />
      <el-table-column label="操作" width="340">
        <template #default="{ row }">
          <el-button v-if="row.status === 'PENDING_VERIFY' && isCommander" size="small" type="success" @click="confirm(row)">确认</el-button>
          <el-button v-if="row.status === 'PENDING_VERIFY' && isCommander" size="small" type="danger" @click="reject(row)">驳回</el-button>
          <el-button v-if="(row.status === 'PENDING_VERIFY' || row.status === 'CONFIRMED') && isCommander" size="small" type="primary" @click="genPlan(row)">生成方案</el-button>
          <el-button v-if="row.status === 'IN_PROGRESS'" size="small" @click="openDispatch(row)">资源调度</el-button>
          <el-button v-if="row.status === 'IN_PROGRESS' || row.status === 'CONFIRMED'" size="small" type="warning" @click="close(row)">归档</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="信息员无看板权限，请前往「灾情上报」" />

    <!-- 方案生成（SSE 进度 + 人工修订） -->
    <el-dialog v-model="planDlg" title="AI 生成处置方案" width="680px">
      <div v-if="planProgress.length">
        <el-steps direction="vertical" :active="planProgress.length">
          <el-step v-for="(p, i) in planProgress" :key="i" :title="p" :status="planDone ? 'finish' : 'process'" />
        </el-steps>
      </div>
      <div v-if="planParsed" style="margin-top:12px">
        <h4>{{ planParsed.title }}</h4>
        <div style="margin:8px 0">
          <b>处置步骤：</b>
          <ol><li v-for="(s, i) in planParsed.steps" :key="i">{{ s }}</li></ol>
        </div>
        <div style="margin:8px 0;color:#909399;font-size:13px">
          引用来源：{{ planParsed.citations.map((c: any) => c.source).join('；') }}
        </div>
        <el-input type="textarea" v-model="planEditable" :rows="8" placeholder="可在此人工修订方案内容" />
        <el-button type="success" :disabled="!planDone" style="margin-top:12px" @click="approvePlan">审批通过</el-button>
      </div>
    </el-dialog>

    <!-- 资源调度 -->
    <el-dialog v-model="dispatchDlg" title="资源调度（锁定 + 冲突检测）" width="680px">
      <el-table :data="dispatchItems">
        <el-table-column label="资源">
          <template #default="{ row }">
            <el-select v-model="row.resourceId" @change="syncName(row)" style="width:100%">
              <el-option v-for="r in resources" :key="r.id" :label="r.name + '（可用' + r.available + '）'" :value="r.id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="140">
          <template #default="{ row }"><el-input-number v-model="row.qty" :min="1" /></template>
        </el-table-column>
        <el-table-column label="" width="90">
          <template #default="{ row, $index }">
            <el-button size="small" type="danger" @click="dispatchItems.splice($index, 1)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:12px">
        <el-button @click="addDispatchItem">+ 添加资源项</el-button>
        <el-button type="primary" @click="submitDispatch">锁定并生成调度单</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuth } from '../stores/auth'
import { ElMessage } from 'element-plus'
import {
  listIncidents, confirmIncident, rejectIncident, closeIncident,
  approvePlan as apiApprove, createDispatch, listResources, getPlan
} from '../api'
import type { Incident, Resource, AiPlan, EmergencyPlan } from '../types'

const auth = useAuth()
const isCommander = computed(() => auth.roleKey === 'ROLE_COMMANDER')

const incidents = ref<Incident[]>([])
const statusFilter = ref('')
const resources = ref<Resource[]>([])

async function load() {
  try {
    incidents.value = await listIncidents(statusFilter.value || undefined)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '加载失败')
  }
}

async function confirm(row: Incident) { await confirmIncident(row.id); ElMessage.success('已确认'); load() }
async function reject(row: Incident) { await rejectIncident(row.id); ElMessage.success('已驳回'); load() }
async function close(row: Incident) { await closeIncident(row.id); ElMessage.success('已归档并释放资源'); load() }

// ---- 方案生成（SSE） ----
const planDlg = ref(false)
const planProgress = ref<string[]>([])
const planParsed = ref<AiPlan | null>(null)
const planEditable = ref('')
const planDone = ref(false)
let currentPlanId = 0

async function genPlan(row: Incident) {
  planProgress.value = []
  planParsed.value = null
  planEditable.value = ''
  planDone.value = false
  currentPlanId = 0
  planDlg.value = true
  const es = new EventSource(`/api/incidents/${row.id}/plan`)
  es.addEventListener('progress', (ev: MessageEvent) => { planProgress.value.push(ev.data) })
  es.addEventListener('done', async (ev: MessageEvent) => {
    currentPlanId = Number(ev.data)
    const plan: EmergencyPlan = await getPlan(currentPlanId)
    planParsed.value = JSON.parse(plan.content)
    planEditable.value = plan.content
    planDone.value = true
    es.close()
  })
  es.addEventListener('error', () => { ElMessage.error('方案生成异常'); es.close() })
}

async function approvePlan() {
  if (!currentPlanId) return
  await apiApprove(currentPlanId, planEditable.value)
  ElMessage.success('方案已审批')
  planDlg.value = false
  load()
}

// ---- 资源调度 ----
const dispatchDlg = ref(false)
const dispatchItems = ref<Array<{ resourceId: number; qty: number; name: string }>>([])
let dispatchIncidentId = 0

async function openDispatch(row: Incident) {
  dispatchIncidentId = row.id
  resources.value = await listResources()
  dispatchItems.value = []
  dispatchDlg.value = true
}
function addDispatchItem() {
  if (!resources.value.length) { ElMessage.warning('暂无可调度资源'); return }
  dispatchItems.value.push({ resourceId: resources.value[0].id, qty: 1, name: resources.value[0].name })
}
function syncName(row: any) {
  const r = resources.value.find((x) => x.id === row.resourceId)
  row.name = r ? r.name : ''
}
async function submitDispatch() {
  const items = dispatchItems.value.map((i) => ({ resourceId: i.resourceId, quantity: i.qty }))
  try {
    await createDispatch({ incidentId: dispatchIncidentId, items })
    ElMessage.success('调度单已生成')
    dispatchDlg.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '调度冲突，请检查资源可用量')
  }
}

function onIncidentUpdate() { load() }
onMounted(() => { load(); window.addEventListener('incident-update', onIncidentUpdate) })
onUnmounted(() => window.removeEventListener('incident-update', onIncidentUpdate))
</script>
