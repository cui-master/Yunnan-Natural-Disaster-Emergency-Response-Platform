import request from '@/utils/request'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

// 懒加载 mock：仅在 useMock=true 时动态 import
let _mock = null
if (useMock) {
  import('@/mock').then(mod => { _mock = mod.default || mod }).catch(() => {})
}
function mock() { return _mock }

export function login(data) {
  if (useMock && mock()) return Promise.resolve(mock().auth.login(data))
  return request({ url: '/auth/login', method: 'post', data }).then(res => {
    if (res.code === 200) {
      return {
        success: true,
        data: {
          token: res.data.token,
          userInfo: {
            id: res.data.id,
            username: res.data.username,
            realName: res.data.realName,
            role: res.data.roleCode,
            roleName: res.data.roleName,
            avatar: res.data.avatar,
            email: res.data.email,
            phone: res.data.phone,
            department: res.data.department
          }
        },
        message: res.message
      }
    }
    return { success: false, message: res.message || '登录失败' }
  })
}

export function logout() {
  if (useMock && mock()) return Promise.resolve(mock().auth.logout())
  return request({ url: '/auth/logout', method: 'post' })
}

export function getUserInfo() {
  if (useMock && mock()) return Promise.resolve(mock().auth.getUserInfo())
  return request({ url: '/auth/info', method: 'get' }).then(res => {
    if (res.code === 200) {
      return {
        success: true,
        data: {
          id: res.data.id,
          username: res.data.username,
          realName: res.data.realName,
          role: res.data.roleCode,
          roleName: res.data.roleName,
          avatar: res.data.avatar,
          email: res.data.email,
          phone: res.data.phone,
          department: res.data.department
        }
      }
    }
    return { success: false, message: res.message }
  })
}
