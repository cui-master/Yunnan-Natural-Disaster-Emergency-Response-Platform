package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Info;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.ResourceMapper;
import com.yunnan.emergency.service.InfoService;
import com.yunnan.emergency.service.SqlNeo4jSyncService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Tag(name = "资源管理", description = "救援资源的增删改查")
@RestController
@RequestMapping("/resources")
public class ResourceController {
    public ResourceController(ResourceMapper resourceMapper, SqlNeo4jSyncService sqlNeo4jSyncService, InfoService infoService) {
        this.resourceMapper = resourceMapper;
        this.sqlNeo4jSyncService = sqlNeo4jSyncService;
        this.infoService = infoService;
    }


    private final ResourceMapper resourceMapper;
    private final SqlNeo4jSyncService sqlNeo4jSyncService;
    private final InfoService infoService;

    @Operation(summary = "分页查询资源")
    @GetMapping("/page")
    public Result<Page<Resource>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String resourceType,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<Resource> wrapper = new LambdaQueryWrapper<>();
        if (category != null && !category.isEmpty()) {
            wrapper.eq(Resource::getCategory, category);
        }
        if (resourceType != null && !resourceType.isEmpty()) {
            wrapper.eq(Resource::getResourceType, resourceType);
        }
        if (status != null) {
            wrapper.eq(Resource::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(Resource::getName, keyword)
                .or().like(Resource::getResourceNo, keyword)
                .or().like(Resource::getLocationName, keyword);
        }
        wrapper.orderByDesc(Resource::getCreatedAt);

        Page<Resource> page = resourceMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取资源列表（不分页，用于下拉选择）")
    @GetMapping("/list")
    public Result<List<Resource>> list(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Integer status) {

        LambdaQueryWrapper<Resource> wrapper = new LambdaQueryWrapper<>();
        if (category != null && !category.isEmpty()) {
            wrapper.eq(Resource::getCategory, category);
        }
        if (status != null) {
            wrapper.eq(Resource::getStatus, status);
        }
        wrapper.orderByAsc(Resource::getResourceNo);
        List<Resource> list = resourceMapper.selectList(wrapper);
        return Result.success(list);
    }

    @Operation(summary = "获取资源详情")
    @GetMapping("/{id}")
    public Result<Resource> getById(@PathVariable Long id) {
        Resource resource = resourceMapper.selectById(id);
        return Result.success(resource);
    }

    @Operation(summary = "新增资源")
    @PostMapping
    public Result<Resource> create(@RequestBody Resource resource,
                                    @AuthenticationPrincipal User user) {
        if (resource.getResourceNo() == null || resource.getResourceNo().isEmpty()) {
            resource.setResourceNo(generateResourceNo(resource.getCategory()));
        }
        if (resource.getStatus() == null) {
            resource.setStatus(1);
        }
        resourceMapper.insert(resource);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncResourceCreate(resource); } catch (Exception ignored) {}

        // 新增物资类资源 → info.available_resources 随机增加 500-1200
        // 新增救援队伍 → info.rescue_teams +1
        try {
            syncInfoOnResourceChange(resource.getCategory(), true, 1);
        } catch (Exception ignored) {}

        return Result.success(resource);
    }

    @Operation(summary = "更新资源")
    @PutMapping("/{id}")
    public Result<Resource> update(@PathVariable Long id, @RequestBody Resource resource) {
        resource.setId(id);
        resourceMapper.updateById(resource);
        Resource updated = resourceMapper.selectById(id);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncResourceUpdate(updated); } catch (Exception ignored) {}

        // 修改物资类资源 → info.available_resources 随机增加 500-1200
        try {
            if (isMaterialCategory(updated.getCategory())) {
                Info info = infoService.getOrInit();
                int increase = 500 + (int)(Math.random() * 701);
                int current = info.getAvailableResources() == null ? 0 : info.getAvailableResources();
                info.setAvailableResources(current + increase);
                infoService.updateById(info);
            }
        } catch (Exception ignored) {}

        return Result.success(updated);
    }

    @Operation(summary = "删除资源")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        Resource resource = resourceMapper.selectById(id);
        resourceMapper.deleteById(id);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncResourceDelete(id); } catch (Exception ignored) {}

        // 删除救援队伍 → info.rescue_teams -1
        try {
            if (resource != null && "team".equals(resource.getCategory())) {
                Info info = infoService.getOrInit();
                int current = info.getRescueTeams() == null ? 0 : info.getRescueTeams();
                info.setRescueTeams(Math.max(0, current - 1));
                infoService.updateById(info);
            }
        } catch (Exception ignored) {}

        return Result.success();
    }

    @Operation(summary = "获取资源分类统计")
    @GetMapping("/stats/category")
    public Result<java.util.Map<String, Object>> getCategoryStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();
        String[] categories = {"warehouse", "team", "shelter", "material", "equipment"};
        String[] categoryNames = {"仓库", "救援队伍", "避难所", "物资", "装备"};

        for (int i = 0; i < categories.length; i++) {
            Long count = resourceMapper.selectCount(
                new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, categories[i])
            );
            stats.put(categoryNames[i], count);
        }

        // 总资源数
        Long total = resourceMapper.selectCount(null);
        stats.put("total", total);

        // 可用资源数
        Long available = resourceMapper.selectCount(
            new LambdaQueryWrapper<Resource>().eq(Resource::getStatus, 1)
        );
        stats.put("available", available);

        return Result.success(stats);
    }

    @Operation(summary = "保存图谱 JSON 文件（同步更新 ai-service 和 frontend 静态目录）")
    @PostMapping("/graph-json")
    public Result<Map<String, Object>> saveGraphJson(@RequestBody Map<String, Object> graphJson) {
        try {
            String content = new com.fasterxml.jackson.databind.ObjectMapper()
                    .writerWithDefaultPrettyPrinter()
                    .writeValueAsString(graphJson);

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

            Path aiServicePath = projectRoot.resolve("ai-service/app/full_graph_triples.json").normalize();
            Path frontendPublicPath = projectRoot.resolve("frontend/public/full_graph_triples.json").normalize();
            Path frontendDistPath = projectRoot.resolve("frontend/dist/full_graph_triples.json").normalize();

            List<String> writtenPaths = new ArrayList<>();
            writeGraphJsonFile(aiServicePath, content, writtenPaths);
            writeGraphJsonFile(frontendPublicPath, content, writtenPaths);
            if (Files.exists(frontendDistPath.getParent())) {
                writeGraphJsonFile(frontendDistPath, content, writtenPaths);
            }

            if (writtenPaths.isEmpty()) {
                return Result.error("未能写入任何 JSON 文件，请检查项目路径: " + projectRoot);
            }

            // 同步更新 info 表：可用资源（物资单品数量之和）和救援队伍数量
            try {
                syncInfoFromGraphJson(graphJson);
            } catch (Exception e) {
                // info 同步失败不影响 JSON 保存主流程
            }

            return Result.success(Map.of(
                    "projectRoot", projectRoot.toString(),
                    "writtenPaths", writtenPaths,
                    "triples", graphJson.getOrDefault("total_triples", 0)
            ));
        } catch (Exception e) {
            return Result.error("保存图谱 JSON 失败: " + e.getMessage());
        }
    }

    /**
     * 从图谱 JSON 中提取可用资源与救援队伍数量并同步到 info 表。
     * 可用资源：所有 subject_type=物资单品、object_type=数量 的数值之和；
     * 救援队伍：subject_type=救援队伍 的不同实体数量。
     */
    @SuppressWarnings("unchecked")
    private void syncInfoFromGraphJson(Map<String, Object> graphJson) {
        Object triplesObj = graphJson.get("triples");
        if (!(triplesObj instanceof List<?>)) {
            return;
        }
        List<Map<String, Object>> triples = (List<Map<String, Object>>) triplesObj;

        int availableResources = 0;
        java.util.Set<String> rescueTeamSet = new java.util.HashSet<>();

        for (Map<String, Object> t : triples) {
            String subjectType = String.valueOf(t.getOrDefault("subject_type", ""));
            String predicate = String.valueOf(t.getOrDefault("predicate", ""));
            String objectType = String.valueOf(t.getOrDefault("object_type", ""));

            if ("物资单品".equals(subjectType) && "有".equals(predicate) && "数量".equals(objectType)) {
                String objectValue = String.valueOf(t.getOrDefault("object", "0"));
                // 兼容 "500" / "500件" / "500吨" 等写法，只取前导数字
                String number = objectValue.replaceAll("[^0-9].*$", "");
                if (!number.isEmpty()) {
                    try {
                        availableResources += Integer.parseInt(number);
                    } catch (NumberFormatException ignored) {
                    }
                }
            }

            if ("救援队伍".equals(subjectType)) {
                String subject = String.valueOf(t.getOrDefault("subject", ""));
                if (!subject.isEmpty()) {
                    rescueTeamSet.add(subject);
                }
            }
        }

        Info info = infoService.getOrInit();
        info.setAvailableResources(availableResources);
        info.setRescueTeams(rescueTeamSet.size());
        infoService.updateById(info);
    }

    private void writeGraphJsonFile(Path path, String content, List<String> writtenPaths) {
        try {
            Files.createDirectories(path.getParent());
            Files.writeString(path, content, StandardCharsets.UTF_8);
            writtenPaths.add(path.toString());
        } catch (IOException e) {
            throw new RuntimeException("写入失败 [" + path + "]: " + e.getMessage(), e);
        }
    }

    private String generateResourceNo(String category) {
        String prefix = switch (category) {
            case "warehouse" -> "WH";
            case "team" -> "TEAM";
            case "shelter" -> "SH";
            case "material" -> "MAT";
            case "equipment" -> "EQ";
            default -> "RES";
        };
        return prefix + "-" + String.format("%03d", System.currentTimeMillis() % 1000);
    }

    /**
     * 判断资源分类是否属于物资类（影响 available_resources）
     */
    private boolean isMaterialCategory(String category) {
        return "material".equals(category) || "warehouse".equals(category) || "equipment".equals(category);
    }

    /**
     * 资源增删时同步更新 info 表。
     * @param category 资源分类
     * @param isCreate true=新增 false=删除
     * @param count 变化数量
     */
    private void syncInfoOnResourceChange(String category, boolean isCreate, int count) {
        Info info = infoService.getOrInit();
        if (isMaterialCategory(category)) {
            // 物资类：随机增加 500-1200（新增时加，删除时不减少，按用户描述仅增改时增加）
            if (isCreate) {
                int increase = 500 + (int)(Math.random() * 701);
                int current = info.getAvailableResources() == null ? 0 : info.getAvailableResources();
                info.setAvailableResources(current + increase);
            }
        }
        if ("team".equals(category)) {
            // 队伍类：增减对应数量
            int current = info.getRescueTeams() == null ? 0 : info.getRescueTeams();
            if (isCreate) {
                info.setRescueTeams(current + count);
            } else {
                info.setRescueTeams(Math.max(0, current - count));
            }
        }
        infoService.updateById(info);
    }
}
