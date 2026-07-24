package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.DispatchRequest;
import com.yunnan.emergency.entity.DispatchOrder;
import com.yunnan.emergency.enums.DispatchStatus;
import com.yunnan.emergency.mapper.DispatchOrderMapper;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 资源调度服务：根据应急方案生成调度单，并对涉及资源做锁定（可用量校验 + 冲突检测）。
 * 整段调度在一个事务内完成，任一项失败则全部回滚。
 */
@Service
public class DispatchService {

    @Autowired
    private DispatchOrderMapper dispatchOrderMapper;
    @Autowired
    private ResourceService resourceService;
    @Autowired
    private AuditService audit;

    @Transactional
    public List<DispatchOrder> dispatch(DispatchRequest req) {
        if (req.getItems() == null || req.getItems().isEmpty()) {
            throw new BizException(400, "调度明细不能为空");
        }
        List<DispatchOrder> orders = new ArrayList<>();
        Long operatorId = UserContext.getUserId();
        for (DispatchRequest.DispatchItem item : req.getItems()) {
            if (item.getResourceId() == null || item.getQuantity() == null || item.getQuantity() <= 0) {
                throw new BizException(400, "调度明细非法：resourceId 与 quantity(>0) 必填");
            }
            // 锁定资源：内部已做可用量校验与冲突检测，不足会抛 BizException(409)
            resourceService.lock(item.getResourceId(), item.getQuantity());

            DispatchOrder order = new DispatchOrder();
            order.setIncidentId(req.getIncidentId());
            order.setPlanId(req.getPlanId());
            order.setResourceId(item.getResourceId());
            order.setQuantity(item.getQuantity());
            order.setStatus(DispatchStatus.DISPATCHED.name());
            order.setOperatorId(operatorId);
            order.setCreatedAt(LocalDateTime.now());
            dispatchOrderMapper.insert(order);

            orders.add(order);
            audit.log("DISPATCH_CREATE", "dispatch:" + order.getId(),
                    "生成调度单 incidentId=" + req.getIncidentId() + " resourceId=" + item.getResourceId());
        }
        return orders;
    }

    public List<DispatchOrder> listByIncident(Long incidentId) {
        LambdaQueryWrapper<DispatchOrder> qw = new LambdaQueryWrapper<>();
        qw.eq(DispatchOrder::getIncidentId, incidentId)
                .orderByDesc(DispatchOrder::getCreatedAt);
        return dispatchOrderMapper.selectList(qw);
    }
}
