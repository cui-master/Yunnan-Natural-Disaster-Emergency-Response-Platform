<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore, type NoticeType } from '@/stores/notifications'
import { USE_MOCK } from '@/api/mock'

const auth = useAuthStore()
const router = useRouter()
const notifications = useNotificationsStore()
const { unread, sorted } = storeToRefs(notifications)

const panelOpen = ref(false)
const drawerOpen = ref(false)
const hoverOpen = ref(false)
let closeTimer: number | null = null

function enter() {
  if (closeTimer) clearTimeout(closeTimer)
  hoverOpen.value = true
}
function leave() {
  closeTimer = window.setTimeout(() => (hoverOpen.value = false), 160)
}

const MIN = 60_000
const HOUR = 60 * MIN
const DAY = 24 * HOUR
function fromNow(ts: number): string {
  const diff = Date.now() - ts
  if (diff < MIN) return '刚刚'
  if (diff < HOUR) return `${Math.floor(diff / MIN)} 分钟前`
  if (diff < DAY) return `${Math.floor(diff / HOUR)} 小时前`
  return `${Math.floor(diff / DAY)} 天前`
}

const typeMeta: Record<NoticeType, { icon: string; cls: string }> = {
  urgent: { icon: 'CircleClose', cls: 'urgent' },
  warning: { icon: 'Warning', cls: 'warning' },
  success: { icon: 'CircleCheck', cls: 'success' },
  info: { icon: 'InfoFilled', cls: 'info' }
}

function openNotice(n: { id: number }) {
  notifications.markRead(n.id)
}
function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="uc">
    <el-tag v-if="USE_MOCK" type="warning" size="small" effect="plain">Mock 联调</el-tag>
    <el-tag v-else type="success" size="small" effect="plain">真实后端</el-tag>

    <!-- 消息盒子 -->
    <div class="msg-wrap" @mouseenter="enter" @mouseleave="leave">
      <button class="msg-btn" :class="{ active: hoverOpen }" @click="hoverOpen = !hoverOpen">
        <el-icon><Bell /></el-icon>
        <span v-if="unread" class="msg-badge">{{ unread > 99 ? '99+' : unread }}</span>
      </button>
      <transition name="msg-pop">
        <div v-if="hoverOpen" class="msg-panel" @mouseenter="enter" @mouseleave="leave">
          <div class="msg-head">
            <span class="msg-head-title">消息中心</span>
            <button class="link" :disabled="!unread" @click="notifications.markAllRead()">
              全部已读
            </button>
          </div>
          <div class="msg-list">
            <button
              v-for="n in sorted"
              :key="n.id"
              class="msg-item"
              :class="[typeMeta[n.type].cls, { unread: !n.read }]"
              @click="openNotice(n)"
            >
              <span class="msg-dot"></span>
              <span class="msg-ico"><el-icon><component :is="typeMeta[n.type].icon" /></el-icon></span>
              <span class="msg-body">
                <span class="msg-item-title">{{ n.title }}</span>
                <span class="msg-text">{{ n.body }}</span>
                <span class="msg-time">{{ n.from ? n.from + ' · ' : '' }}{{ fromNow(n.ts) }}</span>
              </span>
            </button>
            <div v-if="!sorted.length" class="msg-empty">暂无消息</div>
          </div>
          <div class="msg-foot">
            <button class="link" @click="(hoverOpen = false), (drawerOpen = true)">查看全部消息</button>
          </div>
        </div>
      </transition>
    </div>

    <el-dropdown @command="logout">
      <span class="user">
        <el-avatar :size="30" class="avatar">{{ (auth.realName || 'U')[0] }}</el-avatar>
        <span class="name">{{ auth.realName }}</span>
        <span class="role">{{ auth.roleName }}</span>
        <el-icon><ArrowDown /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 全部消息抽屉 -->
    <el-drawer v-model="drawerOpen" title="全部消息" direction="rtl" size="380px">
      <div class="drawer-head">
        <span>共 {{ sorted.length }} 条 · 未读 {{ unread }}</span>
        <button class="link" :disabled="!unread" @click="notifications.markAllRead()">全部已读</button>
      </div>
      <div class="drawer-list">
        <div
          v-for="n in sorted"
          :key="n.id"
          class="msg-item lg"
          :class="[typeMeta[n.type].cls, { unread: !n.read }]"
          @click="openNotice(n)"
        >
          <span class="msg-dot"></span>
          <span class="msg-ico"><el-icon><component :is="typeMeta[n.type].icon" /></el-icon></span>
          <span class="msg-body">
            <span class="msg-item-title">{{ n.title }}</span>
            <span class="msg-text">{{ n.body }}</span>
            <span class="msg-time">{{ n.from ? n.from + ' · ' : '' }}{{ fromNow(n.ts) }}</span>
          </span>
        </div>
        <div v-if="!sorted.length" class="msg-empty">暂无消息</div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.uc {
  display: flex;
  align-items: center;
  gap: 14px;
}
.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}
.avatar {
  background: linear-gradient(135deg, var(--ydr-primary), var(--ydr-primary-dark, #b33226));
  color: #fff;
  font-weight: 600;
}
.name {
  font-size: 14px;
  color: #303133;
}
.role {
  font-size: 12px;
  color: #909399;
}

/* ===== 消息盒子 ===== */
.msg-wrap {
  position: relative;
}
.msg-btn {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ydr-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  cursor: pointer;
  transition: background 0.18s var(--ease-out-quart), color 0.18s var(--ease-out-quart),
    border-color 0.18s var(--ease-out-quart);
}
.msg-btn:hover {
  background: var(--ydr-primary-soft);
  color: var(--ydr-primary);
}
.msg-btn.active {
  background: var(--ydr-primary-soft);
  color: var(--ydr-primary);
  border-color: color-mix(in oklch, var(--ydr-primary) 25%, transparent);
}
.msg-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 9px;
  background: var(--ydr-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  border: 2px solid #fff;
  animation: msg-pulse 1.8s var(--ease-out-quart) infinite;
}
@keyframes msg-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 oklch(55% 0.2 25 / 0.5);
  }
  50% {
    box-shadow: 0 0 0 5px oklch(55% 0.2 25 / 0);
  }
}

.msg-panel {
  position: absolute;
  top: 48px;
  right: 0;
  width: 360px;
  background: #fff;
  border: 1px solid var(--ydr-border);
  border-radius: 14px;
  box-shadow: var(--ydr-shadow-lg);
  overflow: hidden;
  transform-origin: top right;
  z-index: 50;
}
.msg-pop-enter-active {
  transition: opacity 0.2s var(--ease-out-expo), transform 0.2s var(--ease-out-expo);
}
.msg-pop-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}
.msg-pop-enter-from,
.msg-pop-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.97);
}
.msg-head,
.msg-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
}
.msg-head {
  border-bottom: 1px solid var(--ydr-border);
}
.msg-head-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  color: var(--ydr-ink);
}
.msg-foot {
  border-top: 1px solid var(--ydr-border);
  justify-content: center;
}
.link {
  background: none;
  border: none;
  color: var(--ydr-primary);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
}
.link:disabled {
  color: var(--ydr-sub);
  cursor: default;
}
.msg-list,
.drawer-list {
  max-height: 360px;
  overflow-y: auto;
  padding: 6px;
}
.drawer-list {
  max-height: none;
}

.msg-item {
  position: relative;
  width: 100%;
  text-align: left;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 11px 12px 11px 14px;
  border-radius: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.16s var(--ease-out-quart);
}
.msg-item:hover {
  background: var(--ydr-bg);
}
.msg-item.unread {
  background: color-mix(in oklch, var(--ydr-primary) 5%, transparent);
}
.msg-item.unread:hover {
  background: color-mix(in oklch, var(--ydr-primary) 9%, transparent);
}
.msg-dot {
  position: absolute;
  left: 4px;
  top: 18px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
}
.msg-item.unread .msg-dot {
  background: var(--ydr-primary);
}
.msg-ico {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.msg-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.msg-item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ydr-ink);
  line-height: 1.35;
}
.msg-text {
  font-size: 12.5px;
  color: var(--ydr-sub);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.msg-time {
  font-size: 11.5px;
  color: var(--ydr-sub);
  opacity: 0.8;
}

/* 类型着色 */
.urgent .msg-ico {
  background: color-mix(in oklch, var(--ydr-primary) 14%, transparent);
  color: var(--ydr-primary);
}
.warning .msg-ico {
  background: color-mix(in oklch, var(--ydr-warning) 16%, transparent);
  color: var(--ydr-warning);
}
.success .msg-ico {
  background: color-mix(in oklch, var(--ydr-success) 15%, transparent);
  color: var(--ydr-success);
}
.info .msg-ico {
  background: color-mix(in oklch, var(--ydr-info) 14%, transparent);
  color: var(--ydr-info);
}

.msg-empty {
  text-align: center;
  color: var(--ydr-sub);
  font-size: 13px;
  padding: 28px 0;
}
.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px 14px;
  font-size: 13px;
  color: var(--ydr-sub);
  border-bottom: 1px solid var(--ydr-border);
  margin-bottom: 8px;
}
</style>
