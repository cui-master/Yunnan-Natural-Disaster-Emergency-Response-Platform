import { defineStore } from 'pinia'
import { login as loginApi, me as meApi } from '../api'

interface State {
  token: string
  username: string
  realName: string
  roleKey: string
  roleName: string
}

export const useAuth = defineStore('auth', {
  state: (): State => ({
    token: localStorage.getItem('token') || '',
    username: '',
    realName: '',
    roleKey: '',
    roleName: ''
  }),
  actions: {
    async login(username: string, password: string) {
      const d = await loginApi(username, password)
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
      } catch (_) {
        /* ignore */
      }
    },
    logout() {
      this.token = ''
      localStorage.removeItem('token')
    }
  }
})
