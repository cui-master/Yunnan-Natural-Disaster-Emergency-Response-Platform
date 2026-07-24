package com.yunnan.emergency.service;

import com.yunnan.emergency.dto.ReportSubmitRequest;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.IncidentReport;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.mapper.IncidentReportMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class ReportService {

    @Autowired
    private IncidentReportMapper reportMapper;
    @Autowired
    private IncidentMapper incidentMapper;
    @Autowired
    private WebSocketService webSocketService;
    @Autowired
    private AuditService audit;

    public IncidentReport submit(ReportSubmitRequest req, Long reporterId, String reporterName) {
        IncidentReport r = new IncidentReport();
        r.setReporterId(reporterId);
        r.setReporterName(reporterName);
        r.setContact(req.getContact());
        r.setContent(req.getContent());
        r.setImages(req.getImages());
        r.setLocationText(req.getLocationText());
        r.setLat(req.getLat());
        r.setLng(req.getLng());
        r.setStatus("SUBMITED");
        r.setCreatedAt(LocalDateTime.now());
        reportMapper.insert(r);

        Incident inc = new Incident();
        inc.setTitle(req.getTitle() != null ? req.getTitle() : "灾情上报-" + reporterName);
        inc.setType(req.getType());
        inc.setLevel(req.getLevel());
        inc.setDescription(req.getContent());
        inc.setReportId(r.getId());
        inc.setStatus("PENDING_VERIFY");
        inc.setCode(genCode());
        inc.setCreatedAt(LocalDateTime.now());
        inc.setUpdatedAt(LocalDateTime.now());
        incidentMapper.insert(inc);

        r.setIncidentId(inc.getId());
        reportMapper.updateById(r);

        audit.log("REPORT_SUBMIT", "report:" + r.getId(), "提交灾情上报");
        webSocketService.broadcast("NEW_INCIDENT", inc);
        return r;
    }

    private String genCode() {
        return "YN" + System.currentTimeMillis();
    }
}
