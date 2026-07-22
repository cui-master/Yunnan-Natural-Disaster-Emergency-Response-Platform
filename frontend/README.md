# 云南省自然灾害应急响应平台 — 前端工程

> 角色 1（前端开发负责人）交付物 · 技术栈：Vue 3 + TypeScript + Vite + Pinia + Element Plus + ECharts + Leaflet

## 一、功能模块

| 模块 | 路由 | 说明 |
| --- | --- | --- |
| 灾情态势大屏 | `/dashboard` | Leaflet 灾情地图 + ECharts 统计图表 + 实时事件流 |
| 灾情上报 | `/report` | 结构化上报表单 + 图片上传（MinIO） |
| 信息审核工作台 | `/review` | 工单状态机：待核验 → 已确认 → 处置中 → 已结束 |
| 应急方案工作台 | `/plan` | AI（FastAPI）SSE 流式生成 + 引用来源 + 合规审查 + 人工修改 |
| 救援资源查询 | `/resource` | 资源检索、多选调度、冲突检测 |
| 调度看板 | `/dispatch` | 调度记录、KPI、取消释放 |
| 知识库管理 | `/knowledge` | 文档入库（分块向量化）/ 删除 |
| 审计日志 | `/audit` | 操作审计查询 |
| 系统管理 | `/system` | 用户 / 角色权限(RBAC) / 系统配置 |

## 二、本地运行

```bash
cd frontend
npm install
npm run dev        # 默认 http://localhost:5173
```

> 默认启用 **Mock 联调层**（`VITE_USE_MOCK=true`），无需后端即可完整演示。

### 演示账号（密码均为 123456）
- `reporter` 信息员
- `commander` 指挥人员
- `resource` 资源管理员
- `admin` 系统管理员

## 三、对接真实后端 / AI 服务

1. 将 `.env` 中 `VITE_USE_MOCK` 改为 `false`；
2. 后端（Spring Boot）监听 `:8080`，AI 服务（FastAPI）监听 `:8000`；
3. `vite.config.ts` 已配置代理：`/api` → 8080，`/ai` → 8000，`/ws` → WebSocket；
4. 接口契约见 `src/types/index.ts`，与后端 Swagger / AI OpenAPI 对齐。

## 四、目录结构

```
src/
├── api/            # 请求封装 + 各业务接口 + mock 联调层
├── components/     # DisasterMap / EChart / EventTicker / StatCard
├── layout/         # BasicLayout / Sidebar / HeaderBar
├── router/         # 路由表 + RBAC 元信息
├── stores/         # Pinia: auth / disaster / resource / plan / knowledge
├── types/          # 全局类型契约（接口对齐）
├── utils/          # auth / sse / websocket
└── views/          # 各业务页面
```

## 五、构建

```bash
npm run build      # 产物输出 dist/
npm run preview    # 本地预览构建产物
npm run type-check # TypeScript 类型检查
```

## 六、交付文档
- `docs/前端测试用例.md`
- `docs/前端测试报告.md`
