import { defineStore } from 'pinia'

export type NoticeType = 'urgent' | 'warning' | 'success' | 'info'

export interface Notice {
  id: number
  type: NoticeType
  title: string
  body: string
  ts: number // epoch ms
  read: boolean
  from?: string // 来源角色/系统
}

const MIN = 60_000
const HOUR = 60 * MIN
const DAY = 24 * HOUR

let seq = 1000

function seed(): Notice[] {
  const now = Date.now()
  return [
    {
      id: seq++,
      type: 'urgent',
      title: 'Ⅰ级地震灾情待核验',
      body: '怒江州泸水市发生 5.8 级地震，需指挥中心立即研判并指派核实。',
      ts: now - 3 * MIN,
      read: false,
      from: '灾情监测'
    },
    {
      id: seq++,
      type: 'warning',
      title: '可调救援资源偏低',
      body: '昭通市帐篷库存低于预警线（<500 顶），建议启动跨区调配。',
      ts: now - 42 * MIN,
      read: false,
      from: '资源调度'
    },
    {
      id: seq++,
      type: 'success',
      title: '处置方案已签发',
      body: '「大理州洪涝」AI 处置方案已获值班指挥长签发并下达。',
      ts: now - 2 * HOUR,
      read: false,
      from: '指挥研判'
    },
    {
      id: seq++,
      type: 'info',
      title: '新成员接入协同',
      body: '资源调度岗 李工 已接入系统，可分配调度任务。',
      ts: now - 5 * HOUR,
      read: true,
      from: '系统'
    },
    {
      id: seq++,
      type: 'warning',
      title: '气象预警更新',
      body: '云南省气象台发布暴雨橙色预警（Ⅲ级），请相关州市提前防范。',
      ts: now - 1 * DAY,
      read: true,
      from: '气象对接'
    }
  ]
}

// 列表上限：超过后丢弃最旧的，避免实时流长期运行导致数组无限增长、渲染与 getter 渐进变慢
const MAX_NOTICES = 100

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    list: seed()
  }),
  getters: {
    unread: (s) => s.list.filter((n) => !n.read).length,
    sorted: (s) => [...s.list].sort((a, b) => b.ts - a.ts)
  },
  actions: {
    push(n: Omit<Notice, 'id' | 'read'>) {
      this.list.unshift({ ...n, id: seq++, read: false })
      if (this.list.length > MAX_NOTICES) {
        this.list.splice(MAX_NOTICES)
      }
    },
    markRead(id: number) {
      const it = this.list.find((x) => x.id === id)
      if (it) it.read = true
    },
    markAllRead() {
      this.list.forEach((n) => (n.read = true))
    },
    remove(id: number) {
      this.list = this.list.filter((x) => x.id !== id)
    }
  }
})
