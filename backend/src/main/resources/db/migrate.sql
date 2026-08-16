-- ============================================================
-- 数据库迁移脚本：把现有库补齐到与 Java 实体一致
-- 适用：现有 emergency_auth 库（部分表缺列）
-- 原则：每条 ALTER 都用存储过程判断列是否存在，缺则加，存在则跳过
-- 执行：选中 emergency_auth 库后，整段粘贴运行
-- ============================================================

USE emergency_auth;

-- 通用：检查列是否存在，存在则跳过
DROP PROCEDURE IF EXISTS add_col_if_missing;
DELIMITER //
CREATE PROCEDURE add_col_if_missing(
  IN p_table VARCHAR(64),
  IN p_column VARCHAR(64),
  IN p_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table
      AND COLUMN_NAME = p_column
  ) THEN
    SET @sql = CONCAT('ALTER TABLE ', p_table, ' ADD COLUMN ', p_column, ' ', p_definition);
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END //
DELIMITER ;

-- ============================================================
-- users 表
-- ============================================================
CALL add_col_if_missing('users', 'real_name',     'VARCHAR(60)  DEFAULT NULL COMMENT "真实姓名" AFTER password');
CALL add_col_if_missing('users', 'email',         'VARCHAR(128) DEFAULT NULL COMMENT "邮箱" AFTER real_name');
CALL add_col_if_missing('users', 'phone',         'VARCHAR(20)  DEFAULT NULL COMMENT "手机号" AFTER email');
CALL add_col_if_missing('users', 'avatar',        'VARCHAR(255) DEFAULT NULL COMMENT "头像URL" AFTER phone');
CALL add_col_if_missing('users', 'role_code',     'VARCHAR(64)  DEFAULT NULL COMMENT "角色编码" AFTER avatar');
CALL add_col_if_missing('users', 'department',    'VARCHAR(128) DEFAULT NULL COMMENT "部门" AFTER role_code');
CALL add_col_if_missing('users', 'status',        'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态 1启用 0禁用" AFTER department');
CALL add_col_if_missing('users', 'last_login_at', 'DATETIME     DEFAULT NULL COMMENT "最后登录时间" AFTER status');
CALL add_col_if_missing('users', 'created_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER last_login_at');
CALL add_col_if_missing('users', 'updated_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- roles 表
-- ============================================================
CALL add_col_if_missing('roles', 'description', 'VARCHAR(255) DEFAULT NULL COMMENT "角色描述" AFTER role_name');
CALL add_col_if_missing('roles', 'sort_order',  'INT          NOT NULL DEFAULT 0 COMMENT "排序号" AFTER description');
CALL add_col_if_missing('roles', 'status',      'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态 1启用 0禁用" AFTER sort_order');
CALL add_col_if_missing('roles', 'created_at',  'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER status');
CALL add_col_if_missing('roles', 'updated_at',  'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- locations 表
-- ============================================================
CALL add_col_if_missing('locations', 'admin_code', 'VARCHAR(32)  DEFAULT NULL COMMENT "行政区划编码" AFTER name');
CALL add_col_if_missing('locations', 'level',      'VARCHAR(16)  DEFAULT NULL COMMENT "行政级别" AFTER admin_code');
CALL add_col_if_missing('locations', 'parent_id',  'BIGINT       DEFAULT NULL COMMENT "父级ID" AFTER level');
CALL add_col_if_missing('locations', 'lng',        'DECIMAL(10,6) DEFAULT NULL COMMENT "经度" AFTER parent_id');
CALL add_col_if_missing('locations', 'lat',        'DECIMAL(10,6) DEFAULT NULL COMMENT "纬度" AFTER lng');
CALL add_col_if_missing('locations', 'status',     'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态" AFTER lat');
CALL add_col_if_missing('locations', 'created_at', 'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER status');
CALL add_col_if_missing('locations', 'updated_at', 'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- incidents 表
-- ============================================================
CALL add_col_if_missing('incidents', 'incident_no',     'VARCHAR(40)  NOT NULL DEFAULT "" COMMENT "灾情编号" AFTER id');
CALL add_col_if_missing('incidents', 'title',           'VARCHAR(255) NOT NULL DEFAULT "" COMMENT "灾情标题" AFTER incident_no');
CALL add_col_if_missing('incidents', 'disaster_type',   'VARCHAR(32)  DEFAULT NULL COMMENT "灾害类型" AFTER title');
CALL add_col_if_missing('incidents', 'risk_level',      'VARCHAR(16)  DEFAULT NULL COMMENT "风险等级" AFTER disaster_type');
CALL add_col_if_missing('incidents', 'location_id',     'BIGINT       DEFAULT NULL COMMENT "位置ID" AFTER risk_level');
CALL add_col_if_missing('incidents', 'location_name',   'VARCHAR(128) DEFAULT NULL COMMENT "位置名称" AFTER location_id');
CALL add_col_if_missing('incidents', 'lng',             'DECIMAL(10,6) DEFAULT NULL COMMENT "经度" AFTER location_name');
CALL add_col_if_missing('incidents', 'lat',             'DECIMAL(10,6) DEFAULT NULL COMMENT "纬度" AFTER lng');
CALL add_col_if_missing('incidents', 'status',          'VARCHAR(16)  NOT NULL DEFAULT "pending" COMMENT "状态" AFTER lat');
CALL add_col_if_missing('incidents', 'source',          'VARCHAR(32)  DEFAULT NULL COMMENT "来源" AFTER status');
CALL add_col_if_missing('incidents', 'reporter_id',     'BIGINT       DEFAULT NULL COMMENT "上报人ID" AFTER source');
CALL add_col_if_missing('incidents', 'reviewer_id',     'BIGINT       DEFAULT NULL COMMENT "审核人ID" AFTER reporter_id');
CALL add_col_if_missing('incidents', 'reviewed_at',     'DATETIME     DEFAULT NULL COMMENT "审核时间" AFTER reviewer_id');
CALL add_col_if_missing('incidents', 'occurred_at',     'DATETIME     DEFAULT NULL COMMENT "发生时间" AFTER reviewed_at');
CALL add_col_if_missing('incidents', 'description',     'TEXT         DEFAULT NULL COMMENT "灾情描述" AFTER occurred_at');
CALL add_col_if_missing('incidents', 'affected_people', 'INT          DEFAULT NULL COMMENT "受影响人数" AFTER description');
CALL add_col_if_missing('incidents', 'damage_degree',   'VARCHAR(32)  DEFAULT NULL COMMENT "损坏程度" AFTER affected_people');
CALL add_col_if_missing('incidents', 'created_at',      'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER damage_degree');
CALL add_col_if_missing('incidents', 'updated_at',      'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- incident_reports 表
-- ============================================================
CALL add_col_if_missing('incident_reports', 'incident_id',    'BIGINT       DEFAULT NULL COMMENT "关联灾情ID" AFTER id');
CALL add_col_if_missing('incident_reports', 'title',          'VARCHAR(255) NOT NULL DEFAULT "" COMMENT "上报标题" AFTER incident_id');
CALL add_col_if_missing('incident_reports', 'disaster_type',  'VARCHAR(32)  DEFAULT NULL COMMENT "灾害类型" AFTER title');
CALL add_col_if_missing('incident_reports', 'risk_level',     'VARCHAR(16)  DEFAULT NULL COMMENT "风险等级" AFTER disaster_type');
CALL add_col_if_missing('incident_reports', 'location_name',  'VARCHAR(128) DEFAULT NULL COMMENT "位置名称" AFTER risk_level');
CALL add_col_if_missing('incident_reports', 'lng',            'DECIMAL(10,6) DEFAULT NULL COMMENT "经度" AFTER location_name');
CALL add_col_if_missing('incident_reports', 'lat',            'DECIMAL(10,6) DEFAULT NULL COMMENT "纬度" AFTER lng');
CALL add_col_if_missing('incident_reports', 'reporter_id',    'BIGINT       DEFAULT NULL COMMENT "上报人ID" AFTER lat');
CALL add_col_if_missing('incident_reports', 'reporter_name',  'VARCHAR(64)  DEFAULT NULL COMMENT "上报人姓名" AFTER reporter_id');
CALL add_col_if_missing('incident_reports', 'contact',        'VARCHAR(64)  DEFAULT NULL COMMENT "联系方式" AFTER reporter_name');
CALL add_col_if_missing('incident_reports', 'description',    'TEXT         DEFAULT NULL COMMENT "灾情描述" AFTER contact');
CALL add_col_if_missing('incident_reports', 'images',         'JSON         DEFAULT NULL COMMENT "图片URL列表" AFTER description');
CALL add_col_if_missing('incident_reports', 'status',         'VARCHAR(16)  NOT NULL DEFAULT "pending" COMMENT "审核状态" AFTER images');
CALL add_col_if_missing('incident_reports', 'reviewer_id',    'BIGINT       DEFAULT NULL COMMENT "审核人ID" AFTER status');
CALL add_col_if_missing('incident_reports', 'review_comment', 'VARCHAR(500) DEFAULT NULL COMMENT "审核意见" AFTER reviewer_id');
CALL add_col_if_missing('incident_reports', 'reviewed_at',    'DATETIME     DEFAULT NULL COMMENT "审核时间" AFTER review_comment');
CALL add_col_if_missing('incident_reports', 'occurred_at',    'DATETIME     DEFAULT NULL COMMENT "发生时间" AFTER reviewed_at');
CALL add_col_if_missing('incident_reports', 'created_at',     'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER occurred_at');
CALL add_col_if_missing('incident_reports', 'updated_at',     'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- resources 表
-- ============================================================
CALL add_col_if_missing('resources', 'resource_no',   'VARCHAR(40)  NOT NULL DEFAULT "" COMMENT "资源编号" AFTER id');
CALL add_col_if_missing('resources', 'name',          'VARCHAR(128) NOT NULL DEFAULT "" COMMENT "资源名称" AFTER resource_no');
CALL add_col_if_missing('resources', 'category',      'VARCHAR(32)  DEFAULT NULL COMMENT "资源分类" AFTER name');
CALL add_col_if_missing('resources', 'resource_type', 'VARCHAR(32)  DEFAULT NULL COMMENT "资源细类" AFTER category');
CALL add_col_if_missing('resources', 'description',   'VARCHAR(500) DEFAULT NULL COMMENT "资源描述" AFTER resource_type');
CALL add_col_if_missing('resources', 'location_id',   'BIGINT       DEFAULT NULL COMMENT "位置ID" AFTER description');
CALL add_col_if_missing('resources', 'location_name', 'VARCHAR(128) DEFAULT NULL COMMENT "位置名称" AFTER location_id');
CALL add_col_if_missing('resources', 'lng',           'DECIMAL(10,6) DEFAULT NULL COMMENT "经度" AFTER location_name');
CALL add_col_if_missing('resources', 'lat',           'DECIMAL(10,6) DEFAULT NULL COMMENT "纬度" AFTER lng');
CALL add_col_if_missing('resources', 'capacity',      'INT          DEFAULT NULL COMMENT "总容量" AFTER lat');
CALL add_col_if_missing('resources', 'available_qty', 'INT          DEFAULT NULL COMMENT "可用数量" AFTER capacity');
CALL add_col_if_missing('resources', 'manager_id',    'BIGINT       DEFAULT NULL COMMENT "管理人ID" AFTER available_qty');
CALL add_col_if_missing('resources', 'manager_name',  'VARCHAR(64)  DEFAULT NULL COMMENT "管理人姓名" AFTER manager_id');
CALL add_col_if_missing('resources', 'contact',       'VARCHAR(64)  DEFAULT NULL COMMENT "联系方式" AFTER manager_name');
CALL add_col_if_missing('resources', 'status',        'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态" AFTER contact');
CALL add_col_if_missing('resources', 'properties',    'JSON         DEFAULT NULL COMMENT "扩展属性" AFTER status');
CALL add_col_if_missing('resources', 'created_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER properties');
CALL add_col_if_missing('resources', 'updated_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- resource_locks 表
-- ============================================================
CALL add_col_if_missing('resource_locks', 'lock_no',           'VARCHAR(40)  NOT NULL DEFAULT "" COMMENT "锁定编号" AFTER id');
CALL add_col_if_missing('resource_locks', 'resource_id',       'BIGINT       DEFAULT NULL COMMENT "资源ID" AFTER lock_no');
CALL add_col_if_missing('resource_locks', 'resource_name',     'VARCHAR(128) DEFAULT NULL COMMENT "资源名称" AFTER resource_id');
CALL add_col_if_missing('resource_locks', 'incident_id',       'BIGINT       DEFAULT NULL COMMENT "灾情ID" AFTER resource_name');
CALL add_col_if_missing('resource_locks', 'dispatch_order_id', 'BIGINT       DEFAULT NULL COMMENT "调度指令ID" AFTER incident_id');
CALL add_col_if_missing('resource_locks', 'locked_qty',        'INT          DEFAULT NULL COMMENT "锁定数量" AFTER dispatch_order_id');
CALL add_col_if_missing('resource_locks', 'locked_by',         'BIGINT       DEFAULT NULL COMMENT "锁定人ID" AFTER locked_qty');
CALL add_col_if_missing('resource_locks', 'locked_by_name',    'VARCHAR(64)  DEFAULT NULL COMMENT "锁定人姓名" AFTER locked_by');
CALL add_col_if_missing('resource_locks', 'status',            'VARCHAR(16)  NOT NULL DEFAULT "locked" COMMENT "状态" AFTER locked_by_name');
CALL add_col_if_missing('resource_locks', 'reason',            'VARCHAR(255) DEFAULT NULL COMMENT "锁定原因" AFTER status');
CALL add_col_if_missing('resource_locks', 'expires_at',        'DATETIME     DEFAULT NULL COMMENT "过期时间" AFTER reason');
CALL add_col_if_missing('resource_locks', 'locked_at',         'DATETIME     DEFAULT NULL COMMENT "锁定时间" AFTER expires_at');
CALL add_col_if_missing('resource_locks', 'released_at',       'DATETIME     DEFAULT NULL COMMENT "释放时间" AFTER locked_at');
CALL add_col_if_missing('resource_locks', 'created_at',        'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER released_at');
CALL add_col_if_missing('resource_locks', 'updated_at',        'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- dispatch_orders 表
-- ============================================================
CALL add_col_if_missing('dispatch_orders', 'order_no',       'VARCHAR(40)  NOT NULL DEFAULT "" COMMENT "调度编号" AFTER id');
CALL add_col_if_missing('dispatch_orders', 'incident_id',    'BIGINT       DEFAULT NULL COMMENT "灾情ID" AFTER order_no');
CALL add_col_if_missing('dispatch_orders', 'plan_id',        'BIGINT       DEFAULT NULL COMMENT "预案ID" AFTER incident_id');
CALL add_col_if_missing('dispatch_orders', 'resource_id',    'BIGINT       DEFAULT NULL COMMENT "资源ID" AFTER plan_id');
CALL add_col_if_missing('dispatch_orders', 'resource_name',  'VARCHAR(128) DEFAULT NULL COMMENT "资源名称" AFTER resource_id');
CALL add_col_if_missing('dispatch_orders', 'dispatch_qty',   'INT          DEFAULT NULL COMMENT "调度数量" AFTER resource_name');
CALL add_col_if_missing('dispatch_orders', 'from_location',  'VARCHAR(128) DEFAULT NULL COMMENT "出发地" AFTER dispatch_qty');
CALL add_col_if_missing('dispatch_orders', 'to_location',    'VARCHAR(128) DEFAULT NULL COMMENT "目的地" AFTER from_location');
CALL add_col_if_missing('dispatch_orders', 'commander_id',   'BIGINT       DEFAULT NULL COMMENT "指挥员ID" AFTER to_location');
CALL add_col_if_missing('dispatch_orders', 'commander_name', 'VARCHAR(64)  DEFAULT NULL COMMENT "指挥员姓名" AFTER commander_id');
CALL add_col_if_missing('dispatch_orders', 'priority',       'VARCHAR(16)  DEFAULT NULL COMMENT "优先级" AFTER commander_name');
CALL add_col_if_missing('dispatch_orders', 'status',         'VARCHAR(16)  NOT NULL DEFAULT "pending" COMMENT "状态" AFTER priority');
CALL add_col_if_missing('dispatch_orders', 'start_time',     'DATETIME     DEFAULT NULL COMMENT "开始时间" AFTER status');
CALL add_col_if_missing('dispatch_orders', 'end_time',       'DATETIME     DEFAULT NULL COMMENT "结束时间" AFTER start_time');
CALL add_col_if_missing('dispatch_orders', 'remark',         'VARCHAR(500) DEFAULT NULL COMMENT "备注" AFTER end_time');
CALL add_col_if_missing('dispatch_orders', 'created_at',     'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER remark');
CALL add_col_if_missing('dispatch_orders', 'updated_at',     'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- emergency_plans 表
-- ============================================================
CALL add_col_if_missing('emergency_plans', 'plan_no',       'VARCHAR(40)  NOT NULL DEFAULT "" COMMENT "预案编号" AFTER id');
CALL add_col_if_missing('emergency_plans', 'title',         'VARCHAR(255) NOT NULL DEFAULT "" COMMENT "预案标题" AFTER plan_no');
CALL add_col_if_missing('emergency_plans', 'incident_id',   'BIGINT       DEFAULT NULL COMMENT "灾情ID" AFTER title');
CALL add_col_if_missing('emergency_plans', 'disaster_type', 'VARCHAR(32)  DEFAULT NULL COMMENT "灾害类型" AFTER incident_id');
CALL add_col_if_missing('emergency_plans', 'risk_level',    'VARCHAR(16)  DEFAULT NULL COMMENT "风险等级" AFTER disaster_type');
CALL add_col_if_missing('emergency_plans', 'area_name',     'VARCHAR(128) DEFAULT NULL COMMENT "区域名称" AFTER risk_level');
CALL add_col_if_missing('emergency_plans', 'source',        'VARCHAR(32)  DEFAULT NULL COMMENT "来源" AFTER area_name');
CALL add_col_if_missing('emergency_plans', 'generated_by',  'BIGINT       DEFAULT NULL COMMENT "生成人ID" AFTER source');
CALL add_col_if_missing('emergency_plans', 'status',        'VARCHAR(16)  NOT NULL DEFAULT "draft" COMMENT "状态" AFTER generated_by');
CALL add_col_if_missing('emergency_plans', 'materials',     'JSON         DEFAULT NULL COMMENT "物资清单" AFTER status');
CALL add_col_if_missing('emergency_plans', 'teams',         'JSON         DEFAULT NULL COMMENT "救援队伍" AFTER materials');
CALL add_col_if_missing('emergency_plans', 'shelters',      'JSON         DEFAULT NULL COMMENT "避难场所" AFTER teams');
CALL add_col_if_missing('emergency_plans', 'evacuation',    'JSON         DEFAULT NULL COMMENT "疏散方案" AFTER shelters');
CALL add_col_if_missing('emergency_plans', 'short_term_measures', 'JSON DEFAULT NULL COMMENT "短期措施" AFTER evacuation');
CALL add_col_if_missing('emergency_plans', 'mid_term_measures',   'JSON DEFAULT NULL COMMENT "中期措施" AFTER short_term_measures');
CALL add_col_if_missing('emergency_plans', 'long_term_measures',  'JSON DEFAULT NULL COMMENT "长期措施" AFTER mid_term_measures');
CALL add_col_if_missing('emergency_plans', 'remarks',        'TEXT         DEFAULT NULL COMMENT "方案备注" AFTER long_term_measures');
CALL add_col_if_missing('emergency_plans', 'content',       'MEDIUMTEXT   DEFAULT NULL COMMENT "预案内容" AFTER remarks');
CALL add_col_if_missing('emergency_plans', 'version',       'INT          NOT NULL DEFAULT 1 COMMENT "版本号" AFTER content');
CALL add_col_if_missing('emergency_plans', 'parent_id',     'BIGINT       DEFAULT NULL COMMENT "父级预案ID" AFTER version');
CALL add_col_if_missing('emergency_plans', 'approved_by',   'BIGINT       DEFAULT NULL COMMENT "审批人ID" AFTER parent_id');
CALL add_col_if_missing('emergency_plans', 'approved_at',   'DATETIME     DEFAULT NULL COMMENT "审批时间" AFTER approved_by');
CALL add_col_if_missing('emergency_plans', 'created_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER approved_at');
CALL add_col_if_missing('emergency_plans', 'updated_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- knowledge_bases 表
-- ============================================================
CALL add_col_if_missing('knowledge_bases', 'kb_id',           'VARCHAR(64)  NOT NULL DEFAULT "" COMMENT "知识库ID" AFTER id');
CALL add_col_if_missing('knowledge_bases', 'name',            'VARCHAR(128) NOT NULL DEFAULT "" COMMENT "知识库名称" AFTER kb_id');
CALL add_col_if_missing('knowledge_bases', 'description',     'VARCHAR(500) DEFAULT NULL COMMENT "描述" AFTER name');
CALL add_col_if_missing('knowledge_bases', 'category',        'VARCHAR(32)  DEFAULT NULL COMMENT "分类" AFTER description');
CALL add_col_if_missing('knowledge_bases', 'document_count',  'INT          NOT NULL DEFAULT 0 COMMENT "文档数量" AFTER category');
CALL add_col_if_missing('knowledge_bases', 'status',          'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态" AFTER document_count');
CALL add_col_if_missing('knowledge_bases', 'embedding_model', 'VARCHAR(64)  DEFAULT NULL COMMENT "Embedding模型" AFTER status');
CALL add_col_if_missing('knowledge_bases', 'created_at',      'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER embedding_model');
CALL add_col_if_missing('knowledge_bases', 'updated_at',      'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- data_sources 表
-- ============================================================
CALL add_col_if_missing('data_sources', 'name',         'VARCHAR(128) NOT NULL DEFAULT "" COMMENT "数据源名称" AFTER id');
CALL add_col_if_missing('data_sources', 'code',         'VARCHAR(64)  NOT NULL DEFAULT "" COMMENT "数据源编码" AFTER name');
CALL add_col_if_missing('data_sources', 'type',         'VARCHAR(32)  NOT NULL DEFAULT "" COMMENT "类型" AFTER code');
CALL add_col_if_missing('data_sources', 'url',          'VARCHAR(255) DEFAULT NULL COMMENT "访问地址" AFTER type');
CALL add_col_if_missing('data_sources', 'username',     'VARCHAR(64)  DEFAULT NULL COMMENT "账号" AFTER url');
CALL add_col_if_missing('data_sources', 'password',     'VARCHAR(255) DEFAULT NULL COMMENT "密码" AFTER username');
CALL add_col_if_missing('data_sources', 'db_name',      'VARCHAR(64)  DEFAULT NULL COMMENT "库名/表名" AFTER password');
CALL add_col_if_missing('data_sources', 'params',       'JSON         DEFAULT NULL COMMENT "扩展参数" AFTER db_name');
CALL add_col_if_missing('data_sources', 'status',       'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态" AFTER params');
CALL add_col_if_missing('data_sources', 'description',  'VARCHAR(500) DEFAULT NULL COMMENT "描述" AFTER status');
CALL add_col_if_missing('data_sources', 'last_sync_at', 'DATETIME     DEFAULT NULL COMMENT "最后同步时间" AFTER description');
CALL add_col_if_missing('data_sources', 'created_at',   'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER last_sync_at');
CALL add_col_if_missing('data_sources', 'updated_at',   'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- llm_models 表
-- ============================================================
CALL add_col_if_missing('llm_models', 'model_code',  'VARCHAR(64)  NOT NULL DEFAULT "" COMMENT "模型编码" AFTER id');
CALL add_col_if_missing('llm_models', 'model_name',  'VARCHAR(128) NOT NULL DEFAULT "" COMMENT "模型名称" AFTER model_code');
CALL add_col_if_missing('llm_models', 'provider',    'VARCHAR(32)  NOT NULL DEFAULT "" COMMENT "服务商" AFTER model_name');
CALL add_col_if_missing('llm_models', 'base_url',    'VARCHAR(255) DEFAULT NULL COMMENT "API地址" AFTER provider');
CALL add_col_if_missing('llm_models', 'api_key',     'VARCHAR(255) DEFAULT NULL COMMENT "API Key" AFTER base_url');
CALL add_col_if_missing('llm_models', 'model_type',  'VARCHAR(32)  DEFAULT NULL COMMENT "模型类型" AFTER api_key');
CALL add_col_if_missing('llm_models', 'is_active',   'TINYINT      NOT NULL DEFAULT 1 COMMENT "是否启用" AFTER model_type');
CALL add_col_if_missing('llm_models', 'is_default',  'TINYINT      NOT NULL DEFAULT 0 COMMENT "是否默认" AFTER is_active');
CALL add_col_if_missing('llm_models', 'status',      'TINYINT      NOT NULL DEFAULT 1 COMMENT "状态" AFTER is_default');
CALL add_col_if_missing('llm_models', 'sort_order',  'INT          NOT NULL DEFAULT 0 COMMENT "排序" AFTER status');
CALL add_col_if_missing('llm_models', 'description', 'VARCHAR(500) DEFAULT NULL COMMENT "描述" AFTER sort_order');
CALL add_col_if_missing('llm_models', 'created_at',  'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER description');
CALL add_col_if_missing('llm_models', 'updated_at',  'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间" AFTER created_at');

-- ============================================================
-- agent_runs 表
-- ============================================================
CALL add_col_if_missing('agent_runs', 'run_id',        'VARCHAR(64)  NOT NULL DEFAULT "" COMMENT "运行ID" AFTER id');
CALL add_col_if_missing('agent_runs', 'task_type',     'VARCHAR(32)  NOT NULL DEFAULT "" COMMENT "任务类型" AFTER run_id');
CALL add_col_if_missing('agent_runs', 'workflow_id',   'VARCHAR(64)  DEFAULT NULL COMMENT "Workflow ID" AFTER task_type');
CALL add_col_if_missing('agent_runs', 'provider',      'VARCHAR(32)  DEFAULT NULL COMMENT "服务商" AFTER workflow_id');
CALL add_col_if_missing('agent_runs', 'model_name',    'VARCHAR(64)  DEFAULT NULL COMMENT "模型" AFTER provider');
CALL add_col_if_missing('agent_runs', 'incident_id',   'BIGINT       DEFAULT NULL COMMENT "灾情ID" AFTER model_name');
CALL add_col_if_missing('agent_runs', 'user_id',       'BIGINT       DEFAULT NULL COMMENT "用户ID" AFTER incident_id');
CALL add_col_if_missing('agent_runs', 'status',        'VARCHAR(16)  NOT NULL DEFAULT "running" COMMENT "状态" AFTER user_id');
CALL add_col_if_missing('agent_runs', 'input_params',  'JSON         DEFAULT NULL COMMENT "输入参数" AFTER status');
CALL add_col_if_missing('agent_runs', 'output_data',   'MEDIUMTEXT   DEFAULT NULL COMMENT "输出数据" AFTER input_params');
CALL add_col_if_missing('agent_runs', 'error_message', 'TEXT         DEFAULT NULL COMMENT "错误信息" AFTER output_data');
CALL add_col_if_missing('agent_runs', 'duration_ms',   'BIGINT       DEFAULT NULL COMMENT "耗时" AFTER error_message');
CALL add_col_if_missing('agent_runs', 'token_usage',   'INT          DEFAULT NULL COMMENT "Token消耗" AFTER duration_ms');
CALL add_col_if_missing('agent_runs', 'created_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER token_usage');
CALL add_col_if_missing('agent_runs', 'completed_at',  'DATETIME     DEFAULT NULL COMMENT "完成时间" AFTER created_at');

-- ============================================================
-- citations 表
-- ============================================================
CALL add_col_if_missing('citations', 'agent_run_id',  'BIGINT       NOT NULL DEFAULT 0 COMMENT "Agent Run ID" AFTER id');
CALL add_col_if_missing('citations', 'document_id',   'VARCHAR(128) DEFAULT NULL COMMENT "文档ID" AFTER agent_run_id');
CALL add_col_if_missing('citations', 'document_name', 'VARCHAR(255) DEFAULT NULL COMMENT "文档名称" AFTER document_id');
CALL add_col_if_missing('citations', 'dataset_id',    'VARCHAR(64)  DEFAULT NULL COMMENT "知识库ID" AFTER document_name');
CALL add_col_if_missing('citations', 'score',         'DECIMAL(5,4) DEFAULT NULL COMMENT "相似度" AFTER dataset_id');
CALL add_col_if_missing('citations', 'content',       'TEXT         DEFAULT NULL COMMENT "引用内容" AFTER score');
CALL add_col_if_missing('citations', 'source_url',    'VARCHAR(500) DEFAULT NULL COMMENT "原文链接" AFTER content');
CALL add_col_if_missing('citations', 'position',      'INT          DEFAULT NULL COMMENT "引用位置" AFTER source_url');
CALL add_col_if_missing('citations', 'created_at',    'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER position');

-- ============================================================
-- audit_logs 表
-- ============================================================
CALL add_col_if_missing('audit_logs', 'user_id',        'BIGINT       DEFAULT NULL COMMENT "用户ID" AFTER id');
CALL add_col_if_missing('audit_logs', 'username',       'VARCHAR(64)  DEFAULT NULL COMMENT "用户名" AFTER user_id');
CALL add_col_if_missing('audit_logs', 'role_code',      'VARCHAR(64)  DEFAULT NULL COMMENT "角色" AFTER username');
CALL add_col_if_missing('audit_logs', 'module',         'VARCHAR(32)  DEFAULT NULL COMMENT "模块" AFTER role_code');
CALL add_col_if_missing('audit_logs', 'action',         'VARCHAR(32)  DEFAULT NULL COMMENT "操作" AFTER module');
CALL add_col_if_missing('audit_logs', 'target_type',    'VARCHAR(32)  DEFAULT NULL COMMENT "目标类型" AFTER action');
CALL add_col_if_missing('audit_logs', 'target_id',      'VARCHAR(64)  DEFAULT NULL COMMENT "目标ID" AFTER target_type');
CALL add_col_if_missing('audit_logs', 'description',    'VARCHAR(500) DEFAULT NULL COMMENT "描述" AFTER target_id');
CALL add_col_if_missing('audit_logs', 'ip_address',     'VARCHAR(64)  DEFAULT NULL COMMENT "IP" AFTER description');
CALL add_col_if_missing('audit_logs', 'user_agent',     'VARCHAR(500) DEFAULT NULL COMMENT "UA" AFTER ip_address');
CALL add_col_if_missing('audit_logs', 'request_url',    'VARCHAR(500) DEFAULT NULL COMMENT "请求URL" AFTER user_agent');
CALL add_col_if_missing('audit_logs', 'request_method', 'VARCHAR(8)   DEFAULT NULL COMMENT "请求方法" AFTER request_url');
CALL add_col_if_missing('audit_logs', 'params',         'JSON         DEFAULT NULL COMMENT "请求参数" AFTER request_method');
CALL add_col_if_missing('audit_logs', 'result',         'VARCHAR(16)  DEFAULT NULL COMMENT "结果" AFTER params');
CALL add_col_if_missing('audit_logs', 'error_msg',      'TEXT         DEFAULT NULL COMMENT "错误信息" AFTER result');
CALL add_col_if_missing('audit_logs', 'duration_ms',    'INT          DEFAULT NULL COMMENT "耗时" AFTER error_msg');
CALL add_col_if_missing('audit_logs', 'created_at',     'DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间" AFTER duration_ms');

-- ============================================================
-- 数据修复：把 users.role_code 填上（如果之前漏了）
-- ============================================================
UPDATE users u
LEFT JOIN roles r ON r.id = u.role_id
SET u.role_code = r.role_code
WHERE (u.role_code IS NULL OR u.role_code = '')
  AND u.role_id IS NOT NULL;

UPDATE users SET role_code = 'reporter'   WHERE username = 'reporter'   AND (role_code IS NULL OR role_code = '');
UPDATE users SET role_code = 'commander'  WHERE username = 'commander'  AND (role_code IS NULL OR role_code = '');
UPDATE users SET role_code = 'resmanager' WHERE username = 'resmanager' AND (role_code IS NULL OR role_code = '');
UPDATE users SET role_code = 'admin'      WHERE username = 'admin'      AND (role_code IS NULL OR role_code = '');

-- 把老的 status varchar(20) 'ENABLED' 转成 tinyint 1（如已迁移可忽略）
UPDATE users SET status = 1 WHERE status = 'ENABLED' AND data_type_check_failed IS NULL;
-- 如果 status 字段还是 varchar 类型，下面这条会失败，忽略即可
UPDATE users SET status = 0 WHERE status IN ('DISABLED', 'disabled');

-- ============================================================
-- 数据补充：roles 4 个基础角色（如已存在则跳过）
-- ============================================================
INSERT IGNORE INTO roles (role_code, role_name, description, sort_order, status) VALUES
  ('reporter',   '信息员',     '负责灾情信息上报',     1, 1),
  ('commander',  '指挥员',     '负责应急指挥与调度',   2, 1),
  ('resmanager', '资源管理员', '负责应急资源管理',     3, 1),
  ('admin',      '系统管理员', '负责系统管理与配置',   4, 1);

-- ============================================================
-- disaster_situation 表（新增）
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
  type_distribution      JSON         DEFAULT NULL COMMENT '灾害类型分布',
  city_distribution      JSON         DEFAULT NULL COMMENT '各地市灾害数量',
  weekly_trend           JSON         DEFAULT NULL COMMENT '近7日灾害趋势',
  realtime_events        JSON         DEFAULT NULL COMMENT '实时事件流',
  refreshed_at           DATETIME     DEFAULT NULL COMMENT '最后刷新时间',
  created_at             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灾情态势聚合表';

-- ============================================================
-- info 系统综合信息表（大屏 KPI，只有一行记录）
-- ============================================================
CREATE TABLE IF NOT EXISTS info (
  id                  BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  total_disasters     INT          NOT NULL DEFAULT 0 COMMENT '灾害总数',
  in_progress         INT          NOT NULL DEFAULT 0 COMMENT '处置中',
  pending             INT          NOT NULL DEFAULT 0 COMMENT '待审核',
  affected_people     INT          NOT NULL DEFAULT 0 COMMENT '受灾人口',
  available_resources INT          NOT NULL DEFAULT 0 COMMENT '可用资源（物资单品数量之和）',
  rescue_teams        INT          NOT NULL DEFAULT 0 COMMENT '救援队伍数',
  updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统综合信息表';

-- 初始化唯一记录
INSERT IGNORE INTO info (id, total_disasters, in_progress, pending, affected_people, available_resources, rescue_teams)
VALUES (1, 0, 0, 0, 0, 0, 0);

-- ============================================================
-- file 归档文件表
-- ============================================================
CREATE TABLE IF NOT EXISTS `file` (
  id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  content     LONGTEXT     NOT NULL COMMENT '归档内容（JSON 字符串）',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实时事件流归档';

-- ============================================================
-- 清理
-- ============================================================
DROP PROCEDURE IF EXISTS add_col_if_missing;

-- ============================================================
-- 验证
-- ============================================================
SELECT TABLE_NAME, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'emergency_auth'
ORDER BY TABLE_NAME;
