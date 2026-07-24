# ai-service 四角色业务接口实现计划

## Context

ai-service 现有基础已相当完整：Neo4j 图仓库（`graph/repository.py`）、Dify 调度工作流客户端（`agents/dify_client.py`，带模板降级）、Dify 知识库服务（`services/dify_dataset.py`）、节点 CRUD + 调度查询 API。

但缺少四角色完整业务闭环：
- 普通信息员上报灾情（DisasterSpot 字段不足，缺上报人/伤亡/受灾人数/描述）
- 应急指挥人员审核事件（无 Dify 风险评估调用）+ 生成处置方案（降级用模板拼接，用户要求改 DeepSeek/千问）
- 资源管理员只能 Create，缺 Delete/Update/List
- 系统管理员只能管知识库，缺模型/数据源配置管理

本次改造目标：补全四角色业务接口，引入 DeepSeek/千问作为 Dify 失败时的 LLM 降级，模型配置可动态切换。

## 关键设计决策（已与用户确认）

1. **不新增 Vehicle/Person 节点**：资源管理员维护的"人员"= RescueTeam，"车辆"不需要
2. **Shelter 改名**：`remain_space` → `accommodated_count`（已容纳人数），查询逻辑改为 `accommodated_count < max_capacity`
3. **三级降级**：Dify 工作流 → LLM（DeepSeek/千问，可动态切换）→ 模板兜底
4. **灾情上报**：扩展 DisasterSpot 节点属性（保持 snake_case，不新增 Label/关系类型），ai-service 存 Neo4j 并返回完整数据给 SpringBoot 存 SQL
5. **模型配置动态切换**：系统管理员可配置 LLM provider（deepseek/qwen），控制 Dify 失败后的降级行为

## 实施步骤

### 步骤 1：配置层扩展 — [config.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/core/config.py)

新增配置项：
```python
# DeepSeek
DEEPSEEK_API_KEY: str = "sk-acbf853086084ea3a8f1bcd807e073ae"
DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL: str = "deepseek-v4-flash"

# 通义千问
QWEN_API_KEY: str = ""
QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL: str = "qwen-plus"

# LLM 降级 provider（deepseek / qwen），运行时可被 admin 接口动态修改
LLM_PROVIDER: str = "deepseek"

# Dify 风险评估工作流（与调度方案工作流区分）
DIFY_RISK_API_KEY: str = ""
```

同步更新 [.env.example](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/.env.example)。

### 步骤 2：LLM 客户端 — 新建 `app/agents/llm_client.py`

统一 LLM 客户端，支持 deepseek/qwen 动态切换：

```python
class LLMClient:
    """统一 LLM 客户端，支持 DeepSeek / 通义千问动态切换

    作为 Dify 工作流失败时的 LLM 降级方案。
    """
    def __init__(self):
        self._provider = settings.LLM_PROVIDER  # 运行时可改
        self._config = {
            "deepseek": {...},
            "qwen": {...},
        }

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM，返回文本结果。DeepSeek V4 会处理 reasoning_content"""

    def set_provider(self, provider: str): ...
    def get_config(self) -> dict: ...

llm_client = LLMClient()
```

关键点：
- DeepSeek V4 的 `reasoning_content` 字段单独处理（推理过程不返回给用户，只取 `content`）
- 使用 OpenAI 兼容协议（DeepSeek 和千问都兼容）
- 失败时抛异常，由上层捕获后走模板兜底

### 步骤 3：Dify 客户端改造 — [dify_client.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/agents/dify_client.py)

**新增 `run_risk_assessment` 方法**（调用 Dify 风险评估工作流）：
- 输入：灾情事件信息（区域、灾害类型、描述、特征）
- 输出：风险等级 + 研判建议
- 降级链：Dify 风险评估 → LLM（DeepSeek/千问）风险研判 → 规则引擎兜底（复用现有 `pipeline/risk_model.py` 的 `_rule_based_predict`）

**改造 `run_workflow` 降级链**（调度方案）：
- 现状：Dify 失败 → 模板拼接
- 改为：Dify 失败 → LLM 生成方案 → 模板兜底
- LLM 生成时传入 Neo4j 查到的资源三元组数据作为上下文

### 步骤 4：灾情上报模型扩展 — [schemas/graph_nodes.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/schemas/graph_nodes.py)

DisasterSpot 新增属性（保持 snake_case，不新增 Label）：
```python
class DisasterSpotBase(BaseModel):
    # 现有字段保持不变
    name: str
    disaster_type: list[str]
    risk_level: str = "中"
    urgent_level: int = 3
    lng: Optional[float] = None
    lat: Optional[float] = None
    # 新增上报字段
    reporter: Optional[str] = None        # 上报人
    report_time: Optional[datetime] = None # 上报时间
    casualties: Optional[int] = None       # 伤亡人数
    affected_people: Optional[int] = None  # 受灾人数
    description: Optional[str] = None      # 现场描述
    severity: Optional[str] = None         # 严重程度
```

### 步骤 5：Shelter 属性改名

涉及文件：
- [schemas/graph_nodes.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/schemas/graph_nodes.py)：`remain_space` → `accommodated_count`
- [graph/repository.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/graph/repository.py)：
  - `create_shelter` 的 Cypher 属性名
  - `get_nearby_shelters`：`WHERE sh.remain_space > 0` → `WHERE sh.accommodated_count < sh.max_capacity`
  - 返回字段：`sh.remain_space AS remain_space` → `sh.accommodated_count AS accommodated_count, sh.max_capacity - sh.accommodated_count AS available_space`
- [scripts/init_neo4j.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/scripts/init_neo4j.py)：初始化数据中的 `remain_space` → `accommodated_count`
- [agents/dify_client.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/agents/dify_client.py)：`_fallback_plan` 中 `s.get('remain_space')` → `s.get('available_space')`

### 步骤 6：资源管理 CRUD 补全 — [graph/repository.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/graph/repository.py)

为现有 5 类节点补全 Delete/Update/List：
- `delete_disaster_spot(spot_id)` / `update_disaster_spot(spot_id, data)` / `list_disaster_spots()`
- `delete_warehouse` / `update_warehouse` / `list_warehouses`
- `delete_material` / `update_material` / `list_materials`
- `delete_rescue_team` / `update_rescue_team` / `list_rescue_teams`
- `delete_shelter` / `update_shelter` / `list_shelters`

模式统一：Delete 用 `MATCH (n:Label {id: $id}) DETACH DELETE n`，Update 用动态 SET，List 用 `MATCH (n:Label) RETURN n`。

### 步骤 7：四角色 API 路由

#### 7.1 普通信息员 — 新建 `app/api/v1/reporter.py`
```
POST /api/v1/reporter/disasters          上报灾情（创建 DisasterSpot + 返回完整数据给 SpringBoot 存 SQL）
GET  /api/v1/reporter/disasters/{id}     查询上报的灾情
GET  /api/v1/reporter/disasters          列出灾情
```

#### 7.2 应急指挥人员 — 新建 `app/api/v1/commander.py`
```
POST /api/v1/commander/review            审核事件（调 Dify 风险评估 → LLM 降级 → 规则兜底）
POST /api/v1/commander/dispatch-plan     生成处置方案（查 Neo4j 三元组 → Dify 调度工作流 → LLM 降级 → 模板兜底）
GET  /api/v1/commander/disasters/{id}/graph  查灾害点关联三元组（避难所/仓库/队伍/道路）
```

`/dispatch-plan` 流程：
1. 调 `graph_repo.get_dispatch_plan(area_name, disaster_type)` 拿到物资+队伍+避难所三元组
2. 调 `dify_client.run_workflow(...)` 生成方案
3. Dify 失败 → `llm_client.chat(系统提示词, Neo4j数据+灾情信息)` 生成方案
4. LLM 也失败 → `_fallback_plan` 模板兜底

#### 7.3 资源管理员 — 新建 `app/api/v1/resource.py`（整合现有 graph_nodes.py 的 Create + 补全 CRUD）
```
# 受灾点位
POST   /api/v1/resource/disaster-spots
GET    /api/v1/resource/disaster-spots
PUT    /api/v1/resource/disaster-spots/{id}
DELETE /api/v1/resource/disaster-spots/{id}

# 仓库 / 物资 / 救援队伍 / 避难场所 同模式 CRUD
# 道路连接、库存、需求等关系管理保留现有接口
```

现有 [graph_nodes.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/api/v1/graph_nodes.py) 和 [dispatch.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/api/v1/dispatch.py) 保留（Dify 工作流内部 HTTP 节点调用），新增 resource.py 作为资源管理员入口。

#### 7.4 系统管理员 — 新建 `app/api/v1/admin.py`（知识库已有，补模型/数据源）
```
# 模型配置管理
GET  /api/v1/admin/llm/config       查询当前 LLM 配置（provider/api_key 脱敏/model）
PUT  /api/v1/admin/llm/config       动态修改 LLM provider/api_key/model
POST /api/v1/admin/llm/test         测试 LLM 连通性（发一个简单请求）

# 数据源状态
GET  /api/v1/admin/datasources      查询数据源状态（Neo4j 连通性 / Dify 连通性）

# 知识库管理（已有，在 knowledge_base.py，admin.py 不重复实现）
```

`PUT /llm/config` 修改后，`llm_client.set_provider(...)` 即时生效，下次 Dify 失败降级就用新配置。

### 步骤 8：路由注册 — [api/v1/__init__.py](file:///f:/桌面/Yunnan-Natural-Disaster-Emergency-Response-Platform/ai-service/app/api/v1/__init__.py)

注册 4 个新路由：reporter_router / commander_router / resource_router / admin_router。

## 文件改动清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/config.py` | 修改 | 新增 DeepSeek/千问/LLM_PROVIDER/Dify风险配置 |
| `app/agents/llm_client.py` | 新建 | 统一 LLM 客户端（DeepSeek/千问切换） |
| `app/agents/dify_client.py` | 修改 | 新增 run_risk_assessment，改造降级链为三级 |
| `app/schemas/graph_nodes.py` | 修改 | DisasterSpot 加上报字段，Shelter 改名 |
| `app/graph/repository.py` | 修改 | Shelter 改名 + 5类节点补全 CRUD |
| `app/api/v1/reporter.py` | 新建 | 普通信息员：灾情上报 |
| `app/api/v1/commander.py` | 新建 | 应急指挥：审核+处置方案 |
| `app/api/v1/resource.py` | 新建 | 资源管理：增删改查 |
| `app/api/v1/admin.py` | 新建 | 系统管理：模型/数据源配置 |
| `app/api/v1/__init__.py` | 修改 | 注册 4 个新路由 |
| `scripts/init_neo4j.py` | 修改 | Shelter 字段改名 |
| `.env.example` | 修改 | 新增配置项 |

## 验证方式

1. **语法验证**：`python -m py_compile` 所有改动文件
2. **启动验证**：`python -m app.main`，访问 `/docs` 看新接口是否出现
3. **接口测试**（需要 Neo4j 运行）：
   - `POST /api/v1/reporter/disasters` 上报灾情，确认 Neo4j 有新节点
   - `POST /api/v1/commander/review` 审核事件，确认走 Dify → LLM → 规则降级
   - `POST /api/v1/commander/dispatch-plan` 生成方案，确认三级降级
   - `DELETE /api/v1/resource/shelters/{id}` 删除避难所
   - `PUT /api/v1/admin/llm/config` 切换 provider，再触发降级确认生效
4. **降级链路验证**：故意关掉 Dify，确认 LLM 降级生效；再关掉 LLM，确认模板兜底
