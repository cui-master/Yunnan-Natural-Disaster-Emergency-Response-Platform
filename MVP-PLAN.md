<<<<<<< HEAD
# 云南自然灾害应急协同决策平台 — 完整系统实施计划

> 状态图例：✅ 已完成 ｜ 🟡 设计稿/部分代码已有，待落地或接入 ｜ ⬜ 待办
> 本文档由「MVP 垂直切片」升级为「完整系统分阶段实施计划」：一期为已交付的 MVP 闭环，二期为完整系统核心能力，三期为智能与扩展。

---

## 0. 系统总览

**四角色**：信息员（上报）｜指挥（审核+方案+调度）｜资源管理员（人/车/物/避难所）｜系统管理员（知识库+用户+系统）。

**服务拓扑**：
```
前端 Vue3+Vite (5173, 四套角色主题)
        │  /api/* 按路径分发
┌───────┴───────────────────────────────────────────┐
│  report-service    :8091  信息员上报               │
│  command-service   :8092  指挥(事件/方案/调度/WS) │
│  resource-service  :8093  资源管理                 │
│  admin-service     :8094  认证/用户/知识库/审计    │
│       │ (common 共享库：实体/Mapper/双数据源/JWT)  │
└───────┬───────────────────────────────────────────┘
         │ 调用
   ai-service(FastAPI :8001, Agent方案 + Dify RAG)   ┐
   data-pipeline(FastAPI :8000, 爬虫+SSE推送)        ┘ 外部智能/数据
         │
   PostgreSQL+PostGIS+pgvector(业务) │ MySQL(认证) │ Redis │ MinIO │ Neo4j(路网/资源图谱)
```

**技术栈**：后端 Spring Boot 2.7.18 + MyBatis-Plus 3.5.3.2（Java8，Maven 多模块）；AI/数据服务 FastAPI；前端 Vue3 + Vite + Element Plus + ECharts + Leaflet。

---

## 1. 一期 · MVP 垂直切片（✅ 已交付）

端到端闭环：`灾情上报 → 后端校验 → 多源核验(桩) → 风险研判(桩) → RAG检索预案(桩) → Agent生成方案(调AI服务) → 人工审批 → 资源调度(锁定/冲突检测) → 过程记录(审计) → 事件归档`。

> MVP 中「多源核验 / 风险研判 / RAG 检索」以桩（stub）实现保证闭环可跑通；「Agent 生成方案」真实调用 FastAPI AI 服务（桩返回结构化方案，预留 LLM 接入点）。

### 1.1 服务划分
- **4 个 backend 系统**（Maven 多模块，共享 `common` 库，独立 jar/端口，共享同一 PG 业务库 + MySQL 认证库，JWT 无状态跨系统校验）。
- **ai-service**（FastAPI）：无状态，接收事件上下文，返回结构化应急方案。
- **frontend**（Vue3）：面向 4 类角色的操作界面，四套差异化主题。

### 1.2 数据库（PostgreSQL + PostGIS + pgvector）
核心表：`users`、`roles`、`incidents`、`incident_reports`、`locations`、`resources`、`dispatch_orders`、`emergency_plans`、`data_sources`、`agent_runs`、`citations`、`audit_logs`。
- `locations.geom` 用 PostGIS `geometry(Point,4326)`，风险范围用 Polygon。
- `plan_chunks` 用 pgvector `vector(1536)` 存预案分块（预留，不阻断主流程）。

### 1.3 状态机（incidents.status）
=======
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
>>>>>>> feature-cui
```
PENDING_VERIFY(待核验) → CONFIRMED(已确认) → IN_PROGRESS(处置中) → CLOSED(已结束)
                 ↘ REJECTED(已驳回，可重新上报)
```
仅允许合法跃迁，非法转换抛 `BizException`。

<<<<<<< HEAD
### 1.4 资源调度与冲突检测
- 调度前对资源做「锁定(LOCKED)」，占用 available。
- 冲突检测：同一资源 available < 需求 时标记 CONFLICT。
- 处置结束释放资源（available 回补）。

### 1.5 一期接口契约（摘要）
=======
## 5. 资源调度与冲突检测
- 调度前对资源做「锁定(LOCKED)」，占用 available。
- 冲突检测：同一资源在同一事件或多事件间 available < 需求 时标记 CONFLICT。
- 处置结束释放资源（available 回补）。

## 6. 接口契约（摘要）
>>>>>>> feature-cui
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

<<<<<<< HEAD
### 1.6 一期验收标准（✅ 全部达成）
=======
## 7. 本期不做（后续迭代）
地图态势大屏、ECharts 实时大屏、SSE 完整进度条、WebSocket 全量推送、
真实 LangChain RAG、定时气象/预警采集、MinIO 真实上传、完整审计 UI、Playwright E2E。

## 8. 验收标准
>>>>>>> feature-cui
1. 信息员可提交上报，事件进入「待核验」。
2. 指挥确认后事件进入「已确认」，可一键调 AI 生成方案。
3. 方案返回后指挥可人工修改并审批，事件进入「处置中」。
4. 基于方案对资源锁定并生成调度单，冲突可被发现。
5. 指挥归档事件，资源释放，事件进入「已结束」，全程写入审计日志。
<<<<<<< HEAD

---

## 2. 二期 · 完整系统核心能力（进行中）

原 MVP「本期不做」清单升级为二期正式范围。下表标注当前完成度。

### 2.1 灾情态势可视化大屏（✅ 已完成）
- 暗色全屏指挥中心风格（顶部标题栏+实时时钟+链路状态 → 发光 KPI → 三栏：类型饼图/地州柱状 | 态势地图 | 实时事件流/7日趋势）。
- 地图瓦片换为国内可访问源 + `invalidateSize`/ResizeObserver 修复灰屏；图表 ResizeObserver 自适应。
- 入口：菜单「灾情态势大屏」→ `/dashboard`（不新增路由，沿用现有）。

### 2.2 实时链路增强（⬜ 待办）
- SSE 完整进度条：方案生成 `/plan` 的 SSE 当前仅推送最终结果，需补齐「核验→研判→RAG→生成→审批」各阶段进度事件并在前端渲染进度条。
- WebSocket 全量推送：当前 WS 仅覆盖指挥/资源角色基础状态；扩展为全角色事件/资源/方案变更的全量推送与前端订阅。

### 2.3 真实 RAG 知识库（🟢 上传全链路已落地，RAG 检索增强待补）

> 用户需求「第三步(前端交互) + 第四步(查询/删除等扩展接口)，要求所有都有对应数据库」——已全部完成。

- **数据库（✅ 两张表，DB 为唯一真源）**
  - `knowledge_bases`（知识库注册表）：`id, kb_key, kb_name, dataset_id, description, created_at, updated_at`，已种子化两个库（`优化调度`→`a154e469-...`、`风险评估`→`03d787b9-...`，dataset_id 来自用户）。
  - `knowledge_docs`（文档表）：`id, kb_name, dify_document_id, doc_name, status(PARSING/COMPLETED/FAILED), chunk_count, word_count, uploader, uploaded_at, updated_at`。
  - 两段均写入 `sql/init.sql`（docker 重建可复现），并已在运行 PG 容器实时建表+种子化。
- **ai_service 上传模块（✅ 已实现，第二步）**：`app/agents/dify_kb_client.py`（Dify Dataset 客户端，用 **Dataset API Key**）+ `app/api/v1/knowledge_base.py`（6 端点，契约与 `docs/knowledge-base-api.md` 一致）。后端 `KnowledgeAiClient` 转发 `kb_name`+文件二进制流，自动匹配 `dataset_id` 调 Dify `create-by-file`。
  - ⚠️ 接入前须在 `AI_service/.env` 填 `DIFY_DATASET_API_KEY`（Dataset 密钥，**非**应用密钥 `app-xxx`）；Dify 在 Docker 内则 base url 写宿主机内网 IP，勿用 `127.0.0.1`。
- **后端知识库接口（✅ 已实现，第四步）** `admin-service` 的 `KnowledgeController`/`KnowledgeService`，全部 DB 支撑：
  - `GET  /api/knowledge/bases` → 读 `knowledge_bases`（前端下拉渲染，DB 真源）
  - `POST /api/knowledge/upload`（`kbName` 走 URL 查询参数 + `files` 多部件）→ 调 ai_service → 写 `knowledge_docs`
  - `GET  /api/knowledge/documents?kbName=` → 读 `knowledge_docs`
  - `DELETE /api/knowledge/documents/{docId}?kbName=` → 调 ai_service 删 Dify 文档 + 删 `knowledge_docs` 行
- **前端知识库页面（✅ 已实现，第三步）** `KnowledgeManage.vue` + `stores/knowledgeKit` + `api/knowledgeKit`：
  - 知识库下拉（优化调度/风险评估）、文件选择器（.txt/.pdf/.docx/.md 多选）、上传带进度条、文档列表(状态/分块/字数/时间)、删除二次确认。
  - 下拉项来自 `GET /api/knowledge/bases`（DB 支撑，硬编码 `KNOWLEDGE_KITS` 作兜底）。
  - ⚠️ **多部件中文坑**：Tomcat 对 multipart 表单字段默认按 ISO-8859-1 解码会乱码（`优化调度`→乱码）。已把 `kbName` 改为 **URL 查询参数**传输（URL 中文由查询串正确解码）；`KnowledgeController.normalizeKbName` 另作防御性 ISO-8859-1→UTF-8 还原兜底。
- **验证（✅ 已端到端）**：admin-service 起后，`/bases`、`/documents` 直接命中 DB（返回两库 / 空列表）；`/upload`、`/documents/{id}` DELETE 均正确转发到 ai_service 对应端点（ai_service 未起时优雅返回 502，证明中文解码与转发链路打通）。**完整成功上传**需 ai_service 运行 + Dify 配好 Dataset Key。
- **RAG 检索增强（🟡 待办）**：`/run` 方案链路在缺 `DIFY_API_KEY` 时返回 `fallback`；需建 `natural-disaster-workflow` 工作流并填 key，将预案分块写入 pgvector 打通检索增强。

### 2.4 定时气象 / 预警采集（🟡 代码已有，待接入）
- 服务：`data-pipeline`（FastAPI :8000）已实现爬虫框架 + SSE 推送（`docs/data-pipeline-api.md`、`docs/crawler-dev-guide.md`）。
- 现状：`data-pipeline/app/crawlers` 含 `MockCrawler` 与 `YunnanWeatherCrawler`/`yunnan_net` 框架；`tests/test_crawler.py`、`test_event_store.py` 已落地。
- 待办：①接入真实数据源（云南省气象局/云南网）并补充关键词与字段解析；②接 cron/定时调度触发爬取；③爬取事件自动汇入 incidents 或预警队列；④前端大屏/事件流订阅其 SSE。

### 2.5 真实文件存储 MinIO（⬜ 待办）
- 现状：docker-compose 已含 MinIO 容器，但 backend 未接入 `MinioClient`（代码无引用）。
- 待办：预案 PDF/图片、知识库原始文件经 MinIO 存取；与管理员知识库上传、指挥方案附件打通。

### 2.6 完整审计 UI（🟡 后端就绪，前端待补齐）
- 后端 `AuditController(/api/audit/logs)` 接口已可用；前端审计页面待建设（日志检索/时间线/导出）。

### 2.7 端到端测试（⬜ 待办）
- 现状：仅有 Python 单测（`tests/test_api.py`、`test_crawler.py`、`test_event_store.py`、`test_neo4j.py`）。
- 待办：引入 Playwright E2E 覆盖「上报→确认→方案→审批→调度→归档」全角色闭环。

---

## 3. 三期 · 智能与扩展（规划）

- **Neo4j 路网/资源图谱调度优化**：基于 `yn_neo4j` 图库（路网+仓库+物资+救援队+避难所）做最短路径/可达性调度；修复最短路径关系属性写法（`WHERE ALL(r IN relationships(p) WHERE r.blocked=false)`）。
- **Dify 工作流 `/run` 真链路**：补齐 key 后让方案生成走真实 LLM+RAG，而非 fallback。
- **多源核验 / 风险研判去桩**：用 data-pipeline 实时数据与 Neo4j 图谱替换 MVP 桩逻辑。
- **权限与租户细化**：省/市/县三级数据隔离、角色内细粒度权限。
- **代码治理**：当前 `ai-service` 与 `AI_service` 双目录并存，需合并避免分裂。

---

## 4. 完整系统验收标准（二期+三期目标）

1. **可视化**：灾情态势大屏全屏可用，地图/图表/实时流无灰屏、无乱码。
2. **实时**：方案生成有完整 SSE 进度条；WebSocket 全角色推送事件/资源/方案变更。
3. **智能**：指挥一键生成方案走真实 Dify RAG（非 fallback）；知识库可上传/检索预案。
4. **数据接入**：定时爬虫自动采集气象/预警并汇入平台，无需人工录入。
5. **文件**：预案/图片经 MinIO 真实存取。
6. **审计**：完整审计 UI 可检索全过程日志。
7. **质量**：Playwright E2E 覆盖核心闭环，四系统构建全绿。

---

## 附录 A · 前端设计约束（摘自 `.impeccable.md`）
- **调性**：权威、冷静、可信、克制的「指挥中心风」；**不做**炫技、娱乐化、青紫渐变/毛玻璃滥用。
- **焦点色**：应急红 `#e03e2f` 作稀缺强调（60-30-10：中性底 60% / 文字边框 30% / 强调 10%），配合等宽展示字体呈现数据。
- **字体**：中文系统字体栈（PingFang SC / Microsoft YaHei）；拉丁数字/标题可用 Sora 做渐进增强（离线降级）。
- **动效**：仅 ease-out-quart / ease-out-expo；位移只用 transform/opacity；尊重 `prefers-reduced-motion`。
- ⚠️ 注：2.1 大屏的霓虹/光斑效果需收敛，向上述约束对齐（避免青紫渐变/毛玻璃滥用）。

## 附录 B · 数据库与接口总表
- 业务库 PG（5432，`emergency`）+ 认证库 MySQL（3307）。双数据源配置已解决 `url→jdbcUrl`、MySQL8 `caching_sha2`、中文双重编码等坑。
- 全量接口契约见 1.5 及 `docs/*.md`（知识库/数据管道/爬虫）。
=======
>>>>>>> feature-cui
