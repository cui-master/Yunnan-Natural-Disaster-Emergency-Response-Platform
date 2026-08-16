# 云南省自然灾害应急协同决策平台

基于微服务架构的自然灾害应急响应与协同决策系统，面向云南省多灾种（地震、洪涝、地质、气象等）场景，覆盖从灾情上报、态势感知、AI 方案生成、资源调度到知识库管理的全流程闭环。

系统融合 **知识图谱（Neo4j）+ Dify Agent 工作流 + 大语言模型**，实现智能应急方案生成与物资优化调度，并支持多角色协同、实时事件推送与可视化决策大屏。

---

## 核心特性

- **多角色协同**：信息员 / 指挥员 / 资源管理员 / 系统管理员四类角色，按职能分配差异化工作台与权限
- **AI 智能决策**：基于 Dify 工作流 + DeepSeek / 通义千问大模型，自动生成处置方案、风险评估与调度建议
- **知识图谱**：Neo4j 存储灾害-资源-地点-队伍关系，支持图谱可视化（vis-network）与 SQL 双向同步
- **实时态势**：WebSocket + SSE 双通道事件推送，灾情状态机驱动全流程流转
- **数据管道**：FastAPI 爬虫按需抓取天气与灾害数据，为 Dify 工作流提供实时输入
- **知识库**：Dify Dataset 承载应急预案与风险评估文档，支持检索增强生成（RAG）
- **可视化大屏**：ECharts 态势大屏 + 图谱网络图，多维度呈现灾情与资源分布
- **一键部署**：Docker Compose 编排全部服务，含健康检查与数据持久化

---

## 系统架构

```
┌─────────────┐     /api      ┌──────────────┐
│  frontend   │──────────────▶│   backend    │  Spring Boot:8083
│  Nginx:80   │   (反向代理)   │              │
└─────────────┘               └──────┬───────┘
                                     │
        ┌────────────┬───────────────┼───────────────┬────────────┐
        ▼            ▼               ▼               ▼            ▼
   ┌─────────┐  ┌─────────┐    ┌──────────┐   ┌──────────┐  ┌─────────┐
   │  MySQL  │  │  Neo4j  │    │  Redis   │   │ai-service│  │data-    │
   │  :3306  │  │  :7687  │    │  :6379   │   │  :8050   │  │pipeline │
   └─────────┘  └─────────┘    └──────────┘   └────┬─────┘  │  :8000  │
                                                   │        └─────────┘
                                                   ▼
                                            ┌─────────────┐
                                            │ Dify + LLM  │
                                            └─────────────┘
```

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| frontend | 8088 → 80 | Vue3 + Vite + Element Plus | 前端界面，Nginx 反向代理 `/api` |
| backend | 8083 | Spring Boot 3.2.7 + Java 21 | 主后端，业务编排与权限控制 |
| ai-service | 8050 | FastAPI + Neo4j + Dify | AI 服务，工作流代理 + LLM 降级 |
| data-pipeline | 8000 | FastAPI + 爬虫 + SSE | 数据管道，实时灾害数据采集 |
| mysql | 3307 → 3306 | MySQL 8.0 | 业务数据库 `emergency_auth` |
| neo4j | 7474 / 7687 | Neo4j 5.23 + APOC | 图数据库（Browser / Bolt） |
| redis | 6379 | Redis 7 | 缓存（可选） |

---

## 技术栈

**前端**：Vue 3 / Vite 5 / Vue Router 4 / Pinia / Element Plus / ECharts / vue-echarts / vis-network / axios / dayjs / Sass

**后端**：Spring Boot 3.2.7 / Java 21 / Spring Security / Spring WebSocket / Spring Retry / MyBatis-Plus / MySQL / Neo4j Java Driver / Redis / JWT(jjwt) / Knife4j(Swagger) / Hutool / Lombok / Spring AOP

**AI 服务**：FastAPI / Uvicorn / Pydantic / Neo4j Python Driver / httpx / APScheduler / Loguru / Dify Workflow / DeepSeek / 通义千问

**数据管道**：FastAPI / sse-starlette / BeautifulSoup4 / lxml / aiohttp / APScheduler / Dify Dataset

**基础设施**：Docker / Docker Compose / Nginx

---

## 项目结构

```
第六组_云南自然灾害应急协同决策平台/
├── frontend/              # Vue3 前端
│   ├── src/
│   │   ├── api/           # 接口封装（auth、index）
│   │   ├── views/         # 按角色组织：reporter/ commander/ resource/ admin/
│   │   ├── layouts/       # 横向 / 竖向布局
│   │   ├── router/        # 路由 + 角色守卫
│   │   ├── store/         # Pinia 状态
│   │   └── utils/         # 请求封装、常量
│   ├── nginx.conf         # 生产环境反向代理
│   └── vite.config.js     # 开发代理 /api → 8083，/ai-api → 8050
│
├── backend/               # Spring Boot 后端
│   └── src/main/java/com/yunnan/emergency/
│       ├── controller/    # Auth/Incident/Resource/Dispatch/Neo4j/Ai/SSE... 30+ 控制器
│       ├── service/       # 业务服务（含状态机、资源锁、SQL-Neo4j 同步、Dify 同步）
│       ├── entity/        # 领域实体
│       ├── mapper/        # MyBatis-Plus Mapper
│       ├── config/        # Security / Neo4j / WebSocket / Knife4j / MybatisPlus
│       ├── security/      # JWT 过滤器
│       ├── websocket/     # 事件状态实时推送
│       ├── aspect/        # 审计日志切面
│       └── common/        # Result 统一响应、错误码
│
├── ai-service/            # AI 服务（FastAPI）
│   └── app/
│       ├── api/v1/        # graph_nodes / dispatch / workflow / pipeline / knowledge_base
│       │                  # + reporter / commander / resource / admin 角色接口
│       ├── agents/        # LLM 客户端（DeepSeek / Qwen 降级）
│       ├── core/          # 配置、日志、Neo4j 客户端
│       ├── graph/         # 知识图谱仓储
│       ├── ml/            # 风险模型
│       ├── pipeline/      # 数据管道模型
│       ├── schemas/       # 调度 DTO
│       └── tasks/         # 定时任务（风险等级同步）
│
├── data-pipeline/         # 数据管道服务（FastAPI）
│   └── app/
│       ├── api/v1/        # sse / events / crawler / weather / agent / dify_admin
│       ├── crawlers/      # 爬虫基类
│       ├── core/          # 配置、日志
│       └── models/        # 数据 schema
│
├── deploy/                # 部署编排
│   ├── docker-compose.yml # 一键启动全部服务
│   ├── .env.docker.example
│   └── sql/               # schema.sql / data.sql / migrate / seed_dashboard
│
├── docs/                  # 项目文档（需求、技术、计划、测试、部署、问题诊断）
└── tests/                 # 脚本与诊断工具
```

---

## 角色与功能

| 角色 | 路由前缀 | 主要功能 |
|------|----------|----------|
| **普通信息员** reporter | `/reporter` | 灾情态势大屏、灾情上报、后端功能 |
| **应急指挥员** commander | `/commander` | 灾情态势大屏、审核事件、处置方案、调度看板、救援资源查询、灾情上报 |
| **资源管理员** resmanager | `/resource` | 灾情态势大屏、调度看板 |
| **系统管理员** admin | `/admin` | 灾情态势大屏、知识库管理、用户管理、模型管理 |

**后端能力矩阵**：认证授权、灾情事件（状态机：上报→审核→处置→归档）、资源调度（含资源锁）、应急方案、知识图谱 CRUD、知识库同步、AI 代理运行、实时推送（WebSocket + SSE）、灾情态势、天气、定时采集、审计日志、文件上传、模型管理、数据源管理、档案管理。

---

## 快速开始

### 一、Docker 一键部署（推荐）

**前置要求**：Docker 20+、Docker Compose v2、独立部署的 Dify 实例（默认端口 8080）。

```bash
# 1. 准备环境变量
cp deploy/.env.docker.example .env
# 按需修改 .env 中的密钥（生产环境务必修改 MYSQL_ROOT_PASSWORD / NEO4J_PASSWORD / JWT_SECRET / DIFY_API_KEY / DEEPSEEK_API_KEY）

# 2. 构建并启动
docker compose -f deploy/docker-compose.yml --env-file .env up -d --build

# 3. 访问平台
# 前端：       http://localhost:8088
# 后端 Swagger：http://localhost:8083/api/swagger-ui.html
# Neo4j Browser：http://localhost:7474
# AI 服务文档：  http://localhost:8050/docs
# 数据管道文档： http://localhost:8000/docs
```

MySQL 容器首次启动会自动执行 `deploy/sql/` 下的 `schema.sql`、`data.sql` 建表并灌入种子数据。

### 二、默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| reporter | 123456 | 普通信息员 |
| commander | 123456 | 应急指挥员 |
| resmanager | 123456 | 资源管理员 |
| admin | 123456 | 系统管理员 |

### 三、常用命令

```bash
docker compose -f deploy/docker-compose.yml ps                  # 查看服务状态
docker compose -f deploy/docker-compose.yml logs -f backend     # 跟踪后端日志
docker compose -f deploy/docker-compose.yml up -d --build ai-service  # 单独重建服务
docker compose -f deploy/docker-compose.yml down                # 停止全部服务
docker compose -f deploy/docker-compose.yml down -v             # 停止并清空数据卷（慎用）
```

---

## 本地开发

### 前端

```bash
cd frontend
npm install
npm run dev      # 启动开发服务器 http://localhost:3000
npm run build    # 生产构建到 dist/
```

开发模式下，Vite 自动代理：`/api` → `http://localhost:8083`，`/ai-api` → `http://localhost:8050`。如需修改目标地址，在 `frontend/.env.development` 中设置 `VITE_API_TARGET` 与 `VITE_AI_API_TARGET`。

### 后端

```bash
cd backend
mvn clean package -DskipTests
java -jar target/emergency-backend-1.0.0.jar
# 或使用 IDE 直接运行 EmergencyApplication.java
```

依赖 MySQL、Neo4j、Redis，连接信息通过环境变量或 `application.yml` 配置。

### AI 服务

```bash
cd ai-service
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env          # 配置 Neo4j / Dify / DeepSeek 密钥
python -m app.main            # 启动于 http://localhost:8050
```

### 数据管道

```bash
cd data-pipeline
python -m venv .venv_lib
.venv_lib\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main            # 启动于 http://localhost:8000
```

---

## 环境变量

核心环境变量（完整列表见 `deploy/.env.docker.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FRONTEND_PORT` | 前端对外端口 | 8088 |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | rootpass |
| `MYSQL_DATABASE` | 业务库名 | emergency_auth |
| `MYSQL_HOST_PORT` | MySQL 宿主机端口 | 3307 |
| `NEO4J_PASSWORD` | Neo4j 密码（首次初始化后不可改） | disaster2026 |
| `JWT_SECRET` | JWT 签名密钥（≥32 字节） | 预置示例 |
| `CORS_ALLOWED_ORIGINS` | 允许跨域的前端源 | localhost, localhost:8088 |
| `DIFY_BASE_URL` | Dify 实例地址 | host.docker.internal:8080 |
| `DIFY_API_KEY` | 调度方案工作流密钥 | — |
| `DIFY_DATASET_API_KEY` | 知识库数据集密钥 | — |
| `DEEPSEEK_API_KEY` | DeepSeek 模型密钥（LLM 降级） | — |
| `DEEPSEEK_MODEL` | DeepSeek 模型名 | deepseek-v4-flash |
| `JAVA_OPTS` | 后端 JVM 参数 | -Xms256m -Xmx768m |

---

## 关于 Dify

Dify 平台 **不包含** 在本编排中，需独立部署：

- **Dify 在宿主机**：保持 `DIFY_BASE_URL=http://host.docker.internal:8080`
- **Dify 在同一 Docker 网络**：改用容器名访问，如 `http://<dify容器名>:8080`

平台依赖两个 Dify 应用：

1. **调度方案工作流**（`DIFY_API_KEY`）：输入灾情事件、地点、类型、严重度、Neo4j 三元组、风险信息、视觉文本，输出处置与调度方案
2. **知识库数据集**（`DIFY_DATASET_API_KEY`）：承载「优化调度」「风险评估」两个知识库，支持 RAG 检索

---

## 数据持久化

| 卷名 | 挂载点 | 说明 |
|------|--------|------|
| mysql_data | /var/lib/mysql | MySQL 数据 |
| neo4j_data | /data | Neo4j 数据 |
| neo4j_logs | /logs | Neo4j 日志 |
| redis_data | /data | Redis 持久化 |
| uploads_data | /app/uploads | 后端上传文件 |

删除容器不会丢失数据；如需重置需执行 `docker compose down -v`。

---

## 文档

更多文档位于 `docs/` 目录：

- `DEPLOY.md` — Docker 部署指南与故障排查
- `TESTING.md` — 测试说明
- `PROBLEMS_AND_DIAGNOSTICS.md` — 问题与诊断记录
- `需求分析文档.docx` / `技术研究文档.docx` / `项目计划书.docx` / `项目开发文档.docx` / `项目测试文档.docx` / `创新性分析文档.docx`

---

## 故障排查

- **后端启动报数据库连接失败**：MySQL 健康检查通过后 backend 才启动，查看 `docker compose logs mysql` 与 `backend`
- **Neo4j 密码错误**：Neo4j 密码首次启动写入后修改 `.env` 无效，需 `docker compose down -v` 删卷重建
- **Maven 依赖超时**：Dockerfile 已内置阿里云镜像；仍超时可本地 `mvn clean package -DskipTests` 后再 `docker compose build backend`
- **前端无法访问后端 API**：确认 Nginx 反向代理指向 `backend:8083`，容器外直连使用 `http://localhost:8083/api`
