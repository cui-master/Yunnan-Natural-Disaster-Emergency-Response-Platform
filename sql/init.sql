-- ============================================================
-- 云南自然灾害应急协同决策平台 — 数据库初始化
-- PostgreSQL 15 + PostGIS 3.4 + pgvector
-- 执行方式：docker compose 启动 db 后自动加载，或手动 psql -f init.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------- 角色 ----------------
CREATE TABLE IF NOT EXISTS roles (
    id          BIGSERIAL PRIMARY KEY,
    role_key    VARCHAR(40) NOT NULL UNIQUE,
    role_name   VARCHAR(60) NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------- 用户 ----------------
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    username    VARCHAR(40) NOT NULL UNIQUE,
    password    VARCHAR(100) NOT NULL,          -- bcrypt
    real_name   VARCHAR(60),
    phone       VARCHAR(20),
    role_id     BIGINT NOT NULL REFERENCES roles(id),
    status      VARCHAR(20) NOT NULL DEFAULT 'ENABLED', -- ENABLED / DISABLED
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------- 地理位置（PostGIS） ----------------
CREATE TABLE IF NOT EXISTS locations (
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(120),
    address      VARCHAR(255),
    geom         geometry(Point, 4326),         -- 事件/资源坐标
    risk_radius  NUMERIC(10,2),                -- 风险半径(米)，可选
    risk_geom    geometry(Polygon, 4326),      -- 风险范围，可选
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST (geom);

-- ---------------- 灾情事件（状态机主体） ----------------
-- 注意：report_id 与 incident_reports 构成循环引用，先建普通字段，
-- 待 incident_reports 建完后再用 ALTER TABLE 补外键。
CREATE TABLE IF NOT EXISTS incidents (
    id           BIGSERIAL PRIMARY KEY,
    code         VARCHAR(40) UNIQUE,            -- 事件编号 YN + 时间戳
    title        VARCHAR(200) NOT NULL,
    type         VARCHAR(40),                   -- FLOOD/EARTHQUAKE/LANDSLIDE/FIRE...
    level        VARCHAR(20) DEFAULT 'UNKNOWN', -- Ⅰ/Ⅱ/Ⅲ/Ⅳ 或 UNKNOWN
    status       VARCHAR(30) NOT NULL DEFAULT 'PENDING_VERIFY', -- 状态机
    report_id    BIGINT,                        -- 见文末 ALTER 补外键
    location_id  BIGINT REFERENCES locations(id),
    description  TEXT,
    confirmed_by BIGINT,
    confirmed_at TIMESTAMP,
    closed_at    TIMESTAMP,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);

-- ---------------- 灾情上报 ----------------
CREATE TABLE IF NOT EXISTS incident_reports (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  BIGINT REFERENCES incidents(id),
    reporter_id  BIGINT REFERENCES users(id),
    reporter_name VARCHAR(60),
    contact      VARCHAR(40),
    content      TEXT NOT NULL,
    images       TEXT,                           -- 逗号分隔的图片URL/路径
    location_text VARCHAR(255),
    lat          NUMERIC(10,7),
    lng          NUMERIC(10,7),
    status       VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED', -- SUBMITTED / PROCESSED / REJECTED
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);

-- 补 incidents.report_id 外键（循环引用，建表后处理）
ALTER TABLE incidents
    ADD CONSTRAINT fk_incidents_report
    FOREIGN KEY (report_id) REFERENCES incident_reports(id);

-- ---------------- 救援资源 ----------------
CREATE TABLE IF NOT EXISTS resources (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    type        VARCHAR(30) NOT NULL,           -- PERSONNEL/VEHICLE/MATERIAL/SHELTER
    total       INT NOT NULL DEFAULT 0,
    available   INT NOT NULL DEFAULT 0,
    unit        VARCHAR(20),
    location_id BIGINT REFERENCES locations(id),
    status      VARCHAR(20) NOT NULL DEFAULT 'NORMAL', -- NORMAL / DEPLOYED / MAINTENANCE
    locked_by   BIGINT,
    locked_at   TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------- 应急预案（AI 生成） ----------------
-- 须在建 dispatch_orders 之前创建（dispatch_orders.plan_id 引用它）
CREATE TABLE IF NOT EXISTS emergency_plans (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  BIGINT NOT NULL REFERENCES incidents(id),
    title        VARCHAR(200),
    content      TEXT,                          -- 结构化方案（JSON/文本）
    status       VARCHAR(30) NOT NULL DEFAULT 'DRAFT', -- DRAFT / APPROVED
    generated_by BIGINT,
    approved_by  BIGINT,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    approved_at  TIMESTAMP
);

-- ---------------- 调度单 ----------------
CREATE TABLE IF NOT EXISTS dispatch_orders (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  BIGINT NOT NULL REFERENCES incidents(id),
    plan_id      BIGINT REFERENCES emergency_plans(id),
    resource_id  BIGINT NOT NULL REFERENCES resources(id),
    quantity     INT NOT NULL DEFAULT 1,
    status       VARCHAR(30) NOT NULL DEFAULT 'LOCKED', -- LOCKED / DISPATCHED / RELEASED / CONFLICT
    operator_id  BIGINT,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    executed_at  TIMESTAMP,
    released_at  TIMESTAMP
);

-- ---------------- 数据源 ----------------
CREATE TABLE IF NOT EXISTS data_sources (
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(120),
    type         VARCHAR(40),
    url          VARCHAR(512),
    status       VARCHAR(20) DEFAULT 'ACTIVE',
    last_fetch   TIMESTAMP,
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------- Agent 执行记录 ----------------
CREATE TABLE IF NOT EXISTS agent_runs (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  BIGINT REFERENCES incidents(id),
    plan_id      BIGINT REFERENCES emergency_plans(id),
    type         VARCHAR(30),                   -- EXTRACT / RETRIEVE / REVIEW
    prompt       TEXT,
    status       VARCHAR(20) DEFAULT 'RUNNING', -- RUNNING / SUCCESS / FAILED
    result       TEXT,
    started_at   TIMESTAMP NOT NULL DEFAULT now(),
    finished_at  TIMESTAMP
);

-- ---------------- 引用来源 ----------------
CREATE TABLE IF NOT EXISTS citations (
    id           BIGSERIAL PRIMARY KEY,
    agent_run_id BIGINT REFERENCES agent_runs(id),
    source       VARCHAR(255),
    excerpt      TEXT,
    score        NUMERIC(6,4),
    created_at   TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------------- 审计日志 ----------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT,
    username    VARCHAR(40),
    action      VARCHAR(80) NOT NULL,
    target      VARCHAR(80),
    detail      TEXT,
    ip          VARCHAR(64),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);

-- ---------------- 预案向量分块（pgvector，MVP 预留） ----------------
CREATE TABLE IF NOT EXISTS plan_chunks (
    id         BIGSERIAL PRIMARY KEY,
    plan_id    BIGINT REFERENCES emergency_plans(id),
    content    TEXT,
    embedding  vector(1536)
);
CREATE INDEX IF NOT EXISTS idx_plan_chunks_embedding ON plan_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

<<<<<<< HEAD
-- ---------------- 知识库注册表（Dify Dataset 映射，DB 为唯一真源） ----------------
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id          BIGSERIAL PRIMARY KEY,
    kb_key      VARCHAR(32)  NOT NULL UNIQUE,           -- OPTIMIZE / RISK
    kb_name     VARCHAR(64)  NOT NULL UNIQUE,           -- 优化调度 / 风险评估
    dataset_id  VARCHAR(64)  NOT NULL,                  -- Dify dataset UUID
    description VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------- 知识库文档表（每次上传落库，跟踪 Dify document_id / 解析状态） ----------------
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id               BIGSERIAL PRIMARY KEY,
    kb_name          VARCHAR(64)  NOT NULL,            -- 优化调度 / 风险评估
    dify_document_id VARCHAR(64)  NOT NULL,             -- Dify 文档 id（删除/查状态用）
    doc_name         VARCHAR(255) NOT NULL,            -- 文件名
    status           VARCHAR(32)  NOT NULL DEFAULT 'PARSING', -- PARSING / COMPLETED / FAILED
    chunk_count      INTEGER      DEFAULT 0,
    word_count       INTEGER      DEFAULT 0,
    uploader         VARCHAR(64),
    uploaded_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_kb ON knowledge_docs(kb_name);

=======
>>>>>>> feature-cui
-- ============================================================
-- 种子数据
-- ============================================================
INSERT INTO roles (role_key, role_name, description) VALUES
    ('ROLE_REPORTER',  '普通信息员',   '上报灾情'),
    ('ROLE_COMMANDER', '应急指挥人员', '审核事件、生成/审批方案'),
    ('ROLE_RESMGR',    '资源管理员',   '维护人员/车辆/物资/避难所'),
    ('ROLE_ADMIN',     '系统管理员',   '用户/知识库/数据源管理')
ON CONFLICT (role_key) DO NOTHING;

-- 密码统一为 bcrypt("123456")
INSERT INTO users (username, password, real_name, phone, role_id, status) VALUES
    ('reporter',  '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '张信息', '13800000001', (SELECT id FROM roles WHERE role_key='ROLE_REPORTER'),  'ENABLED'),
    ('commander', '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '李指挥', '13800000002', (SELECT id FROM roles WHERE role_key='ROLE_COMMANDER'),'ENABLED'),
    ('resmanager','$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '王资源', '13800000003', (SELECT id FROM roles WHERE role_key='ROLE_RESMGR'),   'ENABLED'),
    ('admin',     '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '赵管理', '13800000004', (SELECT id FROM roles WHERE role_key='ROLE_ADMIN'),    'ENABLED')
ON CONFLICT (username) DO NOTHING;

<<<<<<< HEAD
-- 知识库注册表（dataset_id 来自 Dify 控制台；优化调度 / 风险评估）
INSERT INTO knowledge_bases (kb_key, kb_name, dataset_id, description) VALUES
    ('OPTIMIZE', '优化调度', 'a154e469-3acd-4c33-bcdc-ea65d0886488', '物资调度预案 / Sandbox 仿真参考资料'),
    ('RISK',     '风险评估', '03d787b9-e585-4b85-abbe-332e208c6530', '风险研判 / 历史案例 / 处置规范')
ON CONFLICT (kb_key) DO NOTHING;

=======
>>>>>>> feature-cui
-- 示例资源
INSERT INTO resources (name, type, total, available, unit, status) VALUES
    ('抢险队员-一组', 'PERSONNEL', 30, 30, '人',  'NORMAL'),
    ('抢险队员-二组', 'PERSONNEL', 25, 25, '人',  'NORMAL'),
    ('救援卡车',      'VEHICLE',   12, 12, '辆',  'NORMAL'),
    ('救护车',        'VEHICLE',    8,  8, '辆',  'NORMAL'),
    ('帐篷',          'MATERIAL',  500, 500, '顶',  'NORMAL'),
    ('饮用水',        'MATERIAL', 2000, 2000,'箱',  'NORMAL'),
    ('临时避难所-A',  'SHELTER',  300, 300, '人',  'NORMAL')
ON CONFLICT DO NOTHING;
