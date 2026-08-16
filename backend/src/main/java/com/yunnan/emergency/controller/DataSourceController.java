package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.DataSource;
import com.yunnan.emergency.mapper.DataSourceMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "数据源管理", description = "数据源的增删改查")
@RestController
@RequestMapping("/admin/data-sources")
public class DataSourceController {
    public DataSourceController(DataSourceMapper dataSourceMapper) {
        this.dataSourceMapper = dataSourceMapper;
    }


    private final DataSourceMapper dataSourceMapper;

    @Operation(summary = "分页查询数据源")
    @GetMapping("/page")
    public Result<Page<DataSource>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<DataSource> wrapper = new LambdaQueryWrapper<>();
        if (type != null && !type.isEmpty()) {
            wrapper.eq(DataSource::getType, type);
        }
        if (status != null) {
            wrapper.eq(DataSource::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(DataSource::getName, keyword).or().like(DataSource::getCode, keyword);
        }
        wrapper.orderByDesc(DataSource::getCreatedAt);

        Page<DataSource> page = dataSourceMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取所有数据源")
    @GetMapping("/list")
    public Result<List<DataSource>> list(@RequestParam(required = false) Integer status) {
        LambdaQueryWrapper<DataSource> wrapper = new LambdaQueryWrapper<>();
        if (status != null) {
            wrapper.eq(DataSource::getStatus, status);
        }
        wrapper.orderByAsc(DataSource::getId);
        return Result.success(dataSourceMapper.selectList(wrapper));
    }

    @Operation(summary = "获取数据源详情")
    @GetMapping("/{id}")
    public Result<DataSource> getById(@PathVariable Long id) {
        return Result.success(dataSourceMapper.selectById(id));
    }

    @Operation(summary = "新增数据源")
    @PostMapping
    public Result<DataSource> create(@RequestBody DataSource dataSource) {
        if (dataSource.getStatus() == null) {
            dataSource.setStatus(1);
        }
        dataSourceMapper.insert(dataSource);
        return Result.success(dataSource);
    }

    @Operation(summary = "更新数据源")
    @PutMapping("/{id}")
    public Result<DataSource> update(@PathVariable Long id, @RequestBody DataSource dataSource) {
        dataSource.setId(id);
        // 密码为空时不更新
        if (dataSource.getPassword() == null || dataSource.getPassword().isEmpty()) {
            dataSource.setPassword(null);
        }
        dataSourceMapper.updateById(dataSource);
        return Result.success(dataSourceMapper.selectById(id));
    }

    @Operation(summary = "删除数据源")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        dataSourceMapper.deleteById(id);
        return Result.success();
    }

    @Operation(summary = "启用/禁用数据源")
    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        DataSource ds = dataSourceMapper.selectById(id);
        if (ds == null) {
            return Result.error("数据源不存在");
        }
        ds.setStatus(status);
        dataSourceMapper.updateById(ds);
        return Result.success();
    }
}
