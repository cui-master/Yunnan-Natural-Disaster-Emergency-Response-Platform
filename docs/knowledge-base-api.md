# Dify 知识库文件上传服务 API 文档

## 概述

AI 服务提供 Dify 知识库（Dataset）管理能力，支持将文件上传到指定知识库，供 RAG 检索增强生成使用。

## 知识库映射

| 知识库名称 | dataset_id | 用途 |
|-----------|-----------|------|
| 优化调度 | `a154e469-3acd-4c33-bcdc-ea65d0886488` | 物资调度、应急方案优化相关资料 |
| 风险评估 | `03d787b9-e585-4b85-abbe-332e208c6530` | 风险研判、灾害评估相关资料 |

## 配置

在 `ai-service/.env` 中配置：

```env
# Dify 知识库配置（使用数据集密钥 Dataset API Key，不是应用密钥！）
DIFY_DATASET_BASE_URL=http://localhost:5001
DIFY_DATASET_API_KEY=dataset-xxxxxxxxxxxxxxxxxxxxxxxx

# 知识库 ID 映射
KB_OPTIMIZE_DISPATCH_ID=a154e469-3acd-4c33-bcdc-ea65d0886488
KB_RISK_ASSESSMENT_ID=03d787b9-e585-4b85-abbe-332e208c6530
```

## API 接口

所有接口前缀：`/api/v1/knowledge-base`

### 1. 上传文件到知识库

**接口**：`POST /api/v1/knowledge-base/upload`

**Content-Type**：`multipart/form-data`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| kb_name | string | 是 | 知识库名称：`优化调度` / `风险评估` |
| file | file | 是 | 上传的文件（支持 txt、pdf、docx、md） |
| indexing_technique | string | 否 | 索引方式：`high_quality`(默认) / `economy` |

**响应示例**：

```json
{
  "success": true,
  "message": "文件 xxx.pdf 成功提交至【优化调度】知识库，等待解析完成",
  "kb_name": "优化调度",
  "filename": "xxx.pdf",
  "document_id": "doc-xxx",
  "result": { ... }
}
```

### 2. 查询知识库文档列表

**接口**：`GET /api/v1/knowledge-base/documents`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| kb_name | string | 是 | 知识库名称 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页数量，默认 20 |
| keyword | string | 否 | 搜索关键词 |

**响应示例**：

```json
{
  "success": true,
  "kb_name": "优化调度",
  "data": {
    "page": 1,
    "total": 10,
    "page_size": 20,
    "data": [
      {
        "id": "doc-xxx",
        "name": "应急物资调度方案.pdf",
        "indexing_status": "completed",
        "created_at": "2026-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 3. 删除知识库文档

**接口**：`DELETE /api/v1/knowledge-base/documents/{document_id}?kb_name=优化调度`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | string | 是 | 文档 ID（路径参数） |
| kb_name | string | 是 | 知识库名称（查询参数） |

**响应示例**：

```json
{
  "success": true,
  "message": "文档 doc-xxx 已从【优化调度】知识库删除"
}
```

### 4. 获取文档解析状态

**接口**：`GET /api/v1/knowledge-base/documents/{document_id}/status?kb_name=优化调度`

**说明**：文件上传后 Dify 会异步解析，可通过此接口查询进度。

### 5. 通过文本创建文档

**接口**：`POST /api/v1/knowledge-base/upload-text`

**Content-Type**：`multipart/form-data`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| kb_name | string | 是 | 知识库名称 |
| name | string | 是 | 文档名称 |
| text | string | 是 | 文档内容 |
| indexing_technique | string | 否 | 索引方式 |

### 6. 获取可用知识库列表

**接口**：`GET /api/v1/knowledge-base/list`

**响应示例**：

```json
{
  "success": true,
  "knowledge_bases": [
    {
      "name": "优化调度",
      "dataset_id": "a154e469-3acd-4c33-bcdc-ea65d0886488"
    },
    {
      "name": "风险评估",
      "dataset_id": "03d787b9-e585-4b85-abbe-332e208c6530"
    }
  ]
}
```

## 前端调用示例

```javascript
// 上传文件到知识库
const formData = new FormData();
formData.append('kb_name', '优化调度');
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/v1/knowledge-base/upload', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
console.log(result.message);
```

## 后端调用示例（Java SpringBoot）

SpringBoot Service 层调用 ai-service 接口：

```java
@Service
public class KnowledgeBaseService {

    private final RestTemplate restTemplate;

    public String uploadFile(String kbName, MultipartFile file) throws IOException {
        String url = "http://ai-service:8000/api/v1/knowledge-base/upload";

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("kb_name", kbName);
        body.add("file", new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        });

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.postForEntity(url, requestEntity, String.class);

        return response.getBody();
    }
}
```

## 重要说明

### 关于文档更新

Dify API **不能修改已有文档**。如需更新文档：
1. 先调用删除接口删除旧文档
2. 再上传新版文件

### 支持的文件格式

- 纯文本：`.txt`, `.md`
- 文档：`.docx`
- PDF：`.pdf`（注意：扫描图片 PDF 无法解析文字）

### 上传 vs 解析完成

- 上传接口返回成功 ≠ 解析完成
- Dify 后台会异步进行切片、向量化
- 可通过 `/documents/{id}/status` 查询进度

### 安全建议

- 不要将知识库接口直接暴露在公网无鉴权
- 前端增加登录权限控制
- 限制可上传的文件类型和大小
