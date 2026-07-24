package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.entity.DispatchOrder;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.mapper.DispatchOrderMapper;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class IncidentService {

    @Autowired
    private IncidentMapper incidentMapper;
    @Autowired
    private DispatchOrderMapper dispatchMapper;
    @Autowired
    private ResourceService resourceService;
    @Autowired
    private WebSocketService webSocketService;
    @Autowired
    private AuditService audit;

    public List<Incident> list(String status, String type) {
        Authz.require("ROLE_COMMANDER", "ROLE_RESMGR", "ROLE_ADMIN");
        QueryWrapper<Incident> q = new QueryWrapper<>();
        if (status != null && !status.isEmpty()) {
            q.eq("status", status);
        }
        if (type != null && !type.isEmpty()) {
            q.eq("type", type);
        }
        q.orderByDesc("created_at");
        return incidentMapper.selectList(q);
    }

    public Incident detail(Long id) {
        return require(id);
    }

    public Incident confirm(Long id) {
        Authz.require("ROLE_COMMANDER");
        Incident inc = require(id);
        if (!"PENDING_VERIFY".equals(inc.getStatus())) {
            throw new BizException(400, "仅[待核验]事件可确认");
        }
        inc.setStatus("CONFIRMED");
        inc.setConfirmedBy(UserContext.getUserId());
        inc.setConfirmedAt(LocalDateTime.now());
        inc.setUpdatedAt(LocalDateTime.now());
        incidentMapper.updateById(inc);
        audit.log("INCIDENT_CONFIRM", "incident:" + id, "确认事件");
        webSocketService.broadcast("INCIDENT_STATUS", inc);
        return inc;
    }

    public Incident reject(Long id) {
        Authz.require("ROLE_COMMANDER");
        Incident inc = require(id);
        if (!"PENDING_VERIFY".equals(inc.getStatus())) {
            throw new BizException(400, "仅[待核验]事件可驳回");
        }
        inc.setStatus("REJECTED");
        inc.setUpdatedAt(LocalDateTime.now());
        incidentMapper.updateById(inc);
        audit.log("INCIDENT_REJECT", "incident:" + id, "驳回事件");
        webSocketService.broadcast("INCIDENT_STATUS", inc);
        return inc;
    }

    public Incident close(Long id) {
        Authz.require("ROLE_COMMANDER");
        Incident inc = require(id);
        if (!"IN_PROGRESS".equals(inc.getStatus()) && !"CONFIRMED".equals(inc.getStatus())) {
            throw new BizException(400, "仅[处置中/已确认]事件可归档");
        }
        QueryWrapper<DispatchOrder> q = new QueryWrapper<>();
        q.eq("incident_id", id).in("status", "LOCKED", "DISPATCHED");
        List<DispatchOrder> orders = dispatchMapper.selectList(q);
        for (DispatchOrder o : orders) {
            resourceService.release(o.getResourceId(), o.getQuantity() == null ? 0 : o.getQuantity());
            o.setStatus("RELEASED");
            o.setReleasedAt(LocalDateTime.now());
            dispatchMapper.updateById(o);
        }
        inc.setStatus("CLOSED");
        inc.setClosedAt(LocalDateTime.now());
        inc.setUpdatedAt(LocalDateTime.now());
        incidentMapper.updateById(inc);
        audit.log("INCIDENT_CLOSE", "incident:" + id, "归档事件并释放资源");
        webSocketService.broadcast("INCIDENT_STATUS", inc);
        return inc;
    }

    private Incident require(Long id) {
        Incident inc = incidentMapper.selectById(id);
        if (inc == null) {
            throw new BizException(404, "事件不存在");
        }
        return inc;
    }
}
