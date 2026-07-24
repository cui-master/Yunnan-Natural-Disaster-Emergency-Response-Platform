package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.RoleVO;
import com.yunnan.emergency.dto.SystemConfigVO;
import com.yunnan.emergency.dto.UserVO;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.service.SystemService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/system")
public class SystemController {

    @Autowired
    private SystemService systemService;

    @GetMapping("/users")
    public R<Map<String, Object>> users() {
        Authz.require("ROLE_ADMIN");
        return R.ok(systemService.listUsers());
    }

    @PostMapping("/users")
    public R<UserVO> createUser(@RequestBody Map<String, Object> body) {
        Authz.require("ROLE_ADMIN");
        return R.ok(systemService.createUser(body));
    }

    @PutMapping("/users/{id}")
    public R<UserVO> updateUser(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        Authz.require("ROLE_ADMIN");
        return R.ok(systemService.updateUser(id, body));
    }

    @GetMapping("/roles")
    public R<List<RoleVO>> roles() {
        Authz.require("ROLE_ADMIN");
        return R.ok(systemService.listRoles());
    }

    @GetMapping("/config")
    public R<List<SystemConfigVO>> config() {
        Authz.require("ROLE_ADMIN");
        return R.ok(systemService.getConfig());
    }

    @PutMapping("/config")
    public R<?> updateConfig(@RequestBody List<SystemConfigVO> body) {
        Authz.require("ROLE_ADMIN");
        systemService.updateConfig(body);
        return R.ok();
    }
}
