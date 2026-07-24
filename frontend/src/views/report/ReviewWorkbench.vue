<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useDisasterStore } from '@/stores/disaster'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DisasterEvent, EventStatus, ReviewAction } from '@/types'

const disaster = useDisasterStore()
// 注意：statusMeta 是 store 中的普通对象常量（非 ref），不能用 storeToRefs 解构，
// 否则解构结果为 undefined，模板里 statusMeta[...] 会抛 TypeError 导致整页渲染崩溃/卡死。
const { list, total, loading } = storeToRefs(disaster)

// 状态展示映射（本地常量，避免依赖 store 的非响应式属性）
const statusMeta: Record<EventStatus, { label: string; type: string }> = {
  PENDING_VERIFY: { label: '待核验', type: 'info' },
  CONFIRMED: { label: '已确认', type: 'warning' },
  IN_PROGRESS: { label: '处置中', type: 'primary' },
  CLOSED: { label: '已结束', type: 'success' },
  REJECTED: { label: '已驳回', type: 'danger' }
}

const filterStatus = ref<EventStatus | ''>('')
const drawer = ref(false)
const current = ref<DisasterEvent | null>(null)
const comment = ref('')

const statusOptions: { label: string; value: EventStatus }[] = [
  { label: '待核验', value: 'PENDING_VERIFY' },
  { label: '已确认', value: 'CONFIRMED' },
  { label: '处置中', value: 'IN_PROGRESS' },
  { label: '已结束', value: 'CLOSED' }
]

const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震', FLOOD: '洪涝', LANDSLIDE: '滑坡', DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱', FOREST_FIRE: '森林火灾', HAIL: '冰雹', TYPHOON: '台风'
}
const levelLabel: Record<string, string> = { I: 'I级', II: 'II级', III: 'III级', IV: 'IV级' }

function load() {
  disaster.fetchList({ status: filterStatus.value || undefined, pageSize: 100 })
}

function openDetail(row: DisasterEvent) {
  current.value = row
  comment.value = ''
  drawer.value = true
}

// 根据状态返回可执行动作
function actionsFor(status: EventStatus): { action: ReviewAction; label: string; type: string }[] {
  switch (status) {
    case 'PENDING_VERIFY':
      return [
        { action: 'CONFIRM', label: '确认灾情', type: 'primary' },
        { action: 'REJECT', label: '驳回', type: 'danger' }
      ]
    case 'CONFIRMED':
      return [{ action: 'CLOSE', label: '结束工单', type: 'success' }]
    default:
      return []
  }
}

async function doAction(row: DisasterEvent, action: ReviewAction) {
  if (action === 'REJECT' || action === 'CLOSE') {
    await ElMessageBox.confirm(action === 'REJECT' ? '确认驳回该灾情上报？' : '确认结束该工单？', '提示', { type: 'warning' })
  }
  await disaster.review({ eventId: row.id, action, comment: comment.value })
  ElMessage.success('操作成功')
  drawer.value = false
  load()
}

const pendingCount = computed(() => list.value.filter((d) => d.status === 'PENDING_VERIFY').length)

onMounted(load)
</script>

<template>
  <div class="review">
    <el-card class="page-card">
      <template #header>
        <div class="flex-between">
          <div><b>信息审核工作台</b><span class="text-muted"> 工单状态机：待核验 → 已确认 → 处置中 → 已结束</span></div>
          <el-badge :value="pendingCount" :hidden="!pendingCount" type="danger">
            <el-tag type="info">待核验</el-tag>
          </el-badge>
        </div>
      </template>
      <div class="filter">
        <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 160px" @change="load">
          <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-button @click="load">刷新</el-button>
      </div>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="code" label="工单编号" width="160" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ typeLabel[row.type] }}</template>
        </el-table-column>
        <el-table-column label="等级" width="70">
          <template #default="{ row }">{{ levelLabel[row.level] }}</template>
        </el-table-column>
        <el-table-column prop="city" label="州市" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="(statusMeta[row.status as keyof typeof statusMeta]?.type as any)">{{ statusMeta[row.status as keyof typeof statusMeta]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              v-for="a in actionsFor(row.status)"
              :key="a.action"
              link
              :type="(a.type as any)"
              @click="doAction(row, a.action)"
            >
              {{ a.label }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawer" :title="current?.title" size="46%">
      <template v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="工单编号">{{ current.code }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="(statusMeta[current.status]?.type as any)">{{ statusMeta[current.status]?.label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel[current.type] }}</el-descriptions-item>
          <el-descriptions-item label="等级">{{ levelLabel[current.level] }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ current.location }}</el-descriptions-item>
          <el-descriptions-item label="坐标">{{ current.geo.lng }}, {{ current.geo.lat }}</el-descriptions-item>
          <el-descriptions-item label="受影响人口">{{ current.affectedPopulation || 0 }}</el-descriptions-item>
          <el-descriptions-item label="伤亡人数">{{ current.casualties || 0 }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ current.description }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="current.images?.length" class="imgs">
          <el-image v-for="(img, i) in current.images" :key="i" :src="img" :preview-src-list="current.images" fit="cover" class="img" />
        </div>

        <el-divider />
        <el-input v-model="comment" type="textarea" :rows="2" placeholder="审核意见（可选）" />

        <div class="actions">
          <el-button
            v-for="a in actionsFor(current.status)"
            :key="a.action"
            :type="(a.type as any)"
            @click="doAction(current, a.action)"
          >
            {{ a.label }}
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.filter {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.imgs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.img {
  width: 120px;
  height: 90px;
  border-radius: 6px;
}
.actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}
</style>
