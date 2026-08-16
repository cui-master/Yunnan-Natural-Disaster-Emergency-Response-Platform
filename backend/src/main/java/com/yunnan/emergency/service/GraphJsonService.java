package com.yunnan.emergency.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yunnan.emergency.entity.IncidentReport;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 图数据库 JSON 文件服务
 * 负责读写 full_graph_triples.json，添加/删除受灾点等操作
 */
@Service
public class GraphJsonService {

    private static final String GRAPH_FILE = "full_graph_triples.json";
    private static final DateTimeFormatter DT_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    /**
     * 将审核通过的灾情上报作为受灾点添加到图 JSON 中
     * 同时写入 ai-service、frontend/public、frontend/dist 三个位置的副本
     */
    public void addIncidentToGraph(IncidentReport report, Long incidentId) throws Exception {
        // 读取现有 JSON
        Path jsonPath = findGraphJsonPath();
        if (jsonPath == null) {
            throw new RuntimeException("找不到图 JSON 文件: " + GRAPH_FILE);
        }

        ObjectMapper mapper = new ObjectMapper();
        String content = Files.readString(jsonPath, StandardCharsets.UTF_8);
        @SuppressWarnings("unchecked")
        Map<String, Object> graph = mapper.readValue(content, Map.class);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> triples = (List<Map<String, Object>>) graph.getOrDefault("triples", new ArrayList<>());

        String disasterName = report.getTitle();
        String location = report.getLocationName();
        int affected = (report.getAffectedPeople() == null ? 0 : report.getAffectedPeople())
                + (report.getCasualties() == null ? 0 : report.getCasualties());
        String disasterType = report.getDisasterType();
        String riskLevel = report.getRiskLevel();
        String roadName = report.getRoadName();

        // 危险等级映射：低→1, 中→2, 高→3, 极高→4
        String riskLevelValue = mapRiskLevel(riskLevel);

        // 添加受灾点三元组
        addTriple(triples, disasterName, "受灾点", "编号为", String.valueOf(incidentId), "受灾点编号");
        addTriple(triples, disasterName, "受灾点", "发生时间",
                report.getOccurredAt() != null ? report.getOccurredAt().format(DT_FMT) : "", "时间");
        addTriple(triples, disasterName, "受灾点", "上报时间",
                report.getCreatedAt() != null ? report.getCreatedAt().format(DT_FMT) : "", "时间");
        addTriple(triples, disasterName, "受灾点", "审核同意上报时间",
                java.time.LocalDateTime.now().format(DT_FMT), "时间");
        addTriple(triples, disasterName, "受灾点", "位于", location, "地点名称");
        addTriple(triples, disasterName, "受灾点", "是", disasterType + "灾害风险", "灾害类型");
        addTriple(triples, disasterName, "受灾点", "具备", riskLevelValue, "危险等级");
        addTriple(triples, disasterName, "受灾点", "涉及", String.valueOf(affected), "受灾人数");

        // 临近道路（如果有）
        if (roadName != null && !roadName.isEmpty()) {
            addTriple(triples, disasterName, "受灾点", "临近", roadName, "道路");
            addTriple(triples, roadName, "道路", "服务", disasterName, "受灾点");
        }

        // 更新总数
        graph.put("total_triples", triples.size());

        // 写回所有副本
        String newContent = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(graph);
        writeAllCopies(newContent);
    }

    private void addTriple(List<Map<String, Object>> triples, String subject, String subjectType,
                           String predicate, String object, String objectType) {
        Map<String, Object> t = new LinkedHashMap<>();
        t.put("subject", subject);
        t.put("subject_type", subjectType);
        t.put("predicate", predicate);
        t.put("object", object);
        t.put("object_type", objectType);
        triples.add(t);
    }

    private String mapRiskLevel(String level) {
        if (level == null) return "2";
        return switch (level) {
            case "低" -> "1";
            case "中" -> "2";
            case "高" -> "3";
            case "极高", "特别重大" -> "4";
            default -> "2";
        };
    }

    private Path findGraphJsonPath() {
        Path cwd = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        Path projectRoot;
        if ("backend".equalsIgnoreCase(cwd.getFileName().toString())) {
            projectRoot = cwd.getParent();
        } else if (Files.isDirectory(cwd.resolve("backend"))
                && Files.isDirectory(cwd.resolve("frontend"))
                && Files.isDirectory(cwd.resolve("ai-service"))) {
            projectRoot = cwd;
        } else {
            projectRoot = cwd;
        }

        Path[] candidates = {
            projectRoot.resolve("ai-service/app/" + GRAPH_FILE),
            projectRoot.resolve("frontend/public/" + GRAPH_FILE),
            projectRoot.resolve("backend/src/main/resources/db/" + GRAPH_FILE),
        };
        for (Path p : candidates) {
            if (Files.exists(p)) {
                return p;
            }
        }
        return null;
    }

    private void writeAllCopies(String content) throws Exception {
        Path cwd = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        Path projectRoot;
        if ("backend".equalsIgnoreCase(cwd.getFileName().toString())) {
            projectRoot = cwd.getParent();
        } else if (Files.isDirectory(cwd.resolve("backend"))
                && Files.isDirectory(cwd.resolve("frontend"))
                && Files.isDirectory(cwd.resolve("ai-service"))) {
            projectRoot = cwd;
        } else {
            projectRoot = cwd;
        }

        Path[] paths = {
            projectRoot.resolve("ai-service/app/" + GRAPH_FILE),
            projectRoot.resolve("frontend/public/" + GRAPH_FILE),
            projectRoot.resolve("frontend/dist/" + GRAPH_FILE),
        };
        for (Path p : paths) {
            try {
                if (Files.exists(p.getParent())) {
                    Files.writeString(p, content, StandardCharsets.UTF_8);
                }
            } catch (Exception ignored) {}
        }
    }

    /**
     * 从图 JSON 中删除指定受灾点的所有三元组。
     *
     * 匹配规则（按优先级）：
     * 1. 精确匹配受灾点 subject
     * 2. 模糊匹配：去掉 title 中的常见后缀（灾情上报/险情上报/地震/暴雨/洪涝/灾害等）后，
     *    与受灾点 subject（去掉"受灾点"后缀）做包含匹配
     * 3. 反向：受灾点 subject 去掉"受灾点"后缀 被 title 包含
     *
     * @param incidentName 受灾点名称或 incident title
     * @return 实际删除的三元组数量；未匹配到返回 0
     */
    public int removeIncidentFromGraph(String incidentName) throws Exception {
        if (incidentName == null || incidentName.isEmpty()) {
            return 0;
        }
        Path jsonPath = findGraphJsonPath();
        if (jsonPath == null) {
            return 0;
        }

        ObjectMapper mapper = new ObjectMapper();
        String content = Files.readString(jsonPath, StandardCharsets.UTF_8);
        @SuppressWarnings("unchecked")
        Map<String, Object> graph = mapper.readValue(content, Map.class);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> triples = (List<Map<String, Object>>) graph.getOrDefault("triples", new ArrayList<>());

        // 第一步：收集所有受灾点 subject
        List<String> incidentSubjects = new ArrayList<>();
        for (Map<String, Object> t : triples) {
            if ("受灾点".equals(t.get("subject_type"))) {
                String subj = (String) t.get("subject");
                if (subj != null && !incidentSubjects.contains(subj)) {
                    incidentSubjects.add(subj);
                }
            }
        }

        // 第二步：确定要删除的受灾点 subject 列表
        // 1) 精确匹配
        // 2) 模糊匹配（去掉常见后缀后做包含匹配）
        List<String> toRemove = new ArrayList<>();
        String normalizedTitle = normalizeForMatch(incidentName);

        for (String subj : incidentSubjects) {
            if (subj.equals(incidentName)) {
                toRemove.add(subj);
                continue;
            }
            String normalizedSubj = normalizeForMatch(subj);
            // 至少 4 个字符的重叠才算匹配，避免误删
            if (normalizedTitle.length() >= 4
                    && normalizedSubj.length() >= 4
                    && (normalizedTitle.contains(normalizedSubj)
                        || normalizedSubj.contains(normalizedTitle))) {
                toRemove.add(subj);
            }
        }

        if (toRemove.isEmpty()) {
            return 0;
        }

        // 第三步：删除这些受灾点作为 subject 的所有三元组，以及 object 指向它们的反向关系
        List<Map<String, Object>> remaining = new ArrayList<>();
        int removed = 0;
        for (Map<String, Object> t : triples) {
            String subj = (String) t.get("subject");
            String obj = (String) t.get("object");
            if (toRemove.contains(subj) || toRemove.contains(obj)) {
                removed++;
                continue;
            }
            remaining.add(t);
        }

        graph.put("triples", remaining);
        graph.put("total_triples", remaining.size());

        String newContent = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(graph);
        writeAllCopies(newContent);

        return removed;
    }

    /**
     * 归一化字符串用于模糊匹配：去掉"受灾点"后缀和常见灾情关键词，
     * 只保留地名核心部分。
     */
    private String normalizeForMatch(String s) {
        if (s == null) return "";
        String r = s;
        // 去掉"受灾点"后缀
        r = r.replace("受灾点", "");
        // 去掉常见灾情后缀关键词
        String[] suffixes = {"灾情上报", "险情上报", "灾害上报", "灾情", "险情",
                             "地震", "暴雨", "洪涝", "洪水", "山洪", "滑坡",
                             "泥石流", "崩塌", "山体滑坡", "灾害风险", "灾害"};
        for (String suf : suffixes) {
            if (r.endsWith(suf)) {
                r = r.substring(0, r.length() - suf.length());
            }
        }
        return r.trim();
    }

    /**
     * 按 incidentId 从图 JSON 中删除受灾点及其所有关联三元组。
     *
     * 匹配规则：受灾点的 "编号为" 三元组 object 等于 incidentId。
     * 这是比按 title 匹配更可靠的方式，因为 incidents 表的 title
     * （如"东川区铜都街道受灾点险情上报"）与 JSON 中受灾点 subject
     * （如"东川区铜都街道受灾点"）通常不一致。
     *
     * 删除范围：
     * 1. 该受灾点作为 subject 的所有三元组（编号为/位于/是/具备/涉及/发生时间/上报时间/审核时间/审核同意上报时间/临近等）
     * 2. 反向关系（如 道路 -[服务]-> 受灾点）
     *
     * @param incidentId 受灾点编号（对应 incidents 表主键 id）
     * @return 实际删除的三元组数量；若未匹配到受灾点返回 0
     */
    public int removeIncidentFromGraphById(Long incidentId) throws Exception {
        if (incidentId == null) {
            return 0;
        }
        Path jsonPath = findGraphJsonPath();
        if (jsonPath == null) {
            return 0;
        }

        ObjectMapper mapper = new ObjectMapper();
        String content = Files.readString(jsonPath, StandardCharsets.UTF_8);
        @SuppressWarnings("unchecked")
        Map<String, Object> graph = mapper.readValue(content, Map.class);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> triples = (List<Map<String, Object>>) graph.getOrDefault("triples", new ArrayList<>());

        String idStr = String.valueOf(incidentId);

        // 第一步：找到 "编号为" = incidentId 的受灾点 subject
        String incidentSubject = null;
        for (Map<String, Object> t : triples) {
            String subjType = (String) t.get("subject_type");
            String pred = (String) t.get("predicate");
            String objType = (String) t.get("object_type");
            Object obj = t.get("object");
            if ("受灾点".equals(subjType)
                    && "编号为".equals(pred)
                    && "受灾点编号".equals(objType)
                    && obj != null && idStr.equals(String.valueOf(obj))) {
                incidentSubject = (String) t.get("subject");
                break;
            }
        }

        if (incidentSubject == null) {
            // 未匹配到受灾点，不做任何删除
            return 0;
        }

        // 第二步：删除该受灾点作为 subject 的所有三元组，以及 object 指向它的反向关系
        List<Map<String, Object>> remaining = new ArrayList<>();
        int removed = 0;
        for (Map<String, Object> t : triples) {
            String subj = (String) t.get("subject");
            String obj = (String) t.get("object");
            if (incidentSubject.equals(subj)) {
                removed++;
                continue;
            }
            if (incidentSubject.equals(obj)) {
                removed++;
                continue;
            }
            remaining.add(t);
        }

        graph.put("triples", remaining);
        graph.put("total_triples", remaining.size());

        String newContent = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(graph);
        writeAllCopies(newContent);

        return removed;
    }
}
