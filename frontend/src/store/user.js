import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

  const roleNameMap = {
    reporter: '普通信息员',
    commander: '应急指挥员',
    resmanager: '资源管理员',
    admin: '系统管理员'
  }

  async function login(username, password, role) {
    try {
      const res = await apiLogin({ username, password, role })
      if (res.success) {
        token.value = res.data.token
        userInfo.value = res.data.userInfo
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('userInfo', JSON.stringify(res.data.userInfo))
      }
      return res
    } catch (e) {
      return { success: false, message: e.message || '登录失败' }
    }
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (e) {
      // ignore
    }
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function getRoleName(role) {
    return roleNameMap[role || userInfo.value?.role || userInfo.value?.roleCode] || '未知角色'
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    logout,
    getRoleName
  }
})
