-- ============================================================
-- 云南自然灾害应急协同决策平台 — 认证域初始化（MySQL 8.0）
-- 用户 / 角色 / 审计日志 迁到 MySQL，贴合"用户数据存 MySQL"的要求
-- 业务 / 地理 / 向量数据仍在 PostgreSQL（见 init.sql）
-- ============================================================

CREATE TABLE IF NOT EXISTS roles (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_key    VARCHAR(40) NOT NULL UNIQUE,
    role_name   VARCHAR(60) NOT NULL,
    description VARCHAR(255),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(40) NOT NULL UNIQUE,
    password    VARCHAR(100) NOT NULL,          -- bcrypt
    real_name   VARCHAR(60),
    phone       VARCHAR(20),
    role_id     BIGINT NOT NULL REFERENCES roles(id),
    status      VARCHAR(20) NOT NULL DEFAULT 'ENABLED', -- ENABLED / DISABLED
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT,
    username    VARCHAR(40),
    action      VARCHAR(80) NOT NULL,
    target      VARCHAR(80),
    detail      TEXT,
    ip          VARCHAR(64),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE INDEX idx_audit_created ON audit_logs(created_at);

-- ---------------- 种子数据 ----------------
INSERT INTO roles (role_key, role_name, description) VALUES
    ('ROLE_REPORTER',  '普通信息员',   '上报灾情'),
    ('ROLE_COMMANDER', '应急指挥人员', '审核事件、生成/审批方案'),
    ('ROLE_RESMGR',    '资源管理员',   '维护人员/车辆/物资/避难所'),
    ('ROLE_ADMIN',     '系统管理员',   '用户/知识库/数据源管理');

-- 密码统一为 bcrypt("123456")
INSERT INTO users (username, password, real_name, phone, role_id, status) VALUES
    ('reporter',  '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '张信息', '13800000001', (SELECT id FROM roles WHERE role_key='ROLE_REPORTER'),  'ENABLED'),
    ('commander', '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '李指挥', '13800000002', (SELECT id FROM roles WHERE role_key='ROLE_COMMANDER'),'ENABLED'),
    ('resmanager','$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '王资源', '13800000003', (SELECT id FROM roles WHERE role_key='ROLE_RESMGR'),   'ENABLED'),
    ('admin',     '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '赵管理', '13800000004', (SELECT id FROM roles WHERE role_key='ROLE_ADMIN'),    'ENABLED');

-- MySQL 8.0 默认 caching_sha2_password，老 JDBC 驱动连不上；改为 mysql_native_password
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'root123';
FLUSH PRIVILEGES;
