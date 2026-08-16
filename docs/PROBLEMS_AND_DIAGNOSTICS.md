# 问题与诊断报告（Problems & Diagnostics）

> 生成时间：2026-07-25
> 扫描范围：`backend/`（75 个 Java 源文件）、`frontend/`（Vue 3 项目）、`data-pipeline/`（FastAPI 项目）
> 扫描方式：只读静态分析 + 全局 grep 验证

---

## 一、严重程度分布

| 级别 | 数量 | 含义 |
|------|------|------|
| 🔴 CRITICAL | 7 | 必须立即修复，影响功能正确性、安全性或违反项目硬约束 |
| 🟠 WARNING | 11 | 应尽快修复，影响可维护性、健壮性或生产可用性 |
| 🔵 INFO | 9 | 可选优化，不影响功能 |

---

## 二、🔴 CRITICAL 级别问题（必须立即修复）

### C1. `AuditAspect.java` 重复 import 同名 `AuditLog` 类（注解 + 实体）

- **位置**：[AuditAspect.java](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/aspect/AuditAspect.java#L3-L4)
- **现象**：同时 import 了 `com.yunnan.emergency.annotation.AuditLog`（注解）和 `com.yunnan.emergency.entity.AuditLog`（实体），依赖编译器按 `new` 关键字消歧
- **风险**：任何编译器升级或新增对 `AuditLog` 简单名的引用都会立即触发 `collides with another import statement` 编译错误
- **修复**：删除实体 import，局部变量改名 `log` → `auditLog`

### C2. `SqlNeo4jSyncService` 9 个同步方法是"孤儿方法"，**违反"SQL/Neo4j 一致"硬约束**

- **位置**：[SqlNeo4jSyncService.java](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/service/SqlNeo4jSyncService.java#L48-L157)
- **现象**：`syncIncidentCreate/Update/Delete`、`syncResourceCreate/Update/Delete`、`syncDispatchOrderCreate/Update/Delete` 共 9 个方法**仅自身定义处出现，无任何 Controller/Service 调用**
- **影响**：`IncidentController`、`ResourceController`、`DispatchOrderController`、`IncidentReportController` 直接操作 Mapper 写 SQL，**没有触发 Neo4j 同步**
- **违反约束**：`project_memory.md` 中的硬约束"SQL 和 Neo4j 数据必须一致"
- **修复**：在 3 个 Controller 的 create/update/delete 方法中注入 `SqlNeo4jSyncService`，SQL 写入成功后调用对应 `syncXxx` 方法

### C3. 前端 Layout 顶栏硬编码红色 "Mock 数据" 标签

- **位置**：[HorizontalLayout.vue:34](file:///f:/桌面/disaster/frontend/src/layouts/HorizontalLayout.vue#L34)、[VerticalLayout.vue:48](file:///f:/桌面/disaster/frontend/src/layouts/VerticalLayout.vue#L48)
- **现象**：两个布局顶栏都无条件渲染 `<el-tag type="danger">Mock 数据</el-tag>`，**没有 `v-if="useMock"` 守卫**
- **影响**：`.env` 已设 `VITE_USE_MOCK=false`，但生产环境用户依然会看到醒目的 "Mock 数据" 提示，造成严重误导
- **修复**：删除标签，或加 `v-if="useMock"`（`useMock` 从 `import.meta.env.VITE_USE_MOCK` 计算）

### C4. `ModelManage.vue` 的 `testConnection()` 是纯前端假交互

- **位置**：[ModelManage.vue:305-310](file:///f:/桌面/disaster/frontend/src/views/admin/ModelManage.vue#L305-L310)
- **现象**：测试连通性按钮固定 1 秒后假成功，未走后端，未受 `useMock` 守卫
- **影响**：生产环境下会欺骗用户
- **修复**：接入真实后端 `/admin/models/{id}/test`，或加 `v-if="useMock"` 隐藏按钮

### C5. 前端 mock 模块静态 import 未被守卫，被打包进生产 bundle

- **位置**：[api/index.js:2](file:///f:/桌面/disaster/frontend/src/api/index.js#L2)、[api/auth.js:2](file:///f:/桌面/disaster/frontend/src/api/auth.js#L2)
- **现象**：`import mock from '@/mock'` 是顶层静态 import，即使 `VITE_USE_MOCK=false`，整个 `src/mock/index.js`（327 行假数据）仍会被打包进生产 bundle
- **影响**：生产包体积膨胀，且 mock 内的敏感假数据（用户名/密码 `123456`、手机号、API key）会泄露到前端产物
- **修复**：改为动态 import `const mock = useMock ? await import('@/mock') : null`，或直接删除 `src/mock/`

### C6. Dify API Key 硬编码在源码中并提交进仓库

- **位置**：
  - [dify_client.py:34-35](file:///f:/桌面/disaster/data-pipeline/app/services/dify_client.py#L34-L35)
  - [.env.example:3-4](file:///f:/桌面/disaster/data-pipeline/.env.example#L3-L4)
  - [tests/conftest.py:34-35](file:///f:/桌面/disaster/data-pipeline/tests/conftest.py#L34-L35)
- **现象**：真实的 `app-ELApZzN6iN2LXRfEU2ckM62R` 和 `dataset-sqapyDa5F43pjdaBdkwYn3VU` 作为 `os.getenv` 默认值写入源码
- **影响**：任何能读到代码的人都能拿到 Key，凭证泄露
- **修复**：默认值改为空字符串或占位符；**立即在 Dify 控制台轮换这两个 Key**；用 `.env` 注入真实值

### C7. `.env` 中的 Dify 配置根本不会被读取（无 `load_dotenv` 调用）

- **位置**：[dify_client.py:33-39](file:///f:/桌面/disaster/data-pipeline/app/services/dify_client.py#L33-L39) + 全项目无 `load_dotenv()`
- **现象**：`DifyConfig` 在 import 时一次性 `os.getenv(...)` 求值；pydantic-settings 的 `Settings` 不写 `os.environ`；`Settings` 类完全无 `DIFY_*` 字段
- **影响**：即使用户在 `.env` 写 `DIFY_BASE_URL=...`，`DifyConfig` 也始终回退到硬编码默认值 `http://localhost:8080`。配置文件形同虚设
- **修复**：在 `app/__init__.py` 或 `main.py` 顶部加 `from dotenv import load_dotenv; load_dotenv()`；或把 `DIFY_*` 并入 `Settings`

---

## 三、🟠 WARNING 级别问题（应尽快修复）

### W1. Dify 工作流不支持 SSE 流式进度推送（用户关注点）

- **位置**：[dify_client.py:88-103](file:///f:/桌面/disaster/data-pipeline/app/services/dify_client.py#L88-L103)
- **现象**：`run_workflow_async` 硬编码 `"response_mode": "blocking"`，方法签名不接受 `response_mode`；3 个 agent 接口都直接 `await`，期间前端只能干等
- **影响**：长耗时工作流（事件抽取/方案审查）期间前端无任何反馈，违反项目硬约束"SSE 推送 AI 生成进度"
- **修复**：新增 `run_workflow_streaming` 方法，`response_mode="streaming"`，逐行读 Dify SSE 流（`workflow_started`/`node_started`/`node_finished`/`workflow_finished`），通过 `sse_manager` 推给前端

### W2. Dify 调用零重试机制

- **位置**：[dify_client.py:74-103, 154-205](file:///f:/桌面/disaster/data-pipeline/app/services/dify_client.py#L74-L205)
- **现象**：所有 Dify 调用都是单次请求，失败即 `raise`；对比天气爬虫有 `MAX_RETRIES=3` + 指数退避，Dify 客户端却没有
- **影响**：Dify 偶发 502/超时会导致 agent 接口直接 502，违反项目硬约束"异常重试"
- **修复**：引入 `tenacity` 或手写重试，对 `httpx.ConnectError`/`ReadTimeout`/5xx 做指数退避（3 次，间隔 1/2/4 秒）

### W3. `dify_admin` 在 async handler 中调用同步阻塞 HTTP

- **位置**：[dify_admin.py:41-42, 58, 67, 81, 91](file:///f:/桌面/disaster/data-pipeline/app/api/v1/dify_admin.py#L41-L91)
- **现象**：async def 处理器中调用 `dify_client.check_workflows_status()` / `list_datasets()` 等同步方法（内部用 `httpx.Client`）；`check_workflows_status` 还串行 ping 3 个工作流
- **影响**：高并发下事件循环被卡死，单次接口可能阻塞 30 秒
- **修复**：把 dataset 系列改为 `async` + `httpx.AsyncClient`；或用 `await asyncio.to_thread(...)`；3 个 ping 并发

### W4. `Neo4jConfig.@PreDestroy` 方法未真正关闭 Driver

- **位置**：[Neo4jConfig.java:41-44](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/config/Neo4jConfig.java#L41-L44)
- **现象**：方法体只有日志，没有 `driver.close()`；`Neo4jConfig` 类本身也没持有 Driver 字段
- **影响**：死代码且具误导性，目前依赖 Spring 对 `AutoCloseable` Bean 的自动销毁兜底
- **修复**：删除该 `@PreDestroy` 方法，或注入 `Driver` 字段后调用 `driver.close()`

### W5. `AiAgentService` 使用裸 `new Thread()` 而非 `@Async`

- **位置**：[AiAgentService.java:117-132](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/service/AiAgentService.java#L117-L132)
- **现象**：`EmergencyApplication` 已启用 `@EnableAsync`，但此处用裸 `new Thread(...)` 启动任务，绕过 Spring 线程池管理
- **影响**：无法被监控、无法优雅关闭、无异常 handler 兜底
- **修复**：把 `executeWithRetry` 改为 `@Async` 方法，或注入 `TaskExecutor`

### W6. `EventPushService` 误导性 `@Autowired(required = false)`

- **位置**：[EventPushService.java:23-27](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/service/EventPushService.java#L23-L27)
- **现象**：`WebSocketSessionManager` 标了 `@Component`，Bean 永远存在，`required = false` 多余且误导；`final` 字段允许 null 赋值也矛盾
- **修复**：删除 `@Autowired(required = false)`，改用 `@RequiredArgsConstructor` 风格

### W7. `AuditAspect` 局部变量 `log` 遮蔽 `@Slf4j` 静态字段

- **位置**：[AuditAspect.java:71](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/aspect/AuditAspect.java#L71)
- **现象**：`AuditLog log = new AuditLog();` 遮蔽 `@Slf4j` 生成的 `log` 字段
- **修复**：局部变量改名 `auditLog`（与 C1 一并修复）

### W8. `Report.vue` 城市/区县/坐标全部硬编码

- **位置**：[Report.vue:91-94, 195-199, 209](file:///f:/桌面/disaster/frontend/src/views/reporter/Report.vue#L91-L209)
- **现象**：城市列表硬编码 16 个云南地市；区县下拉框是 "示例区"/"示例县" 占位文字；表单初始坐标写死昆明 `102.7100, 25.0400`
- **影响**：上报时会带假坐标和占位区县提交，污染数据库
- **修复**：城市改调 `getWeatherCities()`；区县监听 `form.city` 变化调 `getWeatherDistricts(city)`；坐标默认置空或调高德定位

### W9. `BackendFunctions.vue` 两个 catch 块静默吞错

- **位置**：[BackendFunctions.vue:297, 523](file:///f:/桌面/disaster/frontend/src/views/reporter/BackendFunctions.vue#L297)
- **现象**：`} catch { /* mock 模式忽略 */ }` 在 `useMock=false` 生产环境下会吞掉真实后端错误
- **影响**：用户看不到"加载失败"提示，问题被掩盖
- **修复**：改为 `catch (e) { ElMessage.error('加载失败'); console.error(e) }`，仅 `useMock=true` 时静默

### W10. CORS 配置不合规：`allow_origins=["*"]` + `allow_credentials=True`

- **位置**：[main.py:39-45](file:///f:/桌面/disaster/data-pipeline/app/main.py#L39-L45)
- **现象**：通配符 origin 与 credentials 同时启用违反 CORS 规范，浏览器会拒绝带凭证的响应
- **修复**：要么 `allow_origins=["显式域名列表"]` + `allow_credentials=True`，要么 `allow_origins=["*"]` + `allow_credentials=False`

### W11. 健康检查把 HTTP 500 当作 "reachable"

- **位置**：[dify_client.py:135](file:///f:/桌面/disaster/data-pipeline/app/services/dify_client.py#L135)
- **现象**：`reachable = resp.status_code in (200, 400, 422, 500)`，500 表示工作流内部出错却被算"可达"
- **修复**：只把 200/400/422 视为可达；500 单独标记 `reachable=True, healthy=False`

---

## 四、🔵 INFO 级别问题（可选优化）

| 编号 | 位置 | 问题 |
|------|------|------|
| I1 | [IncidentStateMachineService.java:149](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/service/IncidentStateMachineService.java#L149) | 冗余的 `IncidentStateMachineService.log.warn(...)` 静态引用，直接 `log.warn` 即可 |
| I2 | [ResourceLockService.java:92](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/service/ResourceLockService.java#L92) | 与状态码字面量 `200` 耦合，建议用 `ResultCode.SUCCESS.getCode()` |
| I3 | [IncidentStatus.java:47](file:///f:/桌面/disaster/backend/src/main/java/com/yunnan/emergency/enums/IncidentStatus.java#L47) | `PROCESSING → CONFIRMED` 反向状态流转，可能不符合工单状态机单向语义 |
| I4 | [mock/index.js](file:///f:/桌面/disaster/frontend/src/mock/index.js) | 327 行假数据残留（依赖 C5 修复后整体删除） |
| I5 | [PlanWorkbench.vue:188](file:///f:/桌面/disaster/frontend/src/views/commander/PlanWorkbench.vue#L188)、[Report.vue:54](file:///f:/桌面/disaster/frontend/src/views/reporter/Report.vue#L54) | placeholder 含 "XX" 字样，建议改真实示例 |
| I6 | [api/index.js:462, 491](file:///f:/桌面/disaster/frontend/src/api/index.js#L462) | SSE/WS URL 手动拼 `/api` 前缀，绕过 axios baseURL |
| I7 | [.env.development:2-3](file:///f:/桌面/disaster/frontend/.env.development#L2-L3) | 高德 Key 明文提交仓库，security code 应通过后端代理下发 |
| I8 | [Dockerfile:8](file:///f:/桌面/disaster/data-pipeline/Dockerfile#L8) | 镜像不含 `.env` 且无 `load_dotenv`，生产部署配置失效 |
| I9 | [requirements.txt:12,15](file:///f:/桌面/disaster/data-pipeline/requirements.txt#L12) | `aiohttp`、`requests` 未被使用，死依赖 |

---

## 五、验证通过的检查项（无问题）

### 后端
- ✅ **循环依赖已正确解耦**：`SecurityConfig → JwtAuthenticationFilter → UserServiceImpl → BCryptPasswordEncoder ← PasswordEncoderConfig`，无环
- ✅ **所有 Bean 都有定义**：15 个 Mapper、13 个 Service、22 个 Controller、8 个 Config 均 `@Bean`/`@Service`/`@Component`/`@Mapper` 齐全
- ✅ **实体字段引用全部正确**：`Resource.capacity`、`Incident.status/reviewerId/occurredAt` 等所有 getter 调用均存在
- ✅ **Mapper 接口全部正确**：15 个 Mapper 都继承 `BaseMapper<对应实体>`，泛型实参与 `@TableName` 一致
- ✅ **配置完整性**：`application.yml` 与 `application-test.yml` 包含所有 `@Value` 引用属性

### 前端
- ✅ **配置层干净**：`VITE_USE_MOCK=false`、无 mock 插件、axios `baseURL='/api'`、代理配置正确
- ✅ **API 路径无重复前缀**：所有函数用 `request({ url: '/auth/login' })` 形式，最终拼为 `/api/auth/login`
- ✅ **DispatchBoard.vue 已走真实 Neo4j 接口**，无 "XX灾区（示例）" 占位符

### 数据管道
- ✅ **路由前缀无重复**：`api_router` 统一前缀 `/api/v1`，各子 router 仅挂子前缀（`/agent`、`/admin`、`/weather`、`/events`、`/crawler`），最终路径如 `/api/v1/agent/extract-incident` 符合文档声明
- ✅ **天气爬虫完整**：URL 格式 `tianqihoubao.com/yubao/{slug}.html`，覆盖昨天到后天共 4 天，云南 16 地州 slug 齐全，有 `MAX_RETRIES=3` 重试
- ✅ **SSE 端点路径正确**：`/api/v1/sse`，用 `EventSourceResponse`，`ping=15`
- ✅ **必需依赖齐全**：`fastapi`、`uvicorn`、`httpx`、`beautifulsoup4`、`pydantic`、`sse-starlette`、`loguru`、`apscheduler` 均在 requirements.txt

---

## 六、修复优先级建议

| 优先级 | 问题编号 | 一句话修复 |
|--------|----------|------------|
| **P0（立即）** | C6 | 立即在 Dify 控制台轮换两个 API Key，删除源码硬编码 |
| **P0（立即）** | C7 | 在 `app/__init__.py` 加 `load_dotenv()`，让 `.env` 生效 |
| **P0（立即）** | C2 | 在 3 个 Controller 注入 `SqlNeo4jSyncService`，CUD 后调 `syncXxx` |
| **P0（立即）** | C3 | 删除两个 Layout 的 "Mock 数据" 红标签 |
| **P0（立即）** | C4 | `ModelManage.vue` 接真实测试接口或隐藏按钮 |
| **P0（立即）** | C1 | 删除 `AuditAspect` 重复 import，局部变量改名 |
| **P1（高）** | C5 | mock 模块改动态 import，生产构建剔除 |
| **P1（高）** | W1 | Dify 工作流改 streaming 模式，接 SSE 推送进度 |
| **P1（高）** | W2 | Dify 调用加重试机制 |
| **P1（高）** | W8 | `Report.vue` 城市/区县/坐标改动态加载 |
| **P2（中）** | W3, W4, W5, W6, W7, W9, W10, W11 | 健壮性、配置清理 |
| **P3（低）** | I1–I9 | 文案优化、死代码清理 |

---

## 七、关键结论

1. **三大基础设施已就位**：循环依赖已解耦、Neo4j/SQL 双库 Mapper/Service/Controller 齐全、Dify 客户端能跑通基础调用。
2. **最严重的功能缺口是 C2**：`SqlNeo4jSyncService` 写了同步逻辑但没接入业务流程，"SQL/Neo4j 一致"硬约束**实际未落地**，必须优先修复。
3. **最严重的安全问题是 C6**：真实 Dify API Key 已泄露到源码和 `.env.example`，必须立即轮换。
4. **最显眼的前端残留是 C3**：Layout 顶栏的 "Mock 数据" 红标签会直接显示给生产用户。
5. **最隐蔽的配置陷阱是 C7**：`.env` 文件形同虚设，所有 Dify 配置走硬编码默认值，部署到任何非 localhost 环境都会失效。
6. **用户最关注的 SSE 进度推送（W1）尚未实现**：Dify 工作流目前只支持 blocking 模式，违反"SSE 推送 AI 生成进度"硬约束。

---

## 八、后台任务状态

启动了 3 个 Vite 开发服务器（端口 3000）作为本地预览，均成功启动：

```
job-edd5e8f6: Vite ready in 2576ms
job-c30674db: Vite ready in 2631ms（.env.development 修改后自动重启）
job-f62bff49: Vite ready in 1969ms
```

> 注意：3 个实例同时占用 3000 端口会冲突，实际只需保留 1 个。建议停掉多余实例。
