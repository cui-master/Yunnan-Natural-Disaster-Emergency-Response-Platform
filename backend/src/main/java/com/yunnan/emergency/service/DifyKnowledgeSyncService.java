package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * 知识库 ↔ Dify Dataset 同步服务
 *
 * 当 KnowledgeBaseController 在 MySQL knowledge_bases 表做 CUD 时，
 * 调用本服务把变更同步到 Dify 知识库（dataset API），保证 SQL 与 Dify 数据对应。
 *
 * 调用链：Spring Boot → FastAPI /api/v1/admin/datasets → Dify
 */
@Service
public class DifyKnowledgeSyncService {
    public DifyKnowledgeSyncService(DataPipelineService dataPipelineService) {
        this.dataPipelineService = dataPipelineService;
    }


    private static final Logger log = LoggerFactory.getLogger(DifyKnowledgeSyncService.class);

    private final DataPipelineService dataPipelineService;

    /** 同步创建知识库到 Dify */
    public Map<String, Object> syncCreate(String name, String description) {
        Map<String, Object> params = new HashMap<>();
        params.put("name", name);
        params.put("description", description == null ? "" : description);
        params.put("index_mode", "high_quality");
        params.put("permission", "only_me");
        try {
            String resp = dataPipelineService.post("/api/v1/admin/datasets", params);
            log.info("[dify-sync] 创建知识库成功: name={}", name);
            return JSONUtil.parseObj(resp);
        } catch (Exception e) {
            log.warn("[dify-sync] 创建知识库到 Dify 失败（不影响 SQL 主流程）: name={}, err={}", name, e.getMessage());
            return Map.of("synced", false, "error", e.getMessage());
        }
    }

    /** 同步删除知识库到 Dify */
    public boolean syncDelete(String difyDatasetId) {
        if (difyDatasetId == null || difyDatasetId.isBlank()) {
            log.debug("[dify-sync] 跳过删除：difyDatasetId 为空");
            return false;
        }
        try {
            dataPipelineService.delete("/api/v1/admin/datasets/" + difyDatasetId);
            log.info("[dify-sync] 删除 Dify 知识库成功: datasetId={}", difyDatasetId);
            return true;
        } catch (Exception e) {
            log.warn("[dify-sync] 删除 Dify 知识库失败: datasetId={}, err={}", difyDatasetId, e.getMessage());
            return false;
        }
    }

    /** 检查 Dify 知识库 dataset API 连通性 */
    public Map<String, Object> checkStatus() {
        try {
            String resp = dataPipelineService.get("/api/v1/admin/dify-status");
            return JSONUtil.parseObj(resp);
        } catch (Exception e) {
            log.warn("[dify-sync] 检查 Dify 状态失败: {}", e.getMessage());
            Map<String, Object> err = new HashMap<>();
            err.put("status", "disconnected");
            err.put("error", e.getMessage());
            return err;
        }
    }
}
