<template>
  <div class="h-layout">
    <!-- 顶部 Header -->
    <header class="h-header">
      <div class="h-header-left">
        <div class="logo">
          <el-icon :size="22" color="#e64545"><Warning /></el-icon>
          <span class="logo-text">云南应急</span>
        </div>
        <div class="h-nav">
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :router="true"
            background-color="transparent"
            text-color="#cbd5e1"
            active-text-color="#ffffff"
            class="h-menu"
          >
            <el-menu-item
              v-for="item in menuItems"
              :key="item.path"
              :index="item.path"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </div>
      </div>

      <div class="h-header-right">
        <div class="page-info">
          <span class="current-page">{{ currentPageTitle }}</span>
          <span class="current-time">{{ currentTime }}</span>
        </div>
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" :icon="UserFilled" />
            <span class="user-name">{{ userStore.userInfo?.name || '用户' }}</span>
            <el-tag :type="roleTagType" size="small" effect="plain">{{ userStore.getRoleName() }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>个人中心
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="h-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  Warning, UserFilled, ArrowDown, User, SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const currentTime = ref('')
let timer = null

const menuItems = computed(() => {
  const role = userStore.userInfo?.role
  const allMenus = {
    reporter: [
      { path: '/reporter/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/reporter/report', title: '灾情上报', icon: 'EditPen' }
    ],
    commander: [
      { path: '/commander/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/commander/review', title: '审核事件', icon: 'CircleCheck' },
      { path: '/commander/dispatch', title: '调度看板', icon: 'Share' },
      { path: '/commander/plan', title: '处置方案', icon: 'Document' }
    ]
  }
  return allMenus[role] || []
})

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => route.meta?.title || '')

const roleTagType = computed(() => {
  const map = {
    reporter: 'success',
    commander: 'warning',
    resmanager: 'info',
    admin: 'danger'
  }
  return map[userStore.userInfo?.role] || 'info'
})

function updateTime() {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

async function handleCommand(cmd) {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // cancel
    }
  }
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.h-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.h-header {
  height: 56px;
  background: linear-gradient(90deg, #1a2332 0%, #243447 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.h-header-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;

  .logo-text {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    letter-spacing: 1px;
  }
}

.h-nav {
  height: 56px;
}

.h-menu {
  border-bottom: none !important;
  height: 56px;
  line-height: 56px;

  :deep(.el-menu-item) {
    height: 56px;
    line-height: 56px;
    font-size: 14px;
    padding: 0 18px;
    border-bottom: 2px solid transparent;

    &.is-active {
      border-bottom: 2px solid #e64545;
      background: rgba(230, 69, 69, 0.08);
    }

    &:hover {
      background: rgba(255, 255, 255, 0.06);
    }
  }
}

.h-header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #94a3b8;
  font-size: 13px;

  .current-page {
    color: #e2e8f0;
    font-weight: 500;
  }

  .current-time {
    font-family: 'Courier New', monospace;
    font-size: 12px;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 6px;
  transition: background 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .user-name {
    color: #f1f5f9;
    font-size: 13px;
  }

  .el-icon {
    color: #94a3b8;
    font-size: 12px;
  }
}

.h-main {
  flex: 1;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .h-header {
    padding: 0 12px;
  }

  .h-header-left {
    gap: 12px;
  }

  .logo .logo-text {
    font-size: 14px;
  }

  .h-nav {
    :deep(.el-menu-item) {
      padding: 0 10px;
      font-size: 12px;

      span {
        display: none;
      }
    }
  }

  .page-info .current-page,
  .page-info .current-time {
    display: none;
  }

  .user-info .user-name,
  .user-info .el-tag,
  .user-info .el-icon {
    display: none;
  }
}
</style>
