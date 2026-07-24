package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.DispatchRequest;
import com.yunnan.emergency.entity.DispatchOrder;
import com.yunnan.emergency.service.DispatchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/dispatch")
public class DispatchController {

    @Autowired
    private DispatchService dispatchService;

    @PostMapping
    public R<List<DispatchOrder>> create(@RequestBody DispatchRequest req) {
        return R.ok(dispatchService.dispatch(req));
    }

    @GetMapping
    public R<List<DispatchOrder>> list(@RequestParam Long incidentId) {
        return R.ok(dispatchService.listByIncident(incidentId));
    }
}
