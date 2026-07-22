package com.yunnan.emergency.dto;

import lombok.Data;

import java.util.List;

@Data
public class DispatchRequest {
    private Long incidentId;
    private Long planId;
    private List<DispatchItem> items;

    @Data
    public static class DispatchItem {
        private Long resourceId;
        private Integer quantity;
    }
}
