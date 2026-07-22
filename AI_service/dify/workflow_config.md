# Dify 工作流配置说明

## 工作流名称
自然灾害智能预防 & 应急方案生成工作流

## 输入变量（开始节点配置）

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `input_risk_info` | 文本 | 风险文本情报（爬虫情报+时序模型风险结果） |
| `disaster_type` | 文本 | 灾害类型：暴雨/洪涝/山洪/滑坡/泥石流/崩塌/地震 |
| `area_name` | 文本 | 目标区域名称 |
| `risk_level` | 文本 | 风险等级：低/中/高/极高 |
| `vision_text` | 文本（可选） | 视觉大模型识别图片得到的灾情描述 |

## 节点拖拽顺序

```
开始 → 条件分支1 → 普通风险 → LLM(巡查建议) → 结束
                    ↓
                 高/极高风险
                    ↓
            HTTP请求（调Neo4j调度API）
                    ↓
            RAG知识库检索（按灾种分组）
                    ↓
            LLM节点（核心Prompt + 全量上下文）
                    ↓
                条件分支2
              ↙         ↘
    灾前预防方案     灾后救援方案
              ↘         ↙
                    结束（结构化输出）
```

## 关键节点配置

### 节点1：条件分支 1 —— 风险等级判断
- **判断条件**：`{{risk_level}}` 等于 "高" 或 "极高"
- **是分支**：执行完整物资调度链路
- **否分支**：生成常态化巡查建议（直接接一个简化版 LLM 节点）

### 节点2：HTTP 请求 —— 调用 Neo4j 调度 API
- **请求方式**：GET
- **URL**：`http://<你的FastAPI服务地址>/api/v1/dispatch/plan`
- **查询参数**：
  - `area_name` = `{{area_name}}`
  - `disaster_type` = `{{disaster_type}}`
- **输出变量名**：`neo4j_resource_data`

> 备用接口（可并联调用）：
> - `/api/v1/dispatch/optimal-warehouses?risk_level={{risk_level}}`
> - `/api/v1/dispatch/available-teams?area_name={{area_name}}&disaster_type={{disaster_type}}`
> - `/api/v1/dispatch/nearby-shelters?area_name={{area_name}}`

### 节点3：RAG 知识库检索
- **知识库分组配置**：
  - 防汛预案（暴雨/洪涝/山洪）
  - 地质灾害防范预案（滑坡/泥石流/崩塌）
  - 地震应急处置预案
- **检索条件**：根据 `{{disaster_type}}` 定向召回对应防灾/应急文档
- **输出变量名**：`rag_context`

### 节点4：LLM 节点（核心）
- **模型**：通义千问 qwen-max 或 deepseek-v4-flash
- **System Prompt**：见 [system_prompt.md](./system_prompt.md)
- **输入变量**：全部 5 个入参 + `neo4j_resource_data` + `rag_context`

### 节点5：条件分支 2 —— 灾前/灾后判断
- **判断逻辑**：检查 `vision_text` 是否为空，或 `risk_level` 的上下文
  - 只有风险预警、无灾情描述 → **灾前预防方案**
  - 有现场灾情描述/灾害已爆发 → **灾后救援方案**
- **两条分支分别输出不同格式的文档**

### 结束节点
- **输出变量**：`final_plan`（Markdown 格式方案文本）
- **流式输出**：开启，支持推送到前端大屏

## 对外接口
- **接口地址**：`/v1/workflows/run`
- **调用方式**：FastAPI 后端通过 `Authorization: Bearer <API_KEY>` 发起调用
- **响应模式**：blocking（阻塞）或 streaming（流式）

## Dify 应用配置参考（YAML 格式片段）

```yaml
app:
  name: 自然灾害智能预防 & 应急方案生成工作流
  mode: workflow
  icon: 🌊
  icon_background: '#0EA5E9'
```

## 知识库文档建议（导入 Dify）

建议上传以下类型文档到 Dify 知识库：

1. **云南省防汛抗旱应急预案**
2. **云南省地质灾害应急预案**
3. **云南省地震应急预案**
4. **云南省森林火灾应急预案**
5. **各州市县级专项应急预案**
6. **应急物资储备管理办法**
7. **救援队伍调动管理规定**
8. **历史灾害处置案例汇编**

**分段策略**：按段落语义分割，chunk size 500~800 字
**检索模式**：混合检索（语义+关键词）
