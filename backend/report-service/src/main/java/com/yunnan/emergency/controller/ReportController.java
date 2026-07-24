package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.ReportSubmitRequest;
import com.yunnan.emergency.entity.IncidentReport;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import com.yunnan.emergency.service.ReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    @Autowired
    private ReportService reportService;

    @PostMapping
    public R<IncidentReport> submit(@RequestBody ReportSubmitRequest req) {
        Authz.require("ROLE_REPORTER");
        Long uid = UserContext.getUserId();
        String name = UserContext.getRealName();
        return R.ok(reportService.submit(req, uid, name));
    }
}
