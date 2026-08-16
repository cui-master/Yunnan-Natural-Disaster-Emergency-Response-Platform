package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.AiService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Enumeration;
import java.util.HashMap;
import java.util.Map;

@Tag(name = "AI服务代理", description = "转发请求到 FastAPI AI 服务")
@RestController
@RequestMapping("/ai")
public class AiController {
    public AiController(AiService aiService) {
        this.aiService = aiService;
    }


    private static final Logger log = LoggerFactory.getLogger(AiController.class);

    private final AiService aiService;

    @Operation(summary = "检查AI服务健康状态")
    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        boolean healthy = aiService.checkHealth();
        Map<String, Object> result = new HashMap<>();
        result.put("healthy", healthy);
        result.put("status", healthy ? "running" : "stopped");
        return Result.success(result);
    }

    @Operation(summary = "检查Dify工作流状态")
    @GetMapping("/dify-status")
    public Result<Map<String, Object>> difyStatus() {
        Map<String, Object> status = aiService.checkDifyWorkflowStatus();
        return Result.success(status);
    }

    @Operation(summary = "生成应急方案（AI）")
    @PostMapping("/generate-plan")
    public ResponseEntity<String> generatePlan(@RequestBody Map<String, Object> params) {
        String result = aiService.post("/api/v1/commander/dispatch-plan", params);
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "获取Neo4j图谱数据")
    @GetMapping("/graph")
    public ResponseEntity<String> getGraph(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String type) {
        String path = "/api/v1/graph/nodes";
        if (category != null || type != null) {
            path += "?";
            if (category != null) path += "category=" + category;
            if (type != null) path += "&type=" + type;
        }
        String result = aiService.get(path);
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "创建Neo4j资源节点")
    @PostMapping("/graph/nodes")
    public ResponseEntity<String> createNode(@RequestBody Map<String, Object> nodeData) {
        String result = aiService.post("/api/v1/graph/nodes", nodeData);
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "更新Neo4j资源节点")
    @PutMapping("/graph/nodes/{id}")
    public ResponseEntity<String> updateNode(@PathVariable String id, @RequestBody Map<String, Object> nodeData) {
        String result = aiService.post("/api/v1/graph/nodes/" + id, nodeData);
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "删除Neo4j资源节点")
    @DeleteMapping("/graph/nodes/{id}")
    public ResponseEntity<String> deleteNode(@PathVariable String id) {
        String result = aiService.get("/api/v1/graph/nodes/" + id + "/delete");
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "知识库文档上传（Dify）")
    @PostMapping("/knowledge/upload")
    public ResponseEntity<String> uploadToKnowledgeBase(@RequestBody Map<String, Object> params) {
        String result = aiService.post("/api/v1/knowledge-base/upload", params);
        return ResponseEntity.ok(result);
    }

    @Operation(summary = "获取知识库列表")
    @GetMapping("/knowledge/list")
    public ResponseEntity<String> getKnowledgeBaseList() {
        String result = aiService.get("/api/v1/knowledge-base/list");
        return ResponseEntity.ok(result);
    }
}
