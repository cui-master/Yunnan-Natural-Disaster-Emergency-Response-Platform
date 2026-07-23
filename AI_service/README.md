# 云南省自然灾害应急决策平台 AI 服务

基于 FastAPI + Neo4j 图数据库 + Dify Agent 的智能应急物资调度与方案生成系统。

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 / 应急指挥大屏                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP / SSE / WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                        FastAPI 服务层                             │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────────┐ │
│  │ 节点管理 │ 物资调度 │ Dify工作流│ 管线监控 │  数据管线Pipeline │ │
│  └──────────┴──────────┴──────────┴──────────┴───────────────┘ │
└───┬───────────────────────┬───────────────────┬─────────────────┘
    │                       │                   │
┌───▼────────┐    ┌─────────▼──────────┐    ┌───▼───────────────┐
│ Neo4j 图库 │    │ Dify + RAG + LLM    │    │  LightGBM 风险模型  │
│ 物资/队伍  │    │ 通义千问/DeepSeek   │    │  时序预测+多源融合   │
│ 路网/避难所│    │                    │    │                    │
└────────────┘    └─────────▲──────────┘    └─────────▲─────────┘
                            │                         │
                     ┌──────┴─────────────────────────┘
                     │    数据采集层
                     │  气象 │ 地质 │ 水文 │ 舆情
                     └─────────────────────────────────
```

## 目录结构

```
AI_service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 主入口
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 环境变量配置
│   │   ├── logging.py          # 日志配置
│   │   └── neo4j_client.py     # Neo4j 连接管理
│   ├── api/v1/                 # API 路由
│   │   ├── graph_nodes.py      # 图节点 CRUD 接口
│   │   ├── dispatch.py         # 物资调度核心接口
│   │   ├── workflow.py         # Dify 工作流接口
│   │   └── pipeline.py         # 数据管线接口
│   ├── graph/                  # 图数据库操作层
│   │   └── repository.py       # Cypher 查询封装
│   ├── agents/                 # Agent 封装
│   │   └── dify_client.py      # Dify 客户端
│   ├── pipeline/               # ⭐ 数据管线（核心新增）
│   │   ├── models.py           # 四类数据 Pydantic 模型
│   │   ├── collectors.py       # 采集器（气象/地质/水文/舆情）
│   │   ├── validator.py        # 数据校验 + 多源融合引擎
│   │   ├── risk_model.py       # LightGBM 风险研判（规则 fallback）
│   │   └── pipeline.py         # 管线编排器（Orchestrator）
│   ├── ml/                     # 模型服务（兼容入口）
│   │   └── risk_model.py       # 从 pipeline 导入
│   ├── tasks/                  # 定时任务
│   │   └── scheduler.py        # APScheduler（定时触发管线）
│   └── schemas/                # Pydantic 模型
│       ├── graph_nodes.py
│       └── dispatch.py
├── scripts/
│   └── init_neo4j.py           # Neo4j 初始化脚本（含云南示例数据）
├── dify/
│   ├── system_prompt.md        # Dify LLM 系统提示词
│   └── workflow_config.md      # Dify 工作流配置说明
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Neo4j 5.x（已安装并启动，默认 bolt://localhost:7687）
- Dify（可选，用于完整工作流；不启动时服务自动降级）

### 2. 安装依赖

```powershell
D:\env\Anaconda\envs\qw\python.exe -m pip install -r requirements.txt
```

### 3. 配置环境变量

```powershell
copy .env.example .env
```

编辑 `.env`，配置 Neo4j 和 Dify 连接信息。

### 4. 初始化 Neo4j 数据

```powershell
D:\env\Anaconda\envs\qw\python.exe scripts/init_neo4j.py
```

这会创建：
- 10 个云南典型高风险区县点位
- 8 个省级/州市级应急物资仓库
- 15 种应急物资品类 + 42 条库存关系
- 6 支救援队伍
- 8 个避难场所
- 道路连通关系（基于经纬度计算）
- 物资需求关系

### 5. 启动服务

```powershell
D:\env\Anaconda\envs\qw\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或直接运行：

```powershell
D:\env\Anaconda\envs\qw\python.exe app/main.py
```

访问：http://localhost:8000/docs 查看 Swagger 文档

## 核心 API 接口

### 物资调度（Dify 调用主接口）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/dispatch/plan` | GET | 综合调度方案（物资+队伍+避难所） |
| `/api/v1/dispatch/optimal-warehouses` | GET | 高风险区域最优物资仓库 |
| `/api/v1/dispatch/available-teams` | GET | 可调度救援队伍 |
| `/api/v1/dispatch/nearby-shelters` | GET | 附近避难场所 |

### Dify 工作流

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/workflow/run` | POST | 调用 Dify 生成应急方案 |
| `/api/v1/workflow/run/stream` | POST | 流式输出方案（SSE） |

### 数据管线 Pipeline

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/pipeline/status` | GET | 管线运行状态 + 历史记录 |
| `/api/v1/pipeline/run` | POST | 手动触发完整管线（同步/异步） |
| `/api/v1/pipeline/run/area` | POST | 对指定区域执行管线 |
| `/api/v1/pipeline/collect/weather` | GET | 采集气象数据（测试用） |
| `/api/v1/pipeline/collect/geology` | GET | 采集地质数据（测试用） |
| `/api/v1/pipeline/assess/area` | GET | 单区域风险研判（测试用） |

### 图节点管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/graph/disaster-spots` | GET/POST | 受灾点位管理 |
| `/api/v1/graph/disaster-spots/risk-level` | PUT | 更新风险等级 |
| `/api/v1/graph/warehouses` | POST | 创建仓库 |
| `/api/v1/graph/warehouses/{id}/stock` | POST | 设置库存 |
| `/api/v1/graph/rescue-teams` | POST | 创建救援队伍 |
| `/api/v1/graph/shelters` | POST | 创建避难场所 |
| `/api/v1/graph/road-connect` | POST | 建立道路连通 |

## 调用示例

### 1. 获取综合调度方案

```bash
curl "http://localhost:8000/api/v1/dispatch/plan?area_name=昆明市东川区&disaster_type=泥石流"
```

### 2. 调用 Dify 生成完整方案

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/run" \
  -H "Content-Type: application/json" \
  -d '{
    "area_name": "昆明市东川区",
    "disaster_type": "泥石流",
    "risk_level": "极高",
    "input_risk_info": "受持续强降雨影响，东川区累计降雨量达180mm，地质灾害气象风险预警为红色，极易诱发泥石流、滑坡等地质灾害。",
    "vision_text": ""
  }'
```

## 图数据库设计

### 节点类型（7 种）

- **DisasterSpot**：受灾点位/高风险区域
- **Warehouse**：应急物资仓库
- **Material**：物资品类
- **WarehouseStock**：仓库库存（中间节点）
- **RescueTeam**：救援队伍
- **Road**：道路
- **Shelter**：避难场所

### 核心关系

```
(Warehouse)-[:HAS_STOCK]->(WarehouseStock)-[:STOCK_MATERIAL]->(Material)
(RescueTeam)-[:CARRY]->(Material)
(DisasterSpot)-[:NEED]->(Material)
(Warehouse)-[:ROAD_CONNECT {distance, blocked}]-(:Warehouse|:DisasterSpot)
(RescueTeam)-[:ROAD_CONNECT {distance, blocked}]-(DisasterSpot)
(RescueTeam)-[:ALLOCATED]->(DisasterSpot)
(DisasterSpot)-[:NEED_EVACUATE]->(Shelter)
```

### 关键 Cypher 查询

最短路径物资调度：

```cypher
MATCH (area:DisasterSpot {risk_level:"极高"})-[:NEED]->(m:Material)
MATCH (wh:Warehouse)-[:HAS_STOCK]->(ws:WarehouseStock)-[:STOCK_MATERIAL]->(m)
WHERE ws.stock_num > 0
MATCH p = shortestPath((wh)-[:ROAD_CONNECT*1..8 {blocked:false}]-(area))
WITH wh, ws, m, reduce(total=0, r IN relationships(p) | total + r.distance) AS total_dist
WITH wh, ws, m, total_dist, (1.0/total_dist)*0.5 + area.urgent_level*0.3 AS score
ORDER BY score DESC
RETURN wh.name, m.name, ws.stock_num, total_dist, score
```

## 数据流转

### 完整数据管线（6 步闭环）

```
┌─────────────┐    ┌────────────┐    ┌─────────────┐    ┌──────────────┐
│ ① 多源采集   │ →  │ ② 数据校验  │ →  │ ③ 多源融合  │ →  │ ④ 风险研判    │
│ 气象/地质/   │    │ 格式/范围/  │    │ 可信度加权  │    │ LightGBM模型  │
│ 水文/舆情    │    │ 异常值检测  │    │ 特征工程    │    │ 规则fallback  │
└─────────────┘    └────────────┘    └─────────────┘    └──────┬───────┘
                                                                ↓
┌─────────────┐    ┌────────────┐    ┌─────────────┐    ┌──────▼───────┐
│ ⑧ 复盘优化   │ ←  │ ⑦ 方案输出  │ ←  │ ⑥ Dify生成  │ ←  │ ⑤ Neo4j更新   │
│ 模型迭代/    │    │ 大屏展示/   │    │ 预案RAG/    │    │ 风险等级同步  │
│ 知识沉淀     │    │ 推送通知    │    │ LLM生成方案 │    │ 物资需求更新  │
└─────────────┘    └────────────┘    └─────────────┘    └──────────────┘
```

### 定时任务触发

```
APScheduler (每30分钟)
    ↓
CollectorManager 并发采集 4 类数据
    ↓
DataValidator 校验过滤
    ↓
MultiSourceFusionEngine 多源加权融合
    ↓
RiskAssessmentModel 风险研判（LightGBM / 规则引擎）
    ↓
同步 Neo4j DisasterSpot.risk_level / urgent_level
    ↓
(可选) 高风险区域自动触发 Dify 生成预防方案
```

## Dify 配置

详细配置见 [dify/workflow_config.md](./dify/workflow_config.md)

系统提示词见 [dify/system_prompt.md](./dify/system_prompt.md)

## 定时任务

- **完整数据管线**：每 30 分钟自动执行（采集→校验→融合→研判→Neo4j更新）
- 通过 `RISK_LEVEL_SYNC_INTERVAL_MINUTES` 环境变量调整
- 可通过 `/api/v1/pipeline/run` 手动触发

## 数据管线模块详解

### 四大采集器

| 采集器 | 类型 | 模拟数据特征 | 可信度 |
|--------|------|-------------|--------|
| WeatherCollector | 气象 | 24h/3d/7d 降雨量、预警等级、温湿度 | 0.85~0.90 |
| GeologyCollector | 地质 | 地震事件、地质灾害气象风险、边坡稳定性 | 0.85~0.95 |
| HydrologyCollector | 水文 | 水位、流量、水库、洪水预警 | 0.75~0.85 |
| PublicOpinionCollector | 舆情 | 热度、情感分、热点话题、传播速度 | 0.45~0.65 |

### 多源核验融合

- **格式校验**：数值范围、必填字段、枚举合法性
- **可信度加权**：每类数据有基础可信度，融合时按权重计算
- **预警取最高**：气象/水文等预警等级取最严重值
- **数据源统计**：每个研判结果标注使用了哪些数据源

### 风险研判模型

- **主模型**：LightGBM 时序模型（自动检测，有则加载）
- **Fallback**：规则引擎（降雨+地质+水文+舆情加权打分）
- **输出**：风险等级（4级）+ 风险评分（0~100）+ 紧急等级（1~5）+ 贡献因子明细

## 降级策略

Dify 不可用时，自动切换为降级模式：
- 直接基于 Neo4j 调度结果生成结构化方案
- 保证核心调度功能可用，不依赖外部 LLM 服务

## 下一步扩展

1. **接入真实数据源 API**：替换模拟采集器，接入云南省气象局、地震局、水文局、舆情监测 API
2. **训练真实 LightGBM 模型**：用云南历史灾害数据训练，替换规则 fallback
3. **接入实时道路状况**：接入交通部门路网数据，动态更新 `blocked` 属性
4. **微调领域模型**：基于云南灾害历史数据，微调 Qwen/DeepSeek 基座
5. **RAG 知识库**：导入云南省各级应急预案到 Dify
6. **大屏可视化**：对接前端，展示灾害热力图、调度路径、实时管线状态
7. **多模态接入**：接入卫星/无人机影像，视觉模型自动解译灾情
8. **模型训练平台**：支持在线标注、模型训练、版本管理
