package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.PlanApproveRequest;
import com.yunnan.emergency.entity.EmergencyPlan;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import com.yunnan.emergency.service.PlanService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api")
public class PlanController {

    @Autowired
    private PlanService planService;

    @GetMapping(value = "/incidents/{id}/plan", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter generate(@PathVariable Long id) {
        Authz.require("ROLE_COMMANDER");
        SseEmitter emitter = new SseEmitter(120000L);
        planService.generatePlanAsync(id, UserContext.getUserId(), emitter);
        return emitter;
    }

    @PostMapping("/plans/{id}/approve")
    public R<EmergencyPlan> approve(@PathVariable Long id, @RequestBody PlanApproveRequest req) {
        return R.ok(planService.approve(id, req.getContent()));
    }

    @GetMapping("/plans/{id}")
    public R<EmergencyPlan> detail(@PathVariable Long id) {
        return R.ok(planService.detail(id));
    }
}
