export interface LoginResp {
  token: string
  username: string
  realName: string
  roleKey: string
  roleName: string
}

export interface Incident {
  id: number
  code: string
  title: string
  type: string
  level: string
  status: string
  description: string
  createdAt: string
}

export interface Resource {
  id: number
  name: string
  type: string
  total: number
  available: number
  unit: string
  status: string
}

export interface EmergencyPlan {
  id: number
  incidentId: number
  title: string
  content: string
  status: string
}

export interface DispatchOrder {
  id: number
  resourceId: number
  quantity: number
  status: string
}

export interface AiPlan {
  title: string
  content: string
  steps: string[]
  resourceSuggestions: Array<{ resourceType: string; name: string; suggestQty: number }>
  citations: Array<{ source: string; excerpt: string; score: number }>
}
