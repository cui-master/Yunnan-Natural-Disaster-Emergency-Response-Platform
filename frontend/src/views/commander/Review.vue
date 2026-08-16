<template>
  <div class="review-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#fa8c16"><CircleCheck /></el-icon>
        <span>审核事件</span>
        <el-tag type="warning" effect="light" size="small">{{ pendingCount }} 条待审核</el-tag>
      </div>
      <div class="header-actions">
        <el-input v-model="searchKeyword" placeholder="搜索标题/位置" style="width: 220px;" clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filterType" placeholder="灾害类型" clearable style="width: 140px;">
          <el-option v-for="t in disasterTypes" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-button type="primary" :icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <div class="review-list">
      <div
        v-for="item in filteredList"
        :key="item.id"
        class="review-card"
      >
        <div class="card-header">
          <div class="card-title">
            <el-tag :color="getDisasterColor(item.type)" effect="dark" size="small" class="type-tag">
              {{ item.type }}
            </el-tag>
            <span class="title-text">{{ item.title }}</span>
            <el-tag :type="riskTagType(item.level)" effect="light" size="small" round>
              {{ item.level }}风险
            </el-tag>
          </div>
          <el-tag type="warning" effect="light" size="small">{{ item.status }}</el-tag>
        </div>

        <div class="card-body">
          <div class="info-row">
            <span><el-icon :size="14"><User /></el-icon> 上报人：{{ item.reporter }}</span>
            <span><el-icon :size="14"><Location /></el-icon> {{ item.address }}</span>
            <span><el-icon :size="14"><Clock /></el-icon> {{ item.time }}</span>
          </div>
          <p class="description">{{ item.description }}</p>
        </div>

        <div class="card-footer">
          <div class="risk-assess">
            <span class="assess-label">风险评估：</span>
            <el-rate v-model="item.assessLevel" :max="5" />
          </div>
          <div class="actions">
            <el-button type="success" :icon="Check" @click="handleReview(item, 'pass')">通过</el-button>
            <el-button type="danger" :icon="Close" @click="handleReview(item, 'reject')">驳回</el-button>
            <el-button type="primary" :icon="MagicStick" @click="handleAiReview(item)" :loading="item.aiLoading">AI审查</el-button>
          </div>
        </div>
      </div>

      <el-empty v-if="filteredList.length === 0" description="暂无待审核事件" />
    </div>

    <!-- AI 审查结果弹窗 -->
    <el-dialog v-model="aiDialogVisible" title="AI 风险评估报告" width="600px" destroy-on-close>
      <div v-if="aiLoading" class="ai-loading">
        <el-icon class="is-loading" :size="40" color="#409eff"><Loading /></el-icon>
        <p>AI 正在分析灾情数据，请稍候...</p>
      </div>
      <div v-else-if="aiResult" class="ai-result">
        <el-descriptions :column="1" border>
          <el-descriptions-item v-if="aiResult.confidence" label="置信度">{{ aiResult.confidence }}%</el-descriptions-item>
          <el-descriptions-item label="评估结论">
            <div class="conclusion-text" v-html="formatConclusion(aiResult.conclusion)"></div>
          </el-descriptions-item>
          <el-descriptions-item v-if="aiResult.trend" label="趋势预测">{{ aiResult.trend }}</el-descriptions-item>
          <el-descriptions-item v-if="aiResult.suggestions.length > 0" label="建议措施">
            <div class="suggestions">
              <p v-for="(s, i) in aiResult.suggestions" :key="i">• {{ s }}</p>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="AI 来源">
            <el-tag v-if="aiResult.fallbackLevel === 'none'" type="success" size="small">Dify 工作流</el-tag>
            <el-tag v-else-if="aiResult.fallbackLevel === 'llm'" type="warning" size="small">LLM 降级</el-tag>
            <el-tag v-else type="info" size="small">规则引擎兜底</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="aiResult.raw" style="margin-top: 12px; text-align: right;">
          <el-button type="primary" link size="small" @click="showRawJson = !showRawJson">
            {{ showRawJson ? '隐藏' : '查看' }} Dify 返回值
          </el-button>
        </div>
        <div v-if="showRawJson && aiResult.raw" class="ai-raw" style="margin-top: 8px;">
          <pre>{{ JSON.stringify(aiResult.raw, null, 2) }}</pre>
        </div>
      </div>
      <div v-else class="ai-error">
        <el-icon :size="40" color="#f56c6c"><WarningFilled /></el-icon>
        <p>AI 审查失败，请稍后重试</p>
      </div>
      <template #footer>
        <el-button @click="aiDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReviewList, reviewEvent, riskAssessSync } from '@/api'
import { DISASTER_TYPES, getDisasterColor } from '@/utils/constants'
import {
  CircleCheck, Search, Refresh, User, Location, Clock,
  Check, Close, MagicStick, Loading, WarningFilled
} from '@element-plus/icons-vue'

const searchKeyword = ref('')
const filterType = ref('')
const reviewList = ref([])
const pendingCount = ref(0)
const disasterTypes = DISASTER_TYPES

// AI 审查相关
const aiDialogVisible = ref(false)
const aiLoading = ref(false)
const aiResult = ref(null)
const showRawJson = ref(false)

const filteredList = computed(() => {
  return reviewList.value.filter(item => {
    const matchKeyword = !searchKeyword.value ||
      item.title.includes(searchKeyword.value) ||
      item.address.includes(searchKeyword.value)
    const matchType = !filterType.value || item.type === filterType.value
    return matchKeyword && matchType
  })
})

function riskTagType(level) {
  const map = { '低': 'success', '中': 'warning', '高': 'danger', '极高': 'danger' }
  return map[level] || 'info'
}

function formatConclusion(text) {
  if (!text) return '-'
  let cleaned = text
  // 去掉 Dify 返回的 JSON 块（从 {"智能体名称" 开始，兼容各种空白/换行格式）
  // 匹配 { 后跟任意空白（含 \n \r\n 空格）再跟 "智能体名称"
  const jsonMatch = cleaned.match(/\{\s*"智能体名称"/)
  if (jsonMatch) {
    cleaned = cleaned.substring(0, jsonMatch.index)
  }
  // 去掉末尾的追问（如"是否需要进一步排查..."）
  cleaned = cleaned.replace(/\s*是否需要进一步排查[^\n]*\n?$/g, '')
  // 去掉末尾多余的换行和空白
  cleaned = cleaned.trim()
  // 将 Markdown 风格的文本转为简单 HTML
  return cleaned
    .replace(/### (.+)/g, '<h4>$1</h4>')
    .replace(/## (.+)/g, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

/**
 * 从字符串中提取 JSON 块
 * Dify 返回格式：Markdown 文本 + {"智能体名称": ...}
 * 从前往后扫描所有 {，逐个提取并验证，返回第一个包含 "智能体名称" 的有效 JSON
 */
function extractJsonBlock(text) {
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '{') {
      const jsonStr = extractBalancedBraces(text, i)
      if (jsonStr) {
        // 清理尾逗号（Dify 返回的 JSON 可能有 trailing comma）
        const cleaned = jsonStr.replace(/,(\s*[}\]])/g, '$1')
        try {
          const parsed = JSON.parse(cleaned)
          if (parsed['智能体名称'] || parsed.智能体名称) {
            return cleaned
          }
        } catch (e) {
          // 不是有效 JSON，继续找下一个 {
        }
      }
    }
  }
  return null
}

/**
 * 从 start 位置开始，用花括号计数法提取平衡的 JSON 块
 */
function extractBalancedBraces(text, start) {
  let depth = 0
  let inString = false
  let escape = false
  for (let i = start; i < text.length; i++) {
    const ch = text[i]
    if (escape) {
      escape = false
      continue
    }
    if (ch === '\\') {
      escape = true
      continue
    }
    if (ch === '"') {
      inString = !inString
      continue
    }
    if (inString) continue
    if (ch === '{') depth++
    if (ch === '}') {
      depth--
      if (depth === 0) {
        return text.substring(start, i + 1)
      }
    }
  }
  return null
}

async function loadData() {
  try {
    const res = await getReviewList({ status: 'pending', pageSize: 100 })
    if (res.code === 200 && res.data) {
      const list = res.data.records || res.data.list || []
      reviewList.value = list.map(item => ({
        id: item.id,
        title: item.title || '未命名',
        type: item.disasterType || '未知',
        level: item.riskLevel || '中',
        reporter: item.reporterName || '未知',
        address: item.locationName || item.address || '未知位置',
        time: item.createdAt ? item.createdAt.substring(0, 16) : '',
        description: item.description || '暂无描述',
        assessLevel: 3,
        status: item.status,
        aiLoading: false
      }))
      pendingCount.value = res.data.total || list.length
    }
  } catch (e) {
    console.error('加载审核列表失败:', e)
  }
}

async function handleReview(item, action) {
  const actionText = action === 'pass' ? '通过' : '驳回'
  try {
    await ElMessageBox.confirm(
      `确定${actionText}该灾情事件的审核吗？`,
      '审核确认',
      { confirmButtonText: `确认${actionText}`, cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  const status = action === 'pass' ? 'approved' : 'rejected'
  const res = await reviewEvent(item.id, status, '')
  if (res.code === 200) {
    ElMessage.success(`已${actionText}`)
    // 重新加载数据，确保界面与后端同步
    await loadData()
  } else {
    ElMessage.error(res.message || `${actionText}失败`)
  }
}

async function handleAiReview(item) {
  item.aiLoading = true
  aiDialogVisible.value = true
  aiLoading.value = true
  aiResult.value = null
  showRawJson.value = false

  try {
    const res = await riskAssessSync({
      title: item.title,
      disaster_type: item.type,
      risk_level: item.level,
      location_name: item.address,
      description: item.description,
      occurred_at: item.time,
    })
    if (res.code === 200 && res.data) {
      const d = res.data
      const rawResult = d.result || ''

      // result 可能是字符串（Markdown + 内嵌 JSON）或对象
      let structured = {}
      let conclusionText = ''

      if (typeof rawResult === 'string') {
        conclusionText = rawResult
        const jsonStr = extractJsonBlock(rawResult)
        if (jsonStr) {
          try {
            const parsed = JSON.parse(jsonStr)
            const output = parsed.输出 || parsed.output || parsed
            structured = {
              riskLevel: output.风险等级 || output.risk_level || '中',
              riskScore: output.综合风险评分 ?? output.risk_score ?? null,
              suggestions: (output.Top风险项 || output.top_risks || []).map(r =>
                `${r.风险描述 || r.risk_desc || ''}：${r.建议措施 || r.suggestion || ''}`
              ),
              trend: output.趋势预测 || output.trend || '',
              confidence: output.置信度 ?? output.confidence ?? null,
            }
          } catch (e) {
            console.warn('JSON 解析失败:', e)
          }
        }
      } else if (typeof rawResult === 'object') {
        structured = rawResult
        conclusionText = rawResult.conclusion || rawResult.summary || ''
      }

      aiResult.value = {
        riskLevel: structured.riskLevel || '中',
        riskScore: structured.riskScore != null ? structured.riskScore : null,
        conclusion: conclusionText || structured.conclusion || '',
        suggestions: structured.suggestions || [],
        trend: structured.trend || '',
        confidence: structured.confidence || '',
        fallbackLevel: d.fallback_level || 'none',
        raw: d,
      }
    } else {
      aiResult.value = null
    }
  } catch (e) {
    console.error('AI审查失败:', e)
    aiResult.value = null
  } finally {
    aiLoading.value = false
    item.aiLoading = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.review-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
  flex-wrap: wrap;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.type-tag {
  font-weight: 500;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.card-body {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 10px;

  span {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.description {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  padding: 10px 14px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #e5e7eb;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 12px;
}

.risk-assess {
  display: flex;
  align-items: center;
  gap: 10px;
}

.assess-label {
  font-size: 13px;
  color: #6b7280;
}

.actions {
  display: flex;
  gap: 8px;
}

.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 16px;

  p {
    font-size: 14px;
    color: #6b7280;
  }
}

.ai-result {
  .suggestions {
    p {
      margin: 4px 0;
      font-size: 13px;
      color: #374151;
    }
  }

  .ai-raw {
    margin-top: 16px;
    details {
      summary {
        cursor: pointer;
        font-size: 12px;
        color: #9ca3af;
      }
      pre {
        margin-top: 8px;
        padding: 12px;
        background: #f3f4f6;
        border-radius: 6px;
        font-size: 12px;
        max-height: 300px;
        overflow: auto;
      }
    }
  }
}

.ai-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 16px;

  p {
    font-size: 14px;
    color: #f56c6c;
  }
}

@media (max-width: 768px) {
  .review-card {
    padding: 14px;
  }

  .info-row {
    gap: 10px;
    font-size: 12px;
  }

  .card-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .actions {
    justify-content: flex-end;
  }
}
</style>
