# 云南自然灾害应急协同决策平台（MVP 垂直切片）

> 统一系统架构下的「选题一」最小可行实现。目标是端到端跑通一条业务闭环：
> **灾情上报 → 多源核验 → 风险研判 → 方案生成(AI) → 人工审批 → 资源调度 → 过程记录 → 事件归档**

## 技术栈（按规格落地）

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Element Plus + ECharts |
| 业务后端 | Spring Boot 2.7.18（Java 8）+ MyBatis-Plus 3.5.3.2 |
| AI 服务 | Python + FastAPI（本期为可替换的桩，预留 LangChain/LlamaIndex） |
| 关系/空间库 | PostgreSQL 15 + PostGIS 3.4 |
| 向量库 | pgvector（预案分块与文档向量；不替代业务库） |
| 缓存/任务 | Redis（MVP 仅用缓存，Celery/RQ 后续扩展） |
| 文件存储 | MinIO（MVP 预留，图片上传接口先落本地/对象存储占位） |
| 部署 | Docker Compose + Nginx |
| 接口文档 | springdoc-openapi / Swagger |
| 测试 | JUnit + Vitest + Playwright（后续） |

> 说明：全局默认技术栈为 MySQL，但本项目规格的「数据库设计」段明确要求
> **PostgreSQL/PostGIS + pgvector**，故本项目以该指令为准。

## 目录结构

```
云南自然灾害应急协同决策平台/
├── backend/            # Spring Boot 业务后端
├── ai-service/         # Python FastAPI AI 服务（桩）
├── frontend/           # Vue3 前端
├── db/                 # 数据库 Dockerfile（postgis + pgvector）
├── sql/                # 初始化 SQL（建表 + 种子数据）
├── nginx/              # 反向代理配置
├── docker-compose.yml  # 一键编排
└── README.md
```

## 快速开始（本地开发）

### 0. 前置
- Docker 29+（用于起 PostgreSQL/PostGIS/pgvector、Redis、MinIO）
- Java 8（项目自带 Maven Wrapper，无需预装 Maven）
- Node 22（前端）

### 1. 启动基础设施
```bash
docker compose up -d db redis minio
# 等待 db healthy 后，init.sql 会自动执行（或通过 psql 手动执行 sql/init.sql）
```

### 2. 启动 AI 服务
```bash
cd ai-service
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

### 3. 启动业务后端
```bash
cd backend
./mvnw spring-boot:run        # Windows: mvnw.cmd spring-boot:run
# 或先打包：./mvnw package -DskipTests
```
- 接口文档：http://localhost:8080/swagger-ui.html
- 默认账号（密码均为 `123456`）：
  - `reporter` 普通信息员
  - `commander` 应急指挥人员
  - `resmanager` 资源管理员
  - `admin` 系统管理员

### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
```

## MVP 角色与权限
- 普通信息员：提交灾情上报
- 应急指挥人员：审核事件、生成/审批处置方案
- 资源管理员：维护人员/车辆/物资/避难所、查看调度看板
- 系统管理员：用户/知识库/数据源管理（MVP 先预留）

## 版本与演进
本期为「纵切 MVP」，后续按规格补齐：灾情态势地图与实时大屏、SSE 推送 AI 进度、
WebSocket 事件状态、RAG 检索预案、定时采集公开预警/气象、完整 RBAC 与审计。
