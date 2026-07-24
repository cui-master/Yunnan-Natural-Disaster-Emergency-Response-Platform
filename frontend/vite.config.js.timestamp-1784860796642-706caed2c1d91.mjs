// vite.config.js
import { defineConfig } from "file:///D:/%E5%AD%A6%E4%B9%A0/%E5%AE%9E%E8%AE%AD%E6%9A%91%E5%81%87/Yunnan-Natural-Disaster-Emergency-Response-Platform/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///D:/%E5%AD%A6%E4%B9%A0/%E5%AE%9E%E8%AE%AD%E6%9A%91%E5%81%87/Yunnan-Natural-Disaster-Emergency-Response-Platform/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import path from "node:path";
var vite_config_default = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(process.cwd(), "src")
    }
  },
  server: {
    port: 5173,
    proxy: {
      // 对齐「别人更新后的多模块后端」：按服务拆分端口代理
      // admin-service :8094  auth/knowledge/audit/system
      "/api/auth": { target: "http://localhost:8094", changeOrigin: true },
      "/api/knowledge": { target: "http://localhost:8094", changeOrigin: true },
      "/api/audit": { target: "http://localhost:8094", changeOrigin: true },
      "/api/system": { target: "http://localhost:8094", changeOrigin: true },
      "/api/upload": { target: "http://localhost:8094", changeOrigin: true },
      // command-service :8092  incidents/plans/dispatch
      "/api/incidents": { target: "http://localhost:8092", changeOrigin: true },
      "/api/plans": { target: "http://localhost:8092", changeOrigin: true },
      "/api/dispatch": { target: "http://localhost:8092", changeOrigin: true },
      // report-service :8091  reports
      "/api/reports": { target: "http://localhost:8091", changeOrigin: true },
      // resource-service :8093  resources
      "/api/resources": { target: "http://localhost:8093", changeOrigin: true },
      // WebSocket(/ws/events, common 模块各服务均注册) → command 8092
      "/ws": { target: "ws://localhost:8092", ws: true }
    }
  },
  build: { outDir: "dist" }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxcdTVCNjZcdTRFNjBcXFxcXHU1QjlFXHU4QkFEXHU2NjkxXHU1MDQ3XFxcXFl1bm5hbi1OYXR1cmFsLURpc2FzdGVyLUVtZXJnZW5jeS1SZXNwb25zZS1QbGF0Zm9ybVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiRDpcXFxcXHU1QjY2XHU0RTYwXFxcXFx1NUI5RVx1OEJBRFx1NjY5MVx1NTA0N1xcXFxZdW5uYW4tTmF0dXJhbC1EaXNhc3Rlci1FbWVyZ2VuY3ktUmVzcG9uc2UtUGxhdGZvcm1cXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcuanNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0Q6LyVFNSVBRCVBNiVFNCVCOSVBMC8lRTUlQUUlOUUlRTglQUUlQUQlRTYlOUElOTElRTUlODElODcvWXVubmFuLU5hdHVyYWwtRGlzYXN0ZXItRW1lcmdlbmN5LVJlc3BvbnNlLVBsYXRmb3JtL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSc7XG5pbXBvcnQgdnVlIGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZSc7XG5pbXBvcnQgcGF0aCBmcm9tICdub2RlOnBhdGgnO1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgICBwbHVnaW5zOiBbdnVlKCldLFxuICAgIHJlc29sdmU6IHtcbiAgICAgICAgYWxpYXM6IHtcbiAgICAgICAgICAgICdAJzogcGF0aC5yZXNvbHZlKHByb2Nlc3MuY3dkKCksICdzcmMnKVxuICAgICAgICB9XG4gICAgfSxcbiAgICBzZXJ2ZXI6IHtcbiAgICAgICAgcG9ydDogNTE3MyxcbiAgICAgICAgcHJveHk6IHtcbiAgICAgICAgICAgIC8vIFx1NUJGOVx1OUY1MFx1MzAwQ1x1NTIyQlx1NEVCQVx1NjZGNFx1NjVCMFx1NTQwRVx1NzY4NFx1NTkxQVx1NkEyMVx1NTc1N1x1NTQwRVx1N0FFRlx1MzAwRFx1RkYxQVx1NjMwOVx1NjcwRFx1NTJBMVx1NjJDNlx1NTIwNlx1N0FFRlx1NTNFM1x1NEVFM1x1NzQwNlxuICAgICAgICAgICAgLy8gYWRtaW4tc2VydmljZSA6ODA5NCAgYXV0aC9rbm93bGVkZ2UvYXVkaXQvc3lzdGVtXG4gICAgICAgICAgICAnL2FwaS9hdXRoJzogeyB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwOTQnLCBjaGFuZ2VPcmlnaW46IHRydWUgfSxcbiAgICAgICAgICAgICcvYXBpL2tub3dsZWRnZSc6IHsgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDk0JywgY2hhbmdlT3JpZ2luOiB0cnVlIH0sXG4gICAgICAgICAgICAnL2FwaS9hdWRpdCc6IHsgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDk0JywgY2hhbmdlT3JpZ2luOiB0cnVlIH0sXG4gICAgICAgICAgICAnL2FwaS9zeXN0ZW0nOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5NCcsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgJy9hcGkvdXBsb2FkJzogeyB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwOTQnLCBjaGFuZ2VPcmlnaW46IHRydWUgfSxcbiAgICAgICAgICAgIC8vIGNvbW1hbmQtc2VydmljZSA6ODA5MiAgaW5jaWRlbnRzL3BsYW5zL2Rpc3BhdGNoXG4gICAgICAgICAgICAnL2FwaS9pbmNpZGVudHMnOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5MicsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgJy9hcGkvcGxhbnMnOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5MicsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgJy9hcGkvZGlzcGF0Y2gnOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5MicsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgLy8gcmVwb3J0LXNlcnZpY2UgOjgwOTEgIHJlcG9ydHNcbiAgICAgICAgICAgICcvYXBpL3JlcG9ydHMnOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5MScsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgLy8gcmVzb3VyY2Utc2VydmljZSA6ODA5MyAgcmVzb3VyY2VzXG4gICAgICAgICAgICAnL2FwaS9yZXNvdXJjZXMnOiB7IHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA5MycsIGNoYW5nZU9yaWdpbjogdHJ1ZSB9LFxuICAgICAgICAgICAgLy8gV2ViU29ja2V0KC93cy9ldmVudHMsIGNvbW1vbiBcdTZBMjFcdTU3NTdcdTU0MDRcdTY3MERcdTUyQTFcdTU3NDdcdTZDRThcdTUxOEMpIFx1MjE5MiBjb21tYW5kIDgwOTJcbiAgICAgICAgICAgICcvd3MnOiB7IHRhcmdldDogJ3dzOi8vbG9jYWxob3N0OjgwOTInLCB3czogdHJ1ZSB9XG4gICAgICAgIH1cbiAgICB9LFxuICAgIGJ1aWxkOiB7IG91dERpcjogJ2Rpc3QnIH1cbn0pO1xuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFpYyxTQUFTLG9CQUFvQjtBQUM5ZCxPQUFPLFNBQVM7QUFDaEIsT0FBTyxVQUFVO0FBQ2pCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQ3hCLFNBQVMsQ0FBQyxJQUFJLENBQUM7QUFBQSxFQUNmLFNBQVM7QUFBQSxJQUNMLE9BQU87QUFBQSxNQUNILEtBQUssS0FBSyxRQUFRLFFBQVEsSUFBSSxHQUFHLEtBQUs7QUFBQSxJQUMxQztBQUFBLEVBQ0o7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNKLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQTtBQUFBO0FBQUEsTUFHSCxhQUFhLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUEsTUFDbkUsa0JBQWtCLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUEsTUFDeEUsY0FBYyxFQUFFLFFBQVEseUJBQXlCLGNBQWMsS0FBSztBQUFBLE1BQ3BFLGVBQWUsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxNQUNyRSxlQUFlLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUE7QUFBQSxNQUVyRSxrQkFBa0IsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxNQUN4RSxjQUFjLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUEsTUFDcEUsaUJBQWlCLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUE7QUFBQSxNQUV2RSxnQkFBZ0IsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQTtBQUFBLE1BRXRFLGtCQUFrQixFQUFFLFFBQVEseUJBQXlCLGNBQWMsS0FBSztBQUFBO0FBQUEsTUFFeEUsT0FBTyxFQUFFLFFBQVEsdUJBQXVCLElBQUksS0FBSztBQUFBLElBQ3JEO0FBQUEsRUFDSjtBQUFBLEVBQ0EsT0FBTyxFQUFFLFFBQVEsT0FBTztBQUM1QixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
