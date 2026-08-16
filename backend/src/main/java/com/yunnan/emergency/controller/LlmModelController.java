package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.LlmModel;
import com.yunnan.emergency.mapper.LlmModelMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "模型管理", description = "LLM模型的增删改查和切换")
@RestController
@RequestMapping("/admin/models")
public class LlmModelController {
    public LlmModelController(LlmModelMapper modelMapper) {
        this.modelMapper = modelMapper;
    }


    private final LlmModelMapper modelMapper;

    @Operation(summary = "分页查询模型")
    @GetMapping("/page")
    public Result<Page<LlmModel>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String provider,
            @RequestParam(required = false) String modelType,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<LlmModel> wrapper = new LambdaQueryWrapper<>();
        if (provider != null && !provider.isEmpty()) {
            wrapper.eq(LlmModel::getProvider, provider);
        }
        if (modelType != null && !modelType.isEmpty()) {
            wrapper.eq(LlmModel::getModelType, modelType);
        }
        if (status != null) {
            wrapper.eq(LlmModel::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(LlmModel::getModelName, keyword).or().like(LlmModel::getModelCode, keyword);
        }
        wrapper.orderByAsc(LlmModel::getSortOrder).orderByDesc(LlmModel::getCreatedAt);

        Page<LlmModel> page = modelMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取可用模型列表")
    @GetMapping("/list")
    public Result<List<LlmModel>> list(
            @RequestParam(required = false) String modelType,
            @RequestParam(required = false) Integer status) {
        LambdaQueryWrapper<LlmModel> wrapper = new LambdaQueryWrapper<>();
        if (modelType != null && !modelType.isEmpty()) {
            wrapper.eq(LlmModel::getModelType, modelType);
        }
        if (status != null) {
            wrapper.eq(LlmModel::getStatus, status);
        }
        wrapper.orderByAsc(LlmModel::getSortOrder);
        return Result.success(modelMapper.selectList(wrapper));
    }

    @Operation(summary = "获取当前激活的模型")
    @GetMapping("/active")
    public Result<LlmModel> getActiveModel() {
        LlmModel model = modelMapper.selectOne(
            new LambdaQueryWrapper<LlmModel>()
                .eq(LlmModel::getIsActive, 1)
                .eq(LlmModel::getStatus, 1)
                .last("LIMIT 1")
        );
        return Result.success(model);
    }

    @Operation(summary = "获取模型详情")
    @GetMapping("/{id}")
    public Result<LlmModel> getById(@PathVariable Long id) {
        return Result.success(modelMapper.selectById(id));
    }

    @Operation(summary = "新增模型")
    @PostMapping
    public Result<LlmModel> create(@RequestBody LlmModel model) {
        if (model.getStatus() == null) {
            model.setStatus(1);
        }
        if (model.getIsActive() == null) {
            model.setIsActive(0);
        }
        if (model.getIsDefault() == null) {
            model.setIsDefault(0);
        }
        modelMapper.insert(model);
        return Result.success(model);
    }

    @Operation(summary = "更新模型")
    @PutMapping("/{id}")
    public Result<LlmModel> update(@PathVariable Long id, @RequestBody LlmModel model) {
        model.setId(id);
        // 不更新 apiKey 为空时
        if (model.getApiKey() == null || model.getApiKey().isEmpty()) {
            model.setApiKey(null);
        }
        modelMapper.updateById(model);
        return Result.success(modelMapper.selectById(id));
    }

    @Operation(summary = "删除模型")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        modelMapper.deleteById(id);
        return Result.success();
    }

    @Operation(summary = "切换激活模型")
    @PutMapping("/{id}/activate")
    public Result<Void> activateModel(@PathVariable Long id) {
        LlmModel model = modelMapper.selectById(id);
        if (model == null) {
            return Result.error("模型不存在");
        }
        if (model.getStatus() == 0) {
            return Result.error("模型已禁用，无法激活");
        }

        // 先取消所有激活
        List<LlmModel> allModels = modelMapper.selectList(null);
        for (LlmModel m : allModels) {
            m.setIsActive(0);
            modelMapper.updateById(m);
        }

        // 设置当前激活
        model.setIsActive(1);
        modelMapper.updateById(model);

        return Result.success();
    }

    @Operation(summary = "启用/禁用模型")
    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        LlmModel model = modelMapper.selectById(id);
        if (model == null) {
            return Result.error("模型不存在");
        }
        model.setStatus(status);
        // 禁用时取消激活
        if (status == 0) {
            model.setIsActive(0);
        }
        modelMapper.updateById(model);
        return Result.success();
    }
}
