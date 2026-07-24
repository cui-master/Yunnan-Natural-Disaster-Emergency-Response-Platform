package com.yunnan.emergency.service;

import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.ResourceRequest;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.mapper.ResourceMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class ResourceService {

    @Autowired
    private ResourceMapper resourceMapper;
    @Autowired
    private AuditService audit;

    public List<Resource> list() {
        return resourceMapper.selectList(null);
    }

    public Resource create(ResourceRequest req) {
        Resource r = new Resource();
        r.setName(req.getName());
        r.setType(req.getType());
        r.setTotal(req.getTotal());
        r.setAvailable(req.getAvailable() == null ? req.getTotal() : req.getAvailable());
        r.setUnit(req.getUnit());
        r.setLocationId(req.getLocationId());
        r.setStatus("NORMAL");
        r.setCreatedAt(LocalDateTime.now());
        resourceMapper.insert(r);
        audit.log("RESOURCE_CREATE", "resource:" + r.getId(), "新增资源");
        return r;
    }

    public Resource update(Long id, ResourceRequest req) {
        Resource r = require(id);
        r.setName(req.getName());
        r.setType(req.getType());
        if (req.getTotal() != null) r.setTotal(req.getTotal());
        if (req.getAvailable() != null) r.setAvailable(req.getAvailable());
        r.setUnit(req.getUnit());
        r.setLocationId(req.getLocationId());
        resourceMapper.updateById(r);
        audit.log("RESOURCE_UPDATE", "resource:" + id, "更新资源");
        return r;
    }

    public void lock(Long resourceId, int qty) {
        Resource r = require(resourceId);
        int avail = r.getAvailable() == null ? 0 : r.getAvailable();
        if (avail < qty) {
            throw new BizException(409, "资源[" + r.getName() + "]可用量不足(可用" + avail + ",需求" + qty + ")");
        }
        r.setAvailable(avail - qty);
        r.setStatus("DEPLOYED");
        r.setLockedAt(LocalDateTime.now());
        resourceMapper.updateById(r);
    }

    public void release(Long resourceId, int qty) {
        Resource r = require(resourceId);
        int avail = r.getAvailable() == null ? 0 : r.getAvailable();
        int total = r.getTotal() == null ? 0 : r.getTotal();
        r.setAvailable(Math.min(total, avail + qty));
        r.setStatus(r.getAvailable() > 0 ? "NORMAL" : "DEPLOYED");
        resourceMapper.updateById(r);
    }

    public Resource require(Long id) {
        Resource r = resourceMapper.selectById(id);
        if (r == null) {
            throw new BizException(404, "资源不存在");
        }
        return r;
    }
}
