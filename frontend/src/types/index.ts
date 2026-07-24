// ============================================================
// 云南省自然灾害应急响应平台 - 前端类型契约
// 与后端（Spring Boot）接口严格对齐：返回结构 R<T>={code,message,data}
// 角色键 / 状态枚举 / 字段名 均以后端为准。
// ============================================================

/** 统一响应包装 */
export interface ApiResp<T> {
  code: number
  message: string
  data: T
}

// -------------------- 用户 / 权限（RBAC） --------------------

/** 4 种角色（与后端 Authz.require 保持一致，带 ROLE_ 前缀） */
export type RoleCode = 'ROLE_REPORTER' | 'ROLE_COMMANDER' | 'ROLE_RESMGR' | 'ROLE_ADMIN'

export interface LoginReq {
  username: string
  password: string
}

/** 后端登录返回（扁平结构） */
export interface LoginResp {
  token: string
  username: string
  realName: string
  roleKey: RoleCode
  roleName: string
}

// -------------------- 灾情工单（状态机） --------------------

export type DisasterType =
  | 'EARTHQUAKE'
  | 'FLOOD'
  | 'LANDSLIDE'
  | 'DEBRIS_FLOW'
  | 'DROUGHT'
  | 'FOREST_FIRE'
  | 'HAIL'
  | 'TYPHOON'

export type DisasterLevel = 'I' | 'II' | 'III' | 'IV'

/** 工单状态机（后端 IncidentStatus）：待核验→已确认→处置中→已结束→已驳回 */
export type EventStatus = 'PENDING_VERIFY' | 'CONFIRMED' | 'IN_PROGRESS' | 'CLOSED' | 'REJECTED'

export interface GeoPoint {
  lng: number
  lat: number
}

/** 前端视图模型（详情/列表展示用） */
export interface DisasterEvent {
  id: number
  code: string
  title: string
  type: DisasterType
  level: DisasterLevel
  status: EventStatus
  province: string
  city: string
  district: string
  location: string
  geo: GeoPoint
  description: string
  reporter: string
  affectedPopulation?: number
  affectedArea?: number
  casualties?: number
  images: string[]
  verifiedBy?: string
  verifiedAt?: string
  createdAt: string
  updatedAt: string
}

/** 上报提交体（映射到后端 ReportSubmitRequest） */
export interface DisasterReportReq {
  title: string
  type: DisasterType
  level: DisasterLevel
  city: string
  district: string
  location: string
  lng: number
  lat: number
  description: string
  affectedPopulation?: number
  affectedArea?: number
  casualties?: number
  images: string[]
}

export type ReviewAction = 'CONFIRM' | 'REJECT' | 'CLOSE'
export interface ReviewReq {
  eventId: number
  action: ReviewAction
  comment?: string
}

// -------------------- 救援资源 / 调度 --------------------

export type ResourceType =
  | 'PERSONNEL'
  | 'VEHICLE'
  | 'EQUIPMENT'
  | 'MATERIAL'
  | 'MEDICAL'
  | 'SHELTER'
  | 'TEAM'

export type ResourceStatus = 'IDLE' | 'DISPATCHED' | 'LOCKED' | 'MAINTENANCE'

export interface RescueResource {
  id: number
  name: string
  type: ResourceType
  status: ResourceStatus
  city: string
  location: string
  geo?: GeoPoint
  capacity?: number
  owner: string
  contact?: string
  lockedBy?: string
  lockedAt?: string
  note?: string
  updatedAt: string
}

export interface DispatchRecord {
  id: number
  eventId: number
  eventCode: string
  resourceId: number
  resourceName: string
  resourceType: ResourceType
  fromCity: string
  toCity: string
  toLocation: string
  status: string
  dispatchedBy: string
  dispatchedAt: string
  eta?: string
  conflict?: boolean
  conflictReason?: string
}

export interface DispatchReq {
  eventId: number
  resourceIds: number[]
  toCity?: string
  toLocation?: string
  note?: string
}

// -------------------- 应急方案（AI） --------------------

export interface PlanSection {
  title: string
  content: string
}

export interface PlanReference {
  docId: number
  docTitle: string
  snippet: string
  score: number
}

export interface PlanCompliance {
  passed: boolean
  score: number
  issues: string[]
  suggestions: string[]
}

export type PlanStatus = 'DRAFT' | 'GENERATING' | 'REVIEWING' | 'APPROVED'

export interface EmergencyPlan {
  id: number
  eventId: number
  eventCode: string
  title: string
  level: DisasterLevel
  type: DisasterType
  status: PlanStatus
  sections: PlanSection[]
  references: PlanReference[]
  compliance?: PlanCompliance
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface PlanGenerateReq {
  eventId: number
  extraRequirement?: string
}

/** SSE 流式 chunk（与方案工作台 onChunk 对齐） */
export interface PlanStreamChunk {
  type: 'START' | 'SECTION' | 'CONTENT' | 'REFERENCE' | 'COMPLIANCE' | 'DONE' | 'ERROR'
  sectionIndex?: number
  title?: string
  delta?: string
  reference?: PlanReference
  compliance?: PlanCompliance
  planId?: number
  message?: string
}

// -------------------- 知识库（RAG，前端页，后端暂未提供接口） --------------------

export type KnowledgeCategory =
  | 'EMERGENCY_PLAN'
  | 'DISASTER_SPEC'
  | 'LAW'
  | 'CASE'
  | 'GUIDE'

export interface KnowledgeDoc {
  id: number
  title: string
  category: KnowledgeCategory
  tags: string[]
  disasterTypes: DisasterType[]
  chunkCount: number
  source: string
  uploader: string
  uploadedAt: string
  updatedAt: string
  summary?: string
}

export interface KnowledgeUploadReq {
  title: string
  category: KnowledgeCategory
  tags: string[]
  disasterTypes: DisasterType[]
  fileUrl: string
}

<<<<<<< HEAD
// -------------------- 知识库（Dify，按 kit 分库：优化调度 / 风险评估） --------------------
// 注意：dataset_id 与密钥均托管在 FastAPI ai_service（其他成员实现），前端只传知识库中文名。

export type KnowledgeKitKey = 'OPTIMIZE' | 'RISK'

export interface KnowledgeKitMeta {
  key: KnowledgeKitKey
  /** 传给后端/ai_service 的中文名，对应 FastAPI KB_MAP 的 key */
  name: string
  datasetId: string
  desc: string
}

export const KNOWLEDGE_KITS: KnowledgeKitMeta[] = [
  {
    key: 'OPTIMIZE',
    name: '优化调度',
    datasetId: 'a154e469-3acd-4c33-bcdc-ea65d0886488',
    desc: '物资调度预案 / Sandbox 仿真参考资料'
  },
  {
    key: 'RISK',
    name: '风险评估',
    datasetId: '03d787b9-e585-4b85-abbe-332e208c6530',
    desc: '风险研判 / 历史案例 / 处置规范'
  }
]

export type KnowledgeKitDocStatus = 'PARSING' | 'COMPLETED' | 'FAILED'

export interface KnowledgeKitDoc {
  id: string
  name: string
  status: KnowledgeKitDocStatus
  wordCount?: number
  chunkCount?: number
  uploadedAt: string
}

export interface KnowledgeKitUploadResult {
  name: string
  status: string
}
export interface KnowledgeKitUploadResp {
  msg: string
  results: KnowledgeKitUploadResult[]
}

=======
>>>>>>> feature-cui
// -------------------- 审计日志 / 系统管理（前端页，后端暂未提供接口） --------------------

export interface AuditLog {
  id: number
  operator: string
  role: RoleCode
  action: string
  module: string
  target: string
  ip: string
  result: 'SUCCESS' | 'FAIL'
  detail?: string
  createdAt: string
}

export interface SystemUser {
  id: number
  username: string
  realName: string
  phone?: string
  roles: RoleCode[]
  status: 'ENABLED' | 'DISABLED'
  createdAt: string
  lastLoginAt?: string
}

export interface SystemConfig {
  id: number
  key: string
  value: string
  group: string
  remark?: string
}

// -------------------- 大屏统计（由 /api/incidents 客户端聚合） --------------------

export interface DashboardStat {
  eventTotal: number
  handlingCount: number
  pendingVerifyCount: number
  finishedCount: number
  resourceTotal: number
  resourceIdle: number
  affectedPopulation: number
  casualties: number
}

export interface TypeCount {
  type: DisasterType
  count: number
}
export interface CityCount {
  city: string
  count: number
}
export interface TrendPoint {
  date: string
  count: number
}

/** 实时事件推送消息（WebSocket /ws/events） */
export interface RealtimeEvent {
  id: number
  eventId: number
  eventCode: string
  type: 'NEW' | 'STATUS_CHANGE' | 'DISPATCH' | 'PLAN'
  message: string
  status?: EventStatus
  createdAt: string
}
