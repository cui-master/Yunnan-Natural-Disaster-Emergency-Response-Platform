package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.AgentRun;
import com.yunnan.emergency.entity.Citation;
import com.yunnan.emergency.mapper.AgentRunMapper;
import com.yunnan.emergency.mapper.CitationMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Agent执行记录", description = "Agent执行过程和引用来源查询")
@RestController
@RequestMapping("/agent-runs")
public class AgentRunController {
    public AgentRunController(AgentRunMapper agentRunMapper, CitationMapper citationMapper) {
        this.agentRunMapper = agentRunMapper;
        this.citationMapper = citationMapper;
    }


    private final AgentRunMapper agentRunMapper;
    private final CitationMapper citationMapper;

    @Operation(summary = "分页查询Agent执行记录")
    @GetMapping("/page")
    public Result<Page<AgentRun>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String taskType,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String provider,
            @RequestParam(required = false) Long incidentId,
            @RequestParam(required = false) Long userId) {

        LambdaQueryWrapper<AgentRun> wrapper = new LambdaQueryWrapper<>();
        if (taskType != null && !taskType.isEmpty()) {
            wrapper.eq(AgentRun::getTaskType, taskType);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(AgentRun::getStatus, status);
        }
        if (provider != null && !provider.isEmpty()) {
            wrapper.eq(AgentRun::getProvider, provider);
        }
        if (incidentId != null) {
            wrapper.eq(AgentRun::getIncidentId, incidentId);
        }
        if (userId != null) {
            wrapper.eq(AgentRun::getUserId, userId);
        }
        wrapper.orderByDesc(AgentRun::getCreatedAt);

        Page<AgentRun> page = agentRunMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取执行详情")
    @GetMapping("/{id}")
    public Result<AgentRun> getById(@PathVariable Long id) {
        return Result.success(agentRunMapper.selectById(id));
    }

    @Operation(summary = "获取引用来源列表")
    @GetMapping("/{runId}/citations")
    public Result<List<Citation>> getCitations(@PathVariable Long runId) {
        List<Citation> list = citationMapper.selectList(
            new LambdaQueryWrapper<Citation>()
                .eq(Citation::getAgentRunId, runId)
                .orderByAsc(Citation::getPosition)
        );
        return Result.success(list);
    }

    @Operation(summary = "获取执行统计")
    @GetMapping("/stats")
    public Result<java.util.Map<String, Object>> getStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();

        Long total = agentRunMapper.selectCount(null);
        Long success = agentRunMapper.selectCount(
            new LambdaQueryWrapper<AgentRun>().eq(AgentRun::getStatus, "success")
        );
        Long failed = agentRunMapper.selectCount(
            new LambdaQueryWrapper<AgentRun>().eq(AgentRun::getStatus, "failed")
        );
        Long running = agentRunMapper.selectCount(
            new LambdaQueryWrapper<AgentRun>().eq(AgentRun::getStatus, "running")
        );

        stats.put("total", total);
        stats.put("success", success);
        stats.put("failed", failed);
        stats.put("running", running);
        stats.put("successRate", total > 0 ? (success * 100.0 / total) : 0);

        return Result.success(stats);
    }
}
