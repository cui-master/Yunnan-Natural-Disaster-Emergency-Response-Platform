<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <aside class="brand">
      <div class="brand-top">
        <div class="brand-logo">
          <span class="badge">⚠</span>
          <span class="brand-name">云南应急</span>
        </div>
        <h1 class="brand-title">云南省自然灾害<br />应急响应平台</h1>
        <p class="brand-sub">Yunnan Natural Disaster Emergency Response Platform</p>
      </div>
      <ul class="brand-feats">
        <li><el-icon><DataLine /></el-icon> 灾情态势一张图，实时监测预警</li>
        <li><el-icon><MagicStick /></el-icon> AI 辅助生成应急处置方案</li>
        <li><el-icon><Promotion /></el-icon> 救援资源一键调度协同</li>
      </ul>
      <div class="brand-foot">协同决策 · 快速响应 · 科学减灾</div>
    </aside>

    <!-- 右侧登录区 -->
    <main class="form-area">
      <div class="login-card">
        <h2 class="form-title">欢迎登录</h2>
        <p class="form-tip">请使用系统账号登录控制台</p>
        <el-form @submit.prevent="doLogin">
          <el-form-item>
            <el-input v-model="username" placeholder="用户名" size="large" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-button
            class="login-btn"
            type="primary"
            :loading="loading"
            size="large"
            style="width: 100%"
            @click="doLogin"
            >登 录</el-button
          >
        </el-form>

        <div class="demo">
          <div class="demo-head">演示账号（点击自动填充）</div>
          <div class="demo-chips">
            <button v-for="a in accounts" :key="a.user" type="button" class="chip" @click="fill(a)">
              <span class="chip-role">{{ a.label }}</span>
              <span class="chip-user">{{ a.user }}</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, DataLine, MagicStick, Promotion } from '@element-plus/icons-vue'
import { useAuth } from '../stores/auth'

const username = ref('')
const password = ref('')
const loading = ref(false)
const router = useRouter()
const auth = useAuth()

const accounts = [
  { user: 'reporter', label: '信息员' },
  { user: 'commander', label: '指挥员' },
  { user: 'resmanager', label: '资源管理员' },
  { user: 'admin', label: '系统管理员' }
]

// 登录后按角色进入各自工作台首页
const roleHome: Record<string, string> = {
  ROLE_REPORTER: '/report',
  ROLE_COMMANDER: '/dashboard',
  ROLE_RESMGR: '/resources',
  ROLE_ADMIN: '/system'
}

function fill(a: { user: string }) {
  username.value = a.user
  password.value = '123456'
}

async function doLogin() {
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    ElMessage.success('登录成功')
    router.push(roleHome[auth.roleKey] || '/')
  } catch (e: any) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
}
.brand {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 56px 56px 40px;
  color: #fff;
  background:
    radial-gradient(1200px 600px at 20% 10%, rgba(224, 62, 47, 0.35), transparent 60%),
    linear-gradient(150deg, #16202e 0%, #1f2d3d 55%, #233a52 100%);
  overflow: hidden;
}
.brand::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  -webkit-mask-image: radial-gradient(700px 500px at 30% 40%, #000, transparent 80%);
  mask-image: radial-gradient(700px 500px at 30% 40%, #000, transparent 80%);
  pointer-events: none;
}
.brand-top,
.brand-feats,
.brand-foot {
  position: relative;
  z-index: 1;
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e03e2f, #f2994a);
  font-size: 20px;
  box-shadow: 0 6px 16px rgba(224, 62, 47, 0.4);
}
.brand-name {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}
.brand-title {
  font-size: 34px;
  line-height: 1.3;
  font-weight: 800;
  margin: 28px 0 12px;
}
.brand-sub {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  letter-spacing: 0.5px;
  margin: 0;
}
.brand-feats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.brand-feats li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
}
.brand-feats .el-icon {
  color: #f2994a;
  font-size: 20px;
}
.brand-foot {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  letter-spacing: 2px;
}

.form-area {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  padding: 24px;
}
.login-card {
  width: 340px;
}
.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #1c2733;
  margin: 0 0 6px;
}
.form-tip {
  color: #7a8794;
  font-size: 13px;
  margin: 0 0 26px;
}
.login-btn {
  margin-top: 6px;
  letter-spacing: 4px;
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(224, 62, 47, 0.28);
}
.demo {
  margin-top: 26px;
  border-top: 1px dashed #e6eaf1;
  padding-top: 16px;
}
.demo-head {
  font-size: 12px;
  color: #7a8794;
  margin-bottom: 12px;
}
.demo-chips {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid #e6eaf1;
  border-radius: 10px;
  background: #fafbfc;
  cursor: pointer;
  text-align: left;
  transition: all 0.18s ease;
}
.chip:hover {
  border-color: #e03e2f;
  background: #fdece9;
  transform: translateY(-1px);
}
.chip-role {
  font-size: 13px;
  font-weight: 600;
  color: #1c2733;
}
.chip-user {
  font-size: 11px;
  color: #7a8794;
}

@media (max-width: 900px) {
  .brand {
    display: none;
  }
  .form-area {
    width: 100%;
  }
}
</style>
