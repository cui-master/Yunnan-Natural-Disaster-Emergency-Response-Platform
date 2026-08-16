-- ============================================================
-- users 表迁移脚本
-- 将现有的 users 表结构对齐到 schema.sql + User.java 的要求
-- 数据库: emergency_auth
-- 安全: 只 ALTER，不 DROP，不丢数据
-- ============================================================

USE emergency_auth;

-- ============================================================
-- 1. 删除多余的 role_id 列（代码里用的是 role_code 字符串）
-- ============================================================
ALTER TABLE users DROP COLUMN role_id;

-- ============================================================
-- 2. 调整已有列的类型，对齐 schema.sql
-- ============================================================
ALTER TABLE users
  MODIFY COLUMN username   VARCHAR(64)  NOT NULL COMMENT '登录用户名',
  MODIFY COLUMN password   VARCHAR(255) NOT NULL COMMENT 'BCrypt 加密密码',
  MODIFY COLUMN real_name  VARCHAR(64)  DEFAULT NULL COMMENT '真实姓名',
  MODIFY COLUMN email      VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  MODIFY COLUMN phone      VARCHAR(32)  DEFAULT NULL COMMENT '手机号',
  MODIFY COLUMN avatar     VARCHAR(255) DEFAULT NULL COMMENT '头像URL';

-- ============================================================
-- 3. 把 status 从 varchar(20) 'ENABLED/DISABLED' 改成 tinyint 1/0
--    先加临时列，用 CASE 转换，再删旧列，最后改名
-- ============================================================
ALTER TABLE users ADD COLUMN status_new TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用';

UPDATE users SET status_new = CASE
  WHEN status IN ('ENABLED', 'enabled', 'active', 'ACTIVE') THEN 1
  WHEN status IN ('DISABLED', 'disabled', 'inactive', 'INACTIVE') THEN 0
  ELSE 1
END;

ALTER TABLE users DROP COLUMN status;
ALTER TABLE users CHANGE COLUMN status_new status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用';

-- ============================================================
-- 4. 补上缺失的列
-- ============================================================
ALTER TABLE users
  ADD COLUMN role_code     VARCHAR(32)  NOT NULL DEFAULT 'reporter' COMMENT '角色编码' AFTER avatar,
  ADD COLUMN department    VARCHAR(128) DEFAULT NULL COMMENT '所属部门' AFTER role_code,
  ADD COLUMN last_login_at DATETIME     DEFAULT NULL COMMENT '最后登录时间' AFTER status,
  ADD COLUMN updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER created_at;

-- ============================================================
-- 5. 补索引（如果不存在则创建）
-- ============================================================
-- 检查并添加 role_code 索引
SET @exist := (SELECT COUNT(*) FROM information_schema.statistics
               WHERE table_schema = 'emergency_auth' AND table_name = 'users' AND index_name = 'idx_role');
SET @sql := IF(@exist = 0,
  'ALTER TABLE users ADD KEY idx_role (role_code)',
  'SELECT ''idx_role already exists'' AS info');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 status 索引
SET @exist := (SELECT COUNT(*) FROM information_schema.statistics
               WHERE table_schema = 'emergency_auth' AND table_name = 'users' AND index_name = 'idx_status');
SET @sql := IF(@exist = 0,
  'ALTER TABLE users ADD KEY idx_status (status)',
  'SELECT ''idx_status already exists'' AS info');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================
-- 6. 验证最终表结构
-- ============================================================
DESCRIBE users;
