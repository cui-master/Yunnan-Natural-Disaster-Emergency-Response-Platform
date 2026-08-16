<template>
  <div class="plan-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#1890ff"><Document /></el-icon>
        <span>应急方案生成工作台</span>
        <el-tag type="info" effect="light" size="small">AI 辅助 + 人工修改</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="MagicStick" @click="showGenerate = true">
          AI生成方案
        </el-button>
        <el-button type="success" :icon="DocumentChecked" @click="handleSubmit" :loading="submitting">
          提交
        </el-button>
      </div>
    </div>

    <div class="workbench">
      <!-- 顶部：四个措施框 -->
      <div class="top-panels">
        <div class="panel-section measure-panel">
          <div class="section-title">
            <el-icon color="#f5222d"><AlarmClock /></el-icon>
            短期措施（0-24小时）
            <el-button size="small" type="primary" text :icon="Plus" @click="addMeasure('short')">添加</el-button>
          </div>
          <div class="measure-list">
            <div v-for="(m, idx) in planForm.shortTermMeasures" :key="'s-'+idx" class="measure-item simple">
              <el-input v-model="m.具体内容" size="small" type="textarea" :rows="2" placeholder="具体内容" />
              <el-button size="small" text type="danger" :icon="Delete" @click="planForm.shortTermMeasures.splice(idx, 1)" />
            </div>
            <el-empty v-if="!planForm.shortTermMeasures.length" description="暂无短期措施" :image-size="50" />
          </div>
        </div>

        <div class="panel-section measure-panel">
          <div class="section-title">
            <el-icon color="#fa8c16"><Clock /></el-icon>
            中期措施（1-7天）
            <el-button size="small" type="primary" text :icon="Plus" @click="addMeasure('mid')">添加</el-button>
          </div>
          <div class="measure-list">
            <div v-for="(m, idx) in planForm.midTermMeasures" :key="'m-'+idx" class="measure-item simple">
              <el-input v-model="m.具体内容" size="small" type="textarea" :rows="2" placeholder="具体内容" />
              <el-button size="small" text type="danger" :icon="Delete" @click="planForm.midTermMeasures.splice(idx, 1)" />
            </div>
            <el-empty v-if="!planForm.midTermMeasures.length" description="暂无中期措施" :image-size="50" />
          </div>
        </div>

        <div class="panel-section measure-panel">
          <div class="section-title">
            <el-icon color="#52c41a"><Timer /></el-icon>
            长期措施（7天以上）
            <el-button size="small" type="primary" text :icon="Plus" @click="addMeasure('long')">添加</el-button>
          </div>
          <div class="measure-list">
            <div v-for="(m, idx) in planForm.longTermMeasures" :key="'l-'+idx" class="measure-item simple">
              <el-input v-model="m.具体内容" size="small" type="textarea" :rows="2" placeholder="具体内容" />
              <el-button size="small" text type="danger" :icon="Delete" @click="planForm.longTermMeasures.splice(idx, 1)" />
            </div>
            <el-empty v-if="!planForm.longTermMeasures.length" description="暂无长期措施" :image-size="50" />
          </div>
        </div>

        <div class="panel-section measure-panel">
          <div class="section-title">
            <el-icon color="#722ed1"><EditPen /></el-icon>
            方案备注
          </div>
          <el-input
            v-model="planForm.remarks"
            type="textarea"
            :rows="8"
            placeholder="在此输入方案备注、补充说明、注意事项等..."
          />
        </div>
      </div>

      <!-- 中间：基本信息 -->
      <div class="panel-section">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          基本信息
        </div>
        <el-form :model="planForm" label-width="90px" size="default">
          <el-row :gutter="12">
            <el-col :span="8">
              <el-form-item label="方案编号">
                <el-input v-model="planForm.planNo" placeholder="自动生成" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="方案标题">
                <el-input v-model="planForm.title" placeholder="方案标题" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="关联灾情">
                <el-input v-model="planForm.areaName" placeholder="区域名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="灾害类型">
                <el-select v-model="planForm.disasterType" style="width: 100%;">
                  <el-option v-for="t in disasterTypes" :key="t.value" :label="t.label" :value="t.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="风险等级">
                <el-select v-model="planForm.riskLevel" style="width: 100%;">
                  <el-option label="低" value="低" />
                  <el-option label="中" value="中" />
                  <el-option label="高" value="高" />
                  <el-option label="极高" value="极高" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="生成来源">
                <el-tag :type="sourceTagType" effect="light">{{ planForm.source }}</el-tag>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <!-- 下方：各方案板块 -->
      <div class="bottom-panels">
        <div class="panel-section">
          <div class="section-title">
            <el-icon color="#1890ff"><Goods /></el-icon>
            物资调度方案
            <el-button size="small" type="primary" text :icon="Plus" @click="addMaterial">添加仓库</el-button>
          </div>
          <div class="resource-list">
            <div v-for="(item, idx) in planForm.materials" :key="idx" class="resource-item editable material-warehouse">
              <div class="item-header">
                <el-input v-model="item.resourceNo" size="small" placeholder="仓库编号" style="width: 120px; margin-right: 8px;" />
                <el-input v-model="item.name" size="small" placeholder="仓库名称" style="flex: 1; margin-right: 8px;" />
                <el-button size="small" text type="primary" :icon="Plus" @click="addMaterialItem(item)">添加物资</el-button>
                <el-button size="small" text type="danger" :icon="Delete" @click="planForm.materials.splice(idx, 1)" />
              </div>
              <div v-if="item.items && item.items.length" class="material-items">
                <div v-for="(it, iidx) in item.items" :key="iidx" class="material-item-row">
                  <el-input v-model="it.name" size="small" placeholder="物资名称" style="flex: 1; margin-right: 8px;" />
                  <span class="qty-label">分配：</span>
                  <el-input-number v-model="it.allocatedQty" :min="0" size="small" controls-position="right" style="width: 100px; margin-right: 8px;" />
                  <el-input v-model="it.unit" size="small" placeholder="单位" style="width: 60px; margin-right: 8px;" />
                  <span class="stock-hint">库存 {{ it.availableQty || 0 }}</span>
                  <el-button size="small" text type="danger" :icon="Delete" @click="item.items.splice(iidx, 1)" />
                </div>
              </div>
              <el-empty v-else description="该仓库暂无物资明细" :image-size="40" style="padding: 8px 0;" />
            </div>
            <el-empty v-if="!planForm.materials.length" description="暂无物资分配" :image-size="60" />
          </div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <el-icon color="#fa8c16"><Suitcase /></el-icon>
            救援队伍方案
            <el-button size="small" type="primary" text :icon="Plus" @click="addTeam">添加队伍</el-button>
          </div>
          <div class="resource-list">
            <div v-for="(item, idx) in planForm.teams" :key="idx" class="resource-item editable team-item">
              <div class="item-header">
                <el-input v-model="item.resourceNo" size="small" placeholder="队伍编号" style="width: 120px; margin-right: 8px;" />
                <el-input v-model="item.name" size="small" placeholder="队伍名称" style="flex: 1; margin-right: 8px;" />
                <el-button size="small" text type="danger" :icon="Delete" @click="planForm.teams.splice(idx, 1)" />
              </div>
              <div class="item-details">
                <span>派遣人数：<el-input-number v-model="item.dispatchSize" :min="0" size="small" controls-position="right" style="width: 110px;" /></span>
                <el-select v-model="item.isBusy" size="small" placeholder="状态" style="width: 100px;">
                  <el-option label="空闲" :value="false" />
                  <el-option label="派遣(忙碌)" :value="true" />
                </el-select>
              </div>
              <div class="team-task">
                <el-input v-model="item.task" size="small" type="textarea" :rows="2" placeholder="任务内容" />
              </div>
            </div>
            <el-empty v-if="!planForm.teams.length" description="暂无救援队伍" :image-size="60" />
          </div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <el-icon color="#52c41a"><HomeFilled /></el-icon>
            避难场所方案
            <el-button size="small" type="primary" text :icon="Plus" @click="addShelter">添加场所</el-button>
          </div>
          <div class="shelter-list">
            <div v-for="(item, idx) in planForm.shelters" :key="idx" class="shelter-item editable">
              <div class="shelter-header">
                <el-input v-model="item.resourceNo" size="small" placeholder="场所编号" style="width: 120px; margin-right: 8px;" />
                <el-input v-model="item.name" size="small" placeholder="场所名称" style="flex: 1; margin-right: 8px;" />
                <el-button size="small" text type="danger" :icon="Delete" @click="planForm.shelters.splice(idx, 1)" />
              </div>
              <div class="shelter-fields">
                <span>容纳人数：<el-input-number v-model="item.evacuees" :min="0" size="small" controls-position="right" style="width: 120px;" /></span>
                <span>最大容量：<el-input-number v-model="item.maxCapacity" :min="0" size="small" controls-position="right" style="width: 120px;" /></span>
              </div>
              <el-progress :percentage="item.maxCapacity > 0 ? Math.round((item.evacuees || 0) / item.maxCapacity * 100) : 0" :stroke-width="6" />
            </div>
            <el-empty v-if="!planForm.shelters.length" description="暂无避难场所" :image-size="60" />
          </div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <el-icon color="#13c2c2"><Guide /></el-icon>
            人员疏散方案
          </div>
          <el-form :model="planForm.evacuation" label-width="100px">
            <el-form-item label="疏散路线">
              <el-input v-model="planForm.evacuation.routes" type="textarea" :rows="3" placeholder="描述疏散路线..." />
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 生成方案弹窗 -->
    <el-dialog v-model="showGenerate" title="AI 生成应急处置方案" width="560px" @open="loadIncidents">
      <el-form :model="genForm" label-width="100px">
        <el-form-item label="受灾点" required>
          <el-select
            v-model="genForm.incidentIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            placeholder="从Neo4j选择受灾点（可多选，至少一个）"
            style="width: 100%;"
            :loading="incidentLoading"
          >
            <el-option
              v-for="inc in incidentList"
              :key="inc.id"
              :label="`${inc.name}（${inc.location || ''}，${inc.disasterType || ''}）`"
              :value="inc.id"
            >
              <span style="float: left;">{{ inc.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px;">
                {{ inc.location }} · {{ inc.disasterType }}
                <el-tag v-if="inc.riskLevel" size="small" :type="riskTagType(inc.riskLevel)" style="margin-left:4px;">{{ inc.riskLevel }}</el-tag>
              </span>
            </el-option>
          </el-select>
          <div style="font-size:12px;color:#909399;line-height:1.4;margin-top:4px;">
            受灾点数据来自Neo4j图数据库，支持多选。选中后将以所选受灾点为中心提取关联三元组。
          </div>
        </el-form-item>
        <el-form-item label="灾害类型">
          <el-select v-model="genForm.disasterType" multiple collapse-tags collapse-tags-tooltip placeholder="可多选" style="width: 100%;">
            <el-option v-for="t in disasterTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="genForm.riskLevel" multiple collapse-tags collapse-tags-tooltip placeholder="可多选" style="width: 100%;">
            <el-option label="低" value="低" />
            <el-option label="中" value="中" />
            <el-option label="高" value="高" />
            <el-option label="极高" value="极高" />
          </el-select>
        </el-form-item>
        <el-form-item label="受灾人数">
          <el-input-number v-model="genForm.affectedPeople" :min="0" />
          <span style="margin-left: 8px;">人</span>
        </el-form-item>
        <el-form-item label="风险情报">
          <el-input v-model="genForm.riskInfo" type="textarea" :rows="3" placeholder="简要描述灾情、风险情况等..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerate = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          开始生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generatePlan, savePlan, submitPlan, listIncidents } from '@/api'
import { DISASTER_TYPES } from '@/utils/constants'
import {
  Document, MagicStick, DocumentChecked, InfoFilled, Goods, Suitcase,
  HomeFilled, Guide, EditPen, Plus, Delete, AlarmClock, Clock, Timer
} from '@element-plus/icons-vue'

const route = useRoute()
const disasterTypes = DISASTER_TYPES
const showGenerate = ref(false)
const generating = ref(false)
const submitting = ref(false)
const incidentList = ref([])
const incidentLoading = ref(false)

const genForm = reactive({
  incidentIds: [],
  disasterType: [],
  riskLevel: [],
  affectedPeople: 0,
  riskInfo: ''
})

const planForm = reactive({
  id: null,
  planNo: '',
  title: '',
  incidentId: null,
  areaName: '',
  disasterType: '',
  riskLevel: '',
  source: 'AI生成',
  materials: [],
  teams: [],
  shelters: [],
  evacuation: {
    routes: ''
  },
  shortTermMeasures: [],
  midTermMeasures: [],
  longTermMeasures: [],
  remarks: ''
})

const sourceTagType = computed(() => {
  const map = { 'Dify工作流': 'success', 'AI生成': 'success', 'LLM降级': 'warning', '人工编辑': 'info', 'template': 'info' }
  return map[planForm.source] || 'info'
})

function addMeasure(type) {
  const prefix = type === 'short' ? 's' : type === 'mid' ? 'm' : 'l'
  const list = type === 'short' ? planForm.shortTermMeasures : type === 'mid' ? planForm.midTermMeasures : planForm.longTermMeasures
  const time = type === 'short' ? '0-24小时内' : type === 'mid' ? '1-7天内' : '7天以上'
  list.push({
    措施编号: `${prefix}${list.length + 1}`,
    措施名称: '',
    执行时间: time,
    执行部门: '',
    具体内容: '',
    优先级: '中',
    预计效果: ''
  })
}

async function loadIncidents() {
  incidentLoading.value = true
  try {
    const res = await listIncidents()
    incidentList.value = res.data || res || []
  } catch (e) {
    console.error('加载受灾点列表失败:', e)
    ElMessage.warning('加载受灾点列表失败，请确认Neo4j数据已同步')
  } finally {
    incidentLoading.value = false
  }
}

function riskTagType(level) {
  const lv = String(level)
  if (lv.includes('极高') || lv.includes('4') || lv.includes('红')) return 'danger'
  if (lv.includes('高') || lv.includes('3') || lv.includes('橙')) return 'warning'
  if (lv.includes('中') || lv.includes('2') || lv.includes('黄')) return ''
  return 'info'
}

async function handleGenerate() {
  if (!genForm.incidentIds || genForm.incidentIds.length === 0) {
    ElMessage.warning('请至少选择一个受灾点')
    return
  }
  generating.value = true
  try {
    // 获取选中受灾点的名称用于标题
    const selectedIncidents = incidentList.value.filter(i => genForm.incidentIds.includes(i.id))
    const areaNames = [...new Set(selectedIncidents.map(i => i.location).filter(Boolean))]
    const areaDisplay = areaNames.length > 0 ? areaNames.join('、') : selectedIncidents.map(i => i.name).join('、')
    const firstIncidentId = genForm.incidentIds[0]
    const totalAffected = selectedIncidents.reduce((sum, i) => sum + (Number(i.affectedPeople) || 0), 0)
    const disasterTypeText = (genForm.disasterType || []).join('、')
    const riskLevelText = (genForm.riskLevel || []).join('、')
    const res = await generatePlan({
      incidentIds: genForm.incidentIds,
      incidentId: firstIncidentId,
      areaName: areaDisplay,
      disasterType: disasterTypeText || '未知灾害',
      riskLevel: riskLevelText || '中',
      affectedPeople: genForm.affectedPeople || totalAffected,
      riskInfo: genForm.riskInfo
    })
    console.log('========== AI方案生成完整返回 ==========')
    console.log('res:', JSON.stringify(res, null, 2))
    if (res.success) {
      // res.data 是后端 Result 包装的 data，即 ai-service 返回的原始对象
      const aiData = res.data || {}
      console.log('aiData:', JSON.stringify(aiData, null, 2))
      console.log('aiData.plan:', JSON.stringify(aiData.plan, null, 2))
      console.log('aiData.fallback_level:', aiData.fallback_level)
      console.log('aiData.ai_raw_output:', aiData.ai_raw_output)
      console.log('aiData.graph_data keys:', Object.keys(aiData.graph_data || {}))
      const data = aiData.plan || aiData
      // 填充方案
      planForm.incidentId = firstIncidentId ? Number(firstIncidentId) : null
      planForm.areaName = areaDisplay
      planForm.disasterType = disasterTypeText
      planForm.riskLevel = riskLevelText
      planForm.title = `${areaDisplay}${disasterTypeText}应急处置方案`
      planForm.planNo = `EP-${Date.now()}`
      planForm.source = aiData.fallback_level === 'none' ? 'Dify工作流' : (aiData.fallback_level === 'deepseek' ? 'DeepSeek(兜底)' : (aiData.fallback_level === 'template' ? '模板生成' : 'AI生成'))

      // 填充措施
      planForm.shortTermMeasures = (data.shortTermMeasures || data['短期措施'] || []).map((m, i) => ({
        措施编号: m.措施编号 || `s${i+1}`,
        措施名称: m.措施名称 || '',
        执行时间: m.执行时间 || '0-24小时内',
        执行部门: m.执行部门 || '',
        具体内容: m.具体内容 || '',
        优先级: m.优先级 || '中',
        预计效果: m.预计效果 || ''
      }))
      planForm.midTermMeasures = (data.midTermMeasures || data['中期措施'] || []).map((m, i) => ({
        措施编号: m.措施编号 || `m${i+1}`,
        措施名称: m.措施名称 || '',
        执行时间: m.执行时间 || '1-7天内',
        执行部门: m.执行部门 || '',
        具体内容: m.具体内容 || '',
        优先级: m.优先级 || '中',
        预计效果: m.预计效果 || ''
      }))
      planForm.longTermMeasures = (data.longTermMeasures || data['长期措施'] || []).map((m, i) => ({
        措施编号: m.措施编号 || `l${i+1}`,
        措施名称: m.措施名称 || '',
        执行时间: m.执行时间 || '7天以上',
        执行部门: m.执行部门 || '',
        具体内容: m.具体内容 || '',
        优先级: m.优先级 || '中',
        预计效果: m.预计效果 || ''
      }))
      planForm.remarks = data.remarks || data['方案备注'] || ''

      // 填充资源方案：优先使用Dify返回的分配方案，若没有则从graph_data获取可用资源列表
      const g = aiData.graph_data || {}
      const warehouseMap = {}
      ;(g.warehouses || []).forEach(w => { warehouseMap[w.resourceNo] = w })
      const teamMap = {}
      ;(g.teams || []).forEach(t => { teamMap[t.resourceNo] = t })
      const shelterMap = {}
      ;(g.shelters || []).forEach(s => { shelterMap[s.resourceNo] = s })

      // 物资分配（支持新结构：仓库 + items 明细；兼容旧结构）
      const materialsPlan = data.materials_plan || data['物资分配'] || []
      if (materialsPlan.length > 0 && materialsPlan[0].items) {
        // 新结构：仓库 + items 明细
        planForm.materials = materialsPlan.map(m => {
          const w = warehouseMap[m.resourceNo] || {}
          return {
            resourceNo: m.resourceNo || w.resourceNo || '',
            name: m.name || w.name || '',
            items: (m.items || []).map(it => ({
              name: it.name || '',
              allocatedQty: it.allocatedQty || it.quantity || 0,
              unit: it.unit || '件',
              availableQty: it.availableQty || 0
            }))
          }
        })
      } else if (materialsPlan.length > 0) {
        // 旧结构：兼容（把所有物资归到一个默认仓库）
        planForm.materials = [{
          resourceNo: '',
          name: '默认调配仓库',
          items: materialsPlan.map(m => ({
            name: m.name || '',
            allocatedQty: m.allocatedQty || m.quantity || 0,
            unit: m.unit || '件',
            availableQty: m.availableQty || 0
          }))
        }]
      } else {
        planForm.materials = []
      }

      // 救援队伍方案
      const teamsPlan = data.teams_plan || data['救援队伍方案'] || []
      if (teamsPlan.length > 0) {
        planForm.teams = teamsPlan.map((t, i) => {
          const gt = teamMap[t.resourceNo] || {}
          return {
            resourceNo: t.resourceNo || gt.resourceNo || '',
            name: t.name || gt.name || '',
            dispatchSize: t.dispatchSize || t.size || gt.availableSize || gt.size || gt.availableQty || 0,
            isBusy: t.isBusy !== undefined ? t.isBusy : true,
            task: t.task || `赶赴灾区开展搜救、转移安置及秩序维护工作`
          }
        })
      } else if (g.teams && g.teams.length > 0) {
        planForm.teams = (g.teams || []).map(t => ({
          resourceNo: t.resourceNo,
          name: t.name,
          dispatchSize: t.availableSize || t.size || t.availableQty || 0,
          isBusy: true,
          task: `赶赴灾区开展搜救、转移安置及秩序维护工作`
        }))
      } else {
        planForm.teams = []
      }

      // 避难场所方案
      const sheltersPlan = data.shelters_plan || data['避难场所方案'] || []
      if (sheltersPlan.length > 0) {
        planForm.shelters = sheltersPlan.map((s, i) => {
          const gs = shelterMap[s.resourceNo] || {}
          return {
            resourceNo: s.resourceNo || gs.resourceNo || '',
            name: s.name || gs.name || '',
            maxCapacity: s.maxCapacity || gs.maxCapacity || gs.capacity || gs.availableQty || 0,
            evacuees: s.evacuees || s.count || 0
          }
        })
      } else {
        planForm.shelters = (g.shelters || []).map(s => ({
          resourceNo: s.resourceNo,
          name: s.name,
          maxCapacity: s.maxCapacity || s.capacity || s.availableQty || 0,
          evacuees: 0
        }))
      }

      // 人员疏散方案：只保留疏散路线
      const evacPlan = data.evacuation_plan || data['人员疏散方案'] || {}
      planForm.evacuation = {
        routes: evacPlan.routes || evacPlan.疏散路线 || ''
      }

      ElMessage.success('方案生成成功，请核对后提交')
      showGenerate.value = false
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('生成失败: ' + (e.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

function addMaterial() {
  planForm.materials.push({
    resourceNo: '',
    name: '',
    items: []
  })
}

function addMaterialItem(material) {
  if (!material.items) material.items = []
  material.items.push({
    name: '',
    allocatedQty: 0,
    unit: '件',
    availableQty: 0
  })
}

function addTeam() {
  planForm.teams.push({
    resourceNo: '',
    name: '',
    dispatchSize: 0,
    isBusy: false,
    task: ''
  })
}

function addShelter() {
  planForm.shelters.push({
    resourceNo: '',
    name: '',
    maxCapacity: 1000,
    evacuees: 0
  })
}

async function handleSubmit() {
  try {
    await ElMessageBox.confirm(
      '提交后将同步更新资源状态（物资库存、队伍状态、避难场所容量），确认提交？',
      '确认提交',
      { type: 'warning', confirmButtonText: '确认提交', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    // 先保存方案
    const saveRes = await savePlan({
      planNo: planForm.planNo || `EP-${Date.now()}`,
      title: planForm.title || `${planForm.areaName}应急方案`,
      incidentId: planForm.incidentId,
      areaName: planForm.areaName,
      disasterType: planForm.disasterType,
      riskLevel: planForm.riskLevel,
      source: planForm.source,
      materials: planForm.materials,
      teams: planForm.teams,
      shelters: planForm.shelters,
      evacuation: planForm.evacuation,
      shortTermMeasures: planForm.shortTermMeasures,
      midTermMeasures: planForm.midTermMeasures,
      longTermMeasures: planForm.longTermMeasures,
      remarks: planForm.remarks
    })

    if (saveRes.success && saveRes.data) {
      planForm.id = saveRes.data.id
      // 调用提交接口，同步更新Neo4j
      await submitPlan(planForm.id)
      ElMessage.success('方案提交成功，资源状态已同步更新')
      planForm.source = '人工编辑'
    } else {
      ElMessage.error('保存失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('提交失败: ' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  // 初始化默认数据
  planForm.title = ''
})
</script>

<style scoped lang="scss">
.plan-page {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-panels {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  @media (max-width: 1400px) {
    grid-template-columns: repeat(2, 1fr);
  }
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.bottom-panels {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;

  @media (max-width: 1000px) {
    grid-template-columns: 1fr;
  }
}

.panel-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.measure-panel {
  min-height: 200px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;

  .el-button {
    margin-left: auto;
  }
}

.measure-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.measure-item {
  padding: 10px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #e5e7eb;
}

.measure-header {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.measure-fields {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;

  .el-input {
    flex: 1;
  }
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
}

.resource-item.editable .item-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.resource-item.team-item {
  border-left-color: #fa8c16;
}

.item-details {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #6b7280;
  align-items: center;
}

.shelter-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;

  @media (max-width: 500px) {
    grid-template-columns: 1fr;
  }
}

.shelter-item {
  padding: 12px;
  background: #f0fdf4;
  border-radius: 6px;
  border-left: 3px solid #52c41a;
}

.shelter-item.editable .shelter-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.shelter-fields {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #6b7280;
  align-items: center;
  margin-bottom: 6px;
}

.measure-item.simple {
  display: flex;
  gap: 8px;
  align-items: flex-start;

  .el-textarea {
    flex: 1;
  }

  .el-button {
    margin-top: 4px;
  }
}

.material-warehouse {
  border-left-color: #1890ff;
}

.material-items {
  margin-top: 10px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.material-item-row {
  display: flex;
  align-items: center;
  gap: 4px;

  .qty-label {
    font-size: 12px;
    color: #6b7280;
    white-space: nowrap;
  }

  .stock-hint {
    font-size: 12px;
    color: #9ca3af;
    white-space: nowrap;
  }
}

.team-task {
  margin-top: 8px;
}
</style>
