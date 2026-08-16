import request from '@/utils/request'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

// 懒加载 mock：仅在 useMock=true 时动态 import，避免假数据/敏感信息打包进生产 bundle
let _mock = null
if (useMock) {
  // Vite 支持顶层 await，但为兼容性用立即执行 async
  import('@/mock').then(mod => { _mock = mod.default || mod }).catch(() => {})
}
/** 同步获取 mock 模块（仅 useMock=true 时有值） */
function mock() { return _mock }

// ===== 认证相关 =====
export function login(data) {
  if (useMock && mock()) return Promise.resolve(mock().auth.login(data))
  return request({ url: '/auth/login', method: 'post', data })
}

export function getUserInfo() {
  if (useMock && mock()) return Promise.resolve(mock().auth.getUserInfo())
  return request({ url: '/auth/info', method: 'get' })
}

export function logout() {
  if (useMock && mock()) return Promise.resolve(mock().auth.logout())
  return request({ url: '/auth/logout', method: 'post' })
}

// ===== 灾情态势大屏 =====
export function getDashboardStats() {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getStats())
  return request({ url: '/incidents/dashboard/stats', method: 'get' })
}

export function getDisasterList(params) {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getDisasterList(params))
  return request({ url: '/incidents/page', method: 'get', params })
}

export function getRealtimeIncidents(limit = 10) {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getDisasterList({ pageSize: limit }))
  return request({ url: '/incidents/realtime', method: 'get', params: { limit } })
}

export function getDisasterTypeDistribution() {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getTypeDistribution())
  return request({ url: '/incidents/dashboard/stats', method: 'get' }).then(res => {
    if (res.code === 200 && res.data?.typeStats) {
      const typeColors = {
        '地震': '#f5222d', '山洪': '#1890ff', '洪涝': '#13c2c2',
        '崩塌': '#fa8c16', '泥石流': '#722ed1', '滑坡': '#faad14', '暴雨': '#52c41a'
      }
      const data = Object.entries(res.data.typeStats).map(([name, value]) => ({
        name, value, color: typeColors[name] || '#1890ff'
      }))
      return { code: 200, data, success: true }
    }
    return res
  })
}

export function getCityDisasterCount() {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getCityCount())
  // 严格使用后端 SQL 数据，前端不再生成任何随机数
  return request({ url: '/incidents/dashboard/city-count', method: 'get' })
}

export function getWeeklyTrend() {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getWeeklyTrend())
  // 严格使用后端 SQL 数据（按 occurred_at 日期聚合近 7 天）
  return request({ url: '/incidents/dashboard/weekly-trend', method: 'get' })
}

export function getMapMarkers() {
  if (useMock && mock()) return Promise.resolve(mock().dashboard.getMapMarkers())
  return request({ url: '/incidents/dashboard/stats', method: 'get' }).then(res => {
    if (res.code === 200 && res.data?.activeIncidents) {
      const markers = res.data.activeIncidents
        .map(inc => ({
          id: inc.id,
          name: inc.title,
          lng: parseFloat(inc.lng),
          lat: parseFloat(inc.lat),
          level: inc.riskLevel,
          type: inc.disasterType,
          status: inc.status
        }))
        .filter(m => !isNaN(m.lng) && !isNaN(m.lat))
      return { code: 200, data: markers, success: true }
    }
    return res
  })
}

// ===== 灾情上报 =====
export function reportDisaster(data) {
  if (useMock && mock()) return Promise.resolve(mock().reporter.report(data))
  return request({ url: '/reports', method: 'post', data })
}

export function getMyReports(params) {
  if (useMock && mock()) return Promise.resolve(mock().reporter.getMyReports(params))
  return request({ url: '/reports/my', method: 'get', params })
}

export function uploadImage(formData) {
  if (useMock && mock()) return Promise.resolve(mock().reporter.uploadImage())
  return request({
    url: '/upload/image',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ===== 审核事件 =====
export function getReviewList(params) {
  if (useMock && mock()) return Promise.resolve(mock().commander.getReviewList(params))
  return request({ url: '/reports/page', method: 'get', params })
}

export function getReportDetail(id) {
  if (useMock && mock()) return Promise.resolve(mock().commander.getReviewDetail(id))
  return request({ url: `/reports/${id}`, method: 'get' })
}

export function reviewEvent(id, status, comment) {
  if (useMock && mock()) return Promise.resolve(mock().commander.reviewEvent({ id, status, comment }))
  return request({ url: `/reports/${id}/review`, method: 'post', params: { status, comment } })
}

// ===== 应急方案 =====
export function listIncidents() {
  return request({ url: '/plans/incidents', method: 'get' })
}

export function generatePlan(data) {
  if (useMock && mock()) return Promise.resolve(mock().commander.generatePlan(data))
  return request({ url: '/plans/generate', method: 'post', data })
}

export function getPlanList(params) {
  if (useMock && mock()) return Promise.resolve(mock().commander.getPlanList(params))
  return request({ url: '/plans/page', method: 'get', params })
}

export function getPlanDetail(id) {
  if (useMock && mock()) return Promise.resolve(mock().commander.getPlanDetail(id))
  return request({ url: `/plans/${id}`, method: 'get' })
}

export function savePlan(data) {
  if (useMock && mock()) return Promise.resolve(mock().commander.savePlan(data))
  if (data.id) {
    return request({ url: `/plans/${data.id}`, method: 'put', data })
  }
  return request({ url: '/plans', method: 'post', data })
}

export function submitPlan(id) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/plans/${id}/submit`, method: 'post' })
}

export function approvePlan(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/plans/${id}/approve`, method: 'post', params: { status } })
}

// ===== 调度看板（Neo4j图谱） =====
export function getDispatchGraph() {
  if (useMock && mock()) return Promise.resolve(mock().commander.getDispatchGraph())
  // 严格使用后端 Neo4j 图谱接口，不再回退 mock 数据
  return request({ url: '/neo4j/dispatch-graph', method: 'get' })
}

// ===== 交互式图谱浏览（Neo4j Browser 风格） =====
export function getNeo4jLabels() {
  return request({ url: '/neo4j/labels', method: 'get' })
}

export function getNeo4jRelationshipTypes() {
  return request({ url: '/neo4j/relationship-types', method: 'get' })
}

export function getNodesByLabel(label, limit = 25) {
  return request({ url: '/neo4j/nodes-by-label', method: 'get', params: { label, limit } })
}

export function expandNodeNeighbors(nodeId) {
  return request({ url: `/neo4j/expand/${nodeId}`, method: 'get' })
}

export function collapseNode(nodeId) {
  return request({ url: `/neo4j/collapse/${nodeId}`, method: 'get' })
}

export function getNodeByInternalId(nodeId) {
  return request({ url: `/neo4j/node/${nodeId}`, method: 'get' })
}

export function clearNeo4j() {
  return request({ url: '/neo4j/clear', method: 'delete' })
}

export function reSyncNeo4j() {
  return request({ url: '/neo4j/resync', method: 'post' })
}

// ===== 救援资源查询 =====
export function getResourceList(params) {
  if (useMock && mock()) return Promise.resolve(mock().resource.getList(params))
  return request({ url: '/resources/page', method: 'get', params })
}

export function getResourceAll(params) {
  if (useMock && mock()) return Promise.resolve(mock().resource.getList(params))
  return request({ url: '/resources/list', method: 'get', params })
}

export function getResourceDetail(id) {
  if (useMock && mock()) return Promise.resolve(mock().resource.getDetail(id))
  return request({ url: `/resources/${id}`, method: 'get' })
}

export function addResource(data) {
  if (useMock && mock()) return Promise.resolve(mock().resource.add(data))
  return request({ url: '/resources', method: 'post', data })
}

export function updateResource(id, data) {
  if (useMock && mock()) return Promise.resolve(mock().resource.update(id, data))
  return request({ url: `/resources/${id}`, method: 'put', data })
}

export function deleteResource(id) {
  if (useMock && mock()) return Promise.resolve(mock().resource.remove(id))
  return request({ url: `/resources/${id}`, method: 'delete' })
}

export function getResourceStats() {
  if (useMock && mock()) return Promise.resolve(mock().resource.getStats())
  return request({ url: '/resources/stats/category', method: 'get' })
}

export function saveGraphJson(data) {
  if (useMock && mock()) return Promise.resolve({ code: 200, success: true, data })
  return request({ url: '/resources/graph-json', method: 'post', data })
}

// ===== 调度指令 =====
export function getDispatchOrders(params) {
  if (useMock && mock()) return Promise.resolve(mock().commander.getDispatchOrders(params))
  return request({ url: '/dispatch-orders/page', method: 'get', params })
}

export function createDispatchOrder(data) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data })
  return request({ url: '/dispatch-orders', method: 'post', data })
}

export function updateDispatchOrder(id, data) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/dispatch-orders/${id}`, method: 'put', data })
}

export function updateDispatchStatus(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/dispatch-orders/${id}/status`, method: 'put', params: { status } })
}

// ===== 知识库管理 =====
export function getKnowledgeList(params) {
  if (useMock && mock()) return Promise.resolve(mock().admin.getKnowledgeList(params))
  return request({ url: '/admin/knowledge-bases/page', method: 'get', params })
}

export function getKnowledgeAll() {
  if (useMock && mock()) return Promise.resolve(mock().admin.getKnowledgeList({ pageSize: 100 }))
  return request({ url: '/admin/knowledge-bases/list', method: 'get' })
}

export function addKnowledge(data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.addKnowledge(data))
  return request({ url: '/admin/knowledge-bases', method: 'post', data })
}

export function updateKnowledge(id, data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.updateKnowledge(id, data))
  return request({ url: `/admin/knowledge-bases/${id}`, method: 'put', data })
}

export function deleteKnowledge(id) {
  if (useMock && mock()) return Promise.resolve(mock().admin.deleteKnowledge(id))
  return request({ url: `/admin/knowledge-bases/${id}`, method: 'delete' })
}

export function toggleKnowledgeStatus(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/knowledge-bases/${id}/status`, method: 'put', params: { status } })
}

export function uploadKnowledgeDoc(kbId, formData) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({
    url: `/admin/knowledge-bases/${kbId}/documents`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getKnowledgeDocuments(kbId) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: [] })
  return request({ url: `/admin/knowledge-bases/${kbId}/documents`, method: 'get' })
}

export function deleteKnowledgeDocument(docId) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/knowledge-bases/documents/${docId}`, method: 'delete' })
}

// ===== 用户管理 =====
export function getUserList(params) {
  if (useMock && mock()) return Promise.resolve(mock().admin.getUserList(params))
  return request({ url: '/admin/users/page', method: 'get', params })
}

export function addUser(data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.addUser(data))
  return request({ url: '/admin/users', method: 'post', data })
}

export function updateUser(id, data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.updateUser(id, data))
  return request({ url: `/admin/users/${id}`, method: 'put', data })
}

export function deleteUser(id) {
  if (useMock && mock()) return Promise.resolve(mock().admin.deleteUser(id))
  return request({ url: `/admin/users/${id}`, method: 'delete' })
}

export function toggleUserStatus(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/users/${id}/status`, method: 'put', params: { status } })
}

export function resetUserPassword(id) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/users/${id}/reset-password`, method: 'put' })
}

// ===== 角色管理 =====
export function getRoleList(params) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: [] })
  return request({ url: '/admin/roles/list', method: 'get', params })
}

export function getRoleStats() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/admin/roles/stats', method: 'get' })
}

export function toggleRoleStatus(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/roles/${id}/status`, method: 'put', params: { status } })
}

// ===== 模型管理 =====
export function getModelList(params) {
  if (useMock && mock()) return Promise.resolve(mock().admin.getModelList(params))
  return request({ url: '/admin/models/page', method: 'get', params })
}

export function getActiveModel() {
  if (useMock && mock()) return Promise.resolve(mock().admin.getActiveModel())
  return request({ url: '/admin/models/active', method: 'get' })
}

export function addModel(data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.addModel(data))
  return request({ url: '/admin/models', method: 'post', data })
}

export function updateModel(id, data) {
  if (useMock && mock()) return Promise.resolve(mock().admin.updateModel(id, data))
  return request({ url: `/admin/models/${id}`, method: 'put', data })
}

export function deleteModel(id) {
  if (useMock && mock()) return Promise.resolve(mock().admin.deleteModel(id))
  return request({ url: `/admin/models/${id}`, method: 'delete' })
}

export function switchModel(id) {
  if (useMock && mock()) return Promise.resolve(mock().admin.switchModel(id))
  return request({ url: `/admin/models/${id}/activate`, method: 'put' })
}

export function toggleModelStatus(id, status) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/admin/models/${id}/status`, method: 'put', params: { status } })
}

// ===== 审计日志 =====
export function getAuditLogs(params) {
  if (useMock && mock()) return Promise.resolve(mock().admin.getAuditLogs(params))
  return request({ url: '/admin/audit-logs/page', method: 'get', params })
}

// ===== 数据源管理 =====
export function getDataSourceList(params) {
  if (useMock && mock()) return Promise.resolve(mock().admin.getDataSources(params))
  return request({ url: '/admin/data-sources/page', method: 'get', params })
}

// ===== 天气查询（爬虫代理） =====
export function getWeatherCities() {
  if (useMock && mock()?.weather) return Promise.resolve(mock().weather.getCities())
  return request({ url: '/weather/cities', method: 'get' })
}

export function getWeatherDistricts(cityName) {
  if (useMock && mock()?.weather) return Promise.resolve(mock().weather.getDistricts(cityName))
  return request({ url: `/weather/districts/${cityName}`, method: 'get' })
}

export function getWeatherForecast(params) {
  if (useMock && mock()?.weather) return Promise.resolve(mock().weather.getForecast(params))
  return request({ url: '/weather/forecast', method: 'get', params })
}

export function getWeatherBySlug(slug) {
  if (useMock && mock()?.weather) return Promise.resolve(mock().weather.getBySlug(slug))
  return request({ url: `/weather/forecast/${slug}`, method: 'get' })
}

// ===== 灾情工单状态机 =====
export function getIncidentTransitions(id) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { currentStatus: '处置中', allowedNext: ['已结束'] } })
  return request({ url: `/incidents/${id}/transitions`, method: 'get' })
}

export function transitionIncident(id, targetStatus, reason) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: `/incidents/${id}/transition`, method: 'put', params: { targetStatus, reason } })
}

// ===== 资源锁定管理 =====
export function checkResourceConflict(resourceId, requiredQty) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { conflict: false } })
  return request({ url: '/resource-locks/conflict-check', method: 'get', params: { resourceId, requiredQty } })
}

export function lockResource(data) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { lockNo: 'LK-mock' } })
  return request({ url: '/resource-locks', method: 'post', data })
}

export function releaseResourceLock(lockId) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/resource-locks/${lockId}`, method: 'delete' })
}

export function releaseLocksByIncident(incidentId) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { released: 1 } })
  return request({ url: `/resource-locks/by-incident/${incidentId}`, method: 'delete' })
}

export function getResourceLocks(params) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: [] })
  return request({ url: '/resource-locks', method: 'get', params })
}

export function cleanupExpiredLocks() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { cleaned: 0 } })
  return request({ url: '/resource-locks/cleanup-expired', method: 'post' })
}

// ===== AI Agent（事件抽取/预案检索/方案审查） =====
export function extractIncident(text) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { taskId: 'mock-task' } })
  return request({ url: '/ai/agent/extract-incident', method: 'post', data: { text } })
}

export function retrievePlans(query, topK) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { taskId: 'mock-task' } })
  return request({ url: '/ai/agent/retrieve-plans', method: 'post', data: { query, top_k: topK } })
}

export function reviewPlan(planContent, incidentId) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { taskId: 'mock-task' } })
  return request({ url: '/ai/agent/review-plan', method: 'post', data: { plan_content: planContent, incident_id: incidentId } })
}

export function extractIncidentSync(text) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/ai/agent/extract-incident/sync', method: 'post', data: { text } })
}

export function retrievePlansSync(query, topK) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/ai/agent/retrieve-plans/sync', method: 'post', data: { query, top_k: topK } })
}

export function reviewPlanSync(planContent, incidentId) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/ai/agent/review-plan/sync', method: 'post', data: { plan_content: planContent, incident_id: incidentId } })
}

export function riskAssessSync(incidentInfo) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/ai/agent/risk-assess/sync', method: 'post', data: incidentInfo })
}

// ===== 定时任务管理 =====
export function getSchedulerTasks() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { tasks: [] } })
  return request({ url: '/scheduler/tasks', method: 'get' })
}

export function triggerWeatherCollection() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { status: 'triggered' } })
  return request({ url: '/scheduler/trigger/weather', method: 'post' })
}

export function triggerWarningCollection() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { status: 'triggered' } })
  return request({ url: '/scheduler/trigger/warnings', method: 'post' })
}

// ===== SSE / WebSocket 实时推送 =====
/**
 * 创建 SSE 订阅 AI 生成进度
 * @param {string} taskId 任务ID
 * @param {function} onProgress 进度回调
 * @param {function} onError 错误回调
 * @returns EventSource 实例
 */
export function subscribeAiProgress(taskId, onProgress, onError) {
  const token = localStorage.getItem('token') || ''
  const url = `/api/sse/progress/${taskId}?token=${encodeURIComponent(token)}`
  const eventSource = new EventSource(url)
  eventSource.addEventListener('progress', (e) => {
    try {
      const data = JSON.parse(e.data)
      onProgress && onProgress(data)
      if (data.stage === 'completed' || data.stage === 'error') {
        eventSource.close()
      }
    } catch (err) {
      console.error('SSE 解析失败:', err)
    }
  })
  eventSource.onerror = (e) => {
    onError && onError(e)
    eventSource.close()
  }
  return eventSource
}

/**
 * 创建 WebSocket 连接订阅事件状态
 * @param {function} onMessage 消息回调
 * @param {function} onOpen 连接成功回调
 * @returns WebSocket 实例
 */
export function connectEventSocket(onMessage, onOpen) {
  const token = localStorage.getItem('token') || ''
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/api/ws/events?token=${encodeURIComponent(token)}`
  const ws = new WebSocket(url)
  ws.onopen = () => onOpen && onOpen()
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage && onMessage(data)
    } catch (err) {
      console.error('WS 解析失败:', err)
    }
  }
  return ws
}

export function getSseStatus() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { activeEmitters: 0 } })
  return request({ url: '/sse/status', method: 'get' })
}

// ===== 灾情态势聚合表（disaster_situation） =====
export function getDisasterSituation() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/disaster-situation', method: 'get' })
}

export function refreshDisasterSituation() {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: '/disaster-situation/refresh', method: 'post' })
}

// ===== 系统综合信息（info 表） =====
export function getInfo() {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: {} })
  return request({ url: '/info', method: 'get' })
}

export function updateInfo(data) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: '/info', method: 'put', data })
}

// ===== 实时事件流归档 =====
export function getArchiveFiles(params) {
  if (useMock) return Promise.resolve({ code: 200, success: true, data: { records: [] } })
  return request({ url: '/archive-files/page', method: 'get', params })
}

export function createArchiveFile(data) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: '/archive-files', method: 'post', data })
}

export function deleteArchiveFile(id) {
  if (useMock) return Promise.resolve({ code: 200, success: true })
  return request({ url: `/archive-files/${id}`, method: 'delete' })
}
