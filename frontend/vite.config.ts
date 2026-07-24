import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

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
      // 对齐「别人更新后的多模块后端」：按服务拆分端口代理
      // admin-service :8094  auth/knowledge/audit/system
      '/api/auth': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/knowledge': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/audit': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/system': { target: 'http://localhost:8094', changeOrigin: true },
      '/api/upload': { target: 'http://localhost:8094', changeOrigin: true },
      // command-service :8092  incidents/plans/dispatch
      '/api/incidents': { target: 'http://localhost:8092', changeOrigin: true },
      '/api/plans': { target: 'http://localhost:8092', changeOrigin: true },
      '/api/dispatch': { target: 'http://localhost:8092', changeOrigin: true },
      // report-service :8091  reports
      '/api/reports': { target: 'http://localhost:8091', changeOrigin: true },
      // resource-service :8093  resources
      '/api/resources': { target: 'http://localhost:8093', changeOrigin: true },
      // WebSocket(/ws/events, common 模块各服务均注册) → command 8092
      '/ws': { target: 'ws://localhost:8092', ws: true }
    }
  },
  build: {
    outDir: 'dist',
    // element-plus 为全量注册（app.use(ElementPlus)），其 chunk 体量较大且各角色首屏均依赖，
    // 此处抬高告警阈值，避免 >500kB 噪音；如需进一步瘦身需改为按需组件级引入。
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 将重型依赖拆分为独立、可独立缓存的 chunk：
        // - echarts/leaflet：仅指挥员态势大屏使用，其余角色首屏不再加载
        // - element-plus：UI 基础库，常驻首屏但独立缓存
        // - vue-vendor：vue / vue-router / pinia / @vue / @vueuse 运行时基座
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
            if (id.includes('leaflet')) return 'leaflet'
            if (id.includes('element-plus') || id.includes('@element-plus')) return 'element-plus'
            if (/[\\/]node_modules[\\/](vue|vue-router|pinia|@vue|@vueuse)[\\/]/.test(id)) return 'vue-vendor'
          }
        }
      }
    }
  }
})
