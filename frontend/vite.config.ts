import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

// 四系统共享数据库：前端按业务路径把 /api/* 分发到对应后端服务
// 信息员(report:8091) / 指挥(command:8092) / 资源(resource:8093) / 管理(admin:8094)
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      // 系统管理（统一认证入口 + 用户/角色/知识库/审计/配置）
      '/api/auth': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/system': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/knowledge': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/audit': { target: 'http://localhost:8094', changeOrigin: true },
      // 信息员：灾情上报
      '/api/reports': { target: 'http://localhost:8091', changeOrigin: true },
      // 资源管理员：人/车/物/避难所
      '/api/resources': { target: 'http://localhost:8093', changeOrigin: true },
      // 应急指挥：事件审核 / 处置方案 / 资源调度 / 实时推送
      '/api/incidents': { target: 'http://localhost:8092', changeOrigin: true },
      '/api/plans': { target: 'http://localhost:8092', changeOrigin: true },
      '/api/dispatch': { target: 'http://localhost:8092', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8092', ws: true }
    }
  },
  build: { outDir: 'dist' }
})
