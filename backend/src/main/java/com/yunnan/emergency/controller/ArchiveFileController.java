package com.yunnan.emergency.controller;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.ArchiveFile;
import com.yunnan.emergency.entity.DisasterSituation;
import com.yunnan.emergency.entity.Info;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.DisasterSituationMapper;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.service.ArchiveFileService;
import com.yunnan.emergency.service.DisasterSituationService;
import com.yunnan.emergency.service.GraphJsonService;
import com.yunnan.emergency.service.InfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Slf4j
@Tag(name = "归档管理", description = "实时事件流归档")
@RestController
@RequestMapping("/archive-files")
public class ArchiveFileController {

    private final ArchiveFileService archiveFileService;
    private final InfoService infoService;
    private final IncidentMapper incidentMapper;
    private final DisasterSituationMapper disasterSituationMapper;
    private final DisasterSituationService disasterSituationService;
    private final GraphJsonService graphJsonService;

    public ArchiveFileController(ArchiveFileService archiveFileService, InfoService infoService,
                                  IncidentMapper incidentMapper, DisasterSituationMapper disasterSituationMapper,
                                  DisasterSituationService disasterSituationService,
                                  GraphJsonService graphJsonService) {
        this.archiveFileService = archiveFileService;
        this.infoService = infoService;
        this.incidentMapper = incidentMapper;
        this.disasterSituationMapper = disasterSituationMapper;
        this.disasterSituationService = disasterSituationService;
        this.graphJsonService = graphJsonService;
    }

    @Operation(summary = "分页查询归档记录")
    @GetMapping("/page")
    public Result<Page<ArchiveFile>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        Page<ArchiveFile> page = archiveFileService.page(new Page<>(pageNum, pageSize));
        return Result.success(page);
    }

    @Operation(summary = "创建归档")
    @PostMapping
    @PreAuthorize("hasRole('RESMANAGER')")
    public Result<ArchiveFile> create(@RequestBody ArchiveFile archiveFile,
                                      @AuthenticationPrincipal User user) {
        LocalDateTime now = LocalDateTime.now();
        archiveFile.setCreatedAt(now);
        archiveFile.setUpdatedAt(now);
        archiveFileService.save(archiveFile);

        // 提取归档的事件 ID 列表
        List<Long> archivedIds = extractEventIdsFromContent(archiveFile.getContent());
        log.info("[归档] 收到归档请求，事件数: {}", archivedIds.size());

        // 1. 更新 incidents 表状态为"已归档"（能找到的就更新）
        int inProgressCount = 0;
        Set<Long> matchedIncidentIds = new HashSet<>();
        for (Long id : archivedIds) {
            try {
                Incident inc = incidentMapper.selectById(id);
                if (inc != null) {
                    matchedIncidentIds.add(id);
                    String status = inc.getStatus();
                    // 判断是否属于处置中/进行中的事件
                    if (isActiveStatus(status)) {
                        inProgressCount++;
                    }
                    inc.setStatus("已归档");
                    incidentMapper.updateById(inc);
                }
            } catch (Exception e) {
                log.warn("[归档] 更新 incident 状态失败 id={}: {}", id, e.getMessage());
            }
        }
        log.info("[归档] incidents 表匹配并更新 {} 条，其中处置中 {} 条", matchedIncidentIds.size(), inProgressCount);

        // 2. 直接从 disaster_situation.realtime_events 中移除已归档事件（确保前端立即生效）
        try {
            DisasterSituation ds = disasterSituationMapper.selectById(1L);
            if (ds != null && ds.getRealtimeEvents() != null) {
                JSONArray events = JSONUtil.parseArray(ds.getRealtimeEvents());
                List<Object> remaining = new ArrayList<>();
                int removed = 0;
                for (int i = 0; i < events.size(); i++) {
                    JSONObject evt = events.getJSONObject(i);
                    Object idObj = evt.get("id");
                    Long evtId = null;
                    if (idObj instanceof Number) {
                        evtId = ((Number) idObj).longValue();
                    } else if (idObj != null) {
                        try { evtId = Long.parseLong(String.valueOf(idObj)); } catch (Exception ignored) {}
                    }
                    if (evtId != null && archivedIds.contains(evtId)) {
                        removed++;
                    } else {
                        remaining.add(evt);
                    }
                }
                if (removed > 0) {
                    ds.setRealtimeEvents(JSONUtil.toJsonStr(remaining));
                    ds.setRefreshedAt(now);
                    disasterSituationMapper.updateById(ds);
                    log.info("[归档] 从 realtime_events 移除 {} 条事件", removed);
                }
            }
        } catch (Exception e) {
            log.error("[归档] 更新 realtime_events 失败: {}", e.getMessage());
        }

        // 3. info 表：处置中事件数 -归档的处置中事件数
        if (inProgressCount > 0) {
            try {
                Info info = infoService.getOrInit();
                int current = info.getInProgress() == null ? 0 : info.getInProgress();
                info.setInProgress(Math.max(0, current - inProgressCount));
                infoService.updateById(info);
                log.info("[归档] info 表 in_progress: {} -> {}", current, Math.max(0, current - inProgressCount));
            } catch (Exception e) {
                log.error("[归档] 更新 info 表失败: {}", e.getMessage());
            }
        }

        // 4. 全量刷新 disaster_situation（类型分布、地市分布等其他统计也排除已归档）
        try {
            disasterSituationService.refresh();
            log.info("[归档] disaster_situation 全量刷新完成");
        } catch (Exception e) {
            log.error("[归档] disaster_situation 刷新失败: {}", e.getMessage());
        }

        // 5. 从图数据库 JSON 中删除对应受灾点节点
        //    匹配优先级：incidentId（编号为） > title 精确匹配 > title 模糊匹配
        try {
            int removedFromGraph = 0;
            for (Long id : archivedIds) {
                // 优先按 incidentId 匹配 JSON 中受灾点的 "编号为" 字段
                int removed = graphJsonService.removeIncidentFromGraphById(id);
                if (removed > 0) {
                    removedFromGraph += removed;
                    log.info("[归档] incidentId={} 按 id 删除 {} 条三元组", id, removed);
                    continue;
                }
                // 兜底：按 title 精确 + 模糊匹配（去掉"灾情上报/险情上报/地震"等后缀后做包含匹配）
                Incident inc = incidentMapper.selectById(id);
                if (inc != null && inc.getTitle() != null) {
                    int removedByTitle = graphJsonService.removeIncidentFromGraph(inc.getTitle());
                    if (removedByTitle > 0) {
                        removedFromGraph += removedByTitle;
                        log.info("[归档] incidentId={} 按 title 兜底删除 {} 条三元组 (title={})",
                                id, removedByTitle, inc.getTitle());
                    } else {
                        log.warn("[归档] incidentId={} 未在图 JSON 中匹配到受灾点 (title={})",
                                id, inc.getTitle());
                    }
                }
            }
            log.info("[归档] 从图 JSON 删除受灾点相关三元组共 {} 条", removedFromGraph);
        } catch (Exception e) {
            log.error("[归档] 从图 JSON 删除受灾点失败: {}", e.getMessage());
        }

        return Result.success(archiveFile);
    }

    private boolean isActiveStatus(String status) {
        if (status == null) return false;
        return switch (status) {
            case "处置中", "已确认", "active", "processing", "confirmed", "待核验", "pending" -> true;
            default -> false;
        };
    }

    @Operation(summary = "删除归档")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('RESMANAGER')")
    public Result<Void> delete(@PathVariable Long id) {
        archiveFileService.removeById(id);
        return Result.success();
    }

    /**
     * 从归档 content JSON 中提取事件 ID 列表
     */
    private List<Long> extractEventIdsFromContent(String content) {
        if (content == null || content.isEmpty()) {
            return new ArrayList<>();
        }
        try {
            JSONObject obj = JSONUtil.parseObj(content);
            Object eventsObj = obj.get("events");
            if (eventsObj instanceof List<?>) {
                List<?> events = (List<?>) eventsObj;
                List<Long> ids = new ArrayList<>();
                for (Object e : events) {
                    if (e instanceof JSONObject) {
                        JSONObject evt = (JSONObject) e;
                        Object idObj = evt.get("id");
                        if (idObj instanceof Number) {
                            ids.add(((Number) idObj).longValue());
                        } else if (idObj != null) {
                            try { ids.add(Long.parseLong(String.valueOf(idObj))); } catch (Exception ignored) {}
                        }
                    }
                }
                return ids;
            }
        } catch (Exception e) {
            log.warn("[归档] 解析 content 提取事件ID失败: {}", e.getMessage());
        }
        return new ArrayList<>();
    }
}
