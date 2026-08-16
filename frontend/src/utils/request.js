import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

const service = axios.create({
  baseURL: '/api',
  timeout: 180000
})

// 全局登录过期处理锁，防止多个请求同时 401 导致弹窗刷屏
let isHandlingUnauthorized = false

service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers['Authorization'] = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    const res = response.data
    return res
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '请求失败'

    if (status === 401) {
      if (isHandlingUnauthorized) {
        return Promise.reject(error)
      }
      isHandlingUnauthorized = true

      const userStore = useUserStore()
      userStore.logout().finally(() => {
        // 已经不在登录页时才跳转和提示，避免刷屏
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
        }
        // 3s 后释放锁，避免后续 401 再次弹窗
        setTimeout(() => { isHandlingUnauthorized = false }, 3000)
      })
      return Promise.reject(error)
    }
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
