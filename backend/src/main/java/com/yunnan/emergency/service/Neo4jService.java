package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Result;
import org.neo4j.driver.Session;
import org.neo4j.driver.Value;
import org.neo4j.driver.types.Node;
import org.neo4j.driver.types.Relationship;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Neo4j 图谱服务 —— 统一使用中文标签和中文关系名（严格遵循用户定义的实体结构）。
 */
@Service
public class Neo4jService {
    public Neo4jService(Driver driver) {
        this.driver = driver;
    }

    private static final Logger log = LoggerFactory.getLogger(Neo4jService.class);
    private final Driver driver;

    /** 允许的节点标签白名单（防止 Cypher 注入） */
    private static final Set<String> ALLOWED_LABELS = Set.of(
        "受灾点", "物资仓库", "物资", "物资单品", "救援队伍", "避难场所", "道路",
        "地点名称", "灾害类型", "危险等级", "受灾人数", "场所名称", "地点",
        "数量", "数值", "重量", "队伍类型", "擅长灾害", "适用灾害", "状态",
        "通行状态", "道路编号", "道路名称", "道路等级", "承载上限", "通行代价",
        "最大容纳人数", "已容纳人数", "最大运载重量", "调度指令"
    );

    /** 允许的关系类型白名单 */
    private static final Set<String> ALLOWED_REL_TYPES = Set.of(
        "位于", "是", "具备", "涉及", "拥有", "包含", "适用于", "有",
        "最大运载重量", "擅长", "状态", "编号为", "命名为", "属于",
        "当前通行", "承载上限", "通行代价", "临近", "连通", "服务",
        "调度给", "分配"
    );

    /** 一级实体标签集合 */
    public static final Set<String> LEVEL1_ENTITIES = Set.of(
        "受灾点", "物资仓库", "救援队伍", "避难场所", "道路"
    );

    /** 标签 → 中文显示名（全部已是中文，保持一致） */
    private static final Map<String, String> LABEL_DISPLAY = new LinkedHashMap<>();
    static {
        // 一级实体
        LABEL_DISPLAY.put("受灾点", "受灾点");
        LABEL_DISPLAY.put("物资仓库", "物资仓库");
        LABEL_DISPLAY.put("物资", "物资");
        LABEL_DISPLAY.put("物资单品", "物资单品");
        LABEL_DISPLAY.put("救援队伍", "救援队伍");
        LABEL_DISPLAY.put("避难场所", "避难场所");
        LABEL_DISPLAY.put("道路", "道路");
        LABEL_DISPLAY.put("调度指令", "调度指令");
        // 二级/三级/四级属性实体
        LABEL_DISPLAY.put("地点名称", "地点名称");
        LABEL_DISPLAY.put("地点", "地点");
        LABEL_DISPLAY.put("场所名称", "场所名称");
        LABEL_DISPLAY.put("灾害类型", "灾害类型");
        LABEL_DISPLAY.put("危险等级", "危险等级");
        LABEL_DISPLAY.put("受灾人数", "受灾人数");
        LABEL_DISPLAY.put("数量", "数量");
        LABEL_DISPLAY.put("数值", "数值");
        LABEL_DISPLAY.put("重量", "重量");
        LABEL_DISPLAY.put("队伍类型", "队伍类型");
        LABEL_DISPLAY.put("擅长灾害", "擅长灾害");
        LABEL_DISPLAY.put("适用灾害", "适用灾害");
        LABEL_DISPLAY.put("状态", "状态");
        LABEL_DISPLAY.put("通行状态", "通行状态");
        LABEL_DISPLAY.put("道路编号", "道路编号");
        LABEL_DISPLAY.put("道路名称", "道路名称");
        LABEL_DISPLAY.put("道路等级", "道路等级");
        LABEL_DISPLAY.put("承载上限", "承载上限");
        LABEL_DISPLAY.put("通行代价", "通行代价");
        LABEL_DISPLAY.put("最大容纳人数", "最大容纳人数");
        LABEL_DISPLAY.put("已容纳人数", "已容纳人数");
        LABEL_DISPLAY.put("最大运载重量", "最大运载重量");
    }

    /** 关系类型 → 中文显示名 */
    private static final Map<String, String> REL_TYPE_DISPLAY = new LinkedHashMap<>();
    static {
        REL_TYPE_DISPLAY.put("位于", "位于");
        REL_TYPE_DISPLAY.put("是", "是");
        REL_TYPE_DISPLAY.put("具备", "具备");
        REL_TYPE_DISPLAY.put("涉及", "涉及");
        REL_TYPE_DISPLAY.put("拥有", "拥有");
        REL_TYPE_DISPLAY.put("包含", "包含");
        REL_TYPE_DISPLAY.put("适用于", "适用于");
        REL_TYPE_DISPLAY.put("有", "有");
        REL_TYPE_DISPLAY.put("最大运载重量", "最大运载重量");
        REL_TYPE_DISPLAY.put("擅长", "擅长");
        REL_TYPE_DISPLAY.put("状态", "状态");
        REL_TYPE_DISPLAY.put("编号为", "编号为");
        REL_TYPE_DISPLAY.put("命名为", "命名为");
        REL_TYPE_DISPLAY.put("属于", "属于");
        REL_TYPE_DISPLAY.put("当前通行", "当前通行");
        REL_TYPE_DISPLAY.put("承载上限", "承载上限");
        REL_TYPE_DISPLAY.put("通行代价", "通行代价");
        REL_TYPE_DISPLAY.put("临近", "临近");
        REL_TYPE_DISPLAY.put("连通", "连通");
        REL_TYPE_DISPLAY.put("服务", "服务");
        REL_TYPE_DISPLAY.put("调度给", "调度给");
        REL_TYPE_DISPLAY.put("分配", "分配");
    }

    // ============ 节点 CRUD ============

    public Map<String, Object> createNode(String label, Map<String, Object> properties) {
        if (!ALLOWED_LABELS.contains(label)) {
            throw new IllegalArgumentException("不允许的标签: " + label);
        }
        // 清理 null 值（Neo4j driver 不接受 null）
        Map<String, Object> cleanProps = new LinkedHashMap<>();
        properties.forEach((k, v) -> { if (v != null) cleanProps.put(k, v); });

        try (Session session = driver.session()) {
            StringBuilder sb = new StringBuilder();
            sb.append("MERGE (n:").append(label).append(" {");
            // 确定业务主键
            String businessKey = businessKeyOf(label);
            if (cleanProps.containsKey(businessKey)) {
                sb.append(businessKey).append(": $").append(businessKey);
            } else {
                // 没有业务主键，用 name
                sb.append("name: $name");
            }
            sb.append("}) SET n += $props RETURN n, id(n) AS internalId, labels(n) AS labels");

            Map<String, Object> params = new HashMap<>(cleanProps);
            params.put("props", cleanProps);
            if (!cleanProps.containsKey(businessKey) && !cleanProps.containsKey("name")) {
                // fallback: use uuid
                params.put("name", "未命名_" + System.currentTimeMillis());
            }

            Result result = session.run(sb.toString(), params);
            if (result.hasNext()) {
                Record record = result.next();
                Node node = record.get("n").asNode();
                return buildNodeMap(node, record.get("labels").asList(Value::asString));
            }
            throw new RuntimeException("创建节点失败: " + label);
        } catch (Exception e) {
            log.error("[neo4j] 创建节点失败: label={}, props={}, err={}", label, properties, e.getMessage(), e);
            throw new RuntimeException("创建节点失败: " + e.getMessage(), e);
        }
    }

    public Map<String, Object> updateNode(String label, Object businessId, Map<String, Object> properties) {
        if (!ALLOWED_LABELS.contains(label)) {
            throw new IllegalArgumentException("不允许的标签: " + label);
        }
        String businessKey = businessKeyOf(label);
        Map<String, Object> cleanProps = new LinkedHashMap<>();
        properties.forEach((k, v) -> { if (v != null) cleanProps.put(k, v); });

        try (Session session = driver.session()) {
            String cypher = "MATCH (n:" + label + " {" + businessKey + ": $bizId}) SET n += $props RETURN n, id(n) AS internalId, labels(n) AS labels";
            Map<String, Object> params = Map.of("bizId", businessId, "props", cleanProps);
            Result result = session.run(cypher, params);
            if (result.hasNext()) {
                Record record = result.next();
                return buildNodeMap(record.get("n").asNode(), record.get("labels").asList(Value::asString));
            }
            throw new RuntimeException("节点不存在: " + label + "#" + businessId);
        } catch (Exception e) {
            log.error("[neo4j] 更新节点失败: label={}, bizId={}, err={}", label, businessId, e.getMessage());
            throw new RuntimeException("更新节点失败: " + e.getMessage(), e);
        }
    }

    public Map<String, Object> getNode(Long internalId) {
        try (Session session = driver.session()) {
            Result result = session.run("MATCH (n) WHERE id(n) = $id RETURN n, labels(n) AS labels",
                Map.of("id", internalId));
            if (result.hasNext()) {
                Record record = result.next();
                return buildNodeMap(record.get("n").asNode(), record.get("labels").asList(Value::asString));
            }
            return null;
        }
    }

    // ============ 关系 CRUD ============

    public Map<String, Object> createRelationship(String fromLabel, Object fromId,
                                                   String toLabel, Object toId,
                                                   String relType, Map<String, Object> properties) {
        if (!ALLOWED_LABELS.contains(fromLabel)) throw new IllegalArgumentException("不允许的标签: " + fromLabel);
        if (!ALLOWED_LABELS.contains(toLabel)) throw new IllegalArgumentException("不允许的标签: " + toLabel);
        if (!ALLOWED_REL_TYPES.contains(relType)) throw new IllegalArgumentException("不允许的关系类型: " + relType);

        String fromKey = businessKeyOf(fromLabel);
        String toKey = businessKeyOf(toLabel);
        Map<String, Object> cleanProps = new LinkedHashMap<>();
        if (properties != null) {
            properties.forEach((k, v) -> { if (v != null) cleanProps.put(k, v); });
        }

        try (Session session = driver.session()) {
            String cypher = "MATCH (a:" + fromLabel + " {" + fromKey + ": $fromId}), " +
                            "(b:" + toLabel + " {" + toKey + ": $toId}) " +
                            "MERGE (a)-[r:`" + relType + "`]->(b) " +
                            "SET r += $props RETURN r, id(r) AS relId, id(a) AS fromInternalId, id(b) AS toInternalId";
            Map<String, Object> params = Map.of("fromId", fromId, "toId", toId, "props", cleanProps);
            Result result = session.run(cypher, params);
            if (result.hasNext()) {
                Record record = result.next();
                Relationship rel = record.get("r").asRelationship();
                Map<String, Object> edge = new LinkedHashMap<>();
                edge.put("id", record.get("relId").asLong());
                edge.put("from", record.get("fromInternalId").asLong());
                edge.put("to", record.get("toInternalId").asLong());
                edge.put("label", REL_TYPE_DISPLAY.getOrDefault(relType, relType));
                edge.put("rawType", relType);
                edge.put("properties", rel.asMap());
                return edge;
            }
            throw new RuntimeException("创建关系失败");
        }
    }

    // ============ 图谱浏览 API ============

    public List<Map<String, Object>> listLabels() {
        Map<String, Map<String, Object>> merged = new LinkedHashMap<>();
        try (Session session = driver.session()) {
            Result result = session.run(
                "MATCH (n) WITH labels(n) AS lbs UNWIND lbs AS lb " +
                "RETURN lb AS label, count(*) AS count ORDER BY count DESC"
            );
            while (result.hasNext()) {
                Record record = result.next();
                String label = record.get("label").asString();
                long count = record.get("count").asLong();
                String displayName = LABEL_DISPLAY.getOrDefault(label, label);
                // 只显示白名单内的标签
                if (!ALLOWED_LABELS.contains(label) && !LABEL_DISPLAY.containsKey(label)) continue;
                if (merged.containsKey(displayName)) {
                    Map<String, Object> existing = merged.get(displayName);
                    existing.put("count", ((Long) existing.get("count")) + count);
                } else {
                    Map<String, Object> entry = new LinkedHashMap<>();
                    entry.put("label", label);
                    entry.put("displayName", displayName);
                    entry.put("count", count);
                    merged.put(displayName, entry);
                }
            }
        } catch (Exception e) {
            log.error("[neo4j] 列出标签失败: err={}", e.getMessage(), e);
            throw new RuntimeException("列出标签失败: " + e.getMessage(), e);
        }
        return new ArrayList<>(merged.values());
    }

    public List<Map<String, Object>> listRelationshipTypes() {
        List<Map<String, Object>> result = new ArrayList<>();
        try (Session session = driver.session()) {
            Result rs = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC"
            );
            while (rs.hasNext()) {
                Record record = rs.next();
                String type = record.get("type").asString();
                long count = record.get("count").asLong();
                Map<String, Object> entry = new LinkedHashMap<>();
                entry.put("type", REL_TYPE_DISPLAY.getOrDefault(type, type));
                entry.put("rawType", type);
                entry.put("count", count);
                result.add(entry);
            }
        }
        return result;
    }

    public List<Map<String, Object>> listNodesByLabel(String label, int limit) {
        if (!ALLOWED_LABELS.contains(label) && !LABEL_DISPLAY.containsKey(label)) {
            // 尝试反向查找：通过 displayName 找 label
            boolean found = false;
            for (Map.Entry<String, String> e : LABEL_DISPLAY.entrySet()) {
                if (e.getValue().equals(label) && ALLOWED_LABELS.contains(e.getKey())) {
                    label = e.getKey();
                    found = true;
                    break;
                }
            }
            if (!found) throw new IllegalArgumentException("不允许的标签: " + label);
        }
        List<Map<String, Object>> nodes = new ArrayList<>();
        try (Session session = driver.session()) {
            String cypher;
            String businessKey = businessKeyOf(label);
            // 按业务主键排序（有就按主键，没有按 name）
            cypher = "MATCH (n:`" + label + "`) RETURN n, labels(n) AS labels, id(n) AS internalId " +
                     "ORDER BY n." + businessKey + " ASC LIMIT $limit";
            Result result = session.run(cypher, Map.of("limit", limit));
            while (result.hasNext()) {
                Record record = result.next();
                Node node = record.get("n").asNode();
                nodes.add(buildNodeMap(node, record.get("labels").asList(Value::asString)));
            }
        } catch (Exception e) {
            log.error("[neo4j] 查询节点失败: label={}, err={}", label, e.getMessage(), e);
        }
        return nodes;
    }

    /**
     * 按标签查询节点（返回Map格式，给Controller用）
     */
    public Map<String, Object> listNodesByLabelMap(String label, int limit) {
        List<Map<String, Object>> nodes = listNodesByLabel(label, limit);
        return Map.of("nodes", nodes);
    }

    /**
     * 按业务键查询节点
     */
    public Map<String, Object> getNode(String label, Object businessId) {
        if (!ALLOWED_LABELS.contains(label)) return null;
        String businessKey = businessKeyOf(label);
        try (Session session = driver.session()) {
            String cypher = "MATCH (n:`" + label + "` {" + businessKey + ": $bizId}) " +
                           "RETURN n, labels(n) AS labels, id(n) AS internalId LIMIT 1";
            Result result = session.run(cypher, Map.of("bizId", businessId));
            if (result.hasNext()) {
                Record record = result.next();
                return buildNodeMap(record.get("n").asNode(), record.get("labels").asList(Value::asString));
            }
        } catch (Exception e) {
            log.error("[neo4j] 按业务键查询节点失败: label={}, bizId={}, err={}", label, businessId, e.getMessage());
        }
        return null;
    }

    /**
     * 按内部ID查询节点（别名）
     */
    public Map<String, Object> getNodeByInternalId(Long internalId) {
        return getNode(internalId);
    }

    /**
     * 按业务键删除节点（连带关系）
     */
    public Map<String, Object> deleteNode(String label, Object businessId) {
        if (!ALLOWED_LABELS.contains(label)) {
            return Map.of("deleted", 0, "message", "不允许的标签");
        }
        String businessKey = businessKeyOf(label);
        try (Session session = driver.session()) {
            String cypher = "MATCH (n:`" + label + "` {" + businessKey + ": $bizId}) " +
                           "DETACH DELETE n RETURN count(n) AS deleted";
            Result result = session.run(cypher, Map.of("bizId", businessId));
            long deleted = result.single().get("deleted").asLong();
            log.info("[neo4j] 删除节点: label={}, bizId={}, deleted={}", label, businessId, deleted);
            return Map.of("deleted", deleted);
        } catch (Exception e) {
            log.error("[neo4j] 删除节点失败: label={}, bizId={}, err={}", label, businessId, e.getMessage());
            return Map.of("deleted", 0, "error", e.getMessage());
        }
    }

    /**
     * 按关系内部ID删除关系
     */
    public Map<String, Object> deleteRelationship(Long relId) {
        try (Session session = driver.session()) {
            String cypher = "MATCH ()-[r]->() WHERE id(r) = $relId DELETE r RETURN count(r) AS deleted";
            Result result = session.run(cypher, Map.of("relId", relId));
            long deleted = result.single().get("deleted").asLong();
            return Map.of("deleted", deleted);
        } catch (Exception e) {
            log.error("[neo4j] 删除关系失败: relId={}, err={}", relId, e.getMessage());
            return Map.of("deleted", 0, "error", e.getMessage());
        }
    }

    /**
     * 收起节点邻居（返回邻居ID和关系ID列表）
     */
    public Map<String, Object> getNodeNeighborInfo(Long internalId) {
        List<Long> neighborIds = new ArrayList<>();
        List<Long> relIds = new ArrayList<>();
        try (Session session = driver.session()) {
            Result result = session.run(
                "MATCH (center)-[r]-(neighbor) WHERE id(center) = $id " +
                "RETURN DISTINCT id(neighbor) AS nid, id(r) AS rid",
                Map.of("id", internalId)
            );
            while (result.hasNext()) {
                Record rec = result.next();
                neighborIds.add(rec.get("nid").asLong());
                relIds.add(rec.get("rid").asLong());
            }
        }
        return Map.of("neighborIds", neighborIds, "relIds", relIds);
    }

    /**
     * 展开指定节点的邻居（一级），返回新节点和新边
     */
    public Map<String, Object> expandNeighbors(Long internalId) {
        List<Map<String, Object>> newNodes = new ArrayList<>();
        List<Map<String, Object>> newEdges = new ArrayList<>();
        try (Session session = driver.session()) {
            // 查询该节点直接相连的邻居（一跳）
            String cypher =
                "MATCH (center) WHERE id(center) = $id " +
                "MATCH (center)-[r]-(neighbor) " +
                "RETURN neighbor, labels(neighbor) AS nLabels, id(neighbor) AS nInternalId, " +
                "r, type(r) AS relType, id(r) AS relInternalId";
            Result result = session.run(cypher, Map.of("id", internalId));
            while (result.hasNext()) {
                Record record = result.next();
                Node neighbor = record.get("neighbor").asNode();
                List<String> nLabels = record.get("nLabels").asList(Value::asString);
                long nInternalId = record.get("nInternalId").asLong();
                Relationship rel = record.get("r").asRelationship();
                String relType = record.get("relType").asString();
                long relInternalId = record.get("relInternalId").asLong();

                // 过滤白名单标签
                boolean labelOk = nLabels.stream().anyMatch(ALLOWED_LABELS::contains);
                if (!labelOk) continue;

                Map<String, Object> nodeMap = buildNodeMap(neighbor, nLabels);
                nodeMap.put("id", nInternalId);
                newNodes.add(nodeMap);

                Map<String, Object> edge = new LinkedHashMap<>();
                edge.put("id", relInternalId);
                edge.put("from", rel.startNodeId());
                edge.put("to", rel.endNodeId());
                edge.put("label", REL_TYPE_DISPLAY.getOrDefault(relType, relType));
                edge.put("rawType", relType);
                edge.put("properties", rel.asMap());
                newEdges.add(edge);
            }
        }
        return Map.of("nodes", newNodes, "edges", newEdges);
    }

    /**
     * 获取某节点的直接邻居 ID 列表（用于收起）
     */
    public List<Long> getNodeNeighborIds(Long internalId) {
        List<Long> ids = new ArrayList<>();
        try (Session session = driver.session()) {
            Result result = session.run(
                "MATCH (center)-[r]-(neighbor) WHERE id(center) = $id " +
                "RETURN DISTINCT id(neighbor) AS nid",
                Map.of("id", internalId)
            );
            while (result.hasNext()) {
                ids.add(result.next().get("nid").asLong());
            }
        }
        return ids;
    }

    /**
     * 查询调度大屏图谱（Incident/Resource/DispatchOrder 相关）
     */
    public Map<String, Object> getDispatchGraph(Long incidentId) {
        Map<String, Object> graph = new HashMap<>();
        List<Map<String, Object>> nodes = new ArrayList<>();
        List<Map<String, Object>> edges = new ArrayList<>();

        try (Session session = driver.session()) {
            String nodeCypher = incidentId == null
                ? "MATCH (n) WHERE n:受灾点 OR n:物资仓库 OR n:物资 OR n:救援队伍 OR n:避难场所 OR n:道路 OR n:调度指令 " +
                  "RETURN n, labels(n) AS labels"
                : "MATCH (n) WHERE (n:受灾点 OR n:物资仓库 OR n:物资 OR n:救援队伍 OR n:避难场所 OR n:道路 OR n:调度指令) " +
                  "AND (n:受灾点 {incidentId: $incidentId} OR " +
                  "      EXISTS { MATCH (n)<-[:`调度给`]-(d:调度指令) WHERE d.incidentId = $incidentId } OR " +
                  "      EXISTS { MATCH (n)-[:`调度给`]->(:受灾点 {incidentId: $incidentId}) } OR " +
                  "      EXISTS { MATCH (n)<-[:位于|:是|:具备|:涉及]-(:受灾点 {incidentId: $incidentId}) } OR " +
                  "      EXISTS { MATCH (n)-[:位于|:是|:具备|:涉及]->(:受灾点 {incidentId: $incidentId}) }) " +
                  "RETURN n, labels(n) AS labels";

            Map<String, Object> params = incidentId == null ? new HashMap<>() : new HashMap<>(Map.of("incidentId", incidentId));
            Result nodeResult = session.run(nodeCypher, params);
            List<Long> nodeIds = new ArrayList<>();
            while (nodeResult.hasNext()) {
                Record record = nodeResult.next();
                Node node = record.get("n").asNode();
                List<String> nodeLabels = record.get("labels").asList(Value::asString);
                nodes.add(buildNodeMap(node, nodeLabels));
                nodeIds.add(node.id());
            }

            params.put("nodeIds", nodeIds);
            String relCypher = "MATCH (a)-[r]->(b) WHERE id(a) IN $nodeIds AND id(b) IN $nodeIds RETURN a, r, b, type(r) AS relType";
            Result relResult = session.run(relCypher, params);
            while (relResult.hasNext()) {
                Record record = relResult.next();
                Relationship rel = record.get("r").asRelationship();
                String relType = record.get("relType").asString();
                Map<String, Object> edge = new LinkedHashMap<>();
                edge.put("id", rel.id());
                edge.put("from", rel.startNodeId());
                edge.put("to", rel.endNodeId());
                edge.put("label", REL_TYPE_DISPLAY.getOrDefault(relType, relType));
                edge.put("rawType", relType);
                edge.put("properties", rel.asMap());
                edges.add(edge);
            }
        } catch (Exception e) {
            log.error("[neo4j] 查询调度图谱失败: incidentId={}, err={}", incidentId, e.getMessage(), e);
        }
        graph.put("nodes", nodes);
        graph.put("edges", edges);
        return graph;
    }

    /**
     * 导出全量图谱数据（适合大批量图谱对接）：
     * { nodes: [ {id, label, group, properties} ], relationships: [ {id, from, to, label, type, properties} ] }
     */
    public Map<String, Object> exportAllGraph() {
        List<Map<String, Object>> nodes = new ArrayList<>();
        List<Map<String, Object>> relationships = new ArrayList<>();

        try (Session session = driver.session()) {
            // 1. 查询全部节点
            Result nodeResult = session.run(
                "MATCH (n) RETURN n, labels(n) AS labels, id(n) AS internalId"
            );
            Map<Long, Map<String, Object>> nodeIndex = new LinkedHashMap<>();
            while (nodeResult.hasNext()) {
                Record record = nodeResult.next();
                Node node = record.get("n").asNode();
                List<String> labels = record.get("labels").asList(Value::asString);
                long internalId = record.get("internalId").asLong();
                Map<String, Object> nodeMap = buildNodeMap(node, labels);
                nodes.add(nodeMap);
                nodeIndex.put(internalId, nodeMap);
            }

            // 2. 查询全部关系
            Result relResult = session.run(
                "MATCH ()-[r]->() RETURN r, id(r) AS relId, type(r) AS relType, " +
                "id(startNode(r)) AS fromId, id(endNode(r)) AS toId"
            );
            while (relResult.hasNext()) {
                Record record = relResult.next();
                Relationship rel = record.get("r").asRelationship();
                long relId = record.get("relId").asLong();
                String relType = record.get("relType").asString();
                long fromId = record.get("fromId").asLong();
                long toId = record.get("toId").asLong();

                Map<String, Object> edge = new LinkedHashMap<>();
                edge.put("id", relId);
                edge.put("from", fromId);
                edge.put("to", toId);
                edge.put("label", REL_TYPE_DISPLAY.getOrDefault(relType, relType));
                edge.put("type", relType);
                edge.put("properties", rel.asMap());

                // 附带起止节点名称便于AI理解
                Map<String, Object> fromNode = nodeIndex.get(fromId);
                Map<String, Object> toNode = nodeIndex.get(toId);
                if (fromNode != null) edge.put("fromLabel", fromNode.get("label"));
                if (toNode != null) edge.put("toLabel", toNode.get("label"));

                relationships.add(edge);
            }
        } catch (Exception e) {
            log.error("[neo4j] 导出全量图谱失败: err={}", e.getMessage(), e);
            throw new RuntimeException("导出全量图谱失败: " + e.getMessage(), e);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("nodes", nodes);
        result.put("relationships", relationships);
        result.put("nodeCount", nodes.size());
        result.put("relationshipCount", relationships.size());
        log.info("[neo4j] 导出全量图谱完成: nodes={}, relationships={}", nodes.size(), relationships.size());
        return result;
    }

    // ============ SQL ↔ Neo4j 一致性校验 ============

    public long countByLabel(String label) {
        if (!ALLOWED_LABELS.contains(label)) return 0;
        try (Session session = driver.session()) {
            Result result = session.run("MATCH (n:`" + label + "`) RETURN count(n) AS c");
            return result.single().get("c").asLong();
        }
    }

    public List<Object> listBusinessIds(String label, String businessKey) {
        List<Object> ids = new ArrayList<>();
        try (Session session = driver.session()) {
            Result result = session.run(
                "MATCH (n:`" + label + "`) RETURN n." + businessKey + " AS id ORDER BY id"
            );
            while (result.hasNext()) {
                Value v = result.next().get("id");
                if (!v.isNull()) ids.add(v.asObject());
            }
        }
        return ids;
    }

    public List<Long> findOrphanNodes(String label, String businessKey, List<Object> sqlIds) {
        List<Long> orphanInternalIds = new ArrayList<>();
        try (Session session = driver.session()) {
            Result result = session.run(
                "MATCH (n:`" + label + "`) WHERE NOT n." + businessKey + " IN $sqlIds RETURN id(n) AS id",
                Map.of("sqlIds", sqlIds)
            );
            while (result.hasNext()) {
                orphanInternalIds.add(result.next().get("id").asLong());
            }
        }
        return orphanInternalIds;
    }

    // ============ 维护工具 ============

    public Map<String, Object> clearAll() {
        try (Session session = driver.session()) {
            Result result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) AS deleted");
            long deleted = result.single().get("deleted").asLong();
            log.info("[neo4j] 清空所有节点: deleted={}", deleted);
            return Map.of("deletedNodes", deleted, "message", "已清空所有节点和关系");
        } catch (Exception e) {
            log.error("[neo4j] 清空失败: err={}", e.getMessage(), e);
            throw new RuntimeException("清空失败: " + e.getMessage(), e);
        }
    }

    /**
     * 更新物资仓库的物资库存（扣减/增加）
     */
    public void updateMaterialStock(String resourceNo, int allocatedQty) {
        try (Session session = driver.session()) {
            String cypher = "MATCH (w:物资仓库 {resourceNo: $resourceNo}) " +
                           "SET w.availableQty = coalesce(w.availableQty, 0) - $allocatedQty " +
                           "RETURN w";
            session.run(cypher, Map.of("resourceNo", resourceNo, "allocatedQty", allocatedQty));
            log.info("[neo4j] 更新物资仓库库存: resourceNo={}, allocatedQty={}", resourceNo, allocatedQty);
        } catch (Exception e) {
            log.error("[neo4j] 更新物资仓库库存失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 更新救援队伍状态（忙碌/空闲）
     */
    public void updateTeamStatus(String resourceNo, boolean isBusy) {
        try (Session session = driver.session()) {
            String statusName = isBusy ? "忙碌" : "空闲";
            String cypher = "MATCH (t:救援队伍 {resourceNo: $resourceNo}) " +
                           "SET t.isBusy = $isBusy, t.status = $statusInt " +
                           "RETURN t";
            session.run(cypher, Map.of(
                "resourceNo", resourceNo,
                "isBusy", isBusy,
                "statusInt", isBusy ? 1 : 0
            ));
            // 同时更新关联的状态节点
            String relCypher = "MATCH (t:救援队伍 {resourceNo: $resourceNo})-[r:状态]->(s:状态) " +
                              "SET s.name = $statusName";
            session.run(relCypher, Map.of("resourceNo", resourceNo, "statusName", statusName));
            log.info("[neo4j] 更新救援队伍状态: resourceNo={}, isBusy={}", resourceNo, isBusy);
        } catch (Exception e) {
            log.error("[neo4j] 更新救援队伍状态失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 更新避难场所剩余容纳人数
     */
    public void updateShelterCapacity(String resourceNo, int evacuees) {
        try (Session session = driver.session()) {
            String cypher = "MATCH (s:避难场所 {resourceNo: $resourceNo}) " +
                           "SET s.remainingCapacity = coalesce(s.remainingCapacity, s.maxCapacity, 0) - $evacuees, " +
                           "    s.currentOccupancy = coalesce(s.currentOccupancy, 0) + $evacuees " +
                           "RETURN s";
            session.run(cypher, Map.of("resourceNo", resourceNo, "evacuees", evacuees));
            log.info("[neo4j] 更新避难场所容量: resourceNo={}, evacuees={}", resourceNo, evacuees);
        } catch (Exception e) {
            log.error("[neo4j] 更新避难场所容量失败: {}", e.getMessage(), e);
        }
    }

    // ============ 工具方法 ============

    public static String businessKeyOf(String label) {
        return switch (label) {
            case "受灾点" -> "incidentId";
            case "物资仓库" -> "resourceNo";
            case "物资" -> "resourceNo";
            case "物资单品" -> "itemId";
            case "救援队伍" -> "resourceNo";
            case "避难场所" -> "resourceNo";
            case "道路" -> "roadNo";
            case "调度指令" -> "dispatchOrderId";
            case "地点名称", "地点" -> "name";
            case "场所名称" -> "name";
            case "灾害类型" -> "typeName";
            case "危险等级" -> "level";
            case "受灾人数" -> "incidentId";
            case "数量", "数值" -> "value";
            case "重量" -> "value";
            case "队伍类型" -> "typeName";
            case "擅长灾害" -> "typeName";
            case "适用灾害" -> "typeName";
            case "状态", "通行状态" -> "name";
            case "道路编号" -> "code";
            case "道路名称" -> "name";
            case "道路等级" -> "level";
            case "承载上限" -> "value";
            case "通行代价" -> "value";
            case "最大容纳人数", "已容纳人数" -> "value";
            case "最大运载重量" -> "value";
            default -> "name";
        };
    }

    private Map<String, Object> buildNodeMap(Node node, List<String> labels) {
        Map<String, Object> map = new LinkedHashMap<>();
        long internalId = node.id();
        Map<String, Object> props = node.asMap();
        // 取第一个白名单标签作为分组
        String primaryLabel = labels.stream()
            .filter(ALLOWED_LABELS::contains)
            .findFirst()
            .orElse(labels.isEmpty() ? "未知" : labels.get(0));
        String displayName = extractNodeName(primaryLabel, props);

        map.put("id", internalId);
        map.put("label", displayName);
        map.put("group", LABEL_DISPLAY.getOrDefault(primaryLabel, primaryLabel));
        map.put("rawLabel", primaryLabel);
        map.put("allLabels", labels);
        map.put("properties", props);
        return map;
    }

    private static String extractNodeName(String label, Map<String, Object> props) {
        // 优先使用通用 name 字段
        if (props.containsKey("name") && props.get("name") != null) {
            String name = String.valueOf(props.get("name"));
            if (!name.isBlank()) return name;
        }
        return switch (label) {
            case "受灾点" -> firstNonBlank(
                (String) props.get("title"), (String) props.get("incidentTitle"), "受灾点"
            );
            case "危险等级" -> {
                Object lv = props.get("level");
                if (lv != null) {
                    int lvInt = ((Number) lv).intValue();
                    yield "等级" + lvInt + "级";
                }
                yield firstNonBlank((String) props.get("name"), "危险等级");
            }
            case "受灾人数" -> {
                Object cnt = props.get("count");
                if (cnt != null) yield cnt + "人";
                yield "受灾人数";
            }
            case "调度指令" -> firstNonBlank((String) props.get("orderNo"), "调度指令");
            default -> firstNonBlank(
                (String) props.get("typeName"),
                (String) props.get("value"),
                (String) props.get("name"),
                "未命名"
            );
        };
    }

    private static String firstNonBlank(String... values) {
        for (String v : values) {
            if (v != null && !v.isBlank() && !"null".equals(v)) return v;
        }
        return "未命名";
    }

    private static Map<String, Object> nodeToMap(Node node, String label) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", node.id());
        map.put("label", label);
        map.put("properties", node.asMap());
        return map;
    }
}
