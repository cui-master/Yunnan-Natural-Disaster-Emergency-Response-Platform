package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Location;
import com.yunnan.emergency.mapper.LocationMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "行政区划", description = "位置/行政区划查询")
@RestController
@RequestMapping("/locations")
public class LocationController {
    public LocationController(LocationMapper locationMapper) {
        this.locationMapper = locationMapper;
    }


    private final LocationMapper locationMapper;

    @Operation(summary = "获取省列表")
    @GetMapping("/provinces")
    public Result<List<Location>> getProvinces() {
        List<Location> list = locationMapper.selectList(
            new LambdaQueryWrapper<Location>()
                .eq(Location::getLevel, "province")
                .eq(Location::getStatus, 1)
                .orderByAsc(Location::getId)
        );
        return Result.success(list);
    }

    @Operation(summary = "获取子级列表")
    @GetMapping("/children/{parentId}")
    public Result<List<Location>> getChildren(@PathVariable Long parentId) {
        List<Location> list = locationMapper.selectList(
            new LambdaQueryWrapper<Location>()
                .eq(Location::getParentId, parentId)
                .eq(Location::getStatus, 1)
                .orderByAsc(Location::getId)
        );
        return Result.success(list);
    }

    @Operation(summary = "按层级获取")
    @GetMapping("/level/{level}")
    public Result<List<Location>> getByLevel(@PathVariable String level) {
        List<Location> list = locationMapper.selectList(
            new LambdaQueryWrapper<Location>()
                .eq(Location::getLevel, level)
                .eq(Location::getStatus, 1)
                .orderByAsc(Location::getId)
        );
        return Result.success(list);
    }

    @Operation(summary = "获取位置详情")
    @GetMapping("/{id}")
    public Result<Location> getById(@PathVariable Long id) {
        return Result.success(locationMapper.selectById(id));
    }

    @Operation(summary = "搜索位置")
    @GetMapping("/search")
    public Result<List<Location>> search(@RequestParam String keyword) {
        List<Location> list = locationMapper.selectList(
            new LambdaQueryWrapper<Location>()
                .like(Location::getName, keyword)
                .eq(Location::getStatus, 1)
                .last("LIMIT 20")
        );
        return Result.success(list);
    }
}
