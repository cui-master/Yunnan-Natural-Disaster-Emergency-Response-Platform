<template>
  <div class="backend-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#e64545"><Cpu /></el-icon>
        <span class="header-title">后端功能</span>
        <span class="header-sub">灾情工单状态机 · 资源锁定 · 实时推送 · 定时采集 · AI 服务 · RBAC审计</span>
      </div>
      <div class="header-right">
        <el-tag :type="wsConnected ? 'success' : 'info'" effect="dark" size="small" round>
          <span class="dot" :class="{ on: wsConnected }"></span>
          {{ wsConnected ? 'WS 已连接' : 'WS 未连接' }}
        </el-tag>
        <span class="time-tag">
          <el-icon><Clock /></el-icon>
          {{ currentTime }}
        </span>
      </div>
    </div>

    <div class="page-body">
      <el-tabs v-model="activeTab" class="func-tabs">
        <!-- ============ 1. 灾情工单状态机 ============ -->
        <el-tab-pane name="state">
          <template #label>
            <el-icon><Histogram /></el-icon> 灾情工单状态机
          </template>
          <div class="tab-desc">
            灾情工单四态流转：<b>待核验</b> → <b>已确认</b> → <b>处置中</b> → <b>已结束</b>，非法跳转会被状态机拦截。
          </div>
          <el-table :data="incidents" border stripe size="small" v-loading="loading.incident">
            <el-table-column prop="incidentNo" label="事件编号" width="160" />
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="disasterType" label="类型" width="80" />
            <el-table-column prop="riskLevel" label="等级" width="70">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.riskLevel)" size="small">{{ row.riskLevel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="当前状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small" effect="dark">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="可流转状态" width="200">
              <template #default="{ row }">
                <el-tag
                  v-for="s in row.allowedNext"
                  :key="s"
                  size="small"
                  type="warning"
                  effect="plain"
                  style="margin: 2px; cursor: pointer"
                  @click="doTransition(row, s)"
                >→ {{ s }}</el-tag>
                <span v-if="!row.allowedNext || !row.allowedNext.length" class="muted">终态</span>
              </template>
            </el-table-column>
            <el-table-column prop="occurredAt" label="发生时间" width="160" />
          </el-table>
          <div class="state-flow">
            <span class="flow-note">状态机流转图：</span>
            <span class="flow-node pending">待核验</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="flow-node confirmed">已确认</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="flow-node processing">处置中</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="flow-node completed">已结束</span>
          </div>
        </el-tab-pane>

        <!-- ============ 2. 资源锁定/调度/释放 ============ -->
        <el-tab-pane name="lock">
          <template #label>
            <el-icon><Lock /></el-icon> 资源锁定
          </template>
          <div class="tab-desc">
            资源锁定（预占可用量）、释放（回补可用量）、冲突检测（校验余量）、过期自动清理。
          </div>
          <div class="lock-actions">
            <el-button type="primary" size="small" :icon="Refresh" @click="loadLocks">刷新锁记录</el-button>
            <el-button size="small" :icon="Delete" @click="handleCleanup">清理过期锁</el-button>
          </div>
          <el-table :data="locks" border stripe size="small" v-loading="loading.lock">
            <el-table-column prop="lockNo" label="锁编号" width="160" />
            <el-table-column prop="resourceName" label="资源名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="lockedQty" label="锁定数量" width="90" />
            <el-table-column prop="lockedByName" label="锁定人" width="90" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'locked' ? 'warning' : 'info'" size="small">{{ row.status === 'locked' ? '锁定中' : row.status === 'released' ? '已释放' : '已过期' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expiresAt" label="过期时间" width="160" />
            <el-table-column prop="lockedAt" label="锁定时间" width="160" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'locked'" type="danger" size="small" link @click="handleRelease(row)">释放</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ 3. 实时推送 SSE/WebSocket ============ -->
        <el-tab-pane name="push">
          <template #label>
            <el-icon><Bell /></el-icon> 实时推送
          </template>
          <div class="tab-desc">
            <b>WebSocket</b> 推送事件状态（灾情流转、资源锁定）；<b>SSE</b> 推送 AI 生成进度。
          </div>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="push-card">
                <div class="push-title">
                  <el-icon color="#40a9ff"><Connection /></el-icon> WebSocket 事件状态
                  <el-button size="small" :type="wsConnected ? 'danger' : 'primary'" @click="toggleWs">
                    {{ wsConnected ? '断开' : '连接' }}
                  </el-button>
                </div>
                <div class="push-msgs">
                  <div v-for="(msg, i) in wsMessages" :key="i" class="msg-item" :class="msg.type">
                    <span class="msg-type">[{{ msg.type }}]</span>
                    <span class="msg-time">{{ msg.time }}</span>
                    <pre class="msg-body">{{ msg.text }}</pre>
                  </div>
                  <el-empty v-if="!wsMessages.length" description="暂无消息，连接后等待事件推送" :image-size="60" />
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="push-card">
                <div class="push-title">
                  <el-icon color="#52c41a"><DataLine /></el-icon> SSE AI 生成进度
                  <el-button size="small" type="primary" :loading="sseLoading" @click="testSse">模拟进度推送</el-button>
                </div>
                <div class="sse-progress">
                  <el-progress :percentage="sseProgress" :status="sseStatus" />
                  <div class="sse-stage">{{ sseStage }}</div>
                </div>
                <div class="sse-logs">
                  <div v-for="(log, i) in sseLogs" :key="i" class="sse-log">{{ log }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ============ 4. 定时采集 ============ -->
        <el-tab-pane name="schedule">
          <template #label>
            <el-icon><Timer /></el-icon> 定时采集
          </template>
          <div class="tab-desc">
            定时采集公开预警与气象数据，清理过期资源锁，归档历史灾情。
          </div>
          <div class="task-cards">
            <div v-for="t in schedulerTasks" :key="t.name" class="task-card">
              <div class="task-name">{{ t.name }}</div>
              <div class="task-schedule">{{ t.schedule }}</div>
              <div class="task-desc">{{ t.description }}</div>
            </div>
          </div>
          <div class="schedule-actions">
            <el-button type="primary" :icon="Cloudy" :loading="triggering.weather" @click="handleTriggerWeather">触发气象采集</el-button>
            <el-button type="warning" :icon="Warning" :loading="triggering.warning" @click="handleTriggerWarning">触发预警采集</el-button>
          </div>
        </el-tab-pane>

        <!-- ============ 5. AI 服务 ============ -->
        <el-tab-pane name="ai">
          <template #label>
            <el-icon><MagicStick /></el-icon> AI 服务
          </template>
          <div class="tab-desc">
            调用 AI 服务完成<b>事件抽取</b>、<b>预案检索</b>、<b>方案审查</b>，支持 SSE 进度推送与异常重试。
          </div>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="ai-card">
                <div class="ai-title"><el-icon color="#722ed1"><DocumentCopy /></el-icon> 事件抽取</div>
                <el-input v-model="aiForm.extractText" type="textarea" :rows="4" placeholder="输入灾情文本，AI 自动抽取结构化信息" />
                <el-button type="primary" size="small" :loading="aiLoading.extract" @click="runExtract" style="margin-top: 8px">抽取</el-button>
                <pre v-if="aiResult.extract" class="ai-result">{{ aiResult.extract }}</pre>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="ai-card">
                <div class="ai-title"><el-icon color="#13c2c2"><Search /></el-icon> 预案检索</div>
                <el-input v-model="aiForm.query" type="textarea" :rows="4" placeholder="输入查询条件，从知识库检索预案" />
                <el-button type="primary" size="small" :loading="aiLoading.retrieve" @click="runRetrieve" style="margin-top: 8px">检索</el-button>
                <pre v-if="aiResult.retrieve" class="ai-result">{{ aiResult.retrieve }}</pre>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="ai-card">
                <div class="ai-title"><el-icon color="#fa8c16"><Checked /></el-icon> 方案审查</div>
                <el-input v-model="aiForm.planContent" type="textarea" :rows="4" placeholder="输入方案内容，AI 进行合规审查" />
                <el-button type="primary" size="small" :loading="aiLoading.review" @click="runReview" style="margin-top: 8px">审查</el-button>
                <pre v-if="aiResult.review" class="ai-result">{{ aiResult.review }}</pre>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ============ 6. RBAC 审计 ============ -->
        <el-tab-pane name="audit">
          <template #label>
            <el-icon><Document /></el-icon> RBAC 审计
          </template>
          <div class="tab-desc">
            RBAC 权限控制（@PreAuthorize）+ 操作审计（@AuditLog 切面自动记录）+ 异常重试（Spring Retry）。
          </div>
          <el-row :gutter="16" class="rbac-row">
            <el-col :span="8">
              <div class="rbac-card">
                <div class="rbac-title">RBAC 权限矩阵</div>
                <el-table :data="rbacMatrix" size="small" border>
                  <el-table-column prop="module" label="功能模块" width="120" />
                  <el-table-column prop="reporter" label="信息员" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.reporter ? 'success' : 'info'">{{ row.reporter ? '✓' : '✗' }}</el-tag></template>
                  </el-table-column>
                  <el-table-column prop="commander" label="指挥员" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.commander ? 'success' : 'info'">{{ row.commander ? '✓' : '✗' }}</el-tag></template>
                  </el-table-column>
                  <el-table-column prop="resmanager" label="资源员" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.resmanager ? 'success' : 'info'">{{ row.resmanager ? '✓' : '✗' }}</el-tag></template>
                  </el-table-column>
                  <el-table-column prop="admin" label="管理员" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.admin ? 'success' : 'info'">{{ row.admin ? '✓' : '✗' }}</el-tag></template>
                  </el-table-column>
                </el-table>
              </div>
            </el-col>
            <el-col :span="16">
              <div class="rbac-card">
                <div class="rbac-title">操作审计日志</div>
                <el-table :data="auditLogs" size="small" border stripe height="320">
                  <el-table-column prop="username" label="用户" width="90" />
                  <el-table-column prop="module" label="模块" width="80" />
                  <el-table-column prop="action" label="操作" width="110" />
                  <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
                  <el-table-column prop="result" label="结果" width="70">
                    <template #default="{ row }"><el-tag size="small" :type="row.result === 'success' ? 'success' : 'danger'">{{ row.result }}</el-tag></template>
                  </el-table-column>
                  <el-table-column prop="createdAt" label="时间" width="150" />
                </el-table>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  getDisasterList, getIncidentTransitions, transitionIncident,
  getResourceLocks, releaseResourceLock, cleanupExpiredLocks,
  getSchedulerTasks, triggerWeatherCollection, triggerWarningCollection,
  extractIncidentSync, retrievePlansSync, reviewPlanSync,
  getAuditLogs, connectEventSocket, subscribeAiProgress
} from '@/api'
import {
  Cpu, Clock, Histogram, Lock, Bell, Connection, DataLine, Timer,
  Cloudy, Warning, MagicStick, DocumentCopy, Search, Checked, Document,
  Refresh, Delete, ArrowRight
} from '@element-plus/icons-vue'

const activeTab = ref('state')
const currentTime = ref('')
let timer = null

const loading = reactive({ incident: false, lock: false })
const triggering = reactive({ weather: false, warning: false })
const aiLoading = reactive({ extract: false, retrieve: false, review: false })

// ===== 灾情工单状态机 =====
const incidents = ref([])
async function loadIncidents() {
  loading.incident = true
  try {
    const res = await getDisasterList({ pageSize: 20 })
    const list = (res.data?.list || res.data?.records || [])
    // 获取每条的可流转状态
    for (const inc of list) {
      inc.allowedNext = []
      try {
        const t = await getIncidentTransitions(inc.id)
        inc.allowedNext = t.data?.allowedNext || []
        inc.status = t.data?.currentStatus || inc.status
      } catch { /* mock 模式忽略 */ }
    }
    incidents.value = list
  } catch (e) {
    ElMessage.error('加载灾情列表失败')
  } finally {
    loading.incident = false
  }
}

async function doTransition(row, target) {
  try {
    await ElMessageBox.prompt(`确认将灾情 [${row.title}] 流转为「${target}」？`, '状态流转', {
      confirmButtonText: '确认流转',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入流转原因（可选）'
    }).then(({ value }) => {
      return transitionIncident(row.id, target, value || '')
    })
    ElMessage.success(`状态已流转为：${target}`)
    loadIncidents()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e?.message || '流转失败')
    }
  }
}

function statusTag(s) {
  return { '待核验': 'warning', '已确认': 'primary', '处置中': 'danger', '已结束': 'success' }[s] || 'info'
}
function levelTag(l) {
  return { '低': 'success', '中': 'warning', '高': 'danger', '极高': 'danger', '特别重大': 'danger' }[l] || 'info'
}

// ===== 资源锁定 =====
const locks = ref([])
async function loadLocks() {
  loading.lock = true
  try {
    const res = await getResourceLocks()
    locks.value = res.data || []
  } catch (e) {
    ElMessage.error('加载锁记录失败')
  } finally {
    loading.lock = false
  }
}

async function handleRelease(row) {
  try {
    await ElMessageBox.confirm(`确认释放锁 [${row.lockNo}]？可用量将回补。`, '释放资源锁', { type: 'warning' })
    await releaseResourceLock(row.id)
    ElMessage.success('已释放')
    loadLocks()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('释放失败')
  }
}

async function handleCleanup() {
  try {
    const res = await cleanupExpiredLocks()
    ElMessage.success(`已清理 ${res.data?.cleaned || 0} 个过期锁`)
    loadLocks()
  } catch (e) {
    ElMessage.error('清理失败')
  }
}

// ===== 实时推送 =====
const wsConnected = ref(false)
const wsMessages = ref([])
let ws = null

function toggleWs() {
  if (wsConnected.value) {
    ws && ws.close()
    wsConnected.value = false
    return
  }
  ws = connectEventSocket((msg) => {
    wsMessages.value.unshift({
      type: msg.type || 'event',
      time: dayjs(msg.timestamp || Date.now()).format('HH:mm:ss'),
      text: JSON.stringify(msg.data || msg, null, 2)
    })
    if (wsMessages.value.length > 30) wsMessages.value.pop()
  }, () => {
    wsConnected.value = true
    ElMessage.success('WebSocket 已连接')
  })
  ws.onerror = () => { wsConnected.value = false }
  ws.onclose = () => { wsConnected.value = false }
}

// SSE 模拟测试
const sseLoading = ref(false)
const sseProgress = ref(0)
const sseStage = ref('')
const sseStatus = ref('')
const sseLogs = ref([])

async function testSse() {
  sseLoading.value = true
  sseProgress.value = 0
  sseStatus.value = ''
  sseLogs.value = []
  // 模拟 SSE 进度（实际场景由 AI 任务触发）
  const stages = [
    { stage: 'started', progress: 10, msg: '任务已启动' },
    { stage: 'calling', progress: 30, msg: '正在调用AI服务...' },
    { stage: 'retrying', progress: 50, msg: '重试中（第2次）' },
    { stage: 'completed', progress: 100, msg: '任务完成' }
  ]
  for (const s of stages) {
    sseProgress.value = s.progress
    sseStage.value = s.msg
    sseLogs.value.unshift(`[${dayjs().format('HH:mm:ss')}] ${s.stage} ${s.progress}% - ${s.msg}`)
    await new Promise(r => setTimeout(r, 800))
  }
  sseStatus.value = 'success'
  sseLoading.value = false
}

// ===== 定时采集 =====
const schedulerTasks = ref([
  { name: '气象数据采集', schedule: '每30分钟', description: '采集云南主要城市天气' },
  { name: '预警信息采集', schedule: '每15分钟', description: '采集公开预警信息' },
  { name: '清理过期资源锁', schedule: '每5分钟', description: '释放超时未确认的资源锁' },
  { name: '归档历史灾情', schedule: '每天02:00', description: '归档已结束超30天的灾情' }
])

async function loadSchedulerTasks() {
  try {
    const res = await getSchedulerTasks()
    if (res.data?.tasks) schedulerTasks.value = res.data.tasks
  } catch { /* 使用默认 */ }
}

async function handleTriggerWeather() {
  triggering.weather = true
  try {
    await triggerWeatherCollection()
    ElMessage.success('气象采集已触发')
  } catch (e) {
    ElMessage.error('触发失败')
  } finally {
    triggering.weather = false
  }
}

async function handleTriggerWarning() {
  triggering.warning = true
  try {
    await triggerWarningCollection()
    ElMessage.success('预警采集已触发')
  } catch (e) {
    ElMessage.error('触发失败')
  } finally {
    triggering.warning = false
  }
}

// ===== AI 服务 =====
const aiForm = reactive({ extractText: '', query: '', planContent: '' })
const aiResult = reactive({ extract: '', retrieve: '', review: '' })

async function runExtract() {
  if (!aiForm.extractText.trim()) return ElMessage.warning('请输入文本')
  aiLoading.extract = true
  aiResult.extract = ''
  try {
    const res = await extractIncidentSync(aiForm.extractText)
    aiResult.extract = JSON.stringify(res.data || res, null, 2)
  } catch (e) {
    aiResult.extract = '抽取失败：' + (e.message || 'AI服务不可用')
  } finally {
    aiLoading.extract = false
  }
}

async function runRetrieve() {
  if (!aiForm.query.trim()) return ElMessage.warning('请输入查询条件')
  aiLoading.retrieve = true
  aiResult.retrieve = ''
  try {
    const res = await retrievePlansSync(aiForm.query, 5)
    aiResult.retrieve = JSON.stringify(res.data || res, null, 2)
  } catch (e) {
    aiResult.retrieve = '检索失败：' + (e.message || 'AI服务不可用')
  } finally {
    aiLoading.retrieve = false
  }
}

async function runReview() {
  if (!aiForm.planContent.trim()) return ElMessage.warning('请输入方案内容')
  aiLoading.review = true
  aiResult.review = ''
  try {
    const res = await reviewPlanSync(aiForm.planContent, null)
    aiResult.review = JSON.stringify(res.data || res, null, 2)
  } catch (e) {
    aiResult.review = '审查失败：' + (e.message || 'AI服务不可用')
  } finally {
    aiLoading.review = false
  }
}

// ===== RBAC 审计 =====
const rbacMatrix = ref([
  { module: '灾情上报', reporter: true, commander: true, resmanager: false, admin: false },
  { module: '事件审核', reporter: false, commander: true, resmanager: false, admin: false },
  { module: '状态流转', reporter: true, commander: true, resmanager: false, admin: false },
  { module: '资源锁定', reporter: false, commander: true, resmanager: true, admin: false },
  { module: '调度指令', reporter: false, commander: true, resmanager: true, admin: false },
  { module: '预案检索', reporter: false, commander: true, resmanager: false, admin: true },
  { module: '方案审查', reporter: false, commander: true, resmanager: false, admin: true },
  { module: '定时任务', reporter: false, commander: false, resmanager: true, admin: true }
])
const auditLogs = ref([])
async function loadAuditLogs() {
  try {
    const res = await getAuditLogs({ pageSize: 20 })
    auditLogs.value = res.data?.list || res.data?.records || []
  } catch { /* mock 忽略 */ }
}

function updateTime() {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  loadIncidents()
  loadLocks()
  loadSchedulerTasks()
  loadAuditLogs()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (ws) ws.close()
})
</script>

<style scoped lang="scss">
.backend-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
  background: #f5f7fa;
}

.page-header {
  background: #fff;
  border-radius: 8px;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;

  .header-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }

  .header-sub {
    font-size: 12px;
    color: #9ca3af;
    margin-left: 8px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;

  .dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #909399;
    margin-right: 4px;

    &.on {
      background: #67c23a;
      animation: pulse 1.5s infinite;
    }
  }

  .time-tag {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: #f3f4f6;
    border-radius: 20px;
    font-size: 13px;
    color: #6b7280;
    font-family: 'Courier New', monospace;
  }
}

.page-body {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: 600px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.func-tabs {
  :deep(.el-tabs__item) {
    font-size: 14px;
    font-weight: 500;
  }
}

.tab-desc {
  background: #f0f7ff;
  border-left: 3px solid #40a9ff;
  padding: 10px 14px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #555;
  line-height: 1.6;

  b {
    color: #1890ff;
  }
}

.muted {
  color: #9ca3af;
  font-size: 12px;
}

.state-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #fffbe6 0%, #fff1f0 50%, #f6ffed 100%);
  border-radius: 8px;
  font-size: 13px;

  .flow-note {
    color: #6b7280;
    margin-right: 8px;
  }

  .flow-node {
    padding: 4px 12px;
    border-radius: 14px;
    font-weight: 600;

    &.pending { background: #fffbe6; color: #d48806; border: 1px solid #ffe58f; }
    &.confirmed { background: #e6f7ff; color: #096dd9; border: 1px solid #91d5ff; }
    &.processing { background: #fff1f0; color: #cf1322; border: 1px solid #ffa39e; }
    &.completed { background: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }
  }
}

.lock-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.push-card {
  background: #fafbfc;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;

  .push-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    margin-bottom: 12px;
    font-size: 14px;

    .el-button {
      margin-left: auto;
    }
  }
}

.push-msgs {
  max-height: 320px;
  overflow-y: auto;

  .msg-item {
    background: #fff;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 8px;
    border-left: 3px solid #1890ff;
    font-size: 12px;

    .msg-type {
      color: #1890ff;
      font-weight: 600;
      margin-right: 8px;
    }

    .msg-time {
      color: #9ca3af;
      float: right;
    }

    .msg-body {
      margin: 4px 0 0;
      white-space: pre-wrap;
      word-break: break-all;
      color: #555;
      font-size: 11px;
    }
  }
}

.sse-progress {
  margin-bottom: 12px;

  .sse-stage {
    text-align: center;
    font-size: 13px;
    color: #555;
    margin-top: 8px;
  }
}

.sse-logs {
  max-height: 200px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 10px;

  .sse-log {
    color: #4ec9b0;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    line-height: 1.6;
  }
}

.task-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.task-card {
  background: linear-gradient(135deg, #f0f7ff 0%, #fff 100%);
  border: 1px solid #d6e4ff;
  border-radius: 8px;
  padding: 14px;

  .task-name {
    font-size: 15px;
    font-weight: 600;
    color: #1890ff;
    margin-bottom: 6px;
  }

  .task-schedule {
    font-size: 12px;
    color: #fa8c16;
    margin-bottom: 6px;
    font-weight: 500;
  }

  .task-desc {
    font-size: 12px;
    color: #6b7280;
  }
}

.schedule-actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e8e8e8;
}

.ai-card {
  background: #fafbfc;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;

  .ai-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 14px;
  }

  .ai-result {
    background: #1e1e1e;
    color: #4ec9b0;
    padding: 10px;
    border-radius: 6px;
    font-size: 11px;
    margin-top: 10px;
    max-height: 180px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    font-family: 'Courier New', monospace;
  }
}

.rbac-row {
  margin-top: 8px;
}

.rbac-card {
  background: #fafbfc;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;

  .rbac-title {
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 14px;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 768px) {
  .backend-page {
    padding: 0;
  }

  .page-header {
    border-radius: 0;
    padding: 12px 16px;
  }

  .page-body {
    border-radius: 0;
    padding: 12px;
  }
}
</style>
