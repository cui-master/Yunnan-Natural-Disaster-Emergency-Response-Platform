package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.service.IncidentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/incidents")
public class IncidentController {

    @Autowired
    private IncidentService incidentService;

    @GetMapping
    public R<List<Incident>> list(@RequestParam(required = false) String status,
                                   @RequestParam(required = false) String type) {
        return R.ok(incidentService.list(status, type));
    }

    @GetMapping("/{id}")
    public R<Incident> detail(@PathVariable Long id) {
        return R.ok(incidentService.detail(id));
    }

    @PostMapping("/{id}/confirm")
    public R<Incident> confirm(@PathVariable Long id) {
        return R.ok(incidentService.confirm(id));
    }

    @PostMapping("/{id}/reject")
    public R<Incident> reject(@PathVariable Long id) {
        return R.ok(incidentService.reject(id));
    }

    @PostMapping("/{id}/close")
    public R<Incident> close(@PathVariable Long id) {
        return R.ok(incidentService.close(id));
    }
}
