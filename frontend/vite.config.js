import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

/**
 * Vite 配置
 *
 * 反向代理目标通过 .env 配置：
 *   - VITE_API_TARGET    Spring Boot 后端（与 backend/src/main/resources/application.yml 中 server.port 保持一致）
 *   - VITE_AI_API_TARGET AI 服务 FastAPI（与 ai-service 启动端口保持一致）
 *
 * 不设环境变量时使用下方默认值（localhost:8083 / localhost:8050）。
 */
export default defineConfig(({ mode }) => {
  // 读取所有 .env / .env.[mode] / .env.local 等文件中的变量（含 VITE_ 前缀的）
  const env = loadEnv(mode, process.cwd(), '')

  // 代理目标：优先用环境变量，回退到默认值
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8083'
  const aiApiTarget = env.VITE_AI_API_TARGET || 'http://localhost:8050'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          ws: true
        },
        '/ai-api': {
          target: aiApiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ai-api/, '')
        }
      }
    }
  }
})
