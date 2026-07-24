package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.ResourceRequest;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.service.ResourceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/resources")
public class ResourceController {

    @Autowired
    private ResourceService resourceService;

    @GetMapping
    public R<List<Resource>> list() {
        Authz.require("ROLE_RESMGR", "ROLE_COMMANDER", "ROLE_ADMIN");
        return R.ok(resourceService.list());
    }

    @PostMapping
    public R<Resource> create(@RequestBody ResourceRequest req) {
        Authz.require("ROLE_RESMGR");
        return R.ok(resourceService.create(req));
    }

    @PutMapping("/{id}")
    public R<Resource> update(@PathVariable Long id, @RequestBody ResourceRequest req) {
        Authz.require("ROLE_RESMGR");
        return R.ok(resourceService.update(id, req));
    }
}
