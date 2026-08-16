package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Role;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.RoleMapper;
import com.yunnan.emergency.mapper.UserMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Tag(name = "角色管理", description = "系统角色查询与状态管理")
@RestController
@RequestMapping("/admin/roles")
public class RoleController {

    private final RoleMapper roleMapper;
    private final UserMapper userMapper;

    public RoleController(RoleMapper roleMapper, UserMapper userMapper) {
        this.roleMapper = roleMapper;
        this.userMapper = userMapper;
    }

    @Operation(summary = "获取全部角色列表")
    @GetMapping("/list")
    public Result<List<Role>> list(@RequestParam(required = false) Integer status) {
        LambdaQueryWrapper<Role> wrapper = new LambdaQueryWrapper<>();
        if (status != null) {
            wrapper.eq(Role::getStatus, status);
        }
        wrapper.orderByAsc(Role::getId);
        return Result.success(roleMapper.selectList(wrapper));
    }

    @Operation(summary = "获取角色统计")
    @GetMapping("/stats")
    public Result<Map<String, Object>> stats() {
        Map<String, Object> result = new HashMap<>();
        List<Role> roles = roleMapper.selectList(null);
        for (Role role : roles) {
            Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getRoleCode, role.getRoleCode())
            );
            Map<String, Object> item = new HashMap<>();
            item.put("role", role);
            item.put("count", count);
            result.put(role.getRoleCode(), item);
        }
        return Result.success(result);
    }

    @Operation(summary = "启用/禁用角色")
    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Integer id, @RequestParam Integer status) {
        Role role = roleMapper.selectById(id);
        if (role == null) {
            return Result.error("角色不存在");
        }
        role.setStatus(status);
        roleMapper.updateById(role);
        return Result.success();
    }
}
