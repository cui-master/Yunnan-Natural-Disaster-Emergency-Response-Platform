// ============================================================
// 前端 Mock 联调层（前后端分离核心）
// 作用：VITE_USE_MOCK=true 时，前端完全独立运行，无需后端。
// 路由严格镜像真实后端路径：/api/auth/login、/api/reports、/api/incidents、/api/dispatch、
// /api/resources、/api/plans、/api/knowledge、/api/audit/logs、/api/system/*、/api/upload。
// 真实联调时把 .env 的 VITE_USE_MOCK 改为 false，前端即通过 Vite proxy 走真实后端。
// ============================================================
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'

export const USE_MOCK = (import.meta.env.VITE_USE_MOCK || 'true') === 'true'

const ok = (data: unknown) => ({ code: 0, message: 'ok', data })
const fail = (message: string, code = 1) => ({ code, message, data: null })
const now = () => new Date().toISOString()
const uid = (() => {
  let n = 1000
  return () => ++n
})()

function parseBody(config: InternalAxiosRequestConfig): any {
  const d = config.data
  if (!d) return {}
  if (typeof d === 'string') {
    try {
      return JSON.parse(d)
    } catch {
      return {}
    }
  }
  return d
}

const YN_CITIES: Record<string, { lat: number; lng: number }> = {
  昆明市: { lat: 25.04, lng: 102.71 }, 曲靖市: { lat: 25.49, lng: 103.83 }, 玉溪市: { lat: 24.35, lng: 102.54 },
  保山市: { lat: 25.11, lng: 99.16 }, 昭通市: { lat: 27.34, lng: 103.71 }, 丽江市: { lat: 26.87, lng: 100.23 },
  普洱市: { lat: 24.06, lng: 100.97 }, 临沧市: { lat: 23.88, lng: 100.1 }, 楚雄州: { lat: 25.04, lng: 101.54 },
  红河州: { lat: 23.37, lng: 103.37 }, 文山州: { lat: 23.37, lng: 104.24 }, 西双版纳州: { lat: 22.0, lng: 100.79 },
  大理州: { lat: 25.61, lng: 100.27 }, 德宏州: { lat: 24.43, lng: 98.58 }, 怒江州: { lat: 25.85, lng: 98.85 },
  迪庆州: { lat: 27.83, lng: 99.71 }
}
const typeLabel: Record<string, string> = {
  EARTHQUAKE: '地震', FLOOD: '洪涝', LANDSLIDE: '滑坡', DEBRIS_FLOW: '泥石流',
  DROUGHT: '干旱', FOREST_FIRE: '森林火灾', HAIL: '冰雹', TYPHOON: '台风'
}

// 角色键与后端 Authz.require 对齐（ROLE_ 前缀）
const ROLES = [
  { code: 'ROLE_REPORTER', name: '信息员', description: '灾情上报与核实', permissions: ['disaster:report', 'disaster:view'] },
  { code: 'ROLE_COMMANDER', name: '指挥人员', description: '审核、方案、调度指挥', permissions: ['disaster:review', 'plan:generate', 'plan:edit', 'dispatch:manage', 'disaster:view'] },
  { code: 'ROLE_RESMGR', name: '资源管理员', description: '救援资源与调度管理', permissions: ['resource:manage', 'dispatch:manage', 'disaster:view'] },
  { code: 'ROLE_ADMIN', name: '系统管理员', description: '用户、角色、系统配置、审计', permissions: ['*'] }
]
const USERS = [
  { id: 1, username: 'reporter', password: '123456', realName: '李上报', roleKey: 'ROLE_REPORTER', roleName: '信息员' },
  { id: 2, username: 'commander', password: '123456', realName: '王指挥', roleKey: 'ROLE_COMMANDER', roleName: '指挥人员' },
  { id: 3, username: 'resmanager', password: '123456', realName: '赵资源', roleKey: 'ROLE_RESMGR', roleName: '资源管理员' },
  { id: 4, username: 'admin', password: '123456', realName: '孙管理员', roleKey: 'ROLE_ADMIN', roleName: '系统管理员' }
]

// 状态枚举与后端 IncidentStatus 对齐
const DISASTERS: any[] = [
  mkEvent('昆明市', '五华区', 'EARTHQUAKE', 'III', 'PENDING_VERIFY', '昆明主城轻微震感，部分老旧房屋出现裂缝', 12000, 3.2, 0, ['https://picsum.photos/seed/yn1/400/300']),
  mkEvent('大理州', '漾濞县', 'EARTHQUAKE', 'II', 'IN_PROGRESS', '漾濞5.1级地震，道路中断，需救援队伍', 35000, 12.5, 4, ['https://picsum.photos/seed/yn2/400/300']),
  mkEvent('昭通市', '鲁甸县', 'LANDSLIDE', 'III', 'CONFIRMED', '持续降雨诱发山体滑坡，阻断省道', 8000, 5.1, 1, ['https://picsum.photos/seed/yn3/400/300']),
  mkEvent('红河州', '元阳县', 'DEBRIS_FLOW', 'III', 'IN_PROGRESS', '暴雨引发泥石流，下游村寨受威胁', 15000, 8.0, 2, ['https://picsum.photos/seed/yn4/400/300']),
  mkEvent('丽江市', '玉龙县', 'FOREST_FIRE', 'II', 'CONFIRMED', '森林火情蔓延，需直升机支援', 0, 6.4, 0, ['https://picsum.photos/seed/yn5/400/300']),
  mkEvent('曲靖市', '宣威市', 'FLOOD', 'IV', 'CLOSED', '城市内涝已基本消退', 5000, 2.1, 0, []),
  mkEvent('保山市', '隆阳区', 'DROUGHT', 'III', 'IN_PROGRESS', '夏旱持续，多个乡镇饮水困难', 42000, 0, 0, []),
  mkEvent('普洱市', '思茅区', 'HAIL', 'IV', 'PENDING_VERIFY', '冰雹致部分农田受损，待核实', 3000, 1.0, 0, ['https://picsum.photos/seed/yn6/400/300']),
  mkEvent('楚雄州', '双柏县', 'EARTHQUAKE', 'IV', 'CONFIRMED', '4.0级地震，暂无人员伤亡报告', 2000, 0.5, 0, []),
  mkEvent('文山州', '砚山县', 'FLOOD', 'III', 'IN_PROGRESS', '河道水位超警戒，需转移低洼区群众', 18000, 4.3, 0, ['https://picsum.photos/seed/yn7/400/300']),
  mkEvent('迪庆州', '香格里拉市', 'LANDSLIDE', 'II', 'IN_PROGRESS', '高山滑坡阻断进藏通道', 6000, 3.0, 1, ['https://picsum.photos/seed/yn8/400/300']),
  mkEvent('西双版纳州', '勐海县', 'FOREST_FIRE', 'III', 'PENDING_VERIFY', '边境附近森林火情待核实', 0, 2.2, 0, []),
  mkEvent('临沧市', '凤庆县', 'DEBRIS_FLOW', 'IV', 'CONFIRMED', '强降雨后泥石流风险较高', 4000, 1.5, 0, []),
  mkEvent('怒江州', '福贡县', 'LANDSLIDE', 'II', 'IN_PROGRESS', '峡谷区滑坡威胁公路与村庄', 9000, 4.0, 2, ['https://picsum.photos/seed/yn9/400/300'])
]

const RESOURCES: any[] = [
  mkResource('云南省地震灾害紧急救援队', 'TEAM', 'IDLE', 200, '省应急管理厅'),
  mkResource('昆明市消防救援支队', 'TEAM', 'DISPATCHED', 150, '市消防'),
  mkResource('大理州矿山救援队', 'TEAM', 'IDLE', 80, '州应急'),
  mkResource('大型起重机编组', 'EQUIPMENT', 'IDLE', 12, '省救援装备中心'),
  mkResource('应急医疗队(创伤)', 'MEDICAL', 'LOCKED', 30, '省卫健委'),
  mkResource('物资保障车(帐篷/被服)', 'VEHICLE', 'IDLE', 20, '省粮食物资'),
  mkResource('卫星通信设备车', 'VEHICLE', 'MAINTENANCE', 4, '省通信管理局'),
  mkResource('临时安置点-昭通体育馆', 'SHELTER', 'IDLE', 3000, '市民政'),
  mkResource('无人机侦察中队', 'EQUIPMENT', 'IDLE', 8, '省应急管理厅'),
  mkResource('森林防火直升机', 'EQUIPMENT', 'DISPATCHED', 2, '省林草局')
]

const DISPATCHES: any[] = []
const KNOWLEDGE: any[] = [
  mkDoc('云南省地震应急预案（2024版）', 'EMERGENCY_PLAN', ['地震', '预案'], ['EARTHQUAKE'], 18, '省应急厅'),
  mkDoc('滑坡泥石流灾害处置技术规范', 'DISASTER_SPEC', ['滑坡', '泥石流'], ['LANDSLIDE', 'DEBRIS_FLOW'], 12, '自然资源厅'),
  mkDoc('森林防火条例实施细则', 'LAW', ['森林', '防火'], ['FOREST_FIRE'], 9, '省林草局'),
  mkDoc('2022年泸定地震处置案例', 'CASE', ['地震', '案例'], ['EARTHQUAKE'], 7, '应急研究院'),
  mkDoc('城市内涝应急响应指南', 'GUIDE', ['内涝', '城市'], ['FLOOD'], 6, '住建厅'),
  mkDoc('干旱灾害救助操作规程', 'DISASTER_SPEC', ['干旱'], ['DROUGHT'], 5, '省应急厅')
]
const AUDITS: any[] = []
USERS.forEach((u, i) => {
  AUDITS.push({
    id: i + 1, operator: u.realName, role: u.roleKey, action: i % 2 ? '审核灾情工单' : '登录系统',
    module: i % 2 ? '灾情管理' : '认证', target: i % 2 ? 'YN-20260722-00' + (i + 1) : '登录',
    ip: '10.20.30.' + (i + 1), result: 'SUCCESS', detail: '', createdAt: now()
  })
})

const PLANS: any[] = []

// 当前登录用户（供 /api/auth/me 返回）
let CURRENT: any = null

function mkEvent(city: string, district: string, type: string, level: string, status: string, desc: string, pop: number, area: number, cas: number, images: string[]) {
  const g = YN_CITIES[city] || { lat: 25, lng: 101 }
  const id = uid()
  return {
    id, code: 'YN-20260722-' + String(id).padStart(3, '0'),
    title: `${city}${district}${typeLabel[type]}灾情`, type, level, status,
    description: desc, locationText: `${city}${district}`, lat: g.lat, lng: g.lng,
    images: images.join(','), contact: '', reporterName: '一线信息员',
    affectedPopulation: pop, affectedArea: area, casualties: cas,
    createdAt: now(), updatedAt: now()
  }
}
function mkResource(name: string, type: string, status: string, cap: number, owner: string) {
  const id = uid()
  return {
    id, name, type, status, total: cap, available: status === 'IDLE' ? cap : 0, unit: '单位',
    city: '', location: '', owner, updatedAt: now()
  }
}
function mkDispatch(eventId: number, resourceId: number, status: string, conflict: boolean, reason?: string) {
  const ev = DISASTERS.find((d) => d.id === eventId)
  const rs = RESOURCES.find((r) => r.id === resourceId)
  return {
    id: uid(), eventId, eventCode: ev?.code || 'YN-UNKNOWN', resourceId,
    resourceName: rs?.name || '资源', resourceType: rs?.type || 'TEAM',
    fromCity: rs?.city || '昆明市', toCity: ev?.city || '昆明市', toLocation: ev?.locationText || '',
    status, dispatchedBy: '王指挥', dispatchedAt: now(), eta: '2h', conflict, conflictReason: reason
  }
}
function mkDoc(title: string, category: string, tags: string[], types: string[], chunks: number, uploader: string) {
  return {
    id: uid(), title, category, tags, disasterTypes: types, chunkCount: chunks,
    source: title, uploader, uploadedAt: now(), updatedAt: now(),
    summary: `${title}（共${chunks}个分块，已进入向量库）`
  }
}

// -------------------- 路由表 --------------------
interface Ctx { params: Record<string, string>; query: Record<string, any>; body: any; headers: any }
type Handler = (ctx: Ctx) => unknown
interface Route { method: string; pattern: RegExp; keys: string[]; handler: Handler }
const routes: Route[] = []
function route(method: string, path: string, handler: Handler) {
  const keys: string[] = []
  const pattern = new RegExp('^' + path.replace(/:[^/]+/g, (m) => { keys.push(m.slice(1)); return '([^/]+)' }) + '$')
  routes.push({ method: method.toUpperCase(), pattern, keys, handler })
}

// ----- 认证（返回结构与后端 LoginResponse 一致） -----
route('post', '/api/auth/login', (c) => {
  const u = USERS.find((x) => x.username === c.body.username && x.password === c.body.password)
  if (!u) return fail('用户名或密码错误', 401)
  CURRENT = { token: 'mock-token-' + u.id, username: u.username, realName: u.realName, roleKey: u.roleKey, roleName: u.roleName }
  return ok(CURRENT)
})
route('get', '/api/auth/me', () => {
  if (!CURRENT) return fail('未登录', 401)
  return ok(CURRENT)
})

// ----- 灾情上报（POST /api/reports，ROLE_REPORTER） -----
route('post', '/api/reports', (c) => {
  const b = c.body
  const id = uid()
  const ev = {
    id, code: 'YN-' + new Date().toISOString().slice(0, 10).replace(/-/g, '') + '-' + String(id).padStart(3, '0'),
    title: b.title, type: b.type, level: b.level, status: 'PENDING_VERIFY',
    description: b.content, locationText: b.locationText, lat: b.lat, lng: b.lng,
    images: b.images || '', contact: b.contact || '', reporterName: '当前信息员',
    createdAt: now(), updatedAt: now()
  }
  DISASTERS.unshift(ev)
  return ok(ev)
})

// ----- 灾情查询 / 状态流转（GET /api/incidents，POST /api/incidents/:id/confirm|reject|close） -----
route('get', '/api/incidents', (c) => {
  let list = [...DISASTERS]
  const { status, type } = c.query
  if (status) list = list.filter((d) => d.status === status)
  if (type) list = list.filter((d) => d.type === type)
  return ok(list)
})
route('get', '/api/incidents/:id', (c) => {
  const d = DISASTERS.find((x) => String(x.id) === c.params.id)
  return d ? ok(d) : fail('未找到灾情', 404)
})
const statusMap: Record<string, string> = { confirm: 'CONFIRMED', reject: 'REJECTED', close: 'CLOSED' }
for (const act of ['confirm', 'reject', 'close']) {
  route('post', '/api/incidents/:id/' + act, (c) => {
    const d = DISASTERS.find((x) => x.id === Number(c.params.id))
    if (!d) return fail('未找到灾情', 404)
    d.status = statusMap[act]
    d.verifiedBy = '王指挥'
    d.verifiedAt = now()
    d.updatedAt = now()
    return ok(d)
  })
}

// ----- 调度（POST /api/dispatch，GET /api/dispatch?incidentId=） -----
route('post', '/api/dispatch', (c) => {
  const b = c.body
  const records: any[] = []
  let conflict = false
  for (const it of b.items || []) {
    const r = RESOURCES.find((x) => x.id === it.resourceId)
    if (!r) continue
    const isConflict = r.status === 'DISPATCHED' || r.status === 'LOCKED' || r.status === 'MAINTENANCE'
    if (isConflict) conflict = true
    r.status = 'DISPATCHED'
    r.lockedBy = '王指挥'
    const rec = mkDispatch(b.incidentId, it.resourceId, isConflict ? 'CONFLICT' : 'EXECUTING', isConflict, isConflict ? `资源${r.name}当前状态为${r.status}，存在调度冲突` : undefined)
    DISPATCHES.unshift(rec)
    records.push(rec)
  }
  return ok(records)
})
route('get', '/api/dispatch', (c) => {
  const list = DISPATCHES.filter((d) => !c.query.incidentId || d.eventId === Number(c.query.incidentId))
  return ok(list)
})

// ----- 救援资源（GET/POST/PUT /api/resources） -----
route('get', '/api/resources', (c) => {
  let list = [...RESOURCES]
  const { type, status, city, keyword } = c.query
  if (type) list = list.filter((r) => r.type === type)
  if (status) list = list.filter((r) => r.status === status)
  if (city) list = list.filter((r) => r.city === city)
  if (keyword) list = list.filter((r) => r.name.includes(keyword))
  return ok(list)
})
route('get', '/api/resources/:id', (c) => {
  const r = RESOURCES.find((x) => String(x.id) === c.params.id)
  return r ? ok(r) : fail('未找到资源', 404)
})
route('post', '/api/resources', (c) => {
  const b = c.body
  const r = mkResource(b.name, b.type, 'IDLE', Number(b.total) || 0, b.owner || '')
  RESOURCES.push(r)
  return ok(r)
})
route('put', '/api/resources/:id', (c) => {
  const r = RESOURCES.find((x) => x.id === Number(c.params.id))
  if (r) Object.assign(r, c.body, { updatedAt: now() })
  return ok(r)
})

// ----- 应急方案（GET /api/plans/:id，POST /api/plans/:id/approve） -----
route('get', '/api/plans/:id', (c) => {
  const p = PLANS.find((x) => x.id === Number(c.params.id))
  return p ? ok(p) : fail('未找到方案', 404)
})
route('post', '/api/plans/:id/approve', (c) => {
  const p = PLANS.find((x) => x.id === Number(c.params.id))
  if (!p) return fail('未找到方案', 404)
  p.status = 'APPROVED'
  p.updatedAt = now()
  return ok(p)
})

// ----- 知识库（前端页，后端暂未提供接口） -----
route('get', '/api/knowledge', (c) => {
  let list = [...KNOWLEDGE]
  const { category, keyword } = c.query
  if (category) list = list.filter((k) => k.category === category)
  if (keyword) list = list.filter((k) => k.title.includes(keyword))
  return ok({ list, total: list.length })
})
route('post', '/api/knowledge', (c) => {
  const b = c.body
  const doc = mkDoc(b.title, b.category, b.tags || [], b.disasterTypes || [], 8, '当前用户')
  doc.summary = b.summary || doc.summary
  KNOWLEDGE.unshift(doc)
  return ok(doc)
})
route('delete', '/api/knowledge/:id', (c) => {
  const i = KNOWLEDGE.findIndex((k) => k.id === Number(c.params.id))
  if (i >= 0) KNOWLEDGE.splice(i, 1)
  return ok(true)
})

// ----- 审计（前端页） -----
route('get', '/api/audit/logs', (c) => {
  let list = [...AUDITS].reverse()
  const { keyword, page = 1, pageSize = 20 } = c.query
  if (keyword) list = list.filter((a) => a.operator.includes(keyword) || a.action.includes(keyword))
  const start = (Number(page) - 1) * Number(pageSize)
  return ok({ list: list.slice(start, start + Number(pageSize)), total: list.length, page: Number(page), pageSize: Number(pageSize) })
})

// ----- 系统管理（前端页） -----
route('get', '/api/system/users', () => {
  const list = USERS.map(({ password, ...u }) => ({ ...u, status: 'ENABLED', createdAt: now(), lastLoginAt: now() }))
  return ok({ list, total: list.length })
})
route('post', '/api/system/users', (c) => {
  const b = c.body
  const id = uid()
  USERS.push({ id, username: b.username, password: b.password || '123456', realName: b.realName, roleKey: (b.roles && b.roles[0]) || 'ROLE_REPORTER', roleName: ROLES.find((x) => x.code === (b.roles && b.roles[0]))?.name || '信息员' })
  return ok(true)
})
route('put', '/api/system/users/:id', (c) => {
  const u = USERS.find((x) => x.id === Number(c.params.id))
  if (u) Object.assign(u, c.body)
  return ok(true)
})
route('get', '/api/system/roles', () => ok(ROLES))
route('get', '/api/system/config', () => ok([
  { id: 1, key: 'weather.cron', value: '0 0 */1 * * *', group: '定时任务', remark: '气象数据自动采集周期' },
  { id: 2, key: 'warning.autoPublic', value: 'true', group: '预警', remark: '是否自动公开发布预警' },
  { id: 3, key: 'dispatch.lockTimeout', value: '30', group: '调度', remark: '调度锁定超时(分钟)' },
  { id: 4, key: 'plan.aiModel', value: 'qwen-max', group: 'AI', remark: '方案生成模型' }
]))
route('put', '/api/system/config', () => ok(true))

// ----- 文件上传（MinIO 代理，mock 返回占位图/视频） -----
route('post', '/api/upload', () => {
  const url = 'https://picsum.photos/seed/yn' + Math.floor(Math.random() * 9999) + '/400/300'
  return ok({ urls: [url] })
})

// -------------------- 适配器 --------------------
export const mockAdapter = async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
  const method = (config.method || 'get').toUpperCase()
  const url = (config.baseURL || '') + (config.url || '')
  const query = (config.params as Record<string, any>) || {}
  const body = parseBody(config)

  const matched = routes.find((r) => r.method === method && r.pattern.test(url))
  let payload: any
  if (!matched) {
    payload = fail('Mock: 未匹配的接口 ' + method + ' ' + url, 404)
  } else {
    const m = url.match(matched.pattern) as RegExpMatchArray
    const params: Record<string, string> = {}
    matched.keys.forEach((k, i) => (params[k] = m[i + 1]))
    try {
      payload = matched.handler({ params, query, body, headers: config.headers })
    } catch (e: any) {
      payload = fail('Mock error: ' + (e?.message || e), 500)
    }
  }
  await new Promise((r) => setTimeout(r, 120))
  return { data: payload, status: 200, statusText: 'OK', headers: {}, config, request: {} } as AxiosResponse
}

// -------------------- AI 方案流式模拟（替代 SSE） --------------------
export function simulatePlanStream(eventId: number, onChunk: (chunk: any) => void, extra?: string): () => void {
  const ev = DISASTERS.find((d) => d.id === eventId)
  const type = ev?.type || 'EARTHQUAKE'
  const planId = uid()
  const sections = [
    { title: '一、灾情研判', content: `根据上报信息，本次为${typeLabel[type as keyof typeof typeLabel] || '灾害'}灾害，影响范围涉及${ev?.locationText || '灾区'}。建议立即启动相应级别应急响应，成立现场指挥部。` },
    { title: '二、组织指挥', content: '由属地政府主要领导担任总指挥，应急、消防、卫健、交通等部门联合值守，实行24小时带班制度。' },
    { title: '三、救援处置', content: '1) 优先搜救被困人员；2) 打通生命通道，调度重型机械清除塌方；3) 设置警戒区，防范次生灾害；4) 保障通信与电力。' },
    { title: '四、群众转移安置', content: '按"就近、安全"原则转移受威胁群众至临时安置点，保障饮水、食品、御寒物资与基本医疗。' },
    { title: '五、信息报送', content: '严格执行灾情零报告制度，每2小时汇总一次进展，重大情况随时上报。' },
    { title: '六、恢复重建', content: '灾情稳定后开展损失评估，制定恢复重建方案，做好卫生防疫与心理疏导。' }
  ]
  const refs = [
    { docId: 1, docTitle: '云南省地震应急预案（2024版）', snippet: '启动Ⅱ级响应时，省应急厅派出工作组...', score: 0.91 },
    { docId: 2, docTitle: '滑坡泥石流灾害处置技术规范', snippet: '斜坡体出现裂缝应划定危险区...', score: 0.84 }
  ]
  const aiPlan = {
    title: `${typeLabel[type as keyof typeof typeLabel] || '灾害'}应急响应方案`,
    sections,
    references: refs,
    compliance: { passed: true, score: 92, issues: [], suggestions: ['建议补充夜间照明保障', '关注降雨预报防范次生灾害'] }
  }
  // 落库，便于 /api/plans/:id 回查
  PLANS.push({ id: planId, incidentId: eventId, title: aiPlan.title, content: JSON.stringify(aiPlan), status: 'REVIEWING', createdAt: now(), updatedAt: now() })

  let cancelled = false
  const timers: number[] = []
  let i = 0
  onChunk({ type: 'START', planId, title: aiPlan.title })
  const step = () => {
    if (cancelled) return
    if (i >= sections.length) {
      refs.forEach((r) => onChunk({ type: 'REFERENCE', reference: r }))
      onChunk({ type: 'COMPLIANCE', compliance: aiPlan.compliance })
      onChunk({ type: 'DONE', planId })
      return
    }
    const sec = sections[i]
    onChunk({ type: 'SECTION', sectionIndex: i, title: sec.title })
    const tokens = sec.content.match(/[^，。；]+[，。；]?/g) || [sec.content]
    let j = 0
    const pushToken = () => {
      if (cancelled) return
      if (j >= tokens.length) { i++; timers.push(window.setTimeout(step, 300)); return }
      onChunk({ type: 'CONTENT', sectionIndex: i, delta: tokens[j] })
      j++
      timers.push(window.setTimeout(pushToken, 90))
    }
    pushToken()
  }
  timers.push(window.setTimeout(step, 200))
  return () => { cancelled = true; timers.forEach((t) => clearTimeout(t)) }
}
