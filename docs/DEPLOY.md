# Docker 部署指南

云南省自然灾害应急响应平台 —— Docker 一键部署方案。

## 架构总览

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
   └─────────┘  └─────────┘    └──────────┘   └──────────┘  │  :8000  │
                                                              └─────────┘
```

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 8088 (宿主) → 80 | Vue3 + Nginx，反向代理 /api 到 backend |
| backend | 8083 | Spring Boot 主后端 |
| ai-service | 8050 | FastAPI，Dify 工作流代理 + LLM 降级 |
| data-pipeline | 8000 | FastAPI，天气爬虫 + SSE 推送 |
| mysql | 3306 | 数据库 emergency_auth |
| neo4j | 7474 / 7687 | 图数据库（Browser / Bolt） |
| redis | 6379 | 缓存（可选） |

## 快速启动

### 1. 准备环境变量

```bash
cp deploy/.env.docker.example .env
```

按需修改 `.env` 文件中的密钥（**生产环境务必修改**）：

- `MYSQL_ROOT_PASSWORD` — MySQL root 密码
- `NEO4J_PASSWORD` — Neo4j 密码（首次初始化后不可改，需删卷重建）
- `JWT_SECRET` — JWT 签名密钥（至少 32 字节）
- `DIFY_API_KEY` — Dify 调度方案工作流密钥
- `DIFY_DATASET_API_KEY` — Dify 知识库数据集密钥
- `DEEPSEEK_API_KEY` — DeepSeek 模型密钥（LLM 降级用）
- `DIFY_BASE_URL` — Dify 实例地址（默认指向宿主机 8080）

### 2. 构建并启动全部服务

```bash
docker compose -f deploy/docker-compose.yml --env-file .env up -d --build
```

首次构建需要下载基础镜像并编译，预计 5-15 分钟（取决于网络）。

> **注意**：`docker-compose.yml` 位于 `deploy/` 目录。本文后续的 `docker compose` 子命令（ps / logs / down 等）均为简写，实际执行时请统一加上 `-f deploy/docker-compose.yml --env-file .env`，或先 `cd deploy` 后执行 `docker compose --env-file ../.env <子命令>`。

### 3. 访问平台

- 前端界面：http://localhost:8088
- 后端 API 文档：http://localhost:8083/api/swagger-ui.html
- Neo4j Browser：http://localhost:7474
- AI 服务文档：http://localhost:8050/docs
- 数据管道文档：http://localhost:8000/docs

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| reporter | 123456 | 普通信息员 |
| commander | 123456 | 应急指挥员 |
| resmanager | 123456 | 资源管理员 |
| admin | 123456 | 系统管理员 |

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志（实时跟踪）
docker compose logs -f backend
docker compose logs -f frontend

# 单独重建某个服务
docker compose up -d --build backend

# 停止全部服务
docker compose down

# 停止并删除数据卷（⚠️ 清空所有数据）
docker compose down -v
```

## 关于 Dify

Dify 平台**不包含**在本编排中，需独立部署。默认配置通过 `host.docker.internal` 让容器访问宿主机上的 Dify（端口 8080）。

- 若 Dify 部署在宿主机：保持 `DIFY_BASE_URL=http://host.docker.internal:8080`
- 若 Dify 也在 Docker 中：将其加入同一 Docker 网络，改用容器名访问

## 数据持久化

以下数据卷在 `deploy/docker-compose.yml` 中定义，删除容器不会丢失数据：

| 卷名 | 挂载点 | 说明 |
|------|--------|------|
| mysql_data | /var/lib/mysql | MySQL 数据 |
| neo4j_data | /data | Neo4j 数据 |
| neo4j_logs | /logs | Neo4j 日志 |
| redis_data | /data | Redis 持久化 |
| uploads_data | /app/uploads | 后端上传文件 |

## 数据库初始化

MySQL 容器**首次启动**时会自动执行 `deploy/sql/` 下的脚本（按文件名排序）：

1. `01-schema.sql` — 建表
2. `02-data.sql` — 灌入角色、用户、行政区划等种子数据

如需重新初始化，需先 `docker compose down -v` 删除数据卷。

## 故障排查

### 后端启动报数据库连接失败

MySQL 健康检查通过后 backend 才会启动（`depends_on: condition: service_healthy`）。若仍失败：

```bash
docker compose logs mysql
docker compose logs backend
```

### Neo4j 密码错误

Neo4j 密码在首次启动时写入，后续修改 `.env` 无效。需删除数据卷重建：

```bash
docker compose down -v
docker compose up -d --build
```

### Maven 依赖下载慢/超时

后端 Dockerfile 已内置阿里云 Maven 镜像。若仍超时，检查容器网络或手动构建：

```bash
cd backend
mvn clean package -DskipTests
docker compose build backend
```

### 前端无法访问后端 API

确认前端 Nginx 反向代理指向 `backend:8083`（容器间服务名通信）。若在容器外直接访问后端，使用 `http://localhost:8083/api`。
