-- ============================================================
-- 云南省自然灾害应急响应平台 - 完整数据库初始化脚本
-- 适用于 MySQL 5.7+ / 8.0
-- 字符集：utf8mb4
-- 数据库：emergency_auth
-- ============================================================

CREATE DATABASE IF NOT EXISTS emergency_auth
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE emergency_auth;

-- ============================================================
-- 1. users（用户表）
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  username      VARCHAR(40)  NOT NULL COMMENT '用户名',
  password      VARCHAR(100) NOT NULL COMMENT 'BCrypt 密码哈希',
  real_name     VARCHAR(60)  DEFAULT NULL COMMENT '真实姓名',
  email         VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  phone         VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
  avatar        VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  role_code     VARCHAR(64)  DEFAULT NULL COMMENT '角色编码（reporter/commander/resmanager/admin）',
  department    VARCHAR(128) DEFAULT NULL COMMENT '所属部门',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  last_login_at DATETIME     DEFAULT NULL COMMENT '最后登录时间',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username),
  KEY idx_role_code (role_code),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- ============================================================
-- 2. roles（角色表）
-- ============================================================
CREATE TABLE IF NOT EXISTS roles (
  id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  role_code   VARCHAR(64)  NOT NULL COMMENT '角色编码（唯一）',
  role_name   VARCHAR(64)  NOT NULL COMMENT '角色名称',
  description VARCHAR(255) DEFAULT NULL COMMENT '角色描述',
  sort_order  INT          NOT NULL DEFAULT 0 COMMENT '排序号',
  status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ============================================================
-- 3. locations（地理位置表）
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
  id         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  name       VARCHAR(128) NOT NULL COMMENT '地点名称',
  admin_code VARCHAR(32)  DEFAULT NULL COMMENT '行政区划编码',
  level      VARCHAR(16)  DEFAULT NULL COMMENT '行政级别（province/city/county/town）',
  parent_id  BIGINT       DEFAULT NULL COMMENT '父级ID',
  lng        DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  lat        DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  status     TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_parent_id (parent_id),
  KEY idx_admin_code (admin_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='地理位置表';

-- ============================================================
-- 4. incidents（灾情事件表）
-- ============================================================
CREATE TABLE IF NOT EXISTS incidents (
  id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  incident_no     VARCHAR(40)  NOT NULL COMMENT '灾情编号',
  title           VARCHAR(255) NOT NULL COMMENT '灾情标题',
  disaster_type   VARCHAR(32)  DEFAULT NULL COMMENT '灾害类型（earthquake/flood/landslide/...）',
  risk_level      VARCHAR(16)  DEFAULT NULL COMMENT '风险等级（low/medium/high/critical）',
  location_id     BIGINT       DEFAULT NULL COMMENT '位置ID',
  location_name   VARCHAR(128) DEFAULT NULL COMMENT '位置名称（冗余）',
  lng             DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  lat             DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  status          VARCHAR(16)  NOT NULL DEFAULT 'pending' COMMENT '状态',
  source          VARCHAR(32)  DEFAULT NULL COMMENT '来源（report/sensor/manual）',
  reporter_id     BIGINT       DEFAULT NULL COMMENT '上报人ID',
  reviewer_id     BIGINT       DEFAULT NULL COMMENT '审核人ID',
  reviewed_at     DATETIME     DEFAULT NULL COMMENT '审核时间',
  occurred_at     DATETIME     DEFAULT NULL COMMENT '发生时间',
  description     TEXT         DEFAULT NULL COMMENT '灾情描述',
  affected_people INT          DEFAULT NULL COMMENT '受影响人数',
  damage_degree   VARCHAR(32)  DEFAULT NULL COMMENT '损坏程度',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_incident_no (incident_no),
  KEY idx_status (status),
  KEY idx_disaster_type (disaster_type),
  KEY idx_reporter_id (reporter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情事件表';

-- ============================================================
-- 5. incident_reports（灾情上报表）
-- ============================================================
CREATE TABLE IF NOT EXISTS incident_reports (
  id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  incident_id     BIGINT       DEFAULT NULL COMMENT '关联灾情ID',
  title           VARCHAR(255) NOT NULL COMMENT '上报标题',
  disaster_type   VARCHAR(32)  DEFAULT NULL COMMENT '灾害类型',
  risk_level      VARCHAR(16)  DEFAULT NULL COMMENT '风险等级',
  location_name   VARCHAR(128) DEFAULT NULL COMMENT '位置名称',
  lng             DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  lat             DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  reporter_id     BIGINT       DEFAULT NULL COMMENT '上报人ID',
  reporter_name   VARCHAR(64)  DEFAULT NULL COMMENT '上报人姓名',
  contact         VARCHAR(64)  DEFAULT NULL COMMENT '联系方式',
  description     TEXT         DEFAULT NULL COMMENT '灾情描述',
  affected_people INT          DEFAULT NULL COMMENT '受灾人数',
  city            VARCHAR(64)  DEFAULT NULL COMMENT '城市',
  district        VARCHAR(64)  DEFAULT NULL COMMENT '区县',
  street          VARCHAR(64)  DEFAULT NULL COMMENT '街道',
  address         VARCHAR(255) DEFAULT NULL COMMENT '详细地址',
  road_name       VARCHAR(128) DEFAULT NULL COMMENT '道路名称',
  images          JSON         DEFAULT NULL COMMENT '图片URL列表（JSON数组）',
  status          VARCHAR(16)  NOT NULL DEFAULT 'pending' COMMENT '审核状态',
  reviewer_id     BIGINT       DEFAULT NULL COMMENT '审核人ID',
  review_comment  VARCHAR(500) DEFAULT NULL COMMENT '审核意见',
  reviewed_at     DATETIME     DEFAULT NULL COMMENT '审核时间',
  occurred_at     DATETIME     DEFAULT NULL COMMENT '发生时间',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_incident_id (incident_id),
  KEY idx_status (status),
  KEY idx_reporter_id (reporter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情上报表';

-- ============================================================
-- 6. resources（应急资源表）
-- ============================================================
CREATE TABLE IF NOT EXISTS resources (
  id             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  resource_no    VARCHAR(40)  NOT NULL COMMENT '资源编号',
  name           VARCHAR(128) NOT NULL COMMENT '资源名称',
  category       VARCHAR(32)  DEFAULT NULL COMMENT '资源分类（material/team/equipment/shelter）',
  resource_type  VARCHAR(32)  DEFAULT NULL COMMENT '资源细类',
  description    VARCHAR(500) DEFAULT NULL COMMENT '资源描述',
  location_id    BIGINT       DEFAULT NULL COMMENT '位置ID',
  location_name  VARCHAR(128) DEFAULT NULL COMMENT '位置名称（冗余）',
  lng            DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  lat            DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  capacity       INT          DEFAULT NULL COMMENT '总容量',
  available_qty  INT          DEFAULT NULL COMMENT '可用数量',
  manager_id     BIGINT       DEFAULT NULL COMMENT '管理人ID',
  manager_name   VARCHAR(64)  DEFAULT NULL COMMENT '管理人姓名',
  contact        VARCHAR(64)  DEFAULT NULL COMMENT '联系方式',
  status         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1可用 0不可用',
  properties     JSON         DEFAULT NULL COMMENT '扩展属性（JSON）',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_resource_no (resource_no),
  KEY idx_category (category),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应急资源表';

-- ============================================================
-- 7. resource_locks（资源锁定记录表）
-- ============================================================
CREATE TABLE IF NOT EXISTS resource_locks (
  id                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  lock_no           VARCHAR(40)  NOT NULL COMMENT '锁定编号',
  resource_id       BIGINT       DEFAULT NULL COMMENT '资源ID',
  resource_name     VARCHAR(128) DEFAULT NULL COMMENT '资源名称（冗余）',
  incident_id       BIGINT       DEFAULT NULL COMMENT '关联灾情ID',
  dispatch_order_id BIGINT       DEFAULT NULL COMMENT '关联调度指令ID',
  locked_qty        INT          DEFAULT NULL COMMENT '锁定数量',
  locked_by         BIGINT       DEFAULT NULL COMMENT '锁定人ID',
  locked_by_name    VARCHAR(64)  DEFAULT NULL COMMENT '锁定人姓名',
  status            VARCHAR(16)  NOT NULL DEFAULT 'locked' COMMENT '状态：locked/released/expired',
  reason            VARCHAR(255) DEFAULT NULL COMMENT '锁定原因',
  expires_at        DATETIME     DEFAULT NULL COMMENT '过期时间',
  locked_at         DATETIME     DEFAULT NULL COMMENT '锁定时间',
  released_at       DATETIME     DEFAULT NULL COMMENT '释放时间',
  created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_lock_no (lock_no),
  KEY idx_resource_id (resource_id),
  KEY idx_status (status),
  KEY idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源锁定记录表';

-- ============================================================
-- 8. dispatch_orders（调度指令表）
-- ============================================================
CREATE TABLE IF NOT EXISTS dispatch_orders (
  id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  order_no        VARCHAR(40)  NOT NULL COMMENT '调度指令编号',
  incident_id     BIGINT       DEFAULT NULL COMMENT '关联灾情ID',
  plan_id         BIGINT       DEFAULT NULL COMMENT '关联应急预案ID',
  resource_id     BIGINT       DEFAULT NULL COMMENT '关联资源ID',
  resource_name   VARCHAR(128) DEFAULT NULL COMMENT '资源名称（冗余）',
  dispatch_qty    INT          DEFAULT NULL COMMENT '调度数量',
  from_location   VARCHAR(128) DEFAULT NULL COMMENT '出发地',
  to_location     VARCHAR(128) DEFAULT NULL COMMENT '目的地',
  commander_id    BIGINT       DEFAULT NULL COMMENT '指挥员ID',
  commander_name  VARCHAR(64)  DEFAULT NULL COMMENT '指挥员姓名',
  priority        VARCHAR(16)  DEFAULT NULL COMMENT '优先级（low/medium/high/urgent）',
  status          VARCHAR(16)  NOT NULL DEFAULT 'pending' COMMENT '状态',
  start_time      DATETIME     DEFAULT NULL COMMENT '开始时间',
  end_time        DATETIME     DEFAULT NULL COMMENT '结束时间',
  remark          VARCHAR(500) DEFAULT NULL COMMENT '备注',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_no (order_no),
  KEY idx_incident_id (incident_id),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调度指令表';

-- ============================================================
-- 9. emergency_plans（应急预案表）
-- ============================================================
CREATE TABLE IF NOT EXISTS emergency_plans (
  id           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  plan_no      VARCHAR(40)  NOT NULL COMMENT '预案编号',
  title        VARCHAR(255) NOT NULL COMMENT '预案标题',
  incident_id  BIGINT       DEFAULT NULL COMMENT '关联灾情ID',
  disaster_type VARCHAR(32) DEFAULT NULL COMMENT '灾害类型',
  risk_level   VARCHAR(16)  DEFAULT NULL COMMENT '风险等级',
  area_name    VARCHAR(128) DEFAULT NULL COMMENT '区域名称',
  source       VARCHAR(32)  DEFAULT NULL COMMENT '来源（ai/manual/import）',
  generated_by BIGINT       DEFAULT NULL COMMENT '生成人ID',
  status       VARCHAR(16)  NOT NULL DEFAULT 'draft' COMMENT '状态：draft/approved/archived',
  materials    JSON         DEFAULT NULL COMMENT '物资清单（JSON数组）',
  teams        JSON         DEFAULT NULL COMMENT '救援队伍（JSON数组）',
  shelters     JSON         DEFAULT NULL COMMENT '避难场所（JSON数组）',
  evacuation   JSON         DEFAULT NULL COMMENT '疏散方案（JSON对象）',
  content      MEDIUMTEXT   DEFAULT NULL COMMENT '预案内容',
  version      INT          NOT NULL DEFAULT 1 COMMENT '版本号',
  parent_id    BIGINT       DEFAULT NULL COMMENT '父级预案ID（用于版本管理）',
  approved_by  BIGINT       DEFAULT NULL COMMENT '审批人ID',
  approved_at  DATETIME     DEFAULT NULL COMMENT '审批时间',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_plan_no (plan_no),
  KEY idx_incident_id (incident_id),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应急预案表';

-- ============================================================
-- 10. knowledge_bases（知识库表）
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_bases (
  id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  kb_id           VARCHAR(64)  NOT NULL COMMENT '知识库业务ID（Dify dataset_id）',
  name            VARCHAR(128) NOT NULL COMMENT '知识库名称',
  description     VARCHAR(500) DEFAULT NULL COMMENT '知识库描述',
  category        VARCHAR(32)  DEFAULT NULL COMMENT '分类',
  document_count  INT          NOT NULL DEFAULT 0 COMMENT '文档数量',
  status          TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  embedding_model VARCHAR(64)  DEFAULT NULL COMMENT 'Embedding 模型',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_kb_id (kb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

-- ============================================================
-- 11. data_sources（外部数据源表）
-- ============================================================
CREATE TABLE IF NOT EXISTS data_sources (
  id           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  name         VARCHAR(128) NOT NULL COMMENT '数据源名称',
  code         VARCHAR(64)  NOT NULL COMMENT '数据源编码',
  type         VARCHAR(32)  NOT NULL COMMENT '类型（api/db/file/crawler）',
  url          VARCHAR(255) DEFAULT NULL COMMENT '访问地址',
  username     VARCHAR(64)  DEFAULT NULL COMMENT '账号',
  password     VARCHAR(255) DEFAULT NULL COMMENT '密码/Token（加密存储）',
  db_name      VARCHAR(64)  DEFAULT NULL COMMENT '数据库名/表名',
  params       JSON         DEFAULT NULL COMMENT '扩展参数（JSON）',
  status       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  description  VARCHAR(500) DEFAULT NULL COMMENT '描述',
  last_sync_at DATETIME     DEFAULT NULL COMMENT '最后同步时间',
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部数据源表';

-- ============================================================
-- 12. llm_models（LLM 模型配置表）
-- ============================================================
CREATE TABLE IF NOT EXISTS llm_models (
  id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  model_code  VARCHAR(64)  NOT NULL COMMENT '模型编码（唯一）',
  model_name  VARCHAR(128) NOT NULL COMMENT '模型名称',
  provider    VARCHAR(32)  NOT NULL COMMENT '服务商（qwen/deepseek/openai/dify/...）',
  base_url    VARCHAR(255) DEFAULT NULL COMMENT 'API 地址',
  api_key     VARCHAR(255) DEFAULT NULL COMMENT 'API Key（加密存储）',
  model_type  VARCHAR(32)  DEFAULT NULL COMMENT '模型类型（chat/embedding/rerank）',
  is_active   TINYINT      NOT NULL DEFAULT 1 COMMENT '是否启用：1是 0否',
  is_default  TINYINT      NOT NULL DEFAULT 0 COMMENT '是否默认：1是 0否',
  status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  sort_order  INT          NOT NULL DEFAULT 0 COMMENT '排序号',
  description VARCHAR(500) DEFAULT NULL COMMENT '描述',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_model_code (model_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 模型配置表';

-- ============================================================
-- 13. agent_runs（AI Agent 执行记录表）
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_runs (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  run_id        VARCHAR(64)  NOT NULL COMMENT '运行实例ID（UUID）',
  task_type     VARCHAR(32)  NOT NULL COMMENT '任务类型（extract_plan/dispatch/match/...）',
  workflow_id   VARCHAR(64)  DEFAULT NULL COMMENT 'Dify Workflow ID',
  provider      VARCHAR(32)  DEFAULT NULL COMMENT 'AI 服务商',
  model_name    VARCHAR(64)  DEFAULT NULL COMMENT '使用的模型',
  incident_id   BIGINT       DEFAULT NULL COMMENT '关联灾情ID',
  user_id       BIGINT       DEFAULT NULL COMMENT '发起用户ID',
  status        VARCHAR(16)  NOT NULL DEFAULT 'running' COMMENT '状态：running/success/failed',
  input_params  JSON         DEFAULT NULL COMMENT '输入参数（JSON）',
  output_data   MEDIUMTEXT   DEFAULT NULL COMMENT '输出数据（JSON字符串）',
  error_message TEXT         DEFAULT NULL COMMENT '错误信息',
  duration_ms   BIGINT       DEFAULT NULL COMMENT '耗时（毫秒）',
  token_usage   INT          DEFAULT NULL COMMENT 'Token 消耗',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  completed_at  DATETIME     DEFAULT NULL COMMENT '完成时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_run_id (run_id),
  KEY idx_task_type (task_type),
  KEY idx_status (status),
  KEY idx_incident_id (incident_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent 执行记录表';

-- ============================================================
-- 14. citations（引用记录表）
-- ============================================================
CREATE TABLE IF NOT EXISTS citations (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  agent_run_id  BIGINT       NOT NULL COMMENT '关联 Agent Run ID',
  document_id   VARCHAR(128) DEFAULT NULL COMMENT '文档ID',
  document_name VARCHAR(255) DEFAULT NULL COMMENT '文档名称',
  dataset_id    VARCHAR(64)  DEFAULT NULL COMMENT '知识库ID',
  score         DECIMAL(5,4) DEFAULT NULL COMMENT '相似度分数',
  content       TEXT         DEFAULT NULL COMMENT '引用内容',
  source_url    VARCHAR(500) DEFAULT NULL COMMENT '原文链接',
  position      INT          DEFAULT NULL COMMENT '引用位置',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_agent_run_id (agent_run_id),
  KEY idx_dataset_id (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库引用记录表';

-- ============================================================
-- 15. audit_logs（审计日志表）
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
  id             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  user_id        BIGINT       DEFAULT NULL COMMENT '操作用户ID',
  username       VARCHAR(64)  DEFAULT NULL COMMENT '操作用户名',
  role_code      VARCHAR(64)  DEFAULT NULL COMMENT '操作角色',
  module         VARCHAR(32)  DEFAULT NULL COMMENT '模块名',
  action         VARCHAR(32)  DEFAULT NULL COMMENT '操作类型（create/update/delete/login/...）',
  target_type    VARCHAR(32)  DEFAULT NULL COMMENT '目标类型',
  target_id      VARCHAR(64)  DEFAULT NULL COMMENT '目标ID',
  description    VARCHAR(500) DEFAULT NULL COMMENT '操作描述',
  ip_address     VARCHAR(64)  DEFAULT NULL COMMENT '操作IP',
  user_agent     VARCHAR(500) DEFAULT NULL COMMENT '浏览器UA',
  request_url    VARCHAR(500) DEFAULT NULL COMMENT '请求URL',
  request_method VARCHAR(8)   DEFAULT NULL COMMENT '请求方法',
  params         JSON         DEFAULT NULL COMMENT '请求参数（JSON）',
  result         VARCHAR(16)  DEFAULT NULL COMMENT '操作结果（success/failure）',
  error_msg      TEXT         DEFAULT NULL COMMENT '错误信息',
  duration_ms    INT          DEFAULT NULL COMMENT '耗时（毫秒）',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_user_id (user_id),
  KEY idx_module (module),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- ============================================================
-- 16. disaster_situation（灾情态势聚合表）
-- 前端灾情大屏直接从此表读取，由后端在事件变更时刷新
-- ============================================================
CREATE TABLE IF NOT EXISTS disaster_situation (
  id                     BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  total_count            INT          NOT NULL DEFAULT 0 COMMENT '总事件数',
  pending_count          INT          NOT NULL DEFAULT 0 COMMENT '待核验数',
  confirmed_count        INT          NOT NULL DEFAULT 0 COMMENT '已确认数',
  processing_count       INT          NOT NULL DEFAULT 0 COMMENT '处置中数',
  completed_count        INT          NOT NULL DEFAULT 0 COMMENT '已结束数',
  high_risk_count        INT          NOT NULL DEFAULT 0 COMMENT '高风险未结束数',
  total_affected         INT          NOT NULL DEFAULT 0 COMMENT '受灾总人数',
  available_resources    INT          NOT NULL DEFAULT 0 COMMENT '可用资源数',
  rescue_teams           INT          NOT NULL DEFAULT 0 COMMENT '救援队伍数',
  type_distribution      JSON         DEFAULT NULL COMMENT '灾害类型分布 {"地震":5,"山洪":3,...}',
  city_distribution      JSON         DEFAULT NULL COMMENT '各地市灾害数量 [{"city":"昆明市","count":3},...]',
  weekly_trend           JSON         DEFAULT NULL COMMENT '近7日灾害趋势 [{"date":"07-20","count":2},...]',
  realtime_events        JSON         DEFAULT NULL COMMENT '实时事件流（最新N条摘要）',
  refreshed_at           DATETIME     DEFAULT NULL COMMENT '最后刷新时间',
  created_at             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情态势聚合表';

-- ============================================================
-- 初始化数据
-- ============================================================

-- 角色数据
INSERT IGNORE INTO roles (role_code, role_name, description, sort_order, status) VALUES
  ('reporter',   '信息员',     '负责灾情信息上报',     1, 1),
  ('commander',  '指挥员',     '负责应急指挥与调度',   2, 1),
  ('resmanager', '资源管理员', '负责应急资源管理',     3, 1),
  ('admin',      '系统管理员', '负责系统管理与配置',   4, 1);

-- 4 个默认用户（密码统一为 123456，BCrypt 哈希 cost=10）
-- 哈希值通过 BCryptPasswordEncoder.encode("123456") 生成
INSERT IGNORE INTO users
  (username, password, real_name, role_code, status, phone)
VALUES
  ('reporter',   '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '张信息', 'reporter',   1, '13800000001'),
  ('commander',  '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '李指挥', 'commander',  1, '13800000002'),
  ('resmanager', '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '王资源', 'resmanager', 1, '13800000003'),
  ('admin',      '$2b$10$5JW5WOWOqnAYG0wbrJrVYOdAQXlGrTbT.ep2Y25c9RhgfBDBQxE7S', '赵管理', 'admin',      1, '13800000004');
