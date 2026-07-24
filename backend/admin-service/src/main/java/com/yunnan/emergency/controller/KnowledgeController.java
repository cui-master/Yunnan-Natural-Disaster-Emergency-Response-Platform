package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.KnowledgeUploadReq;
import com.yunnan.emergency.dto.KnowledgeVO;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import com.yunnan.emergency.service.KnowledgeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @Autowired
    private KnowledgeService knowledgeService;

    @GetMapping
    public R<List<KnowledgeVO>> list(@RequestParam(required = false) String category) {
        Authz.require("ROLE_ADMIN");
        return R.ok(knowledgeService.list(category));
    }

    @PostMapping
    public R<KnowledgeVO> upload(@RequestBody KnowledgeUploadReq req) {
        Authz.require("ROLE_ADMIN");
        return R.ok(knowledgeService.upload(req, UserContext.getUsername()));
    }

    @DeleteMapping("/{id}")
    public R<?> delete(@PathVariable Long id) {
        Authz.require("ROLE_ADMIN");
        knowledgeService.delete(id);
        return R.ok();
    }
}
