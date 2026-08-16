package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.Neo4jService;
import com.yunnan.emergency.service.SqlNeo4jSyncService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Neo4j 图谱 Controller
 *
 * 支持前端对 Neo4j 的增删改查：
 *   GET    /neo4j/dispatch-graph         调度大屏图谱（灾情/资源/调度指令/地点 节点 + 关系）
 *   GET    /neo4j/nodes/{label}/{id}     查询单个节点
 *   POST   /neo4j/nodes/{label}          创建节点（与 SQL 业务表对应）
 *   PUT    /neo4j/nodes/{label}/{id}     更新节点属性
 *   DELETE /neo4j/nodes/{label}/{id}     删除节点（连带删除关系）
 *
 *   POST   /neo4j/relationships          创建关系
 *   DELETE /neo4j/relationships/{relId}  删除关系
 *
 *   GET    /neo4j/consistency            SQL ↔ Neo4j 数据一致性校验
 */
@Tag(name = "Neo4j 图谱", description = "资源调度图谱查询与增删改查")
@RestController
@RequestMapping("/neo4j")
public class Neo4jController {
    public Neo4jController(Neo4jService neo4jService, SqlNeo4jSyncService sqlNeo4jSyncService) {
        this.neo4jService = neo4jService;
        this.sqlNeo4jSyncService = sqlNeo4jSyncService;
    }


    private final Neo4jService neo4jService;
    private final SqlNeo4jSyncService sqlNeo4jSyncService;

    @Operation(summary = "调度大屏图谱（Neo4j）")
    @GetMapping("/dispatch-graph")
    public Result<Map<String, Object>> dispatchGraph(
            @RequestParam(required = false) Long incidentId) {
        return Result.success(neo4jService.getDispatchGraph(incidentId));
    }

    // ============ 交互式图谱浏览（Neo4j Browser 风格） ============

    @Operation(summary = "获取所有节点标签及计数")
    @GetMapping("/labels")
    public Result<List<Map<String, Object>>> listLabels() {
        return Result.success(neo4jService.listLabels());
    }

    @Operation(summary = "获取所有关系类型及计数")
    @GetMapping("/relationship-types")
    public Result<List<Map<String, Object>>> listRelationshipTypes() {
        return Result.success(neo4jService.listRelationshipTypes());
    }

    @Operation(summary = "按标签查询节点（分页）")
    @GetMapping("/nodes-by-label")
    public Result<Map<String, Object>> nodesByLabel(
            @RequestParam String label,
            @RequestParam(defaultValue = "25") int limit) {
        return Result.success(neo4jService.listNodesByLabelMap(label, limit));
    }

    @Operation(summary = "展开节点邻居（双击节点展开）")
    @GetMapping("/expand/{nodeId}")
    public Result<Map<String, Object>> expandNeighbors(@PathVariable long nodeId) {
        return Result.success(neo4jService.expandNeighbors(nodeId));
    }

    @Operation(summary = "收起节点（返回邻居ID和关系ID列表，前端决定是否移除）")
    @GetMapping("/collapse/{nodeId}")
    public Result<Map<String, Object>> collapseNode(@PathVariable long nodeId) {
        return Result.success(neo4jService.getNodeNeighborInfo(nodeId));
    }

    @Operation(summary = "按内部ID查询节点")
    @GetMapping("/node/{nodeId}")
    public Result<Map<String, Object>> getNodeByInternalId(@PathVariable long nodeId) {
        Map<String, Object> node = neo4jService.getNodeByInternalId(nodeId);
        if (node == null) {
            return Result.error("节点不存在: id=" + nodeId);
        }
        return Result.success(node);
    }

    @Operation(summary = "查询单个节点")
    @GetMapping("/nodes/{label}/{id}")
    public Result<Map<String, Object>> getNode(
            @PathVariable String label,
            @PathVariable Object id) {
        Map<String, Object> node = neo4jService.getNode(label, id);
        if (node == null) {
            return Result.error("节点不存在: " + label + " id=" + id);
        }
        return Result.success(node);
    }

    @Operation(summary = "创建节点（与 SQL 业务表对应，按业务主键 MERGE）")
    @PostMapping("/nodes/{label}")
    public Result<Map<String, Object>> createNode(
            @PathVariable String label,
            @RequestBody Map<String, Object> properties) {
        try {
            return Result.success(neo4jService.createNode(label, properties));
        } catch (Exception e) {
            return Result.error(e.getMessage());
        }
    }

    @Operation(summary = "更新节点属性")
    @PutMapping("/nodes/{label}/{id}")
    public Result<Map<String, Object>> updateNode(
            @PathVariable String label,
            @PathVariable Object id,
            @RequestBody Map<String, Object> properties) {
        try {
            return Result.success(neo4jService.updateNode(label, id, properties));
        } catch (Exception e) {
            return Result.error(e.getMessage());
        }
    }

    @Operation(summary = "删除节点（连带删除关系）")
    @DeleteMapping("/nodes/{label}/{id}")
    public Result<Map<String, Object>> deleteNode(
            @PathVariable String label,
            @PathVariable Object id) {
        try {
            return Result.success(neo4jService.deleteNode(label, id));
        } catch (Exception e) {
            return Result.error(e.getMessage());
        }
    }

    @Operation(summary = "创建关系")
    @PostMapping("/relationships")
    public Result<Map<String, Object>> createRelationship(@RequestBody Map<String, Object> body) {
        try {
            String fromLabel = (String) body.get("fromLabel");
            Object fromId = body.get("fromId");
            String toLabel = (String) body.get("toLabel");
            Object toId = body.get("toId");
            String relType = (String) body.get("relType");
            @SuppressWarnings("unchecked")
            Map<String, Object> props = (Map<String, Object>) body.get("properties");
            return Result.success(neo4jService.createRelationship(fromLabel, fromId, toLabel, toId, relType, props));
        } catch (Exception e) {
            return Result.error(e.getMessage());
        }
    }

    @Operation(summary = "删除关系")
    @DeleteMapping("/relationships/{relId}")
    public Result<Map<String, Object>> deleteRelationship(@PathVariable Long relId) {
        return Result.success(neo4jService.deleteRelationship(relId));
    }

    @Operation(summary = "按标签统计节点数")
    @GetMapping("/count/{label}")
    public Result<Long> countByLabel(@PathVariable String label) {
        return Result.success(neo4jService.countByLabel(label));
    }

    @Operation(summary = "列出某标签所有节点的业务 ID")
    @GetMapping("/ids/{label}")
    public Result<List<Object>> listBusinessIds(@PathVariable String label) {
        String businessKey = Neo4jService.businessKeyOf(label);
        return Result.success(neo4jService.listBusinessIds(label, businessKey));
    }

    @Operation(summary = "清空 Neo4j 所有数据")
    @DeleteMapping("/clear")
    public Result<Map<String, Object>> clearAll() {
        return Result.success(neo4jService.clearAll());
    }

    @Operation(summary = "全量重新同步：清空并从 MySQL 重建图谱")
    @PostMapping("/resync")
    public Result<Map<String, Object>> fullReSync() {
        return Result.success(sqlNeo4jSyncService.fullReSync());
    }

    @Operation(summary = "导出全量图谱JSON（nodes + relationships），供调度方案工作流/大批量对接使用")
    @GetMapping("/export")
    public Result<Map<String, Object>> exportGraphData() {
        return Result.success(sqlNeo4jSyncService.exportGraphData());
    }
}
