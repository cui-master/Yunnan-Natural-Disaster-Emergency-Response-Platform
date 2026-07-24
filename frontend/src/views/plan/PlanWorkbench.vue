<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useDisasterStore } from '@/stores/disaster'
import { usePlanStore } from '@/stores/plan'
import { generatePlanStream } from '@/api/plan'
import type { DisasterEvent, PlanSection, PlanReference, PlanCompliance, PlanStreamChunk } from '@/types'

const disaster = useDisasterStore()
const planStore = usePlanStore()

const events = ref<DisasterEvent[]>([])
const selectedEventId = ref<number | null>(null)
const streaming = ref(false)
const streamingText = ref('') // 当前正在生成的段落预览
const saveState = ref<'idle' | 'saved'>('idle')

// 正在构建 / 已生成的方案
const plan = reactive({
  id: 0 as number,
  title: '',
  sections: [] as PlanSection[],
  references: [] as PlanReference[],
  compliance: null as PlanCompliance | null,
  status: 'DRAFT' as string
})

const canGenerate = computed(() => !!selectedEventId.value && !streaming.value)
const activeIdx = computed(() => (plan.status === 'GENERATING' ? Math.max(0, plan.sections.length - 1) : -1))

// AI 生成过程步骤条（连接 → 各处置要点 → 合规审查 → 完成）
const steps = computed<{ label: string; state: 'done' | 'active' | 'wait' }[]>(() => {
  const list: { label: string; state: 'done' | 'active' | 'wait' }[] = [
    { label: '连接 AI 服务', state: 'wait' }
  ]
  plan.sections.forEach((s, i) => list.push({ label: s.title || `处置要点 ${i + 1}`, state: 'wait' }))
  list.push({ label: 'AI 合规审查', state: 'wait' })
  list.push({ label: '方案生成完成', state: 'wait' })

  if (plan.status === 'REVIEWING' || plan.status === 'APPROVED') {
    list.forEach((s) => (s.state = 'done'))
    return list
  }
  if (plan.status !== 'GENERATING') return list

  list[0].state = plan.sections.length > 0 ? 'done' : 'active'
  const refsDone = plan.references.length > 0
  const compSet = !!plan.compliance
  if (compSet || refsDone) {
    plan.sections.forEach((_, i) => (list[i + 1].state = 'done'))
    list[plan.sections.length + 1].state = 'active'
  } else {
    plan.sections.forEach((_, i) => {
      list[i + 1].state = i === plan.sections.length - 1 ? 'active' : 'done'
    })
  }
  return list
})

function loadEvents() {
  disaster.fetchList({ pageSize: 100 }).then(() => {
    events.value = disaster.list.filter((d) => d.status === 'CONFIRMED' || d.status === 'IN_PROGRESS')
  })
}

function resetPlan() {
  plan.id = 0
  plan.title = ''
  plan.sections = []
  plan.references = []
  plan.compliance = null
  plan.status = 'DRAFT'
  streamingText.value = ''
}

function onChunk(chunk: PlanStreamChunk) {
  switch (chunk.type) {
    case 'START':
      plan.id = chunk.planId || 0
      plan.title = chunk.title || '应急响应方案'
      plan.status = 'GENERATING'
      break
    case 'SECTION':
      plan.sections.push({ title: chunk.title || '', content: '' })
      break
    case 'CONTENT': {
      const sec = plan.sections[chunk.sectionIndex ?? plan.sections.length - 1]
      if (sec) sec.content += chunk.delta || ''
      streamingText.value = (sec?.content || '').slice(-48)
      break
    }
    case 'REFERENCE':
      if (chunk.reference) plan.references.push(chunk.reference)
      break
    case 'COMPLIANCE':
      plan.compliance = chunk.compliance || null
      break
    case 'DONE':
      plan.status = 'REVIEWING'
      streaming.value = false
      ElMessage.success('方案生成完成，可人工修改后提交审核')
      break
    case 'ERROR':
      streaming.value = false
      ElMessage.error(chunk.message || '生成失败')
      break
  }
}

let cancelStream: (() => void) | null = null

function generate() {
  if (!selectedEventId.value) return
  resetPlan()
  streaming.value = true
  saveState.value = 'idle'
  cancelStream = generatePlanStream(
    { eventId: selectedEventId.value },
    onChunk,
    (e) => {
      streaming.value = false
      console.error(e)
    }
  )
}

function stop() {
  cancelStream?.()
  streaming.value = false
}

async function save() {
  if (!plan.id) {
    ElMessage.warning('请先生成方案')
    return
  }
  await planStore.save(plan.id, {
    title: plan.title,
    sections: plan.sections,
    references: plan.references,
    compliance: plan.compliance ?? undefined,
    status: 'REVIEWING'
  })
  saveState.value = 'saved'
  ElMessage.success('已保存人工修改')
}

async function approve() {
  if (!plan.id) return
  await planStore.approve(plan.id)
  plan.status = 'APPROVED'
  ElMessage.success('方案已审批通过')
}

const progress = computed(() => {
  if (plan.status === 'GENERATING') return 'AI 正在生成处置方案…'
  if (plan.status === 'REVIEWING') return '方案待人工确认/修改'
  if (plan.status === 'APPROVED') return '方案已审批通过'
  return '尚未生成方案'
})

onMounted(loadEvents)
</script>

<template>
  <div class="plan">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
          <div class="section-title">应急方案生成工作台</div>
          <el-tag :type="plan.status === 'APPROVED' ? 'success' : 'warning'" effect="dark">{{ progress }}</el-tag>
        </div>
        <p class="head-sub">AI Agent 结合灾情 + RAG 预案生成，支持人工修改与合规审查</p>
      </template>

      <div class="toolbar">
        <el-select v-model="selectedEventId" placeholder="选择灾情工单" style="width: 320px" :disabled="streaming">
          <el-option v-for="e in events" :key="e.id" :label="`${e.code} ${e.title}`" :value="e.id" />
        </el-select>
        <el-button type="primary" :disabled="!canGenerate" @click="generate">
          <el-icon><VideoPlay /></el-icon> 生成方案
        </el-button>
        <el-button v-if="streaming" type="danger" @click="stop">停止</el-button>
        <el-button :disabled="!plan.id || streaming" @click="save">保存修改</el-button>
        <el-button type="success" :disabled="!plan.id || streaming || plan.status === 'APPROVED'" @click="approve">审批通过</el-button>
        <span v-if="saveState === 'saved'" class="text-muted">已保存 ✓</span>
      </div>

      <el-empty v-if="!plan.sections.length && !streaming" description="请选择灾情工单并点击「生成方案」" :image-size="90" />

      <div v-else class="gen-grid">
        <!-- 左：AI 生成过程 -->
        <aside class="gen-flow">
          <div class="flow-head">
            <span class="ai-dot"><span class="ai-core">AI</span></span>
            <div>
              <div class="flow-title">AI 生成过程</div>
              <div class="flow-sub">{{ streaming ? streamingText || '连接 AI 服务，接收流式输出…' : '方案构建流程' }}</div>
            </div>
          </div>
          <ul class="stepper">
            <li v-for="(s, i) in steps" :key="i" :class="['step', s.state]">
              <span class="step-mark">
                <svg v-if="s.state === 'done'" viewBox="0 0 24 24" class="tick"><path d="M5 13l4 4L19 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span v-else-if="s.state === 'active'" class="spin"></span>
                <span v-else class="dot"></span>
              </span>
              <span class="step-label">{{ s.label }}</span>
            </li>
          </ul>
        </aside>

        <!-- 右：方案正文 -->
        <section class="gen-doc">
          <div class="doc-title">
            <el-icon class="doc-ic"><Document /></el-icon>
            <b>{{ plan.title }}</b>
          </div>

          <div v-for="(sec, i) in plan.sections" :key="i" class="doc-sec" :class="{ streaming: i === activeIdx }">
            <div class="sec-title">
              <span class="sec-bar"></span>{{ sec.title }}
            </div>
            <div v-if="i === activeIdx" class="sec-body">{{ sec.content }}<span class="caret">▋</span></div>
            <el-input
              v-else
              v-model="plan.sections[i].content"
              type="textarea"
              :rows="Math.max(3, Math.ceil(sec.content.length / 40))"
              :disabled="streaming"
              @input="saveState = 'idle'"
            />
          </div>

          <template v-if="plan.references.length">
            <div class="block-title"><span class="sec-bar"></span>引用来源（RAG 检索）</div>
            <el-table :data="plan.references" border size="small">
              <el-table-column prop="docTitle" label="预案/规范" min-width="200" />
              <el-table-column prop="snippet" label="片段" min-width="260" show-overflow-tooltip />
              <el-table-column label="相关度" width="90">
                <template #default="{ row }">{{ (row.score * 100).toFixed(0) }}%</template>
              </el-table-column>
            </el-table>
          </template>

          <template v-if="plan.compliance">
            <div class="block-title"><span class="sec-bar"></span>AI 合规审查</div>
            <el-result
              :icon="plan.compliance.passed ? 'success' : 'warning'"
              :title="`合规评分 ${plan.compliance.score} 分 · ${plan.compliance.passed ? '通过' : '需修正'}`"
            >
              <template #extra>
                <div class="comp">
                  <div v-if="plan.compliance.issues.length"><b>问题：</b>{{ plan.compliance.issues.join('；') }}</div>
                  <div v-if="plan.compliance.suggestions.length"><b>建议：</b>{{ plan.compliance.suggestions.join('；') }}</div>
                </div>
              </template>
            </el-result>
          </template>
        </section>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.head-sub {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--ydr-sub);
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.gen-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 18px;
  margin-top: 16px;
  align-items: start;
}
/* 左侧生成流程 */
.gen-flow {
  background: linear-gradient(180deg, #fbfcfe, #f4f7fb);
  border: 1px solid var(--ydr-border);
  border-radius: var(--ydr-radius);
  padding: 16px;
  position: sticky;
  top: 16px;
}
.flow-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.ai-dot {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, #2f80ed, #1d4ed8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(47, 128, 237, 0.3);
}
.ai-core {
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
}
.flow-title {
  font-weight: 600;
  color: var(--ydr-ink);
  font-size: 14px;
}
.flow-sub {
  font-size: 11px;
  color: var(--ydr-sub);
  margin-top: 2px;
  min-height: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}
.stepper {
  list-style: none;
  margin: 0;
  padding: 0;
}
.step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  position: relative;
}
.step:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 28px;
  bottom: -2px;
  width: 2px;
  background: var(--ydr-border);
}
.step.done:not(:last-child)::before {
  background: var(--ydr-success);
}
.step-mark {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 2px solid var(--ydr-border);
  color: var(--ydr-success);
  flex-shrink: 0;
  z-index: 1;
}
.step.done .step-mark {
  border-color: var(--ydr-success);
  background: var(--ydr-success);
  color: #fff;
}
.step.active .step-mark {
  border-color: var(--ydr-info);
}
.tick {
  width: 13px;
  height: 13px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #c4ccd6;
}
.spin {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(47, 128, 237, 0.25);
  border-top-color: var(--ydr-info);
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.step-label {
  font-size: 13px;
  color: var(--ydr-sub);
}
.step.active .step-label {
  color: var(--ydr-info);
  font-weight: 600;
}
.step.done .step-label {
  color: var(--ydr-text);
}
/* 右侧方案正文 */
.gen-doc {
  min-width: 0;
}
.doc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 19px;
  color: var(--ydr-ink);
  margin-bottom: 14px;
}
.doc-ic {
  color: var(--ydr-primary);
}
.doc-sec {
  background: #fff;
  border: 1px solid var(--ydr-border);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.doc-sec.streaming {
  border-color: var(--ydr-info);
  box-shadow: 0 0 0 3px rgba(47, 128, 237, 0.12);
}
.sec-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--ydr-ink);
}
.sec-bar {
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: var(--ydr-primary);
}
.sec-body {
  font-size: 13.5px;
  line-height: 1.9;
  color: #3a4654;
  white-space: pre-wrap;
  word-break: break-word;
}
.caret {
  display: inline-block;
  margin-left: 1px;
  color: var(--ydr-info);
  animation: blink 1s step-end infinite;
  font-weight: 700;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.block-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin: 18px 0 8px;
  color: var(--ydr-ink);
}
.comp {
  text-align: left;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
@media (max-width: 900px) {
  .gen-grid {
    grid-template-columns: 1fr;
  }
  .gen-flow {
    position: static;
  }
}
</style>
