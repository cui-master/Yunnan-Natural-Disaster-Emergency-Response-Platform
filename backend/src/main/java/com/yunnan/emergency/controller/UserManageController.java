package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.UserMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;

@Tag(name = "用户管理", description = "系统用户的增删改查（管理员功能）")
@RestController
@RequestMapping("/admin/users")
public class UserManageController {
    public UserManageController(UserMapper userMapper, BCryptPasswordEncoder passwordEncoder) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
    }


    private final UserMapper userMapper;
    private final BCryptPasswordEncoder passwordEncoder;

    @Operation(summary = "分页查询用户")
    @GetMapping("/page")
    public Result<Page<User>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String roleCode,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        if (roleCode != null && !roleCode.isEmpty()) {
            wrapper.eq(User::getRoleCode, roleCode);
        }
        if (status != null) {
            wrapper.eq(User::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(User::getUsername, keyword)
                .or().like(User::getRealName, keyword)
                .or().like(User::getPhone, keyword);
        }
        wrapper.orderByDesc(User::getCreatedAt);

        Page<User> page = userMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        // 清除密码字段
        page.getRecords().forEach(u -> u.setPassword(null));
        return Result.success(page);
    }

    @Operation(summary = "获取用户详情")
    @GetMapping("/{id}")
    public Result<User> getById(@PathVariable Long id) {
        User user = userMapper.selectById(id);
        if (user != null) {
            user.setPassword(null);
        }
        return Result.success(user);
    }

    @Operation(summary = "新增用户")
    @PostMapping
    public Result<User> create(@RequestBody User user) {
        // 检查用户名是否存在
        User exist = userMapper.selectOne(
            new LambdaQueryWrapper<User>().eq(User::getUsername, user.getUsername())
        );
        if (exist != null) {
            return Result.error("用户名已存在");
        }
        // 默认密码 123456
        if (user.getPassword() == null || user.getPassword().isEmpty()) {
            user.setPassword(passwordEncoder.encode("123456"));
        } else {
            user.setPassword(passwordEncoder.encode(user.getPassword()));
        }
        if (user.getStatus() == null) {
            user.setStatus(1);
        }
        userMapper.insert(user);
        user.setPassword(null);
        return Result.success(user);
    }

    @Operation(summary = "更新用户")
    @PutMapping("/{id}")
    public Result<User> update(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        // 密码为空时不更新密码
        if (user.getPassword() == null || user.getPassword().isEmpty()) {
            user.setPassword(null);
        } else {
            user.setPassword(passwordEncoder.encode(user.getPassword()));
        }
        userMapper.updateById(user);
        User updated = userMapper.selectById(id);
        updated.setPassword(null);
        return Result.success(updated);
    }

    @Operation(summary = "删除用户")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        userMapper.deleteById(id);
        return Result.success();
    }

    @Operation(summary = "启用/禁用用户")
    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        User user = userMapper.selectById(id);
        if (user == null) {
            return Result.error("用户不存在");
        }
        user.setStatus(status);
        userMapper.updateById(user);
        return Result.success();
    }

    @Operation(summary = "重置密码")
    @PutMapping("/{id}/reset-password")
    public Result<Void> resetPassword(@PathVariable Long id) {
        User user = userMapper.selectById(id);
        if (user == null) {
            return Result.error("用户不存在");
        }
        user.setPassword(passwordEncoder.encode("123456"));
        userMapper.updateById(user);
        return Result.success();
    }

    @Operation(summary = "获取用户统计")
    @GetMapping("/stats")
    public Result<java.util.Map<String, Object>> getStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();
        Long total = userMapper.selectCount(null);
        Long active = userMapper.selectCount(new LambdaQueryWrapper<User>().eq(User::getStatus, 1));

        String[] roles = {"reporter", "commander", "resmanager", "admin"};
        String[] roleNames = {"普通信息员", "应急指挥员", "资源管理员", "系统管理员"};
        for (int i = 0; i < roles.length; i++) {
            Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getRoleCode, roles[i])
            );
            stats.put(roleNames[i], count);
        }
        stats.put("total", total);
        stats.put("active", active);
        return Result.success(stats);
    }
}
