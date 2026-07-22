# MVP 垂直切片 — 实施方案

## 1. 切片范围（端到端一条线）
```
灾情上报 → 后端校验 → 多源核验(桩) → 风险研判(桩) →
RAG检索预案(桩) → Agent生成方案(调AI服务) → 人工审批 →
资源调度(锁定/冲突检测) → 过程记录(审计) → 事件归档
```
MVP 中「多源核验 / 风险研判 / RAG 检索」以桩（stub）实现，保证闭环可跑通；
「Agent 生成方案」真实调用 FastAPI AI 服务（桩返回结构化方案，预留 LLM 接入点）。

## 2. 服务划分
- **backend**（Spring Boot）：唯一业务入口，持有业务库与状态机，调用 ai-service。
- **ai-service**（FastAPI）：无状态，接收事件上下文，返回结构化应急方案。
- **frontend**（Vue3）：面向 4 类角色的操作界面。

## 3. 数据库（PostgreSQL + PostGIS + pgvector）
核心表（详见 sql/init.sql）：
users、roles、incidents、incident_reports、locations、resources、
dispatch_orders、emergency_plans、data_sources、agent_runs、citations、audit_logs。
- locations.geom 用 PostGIS `geometry(Point,4326)`，风险范围用 Polygon。
- plan_chunks 用 pgvector `vector(1536)` 存预案分块（MVP 预留，不阻断主流程）。

## 4. 状态机（incidents.status）
```
PENDING_VERIFY(待核验) → CONFIRMED(已确认) → IN_PROGRESS(处置中) → CLOSED(已结束)
                 ↘ REJECTED(已驳回，可重新上报)
```
仅允许合法跃迁，非法转换抛 `BizException`。

## 5. 资源调度与冲突检测
- 调度前对资源做「锁定(LOCKED)」，占用 available。
- 冲突检测：同一资源在同一事件或多事件间 available < 需求 时标记 CONFLICT。
- 处置结束释放资源（available 回补）。

## 6. 接口契约（摘要）
| 方法 | 路径 | 说明 | 角色 |
|------|------|------|------|
| POST | /api/auth/login | 登录获取 JWT | 所有 |
| POST | /api/reports | 提交灾情上报 | 信息员 |
| GET  | /api/incidents?status= | 事件列表 | 指挥/资源/管理员 |
| POST | /api/incidents/{id}/confirm | 确认事件 | 指挥 |
| POST | /api/incidents/{id}/reject | 驳回事件 | 指挥 |
| POST | /api/incidents/{id}/plan | 调 AI 生成方案(SSE) | 指挥 |
| POST | /api/plans/{id}/approve | 审批方案 | 指挥 |
| GET/POST/PUT | /api/resources | 资源维护 | 资源管理员 |
| POST | /api/dispatch | 创建调度单(锁定+冲突检测) | 指挥/资源 |
| POST | /api/incidents/{id}/close | 归档事件(释放资源) | 指挥 |
| WS   | /ws/events | 事件状态推送 | 前端 |

## 7. 本期不做（后续迭代）
地图态势大屏、ECharts 实时大屏、SSE 完整进度条、WebSocket 全量推送、
真实 LangChain RAG、定时气象/预警采集、MinIO 真实上传、完整审计 UI、Playwright E2E。

## 8. 验收标准
1. 信息员可提交上报，事件进入「待核验」。
2. 指挥确认后事件进入「已确认」，可一键调 AI 生成方案。
3. 方案返回后指挥可人工修改并审批，事件进入「处置中」。
4. 基于方案对资源锁定并生成调度单，冲突可被发现。
5. 指挥归档事件，资源释放，事件进入「已结束」，全程写入审计日志。
