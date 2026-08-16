-- ============================================================
-- 全库迁移脚本（安全版）
-- 将现有数据库对齐到 schema.sql + Java 实体的要求
-- 数据库: emergency_auth
-- 安全: 只 ALTER，不 DROP 表，不丢数据
-- 兼容: 所有操作都先检查列/索引是否存在，不存在才执行
-- ============================================================

USE emergency_auth;

-- ============================================================
-- 1. users 表
-- ============================================================

-- 1.1 删除多余的 role_id 列（如果存在）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='role_id');
SET @sql := IF(@exist > 0, 'ALTER TABLE users DROP COLUMN role_id', 'SELECT ''users.role_id not exist, skip'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 1.2 调整已有列类型（只改已存在的列）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='username');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN username VARCHAR(64) NOT NULL COMMENT ''登录用户名''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='password');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN password VARCHAR(255) NOT NULL COMMENT ''BCrypt 加密密码''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='real_name');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN real_name VARCHAR(64) DEFAULT NULL COMMENT ''真实姓名''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='email');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN email VARCHAR(128) DEFAULT NULL COMMENT ''邮箱''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='phone');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN phone VARCHAR(32) DEFAULT NULL COMMENT ''手机号''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='avatar');
SET @sql := IF(@exist > 0, 'ALTER TABLE users MODIFY COLUMN avatar VARCHAR(255) DEFAULT NULL COMMENT ''头像URL''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 1.3 status: varchar -> tinyint（安全转换）
SET @col_type := (SELECT DATA_TYPE FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='status');
SET @sql := IF(@col_type = 'varchar',
  CONCAT(
    'ALTER TABLE users ADD COLUMN status_new TINYINT NOT NULL DEFAULT 1 COMMENT ''状态: 1-启用 0-禁用''; ',
    'UPDATE users SET status_new = CASE WHEN status IN (''ENABLED'',''enabled'',''active'',''ACTIVE'',''1'') THEN 1 WHEN status IN (''DISABLED'',''disabled'',''inactive'',''INACTIVE'',''0'') THEN 0 ELSE 1 END; ',
    'ALTER TABLE users DROP COLUMN status; ',
    'ALTER TABLE users CHANGE COLUMN status_new status TINYINT NOT NULL DEFAULT 1 COMMENT ''状态: 1-启用 0-禁用'''
  ),
  'SELECT ''users.status already tinyint or not exist'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 1.4 补缺失列
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='role_code');
SET @sql := IF(@exist = 0, 'ALTER TABLE users ADD COLUMN role_code VARCHAR(32) NOT NULL DEFAULT ''reporter'' COMMENT ''角色编码'' AFTER avatar', 'SELECT ''users.role_code exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='department');
SET @sql := IF(@exist = 0, 'ALTER TABLE users ADD COLUMN department VARCHAR(128) DEFAULT NULL COMMENT ''所属部门'' AFTER role_code', 'SELECT ''users.department exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='last_login_at');
SET @sql := IF(@exist = 0, 'ALTER TABLE users ADD COLUMN last_login_at DATETIME DEFAULT NULL COMMENT ''最后登录时间'' AFTER status', 'SELECT ''users.last_login_at exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='users' AND column_name='updated_at');
SET @sql := IF(@exist = 0, 'ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ''更新时间'' AFTER created_at', 'SELECT ''users.updated_at exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 1.5 补索引
SET @exist := (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema='emergency_auth' AND table_name='users' AND index_name='idx_role');
SET @sql := IF(@exist=0, 'ALTER TABLE users ADD KEY idx_role (role_code)', 'SELECT ''users.idx_role exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema='emergency_auth' AND table_name='users' AND index_name='idx_status');
SET @sql := IF(@exist=0, 'ALTER TABLE users ADD KEY idx_status (status)', 'SELECT ''users.idx_status exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- 2. roles 表
-- ============================================================

-- 2.1 补缺失列（先 ADD，再 MODIFY）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='role_code');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN role_code VARCHAR(32) NOT NULL DEFAULT '''' COMMENT ''角色编码''', 'SELECT ''roles.role_code exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='role_name');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN role_name VARCHAR(64) NOT NULL DEFAULT '''' COMMENT ''角色名称''', 'SELECT ''roles.role_name exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='description');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN description VARCHAR(255) DEFAULT NULL COMMENT ''角色描述''', 'SELECT ''roles.description exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='sort_order');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN sort_order INT NOT NULL DEFAULT 0 COMMENT ''排序''', 'SELECT ''roles.sort_order exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2.2 调整已有列类型
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='role_code');
SET @sql := IF(@exist > 0, 'ALTER TABLE roles MODIFY COLUMN role_code VARCHAR(32) NOT NULL COMMENT ''角色编码''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='role_name');
SET @sql := IF(@exist > 0, 'ALTER TABLE roles MODIFY COLUMN role_name VARCHAR(64) NOT NULL COMMENT ''角色名称''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='description');
SET @sql := IF(@exist > 0, 'ALTER TABLE roles MODIFY COLUMN description VARCHAR(255) DEFAULT NULL COMMENT ''角色描述''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='sort_order');
SET @sql := IF(@exist > 0, 'ALTER TABLE roles MODIFY COLUMN sort_order INT NOT NULL DEFAULT 0 COMMENT ''排序''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2.3 status: varchar -> tinyint
SET @col_type := (SELECT DATA_TYPE FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='status');
SET @sql := IF(@col_type = 'varchar',
  CONCAT(
    'ALTER TABLE roles ADD COLUMN status_new TINYINT NOT NULL DEFAULT 1 COMMENT ''状态: 1-启用 0-禁用''; ',
    'UPDATE roles SET status_new = CASE WHEN status IN (''ENABLED'',''enabled'',''active'',''ACTIVE'',''1'') THEN 1 WHEN status IN (''DISABLED'',''disabled'',''inactive'',''INACTIVE'',''0'') THEN 0 ELSE 1 END; ',
    'ALTER TABLE roles DROP COLUMN status; ',
    'ALTER TABLE roles CHANGE COLUMN status_new status TINYINT NOT NULL DEFAULT 1 COMMENT ''状态: 1-启用 0-禁用'''
  ),
  'SELECT ''roles.status already tinyint or not exist'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2.4 补缺失列
SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='created_at');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT ''创建时间'' AFTER status', 'SELECT ''roles.created_at exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='emergency_auth' AND table_name='roles' AND column_name='updated_at');
SET @sql := IF(@exist = 0, 'ALTER TABLE roles ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ''更新时间'' AFTER created_at', 'SELECT ''roles.updated_at exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2.5 补唯一索引
SET @exist := (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema='emergency_auth' AND table_name='roles' AND index_name='uk_role_code');
SET @sql := IF(@exist=0, 'ALTER TABLE roles ADD UNIQUE KEY uk_role_code (role_code)', 'SELECT ''roles.uk_role_code exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- 3. 验证最终结构
-- ============================================================
SELECT '=== users ===' AS table_name;
DESCRIBE users;
SELECT '=== roles ===' AS table_name;
DESCRIBE roles;
