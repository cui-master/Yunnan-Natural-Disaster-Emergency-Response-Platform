package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.DataPipelineService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Tag(name = "天气查询", description = "云南省各地市/区县天气预报查询（爬虫代理）")
@RestController
@RequestMapping("/weather")
public class WeatherController {
    public WeatherController(DataPipelineService dataPipelineService) {
        this.dataPipelineService = dataPipelineService;
    }


    private static final Logger log = LoggerFactory.getLogger(WeatherController.class);

    private final DataPipelineService dataPipelineService;

    @Operation(summary = "获取云南城市列表（地市+区县树）")
    @GetMapping("/cities")
    public Result<Object> getCities() {
        String result = dataPipelineService.get("/api/v1/weather/cities");
        return Result.success(parseBody(result));
    }

    @Operation(summary = "获取地市下辖区县")
    @GetMapping("/districts/{cityName}")
    public Result<Object> getDistricts(@PathVariable String cityName) {
        String result = dataPipelineService.get("/api/v1/weather/districts/" + cityName);
        return Result.success(parseBody(result));
    }

    @Operation(summary = "查询天气预报（昨天到后天）")
    @GetMapping("/forecast")
    public Result<Object> getForecast(
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String slug) {
        StringBuilder path = new StringBuilder("/api/v1/weather/forecast?");
        if (city != null && !city.isEmpty()) {
            path.append("city=").append(city);
        }
        if (slug != null && !slug.isEmpty()) {
            if (path.charAt(path.length() - 1) != '?') {
                path.append("&");
            }
            path.append("slug=").append(slug);
        }
        String result = dataPipelineService.get(path.toString());
        return Result.success(parseBody(result));
    }

    @Operation(summary = "通过 slug 查询天气预报")
    @GetMapping("/forecast/{slug}")
    public Result<Object> getForecastBySlug(@PathVariable String slug) {
        String result = dataPipelineService.get("/api/v1/weather/forecast/" + slug);
        return Result.success(parseBody(result));
    }

    @Operation(summary = "天气服务健康检查")
    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        boolean healthy = dataPipelineService.checkHealth();
        Map<String, Object> result = new HashMap<>();
        result.put("healthy", healthy);
        result.put("status", healthy ? "running" : "stopped");
        return Result.success(result);
    }

    private Object parseBody(String body) {
        if (body == null || body.isEmpty()) {
            return null;
        }
        try {
            return cn.hutool.json.JSONUtil.parse(body);
        } catch (Exception e) {
            return body;
        }
    }
}
