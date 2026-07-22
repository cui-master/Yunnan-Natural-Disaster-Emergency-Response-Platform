import { createRouter, createWebHashHistory } from 'vue-router'
import Login from '../views/Login.vue'
import EventBoard from '../views/EventBoard.vue'
import ReportSubmit from '../views/ReportSubmit.vue'
import ResourceBoard from '../views/ResourceBoard.vue'
import { useAuth } from '../stores/auth'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: EventBoard, meta: { requiresAuth: true } },
  { path: '/report', component: ReportSubmit, meta: { requiresAuth: true, role: 'ROLE_REPORTER' } },
  { path: '/resources', component: ResourceBoard, meta: { requiresAuth: true, role: 'ROLE_RESMGR' } }
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to, _from, next) => {
  const auth = useAuth()
  if (to.meta.requiresAuth && !auth.token) {
    next('/login')
    return
  }
  if (to.meta.role && auth.roleKey && to.meta.role !== auth.roleKey) {
    next('/')
    return
  }
  next()
})

export default router
