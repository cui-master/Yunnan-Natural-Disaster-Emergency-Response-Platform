<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <div class="logo">
          <el-icon :size="28"><Warning /></el-icon>
          <span>云南应急</span>
        </div>
        <h1 class="title">云南省自然灾害<br />应急响应平台</h1>
        <p class="subtitle">Yunnan Natural Disaster Emergency Response Platform</p>
      </div>
      <div class="features">
        <div class="feature-item">
          <el-icon :size="16"><DataBoard /></el-icon>
          <span>灾情态势一张图，实时动态预警</span>
        </div>
        <div class="feature-item">
          <el-icon :size="16"><Cpu /></el-icon>
          <span>AI 辅助决策，智能调度方案</span>
        </div>
        <div class="feature-item">
          <el-icon :size="16"><Connection /></el-icon>
          <span>数据融合，稳定高效运行</span>
        </div>
      </div>
      <div class="footer-text">
        协同决策 · 快速响应 · 科学减灾
      </div>
    </div>

    <div class="login-right">
      <div class="login-form-wrapper">
        <h2 class="form-title">欢迎登录</h2>
        <p class="form-subtitle">请选择角色并登录您的账号</p>

        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="admin" size="large" :prefix-icon="User" />
          </el-form-item>

          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="******" size="large" :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
              登 录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="role-section">
          <p class="role-label">选择角色（点击切换）</p>
          <div class="role-grid">
            <div
              v-for="role in roles"
              :key="role.value"
              class="role-card"
              :class="{ active: form.role === role.value }"
              @click="form.role = role.value; form.username = role.value"
            >
              <el-icon :size="22"><component :is="role.icon" /></el-icon>
              <span>{{ role.label }}</span>
            </div>
          </div>
          <p class="hint"></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import {
  User, Lock, Warning, DataBoard, Cpu, Connection,
  EditPen, DataLine, Share, Setting
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const roles = [
  { value: 'reporter', label: '信息员', icon: 'EditPen' },
  { value: 'commander', label: '指挥员', icon: 'DataLine' },
  { value: 'resmanager', label: '资源管理员', icon: 'Share' },
  { value: 'admin', label: '系统管理员', icon: 'Setting' }
]

const form = reactive({
  username: 'admin',
  password: '123456',
  role: 'admin'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await userStore.login(form.username, form.password, form.role)
    if (res.success) {
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || getDefaultRoute(form.role)
      router.push(redirect)
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}

function getDefaultRoute(role) {
  const map = {
    reporter: '/reporter/dashboard',
    commander: '/commander/dashboard',
    resmanager: '/resource/dashboard',
    admin: '/admin/dashboard'
  }
  return map[role] || '/login'
}
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 100vh;

  @media (max-width: 900px) {
    flex-direction: column;
  }
}

.login-left {
  flex: 1.2;
  background: linear-gradient(135deg, #0f1923 0%, #1a2d42 50%, #243b55 100%);
  color: #fff;
  padding: 60px 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -100px;
    right: -100px;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(230, 69, 69, 0.3) 0%, transparent 70%);
    border-radius: 50%;
  }

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 100%;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  @media (max-width: 900px) {
    padding: 30px;
    min-height: 200px;
  }
}

.brand {
  position: relative;
  z-index: 1;

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 40px;

    .el-icon {
      color: #e64545;
      background: rgba(230, 69, 69, 0.15);
      padding: 8px;
      border-radius: 8px;
    }
  }

  .title {
    font-size: 34px;
    font-weight: 700;
    line-height: 1.4;
    margin-bottom: 12px;
    background: linear-gradient(135deg, #fff 0%, #b8c4d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .subtitle {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    letter-spacing: 1px;
  }
}

.features {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .feature-item {
    display: flex;
    align-items: center;
    gap: 12px;
    color: rgba(255, 255, 255, 0.75);
    font-size: 14px;

    .el-icon {
      color: #4fc3f7;
    }
  }
}

.footer-text {
  position: relative;
  z-index: 1;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 2px;
}

.login-right {
  flex: 0.8;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;

  @media (max-width: 900px) {
    padding: 30px 20px;
  }
}

.login-form-wrapper {
  width: 100%;
  max-width: 380px;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.form-subtitle {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 32px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 4px;
  border-radius: 6px;
  margin-top: 8px;
}

.role-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.role-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 12px;
  text-align: center;
}

.role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.role-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #4b5563;

  .el-icon {
    color: #9ca3af;
    transition: color 0.2s;
  }

  &:hover {
    border-color: #e64545;
    color: #e64545;

    .el-icon {
      color: #e64545;
    }
  }

  &.active {
    border-color: #e64545;
    background: rgba(230, 69, 69, 0.05);
    color: #e64545;
    font-weight: 500;

    .el-icon {
      color: #e64545;
    }
  }
}

.hint {
  text-align: center;
  font-size: 12px;
  color: #d1d5db;
  margin-top: 16px;
}
</style>
