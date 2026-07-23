import { defineStore } from 'pinia'
import { login as loginApi, me as meApi } from '@/api/auth'
import type { RoleCode } from '@/types'

interface State {
  token: string
  username: string
  realName: string
  roleKey: RoleCode | ''
  roleName: string
}

export const useAuthStore = defineStore('auth', {
  state: (): State => ({
    token: localStorage.getItem('token') || '',
    username: '',
    realName: '',
    roleKey: '',
    roleName: ''
  }),
  getters: {
    hasRole: (s) => (role: RoleCode | string) => (s.roleKey as string) === role
  },
  actions: {
    async login(username: string, password: string) {
      const d = await loginApi({ username, password })
      this.token = d.token
      this.username = d.username
      this.realName = d.realName
      this.roleKey = d.roleKey
      this.roleName = d.roleName
      localStorage.setItem('token', d.token)
    },
    async fetchMe() {
      try {
        const d = await meApi()
        this.username = d.username
        this.realName = d.realName
        this.roleKey = d.roleKey
        this.roleName = d.roleName
      } catch {
        /* ignore */
      }
    },
    logout() {
      this.token = ''
      this.username = ''
      this.realName = ''
      this.roleKey = ''
      this.roleName = ''
      localStorage.removeItem('token')
    }
  }
})

// 兼容旧引用
export const useAuth = useAuthStore
