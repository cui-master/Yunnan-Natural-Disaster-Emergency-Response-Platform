# 测试说明

本项目测试覆盖四大核心模块：**AI 服务（Dify 工作流）**、**知识库 Dify 接入**、**Neo4j 增删改查**、**SQL ↔ Neo4j 数据一致性**，并附带前端 mock 残留检测。

## 目录结构

```
backend/src/test/
├── java/com/yunnan/emergency/
│   ├── Neo4jCrudTest.java              # Neo4j 节点/关系 CRUD 测试
│   ├── SqlNeo4jConsistencyTest.java    # SQL ↔ Neo4j 数据一致性测试
│   ├── AiAgentServiceTest.java         # AI 服务（两个 Dify 工作流）测试
│   ├── KnowledgeBaseDifyTest.java      # 知识库 Dify dataset 接入测试
│   └── FrontendMockRemnantTest.java    # 前端 mock 残留检测
└── resources/
    └── application-test.yml            # 测试环境配置

data-pipeline/tests/
├── conftest.py                          # pytest 公共 fixture
├── test_dify_workflow.py                # Dify 工作流测试（事件抽取/预案检索/方案审查）
├── test_dify_dataset.py                 # 知识库 Dify dataset API 测试
├── test_neo4j_crud.py                   # Neo4j CRUD 测试（通过 Spring Boot 接口）
├── test_sql_neo4j_consistency.py        # SQL ↔ Neo4j 一致性测试
└── test_frontend_mock.py                # 前端 mock 残留检测
```

## 测试分类

| 类型 | 触发条件 | 说明 |
|------|----------|------|
| 单元测试 | 默认运行 | 使用 Mockito/mock，不依赖外部服务 |
| 集成测试 | `RUN_INTEGRATION=1` | 真实调用 Dify / Neo4j / MySQL / Spring Boot |
| 静态检测 | 默认运行 | 扫描前端代码，确保无 mock 残留 |

## 环境准备

### 必需服务

| 服务 | 端口 | 用途 |
|------|------|------|
| MySQL | 3306 | 主存储（emergency_auth 数据库） |
| Neo4j | 7687 (bolt) | 图谱存储 |
| FastAPI (data-pipeline) | 8000 | Dify 工作流代理 + 知识库 dataset |
| Spring Boot | 8083 | 业务 API + Neo4j CRUD 接口 |
| Dify | 8080 (默认) | AI 工作流 + 知识库 |

### 数据库初始化

```bash
mysql -u root -p emergency_auth < deploy/sql/schema.sql
mysql -u root -p emergency_auth < deploy/sql/data.sql
```

### 启动服务

```bash
# 1. FastAPI 数据管道
cd data-pipeline
pip install -r requirements.txt
cp .env.example .env  # 按需修改 Dify 配置
uvicorn app.main:app --port 8000

# 2. Spring Boot 后端
cd backend
mvn spring-boot:run

# 3. Neo4j（Docker 推荐）
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/12345678 neo4j:5.23

# 4. Dify（按官方文档部署）
```

## 运行测试

### Python 测试（data-pipeline）

```bash
cd data-pipeline

# 1. 仅跑单元测试（默认，无需外部服务）
pytest tests/ -v

# 2. 跑全部测试（含集成测试，需要所有服务运行）
RUN_INTEGRATION=1 pytest tests/ -v

# 3. 只跑 Dify 工作流测试
RUN_INTEGRATION=1 pytest tests/test_dify_workflow.py -v

# 4. 只跑 Neo4j CRUD 测试
RUN_INTEGRATION=1 pytest tests/test_neo4j_crud.py -v

# 5. 只跑 SQL ↔ Neo4j 一致性测试
RUN_INTEGRATION=1 pytest tests/test_sql_neo4j_consistency.py -v

# 6. 只跑知识库 Dify 测试
RUN_INTEGRATION=1 pytest tests/test_dify_dataset.py -v

# 7. 只跑前端 mock 残留检测（不需要外部服务）
pytest tests/test_frontend_mock.py -v
```

### Java 测试（backend）

```bash
cd backend

# 1. 仅跑单元测试（默认，不需要外部服务）
mvn test

# 2. 跑指定测试类
mvn test -Dtest=FrontendMockRemnantTest

# 3. 跑集成测试（需要 MySQL + Neo4j + Spring Boot 运行）
mvn test -Dtest=Neo4jCrudTest -DRUN_INTEGRATION=1
mvn test -Dtest=SqlNeo4jConsistencyTest -DRUN_INTEGRATION=1
mvn test -Dtest=AiAgentServiceTest -DRUN_INTEGRATION=1
mvn test -Dtest=KnowledgeBaseDifyTest -DRUN_INTEGRATION=1

# 4. 跑全部集成测试
mvn test -DRUN_INTEGRATION=1
```

## 测试矩阵

| 测试文件 | 类型 | 依赖服务 | 通过标准 |
|---------|------|---------|---------|
| `test_dify_workflow.py::TestExtractIncidentUnit` | 单元 | 无 | mock 响应被正确解析 |
| `test_dify_workflow.py::TestDifyWorkflowIntegration` | 集成 | FastAPI + Dify | Dify 工作流返回 succeeded |
| `test_dify_dataset.py::TestDifyDatasetUnit` | 单元 | 无 | mock httpx 调用正确 |
| `test_dify_dataset.py::TestDifyDatasetIntegration` | 集成 | FastAPI + Dify | 创建/删除 dataset 成功 |
| `test_dify_dataset.py::TestSpringBootKnowledgeDifySync` | 集成 | Spring Boot + FastAPI + Dify | SQL 创建后 Dify 侧出现对应 dataset |
| `test_neo4j_crud.py::TestNeo4jCrudIntegration` | 集成 | Spring Boot + Neo4j | 节点 CRUD 全周期成功 |
| `test_sql_neo4j_consistency.py::TestSqlNeo4jConsistency` | 集成 | Spring Boot + MySQL + Neo4j | 各标签 sqlCount == neo4jCount |
| `test_frontend_mock.py::TestNoMockRemnant` | 静态 | 无 | .env VITE_USE_MOCK=false，无 Math.random |
| `Neo4jCrudTest.java` | 集成 | Neo4j | 节点/关系 CRUD 成功 |
| `SqlNeo4jConsistencyTest.java` | 集成 | MySQL + Neo4j | 一致性报告 consistent=true |
| `AiAgentServiceTest.java` | 单元+集成 | FastAPI + Dify | 工作流调用成功 + 重试机制 |
| `KnowledgeBaseDifyTest.java` | 单元 | Spring Boot | 创建/删除同步到 Dify |
| `FrontendMockRemnantTest.java` | 静态 | 无 | 前端无 mock 残留 |

## 常见问题

### Q: 集成测试报 "Spring Boot 服务未运行"
A: 先启动 Spring Boot（`mvn spring-boot:run`），默认端口 8083，context-path `/api`。

### Q: Neo4j 测试报连接失败
A: 检查 `application-test.yml` 中 `neo4j.uri` 配置，默认 `bolt://localhost:7687`，密码 `12345678`。

### Q: Dify 工作流测试报 502
A: 检查 data-pipeline 的 `.env` 是否配置了正确的 `DIFY_BASE_URL` 和 `DIFY_API_KEY_WORKFLOW`，以及 Dify 服务是否运行。

### Q: SQL ↔ Neo4j 一致性测试失败
A: 说明 Neo4j 中存在 SQL 已删除的孤儿节点，或 SQL 有但 Neo4j 没有的节点。可通过 `SqlNeo4jSyncService.syncIncidentCreate` 等方法手动同步，或在业务代码中接入双写。

### Q: 前端 mock 残留检测失败
A: 检查 `frontend/.env.development` 中 `VITE_USE_MOCK=false`，并确保 `api/index.js` 中没有 `Math.random()` 生成业务数据。
