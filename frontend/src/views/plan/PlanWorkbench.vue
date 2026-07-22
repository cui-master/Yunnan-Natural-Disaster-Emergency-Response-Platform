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
      streamingText.value = (sec?.content || '').slice(-40)
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
          <div><b>应急方案生成工作台</b><span class="text-muted"> AI Agent 结合灾情+RAG 预案生成，支持人工修改与合规审查</span></div>
          <el-tag :type="plan.status === 'APPROVED' ? 'success' : 'warning'">{{ progress }}</el-tag>
        </div>
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

      <el-alert v-if="streaming" :title="streamingText || '连接 AI 服务，接收流式输出…'" type="info" :closable="false" show-icon style="margin: 12px 0" />

      <el-empty v-if="!plan.sections.length && !streaming" description="请选择灾情工单并点击「生成方案」" />

      <div v-else class="content">
        <h2 class="plan-title">{{ plan.title }}</h2>
        <div v-for="(sec, i) in plan.sections" :key="i" class="section">
          <div class="sec-title">{{ sec.title }}</div>
          <el-input
            v-model="plan.sections[i].content"
            type="textarea"
            :rows="Math.max(3, Math.ceil(sec.content.length / 40))"
            :disabled="streaming"
            @input="saveState = 'idle'"
          />
        </div>

        <template v-if="plan.references.length">
          <div class="block-title">引用来源（RAG 检索）</div>
          <el-table :data="plan.references" border size="small">
            <el-table-column prop="docTitle" label="预案/规范" min-width="200" />
            <el-table-column prop="snippet" label="片段" min-width="260" show-overflow-tooltip />
            <el-table-column label="相关度" width="90">
              <template #default="{ row }">{{ (row.score * 100).toFixed(0) }}%</template>
            </el-table-column>
          </el-table>
        </template>

        <template v-if="plan.compliance">
          <div class="block-title">AI 合规审查</div>
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
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.content {
  margin-top: 16px;
}
.plan-title {
  font-size: 20px;
  margin: 0 0 14px;
  color: #1f2d3d;
}
.section {
  margin-bottom: 14px;
}
.sec-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #c0392b;
}
.block-title {
  font-weight: 600;
  margin: 18px 0 8px;
  color: #1f2d3d;
}
.comp {
  text-align: left;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
