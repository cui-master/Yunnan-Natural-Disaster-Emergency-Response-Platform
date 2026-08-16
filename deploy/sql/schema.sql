-- ============================================================
-- 云南省自然灾害应急响应平台 - 数据库建表脚本
-- 数据库: emergency_auth
-- 字符集: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS emergency_auth
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE emergency_auth;

-- ============================================================
-- 1. 用户表 users
-- ============================================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  username      VARCHAR(64)  NOT NULL COMMENT '登录用户名',
  password      VARCHAR(255) NOT NULL COMMENT 'BCrypt 加密密码',
  real_name     VARCHAR(64)  DEFAULT NULL COMMENT '真实姓名',
  email         VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  phone         VARCHAR(32)  DEFAULT NULL COMMENT '手机号',
  avatar        VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  role_code     VARCHAR(32)  NOT NULL DEFAULT 'reporter' COMMENT '角色编码',
  department    VARCHAR(128) DEFAULT NULL COMMENT '所属部门',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用',
  last_login_at DATETIME     DEFAULT NULL COMMENT '最后登录时间',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username),
  KEY idx_role (role_code),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================================
-- 2. 角色表 roles
-- ============================================================
DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  role_code   VARCHAR(32)  NOT NULL COMMENT '角色编码',
  role_name   VARCHAR(64)  NOT NULL COMMENT '角色名称',
  description VARCHAR(255) DEFAULT NULL COMMENT '角色描述',
  sort_order  INT          NOT NULL DEFAULT 0 COMMENT '排序',
  status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ============================================================
-- 3. 位置表 locations
-- ============================================================
DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '位置ID',
  name         VARCHAR(128) NOT NULL COMMENT '位置名称',
  admin_code   VARCHAR(20)  DEFAULT NULL COMMENT '行政区划代码',
  level        VARCHAR(20)  NOT NULL DEFAULT 'county' COMMENT '层级: province/city/county/town',
  parent_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '父级ID',
  lng          DECIMAL(11,8) DEFAULT NULL COMMENT '经度',
  lat          DECIMAL(10,8) DEFAULT NULL COMMENT '纬度',
  geom         GEOMETRY     DEFAULT NULL COMMENT '地理空间数据（可选）',
  status       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_parent (parent_id),
  KEY idx_level (level),
  KEY idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='位置/行政区划表';

-- ============================================================
-- 4. 灾情事件表 incidents
-- ============================================================
DROP TABLE IF EXISTS incidents;
CREATE TABLE incidents (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '事件ID',
  incident_no    VARCHAR(32)  NOT NULL COMMENT '事件编号',
  title          VARCHAR(255) NOT NULL COMMENT '事件标题',
  disaster_type  VARCHAR(32)  NOT NULL COMMENT '灾害类型: 地震/山洪/洪涝/崩塌/泥石流/滑坡/暴雨',
  risk_level     VARCHAR(16)  NOT NULL DEFAULT '低' COMMENT '风险等级: 低/中/高/特别重大',
  location_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '位置ID',
  location_name  VARCHAR(255) DEFAULT NULL COMMENT '位置描述（冗余）',
  lng            DECIMAL(11,8) DEFAULT NULL COMMENT '发生地经度',
  lat            DECIMAL(10,8) DEFAULT NULL COMMENT '发生地纬度',
  status         VARCHAR(20)  NOT NULL DEFAULT '待核验' COMMENT '状态机: 待核验/已确认/处置中/已结束',
  source         VARCHAR(32)  DEFAULT 'manual' COMMENT '来源: manual/auto/web',
  reporter_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '上报人ID',
  reviewer_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '审核人ID',
  reviewed_at    DATETIME     DEFAULT NULL COMMENT '审核时间',
  occurred_at    DATETIME     DEFAULT NULL COMMENT '发生时间',
  description    TEXT         DEFAULT NULL COMMENT '事件描述',
  affected_people INT         DEFAULT 0 COMMENT '受灾人数',
  damage_degree  VARCHAR(16)  DEFAULT '一般' COMMENT '损失程度: 一般/较大/重大/特别重大',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_incident_no (incident_no),
  KEY idx_disaster_type (disaster_type),
  KEY idx_risk_level (risk_level),
  KEY idx_status (status),
  KEY idx_reporter (reporter_id),
  KEY idx_location (location_id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情事件表';

-- ============================================================
-- 5. 灾情上报表 incident_reports
-- ============================================================
DROP TABLE IF EXISTS incident_reports;
CREATE TABLE incident_reports (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '上报ID',
  incident_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '关联事件ID',
  title          VARCHAR(255) NOT NULL COMMENT '上报标题',
  disaster_type  VARCHAR(32)  NOT NULL COMMENT '灾害类型',
  risk_level     VARCHAR(16)  NOT NULL DEFAULT '低' COMMENT '上报风险等级',
  location_name  VARCHAR(255) DEFAULT NULL COMMENT '发生地点',
  lng            DECIMAL(11,8) DEFAULT NULL COMMENT '经度',
  lat            DECIMAL(10,8) DEFAULT NULL COMMENT '纬度',
  reporter_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '上报人ID',
  reporter_name  VARCHAR(64)  DEFAULT NULL COMMENT '上报人姓名（冗余）',
  contact        VARCHAR(64)  DEFAULT NULL COMMENT '联系方式',
  description    TEXT         DEFAULT NULL COMMENT '详细描述',
  images         JSON         DEFAULT NULL COMMENT '图片列表 JSON数组',
  status         VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '状态: pending待审核/approved已通过/rejected已驳回/revised待修改',
  reviewer_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '审核人ID',
  review_comment VARCHAR(500) DEFAULT NULL COMMENT '审核意见',
  reviewed_at    DATETIME     DEFAULT NULL COMMENT '审核时间',
  occurred_at    DATETIME     DEFAULT NULL COMMENT '发生时间',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_incident (incident_id),
  KEY idx_disaster_type (disaster_type),
  KEY idx_status (status),
  KEY idx_reporter (reporter_id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情上报表';

-- ============================================================
-- 6. 资源表 resources
-- ============================================================
DROP TABLE IF EXISTS resources;
CREATE TABLE resources (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '资源ID',
  resource_no   VARCHAR(32)  NOT NULL COMMENT '资源编号',
  name          VARCHAR(255) NOT NULL COMMENT '资源名称',
  category      VARCHAR(32)  NOT NULL COMMENT '资源类别: warehouse仓库/team队伍/shelter避难所/material物资/equipment装备',
  resource_type VARCHAR(64)  DEFAULT NULL COMMENT '资源子类型',
  description   TEXT         DEFAULT NULL COMMENT '资源描述',
  location_id   BIGINT UNSIGNED DEFAULT NULL COMMENT '位置ID',
  location_name VARCHAR(255) DEFAULT NULL COMMENT '位置名称（冗余）',
  lng           DECIMAL(11,8) DEFAULT NULL COMMENT '经度',
  lat           DECIMAL(10,8) DEFAULT NULL COMMENT '纬度',
  capacity      INT          DEFAULT 0 COMMENT '容量/数量',
  available_qty INT          DEFAULT 0 COMMENT '可用数量',
  manager_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '负责人ID',
  manager_name  VARCHAR(64)  DEFAULT NULL COMMENT '负责人姓名',
  contact       VARCHAR(64)  DEFAULT NULL COMMENT '联系电话',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-可用 0-不可用',
  properties    JSON         DEFAULT NULL COMMENT '扩展属性 JSON',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_resource_no (resource_no),
  KEY idx_category (category),
  KEY idx_location (location_id),
  KEY idx_status (status),
  KEY idx_resource_type (resource_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='救援资源表';

-- ============================================================
-- 7. 调度指令表 dispatch_orders
-- ============================================================
DROP TABLE IF EXISTS dispatch_orders;
CREATE TABLE dispatch_orders (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '调度ID',
  order_no       VARCHAR(32)  NOT NULL COMMENT '调度编号',
  incident_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '关联事件ID',
  plan_id        BIGINT UNSIGNED DEFAULT NULL COMMENT '关联方案ID',
  resource_id    BIGINT UNSIGNED NOT NULL COMMENT '资源ID',
  resource_name  VARCHAR(255) DEFAULT NULL COMMENT '资源名称（冗余）',
  dispatch_qty   INT          NOT NULL DEFAULT 1 COMMENT '调度数量',
  from_location  VARCHAR(255) DEFAULT NULL COMMENT '调出位置',
  to_location    VARCHAR(255) DEFAULT NULL COMMENT '调入位置',
  commander_id   BIGINT UNSIGNED DEFAULT NULL COMMENT '指挥员ID',
  commander_name VARCHAR(64)  DEFAULT NULL COMMENT '指挥员姓名',
  priority       VARCHAR(16)  NOT NULL DEFAULT 'normal' COMMENT '优先级: high/normal/low',
  status         VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '状态: pending待执行/executing执行中/completed已完成/cancelled已取消',
  start_time     DATETIME     DEFAULT NULL COMMENT '开始时间',
  end_time       DATETIME     DEFAULT NULL COMMENT '完成时间',
  remark         VARCHAR(500) DEFAULT NULL COMMENT '备注',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_no (order_no),
  KEY idx_incident (incident_id),
  KEY idx_resource (resource_id),
  KEY idx_status (status),
  KEY idx_commander (commander_id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源调度指令表';

-- ============================================================
-- 7.1 资源锁定表 resource_locks（资源预占与冲突检测）
-- ============================================================
DROP TABLE IF EXISTS resource_locks;
CREATE TABLE resource_locks (
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '锁ID',
  lock_no           VARCHAR(32)  NOT NULL COMMENT '锁定编号',
  resource_id       BIGINT UNSIGNED NOT NULL COMMENT '资源ID',
  resource_name     VARCHAR(255) DEFAULT NULL COMMENT '资源名称（冗余）',
  incident_id       BIGINT UNSIGNED DEFAULT NULL COMMENT '关联灾情ID',
  dispatch_order_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联调度指令ID',
  locked_qty        INT          NOT NULL COMMENT '锁定数量',
  locked_by         BIGINT UNSIGNED DEFAULT NULL COMMENT '锁定人ID',
  locked_by_name    VARCHAR(64)  DEFAULT NULL COMMENT '锁定人姓名',
  status            VARCHAR(20)  NOT NULL DEFAULT 'locked' COMMENT '状态: locked-锁定中/released-已释放/expired-已过期',
  reason            VARCHAR(500) DEFAULT NULL COMMENT '锁定原因',
  expires_at        DATETIME     DEFAULT NULL COMMENT '过期时间（自动释放）',
  locked_at         DATETIME     DEFAULT NULL COMMENT '锁定时间',
  released_at       DATETIME     DEFAULT NULL COMMENT '释放时间',
  created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_lock_no (lock_no),
  KEY idx_resource (resource_id),
  KEY idx_incident (incident_id),
  KEY idx_dispatch (dispatch_order_id),
  KEY idx_status (status),
  KEY idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源锁定记录表';

-- ============================================================
-- 8. 应急方案表 emergency_plans
-- ============================================================
DROP TABLE IF EXISTS emergency_plans;
CREATE TABLE emergency_plans (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '方案ID',
  plan_no        VARCHAR(32)  NOT NULL COMMENT '方案编号',
  title          VARCHAR(255) NOT NULL COMMENT '方案标题',
  incident_id    BIGINT UNSIGNED DEFAULT NULL COMMENT '关联事件ID',
  disaster_type  VARCHAR(32)  DEFAULT NULL COMMENT '灾害类型',
  risk_level     VARCHAR(16)  DEFAULT NULL COMMENT '风险等级',
  area_name      VARCHAR(255) DEFAULT NULL COMMENT '影响区域',
  source         VARCHAR(20)  NOT NULL DEFAULT 'ai' COMMENT '来源: ai-AI生成/manual-人工',
  generated_by   BIGINT UNSIGNED DEFAULT NULL COMMENT '生成人ID',
  status         VARCHAR(20)  NOT NULL DEFAULT 'draft' COMMENT '状态: draft草稿/pending待审批/approved已批准/executing执行中/archived已归档',
  materials      JSON         DEFAULT NULL COMMENT '物资调配方案 JSON',
  teams          JSON         DEFAULT NULL COMMENT '救援队伍方案 JSON',
  shelters       JSON         DEFAULT NULL COMMENT '避难所方案 JSON',
  evacuation     JSON         DEFAULT NULL COMMENT '疏散方案 JSON',
  content        MEDIUMTEXT   DEFAULT NULL COMMENT '方案正文（完整描述）',
  version        INT          NOT NULL DEFAULT 1 COMMENT '版本号',
  parent_id      BIGINT UNSIGNED DEFAULT NULL COMMENT '父方案ID（修订来源）',
  approved_by    BIGINT UNSIGNED DEFAULT NULL COMMENT '审批人ID',
  approved_at    DATETIME     DEFAULT NULL COMMENT '审批时间',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_plan_no (plan_no),
  KEY idx_incident (incident_id),
  KEY idx_disaster_type (disaster_type),
  KEY idx_status (status),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应急方案表';

-- ============================================================
-- 9. 数据源表 data_sources
-- ============================================================
DROP TABLE IF EXISTS data_sources;
CREATE TABLE data_sources (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '数据源ID',
  name         VARCHAR(128) NOT NULL COMMENT '数据源名称',
  code         VARCHAR(64)  NOT NULL COMMENT '数据源编码',
  type         VARCHAR(32)  NOT NULL COMMENT '类型: api/mysql/neo4j/file/crawler',
  url          VARCHAR(500) DEFAULT NULL COMMENT '地址/URL',
  username     VARCHAR(64)  DEFAULT NULL COMMENT '用户名',
  password     VARCHAR(255) DEFAULT NULL COMMENT '密码（加密）',
  db_name      VARCHAR(64)  DEFAULT NULL COMMENT '数据库名',
  params       JSON         DEFAULT NULL COMMENT '连接参数 JSON',
  status       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用',
  description  VARCHAR(500) DEFAULT NULL COMMENT '描述',
  last_sync_at DATETIME     DEFAULT NULL COMMENT '最后同步时间',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_code (code),
  KEY idx_type (type),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据源表';

-- ============================================================
-- 10. Agent 执行记录表 agent_runs
-- ============================================================
DROP TABLE IF EXISTS agent_runs;
CREATE TABLE agent_runs (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '运行ID',
  run_id          VARCHAR(64)  NOT NULL COMMENT '运行唯一标识',
  task_type       VARCHAR(32)  NOT NULL COMMENT '任务类型: risk_assessment/dispatch_plan/knowledge_query',
  workflow_id     VARCHAR(64)  DEFAULT NULL COMMENT 'Dify工作流ID',
  provider        VARCHAR(32)  NOT NULL DEFAULT 'dify' COMMENT '提供者: dify/llm',
  model_name      VARCHAR(128) DEFAULT NULL COMMENT '使用的模型名称',
  incident_id     BIGINT UNSIGNED DEFAULT NULL COMMENT '关联事件ID',
  user_id         BIGINT UNSIGNED DEFAULT NULL COMMENT '触发用户ID',
  status          VARCHAR(20)  NOT NULL DEFAULT 'running' COMMENT '状态: running/success/failed/timeout',
  input_params    JSON         DEFAULT NULL COMMENT '输入参数 JSON',
  output_data     MEDIUMTEXT   DEFAULT NULL COMMENT '输出结果',
  error_message   VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
  duration_ms     BIGINT       DEFAULT NULL COMMENT '耗时(毫秒)',
  token_usage     INT          DEFAULT 0 COMMENT 'Token用量',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  completed_at    DATETIME     DEFAULT NULL COMMENT '完成时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_run_id (run_id),
  KEY idx_task_type (task_type),
  KEY idx_status (status),
  KEY idx_incident (incident_id),
  KEY idx_user (user_id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent执行记录表';

-- ============================================================
-- 11. 引用来源表 citations
-- ============================================================
DROP TABLE IF EXISTS citations;
CREATE TABLE citations (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '引用ID',
  agent_run_id  BIGINT UNSIGNED NOT NULL COMMENT 'Agent运行ID',
  document_id   VARCHAR(64)  DEFAULT NULL COMMENT '文档ID',
  document_name VARCHAR(255) DEFAULT NULL COMMENT '文档名称',
  dataset_id    VARCHAR(64)  DEFAULT NULL COMMENT '知识库ID',
  score         DECIMAL(5,4) DEFAULT NULL COMMENT '相似度得分',
  content       TEXT         DEFAULT NULL COMMENT '引用片段内容',
  source_url    VARCHAR(500) DEFAULT NULL COMMENT '源地址',
  position      INT          DEFAULT 0 COMMENT '引用顺序',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_agent_run (agent_run_id),
  KEY idx_dataset (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='引用来源表';

-- ============================================================
-- 12. 审计日志表 audit_logs
-- ============================================================
DROP TABLE IF EXISTS audit_logs;
CREATE TABLE audit_logs (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  user_id       BIGINT UNSIGNED DEFAULT NULL COMMENT '操作用户ID',
  username      VARCHAR(64)  DEFAULT NULL COMMENT '用户名（冗余）',
  role_code     VARCHAR(32)  DEFAULT NULL COMMENT '角色编码（冗余）',
  module        VARCHAR(64)  NOT NULL COMMENT '模块: auth/incident/resource/plan/system',
  action        VARCHAR(64)  NOT NULL COMMENT '操作: login/logout/create/update/delete/approve/reject',
  target_type   VARCHAR(64)  DEFAULT NULL COMMENT '操作对象类型',
  target_id     VARCHAR(64)  DEFAULT NULL COMMENT '操作对象ID',
  description   VARCHAR(500) DEFAULT NULL COMMENT '操作描述',
  ip_address    VARCHAR(64)  DEFAULT NULL COMMENT 'IP地址',
  user_agent    VARCHAR(500) DEFAULT NULL COMMENT '客户端信息',
  request_url   VARCHAR(500) DEFAULT NULL COMMENT '请求URL',
  request_method VARCHAR(16) DEFAULT NULL COMMENT '请求方法',
  params        JSON         DEFAULT NULL COMMENT '请求参数',
  result        VARCHAR(20)  NOT NULL DEFAULT 'success' COMMENT '结果: success/fail',
  error_msg     VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
  duration_ms   INT          DEFAULT 0 COMMENT '耗时(毫秒)',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_module_action (module, action),
  KEY idx_created_at (created_at),
  KEY idx_result (result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- ============================================================
-- 13. 知识库配置表（Dify 知识库映射）
-- ============================================================
DROP TABLE IF EXISTS knowledge_bases;
CREATE TABLE knowledge_bases (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  kb_id           VARCHAR(64)  NOT NULL COMMENT 'Dify知识库ID',
  name            VARCHAR(128) NOT NULL COMMENT '知识库名称',
  description     VARCHAR(500) DEFAULT NULL COMMENT '描述',
  category        VARCHAR(32)  DEFAULT NULL COMMENT '分类',
  document_count  INT          NOT NULL DEFAULT 0 COMMENT '文档数量',
  status          TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用',
  embedding_model VARCHAR(64)  DEFAULT NULL COMMENT '向量模型',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_kb_id (kb_id),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库配置表';

-- ============================================================
-- 14. 模型配置表
-- ============================================================
DROP TABLE IF EXISTS llm_models;
CREATE TABLE llm_models (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  model_code    VARCHAR(64)  NOT NULL COMMENT '模型编码',
  model_name    VARCHAR(128) NOT NULL COMMENT '模型名称',
  provider      VARCHAR(32)  NOT NULL COMMENT '提供商: deepseek/qwen/openai/...',
  base_url      VARCHAR(255) DEFAULT NULL COMMENT 'API地址',
  api_key       VARCHAR(255) DEFAULT NULL COMMENT 'API密钥（加密）',
  model_type    VARCHAR(32)  NOT NULL DEFAULT 'chat' COMMENT '类型: chat/embedding/image',
  is_active     TINYINT      NOT NULL DEFAULT 0 COMMENT '是否当前启用: 1-是 0-否',
  is_default    TINYINT      NOT NULL DEFAULT 0 COMMENT '是否默认: 1-是 0-否',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态: 1-启用 0-禁用',
  sort_order    INT          NOT NULL DEFAULT 0 COMMENT '排序',
  description   VARCHAR(500) DEFAULT NULL COMMENT '描述',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_model_code (model_code),
  KEY idx_provider (provider),
  KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM模型配置表';
