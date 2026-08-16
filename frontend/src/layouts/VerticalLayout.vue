<template>
  <div class="v-layout">
    <!-- 左侧侧边栏 -->
    <aside class="v-sidebar" :class="{ collapsed: isCollapsed }">
      <div class="v-logo">
        <el-icon :size="22" color="#e64545"><Warning /></el-icon>
        <span v-if="!isCollapsed" class="logo-text">云南应急</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :router="true"
        background-color="#243447"
        text-color="#a0aec0"
        active-text-color="#ffffff"
        class="v-menu"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>

      <div class="v-sidebar-footer">
        <el-button text size="small" @click="isCollapsed = !isCollapsed">
          <el-icon><component :is="isCollapsed ? 'Expand' : 'Fold'" /></el-icon>
          <span v-if="!isCollapsed">收起菜单</span>
        </el-button>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="v-main-wrapper">
      <!-- 顶部条 -->
      <header class="v-topbar">
        <div class="v-topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="defaultPath">{{ userStore.getRoleName() }}工作台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="v-topbar-right">
          <span class="time-text">{{ currentTime }}</span>
          <el-dropdown @command="handleCommand">
            <div class="user-bar">
              <el-avatar :size="30" :icon="UserFilled" />
              <div class="user-detail">
                <div class="user-name">{{ userStore.userInfo?.name || '用户' }}</div>
                <div class="user-role">{{ userStore.getRoleName() }}</div>
              </div>
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

      <!-- 内容区 -->
      <main class="v-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  Warning, UserFilled, ArrowDown, User, SwitchButton,
  Expand, Fold
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapsed = ref(false)
const currentTime = ref('')
let timer = null

const menuItems = computed(() => {
  const role = userStore.userInfo?.role
  const allMenus = {
    resmanager: [
      { path: '/resource/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/resource/dispatch', title: '调度看板', icon: 'Share' }
    ],
    admin: [
      { path: '/admin/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/admin/knowledge', title: '知识库管理', icon: 'Reading' },
      { path: '/admin/users', title: '用户管理', icon: 'User' },
      { path: '/admin/models', title: '模型管理', icon: 'Cpu' }
    ]
  }
  return allMenus[role] || []
})

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => route.meta?.title || '')

const defaultPath = computed(() => {
  const role = userStore.userInfo?.role
  const map = {
    resmanager: '/resource/dashboard',
    admin: '/admin/dashboard'
  }
  return map[role] || '/'
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
.v-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.v-sidebar {
  width: 220px;
  background: #1a2332;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s;
  overflow: hidden;

  &.collapsed {
    width: 64px;
  }
}

.v-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: #243447;

  .logo-text {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    letter-spacing: 1px;
    white-space: nowrap;
  }
}

.v-menu {
  flex: 1;
  border-right: none;
  padding: 12px 0;

  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: 8px;
    width: calc(100% - 24px);

    &.is-active {
      background: linear-gradient(90deg, rgba(230, 69, 69, 0.25) 0%, rgba(230, 69, 69, 0.05) 100%);
      color: #fff;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: #e64545;
        border-radius: 0 3px 3px 0;
      }
    }

    &:hover {
      background: rgba(255, 255, 255, 0.06);
    }
  }
}

.v-sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  text-align: center;

  .el-button {
    color: #64748b;
  }
}

.v-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.v-topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.v-topbar-left {
  :deep(.el-breadcrumb__inner) {
    font-size: 14px;
  }
}

.v-topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;

  .time-text {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #6b7280;
  }
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: #f3f4f6;
  }

  .user-detail {
    .user-name {
      font-size: 13px;
      font-weight: 500;
      color: #1f2937;
      line-height: 1.2;
    }

    .user-role {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 2px;
    }
  }

  .el-icon {
    color: #9ca3af;
    font-size: 12px;
  }
}

.v-content {
  flex: 1;
  overflow: auto;
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
  .v-sidebar {
    width: 64px;
  }

  .v-topbar {
    padding: 0 12px;
  }

  .v-topbar-left {
    :deep(.el-breadcrumb) {
      font-size: 12px;
    }
  }

  .user-detail,
  .time-text {
    display: none;
  }
}
</style>
